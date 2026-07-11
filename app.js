const recordButton = document.querySelector('#recordButton');
const timer = document.querySelector('#timer');
const statusText = document.querySelector('#status');
const wave = document.querySelector('#wave');
const playback = document.querySelector('#playback');
let recorder;
let stream;
let chunks = [];
let startedAt = 0;
let tick;

function setTime() {
  const elapsed = Math.floor((Date.now() - startedAt) / 1000);
  timer.textContent = `${String(Math.floor(elapsed / 60)).padStart(2, '0')}:${String(elapsed % 60).padStart(2, '0')}`;
}

recordButton.addEventListener('click', async () => {
  if (recorder?.state === 'recording') {
    recorder.stop();
    stream.getTracks().forEach(track => track.stop());
    clearInterval(tick);
    recordButton.classList.remove('active');
    recordButton.querySelector('b').textContent = 'Record again';
    statusText.textContent = 'Recording complete';
    wave.classList.remove('active');
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    statusText.textContent = 'Recording is unavailable in this browser';
    return;
  }
  try {
    chunks = [];
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    recorder.addEventListener('dataavailable', event => chunks.push(event.data));
    recorder.addEventListener('stop', () => {
      playback.src = URL.createObjectURL(new Blob(chunks, { type: recorder.mimeType }));
      playback.hidden = false;
    });
    recorder.start();
    startedAt = Date.now();
    timer.textContent = '00:00';
    tick = setInterval(setTime, 250);
    statusText.textContent = 'Recording locally';
    recordButton.classList.add('active');
    recordButton.querySelector('b').textContent = 'Stop recording';
    wave.classList.add('active');
    playback.hidden = true;
  } catch {
    statusText.textContent = 'Microphone permission was not granted';
  }
});

const walletDemo = document.querySelector('#walletDemo');
const walletState = document.querySelector('#walletState');
walletDemo.addEventListener('click', () => {
  walletState.textContent = 'Connecting…';
  setTimeout(() => { walletState.textContent = 'Connected (demo)'; }, 900);
  setTimeout(() => { walletState.textContent = 'Disconnected'; }, 3200);
});
