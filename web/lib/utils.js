// Pedal Hidrográfico — utility helpers
// First ES module extracted from app.js. Pure functions and the toast UI;
// no state coupling to other subsystems.

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
}

export function escapeXml(s) {
  return String(s).replace(/[<>&"']/g, (c) =>
    ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[c],
  );
}

// hh:mm:ss formatter for the trace metrics + tooltip lines.
export function formatHMS(sec) {
  const total = Math.max(0, Math.round(sec));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n) => String(n).padStart(2, '0');
  if (h > 0) return `${h}h ${pad(m)}m ${pad(s)}s`;
  return `${m}m ${pad(s)}s`;
}

// Run an async fn over an array with at most `limit` calls in flight at once.
export async function mapConcurrent(items, limit, fn) {
  const out = new Array(items.length);
  let next = 0;
  async function worker() {
    while (true) {
      const i = next++;
      if (i >= items.length) return;
      out[i] = await fn(items[i], i);
    }
  }
  const n = Math.min(limit, items.length);
  await Promise.all(Array.from({ length: n }, () => worker()));
  return out;
}

// Earth-surface distance (haversine) in metres. Used by the route stats
// computation in the build script and by the editor's segment finder.
export function haversineMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const rad = (d) => (d * Math.PI) / 180;
  const dLat = rad(lat2 - lat1);
  const dLon = rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Lightweight non-blocking toast for one-shot status messages. The DOM
// element is read once and cached; subsequent calls reuse the same node.
let toastEl = null;
let toastTimer = null;
export function showToast(msg, ms = 3500) {
  if (!toastEl) toastEl = document.getElementById('toast');
  if (!toastEl) return;
  // Tornar visível ANTES de escrever o texto: o #toast é um live region
  // (role=status / aria-live=polite); enquanto [hidden] ele fica fora da
  // árvore de acessibilidade, então mudar o texto com ele oculto não é
  // anunciado. Desocultar primeiro garante que a mudança vire um update.
  toastEl.hidden = false;
  toastEl.classList.remove('fade');
  toastEl.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.add('fade');
    setTimeout(() => { toastEl.hidden = true; }, 300);
  }, ms);
}

// Salva/compartilha um arquivo gerado no cliente (GPX, QR, ZIP, JSON…) — o
// ÚNICO caminho de download do app. No celular (ponteiro grosso) e no shell
// nativo, com Web Share nível 2, abre a folha de compartilhar do sistema: no
// iPhone é por ela que o arquivo chega no WhatsApp, Garmin/Komoot, Instagram,
// Fotos ou "Salvar em Arquivos" (o <a download> caía em Arquivos › Downloads,
// e no shell Capacitor não salvava NADA — o WKWebView do Capacitor não trata
// download). No desktop (e sem Web Share) segue o <a download> de sempre.
// Chame DENTRO do gesto do usuário e sem await antes: o navigator.share
// consome a ativação transitória (5 s no WebKit) — sem ela cai no download.
// Devolve 'shared' | 'downloaded' | 'cancelled' (o usuário fechou a folha);
// quem chama só mostra o aviso de sucesso depois disso.
export async function saveFile(blob, filename, { type } = {}) {
  const mime = type || blob.type || 'application/octet-stream';
  let coarse = false;
  try { coarse = window.matchMedia('(pointer: coarse)').matches; } catch (_) { /* sem matchMedia */ }
  const cap = window.Capacitor;
  const native = !!(cap && typeof cap.isNativePlatform === 'function' && cap.isNativePlatform());
  if ((coarse || native) && typeof navigator.share === 'function' && typeof File === 'function') {
    let data = null;
    try { data = { files: [new File([blob], filename, { type: mime })] }; } catch (_) { data = null; }
    // Sem ativação (o arquivo levou mais que a janela do gesto pra ficar
    // pronto), o share rejeitaria — vai direto pro download.
    const active = !navigator.userActivation || navigator.userActivation.isActive;
    let shareable = false;
    try { shareable = !!data && active && (!navigator.canShare || navigator.canShare(data)); } catch (_) { shareable = false; }
    if (shareable) {
      try {
        await navigator.share(data);
        return 'shared';
      } catch (err) {
        if (err && err.name === 'AbortError') return 'cancelled';
        // NotAllowedError (gesto perdido), TypeError (tipo recusado)… → download
      }
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revogar cedo é seguro (o WebKit estende a vida do blob: durante a checagem
  // de navegação do download), mas não há pressa.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
  return 'downloaded';
}

// localStorage with try/catch so private-mode / quota-exceeded errors don't
// crash flow. Returns null on read failure, false on write failure, true on
// successful write.
export const storage = {
  get(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); return true; } catch { return false; }
  },
  remove(key) {
    try { localStorage.removeItem(key); return true; } catch { return false; }
  },
};
