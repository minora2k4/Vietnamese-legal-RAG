'use strict';
// Giao diện chat: gửi câu hỏi tới POST /api/chat, hiển thị câu trả lời (markdown) và cột văn bản dẫn chiếu.

function getElement(id) {
  return document.getElementById(id);
}

const chatBox = getElement('chat');
const questionForm = getElement('form');
const questionInput = getElement('input');
const sendButton = getElement('send');

// Các ô bộ lọc (id trong index.html) và giá trị mặc định
const filterInputs = {
  status: getElement('f-status'),
  from: getElement('f-from'),
  to: getElement('f-to'),
  soKyHieu: getElement('f-sokh'),
  search: getElement('f-search'),
  rerank: getElement('f-rerank'),
};
const defaultFilters = {
  status: 'dang_ap_dung',
  from: '',
  to: '',
  soKyHieu: '',
  search: '10',
  rerank: '3',
};

// ---------- Bộ lọc (lưu localStorage) ----------
// Khóa 'filters_v2': bộ lọc lưu từ bản cũ (mặc định "Còn hiệu lực") không được đè lên mặc định mới "Đang áp dụng"
const filterStorageKey = 'filters_v2';

function loadFilters() {
  let savedFilters;
  try {
    savedFilters = JSON.parse(localStorage.getItem(filterStorageKey) || '{}');
  } catch {
    return;
  }
  if (typeof savedFilters !== 'object' || savedFilters === null) {
    return;
  }
  // 'sokh': tên khóa ở các bản trước, vẫn đọc để giữ bộ lọc người dùng đã lưu
  if (savedFilters.soKyHieu == null && savedFilters.sokh != null) {
    savedFilters.soKyHieu = savedFilters.sokh;
  }
  for (const name in filterInputs) {
    if (savedFilters[name] != null) {
      filterInputs[name].value = savedFilters[name];
    }
  }
}

function saveFilters() {
  const values = {};
  for (const name in filterInputs) {
    values[name] = filterInputs[name].value;
  }
  try {
    localStorage.setItem(filterStorageKey, JSON.stringify(values));
  } catch {
    // Trình duyệt chặn localStorage: bỏ qua, bộ lọc chỉ không được nhớ cho lần sau
  }
}

function resetFilters() {
  for (const name in filterInputs) {
    filterInputs[name].value = defaultFilters[name];
  }
  saveFilters();
}

loadFilters();
for (const name in filterInputs) {
  filterInputs[name].addEventListener('change', saveFilters);
}
getElement('freset').onclick = resetFilters;

// Nội dung request gửi cho API (tên trường phải khớp ChatRequest trong main.py)
function toNumberOrNull(input) {
  if (!input.value) {
    return null;
  }
  return parseInt(input.value, 10);
}

function buildRequestBody(query) {
  return {
    query: query,
    top_search: Number(filterInputs.search.value),
    top_rerank: Number(filterInputs.rerank.value),
    filters: {
      status: filterInputs.status.value,
      year_from: toNumberOrNull(filterInputs.from),
      year_to: toNumberOrNull(filterInputs.to),
      so_ky_hieu: filterInputs.soKyHieu.value.trim() || null,
    },
  };
}

// ---------- Tiện ích ----------
function scrollToBottom() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(text) {
  if (!text) {
    return '';
  }
  return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderMarkdown(text) {
  return DOMPurify.sanitize(marked.parse(text));
}

function formatDuration(milliseconds) {
  if (milliseconds < 1000) {
    return `${milliseconds} ms`;
  }
  return `${(milliseconds / 1000).toFixed(2)} s`;
}

function addMessage(className, text) {
  const element = document.createElement('div');
  element.className = className;
  element.textContent = text;
  chatBox.appendChild(element);
  scrollToBottom();
  return element;
}

// Dòng "Đang tra cứu ... s" có đồng hồ đếm thời gian, trả về đối tượng có hàm remove()
function addLoadingIndicator() {
  const element = document.createElement('div');
  element.className = 'loading';
  element.innerHTML = '<span class="dots"><i></i><i></i><i></i></span><span>Đang tra cứu <b class="t">0.0 s</b></span>';
  chatBox.appendChild(element);
  scrollToBottom();

  const startTime = performance.now();
  const timerLabel = element.querySelector('.t');
  const timer = setInterval(function () {
    const seconds = (performance.now() - startTime) / 1000;
    timerLabel.textContent = seconds.toFixed(1) + ' s';
  }, 100);

  return {
    remove() {
      clearInterval(timer);
      element.remove();
    },
  };
}

// ---------- Gửi câu hỏi ----------
async function handleSubmit(event) {
  event.preventDefault();
  const query = questionInput.value.trim();
  if (!query) {
    return;
  }

  const emptyState = getElement('empty');
  if (emptyState) {
    emptyState.remove();
  }
  addMessage('msg-user', query);
  questionInput.value = '';
  sendButton.disabled = true;
  const loadingIndicator = addLoadingIndicator();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildRequestBody(query)),
    });
    let data;
    try {
      data = await response.json();
    } catch {
      data = {};
    }
    loadingIndicator.remove();

    if (response.ok) {
      await addAnswer(data);
    } else if (typeof data.detail === 'string') {
      addMessage('error', data.detail);
    } else {
      addMessage('error', 'Dữ liệu bộ lọc không hợp lệ.');
    }
  } catch {
    loadingIndicator.remove();
    addMessage('error', 'Không thể kết nối tới máy chủ. Vui lòng thử lại.');
  } finally {
    sendButton.disabled = false;
    questionInput.focus();
  }
}

questionForm.addEventListener('submit', handleSubmit);

function wait(milliseconds) {
  return new Promise(function (resolve) {
    setTimeout(resolve, milliseconds);
  });
}

function createLinkButton(text) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'link-btn';
  button.textContent = text;
  return button;
}

// Hiển thị câu trả lời dần dần (khoảng 50 bước), kèm nút sao chép, nút xem căn cứ và thời gian từng bước
async function addAnswer(data) {
  const answer = data.answer || '';
  const sources = data.sources;
  const timings = data.timings;

  const wrapper = document.createElement('div');
  wrapper.className = 'msg-ai';
  wrapper.innerHTML = '<div class="answer"></div>';
  chatBox.appendChild(wrapper);
  showSources(sources);

  const answerElement = wrapper.querySelector('.answer');
  const words = answer.split(' ');
  const wordsPerStep = Math.max(1, Math.ceil(words.length / 50));
  for (let wordCount = wordsPerStep; wordCount < words.length + wordsPerStep; wordCount += wordsPerStep) {
    const partialAnswer = words.slice(0, wordCount).join(' ');
    answerElement.innerHTML = renderMarkdown(partialAnswer);
    scrollToBottom();
    await wait(16);
  }

  const footer = document.createElement('div');
  footer.className = 'meta';

  const copyButton = createLinkButton('Sao chép');
  copyButton.onclick = async function () {
    await navigator.clipboard.writeText(answerElement.innerText);
    copyButton.textContent = 'Đã sao chép';
    setTimeout(function () {
      copyButton.textContent = 'Sao chép';
    }, 1800);
  };
  footer.appendChild(copyButton);

  if (sources && sources.length) {
    const sourcesButton = createLinkButton(`Xem căn cứ (${sources.length})`);
    sourcesButton.onclick = function () {
      showSources(sources);
    };
    footer.appendChild(sourcesButton);
  }

  if (timings) {
    addTimeChip(footer, `Truy vấn ${formatDuration(timings.search_ms)}`, '');
    addTimeChip(footer, `Rerank ${formatDuration(timings.rerank_ms)}`, '');
    addTimeChip(footer, `LLM ${formatDuration(timings.llm_ms)}`, '');
    addTimeChip(footer, `Tổng ${formatDuration(timings.total_ms)}`, 'total');
  }
  wrapper.appendChild(footer);
  scrollToBottom();
}

function addTimeChip(container, text, className) {
  container.insertAdjacentHTML('beforeend', `<span class="time ${className}">${text}</span>`);
}

// ---------- Cột văn bản dẫn chiếu ----------
// Một dòng nội dung Điều -> thẻ <p> theo cấp: Điều / Khoản ("1.") / Điểm ("a)")
function formatLegalLine(line) {
  const escaped = escapeHtml(line);
  if (/^Điều\s+\d+/i.test(line)) {
    return `<p class="l-dieu">${escaped}</p>`;
  }
  if (/^\d{1,2}\.\s/.test(line)) {
    return `<p class="l-khoan">${escaped.replace(/^(\d{1,2}\.)/, '<b>$1</b>')}</p>`;
  }
  if (/^[a-zđ]\)\s/.test(line)) {
    return `<p class="l-diem">${escaped.replace(/^([a-zđ]\))/, '<b>$1</b>')}</p>`;
  }
  return `<p>${escaped}</p>`;
}

// Tách nội dung Điều thành các dòng để hiển thị thụt lề
function formatLegalText(text) {
  text = (text || '').replace(/\r/g, '').trim();
  // Nội dung bị dồn thành một dòng: tự xuống dòng trước số khoản và chữ cái điểm
  if (!text.includes('\n')) {
    text = text.replace(/(?<!Điều)\s+(?=\d{1,2}\.\s)/g, '\n');
    text = text.replace(/\s+(?=[a-zđ]\)\s)/g, '\n');
  }
  const paragraphs = [];
  for (const rawLine of text.split(/\n+/)) {
    const line = rawLine.trim();
    if (line) {
      paragraphs.push(formatLegalLine(line));
    }
  }
  return paragraphs.join('');
}

function formatSource(source, index) {
  const isInForce = /còn hiệu lực/i.test(source.tinh_trang_hieu_luc || '');
  let statusClass = 'bad';
  if (isInForce) {
    statusClass = '';
  }
  let issueDateTag = '';
  if (source.ngay_ban_hanh) {
    issueDateTag = `<span class="tag gray">Ban hành: ${escapeHtml(source.ngay_ban_hanh)}</span>`;
  }
  const relevancePercent = Math.round((source.rerank_score || 0) * 100);
  return `<article class="source">
      <div class="source-title">${index + 1}. ${escapeHtml(source.title)}</div>
      <div class="tags">
        <span class="tag">${escapeHtml(source.so_ky_hieu)}</span>
        <span class="tag gray">Vị trí: ${escapeHtml(source.partId)}</span>
        ${issueDateTag}
        <span class="tag ${statusClass}">${escapeHtml(source.tinh_trang_hieu_luc)}</span>
        <span class="tag gray">Độ phù hợp ${relevancePercent}%</span>
      </div>
      <div class="source-text">${formatLegalText(source.text)}</div>
    </article>`;
}

function showSources(sources) {
  const sourcesBox = getElement('sources');
  const hasSources = Boolean(sources && sources.length);
  if (hasSources) {
    getElement('srccount').textContent = `(${sources.length})`;
  } else {
    getElement('srccount').textContent = '';
    sourcesBox.innerHTML = '<p class="hint">Không có văn bản nào được dẫn chiếu.</p>';
    return;
  }

  const articles = [];
  sources.forEach(function (source, index) {
    articles.push(formatSource(source, index));
  });
  sourcesBox.innerHTML = articles.join('');
  sourcesBox.scrollTop = 0;
}
