/**
 * app.js — Insight Narrator AI Frontend
 * Handles: file upload, drag-and-drop, API communication, dashboard rendering
 */

// ── DOM References ──────────────────────────────────────────────────────────
const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const dashboard = document.getElementById('dashboard');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const sampleBtn = document.getElementById('sample-btn');
const resetBtn = document.getElementById('reset-btn');
const loadingStatus = document.getElementById('loading-status');
const errorToast = document.getElementById('error-toast');

// Agent pipeline nodes
const nodeAnalyzer = document.getElementById('node-analyzer');
const nodeVisualizer = document.getElementById('node-visualizer');
const nodeNarrator = document.getElementById('node-narrator');

// ── Upload Handling ─────────────────────────────────────────────────────────
browseBtn.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') fileInput.click();
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

// Drag & Drop
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// Sample dataset shortcut
sampleBtn.addEventListener('click', async () => {
  try {
    const resp = await fetch('/data/sample_sales.csv');
    const blob = await resp.blob();
    const file = new File([blob], 'sample_sales.csv', { type: 'text/csv' });
    handleFile(file);
  } catch (err) {
    // Fallback: just trigger file input
    showError('Could not auto-load sample. Please upload it from the data/ folder manually.');
  }
});

resetBtn.addEventListener('click', resetUI);

// ── Core Flow ───────────────────────────────────────────────────────────────
async function handleFile(file) {
  const allowed = ['.csv', '.xls', '.xlsx'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showError('Unsupported file type. Please upload a CSV or Excel file.');
    return;
  }

  showLoading();

  const formData = new FormData();
  formData.append('file', file);

  // Animate pipeline nodes
  animatePipeline();

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Server error: ${response.status}`);
    }

    renderDashboard(data);
  } catch (err) {
    hideLoading();
    showUpload();
    showError(err.message || 'Analysis failed. Please try again.');
  }
}

// ── Pipeline Animation ──────────────────────────────────────────────────────
let pipelineTimer = null;
function animatePipeline() {
  const steps = [
    { node: nodeAnalyzer, status: '🔬 Analyzer Agent running statistical analysis…' },
    { node: nodeVisualizer, status: '📈 Visualizer Agent generating charts…' },
    { node: nodeNarrator, status: '✍️ Narrator Agent crafting the story…' },
  ];

  // Reset
  [nodeAnalyzer, nodeVisualizer, nodeNarrator].forEach(n => {
    n.classList.remove('active', 'done');
  });

  let i = 0;
  function nextStep() {
    if (i > 0) {
      steps[i - 1].node.classList.remove('active');
      steps[i - 1].node.classList.add('done');
    }
    if (i < steps.length) {
      steps[i].node.classList.add('active');
      loadingStatus.textContent = steps[i].status;
      i++;
      pipelineTimer = setTimeout(nextStep, 1800);
    }
  }
  nextStep();
}

// ── UI State Helpers ────────────────────────────────────────────────────────
function showLoading() {
  uploadSection.style.display = 'none';
  loadingSection.style.display = 'block';
  dashboard.style.display = 'none';
}
function hideLoading() {
  loadingSection.style.display = 'none';
  if (pipelineTimer) clearTimeout(pipelineTimer);
}
function showUpload() {
  uploadSection.style.display = 'block';
  dashboard.style.display = 'none';
  fileInput.value = '';
}
function showDashboard() {
  hideLoading();
  uploadSection.style.display = 'none';
  dashboard.style.display = 'block';
}
function resetUI() {
  showUpload();
}

// ── Error Toast ─────────────────────────────────────────────────────────────
let errorTimer = null;
function showError(msg) {
  errorToast.textContent = '⚠️ ' + msg;
  errorToast.style.display = 'block';
  if (errorTimer) clearTimeout(errorTimer);
  errorTimer = setTimeout(() => {
    errorToast.style.display = 'none';
  }, 6000);
}

// ── Dashboard Rendering ─────────────────────────────────────────────────────
function renderDashboard(result) {
  // Mark all pipeline nodes done
  [nodeAnalyzer, nodeVisualizer, nodeNarrator].forEach(n => {
    n.classList.remove('active');
    n.classList.add('done');
  });
  setTimeout(() => {
    showDashboard();
    renderOverview(result);
    renderPipelineLog(result.pipeline_log, result.total_elapsed_s);
    renderInsights(result.insights);
    renderCharts(result.charts);
    renderNarrative(result.narrative);
  }, 600);
}

// Overview Cards
function renderOverview(result) {
  const ov = result.insights.overview;
  const grid = document.getElementById('overview-grid');
  const cards = [
    { icon: '📋', value: ov.rows.toLocaleString(), label: 'Total Rows', accent: 'var(--accent-cyan)' },
    { icon: '🏛️', value: ov.columns, label: 'Columns', accent: 'var(--accent-violet)' },
    { icon: '🔢', value: ov.numeric_count, label: 'Numeric Columns', accent: 'var(--accent-teal)' },
    { icon: '🏷️', value: ov.categorical_count, label: 'Categorical', accent: 'var(--accent-amber)' },
    { icon: '❓', value: ov.total_missing.toLocaleString(), label: 'Missing Values', accent: ov.total_missing > 0 ? 'var(--accent-pink)' : 'var(--accent-green)' },
    { icon: '⚡', value: result.total_elapsed_s + 's', label: 'Analysis Time', accent: 'var(--accent-green)' },
  ];

  grid.innerHTML = cards.map(c => `
    <div class="stat-card" style="--card-accent: linear-gradient(90deg, ${c.accent}, transparent);">
      <span class="stat-icon">${c.icon}</span>
      <div class="stat-value">${c.value}</div>
      <div class="stat-label">${c.label}</div>
    </div>
  `).join('');
}

// Pipeline Log
function renderPipelineLog(log, total) {
  const container = document.getElementById('pipeline-log');
  container.innerHTML = log.map(entry => `
    <div class="log-item">
      <span class="tick">✓</span>
      <strong>${entry.agent}</strong>
      <span class="log-time">${entry.elapsed_s}s</span>
    </div>
  `).join('') + `
    <div class="log-item" style="border-color:rgba(0,212,255,0.3);color:var(--accent-cyan);">
      🏁 Total: <strong>${total}s</strong>
    </div>
  `;
}

// Key Insights
function renderInsights(insights) {
  const grid = document.getElementById('insights-grid');
  const topIns = insights.top_insights || [];

  if (topIns.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem;">No strong patterns detected in this dataset.</p>';
    return;
  }

  // Use marked.js to parse inline markdown in insight strings
  grid.innerHTML = topIns.map((text, i) => `
    <div class="insight-card fade-in" style="animation-delay:${i * 0.08}s;">
      ${marked.parseInline(text)}
    </div>
  `).join('');

  // Add descriptive stat cards for numeric cols (up to 3)
  const stats = insights.descriptive_stats || {};
  const statCards = Object.entries(stats).slice(0, 3).map(([col, s]) => `
    <div class="insight-card" style="display:grid;grid-template-columns:1fr 1fr;gap:8px 20px;">
      <div style="grid-column:1/-1;font-weight:600;color:var(--text-primary);font-size:0.9rem;margin-bottom:4px;">
        📊 ${col}
      </div>
      ${[['Mean', s.mean], ['Median', s.median], ['Min', s.min], ['Max', s.max]].map(([k, v]) => `
        <div>
          <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;">${k}</div>
          <div style="font-weight:600;color:var(--text-primary);font-size:0.9rem;">${fmtNum(v)}</div>
        </div>
      `).join('')}
    </div>
  `).join('');
  grid.innerHTML += statCards;
}

// Charts
function renderCharts(charts) {
  const grid = document.getElementById('charts-grid');
  if (!charts || charts.length === 0) {
    grid.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem;">No visualizations generated.</p>';
    return;
  }
  grid.innerHTML = charts.map((chart, i) => `
    <div class="chart-card fade-in" style="animation-delay:${i * 0.1}s;">
      <div class="chart-title">${chart.title}</div>
      <img src="data:image/png;base64,${chart.image}"
           alt="${chart.title}" loading="lazy" />
    </div>
  `).join('');
}

// Narrative Story
function renderNarrative(narrative) {
  const sourceEl = document.getElementById('narrative-source');
  const sectionsEl = document.getElementById('narrative-sections');

  const sourceLabel = narrative.source === 'openai'
    ? '✨ GPT-4o Narrative'
    : '🤖 AI Rule-Based Narrative';
  sourceEl.textContent = sourceLabel;

  if (narrative.sections && narrative.sections.length > 0) {
    sectionsEl.innerHTML = narrative.sections.map((s, i) => `
      <div class="narrative-section-item fade-in" style="animation-delay:${i * 0.15}s;">
        <div class="narrative-section-title">${s.title}</div>
        <div class="narrative-section-content" id="ns-content-${i}"></div>
      </div>
    `).join('');

    // Typewriter effect for each section, staggered
    narrative.sections.forEach((section, i) => {
      const contentEl = document.getElementById(`ns-content-${i}`);
      setTimeout(() => {
        renderMarkdownWithTypewriter(contentEl, processMarkdown(section.content), i === narrative.sections.length - 1);
      }, i * 260);
    });
  } else {
    sectionsEl.innerHTML = `<div class="narrative-section-content">${processMarkdown(narrative.story)}</div>`;
  }
}

// Process markdown bold syntax to HTML strong tags
function processMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

// Typewriter animation
function renderMarkdownWithTypewriter(el, htmlContent, addCursor = false) {
  // Strip HTML tags for typed version, then reveal formatted version
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = htmlContent;
  const plainText = tempDiv.textContent || '';

  let i = 0;
  const delay = Math.max(8, Math.min(20, 1500 / plainText.length));

  function type() {
    if (i < plainText.length) {
      el.textContent = plainText.slice(0, i + 1);
      i++;
      setTimeout(type, delay);
    } else {
      // Replace with fully formatted version
      el.innerHTML = htmlContent;
      if (addCursor) {
        const cursor = document.createElement('span');
        cursor.className = 'cursor';
        el.appendChild(cursor);
        setTimeout(() => cursor.remove(), 3000);
      }
    }
  }
  type();
}

// ── Formatters ──────────────────────────────────────────────────────────────
function fmtNum(v) {
  if (v === null || v === undefined) return '—';
  const n = parseFloat(v);
  return isNaN(n) ? v : n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
