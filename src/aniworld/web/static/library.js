let libraryLocations = [];

async function loadLibrary() {
  const list = document.getElementById('libraryList');
  list.innerHTML = '<div class="library-empty">Loading...</div>';
  try {
    const resp = await fetch('/api/library');
    const data = await resp.json();
    libraryLocations = data.locations || [];
    renderLibrary(libraryLocations);
  } catch (e) {
    list.innerHTML = '<div class="library-empty">Failed to load library</div>';
  }
}

function renderLibrary(locations) {
  const list = document.getElementById('libraryList');
  if (!locations.length) {
    list.innerHTML = '<div class="library-empty">No downloaded content found</div>';
    return;
  }

  let html = '';
  locations.forEach(function(loc, li) {
    var locTotalEps = 0;
    var locTotalSize = 0;
    loc.titles.forEach(function(t) { locTotalEps += t.total_episodes; locTotalSize += t.total_size; });

    // Location header
    html += '<div class="library-title-section">';
    html += '<div class="library-location-header" onclick="toggleLibraryLocation(' + li + ')">';
    html += '<div class="library-title-left">';
    html += '<span class="library-arrow" id="libraryLocArrow' + li + '">&#9654;</span>';
    html += '<span class="library-title-name" style="font-weight:600;color:#fff">' + escLib(loc.label) + '</span>';
    html += '</div>';
    html += '<div class="library-title-right">';
    html += '<span class="library-meta">' + locTotalEps + ' ep</span>';
    html += '<span class="library-meta library-meta-size">' + formatSize(locTotalSize) + '</span>';
    html += '</div>';
    html += '</div>';

    // Location body (titles)
    html += '<div class="library-title-body" id="libraryLocBody' + li + '">';
    loc.titles.forEach(function(title, ti) {
      var globalTi = 'L' + li + 'T' + ti;
      var seasonKeys = Object.keys(title.seasons).sort(function(a, b) { return parseInt(a) - parseInt(b); });

      // Title header
      html += '<div class="library-title-section">';
      html += '<div class="library-title-header" onclick="toggleLibraryTitle(\'' + globalTi + '\')" style="padding-left:32px">';
      html += '<div class="library-title-left">';
      html += '<span class="library-arrow" id="libraryTitleArrow' + globalTi + '">&#9654;</span>';
      html += '<span class="library-title-name">' + escLib(title.folder) + '</span>';
      html += '</div>';
      html += '<div class="library-title-right">';
      html += '<span class="library-meta">' + title.total_episodes + ' ep</span>';
      html += '<span class="library-meta library-meta-size">' + formatSize(title.total_size) + '</span>';
      if (libraryCanDelete) html += '<button class="library-delete" onclick="event.stopPropagation();deleteLibraryItem(' + li + ',' + ti + ',null,null)" title="Delete title">&times;</button>';
      html += '</div>';
      html += '</div>';

      // Title body (seasons)
      html += '<div class="library-title-body" id="libraryTitleBody' + globalTi + '">';
      seasonKeys.forEach(function(skey) {
        var eps = title.seasons[skey];
        var sid = 'libS' + globalTi + '_' + skey;
        var seasonSize = eps.reduce(function(acc, e) { return acc + e.size; }, 0);

        // Season header
        html += '<div class="library-season-header" onclick="toggleLibrarySeason(\'' + sid + '\')" style="padding-left:48px">';
        html += '<div class="library-season-left">';
        html += '<span class="library-arrow" id="' + sid + 'Arrow">&#9654;</span>';
        html += '<span>Season ' + skey + ' (' + eps.length + ' ep)</span>';
        html += '</div>';
        html += '<div class="library-season-right">';
        html += '<span class="library-meta library-meta-size">' + formatSize(seasonSize) + '</span>';
        if (libraryCanDelete) html += '<button class="library-delete" onclick="event.stopPropagation();deleteLibraryItem(' + li + ',' + ti + ',' + skey + ',null)" title="Delete season">&times;</button>';
        html += '</div>';
        html += '</div>';

        // Season body (episodes)
        html += '<div class="library-season-body" id="' + sid + 'Body">';
        eps.forEach(function(ep) {
          html += '<div class="library-episode" style="padding-left:64px">';
          html += '<span class="library-ep-num">E' + String(ep.episode).padStart(3, '0') + '</span>';
          html += '<span class="library-ep-file">' + escLib(ep.file) + '</span>';
          html += '<span class="library-ep-size">' + formatSize(ep.size) + '</span>';
          if (libraryCanDelete) html += '<button class="library-delete" onclick="deleteLibraryItem(' + li + ',' + ti + ',' + skey + ',' + ep.episode + ')" title="Delete episode">&times;</button>';
          html += '</div>';
        });
        html += '</div>';
      });
      html += '</div>';
      html += '</div>';
    });
    html += '</div>';
    html += '</div>';
  });

  list.innerHTML = html;
}

function toggleLibraryLocation(index) {
  var body = document.getElementById('libraryLocBody' + index);
  var arrow = document.getElementById('libraryLocArrow' + index);
  if (!body) return;
  var expanded = body.classList.toggle('expanded');
  if (arrow) arrow.classList.toggle('expanded', expanded);
}

function toggleLibraryTitle(id) {
  var body = document.getElementById('libraryTitleBody' + id);
  var arrow = document.getElementById('libraryTitleArrow' + id);
  if (!body) return;
  var expanded = body.classList.toggle('expanded');
  if (arrow) arrow.classList.toggle('expanded', expanded);
}

function toggleLibrarySeason(id) {
  var body = document.getElementById(id + 'Body');
  var arrow = document.getElementById(id + 'Arrow');
  if (!body) return;
  var expanded = body.classList.toggle('expanded');
  if (arrow) arrow.classList.toggle('expanded', expanded);
}

async function deleteLibraryItem(locIndex, titleIndex, season, episode) {
  var loc = libraryLocations[locIndex];
  if (!loc) return;
  var title = loc.titles[titleIndex];
  if (!title) return;

  var msg;
  if (season === null && episode === null) {
    msg = 'Delete entire title "' + title.folder + '" from ' + loc.label + '?';
  } else if (episode === null) {
    msg = 'Delete all episodes from Season ' + season + ' in "' + title.folder + '" (' + loc.label + ')?';
  } else {
    msg = 'Delete S' + String(season).padStart(2, '0') + 'E' + String(episode).padStart(3, '0') + ' from "' + title.folder + '" (' + loc.label + ')?';
  }

  if (!confirm(msg)) return;

  try {
    var resp = await fetch('/api/library/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        folder: title.folder,
        season: season,
        episode: episode,
        custom_path_id: loc.custom_path_id
      })
    });
    var data = await resp.json();
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
  var d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

// Load library on page init
loadLibrary();
