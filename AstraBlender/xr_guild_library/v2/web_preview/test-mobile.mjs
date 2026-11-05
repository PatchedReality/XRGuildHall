// Native multi-touch input through Chrome DevTools; no input handlers are mocked.
// Use a dedicated browser session; do not run other automation commands in it during this test.
// node test-mobile.mjs <browser-websocket-url> <preview-url> <evidence-prefix>
import { writeFileSync } from 'node:fs';
const [browserURL, url, output] = process.argv.slice(2);
const endpoint = new URL(browserURL);
const pages = await (await fetch(`http://${endpoint.host}/json/list`)).json();
const page = pages.find(p => p.type === 'page' && p.url.startsWith('http'));
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let sequence = 0;
const pending = new Map();
const errors = [];
ws.onmessage = ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
  if (!message.id) return;
  const request = pending.get(message.id); if (!request) return; pending.delete(message.id); clearTimeout(request.timer);
  if (message.error) request.reject(new Error(JSON.stringify(message.error))); else request.resolve(message.result);
};
function send(method, params = {}) {
  return new Promise((resolve, reject) => { const id = ++sequence; const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method} ${JSON.stringify(params)}`)); }, 20000); pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params })); });
}
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
const wait = ms => new Promise(r => setTimeout(r, ms));
const state = () => evaluate('JSON.parse(JSON.stringify(window.libraryPreview))');
const checks = {};
const distance = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
async function center(selector) {
  return evaluate(`(() => { const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}; })()`);
}
const point = (id, p) => ({ id, x: p.x, y: p.y, radiusX: 8, radiusY: 8, force: 1 });
const touch = (type, points) => send('Input.dispatchTouchEvent', { type, touchPoints: points });
async function tap(selector) { const p = point(9, await center(selector)); await touch('touchStart', [p]); await touch('touchEnd', []); await wait(120); }
async function reset() { await tap('#reset'); await wait(100); }
async function stick(dx, dy) {
  const c = await center('#joystick'); const p = point(1, c);
  await touch('touchStart', [p]); p.x += dx; p.y += dy;
  await touch('touchMove', [p]); return p;
}
async function screenshot(suffix) {
  const { data } = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(`${output}_${suffix}.png`, Buffer.from(data, 'base64'));
}
try {
  await send('Runtime.enable');
  await send('Page.bringToFront');
  await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url });
  let loaded = false;
  for (let i = 0; i < 120; i++) { if (await evaluate('window.libraryPreview?.ready === true')) { loaded = true; break; } await wait(500); }
  if (!loaded) throw new Error('Preview did not become ready');
  await screenshot('welcome');
  await tap('#enter');
  const initial = await state(); checks.touchEntry = initial.touchMode && initial.touchActive && !initial.pointerLocked;
  for (const [name, dx, dy] of [['forward',0,-36],['backward',0,36],['left',-36,0],['right',36,0]]) {
    await reset(); const before = await state(); await stick(dx,dy); await wait(400); await touch('touchEnd', []); const after = await state();
    console.log(`Checked ${name}`);
    checks[name] = distance(before.position, after.position) > .25;
  }
  console.log('Checking simultaneous touches');
  await reset(); const before = await state();
  const p1 = await stick(0,-36); await wait(250);
  const p2 = point(2,{x:290,y:330}); await touch('touchStart',[p1,p2]);
  p2.x -= 45; p2.y += 25; await touch('touchMove',[p1,p2]); await wait(300);
  const both = await state(); checks.simultaneousMoveLook = distance(before.position,both.position)>.4 && JSON.stringify(before.rotation)!==JSON.stringify(both.rotation);
  await touch('touchMove',[p1]); const oneLeft = await state(); await wait(300);
  checks.liftingLookKeepsWalking = distance(oneLeft.position,(await state()).position)>.2;
  await touch('touchEnd',[]); const released = await state(); await wait(300);
  checks.releaseStopsWalking = distance(released.position,(await state()).position)<.04;
  await stick(0,-36); await wait(150); await touch('touchCancel',[]); const cancelled=await state(); await wait(250);
  checks.cancelStopsWalking = distance(cancelled.position,(await state()).position)<.04 && cancelled.touchMove.z===0;
  await reset(); const ordinary=(await state()).position; await stick(0,-36); await wait(400); await touch('touchEnd',[]); const walkDistance=distance(ordinary,(await state()).position);
  await reset(); await tap('#touch-speed'); const quick=(await state()).position; await stick(0,-36); await wait(400); await touch('touchEnd',[]);
  checks.fasterWalking=distance(quick,(await state()).position)>walkDistance*1.4; await tap('#touch-speed');
  console.log('Checking collision and interactions');
  await reset(); await stick(0,-36); await wait(5100); await touch('touchEnd',[]);
  checks.collision=Math.abs((await state()).position[2]+3.23)<.04;
  await stick(0,36); await wait(650); await touch('touchEnd',[]); await wait(100);
  checks.libraryButton = await evaluate('!document.getElementById("touch-interact").disabled && document.getElementById("touch-interact").textContent.includes("Search")');
  await evaluate('window.savedOpen = window.open; window.open = url => { window.testOpenedURL = url; return null; }');
  await tap('#touch-interact');
  checks.libraryLink=await evaluate('window.testOpenedURL === "https://library.xrguild.org/"');
  await evaluate('window.open = window.savedOpen; delete window.savedOpen');
  checks.linkPauses=!(await state()).touchActive;
  await tap('#enter'); await reset();
  // Turn toward the meeting door with four ordinary screen-width swipes.
  for (let i=0;i<4;i++) {
    const finger=point(2,{x:290,y:330}); await touch('touchStart',[finger]);
    finger.x-=Math.PI/.004/4; await touch('touchMove',[finger]); await touch('touchEnd',[]);
  }
  await wait(100);
  checks.doorButton=await evaluate('!document.getElementById("touch-interact").disabled && document.getElementById("touch-interact").textContent.includes("doors")');
  await tap('#touch-interact'); await wait(1200); checks.touchOpensDoor=(await state()).doorOpen>.98;
  await tap('#touch-interact'); await wait(1200); checks.touchClosesDoor=(await state()).doorOpen<.02;
  await reset();
  await tap('#pause-touch'); checks.pause=!(await state()).touchActive && await evaluate('document.getElementById("touch-controls").hidden');
  await tap('#enter'); checks.resume=(await state()).touchActive;
  console.log('Checking layouts and interruptions');
  await screenshot('portrait');
  await stick(0,-36);
  await send('Emulation.setDeviceMetricsOverride',{width:844,height:390,deviceScaleFactor:2,mobile:true}); await wait(200);
  await touch('touchEnd',[]);
  checks.rotationClearsMovement=(await state()).touchMove.z===0;
  const still=(await state()).position; await wait(250); checks.rotationStopsWalking=distance(still,(await state()).position)<.04;
  await screenshot('landscape');
  checks.controlsFit=await evaluate(`['#joystick','#touch-interact','#touch-speed','#pause-touch','.toolbar'].every(s=>{const r=document.querySelector(s).getBoundingClientRect();return r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;})`);
  await stick(0,-36); await evaluate('window.dispatchEvent(new Event("blur"))'); await touch('touchEnd',[]);
  checks.blurPauses=!(await state()).touchActive && (await state()).touchMove.z===0;
  const report={url,environment:'Chrome mobile emulation with native CDP multi-touch input; no physical phone test',initial,checks,errors,pass:Object.values(checks).every(Boolean)&&errors.length===0};
  writeFileSync(`${output}.json`,JSON.stringify(report,null,2)+'\n'); console.log(JSON.stringify(report,null,2));
  if (!report.pass) process.exitCode=1;
} finally { ws.close(); }
