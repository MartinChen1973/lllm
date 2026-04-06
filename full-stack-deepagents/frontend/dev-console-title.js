// ## ⬇️ Next dev sets `process.title` to `next-server (v…)` once in start-server.js; reassert a stable label for the Windows console/taskbar.
const { spawn } = require('child_process');
const path = require('path');

const TITLE = 'Node frontend (3500)';
const nextBin = path.join(__dirname, 'node_modules', 'next', 'dist', 'bin', 'next');
const nextArgs = process.argv.slice(2).length > 0 ? process.argv.slice(2) : ['dev', '-p', '3500'];

const child = spawn(process.execPath, [nextBin, ...nextArgs], {
  stdio: 'inherit',
  windowsHide: false,
});

process.title = TITLE;
let interval = null;
if (process.platform === 'win32') {
  interval = setInterval(() => {
    process.title = TITLE;
  }, 400);
}

child.on('exit', (code, signal) => {
  if (interval) clearInterval(interval);
  if (signal) process.exit(1);
  process.exit(code == null ? 0 : code);
});

child.on('error', (err) => {
  clearInterval(interval);
  console.error(err);
  process.exit(1);
});
