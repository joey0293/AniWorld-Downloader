let libraryTitles = [];

async function loadLibrary() {
  const list = document.getElementById('libraryList');
  list.innerHTML = '<div class="library-empty">Loading...</div>';
  try {
    const resp = await fetch('/api/library');
    const data = await resp.json();
    libraryTitles = data.titles || [];
    renderLibrary(libraryTitles);
  } catch (e) {
    list.innerHTML = '<div class="library-empty">Failed to load library</div>';
  }
}

function renderLibrary(titles) {
  const list = document.getElementById('libraryList');
  if (!titles.length) {
    list.innerHTML = '<div class="library-empty">No downloaded content found</div>';
    return;
  }

  let html = '';
  titles.forEach(function(title, ti) {
    const seasonKeys = Object.keys(title.seasons).sort(function(a, b) { return parseInt(a) - parseInt(b); });

    // Title header
    html += '<div class="library-title-section">';
    html += '<div class="library-title-header" onclick="toggleLibraryTitle(' + ti + ')">';
    html += '<div class="library-title-left">';
    html += '<span class="library-arrow" id="libraryTitleArrow' + ti + '">&#9654;</span>';
    html += '<span class="library-title-name">' + escLib(title.folder) + '</span>';
    html += '</div>';
    html += '<div class="library-title-right">';
    html += '<span class="library-meta">' + title.total_episodes + ' ep</span>';
    html += '<span class="library-meta library-meta-size">' + formatSize(title.total_size) + '</span>';
    if (libraryCanDelete) html += '<button class="library-delete" onclick="event.stopPropagation();deleteLibraryItem(' + ti + ',null,null)" title="Delete title">&times;</button>';
    html += '</div>';
    html += '</div>';

    // Title body (seasons)
    html += '<div class="library-title-body" id="libraryTitleBody' + ti + '">';
    seasonKeys.forEach(function(skey) {
      const eps = title.seasons[skey];
      const sid = 'libS' + ti + '_' + skey;
      const seasonSize = eps.reduce(function(acc, e) { return acc + e.size; }, 0);

      // Season header
      html += '<div class="library-season-header" onclick="toggleLibrarySeason(\'' + sid + '\')">';
      html += '<div class="library-season-left">';
      html += '<span class="library-arrow" id="' + sid + 'Arrow">&#9654;</span>';
      html += '<span>Season ' + skey + ' (' + eps.length + ' ep)</span>';
      html += '</div>';
      html += '<div class="library-season-right">';
      html += '<span class="library-meta library-meta-size">' + formatSize(seasonSize) + '</span>';
      if (libraryCanDelete) html += '<button class="library-delete" onclick="event.stopPropagation();deleteLibraryItem(' + ti + ',' + skey + ',null)" title="Delete season">&times;</button>';
      html += '</div>';
      html += '</div>';

      // Season body (episodes)
      html += '<div class="library-season-body" id="' + sid + 'Body">';
      eps.forEach(function(ep) {
        html += '<div class="library-episode">';
        html += '<span class="library-ep-num">E' + String(ep.episode).padStart(3, '0') + '</span>';
        html += '<span class="library-ep-file">' + escLib(ep.file) + '</span>';
        html += '<span class="library-ep-size">' + formatSize(ep.size) + '</span>';
        if (libraryCanDelete) html += '<button class="library-delete" onclick="deleteLibraryItem(' + ti + ',' + skey + ',' + ep.episode + ')" title="Delete episode">&times;</button>';
        html += '</div>';
      });
      html += '</div>';
    });
    html += '</div>';
    html += '</div>';
  });

  list.innerHTML = html;
}

function toggleLibraryTitle(index) {
  const body = document.getElementById('libraryTitleBody' + index);
  const arrow = document.getElementById('libraryTitleArrow' + index);
  if (!body) return;
  const expanded = body.classList.toggle('expanded');
  if (arrow) arrow.classList.toggle('expanded', expanded);
}

function toggleLibrarySeason(id) {
  const body = document.getElementById(id + 'Body');
  const arrow = document.getElementById(id + 'Arrow');
  if (!body) return;
  const expanded = body.classList.toggle('expanded');
  if (arrow) arrow.classList.toggle('expanded', expanded);
}

async function deleteLibraryItem(titleIndex, season, episode) {
  const title = libraryTitles[titleIndex];
  if (!title) return;

  let msg;
  if (season === null && episode === null) {
    msg = 'Delete entire title "' + title.folder + '"?';
  } else if (episode === null) {
    msg = 'Delete all episodes from Season ' + season + ' in "' + title.folder + '"?';
  } else {
    msg = 'Delete S' + String(season).padStart(2, '0') + 'E' + String(episode).padStart(3, '0') + ' from "' + title.folder + '"?';
  }

  if (!confirm(msg)) return;

  try {
    const resp = await fetch('/api/library/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        folder: title.folder,
        season: season,
        episode: episode
      })
    });
    const data = await resp.json();
    if (data.error) {
      if (typeof showToast === 'function') showToast(data.error);
    } else {
      if (typeof showToast === 'function') showToast('Deleted successfully');
    }
    loadLibrary();
  } catch (e) {
    if (typeof showToast === 'function') showToast('Delete failed');
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

function escLib(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

// Load library on page init
loadLibrary();
