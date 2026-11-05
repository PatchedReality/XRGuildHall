import * as THREE from 'three/webgpu';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { pass, renderOutput } from 'three/tsl';
import { denoise } from 'three/addons/tsl/display/DenoiseNode.js';
import { fxaa } from 'three/addons/tsl/display/FXAANode.js';
import { ao } from 'three/addons/tsl/display/GTAONode.js';
import './style.css';

const $ = (id) => document.getElementById(id);
const touchMode = matchMedia('(any-pointer: coarse)').matches || navigator.maxTouchPoints > 0;
document.body.classList.toggle('touch-device', touchMode);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xa4bec6);
scene.fog = new THREE.Fog(0xa4bec6, 45, 180);
const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.035, 250);
const renderer = new THREE.WebGPURenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = .80;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.BasicShadowMap;
renderer.domElement.tabIndex = 0;
renderer.domElement.setAttribute('aria-label', touchMode ? 'Library. Enter to walk with the thumbstick and swipe to look.' : 'Library. Click Enter library to use WASD and mouse look.');
$('viewport').appendChild(renderer.domElement);
const controls = new PointerLockControls(camera, renderer.domElement);
controls.pointerSpeed = .65;
controls.minPolarAngle = .08;
controls.maxPolarAngle = Math.PI - .08;
let pipeline;
let ready = false, furniture, hinges = [], doorTarget = 0, doorAngle = 0, locked = false;
let lookPointer = null, lastPointer = { x: 0, y: 0 };
let touchActive = false, joystickPointer = null, touchFast = false;
const touchMove = { x: 0, z: 0 };
const keys = new Set();
const originalHinges = new Map();
const presets = {
  entrance: { pos: [0, 1.7, 3.25], target: [0, 2.55, -1.5] },
  ceiling: { pos: [0, 1.7, .8], target: [0, 6.2, 0] },
  detail: { pos: [1.15, 2.65, 1.9], target: [3.7, 3.25, -.4] },
};
function setView(name) {
  releaseMouse(); clearInput();
  camera.position.fromArray(presets[name].pos);
  camera.lookAt(...presets[name].target);
  camera.updateMatrixWorld();
}
setView('entrance');

// A diffuse sky environment gives polished brass something continuous to reflect.
// No white rectangular light cards appear in the transparent windows.
function skyEnvironment() {
  const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 256;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, '#c3d6e6'); grad.addColorStop(.42, '#e9dfc2');
  grad.addColorStop(.56, '#9ea899'); grad.addColorStop(1, '#202d21');
  ctx.fillStyle = grad; ctx.fillRect(0, 0, 512, 256);
  const texture = new THREE.CanvasTexture(canvas);
  texture.mapping = THREE.EquirectangularReflectionMapping; texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
scene.environment = skyEnvironment(); scene.environmentIntensity = .22;
scene.add(new THREE.HemisphereLight(0xe2edee, 0x3b3922, .16));
const bounce = new THREE.PointLight(0xffdb9e, 8, 13, 2); bounce.position.set(0, 4.5, 0); scene.add(bounce);
const ceilingWash = new THREE.PointLight(0xffedc9, 5, 10, 2); ceilingWash.position.set(0, 3.3, .2); scene.add(ceilingWash);
for (let i = 0; i < 6; i++) {
  const a = i * Math.PI / 3;
  const light = new THREE.PointLight(0xd6ecff, 6, 8, 2);
  light.position.set(3.35 * Math.cos(a), 2.8, -3.35 * Math.sin(a)); scene.add(light);
}
// One directional light provides recess shadows without a shadow map per lamp.
const sun = new THREE.DirectionalLight(0xffe3b3, 1.8);
sun.position.set(7, 8, 5); sun.target.position.set(-1, 0, -1);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 7, bottom: -6, near: .1, far: 25 });
sun.shadow.bias = -.00015; sun.shadow.normalBias = .013;
scene.add(sun, sun.target);

// Optional landscape context is separate from the downloadable room GLB.
const land = new THREE.Group(); land.name = 'Preview landscape';
const water = new THREE.Mesh(new THREE.CircleGeometry(120, 96), new THREE.MeshStandardMaterial({ color: 0x547b7b, roughness: .27, metalness: .15 }));
water.rotation.x = -Math.PI / 2; water.position.y = -.25; land.add(water);
for (let layer = 0; layer < 3; layer++) {
  const verts = [], inds = [], radius = 38 + layer * 30, n = 192;
  for (let i = 0; i <= n; i++) {
    const a = i * Math.PI * 2 / n;
    const h = (7 + layer * 8) * (.55 + .18 * Math.sin(a * 3 + layer) + .15 * Math.sin(a * 7 + 2 * layer) + .08 * Math.cos(a * 13));
    verts.push(radius * Math.cos(a), -.3, radius * Math.sin(a), radius * Math.cos(a), h, radius * Math.sin(a));
    if (i < n) { const j = i * 2; inds.push(j, j + 1, j + 2, j + 1, j + 3, j + 2); }
  }
  const geom = new THREE.BufferGeometry(); geom.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3)); geom.setIndex(inds); geom.computeVertexNormals();
  land.add(new THREE.Mesh(geom, new THREE.MeshBasicMaterial({ color: [0x35534b, 0x587571, 0x829d9e][layer], side: THREE.DoubleSide })));
}
scene.add(land);

function releaseMouse() { if (document.pointerLockElement) controls.unlock(); }
function resetJoystick() {
  const pointer = joystickPointer; joystickPointer = null;
  touchMove.x = 0; touchMove.z = 0;
  $('joystick-knob').style.transform = 'translate(0px, 0px)';
  if (pointer !== null && $('joystick').hasPointerCapture(pointer)) $('joystick').releasePointerCapture(pointer);
}
function clearInput() {
  keys.clear(); resetJoystick();
  const pointer = lookPointer; lookPointer = null;
  if (pointer !== null && renderer.domElement.hasPointerCapture(pointer)) renderer.domElement.releasePointerCapture(pointer);
}
function setTouchWalking(active) {
  clearInput(); touchActive = active; touchFast = false;
  $('touch-speed').setAttribute('aria-pressed', 'false');
  document.body.classList.toggle('walking', active);
  document.body.classList.toggle('touch-walking', active);
  $('touch-controls').hidden = !active; $('reticle').hidden = !active;
  $('interaction').hidden = true;
  if (!active) $('enter').textContent = 'Continue exploring';
}
function pauseWalking() { setTouchWalking(false); releaseMouse(); }
controls.addEventListener('lock', () => { locked = true; document.body.classList.add('walking'); $('reticle').hidden = false; clearInput(); });
controls.addEventListener('unlock', () => { locked = false; document.body.classList.remove('walking'); $('reticle').hidden = true; $('interaction').hidden = true; clearInput(); $('enter').textContent = 'Continue exploring'; });
$('enter').onclick = () => { if (!ready) return; if (touchMode) setTouchWalking(true); else controls.lock(); };
$('pause-touch').onclick = pauseWalking;
$('read-labels').onclick = () => { pauseWalking(); $('labels-dialog').showModal(); };
$('close-labels').onclick = () => $('labels-dialog').close();
$('touch-interact').onclick = interact;
$('touch-speed').onclick = () => { touchFast = !touchFast; $('touch-speed').setAttribute('aria-pressed', String(touchFast)); };
function moveJoystick(e) {
  const rect = $('joystick').getBoundingClientRect();
  let x = e.clientX - rect.left - rect.width / 2, y = e.clientY - rect.top - rect.height / 2;
  const radius = rect.width * .31, distance = Math.hypot(x, y);
  if (distance > radius) { x *= radius / distance; y *= radius / distance; }
  const strength = Math.max(0, (Math.min(distance / radius, 1) - .12) / .88);
  const length = Math.hypot(x, y) || 1;
  touchMove.x = x / length * strength; touchMove.z = -y / length * strength;
  $('joystick-knob').style.transform = `translate(${x}px, ${y}px)`;
}
$('joystick').addEventListener('pointerdown', (e) => {
  if (!touchActive || joystickPointer !== null) return;
  e.preventDefault(); joystickPointer = e.pointerId;
  $('joystick').setPointerCapture(e.pointerId); moveJoystick(e);
});
$('joystick').addEventListener('pointermove', (e) => { if (e.pointerId === joystickPointer) { e.preventDefault(); moveJoystick(e); } });
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) {
  $('joystick').addEventListener(event, (e) => { if (e.pointerId === joystickPointer) resetJoystick(); });
}
document.addEventListener('pointerlockerror', () => { $('status').textContent = 'Mouse capture unavailable here. Drag the view to look; use WASD while the canvas is focused.'; renderer.domElement.focus(); });
renderer.domElement.addEventListener('pointerdown', (e) => {
  if (!ready || locked || lookPointer !== null || (touchMode && !touchActive)) return;
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  e.preventDefault(); lookPointer = e.pointerId; lastPointer = { x: e.clientX, y: e.clientY };
  renderer.domElement.setPointerCapture(e.pointerId); renderer.domElement.focus({ preventScroll: true });
});
renderer.domElement.addEventListener('pointermove', (e) => {
  if (e.pointerId !== lookPointer || locked) return;
  const angle = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ');
  const sensitivity = e.pointerType === 'touch' ? .004 : .002;
  angle.y -= (e.clientX - lastPointer.x) * sensitivity; angle.x -= (e.clientY - lastPointer.y) * sensitivity;
  angle.x = THREE.MathUtils.clamp(angle.x, -1.48, 1.48); camera.quaternion.setFromEuler(angle);
  lastPointer = { x: e.clientX, y: e.clientY };
});
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) {
  renderer.domElement.addEventListener(event, (e) => { if (e.pointerId === lookPointer) lookPointer = null; });
}
window.addEventListener('blur', pauseWalking);
document.addEventListener('visibilitychange', () => { if (document.hidden) pauseWalking(); });
function isMovingEnabled() { return ready && (touchMode ? touchActive : (locked || document.activeElement === renderer.domElement)); }
window.addEventListener('keydown', (e) => {
  if (!isMovingEnabled()) return;
  if (['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowLeft','ArrowDown','ArrowRight','ShiftLeft','ShiftRight'].includes(e.code)) { e.preventDefault(); keys.add(e.code); }
  if (e.repeat) return;
  if (e.code === 'Escape' && touchActive) pauseWalking();
  if (e.code === 'KeyR') setView('entrance');
  if (e.code === 'KeyE') interact();
});
window.addEventListener('keyup', (e) => keys.delete(e.code));
$('reset').onclick = () => setView('entrance'); $('ceiling').onclick = () => setView('ceiling'); $('detail').onclick = () => setView('detail');
function toggleDoor() { doorTarget = 1 - doorTarget; $('door').setAttribute('aria-pressed', String(Boolean(doorTarget))); $('door').textContent = doorTarget ? 'Close doors' : 'Open doors'; }
$('door').onclick = toggleDoor;
$('furniture').onclick = () => {
  if (!furniture) return;
  furniture.visible = !furniture.visible; $('furniture').setAttribute('aria-pressed', String(furniture.visible));
  if (furniture.visible && Math.hypot(camera.position.x, camera.position.z) < 2.3) setView('entrance');
};
$('fullscreen').onclick = async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch { $('status').textContent = 'Fullscreen is unavailable in this browser panel.'; } };

// A walking capsule is constrained by each wall, the shelving faces and columns.
function resolveCollision(pos) {
  for (let pass = 0; pass < 3; pass++) {
    for (let i = 0; i < 12; i++) {
      const a = i * Math.PI / 6, nx = Math.cos(a), nz = -Math.sin(a);
      const limit = i % 2 === 0 ? 3.63 : (i === 9 ? 3.72 : 3.23);
      const d = pos.x * nx + pos.z * nz - limit;
      if (d > 0) { pos.x -= d * nx; pos.z -= d * nz; }
    }
    for (let i = 0; i < 12; i++) {
      const a = (i + .5) * Math.PI / 6, cx = 3.95 * Math.cos(a), cz = -3.95 * Math.sin(a);
      const dx = pos.x - cx, dz = pos.z - cz, d = Math.hypot(dx, dz);
      if (d < .46 && d > .0001) { pos.x = cx + dx / d * .46; pos.z = cz + dz / d * .46; }
    }
  }
  if (furniture?.visible) {
    const r = Math.hypot(pos.x, pos.z);
    if (r < 2.15) { const ratio = 2.15 / Math.max(r, .001); pos.x *= ratio; pos.z *= ratio; }
  }
  return pos;
}
function interactionTarget() {
  const dir = controls.getDirection(new THREE.Vector3());
  for (const [kind, point] of [['library', new THREE.Vector3(0, 1.5, -3.35)], ['door', new THREE.Vector3(0, 1.6, 4)]]) {
    const delta = point.sub(camera.position), distance = delta.length();
    if (distance < 2.3 && dir.dot(delta.normalize()) > .80) return kind;
  }
  return null;
}
function interact() {
  const target = interactionTarget();
  if (target === 'door') toggleDoor();
  if (target === 'library') { pauseWalking(); window.open('https://library.xrguild.org/', '_blank', 'noopener,noreferrer'); }
}
let lastTime = performance.now(), frameCount = 0, fpsStart = lastTime;
const forward = new THREE.Vector3(), right = new THREE.Vector3(), step = new THREE.Vector3();
function frame(now) {
  const dt = Math.min((now - lastTime) / 1000, .04); lastTime = now;
  if (isMovingEnabled()) {
    controls.getDirection(forward); forward.y = 0; forward.normalize(); right.crossVectors(forward, camera.up);
    const x = Number(keys.has('KeyD') || keys.has('ArrowRight')) - Number(keys.has('KeyA') || keys.has('ArrowLeft')) + touchMove.x;
    const z = Number(keys.has('KeyW') || keys.has('ArrowUp')) - Number(keys.has('KeyS') || keys.has('ArrowDown')) + touchMove.z;
    step.copy(forward).multiplyScalar(z).addScaledVector(right, x);
    if (step.lengthSq()) { step.clampLength(0, 1).multiplyScalar(dt * (touchFast || keys.has('ShiftLeft') || keys.has('ShiftRight') ? 2.7 : 1.5)); camera.position.add(step); resolveCollision(camera.position); }
  }
  doorAngle = THREE.MathUtils.damp(doorAngle, doorTarget, 5, dt);
  for (const hinge of hinges) { hinge.quaternion.copy(originalHinges.get(hinge)); hinge.rotateY(THREE.MathUtils.degToRad(hinge.userData.open_angle_degrees) * doorAngle); }
  if (locked || touchActive) {
    const target = interactionTarget();
    $('interaction').hidden = !target || touchActive;
    $('interaction').textContent = target === 'library' ? 'E · Search the XR Guild collection ↗' : `E · ${doorTarget ? 'Close' : 'Open'} meeting doors`;
    $('touch-interact').disabled = !target;
    $('touch-interact').textContent = target === 'library' ? 'Search library ↗' : target === 'door' ? `${doorTarget ? 'Close' : 'Open'} doors` : 'Interact';
  }
  pipeline.render();
  frameCount++;
  if (now - fpsStart > 1500) { $('fps').textContent = `${Math.round(frameCount * 1000 / (now - fpsStart))} fps`; fpsStart = now; frameCount = 0; }
}
window.addEventListener('resize', () => { clearInput(); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });

async function init() {
  await renderer.init();
  const webgpu = renderer.backend.isWebGPUBackend === true;
  $('backend').textContent = webgpu ? 'WebGPU active' : 'WebGL 2 fallback';
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(`${import.meta.env.BASE_URL}assets/XR_Guild_Library_v2.glb`, (event) => {
    if (event.total) { const pct = Math.round(event.loaded / event.total * 100); $('loading').value = pct; $('status').textContent = `Loading room · ${pct}%`; }
  });
  const room = gltf.scene; room.name = 'XR Guild Library v2';
  room.traverse((obj) => {
    if (obj.userData.optional_furniture) { furniture = obj; obj.visible = false; }
    if (obj.userData.door_hinge) { hinges.push(obj); originalHinges.set(obj, obj.quaternion.clone()); }
    if (obj.isMesh) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      const isGlass = mats.some((m) => m.transmission > .9);
      obj.castShadow = !isGlass; obj.receiveShadow = !isGlass;
      for (const mat of mats) { if (mat.map) mat.map.anisotropy = 8; if (isGlass) { mat.roughness = .018; mat.thickness = .008; } }
    }
  });
  scene.add(room);
  $('status').textContent = 'Preparing the first view…';
  await renderer.compileAsync(scene, camera);
  // GTAO requires a resolved, single-sample depth texture on WebGPU.
  const scenePass = pass(scene, camera, { samples: 0 });
  const occlusion = ao(scenePass.getTextureNode('depth'), null, camera);
  occlusion.radius.value = .42; occlusion.thickness.value = .12;
  occlusion.resolutionScale = .5;
  pipeline = new THREE.RenderPipeline(renderer);
  const smoothOcclusion = denoise(occlusion.getTextureNode(), scenePass.getTextureNode('depth'), null, camera);
  smoothOcclusion.radius.value = 3;
  pipeline.outputColorTransform = false;
  pipeline.outputNode = fxaa(renderOutput(scenePass.getTextureNode('output').mul(smoothOcclusion)));
  pipeline.render();
  renderer.setAnimationLoop(frame);
  ready = true; $('enter').disabled = false; $('enter').textContent = 'Enter the library'; $('loading').hidden = true;
  $('status').textContent = touchMode ? 'Tap Enter to explore. Pause brings these instructions back.' : webgpu ? 'Drag to look around, or enter for mouse capture.' : 'WebGPU unavailable here; using WebGL 2. Drag or enter to explore.';
  // Read-only runtime evidence for QA, also useful when inspecting a hosted copy.
  window.libraryPreview = { get ready() { return ready; }, get backend() { return webgpu ? 'WebGPU' : 'WebGL2'; }, get touchMode() { return touchMode; }, get touchActive() { return touchActive; }, get touchMove() { return { ...touchMove }; }, get exposure() { return renderer.toneMappingExposure; }, get position() { return camera.position.toArray(); }, get rotation() { return camera.quaternion.toArray(); }, get pointerLocked() { return locked; }, get meetingLayout() { return Boolean(furniture?.visible); }, get doorOpen() { return doorAngle; }, get triangles() { return renderer.info.render.triangles; }, get drawCalls() { return renderer.info.render.drawCalls; } };
}
init().catch((error) => { console.error(error); $('enter').disabled = true; $('enter').textContent = 'Unable to load preview'; $('status').textContent = `${error.message}. Reload this page in a WebGPU-capable browser on localhost or HTTPS.`; $('loading').hidden = true; });
