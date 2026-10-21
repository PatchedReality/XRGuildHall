#!/usr/bin/env node
// Photon voice load test (Tier 2 in docs/PHOTON-VOICE-SPIKE.md): K headless Chromium instances, each running bots.html with
// --per-page Photon clients (bots.html), each pushing a speech clip into its outgoing voice.
//
//   node scripts/load/run-bots.mjs --room loadtest-abc --total 19 [--per-page 5] [--duration 300] [--mic 1] [--stage]
//                                  [--base http://localhost:5173] [--wav speech.wav] [--headed] [--region us]
//
// Without --base it starts the Vite dev server itself (which reads VITE_PHOTON_APP_ID from .env.local); VITE_LOG=info shows its log.
// Without --wav the bots synthesise a speech-like clip. Needs only Node and Playwright's Chromium (npx playwright install chromium).
import { chromium } from 'playwright';
import { createServer } from 'vite';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values: a } = parseArgs({
  options: {
    room: { type: 'string' }, total: { type: 'string', default: '19' }, 'per-page': { type: 'string', default: '1' },
    duration: { type: 'string', default: '300' }, mic: { type: 'string', default: '1' }, stage: { type: 'boolean', default: false },
    base: { type: 'string' }, wav: { type: 'string' }, headed: { type: 'boolean', default: false }, region: { type: 'string' },
  },
});
if (!a.room || a.room === 'guild-hall') { console.error('Pass --room <private room name>; the live room "guild-hall" is refused.'); process.exit(2); }
const total = Math.max(1, +a.total), perPage = Math.max(1, +a['per-page']), duration = Math.max(10, +a.duration);
const instances = Math.ceil(total / perPage);

let server = null, base = a.base;
if (!base) {
  server = await createServer({ root: fileURLToPath(new URL('../..', import.meta.url)), logLevel: process.env.VITE_LOG ?? 'warn', server: { port: 5199, open: false, hmr: false, watch: null } });
  await server.listen();
  base = server.resolvedUrls.local[0];
}
const browsers = [];
let stopping = false;
async function stop(code = 0) {
  if (stopping) return; stopping = true;
  await Promise.allSettled(browsers.map(b => b.close()));
  await server?.close();
  process.exit(code);
}
process.on('SIGINT', () => { console.log('\nStopping…'); stop(0); });
process.on('unhandledRejection', e => { console.error(e?.message ?? e); stop(1); });

console.log(`${total} bots in room "${a.room}": ${instances} Chromium instance(s) × up to ${perPage} per page, for ${duration} s. Base ${base}`);
const pages = [];
for (let k = 0; k < instances; k++) {
  const n = Math.min(perPage, total - k * perPage);
  const browser = await chromium.launch({
    headless: !a.headed,
    args: ['--autoplay-policy=no-user-gesture-required'],
  });
  browsers.push(browser);
  const page = await browser.newPage();
  if (a.wav) await page.route('**/bot-clip', r => r.fulfill({ path: resolve(a.wav) }));
  page.on('console', m => { if (m.type() === 'error' || m.text().startsWith('[bots]')) console.log(`  [page ${k}] ${m.text()}`); });
  page.on('pageerror', e => console.log(`  [page ${k}] ${e.message}`));
  const q = new URLSearchParams({ room: a.room, bots: String(n), first: String(k * perPage), mic: a.mic, ...(a.stage && k === 0 ? { stage: '1' } : {}), ...(a.region ? { region: a.region } : {}), ...(a.wav ? { clip: 'bot-clip' } : {}) });
  await page.goto(new URL(`bots.html?${q}`, base).href);
  pages.push(page);
}

const status = async () => {
  const s = await Promise.all(pages.map(p => p.evaluate(() => window.__bots ?? { joined: 0, errors: [] }).catch(() => ({ joined: 0, errors: ['page closed'] }))));
  return { joined: s.reduce((n, x) => n + x.joined, 0), decoded: s.reduce((n, x) => n + (x.framesDecoded ?? 0), 0), sent: s.reduce((n, x) => n + (x.framesSent ?? 0), 0), errors: s.flatMap(x => x.errors) };
};
let lastDecoded = 0, lastSent = 0;
const until = Date.now() + duration * 1000;
const timer = setInterval(async () => {
  const s = await status();
  // bots decode each other's voices like any client, so this confirms audio is flowing through Photon
  const rate = Math.round((s.decoded - lastDecoded) / 10), sent = Math.round((s.sent - lastSent) / 10); lastDecoded = s.decoded; lastSent = s.sent;
  console.log(`${new Date().toISOString().slice(11, 19)}  joined ${s.joined}/${total}  voice frames sent ${sent}/s, decoded by bots ${rate}/s${s.errors.length ? `  errors: ${s.errors.join('; ')}` : ''}  (${Math.round((until - Date.now()) / 1000)} s left)`);
  if (Date.now() > until) { clearInterval(timer); stop(0); }
}, 10000);
