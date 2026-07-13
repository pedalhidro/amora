// pHash calculado pelo NAVEGADOR DE VERDADE (Chromium via Playwright).
//
// Por que não em Python: o pHash começa com `drawImage(bitmap, 0, 0, 32, 32)`
// num canvas, e o resultado depende do RESAMPLER do navegador (Skia), da
// conversão do perfil de cor pra sRGB e da orientação EXIF que o
// `createImageBitmap` aplica sozinho. Reimplementar isso é adivinhar: uma
// porta cuidadosa em NumPy (bilinear do canvas + conversão de gamut ICC)
// reproduziu só **78%** dos hashes de 352 fotos já no acervo — ou seja, 1 em
// cada 5 fotos ganharia uma IRI DIFERENTE da que o navegador dá pra mesma
// foto, duplicando o acervo em vez de deduplicá-lo. E o pHash **é** a
// identidade da mídia (`med:<phash16>`).
//
// Aqui não se emula nada: roda-se o MESMO código do web/upload_images.html,
// no mesmo motor. Paridade por construção.
//
// Uso:
//   node scripts/phash-browser.mjs arquivo1.jpg arquivo2.heic ...
//   echo -e "a.jpg\nb.jpg" | node scripts/phash-browser.mjs --stdin
//
// Saída: uma linha por arquivo, "<phash16>\t<caminho>" (ou "ERRO\t<caminho>").
import { readFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { createRequire } from 'node:module';

// O amora não tem build step nem dependências de runtime em JS, e não é por
// causa de um script de preparo de dados que vai passar a ter. O playwright é
// resolvido em tempo de execução: do node_modules local, se existir; senão do
// caminho em PLAYWRIGHT_PATH (dá pra apontar pro cache do npx, sem instalar
// nada no repo).
const require = createRequire(import.meta.url);
function carregaChromium() {
  const tentativas = ['playwright', 'playwright-core'];
  if (process.env.PLAYWRIGHT_PATH) {
    tentativas.unshift(`${process.env.PLAYWRIGHT_PATH}/playwright`,
                       `${process.env.PLAYWRIGHT_PATH}/playwright-core`);
  }
  for (const t of tentativas) {
    try { return require(t).chromium; } catch { /* tenta o próximo */ }
  }
  console.error(
    'playwright não encontrado.\n\n'
    + 'Este script roda o pHash no motor do navegador DE VERDADE — é a única\n'
    + 'forma de a IRI da mídia bater com a que o upload_images.html geraria.\n\n'
    + 'Opções:\n'
    + '  npx playwright install chromium   # baixa o navegador\n'
    + '  PLAYWRIGHT_PATH=$(find ~/.npm/_npx -maxdepth 2 -name node_modules | head -1) \\\n'
    + '    node scripts/phash-browser.mjs ...\n');
  process.exit(3);
}
const chromium = carregaChromium();

// ── O pHash, copiado VERBATIM de web/upload_images.html ────────────────────
// Se aquele arquivo mudar o algoritmo, este tem que mudar junto — são a mesma
// identidade. (Ver o comentário do pHash lá: Hacker Factor / Zauner.)
const PHASH_JS = `
function dct1d(input, N) {
  const out = new Float32Array(N);
  for (let k = 0; k < N; k++) {
    let sum = 0;
    const f = Math.PI * k / (2 * N);
    for (let n = 0; n < N; n++) sum += input[n] * Math.cos((2 * n + 1) * f);
    out[k] = sum;
  }
  return out;
}
function pHashFromRgba(data, N) {
  const m = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) {
    m[i] = data[i*4]*0.299 + data[i*4+1]*0.587 + data[i*4+2]*0.114;
  }
  const tmp = new Float32Array(N * N);
  for (let y = 0; y < N; y++) {
    const out = dct1d(m.subarray(y * N, (y + 1) * N), N);
    for (let x = 0; x < N; x++) tmp[y * N + x] = out[x];
  }
  const dct = new Float32Array(N * N);
  const col = new Float32Array(N);
  for (let x = 0; x < N; x++) {
    for (let y = 0; y < N; y++) col[y] = tmp[y * N + x];
    const out = dct1d(col, N);
    for (let y = 0; y < N; y++) dct[y * N + x] = out[y];
  }
  const block = new Float32Array(64);
  for (let y = 0; y < 8; y++)
    for (let x = 0; x < 8; x++) block[y * 8 + x] = dct[y * N + x];
  const sorted = Array.from(block.slice(1)).sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  let hex = '';
  for (let row = 0; row < 8; row++) {
    let byte = 0;
    for (let col2 = 0; col2 < 8; col2++) {
      byte = (byte << 1) | (block[row * 8 + col2] > median ? 1 : 0);
    }
    hex += byte.toString(16).padStart(2, '0');
  }
  return hex;
}
window.__phashDeBytes = async (bytes, mime) => {
  const blob = new Blob([new Uint8Array(bytes)], { type: mime });
  // createImageBitmap é o mesmo que o form usa: aplica orientação EXIF e
  // converte o perfil de cor — as duas coisas que uma porta em Python erra.
  const bmp = await createImageBitmap(blob);
  const N = 32;
  const c = document.createElement('canvas');
  c.width = N; c.height = N;
  const ctx = c.getContext('2d');
  ctx.drawImage(bmp, 0, 0, N, N);
  const data = ctx.getImageData(0, 0, N, N).data;
  bmp.close();
  return pHashFromRgba(data, N);
};
`;

const MIME = {
  jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp',
  gif: 'image/gif', heic: 'image/heic', heif: 'image/heif', tif: 'image/tiff',
  tiff: 'image/tiff', avif: 'image/avif',
};

async function lerCaminhos() {
  const args = process.argv.slice(2);
  if (!args.includes('--stdin')) return args;
  const rl = createInterface({ input: process.stdin });
  const out = [];
  for await (const l of rl) if (l.trim()) out.push(l.trim());
  return out;
}

const caminhos = await lerCaminhos();
if (!caminhos.length) {
  console.error('uso: node scripts/phash-browser.mjs <arquivos...> | --stdin');
  process.exit(2);
}

const browser = await chromium.launch();
const page = await browser.newPage();
await page.addScriptTag({ content: PHASH_JS });

for (const p of caminhos) {
  try {
    const buf = await readFile(p);
    const ext = p.split('.').pop().toLowerCase();
    const hash = await page.evaluate(
      ([bytes, mime]) => window.__phashDeBytes(bytes, mime),
      [Array.from(buf), MIME[ext] || 'application/octet-stream'],
    );
    process.stdout.write(`${hash}\t${p}\n`);
  } catch (e) {
    process.stdout.write(`ERRO\t${p}\t${e.message}\n`);
  }
}

await browser.close();
