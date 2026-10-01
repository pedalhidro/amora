package co.pedalhidrografi.amora.upload;

import android.content.Context;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArrayList;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Estado durável do envio: arquivos escolhidos (picks/), pedaços gerados pelo
 * JS (blobs/) e o manifesto dos jobs (manifest.json, reescrito atômico).
 *
 * Mora em noBackupFilesDir: o SO não apaga (ao contrário do cache) e não vai
 * pro backup do Google. Um processo só, então um lock só — o plugin (thread da
 * ponte) e o worker (thread do WorkManager) passam todos por aqui.
 *
 * Estados do job (contrato §3): queued → sending → done | waiting → … | failed.
 */
final class Store {

    interface Listener {
        void onJobChanged(JSONObject publicJob);
    }

    static final String TAG = "AmoraUpload";
    static final long KEEP_FINAL_MS = 7L * 24 * 3600 * 1000;      // job final sem ack
    static final long KEEP_ORPHAN_MS = 7L * 24 * 3600 * 1000;     // pick/blob sem job
    static final long GIVE_UP_MS = 24L * 3600 * 1000;             // desiste de re-tentar
    static final long[] BACKOFF_MS = { 30_000, 120_000, 600_000, 1_800_000, 3_600_000 };

    private static Store instance;

    static synchronized Store get(Context ctx) {
        if (instance == null) instance = new Store(ctx.getApplicationContext());
        return instance;
    }

    final File root, picks, blobs;
    private final File manifest;
    private JSONObject jobs;   // jobId → job (com a especificação do request)
    private final List<Listener> listeners = new CopyOnWriteArrayList<>();

    private Store(Context ctx) {
        root = new File(ctx.getNoBackupFilesDir(), "amora-upload");
        picks = new File(root, "picks");
        blobs = new File(root, "blobs");
        picks.mkdirs();
        blobs.mkdirs();
        manifest = new File(root, "manifest.json");
        jobs = load();
        // Processo novo = nenhum worker rodando: o que ficou "sending" morreu no
        // meio (processo morto) — volta pra fila, sem contar tentativa.
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) {
            JSONObject j = jobs.optJSONObject(it.next());
            if (j != null && "sending".equals(j.optString("state"))) {
                put(j, "state", "queued");
                j.remove("sent");
                j.remove("total");
            }
        }
        save();
    }

    void addListener(Listener l) { listeners.add(l); }
    void removeListener(Listener l) { listeners.remove(l); }

    // ===================== Manifesto =====================

    private JSONObject load() {
        try {
            if (manifest.exists()) {
                String text = readText(manifest);
                JSONObject j = new JSONObject(text).optJSONObject("jobs");
                if (j != null) return j;
            }
        } catch (Exception e) {
            Log.e(TAG, "manifesto ilegível — começando vazio", e);
        }
        return new JSONObject();
    }

    // (java.nio.file só existe a partir da API 26; o minSdk é 24.)
    private static String readText(File f) throws java.io.IOException {
        try (InputStream in = new FileInputStream(f)) {
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            byte[] b = new byte[16 * 1024];
            int n;
            while ((n = in.read(b)) > 0) bo.write(b, 0, n);
            return new String(bo.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    private void save() {
        File tmp = new File(root, "manifest.json.tmp");
        try (FileOutputStream out = new FileOutputStream(tmp)) {
            out.write(new JSONObject().put("jobs", jobs).toString().getBytes(StandardCharsets.UTF_8));
            out.getFD().sync();
        } catch (Exception e) {
            Log.e(TAG, "falha gravando o manifesto", e);
            return;
        }
        if (!tmp.renameTo(manifest)) Log.e(TAG, "falha no rename do manifesto");
    }

    private void changed(JSONObject job) {
        save();
        JSONObject pub = publicView(job);
        for (Listener l : listeners) {
            try { l.onJobChanged(pub); } catch (Exception e) { Log.w(TAG, "listener", e); }
        }
    }

    /** O que o JS vê: sem a especificação do request (o TTL é grande e o JS já tem). */
    static JSONObject publicView(JSONObject job) {
        JSONObject p = new JSONObject();
        for (String k : new String[] { "jobId", "meta", "state", "attempts", "sent", "total",
                "nextAttemptAt", "httpStatus", "response", "error", "createdAt", "updatedAt" }) {
            if (job.has(k)) put(p, k, job.opt(k));
        }
        return p;
    }

    private static void put(JSONObject o, String k, Object v) {
        try { o.put(k, v); } catch (JSONException e) { throw new IllegalStateException(e); }
    }

    // ===================== Jobs =====================

    /** Cria o job, ou devolve o existente (enqueue é idempotente por jobId). */
    synchronized JSONObject createJob(JSONObject spec) {
        String id = spec.optString("jobId");
        JSONObject existing = jobs.optJSONObject(id);
        if (existing != null) return publicView(existing);
        long now = System.currentTimeMillis();
        JSONObject job;
        try { job = new JSONObject(spec.toString()); } catch (JSONException e) { throw new IllegalStateException(e); }
        put(job, "state", "queued");
        put(job, "attempts", 0);
        put(job, "createdAt", now);
        put(job, "updatedAt", now);
        put(jobs, id, job);
        changed(job);
        return publicView(job);
    }

    synchronized JSONObject getPublic(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        return j == null ? null : publicView(j);
    }

    synchronized JSONArray listPublic() {
        JSONArray out = new JSONArray();
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) out.put(publicView(jobs.optJSONObject(it.next())));
        return out;
    }

    /** Snapshot completo (com a especificação) pra o worker montar o request. */
    synchronized JSONObject snapshot(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        try { return j == null ? null : new JSONObject(j.toString()); } catch (JSONException e) { return null; }
    }

    /**
     * Reserva o próximo job que pode rodar agora (queued, ou waiting já
     * vencido, com o predecessor `after` concluído). Marca "sending" antes de
     * soltar o lock — dois drenos simultâneos nunca pegam o mesmo job.
     * Predecessor que falhou → este falha junto.
     */
    synchronized String claimNext(long now) {
        List<String> ids = new ArrayList<>();
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) ids.add(it.next());
        // Ordem de criação: o que foi escolhido primeiro sobe primeiro.
        ids.sort((a, b) -> Long.compare(jobs.optJSONObject(a).optLong("createdAt"), jobs.optJSONObject(b).optLong("createdAt")));
        for (String id : ids) {
            JSONObject j = jobs.optJSONObject(id);
            String st = j.optString("state");
            boolean due = "queued".equals(st) || ("waiting".equals(st) && j.optLong("nextAttemptAt") <= now);
            if (!due) continue;
            String after = j.optString("after", "");
            if (!after.isEmpty()) {
                JSONObject prev = jobs.optJSONObject(after);
                String ps = prev == null ? "done" : prev.optString("state");   // ack'ado = concluído
                if ("failed".equals(ps)) {
                    finish(j, "failed", 0, null, "o envio anterior desta cadeia falhou");
                    continue;
                }
                if (!"done".equals(ps)) continue;
            }
            if (now - j.optLong("createdAt") > GIVE_UP_MS) {
                finish(j, "failed", j.optInt("httpStatus"), null,
                    "desisti depois de 24 h tentando" + (j.has("error") ? " — " + j.optString("error") : ""));
                continue;
            }
            put(j, "state", "sending");
            put(j, "attempts", j.optInt("attempts") + 1);
            put(j, "updatedAt", now);
            j.remove("nextAttemptAt");
            changed(j);
            return id;
        }
        return null;
    }

    /** Menor nextAttemptAt entre os waiting (pra agendar o próximo dreno), ou 0. */
    synchronized long nextWakeAt() {
        long min = 0;
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) {
            JSONObject j = jobs.optJSONObject(it.next());
            if (!"waiting".equals(j.optString("state"))) continue;
            long t = j.optLong("nextAttemptAt");
            if (min == 0 || t < min) min = t;
        }
        return min;
    }

    synchronized boolean hasRunnable(long now) {
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) {
            String st = jobs.optJSONObject(it.next()).optString("state");
            if ("queued".equals(st)) return true;
        }
        long w = nextWakeAt();
        return w != 0 && w <= now;
    }

    /** Contagem pra notificação: [pendentes (queued+waiting+sending), em envio]. */
    synchronized int[] counts() {
        int pending = 0, sending = 0;
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) {
            String st = jobs.optJSONObject(it.next()).optString("state");
            if ("queued".equals(st) || "waiting".equals(st) || "sending".equals(st)) pending++;
            if ("sending".equals(st)) sending++;
        }
        return new int[] { pending, sending };
    }

    synchronized void progress(String jobId, long sent, long total) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j == null || !"sending".equals(j.optString("state"))) return;
        put(j, "sent", sent);
        put(j, "total", total);
        // Progresso não vai pro disco (seria uma gravação por fatia) — só pros ouvintes.
        JSONObject pub = publicView(j);
        for (Listener l : listeners) {
            try { l.onJobChanged(pub); } catch (Exception e) { Log.w(TAG, "listener", e); }
        }
    }

    synchronized void done(String jobId, int status, Object response) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j != null) finish(j, "done", status, response, null);
    }

    synchronized void failed(String jobId, int status, Object response, String error) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j != null) finish(j, "failed", status, response, error);
    }

    /** Falha transitória: agenda a próxima tentativa com recuo. */
    synchronized void retryLater(String jobId, int status, String error) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j == null) return;
        int attempts = Math.max(1, j.optInt("attempts"));
        long delay = BACKOFF_MS[Math.min(attempts - 1, BACKOFF_MS.length - 1)];
        long now = System.currentTimeMillis();
        put(j, "state", "waiting");
        put(j, "nextAttemptAt", now + delay);
        if (status > 0) put(j, "httpStatus", status); else j.remove("httpStatus");
        put(j, "error", error);
        put(j, "updatedAt", now);
        j.remove("sent");
        j.remove("total");
        changed(j);
    }

    /** Interrompido (worker parado pelo SO): volta pra fila sem gastar tentativa. */
    synchronized void requeue(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j == null || !"sending".equals(j.optString("state"))) return;
        put(j, "state", "queued");
        put(j, "attempts", Math.max(0, j.optInt("attempts") - 1));
        j.remove("sent");
        j.remove("total");
        changed(j);
    }

    private void finish(JSONObject j, String state, int status, Object response, String error) {
        put(j, "state", state);
        if (status > 0) put(j, "httpStatus", status);
        if (response != null) put(j, "response", response);
        if (error != null) put(j, "error", error); else j.remove("error");
        put(j, "updatedAt", System.currentTimeMillis());
        j.remove("nextAttemptAt");
        j.remove("sent");
        j.remove("total");
        changed(j);
    }

    /** Cancelado pelo JS: falha definitiva (o worker vê o estado e pula). */
    synchronized boolean cancel(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j == null) return false;
        String st = j.optString("state");
        if ("done".equals(st) || "failed".equals(st)) return false;
        finish(j, "failed", 0, null, "cancelled");
        return true;
    }

    /** ↻ do JS num job que falhou: volta pra fila do zero (tentativas e prazo de 24 h). */
    synchronized boolean retry(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j == null || !"failed".equals(j.optString("state"))) return false;
        long now = System.currentTimeMillis();
        put(j, "state", "queued");
        put(j, "attempts", 0);
        put(j, "createdAt", now);
        put(j, "updatedAt", now);
        for (String k : new String[] { "error", "httpStatus", "response", "nextAttemptAt", "sent", "total" }) j.remove(k);
        changed(j);
        return true;
    }

    synchronized boolean isCancelled(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        return j == null || !"sending".equals(j.optString("state"));
    }

    /** O JS registrou o resultado: some o job e os arquivos que só ele usava. */
    synchronized void ack(String jobId) {
        JSONObject j = jobs.optJSONObject(jobId);
        if (j == null) return;
        String st = j.optString("state");
        if (!"done".equals(st) && !"failed".equals(st)) return;   // ack só de estado final
        jobs.remove(jobId);
        deleteUnreferenced(sourcesOf(j));
        save();
    }

    synchronized void release(List<String> pickIds) {
        Set<String> refs = new HashSet<>();
        for (String id : pickIds) refs.add("pick:" + id);
        deleteUnreferenced(refs);
    }

    private static Set<String> sourcesOf(JSONObject job) {
        Set<String> s = new HashSet<>();
        JSONArray files = job.optJSONArray("files");
        if (files == null) return s;
        for (int i = 0; i < files.length(); i++) {
            JSONObject src = files.optJSONObject(i) == null ? null : files.optJSONObject(i).optJSONObject("source");
            if (src == null) continue;
            if (src.has("pickId")) s.add("pick:" + src.optString("pickId"));
            if (src.has("blobId")) s.add("blob:" + src.optString("blobId"));
        }
        return s;
    }

    /** Apaga picks/blobs que nenhum job restante referencia. */
    private void deleteUnreferenced(Set<String> candidates) {
        Set<String> live = new HashSet<>();
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) live.addAll(sourcesOf(jobs.optJSONObject(it.next())));
        for (String c : candidates) {
            if (live.contains(c)) continue;
            File f = c.startsWith("pick:") ? findPick(c.substring(5)) : blobFile(c.substring(5));
            if (f != null && f.exists() && !f.delete()) Log.w(TAG, "não apaguei " + f);
        }
    }

    // ===================== Arquivos =====================

    static boolean validId(String id) {
        return id != null && id.matches("[A-Za-z0-9-]{1,64}");
    }

    File blobFile(String blobId) {
        return validId(blobId) ? new File(blobs, blobId) : null;
    }

    /** picks/<pickId>.<ext> — a extensão é a do arquivo original. */
    File findPick(String pickId) {
        if (!validId(pickId)) return null;
        File[] found = picks.listFiles((dir, name) -> name.equals(pickId) || name.startsWith(pickId + "."));
        return found == null || found.length == 0 ? null : found[0];
    }

    File sourceFile(JSONObject source) {
        if (source == null) return null;
        if (source.has("pickId")) return findPick(source.optString("pickId"));
        if (source.has("blobId")) return blobFile(source.optString("blobId"));
        return null;
    }

    /** Varredura (no load do plugin): jobs finais velhos e arquivos órfãos velhos. */
    synchronized void sweep() {
        long now = System.currentTimeMillis();
        boolean dirty = false;
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) {
            JSONObject j = jobs.optJSONObject(it.next());
            String st = j.optString("state");
            if (("done".equals(st) || "failed".equals(st)) && now - j.optLong("updatedAt") > KEEP_FINAL_MS) {
                it.remove();
                dirty = true;
            }
        }
        if (dirty) save();
        Set<String> live = new HashSet<>();
        for (Iterator<String> it = jobs.keys(); it.hasNext(); ) live.addAll(sourcesOf(jobs.optJSONObject(it.next())));
        sweepDir(picks, "pick:", live, now);
        sweepDir(blobs, "blob:", live, now);
    }

    private static void sweepDir(File dir, String prefix, Set<String> live, long now) {
        File[] fs = dir.listFiles();
        if (fs == null) return;
        for (File f : fs) {
            String id = f.getName().contains(".") ? f.getName().substring(0, f.getName().indexOf('.')) : f.getName();
            if (live.contains(prefix + id)) continue;
            if (now - f.lastModified() > KEEP_ORPHAN_MS && !f.delete()) Log.w(TAG, "não apaguei " + f);
        }
    }
}
