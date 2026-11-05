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
  if (message.method === 'Runtime.executionContextsCleared') errors.length = 0;
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
const distance = (a,b) => Math.hypot(a[0]-b[0],a[2]-b[2]);
async function click(selector) {
  const p=await evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest',inline:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  await send('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',clickCount:1});
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',...p,button:'left',clickCount:1});
  await wait(100);
}
async function key(code,ms) {
  await send('Input.dispatchKeyEvent',{type:'keyDown',code,key:code.startsWith('Key')?code.slice(3).toLowerCase():code});
  await wait(ms);await send('Input.dispatchKeyEvent',{type:'keyUp',code,key:code.startsWith('Key')?code.slice(3).toLowerCase():code});
}
async function screenshot(suffix) {const {data}=await send('Page.captureScreenshot',{format:'png'});writeFileSync(`${output}_${suffix}.png`,Buffer.from(data,'base64'));}
try {
  await send('Runtime.enable'); await send('Page.bringToFront');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await evaluate('window.__navigationPending = true');
  await send('Page.navigate',{url});
  let loaded=false; for(let i=0;i<120;i++){if(await evaluate('window.__navigationPending !== true && window.libraryPreview?.ready===true')){loaded=true;break;}await wait(500);}
  if(!loaded)throw new Error('Preview failed to load');
  await send('Page.bringToFront');
  const initial=await state();checks.webgpu=initial.backend==='WebGPU';
  checks.referenceDimensions=Math.abs(initial.roomDimensions.width-8.0)<1e-5&&Math.abs(initial.roomDimensions.apex-6.2)<1e-5;
  await screenshot('welcome'); await click('#enter'); checks.pointerLock=(await state()).pointerLocked;
  for(const code of ['KeyW','KeyS','KeyA','KeyD']){const p=(await state()).position;await key(code,350);checks[code]=distance(p,(await state()).position)>.25;}
  const rotation=(await state()).rotation;await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:720,y:500,movementX:90,movementY:-40});await wait(100);checks.mouseLook=JSON.stringify(rotation)!==JSON.stringify((await state()).rotation);
  await evaluate('document.exitPointerLock()'); await wait(100);
  await click('#library-view');await click('canvas');await key('KeyW',1800);
  checks.shelfCollision=Math.abs((await state()).position[2]+3.18)<.04;
  await key('KeyS',650);
  await evaluate('window.savedOpen=window.open;window.open=url=>{window.testOpenedURL=url;return null}');
  await key('KeyE',50); checks.libraryLink=await evaluate('window.testOpenedURL === "https://library.xrguild.org/"');
  await evaluate('window.open=window.savedOpen;delete window.savedOpen');
  await click('#meeting-view');checks.furniture=(await state()).meetingLayout;
  await click('canvas');await key('KeyW',1800);checks.furnitureCollision=Math.hypot((await state()).position[0],(await state()).position[2])>=2.149;
  await click('#furniture');checks.furnitureHides=!(await state()).meetingLayout;
  await click('#door');await wait(1200);checks.doorOpens=(await state()).doorOpen>.98;
  await click('#door');await wait(1200);checks.doorCloses=(await state()).doorOpen<.02;
  const eyes=[];for(const id of ['#reset','#ceiling','#detail','#library-view','#meeting-view']){await click(id);eyes.push((await state()).position[1]);}
  checks.eyeHeightConsistent=eyes.every(y=>y===1.7);
  await click('#furniture');await click('#detail');await screenshot('craft');
  await click('#ceiling');await screenshot('fresco');
  await click('#read-labels'); checks.labels=await evaluate('document.getElementById("labels-dialog").open && document.querySelectorAll(".topic-list a").length===9');await screenshot('labels');await click('#close-labels');
  await click('#reset');await screenshot('entrance');
  const report={url,environment:'Chrome desktop, native CDP mouse and keyboard',initial,final:await state(),modelBounds:await evaluate('window.libraryModelBounds'),checks,errors,pass:Object.values(checks).every(Boolean)&&errors.length===0};
  writeFileSync(`${output}.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));if(!report.pass)process.exitCode=1;
}finally{ws.close();}
