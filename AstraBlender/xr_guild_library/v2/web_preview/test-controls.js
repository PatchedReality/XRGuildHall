(async () => {
  const state = () => JSON.parse(JSON.stringify(window.libraryPreview));
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const hold = async (code, ms) => { window.dispatchEvent(new KeyboardEvent('keydown', { code })); await wait(ms); window.dispatchEvent(new KeyboardEvent('keyup', { code })); };
  const report = { userAgent: navigator.userAgent, initial: state(), checks: [] };
  for (const code of ['KeyW', 'KeyS', 'KeyA', 'KeyD']) {
    const before = state().position; await hold(code, 300); const after = state().position;
    report.checks.push({ key: code, before, after, moved: Math.hypot(after[0]-before[0], after[2]-before[2]) > .2 });
  }
  const rotation = state().rotation;
  document.dispatchEvent(new MouseEvent('mousemove', { movementX: 90, movementY: -40 }));
  report.mouseLook = JSON.stringify(rotation) !== JSON.stringify(state().rotation);
  document.getElementById('reset').click(); await wait(150); document.querySelector('canvas').focus();
  await hold('KeyW', 5000);
  report.collision = { position: state().position, stoppedAtShelf: Math.abs(state().position[2] + 3.23) < .03 };
  await hold('KeyS', 650); // Stand back far enough to aim at the reachable screen.
  const open = window.open; let openedURL = null;
  try { window.open = url => { openedURL = url; return null; }; window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyE' })); }
  finally { window.open = open; }
  report.libraryInteraction = openedURL === 'https://library.xrguild.org/';
  document.getElementById('reset').click(); await wait(150);
  document.getElementById('furniture').click(); report.furnitureShown = state().meetingLayout;
  document.getElementById('furniture').click(); report.furnitureHidden = !state().meetingLayout;
  document.getElementById('door').click(); await wait(1100); report.doorOpened = state().doorOpen > .98;
  document.getElementById('door').click(); await wait(1100); report.doorClosed = state().doorOpen < .02;
  document.getElementById('ceiling').click(); report.ceilingView = state().position[2] === .8;
  document.getElementById('detail').click(); report.detailView = state().position[1] === 2.65;
  document.getElementById('reset').click(); report.final = state(); report.fps = document.getElementById('fps').textContent;
  report.pass = report.initial.backend === 'WebGPU' && report.initial.pointerLocked && report.checks.every(c => c.moved) && report.mouseLook && report.collision.stoppedAtShelf && report.libraryInteraction && report.furnitureShown && report.furnitureHidden && report.doorOpened && report.doorClosed && report.ceilingView && report.detailView;
  return report;
})()
