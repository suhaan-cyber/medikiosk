/* ═══════════════════════════════════════════════════════════════════
   MEDIKOISK — Backend API Bridge
   Replaces localStorage with real backend calls.
   Keeps Data.* synchronous by caching everything in memory after login.
   ═══════════════════════════════════════════════════════════════════ */
(function(){
'use strict';

const API_BASE = window.MEDIKOISK_API || 'http://localhost:8000';

const API = {
  base: API_BASE,
  token: (function(){ try { return localStorage.getItem('mk_token'); } catch(e){ return null; } })(),

  async request(method, path, body) {
    const headers = {};
    if (this.token) headers['Authorization'] = 'Bearer ' + this.token;

    let payload = body;
    if (body !== undefined && body !== null && !(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      payload = JSON.stringify(body);
    }

    let res;
    try {
      res = await fetch(this.base + path, { method, headers, body: payload });
    } catch (e) {
      throw new Error('Cannot reach backend at ' + this.base + ' — is it running?');
    }

    if (res.status === 401) {
      this.logout();
      throw new Error('Session expired — please sign in again');
    }

    const text = await res.text();
    let data = null;
    if (text) {
      try { data = JSON.parse(text); }
      catch (e) { data = text; }
    }

    if (!res.ok) {
      const msg = (data && (data.detail || data.message)) || ('Request failed (' + res.status + ')');
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  },

  get(p)      { return this.request('GET', p); },
  post(p, b)  { return this.request('POST', p, b); },
  patch(p, b) { return this.request('PATCH', p, b); },
  put(p, b)   { return this.request('PUT', p, b); },
  del(p)      { return this.request('DELETE', p); },

  logout() {
    this.token = null;
    try {
      localStorage.removeItem('mk_token');
      localStorage.removeItem('mk_user');
    } catch(e){}
  }
};

/* ── AUTH ────────────────────────────────────────────────────── */
API.auth = {
  register(payload)        { return API.post('/auth/register', payload); },
  login(email, pass, role) { return API.post('/auth/login', { email, password: pass, role }); },
  me()                     { return API.get('/auth/me'); },
  logout()                 { return API.post('/auth/logout', {}); }
};

/* ── BOOTSTRAP ───────────────────────────────────────────────── */
API.bootstrap = function() { return API.get('/bootstrap'); };

/* ── ASYNC MUTATIONS (fire-and-forget from Data.*) ───────────── */
function logErr(e){ console.warn('[MEDIKOISK sync]', e && e.message ? e.message : e); }

API.sync = {
  createAppointment(a)          { return API.post('/appointments', a).catch(logErr); },
  updateAppointment(id, patch)  { return API.patch('/appointments/' + id, patch).catch(logErr); },
  createPrescription(p)         { return API.post('/prescriptions', p).catch(logErr); },
  createReport(r)               { return API.post('/reports', r).catch(logErr); },
  updateReport(id, patch)       { return API.patch('/reports/' + id, patch).catch(logErr); },
  deleteReport(id)              { return API.del('/reports/' + id).catch(logErr); },
  createPayment(p)              { return API.post('/payments', p).catch(logErr); },
  addVitals(patientId, v)       { return API.post('/vitals', Object.assign({}, v, { patientId })).catch(logErr); },
  createChangeRequest(cr)       { return API.post('/change-requests', cr).catch(logErr); },
  updateChangeRequest(id, patch){ return API.patch('/change-requests/' + id, patch).catch(logErr); },
  updateUser(id, patch)         { return API.patch('/users/' + id, patch).catch(logErr); },
  setChats(messages)            { return API.put('/chats', { messages }).catch(logErr); },
  addTimeline(t)                { return API.post('/timeline', t).catch(logErr); }
};

window.API = API;
})();