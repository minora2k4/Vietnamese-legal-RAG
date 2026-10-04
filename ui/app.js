'use strict';
const $ = id => document.getElementById(id);
const chat = $('chat'), form = $('form'), input = $('input'), send = $('send');
const F = {status:$('f-status'), from:$('f-from'), to:$('f-to'), sokh:$('f-sokh'), search:$('f-search'), rerank:$('f-rerank')};
const DEF = {status:'con_hieu_luc', from:'', to:'', sokh:'', search:'10', rerank:'3'};

// ---------- Bộ lọc (lưu localStorage) ----------
try { const s = JSON.parse(localStorage.getItem('filters') || '{}'); for (const k in F) if (s[k] != null) F[k].value = s[k]; } catch {}
const saveFilters = () => { try { localStorage.setItem('filters', JSON.stringify(Object.fromEntries(Object.entries(F).map(([k, el]) => [k, el.value])))); } catch {} };
Object.values(F).forEach(el => el.addEventListener('change', saveFilters));
$('freset').onclick = () => { for (const k in F) F[k].value = DEF[k]; saveFilters(); };

const payload = query => {
  const num = el => el.value ? parseInt(el.value, 10) : null;
  return { query, top_search: +F.search.value, top_rerank: +F.rerank.value,
    filters: { status: F.status.value, year_from: num(F.from), year_to: num(F.to), so_ky_hieu: F.sokh.value.trim() || null } };
};

// ---------- Tiện ích ----------
const toBottom = () => { chat.scrollTop = chat.scrollHeight; };
const esc = s => s ? String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';
const md = s => DOMPurify.sanitize(marked.parse(s));
const fmtMs = ms => ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(2)} s`;
function add(cls, text) { const el = document.createElement('div'); el.className = cls; el.textContent = text; chat.appendChild(el); toBottom(); return el; }

function addLoading() {
  const el = document.createElement('div'); el.className = 'loading';
  el.innerHTML = '<span class="dots"><i></i><i></i><i></i></span><span>Đang tra cứu <b class="t">0.0 s</b></span>';
  chat.appendChild(el); toBottom();
  const t0 = performance.now(), t = el.querySelector('.t');
  const timer = setInterval(() => t.textContent = ((performance.now() - t0) / 1000).toFixed(1) + ' s', 100);
  return { remove() { clearInterval(timer); el.remove(); } };
}

// ---------- Gửi câu hỏi ----------
form.addEventListener('submit', async e => {
  e.preventDefault();
  const query = input.value.trim(); if (!query) return;
  $('empty')?.remove(); add('msg-user', query); input.value = ''; send.disabled = true;
  const loading = addLoading();
  try {
    const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload(query)) });
    const data = await res.json().catch(() => ({}));
    loading.remove();
    if (res.ok) await addAnswer(data);
    else add('error', typeof data.detail === 'string' ? data.detail : 'Dữ liệu bộ lọc không hợp lệ.');
  } catch { loading.remove(); add('error', 'Không thể kết nối tới máy chủ. Vui lòng thử lại.'); }
  finally { send.disabled = false; input.focus(); }
});

async function addAnswer({ answer, sources, timings }) {
  const wrap = document.createElement('div'); wrap.className = 'msg-ai';
  wrap.innerHTML = '<div class="answer"></div>'; chat.appendChild(wrap);
  showSources(sources);
  const el = wrap.querySelector('.answer');
  const words = (answer || '').split(' '), step = Math.max(1, Math.ceil(words.length / 50));
  for (let i = step; i < words.length + step; i += step) {
    el.innerHTML = md(words.slice(0, i).join(' ')); toBottom();
    await new Promise(r => setTimeout(r, 16));
  }
  const meta = document.createElement('div'); meta.className = 'meta';
  const copy = Object.assign(document.createElement('button'), { type: 'button', className: 'link-btn', textContent: 'Sao chép' });
  copy.onclick = () => navigator.clipboard.writeText(el.innerText).then(() => { copy.textContent = 'Đã sao chép'; setTimeout(() => copy.textContent = 'Sao chép', 1800); });
  meta.appendChild(copy);
  if (sources?.length) {
    const b = Object.assign(document.createElement('button'), { type: 'button', className: 'link-btn', textContent: `Xem căn cứ (${sources.length})` });
    b.onclick = () => showSources(sources);
    meta.appendChild(b);
  }
  if (timings) {
    const chip = (txt, cls = '') => meta.insertAdjacentHTML('beforeend', `<span class="time ${cls}">${txt}</span>`);
    chip(`Truy vấn ${fmtMs(timings.search_ms)}`);
    chip(`Rerank ${fmtMs(timings.rerank_ms)}`);
    chip(`LLM ${fmtMs(timings.llm_ms)}`);
    chip(`Tổng ${fmtMs(timings.total_ms)}`, 'total');
  }
  wrap.appendChild(meta); toBottom();
}

// ---------- Cột văn bản dẫn chiếu ----------
function fmt(t) {
  t = (t || '').replace(/\r/g, '').trim();
  if (!t.includes('\n')) t = t.replace(/(?<!Điều)\s+(?=\d{1,2}\.\s)/g, '\n').replace(/\s+(?=[a-zđ]\)\s)/g, '\n');
  return t.split(/\n+/).map(l => l.trim()).filter(Boolean).map(l => {
    const e = esc(l);
    if (/^Điều\s+\d+/i.test(l)) return `<p class="l-dieu">${e}</p>`;
    if (/^\d{1,2}\.\s/.test(l)) return `<p class="l-khoan">${e.replace(/^(\d{1,2}\.)/, '<b>$1</b>')}</p>`;
    if (/^[a-zđ]\)\s/.test(l)) return `<p class="l-diem">${e.replace(/^([a-zđ]\))/, '<b>$1</b>')}</p>`;
    return `<p>${e}</p>`;
  }).join('');
}

function showSources(sources) {
  const box = $('sources');
  $('srccount').textContent = sources?.length ? `(${sources.length})` : '';
  if (!sources?.length) { box.innerHTML = '<p class="hint">Không có văn bản nào được dẫn chiếu.</p>'; return; }
  box.innerHTML = sources.map((s, i) => {
    const ok = /còn hiệu lực/i.test(s.tinh_trang_hieu_luc || '');
    return `<article class="source">
      <div class="source-title">${i + 1}. ${esc(s.title)}</div>
      <div class="tags">
        <span class="tag">${esc(s.so_ky_hieu)}</span>
        <span class="tag gray">Vị trí: ${esc(s.partId)}</span>
        ${s.ngay_ban_hanh ? `<span class="tag gray">Ban hành: ${esc(s.ngay_ban_hanh)}</span>` : ''}
        <span class="tag ${ok ? '' : 'bad'}">${esc(s.tinh_trang_hieu_luc)}</span>
        <span class="tag gray">Độ phù hợp ${Math.round((s.rerank_score || 0) * 100)}%</span>
      </div>
      <div class="source-text">${fmt(s.text)}</div>
    </article>`;
  }).join('');
  box.scrollTop = 0;
}