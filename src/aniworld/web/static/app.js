const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const searchSpinner = document.getElementById('searchSpinner');
const resultsDiv = document.getElementById('results');
const overlay = document.getElementById('overlay');
const seasonSelect = document.getElementById('seasonSelect');
const languageSelect = document.getElementById('languageSelect');
const providerSelect = document.getElementById('providerSelect');
const episodeList = document.getElementById('episodeList');
const episodeSpinner = document.getElementById('episodeSpinner');
const selectAllCb = document.getElementById('selectAll');
const statusBar = document.getElementById('statusBar');
const statusText = document.getElementById('statusText');
const downloadBtn = document.getElementById('downloadBtn');

let currentSeasons = [];
let currentDownloadId = null;
let pollTimer = null;
// Provider data per language label, e.g. {"German Dub": ["VOE","Vidmoly"], ...}
let availableProviders = null;
// Static list of providers rendered into the template (working extractors only)
const staticProviders = Array.from(providerSelect.options).map(o => o.value);

searchInput.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
languageSelect.addEventListener('change', updateProviderDropdown);

async function doSearch() {
  const keyword = searchInput.value.trim();
  if (!keyword) return;
  searchBtn.disabled = true;
  searchSpinner.style.display = 'block';
  resultsDiv.innerHTML = '';
  try {
    const resp = await fetch('/api/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({keyword})
    });
    const data = await resp.json();
    renderResults(data.results || []);
  } catch (e) {
    showToast('Search failed: ' + e.message);
  } finally {
    searchBtn.disabled = false;
    searchSpinner.style.display = 'none';
  }
}

function renderResults(results) {
  resultsDiv.innerHTML = '';
  if (!results.length) {
    resultsDiv.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:#888;padding:40px">No results found.</div>';
    return;
  }
  results.forEach(r => {
    const card = document.createElement('div');
    card.className = 'card';
    card.onclick = () => openSeries(r.url);
    card.innerHTML = `<img src="" alt="" data-url="${esc(r.url)}"><div class="info"><div class="title">${esc(r.title)}</div></div>`;
    resultsDiv.appendChild(card);
    loadPoster(r.url, card.querySelector('img'));
  });
}

async function loadPoster(url, imgEl) {
  try {
    const resp = await fetch('/api/series?url=' + encodeURIComponent(url));
    const data = await resp.json();
    if (data.poster_url) imgEl.src = data.poster_url;
  } catch(e) { /* ignore poster load failure */ }
}

async function openSeries(url) {
  overlay.style.display = 'block';
  document.getElementById('modalPoster').src = '';
  document.getElementById('modalTitle').textContent = 'Loading...';
  document.getElementById('modalGenres').textContent = '';
  document.getElementById('modalYear').textContent = '';
  document.getElementById('modalDesc').textContent = '';
  seasonSelect.innerHTML = '';
  episodeList.innerHTML = '';
  statusBar.classList.remove('active');
  availableProviders = null;
  resetProviderDropdown();

  try {
    const [seriesResp, seasonsResp] = await Promise.all([
      fetch('/api/series?url=' + encodeURIComponent(url)),
      fetch('/api/seasons?url=' + encodeURIComponent(url))
    ]);
    const seriesData = await seriesResp.json();
    const seasonsData = await seasonsResp.json();

    document.getElementById('modalTitle').textContent = seriesData.title || 'Unknown';
    if (seriesData.poster_url) document.getElementById('modalPoster').src = seriesData.poster_url;
    document.getElementById('modalGenres').textContent = (seriesData.genres || []).join(', ');
    document.getElementById('modalYear').textContent = seriesData.release_year || '';
    document.getElementById('modalDesc').textContent = seriesData.description || '';

    currentSeasons = seasonsData.seasons || [];
    seasonSelect.innerHTML = '';
    currentSeasons.forEach((s, i) => {
      const opt = document.createElement('option');
      opt.value = i;
      opt.textContent = s.are_movies ? 'Movies' : `Season ${s.season_number} (${s.episode_count} eps)`;
      seasonSelect.appendChild(opt);
    });

    if (currentSeasons.length) loadEpisodes();
  } catch (e) {
    showToast('Failed to load series: ' + e.message);
  }
}

async function loadEpisodes() {
  const idx = parseInt(seasonSelect.value);
  const season = currentSeasons[idx];
  if (!season) return;

  episodeList.innerHTML = '';
  episodeSpinner.style.display = 'block';
  selectAllCb.checked = false;
  availableProviders = null;
  resetProviderDropdown();

  try {
    const resp = await fetch('/api/episodes?url=' + encodeURIComponent(season.url));
    const data = await resp.json();
    const episodes = data.episodes || [];

    episodeList.innerHTML = '';
    episodes.forEach(ep => {
      const div = document.createElement('div');
      div.className = 'episode-item';
      const title = ep.title_en || ep.title_de || '';
      div.innerHTML = `<input type="checkbox" value="${esc(ep.url)}"><span class="ep-num">E${ep.episode_number}</span><span class="ep-title">${esc(title)}</span>`;
      episodeList.appendChild(div);
    });

    // Fetch available providers using the first episode as a sample
    if (episodes.length) {
      fetchProviders(episodes[0].url);
    }
  } catch (e) {
    episodeList.innerHTML = '<div style="padding:12px;color:#888">Failed to load episodes.</div>';
  } finally {
    episodeSpinner.style.display = 'none';
  }
}

async function fetchProviders(episodeUrl) {
  try {
    const resp = await fetch('/api/providers?url=' + encodeURIComponent(episodeUrl));
    const data = await resp.json();
    if (data.providers) {
      availableProviders = data.providers;
      updateProviderDropdown();
    }
  } catch (e) {
    // If provider fetch fails, keep the static list
  }
}

function resetProviderDropdown() {
  providerSelect.innerHTML = '';
  staticProviders.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p;
    opt.textContent = p;
    providerSelect.appendChild(opt);
  });
  selectDefaultProvider();
}

function updateProviderDropdown() {
  if (!availableProviders) return;

  const lang = languageSelect.value;
  const providers = availableProviders[lang];

  providerSelect.innerHTML = '';
  if (providers && providers.length) {
    providers.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      providerSelect.appendChild(opt);
    });
  } else {
    // Fallback to the static working providers list
    staticProviders.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      providerSelect.appendChild(opt);
    });
  }
  selectDefaultProvider();
}

function selectDefaultProvider() {
  // Prefer VOE as default since it's the most common working provider
  for (const opt of providerSelect.options) {
    if (opt.value === 'VOE') {
      providerSelect.value = 'VOE';
      return;
    }
  }
}

function toggleSelectAll() {
  const checked = selectAllCb.checked;
  episodeList.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = checked);
}

async function startDownload() {
  const checkboxes = episodeList.querySelectorAll('input[type=checkbox]:checked');
  const episodes = Array.from(checkboxes).map(cb => cb.value);
  if (!episodes.length) { showToast('No episodes selected.'); return; }

  const language = languageSelect.value;
  const provider = providerSelect.value;

  downloadBtn.disabled = true;
  try {
    const resp = await fetch('/api/download', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({episodes, language, provider})
    });
    const data = await resp.json();
    if (data.error) { showToast(data.error); downloadBtn.disabled = false; return; }

    currentDownloadId = data.download_id;
    statusBar.classList.add('active');
    statusText.textContent = `Downloading 0/${episodes.length}...`;
    pollStatus();
  } catch (e) {
    showToast('Download request failed: ' + e.message);
    downloadBtn.disabled = false;
  }
}

function pollStatus() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    if (!currentDownloadId) return;
    try {
      const resp = await fetch('/api/download/status?id=' + currentDownloadId);
      const data = await resp.json();
      statusText.textContent = `Downloading ${data.current}/${data.total}...`;

      if (data.status === 'completed') {
        clearInterval(pollTimer);
        pollTimer = null;
        const errorCount = data.errors ? data.errors.length : 0;
        const successCount = data.total - errorCount;
        if (errorCount === 0) {
          statusText.textContent = `Done! ${data.total} episode(s) downloaded.`;
        } else {
          const lastError = data.errors[data.errors.length - 1];
          statusText.textContent = `Done: ${successCount}/${data.total} downloaded, ${errorCount} failed.`;
          if (lastError) {
            showToast(`Download error: ${lastError.error}`);
          }
        }
        downloadBtn.disabled = false;
        currentDownloadId = null;
      }
    } catch (e) { /* ignore poll errors */ }
  }, 2000);
}

function closeModal() {
  overlay.style.display = 'none';
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}
function closeModalOutside(e) { if (e.target === overlay) closeModal(); }

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 4000);
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}
