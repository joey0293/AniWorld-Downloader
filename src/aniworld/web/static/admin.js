const userTableBody = document.getElementById('userTableBody');

loadUsers();

async function loadUsers() {
  try {
    const resp = await fetch('/admin/api/users');
    const data = await resp.json();
    renderUsers(data.users || []);
  } catch (e) {
    showToast('Failed to load users: ' + e.message);
  }
}

function renderUsers(users) {
  const adminCount = users.filter(u => u.role === 'admin').length;
  userTableBody.innerHTML = '';
  users.forEach(u => {
    const isLastAdmin = u.role === 'admin' && adminCount <= 1;
    const tr = document.createElement('tr');
    const authMethod = u.auth_method || 'local';
    const authBadge = authMethod === 'oidc'
      ? '<span class="auth-badge auth-sso">SSO</span>'
      : '<span class="auth-badge auth-local">Local</span>';
    tr.innerHTML =
      `<td>${u.id}</td>` +
      `<td>${esc(u.username)}</td>` +
      `<td>
        <select onchange="changeRole(${u.id}, this.value)" ${isLastAdmin ? 'disabled' : ''}>
          <option value="user" ${u.role === 'user' ? 'selected' : ''}>User</option>
          <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
        </select>
      </td>` +
      `<td>${authBadge}</td>` +
      `<td>${esc(u.created_at)}</td>` +
      `<td>${isLastAdmin
        ? '<span style="color:#555">protected</span>'
        : `<button class="btn-del" onclick="deleteUser(${u.id})">Delete</button>`
      }</td>`;
    userTableBody.appendChild(tr);
  });
}

async function addUser() {
  const username = document.getElementById('newUsername').value.trim();
  const password = document.getElementById('newPassword').value;
  const role = document.getElementById('newRole').value;

  if (!username || !password) { showToast('Username and password required'); return; }

  try {
    const resp = await fetch('/admin/api/users', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password, role})
    });
    const data = await resp.json();
    if (data.error) { showToast(data.error); return; }
    document.getElementById('newUsername').value = '';
    document.getElementById('newPassword').value = '';
    showToast('User created');
    loadUsers();
  } catch (e) {
    showToast('Failed to create user: ' + e.message);
  }
}

async function deleteUser(id) {
  if (!confirm('Delete this user?')) return;
  try {
    const resp = await fetch(`/admin/api/users/${id}`, {method: 'DELETE'});
    const data = await resp.json();
    if (data.error) { showToast(data.error); return; }
    showToast('User deleted');
    loadUsers();
  } catch (e) {
    showToast('Failed to delete user: ' + e.message);
  }
}

async function changeRole(id, newRole) {
  try {
    const resp = await fetch(`/admin/api/users/${id}/role`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({role: newRole})
    });
    const data = await resp.json();
    if (data.error) { showToast(data.error); loadUsers(); return; }
    showToast('Role updated');
    loadUsers();
  } catch (e) {
    showToast('Failed to update role: ' + e.message);
  }
}

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
