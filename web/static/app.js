const form = document.getElementById('generator-form');
const statusText = document.getElementById('status-text');
const resultBox = document.getElementById('result-box');
const jobMessage = document.getElementById('job-message');
const downloadLink = document.getElementById('download-link');
const errorBox = document.getElementById('error-box');
const logBox = document.getElementById('log-box');

let lastLogCount = 0;

function renderLogs(logs) {
  if (!Array.isArray(logs) || logs.length === 0) {
    return;
  }

  if (logs.length < lastLogCount) {
    lastLogCount = 0;
    logBox.textContent = 'Waiting for output...';
  }

  const newLines = logs.slice(lastLogCount);
  if (newLines.length > 0) {
    if (logBox.textContent === 'Waiting for output...' || logBox.textContent === 'Queued. Waiting for the first pipeline line...') {
      logBox.textContent = '';
    }

    const current = logBox.textContent.trimEnd();
    const appended = newLines.join('');
    logBox.textContent = current ? `${current}${appended.startsWith('\n') ? '' : '\n'}${appended}` : appended;
    logBox.scrollTop = logBox.scrollHeight;
    lastLogCount = logs.length;
  }
}

async function pollJob(url) {
  const response = await fetch(url);
  const data = await response.json();
  renderLogs(data.logs);

  if (data.status === 'done') {
    statusText.textContent = 'Finished.';
    jobMessage.textContent = 'Your video is ready.';
    downloadLink.hidden = false;
    downloadLink.href = data.result_url;
    downloadLink.textContent = 'Download MP4';
    errorBox.hidden = true;
    return;
  }

  if (data.status === 'error') {
    statusText.textContent = 'Generation failed.';
    jobMessage.textContent = data.message || 'The job failed.';
    downloadLink.hidden = true;
    errorBox.hidden = false;
    errorBox.textContent = data.stderr || 'Unknown error';
    return;
  }

  statusText.textContent = data.message || 'Working...';
  setTimeout(() => pollJob(url), 3000);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusText.textContent = 'Submitting job...';
  downloadLink.hidden = true;
  errorBox.hidden = true;
  resultBox.hidden = false;
  logBox.textContent = 'Waiting for output...';
  lastLogCount = 0;

  const formData = new FormData(form);
  const response = await fetch('/submit', { method: 'POST', body: formData });
  const data = await response.json();

  if (!response.ok) {
    statusText.textContent = 'Validation failed.';
    jobMessage.textContent = data.error || 'Invalid input.';
    return;
  }

  jobMessage.textContent = `Job ${data.job_id} queued.`;
  statusText.textContent = 'Queued.';
  logBox.textContent = 'Queued. Waiting for the first pipeline line...';
  pollJob(data.status_url);
});