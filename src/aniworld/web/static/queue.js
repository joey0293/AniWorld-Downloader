let queueModalOpen = false;
let queuePollTimer = null;
let badgePollTimer = null;

function openQueueModal() {
  queueModalOpen = true;
  document.getElementById('queueOverlay').style.display = 'block';
  loadQueue();
  if (queuePollTimer) clearInterval(queuePollTimer);
  queuePollTimer = setInterval(loadQueue, 2000);
}

function closeQueueModal() {
  queueModalOpen = false;
  document.getElementById('queueOverlay').style.display = 'none';
  if (queuePollTimer) { clearInterval(queuePollTimer); queuePollTimer = null; }
}

async function loadQueue() {
  try {
    const resp = await fetch('/api/queue');
    const data = await resp.json();
    const items = data.items || [];
    renderQueue(items);
    updateBadge(items);
  } catch (e) { /* ignore */ }
}

function updateBadge(items) {
  const active = items.filter(i => i.status === 'queued' || i.status === 'running').length;
  const badge = document.getElementById('queueBadge');
  if (active > 0) {
    badge.textContent = active;
    badge.style.display = 'inline-block';
  } else {
    badge.style.display = 'none';
  }
}

function renderQueue(items) {
  const list = document.getElementById('queueList');

  // Show all active items + last 3 completed/failed/cancelled
  const active = items.filter(i => i.status === 'queued' || i.status === 'running');
  const done = items.filter(i => i.status === 'completed' || i.status === 'failed' || i.status === 'cancelled').slice(-3);
  const visible = active.concat(done);
  visible.sort((a, b) => a.id - b.id);

  if (!visible.length) {
    list.innerHTML = '<div class="queue-empty">Queue is empty</div>';
    return;
  }

  // Remember which error panels are expanded before re-render
  const expandedErrors = new Set();
  list.querySelectorAll('.queue-error-details.expanded').forEach(el => {
    expandedErrors.add(el.id);
  });

  let html = '';
  visible.forEach(item => {
    const isRunning = item.status === 'running';
    const cls = isRunning ? 'queue-item queue-item-active' : 'queue-item';

    let statusBadge = '';
    if (item.status === 'running') statusBadge = '<span class="queue-status queue-status-running">In Progress</span>';
    else if (item.status === 'queued') statusBadge = '<span class="queue-status queue-status-queued">Queued</span>';
    else if (item.status === 'completed') statusBadge = '<span class="queue-status queue-status-completed">Completed</span>';
    else if (item.status === 'failed') statusBadge = '<span class="queue-status queue-status-failed">Failed</span>';
    else if (item.status === 'cancelled') statusBadge = '<span class="queue-status queue-status-cancelled">Cancelled</span>';

    let progressHtml = '';
    if (isRunning || item.status === 'cancelled') {
      const pct = item.total_episodes > 0 ? Math.round((item.current_episode / item.total_episodes) * 100) : 0;
      const seInfo = item.current_url ? parseSeasonEpisode(item.current_url) : '';
      const label = item.status === 'cancelled'
        ? item.current_episode + '/' + item.total_episodes + ' episodes (stopped)'
        : item.current_episode + '/' + item.total_episodes + ' episodes' + (seInfo ? ' - ' + seInfo : '');
      progressHtml =
        '<div class="queue-progress">' +
          '<div class="queue-progress-info">' +
            '<span>' + label + '</span>' +
            '<span>' + pct + '%</span>' +
          '</div>' +
          '<div class="queue-progress-bar"><div class="queue-progress-fill" style="width:' + pct + '%"></div></div>' +
        '</div>';
    }

    let errorsHtml = '';
    if (item.errors) {
      let errors = [];
      try { errors = typeof item.errors === 'string' ? JSON.parse(item.errors) : item.errors; } catch(e) {}
      if (errors.length) {
        const errId = 'qerr-' + item.id;
        let details = '';
        errors.forEach(function(err) {
          details += '<div class="queue-error-detail">' + escQ(err.error || '') + '</div>';
        });
        errorsHtml =
          '<div class="queue-errors queue-errors-expandable" onclick="this.classList.toggle(\'expanded\');document.getElementById(\'' + errId + '\').classList.toggle(\'expanded\')">' +
            errors.length + ' error(s) <span class="queue-errors-toggle">&#9654;</span>' +
          '</div>' +
          '<div class="queue-error-details" id="' + errId + '">' + details + '</div>';
      }
    }

    let actionBtn = '';
    if (item.status === 'queued') {
      actionBtn = '<button class="queue-remove" onclick="removeQueueItem(' + item.id + ')" title="Remove">&times;</button>';
    } else if (item.status === 'running') {
      actionBtn = '<button class="queue-cancel" onclick="cancelQueueItem(' + item.id + ')" title="Cancel after current episode">Cancel</button>';
    }

    const userHtml = item.username ? '<span class="queue-user">' + escQ(item.username) + '</span>' : '';

    html +=
      '<div class="' + cls + '">' +
        '<div class="queue-item-header">' +
          '<div class="queue-item-title">' + escQ(item.title) + '</div>' +
          '<div class="queue-item-right">' + statusBadge + actionBtn + '</div>' +
        '</div>' +
        '<div class="queue-item-meta">' +
          '<span>' + item.total_episodes + ' episode(s)</span>' +
          '<span>' + escQ(item.language) + '</span>' +
          '<span>' + escQ(item.provider) + '</span>' +
          userHtml +
        '</div>' +
        progressHtml +
        errorsHtml +
      '</div>';
  });

  list.innerHTML = html;

  // Restore expanded state (both the details panel and its sibling header)
  expandedErrors.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('expanded');
      const header = el.previousElementSibling;
      if (header) header.classList.add('expanded');
    }
  });
}

function parseSeasonEpisode(url) {
  const m = url.match(/staffel-(\d+)\/episode-(\d+)/i);
  if (m) return 'S' + m[1] + 'E' + m[2];
  return '';
}

async function cancelQueueItem(id) {
  try {
    const resp = await fetch('/api/queue/' + id + '/cancel', { method: 'POST' });
    const data = await resp.json();
    if (data.error) {
      if (typeof showToast === 'function') showToast(data.error);
    } else {
      if (typeof showToast === 'function') showToast('Cancelling after current episode...');
    }
    loadQueue();
  } catch (e) { /* ignore */ }
}

async function removeQueueItem(id) {
  try {
    const resp = await fetch('/api/queue/' + id, { method: 'DELETE' });
    const data = await resp.json();
    if (data.error) {
      if (typeof showToast === 'function') showToast(data.error);
    }
    loadQueue();
  } catch (e) { /* ignore */ }
}

function escQ(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

// ESC key closes queue modal
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' && queueModalOpen) closeQueueModal();
});

// Background badge poll every 10s
(function startBadgePoll() {
  loadQueue();
  badgePollTimer = setInterval(function() {
    if (!queueModalOpen) loadQueue();
  }, 10000);
})();
