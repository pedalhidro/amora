package co.pedalhidrografi.amora.upload;

import android.Manifest;
import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.database.Cursor;
import android.media.MediaMetadataRetriever;
import android.net.Uri;
import android.os.Build;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.util.Log;
import android.webkit.MimeTypeMap;
import androidx.activity.result.ActivityResult;
import androidx.activity.result.PickVisualMediaRequest;
import androidx.activity.result.contract.ActivityResultContracts.PickMultipleVisualMedia;
import androidx.activity.result.contract.ActivityResultContracts.PickVisualMedia;
import androidx.exifinterface.media.ExifInterface;
import com.getcapacitor.Bridge;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;

/**
 * Seletor nativo de mídia + envio em segundo plano. Contrato (o mesmo que o
 * iOS vai implementar): docs/PLAN-native-upload.md §3.
 *
 * O JS continua dono de tudo que é produto (hash, EXIF, variantes, TTL,
 * álbum); aqui só (1) traz os arquivos da galeria pro armazenamento do app
 * COM a localização, e (2) sobe os POSTs montados pelo JS de um jeito que
 * sobrevive à tela apagada, à troca de app e à queda de rede.
 */
@CapacitorPlugin(
    name = "AmoraUpload",
    permissions = { @Permission(alias = "notifications", strings = { Manifest.permission.POST_NOTIFICATIONS }) }
)
public class AmoraUploadPlugin extends Plugin implements Store.Listener {

    static final int API_VERSION = 1;
    private static final int MAX_CHUNK = 4 << 20;

    private Store store;
    // Cópias da galeria numa fila própria: um lote de vídeos não pode
    // segurar putBlob/enqueue (que o JS chama enquanto a escolha copia).
    private final ExecutorService copyIo = Executors.newSingleThreadExecutor();
    private final ExecutorService io = Executors.newCachedThreadPool();

    @Override
    public void load() {
        store = Store.get(getContext());
        store.addListener(this);
        io.execute(() -> {
            store.sweep();
            // Fila sobrando de antes (app atualizado, processo morto): garante o dreno.
            if (store.counts()[0] > 0) UploadWorker.kick(getContext());
        });
    }

    @Override
    protected void handleOnDestroy() {
        store.removeListener(this);
    }

    @Override
    public void onJobChanged(JSONObject publicJob) {
        try {
            notifyListeners("jobChanged", JSObject.fromJSONObject(publicJob));
        } catch (Exception e) {
            Log.w(Store.TAG, "jobChanged", e);
        }
    }

    @PluginMethod
    public void info(PluginCall call) {
        JSObject r = new JSObject();
        r.put("apiVersion", API_VERSION);
        r.put("platform", "android");
        r.put("sdkInt", Build.VERSION.SDK_INT);
        r.put("picker", "documents");
        call.resolve(r);
    }

    // ===================== pick =====================

    // QUAL seletor (medido no Android 15, emulador — docs/PLAN-native-upload.md):
    //  - Photo Picker: entrega a cópia com o GPS ZERADO, mesmo com
    //    ACCESS_MEDIA_LOCATION, e recusa o setRequireOriginal. Inútil pro mapa.
    //  - Photo Picker + leitura pelo MediaStore: vem com GPS, mas exige
    //    READ_MEDIA_IMAGES/VIDEO ("Allow all") — declaração na Play Store.
    //  - Seletor de DOCUMENTOS (default): o original intacto, COM GPS e com o
    //    nome de verdade, SEM permissão nenhuma.
    // `source: 'photos'` ainda abre o Photo Picker (sem GPS) — reserva.
    @PluginMethod
    public void pick(PluginCall call) {
        // Na 1ª vez: notificações (progresso do envio). Negar não impede a escolha.
        if (Build.VERSION.SDK_INT >= 33 && askable("notifications")) {
            requestPermissionForAlias("notifications", call, "afterPickPermissions");
        } else {
            launchPicker(call);
        }
    }

    private boolean askable(String alias) {
        PermissionState s = getPermissionState(alias);
        return s == PermissionState.PROMPT || s == PermissionState.PROMPT_WITH_RATIONALE;
    }

    @PermissionCallback
    private void afterPickPermissions(PluginCall call) {
        launchPicker(call);
    }

    private void launchPicker(PluginCall call) {
        boolean videos = Boolean.TRUE.equals(call.getBoolean("videos", false));
        int limit = call.getInt("limit", 0);
        PickVisualMedia.VisualMediaType type = videos ? PickVisualMedia.ImageAndVideo.INSTANCE : PickVisualMedia.ImageOnly.INSTANCE;
        if (!"photos".equals(call.getString("source"))) {
            // Seletor de documentos do sistema (DocumentsUI) — ver o pick().
            Intent doc = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            doc.addCategory(Intent.CATEGORY_OPENABLE);
            doc.setType(videos ? "*/*" : "image/*");
            if (videos) doc.putExtra(Intent.EXTRA_MIME_TYPES, new String[] { "image/*", "video/*" });
            doc.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, limit != 1);
            startActivityForResult(call, doc, "onPicked");
            return;
        }
        PickVisualMediaRequest req = new PickVisualMediaRequest.Builder().setMediaType(type).build();
        Intent intent = limit == 1
            ? new PickVisualMedia().createIntent(getContext(), req)
            : (limit >= 2 ? new PickMultipleVisualMedia(limit) : new PickMultipleVisualMedia()).createIntent(getContext(), req);
        startActivityForResult(call, intent, "onPicked");
    }

    @ActivityCallback
    private void onPicked(PluginCall call, ActivityResult result) {
        if (call == null) return;
        List<Uri> uris;
        if (result.getResultCode() != Activity.RESULT_OK) {
            uris = Collections.emptyList();
        } else if (!"photos".equals(call.getString("source"))) {
            uris = new ArrayList<>();
            Intent d = result.getData();
            if (d != null && d.getClipData() != null) {
                for (int i = 0; i < d.getClipData().getItemCount(); i++) uris.add(d.getClipData().getItemAt(i).getUri());
            } else if (d != null && d.getData() != null) {
                uris.add(d.getData());
            }
        } else if (call.getInt("limit", 0) == 1) {
            Uri u = new PickVisualMedia().parseResult(result.getResultCode(), result.getData());
            uris = u == null ? Collections.emptyList() : Collections.singletonList(u);
        } else {
            uris = new PickMultipleVisualMedia().parseResult(result.getResultCode(), result.getData());
        }
        if (uris.isEmpty()) {
            JSObject r = new JSObject();
            r.put("items", new JSArray());
            r.put("failed", new JSArray());
            call.resolve(r);
            getBridge().releaseCall(call);
            return;
        }
        // A escolha acabou de voltar: o app está na frente — o único momento em
        // que o Android deixa o dreno virar serviço de primeiro plano antes de
        // o JS terminar o preparo (ver UploadWorker.kick(ctx, warm)).
        io.execute(() -> UploadWorker.kick(getContext(), true));
        copyIo.execute(() -> copyPicked(call, uris));
    }

    private void copyPicked(PluginCall call, List<Uri> uris) {
        JSArray items = new JSArray();
        JSArray failed = new JSArray();
        String origin = pageOrigin();
        int done = 0;
        for (Uri uri : uris) {
            String name = "arquivo";
            try {
                ContentResolver cr = getContext().getContentResolver();
                long size = -1;
                try (Cursor c = cr.query(uri, new String[] { OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE }, null, null, null)) {
                    if (c != null && c.moveToFirst()) {
                        if (!c.isNull(0)) name = c.getString(0);
                        if (!c.isNull(1)) size = c.getLong(1);
                    }
                }
                String mime = cr.getType(uri);
                String ext = extension(name, mime);
                if (mime == null) mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext);
                if (mime == null) mime = "application/octet-stream";
                String pickId = UUID.randomUUID().toString();
                File dest = new File(store.picks, pickId + "." + ext);

                InputStream in = cr.openInputStream(uri);
                if (in == null) throw new IllegalStateException("sem leitura");
                try (InputStream src = in; OutputStream out = new FileOutputStream(dest)) {
                    byte[] buf = new byte[256 * 1024];
                    int n;
                    while ((n = src.read(buf)) > 0) out.write(buf, 0, n);
                }

                boolean video = mime.startsWith("video/");
                JSObject item = new JSObject();
                item.put("pickId", pickId);
                item.put("kind", video ? "video" : "image");
                item.put("name", name);
                item.put("mime", mime);
                item.put("size", dest.length());
                item.put("url", origin + Bridge.CAPACITOR_FILE_START + dest.getAbsolutePath());
                // Diagnóstico do GPS (spike A1 do plano): o arquivo copiado tem localização?
                JSObject diag = new JSObject();
                diag.put("authority", uri.getAuthority());
                diag.put("hasGps", hasGps(dest, video));
                if (size >= 0 && size != dest.length()) diag.put("reportedSize", size);
                item.put("diag", diag);
                items.put(item);
            } catch (Exception e) {
                Log.w(Store.TAG, "cópia de " + uri, e);
                JSObject f = new JSObject();
                f.put("name", name);
                f.put("error", e.getClass().getSimpleName() + (e.getMessage() != null ? ": " + e.getMessage() : ""));
                failed.put(f);
            }
            done++;
            JSObject p = new JSObject();
            p.put("done", done);
            p.put("total", uris.size());
            notifyListeners("pickProgress", p);
        }
        JSObject r = new JSObject();
        r.put("items", items);
        r.put("failed", failed);
        call.resolve(r);
        getBridge().releaseCall(call);
    }

    private static String extension(String name, String mime) {
        int dot = name.lastIndexOf('.');
        if (dot > 0 && dot < name.length() - 1) {
            String e = name.substring(dot + 1).toLowerCase(Locale.ROOT);
            if (e.matches("[a-z0-9]{1,5}")) return e;
        }
        String e = mime == null ? null : MimeTypeMap.getSingleton().getExtensionFromMimeType(mime);
        return e == null ? "bin" : e;
    }

    private static Boolean hasGps(File f, boolean video) {
        try {
            if (video) {
                MediaMetadataRetriever mmr = new MediaMetadataRetriever();
                try {
                    mmr.setDataSource(f.getAbsolutePath());
                    return mmr.extractMetadata(MediaMetadataRetriever.METADATA_KEY_LOCATION) != null;
                } finally {
                    mmr.release();
                }
            }
            float[] ll = new float[2];
            return new ExifInterface(f.getAbsolutePath()).getLatLong(ll) && !(ll[0] == 0f && ll[1] == 0f);
        } catch (Exception e) {
            return null;
        }
    }

    /** Origem da página (server.url): os arquivos são servidos NELA, mesma origem. */
    private String pageOrigin() {
        String s = getBridge().getServerUrl();
        if (s == null) return getBridge().getLocalUrl();
        try {
            URL u = new URL(s);
            return u.getProtocol() + "://" + u.getAuthority();
        } catch (Exception e) {
            return getBridge().getLocalUrl();
        }
    }

    // ===================== bytes JS ⇄ disco =====================

    @PluginMethod
    public void readChunk(PluginCall call) {
        File f = store.findPick(call.getString("pickId"));
        if (f == null) {
            call.reject("pick desconhecido");
            return;
        }
        long offset = call.getLong("offset", 0L);
        int length = Math.min(call.getInt("length", MAX_CHUNK), MAX_CHUNK);
        io.execute(() -> {
            try (RandomAccessFile raf = new RandomAccessFile(f, "r")) {
                long avail = Math.max(0, raf.length() - offset);
                byte[] b = new byte[(int) Math.min(length, avail)];
                raf.seek(offset);
                raf.readFully(b);
                JSObject r = new JSObject();
                r.put("base64", Base64.encodeToString(b, Base64.NO_WRAP));
                r.put("size", raf.length());
                call.resolve(r);
            } catch (Exception e) {
                call.reject("leitura: " + e.getMessage());
            }
        });
    }

    @PluginMethod
    public void putBlob(PluginCall call) {
        String id = call.getString("blobId");
        if (id == null) id = UUID.randomUUID().toString();
        File f = store.blobFile(id);
        String b64 = call.getString("base64", "");
        if (f == null) {
            call.reject("blobId inválido");
            return;
        }
        final String blobId = id;
        io.execute(() -> {
            try (FileOutputStream out = new FileOutputStream(f, true)) {
                out.write(Base64.decode(b64, Base64.DEFAULT));
                JSObject r = new JSObject();
                r.put("blobId", blobId);
                r.put("size", f.length());
                call.resolve(r);
            } catch (Exception e) {
                call.reject("gravação: " + e.getMessage());
            }
        });
    }

    // ===================== fila =====================

    @PluginMethod
    public void enqueue(PluginCall call) {
        JSObject spec = call.getData();
        String jobId = spec.optString("jobId");
        if (!Store.validId(jobId)) {
            call.reject("jobId inválido (use [A-Za-z0-9-], até 64)");
            return;
        }
        String err = validateSpec(spec);
        if (err != null) {
            call.reject(err);
            return;
        }
        io.execute(() -> {
            try {
                JSONObject job = store.createJob(spec);
                UploadWorker.kick(getContext());
                call.resolve(JSObject.fromJSONObject(job));
            } catch (Exception e) {
                call.reject("enqueue: " + e.getMessage());
            }
        });
    }

    /** Só sobe pro servidor da própria página, e só arquivos do armazenamento do plugin. */
    private String validateSpec(JSObject spec) {
        try {
            URL target = new URL(spec.getString("url"));
            URL page = new URL(pageOrigin());
            if (!"https".equals(target.getProtocol()) && !"localhost".equals(target.getHost())) return "url precisa ser https";
            if (!target.getHost().equalsIgnoreCase(page.getHost())) return "url fora do servidor do app: " + target.getHost();
            org.json.JSONArray files = spec.optJSONArray("files");
            for (int i = 0; files != null && i < files.length(); i++) {
                JSONObject f = files.getJSONObject(i);
                File src = store.sourceFile(f.optJSONObject("source"));
                if (src == null || !src.exists()) return "arquivo inexistente no envio: " + f.optString("field");
                if (f.optString("field").isEmpty() || f.optString("filename").isEmpty()) return "field/filename obrigatórios";
            }
            String after = spec.optString("after", "");
            if (!after.isEmpty() && !Store.validId(after)) return "after inválido";
            return null;
        } catch (Exception e) {
            return "especificação inválida: " + e.getMessage();
        }
    }

    @PluginMethod
    public void listJobs(PluginCall call) {
        JSObject r = new JSObject();
        r.put("jobs", store.listPublic());
        call.resolve(r);
    }

    @PluginMethod
    public void cancel(PluginCall call) {
        boolean ok = store.cancel(call.getString("jobId", ""));
        JSObject r = new JSObject();
        r.put("cancelled", ok);
        call.resolve(r);
    }

    @PluginMethod
    public void retry(PluginCall call) {
        String id = call.getString("jobId", "");
        io.execute(() -> {
            boolean ok = store.retry(id);
            if (ok) UploadWorker.kick(getContext());
            JSObject r = new JSObject();
            r.put("retried", ok);
            call.resolve(r);
        });
    }

    @PluginMethod
    public void ack(PluginCall call) {
        String id = call.getString("jobId", "");
        io.execute(() -> {
            store.ack(id);
            call.resolve();
        });
    }

    @PluginMethod
    public void release(PluginCall call) {
        JSArray ids = call.getArray("pickIds", new JSArray());
        List<String> list = new ArrayList<>();
        for (int i = 0; i < ids.length(); i++) list.add(ids.optString(i));
        io.execute(() -> {
            store.release(list);
            call.resolve();
        });
    }
}
