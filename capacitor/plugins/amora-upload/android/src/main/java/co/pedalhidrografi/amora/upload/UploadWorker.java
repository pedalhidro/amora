package co.pedalhidrografi.amora.upload;

import android.app.ActivityManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.util.Log;
import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.work.Constraints;
import androidx.work.ExistingWorkPolicy;
import androidx.work.ForegroundInfo;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.OutOfQuotaPolicy;
import androidx.work.WorkInfo;
import androidx.work.WorkManager;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * O "dreno": UM worker que sobe os jobs da fila em série até esvaziá-la.
 * Um só (e não um por job) pra ter UMA notificação de progresso, e porque o
 * envio é limitado pela banda de subida do celular — paralelo não ganha nada.
 *
 * Dois nomes únicos no WorkManager:
 *  - NOW   — disparado por enqueue (expedited, com rede), encadeado se já há
 *            um rodando, mantido se há um esperando;
 *  - LATER — o próximo recuo de uma falha transitória (com atraso, REPLACE).
 * Os dois podem rodar juntos sem pegar o mesmo job (Store.claimNext).
 */
public class UploadWorker extends Worker {

    static final String NOW = "amora-upload-now";
    static final String LATER = "amora-upload-later";
    static final String CHANNEL = "amora-upload";
    static final int NOTIF_ID = 0x4A01;
    static final int SUMMARY_ID = 0x4A02;

    private long lastNotify = 0;
    private int doneCount = 0;

    public UploadWorker(@NonNull Context ctx, @NonNull WorkerParameters params) {
        super(ctx, params);
    }

    /** Garante que um dreno vai rodar (chamado depois de enqueue, fora da thread da ponte). */
    static void kick(Context ctx) {
        WorkManager wm = WorkManager.getInstance(ctx);
        ExistingWorkPolicy policy = ExistingWorkPolicy.APPEND_OR_REPLACE;
        try {
            List<WorkInfo> infos = wm.getWorkInfosForUniqueWork(NOW).get();
            for (WorkInfo wi : infos) {
                // Um dreno ainda esperando a vez vai ler o manifesto quando rodar:
                // não precisa de outro atrás dele.
                if (wi.getState() == WorkInfo.State.ENQUEUED || wi.getState() == WorkInfo.State.BLOCKED) {
                    policy = ExistingWorkPolicy.KEEP;
                }
            }
        } catch (Exception e) {
            Log.w(Store.TAG, "consulta ao WorkManager", e);
        }
        OneTimeWorkRequest req = new OneTimeWorkRequest.Builder(UploadWorker.class)
            .setConstraints(new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)
            .build();
        wm.enqueueUniqueWork(NOW, policy, req);
    }

    private static void scheduleLater(Context ctx, long delayMs) {
        OneTimeWorkRequest req = new OneTimeWorkRequest.Builder(UploadWorker.class)
            .setConstraints(new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .setInitialDelay(Math.max(1000, delayMs), TimeUnit.MILLISECONDS)
            .build();
        WorkManager.getInstance(ctx).enqueueUniqueWork(LATER, ExistingWorkPolicy.REPLACE, req);
    }

    @NonNull
    @Override
    public Result doWork() {
        Context ctx = getApplicationContext();
        Store store = Store.get(ctx);
        String ua = userAgent(ctx);
        boolean foreground = false;
        while (!isStopped()) {
            final String id = store.claimNext(System.currentTimeMillis());
            if (id == null) break;
            if (!foreground) {
                foreground = true;
                promote(0, 0);
            }
            JSONObject job = store.snapshot(id);
            if (job == null) continue;
            Uploader.Result r = Uploader.post(job, store, ua,
                (sent, total) -> {
                    store.progress(id, sent, total);
                    long now = System.currentTimeMillis();
                    if (now - lastNotify > 1000) {
                        lastNotify = now;
                        promote(sent, total);
                    }
                },
                () -> isStopped() || store.isCancelled(id));
            if (store.isCancelled(id)) continue;   // cancelado no meio: já está failed
            if (r.status == 0 && isStopped()) {
                store.requeue(id);
                break;
            }
            classify(store, id, r);
        }
        long wake = store.nextWakeAt();
        if (wake > 0) scheduleLater(ctx, wake - System.currentTimeMillis());
        if (doneCount > 0) summary(ctx, doneCount);
        return Result.success();
    }

    private void classify(Store store, String id, Uploader.Result r) {
        int s = r.status;
        if (s >= 200 && s < 300) {
            store.done(id, s, r.body);
            doneCount++;
        } else if (s == -1) {
            store.failed(id, 0, null, r.error);
        } else if (s == 0) {
            store.retryLater(id, 0, r.error);
        } else if (s == 408 || s == 429 || s >= 500) {
            store.retryLater(id, s, errorText(r.body, s));
        } else {
            store.failed(id, s, r.body, errorText(r.body, s));
        }
    }

    /** Mesma leitura que o postMedia do subir.html: details, senão error, senão HTTP n. */
    static String errorText(Object body, int status) {
        if (body instanceof JSONObject) {
            JSONObject b = (JSONObject) body;
            JSONArray d = b.optJSONArray("details");
            if (d != null && d.length() > 0) {
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < d.length(); i++) {
                    if (i > 0) sb.append("; ");
                    sb.append(d.optString(i));
                }
                return sb.toString();
            }
            if (b.has("error")) return b.optString("error");
        }
        return "HTTP " + status;
    }

    // ===================== Notificação =====================

    @NonNull
    @Override
    public ForegroundInfo getForegroundInfo() {
        // Exigido pra trabalho expedited em Android < 12.
        return foregroundInfo(getApplicationContext(), 0, 0);
    }

    private void promote(long sent, long total) {
        try {
            setForegroundAsync(foregroundInfo(getApplicationContext(), sent, total)).get();
        } catch (Exception e) {
            // Android 12+ pode recusar serviço de primeiro plano iniciado em
            // segundo plano: o envio segue como job comum, só sem notificação.
            Log.i(Store.TAG, "sem primeiro plano: " + e);
        }
    }

    private static ForegroundInfo foregroundInfo(Context ctx, long sent, long total) {
        ensureChannel(ctx);
        int pending = Store.get(ctx).counts()[0];
        NotificationCompat.Builder b = new NotificationCompat.Builder(ctx, CHANNEL)
            .setSmallIcon(android.R.drawable.stat_sys_upload)
            .setContentTitle("Enviando pro amora")
            .setContentText(pending == 1 ? "1 arquivo na fila" : pending + " arquivos na fila")
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .setContentIntent(openApp(ctx));
        if (total > 0) b.setProgress(1000, (int) (sent * 1000 / total), false);
        else b.setProgress(0, 0, true);
        Notification n = b.build();
        if (Build.VERSION.SDK_INT >= 29) {
            return new ForegroundInfo(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
        }
        return new ForegroundInfo(NOTIF_ID, n);
    }

    /** "N enviados" — só com o app fora da tela (na tela, quem avisa é o próprio app). */
    private static void summary(Context ctx, int n) {
        ActivityManager.RunningAppProcessInfo me = new ActivityManager.RunningAppProcessInfo();
        ActivityManager.getMyMemoryState(me);
        if (me.importance <= ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND) return;
        NotificationManagerCompat nm = NotificationManagerCompat.from(ctx);
        if (!nm.areNotificationsEnabled()) return;
        ensureChannel(ctx);
        Notification notif = new NotificationCompat.Builder(ctx, CHANNEL)
            .setSmallIcon(android.R.drawable.stat_sys_upload_done)
            .setContentTitle(n == 1 ? "1 arquivo enviado pro amora" : n + " arquivos enviados pro amora")
            .setAutoCancel(true)
            .setContentIntent(openApp(ctx))
            .build();
        try {
            nm.notify(SUMMARY_ID, notif);
        } catch (SecurityException e) {
            Log.i(Store.TAG, "notificação recusada: " + e);
        }
    }

    private static void ensureChannel(Context ctx) {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        if (nm.getNotificationChannel(CHANNEL) != null) return;
        NotificationChannel ch = new NotificationChannel(CHANNEL, "Envios pro amora", NotificationManager.IMPORTANCE_LOW);
        ch.setDescription("Progresso do envio de fotos e vídeos em segundo plano");
        nm.createNotificationChannel(ch);
    }

    private static PendingIntent openApp(Context ctx) {
        Intent i = ctx.getPackageManager().getLaunchIntentForPackage(ctx.getPackageName());
        if (i == null) i = new Intent();
        return PendingIntent.getActivity(ctx, 0, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    static String userAgent(Context ctx) {
        String v = "?";
        try {
            PackageInfo pi = ctx.getPackageManager().getPackageInfo(ctx.getPackageName(), 0);
            v = pi.versionName;
        } catch (Exception ignored) {}
        return "Amora-Android/" + v + " (Android " + Build.VERSION.RELEASE + ")";
    }
}
