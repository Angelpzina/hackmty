// netlify/functions/login.js
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// Load secret from env
const SECRET = process.env.JWT_SECRET || 'changeme_demo_secret';

// ---- Demo bootstrap user ----
// WARNING: This is a demo only. In production you'll have persistent user storage.
const demoUsername = 'demo';
const demoRawPassword = 'Password123!'; // shown in demo UI above

// compute sha256(demoRawPassword)
function sha256hexNode(str) {
  return crypto.createHash('sha256').update(str, 'utf8').digest('hex');
}

// on cold start, build the bcrypt hash of sha256(demoRawPassword)
const demoClientHash = sha256hexNode(demoRawPassword); // this is what client sends after hashing
const demoStoredBcryptHash = bcrypt.hashSync(demoClientHash, 10);

// simple in-memory user store
const USERS = {
  [demoUsername]: {
    username: demoUsername,
    password_bcrypt: demoStoredBcryptHash,
    role: 'demo'
  }
};

// Handler
exports.handler = async function(event, context) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch (err) {
    return { statusCode: 400, body: JSON.stringify({ error: 'Invalid JSON' }) };
  }

  const { username, password_hash } = body;
  if (!username || !password_hash) {
    return { statusCode: 400, body: JSON.stringify({ error: 'username and password_hash required' }) };
  }

  const user = USERS[username];
  if (!user) {
    await delay(300); // small delay to avoid fast user enumeration
    return { statusCode: 401, body: JSON.stringify({ error: 'Invalid credentials' }) };
  }

  // Compare the client-side SHA256 hash (password_hash) with stored bcrypt of sha256(password)
  const match = await bcrypt.compare(password_hash, user.password_bcrypt);
  if (!match) {
    return { statusCode: 401, body: JSON.stringify({ error: 'Invalid credentials' }) };
  }

  // Build a signed JWT (short lived)
  const token = jwt.sign({ username: user.username, role: user.role }, SECRET, { expiresIn: '2h' });

  return {
    statusCode: 200,
    body: JSON.stringify({ token, username: user.username })
  };
};

// small helper
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
