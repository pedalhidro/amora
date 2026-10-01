package co.pedalhidrografi.amora.upload;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Um POST multipart/form-data montado a partir do job: campos de texto (ttl,
 * id, staged…) + arquivos lidos do disco em fluxo — nada do corpo fica inteiro
 * na memória. Mesmo formato que o FormData do subir.html manda hoje.
 */
final class Uploader {

    interface Progress {
        void on(long sent, long total);
    }

    interface Stop {
        boolean stopped();
    }

    static final class Result {
        int status;            // 0 = falha de transporte (sem resposta)
        Object body;           // JSON da resposta, ou {raw: "..."}
        String error;          // mensagem de transporte, se status == 0
    }

    private static final int CHUNK = 64 * 1024;
    private static final int MAX_RESPONSE = 1 << 20;

    private static String quote(String s) {
        // Como os navegadores: aspas e quebras viram percent-encoding.
        return s.replace("\"", "%22").replace("\r", "%0D").replace("\n", "%0A");
    }

    static Result post(JSONObject job, Store store, String userAgent, Progress progress, Stop stop) {
        Result r = new Result();
        String boundary = "----amora" + UUID.randomUUID().toString().replace("-", "");
        List<Object> parts = new ArrayList<>();   // byte[] (cabeçalhos/campos) ou File
        long total = 0;
        try {
            JSONObject fields = job.optJSONObject("fields");
            if (fields != null) {
                for (Iterator<String> it = fields.keys(); it.hasNext(); ) {
                    String k = it.next();
                    byte[] b = ("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + quote(k) + "\"\r\n\r\n"
                        + fields.optString(k) + "\r\n").getBytes(StandardCharsets.UTF_8);
                    parts.add(b);
                    total += b.length;
                }
            }
            JSONArray files = job.optJSONArray("files");
            for (int i = 0; files != null && i < files.length(); i++) {
                JSONObject f = files.getJSONObject(i);
                File src = store.sourceFile(f.optJSONObject("source"));
                if (src == null || !src.exists()) {
                    r.status = -1;
                    r.error = "arquivo do envio sumiu do aparelho (" + f.optString("field") + ")";
                    return r;
                }
                byte[] head = ("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + quote(f.optString("field"))
                    + "\"; filename=\"" + quote(f.optString("filename")) + "\"\r\nContent-Type: "
                    + f.optString("contentType", "application/octet-stream") + "\r\n\r\n").getBytes(StandardCharsets.UTF_8);
                parts.add(head);
                parts.add(src);
                parts.add("\r\n".getBytes(StandardCharsets.UTF_8));
                total += head.length + src.length() + 2;
            }
            byte[] end = ("--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8);
            parts.add(end);
            total += end.length;
        } catch (Exception e) {
            r.status = -1;
            r.error = "job malformado: " + e.getMessage();
            return r;
        }

        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(job.optString("url")).openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setInstanceFollowRedirects(false);
            conn.setFixedLengthStreamingMode(total);
            conn.setConnectTimeout(30_000);
            // O servidor valida (SHACL) e grava no bucket depois de receber tudo.
            conn.setReadTimeout(180_000);
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            conn.setRequestProperty("Accept", "application/json");
            conn.setRequestProperty("User-Agent", userAgent);
            long sent = 0, lastReport = 0;
            byte[] buf = new byte[CHUNK];
            try (OutputStream out = conn.getOutputStream()) {
                for (Object p : parts) {
                    if (stop.stopped()) throw new StoppedException();
                    if (p instanceof byte[]) {
                        out.write((byte[]) p);
                        sent += ((byte[]) p).length;
                        continue;
                    }
                    try (InputStream in = new FileInputStream((File) p)) {
                        int n;
                        while ((n = in.read(buf)) > 0) {
                            if (stop.stopped()) throw new StoppedException();
                            out.write(buf, 0, n);
                            sent += n;
                            if (sent - lastReport >= 256 * 1024) {
                                lastReport = sent;
                                progress.on(sent, total);
                            }
                        }
                    }
                }
            }
            progress.on(total, total);
            r.status = conn.getResponseCode();
            InputStream body = r.status >= 400 ? conn.getErrorStream() : conn.getInputStream();
            r.body = parseBody(body);
        } catch (StoppedException e) {
            r.status = 0;
            r.error = "interrompido";
        } catch (IOException e) {
            r.status = 0;
            r.error = e.getClass().getSimpleName() + (e.getMessage() != null ? ": " + e.getMessage() : "");
        } finally {
            if (conn != null) conn.disconnect();
        }
        return r;
    }

    private static Object parseBody(InputStream in) {
        if (in == null) return null;
        try (InputStream s = in) {
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            byte[] b = new byte[8192];
            int n;
            while ((n = s.read(b)) > 0 && bo.size() < MAX_RESPONSE) bo.write(b, 0, n);
            String text = bo.toString("UTF-8");
            try {
                return new JSONObject(text);
            } catch (Exception notJson) {
                // Ex.: página HTML de bloqueio da Cloudflare — guarda o começo pro diagnóstico.
                return new JSONObject().put("raw", text.length() > 300 ? text.substring(0, 300) : text);
            }
        } catch (Exception e) {
            return null;
        }
    }

    /** Distingue o "parar" do worker de uma falha de rede. */
    static final class StoppedException extends IOException {}
}
