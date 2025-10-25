// assets/js/app.js
async function sha256hex(message) {
  const enc = new TextEncoder();
  const data = enc.encode(message);
  const hash = await crypto.subtle.digest('SHA-256', data);
  // convert to hex
  const bytes = Array.from(new Uint8Array(hash));
  return bytes.map(b => b.toString(16).padStart(2,'0')).join('');
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const user = document.getElementById('username').value.trim();
  const pass = document.getElementById('password').value;

  const msgEl = document.getElementById('message');
  msgEl.textContent = 'Procesando...';

  try {
    // 1) client-side hash (reduces exposure of raw password on the wire)
    const clientHash = await sha256hex(pass);

    // 2) send to netlify function
    const res = await fetch('/.netlify/functions/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password_hash: clientHash })
    });

    if (!res.ok) {
      const err = await res.json().catch(()=>({error:'unknown'}));
      msgEl.innerHTML = `<span style="color:#d9534f">Error: ${err.error || res.statusText}</span>`;
      return;
    }

    const payload = await res.json();
    // payload: { token, username }
    localStorage.setItem('gategroup_demo_token', payload.token);
    msgEl.innerHTML = `<span style="color:green">Autenticación exitosa — Bienvenido ${payload.username}</span>`;
  } catch (err) {
    console.error(err);
    msgEl.innerHTML = `<span style="color:#d9534f">Error de conexión</span>`;
  }
});
