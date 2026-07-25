/**
 * OKF Planning Discovery Bundle Web Application
 */

document.addEventListener('DOMContentLoaded', async () => {
  const datasetGrid = document.getElementById('dataset-grid');
  const searchInput = document.getElementById('search-input');
  const recordCountEl = document.getElementById('record-count');
  const codeViewer = document.getElementById('code-viewer');
  
  let allRecords = [];
  let filteredRecords = [];

  // Fetch overview & record shard
  try {
    const shardResp = await fetch('data/records/shard-0.json');
    const shardData = await shardResp.json();
    allRecords = shardData.records || [];
    filteredRecords = [...allRecords];
    renderRecords();
    setupFilters();
  } catch (err) {
    console.error('Failed to load dataset records:', err);
  }

  // Render cards
  function renderRecords() {
    if (!datasetGrid) return;
    datasetGrid.innerHTML = '';
    recordCountEl.textContent = `${filteredRecords.length} records matching search`;

    filteredRecords.forEach(rec => {
      const card = document.createElement('div');
      card.className = 'dataset-card';

      const tagClass = `tag-${rec.typology || 'geography'}`;
      card.innerHTML = `
        <div>
          <div class="card-header">
            <div class="card-tags">
              <span class="tag ${tagClass}">${rec.typology || 'geography'}</span>
              <span class="tag" style="background: rgba(255,255,255,0.1); color: #94a3b8">${rec.phase || 'beta'}</span>
            </div>
            <h3 class="card-title">${rec.title}</h3>
            <p class="card-desc">${rec.description || 'No description provided.'}</p>
          </div>
        </div>
        <div class="card-meta">
          <span>Entities: <strong>${(rec.entity_count || 0).toLocaleString()}</strong></span>
          <span>Publisher: ${rec.publisher || 'MHCLG'}</span>
        </div>
      `;
      datasetGrid.appendChild(card);
    });
  }

  // Filter setup
  function setupFilters() {
    searchInput?.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      filteredRecords = allRecords.filter(r => 
        r.title.toLowerCase().includes(term) ||
        r.description.toLowerCase().includes(term) ||
        (r.collection && r.collection.toLowerCase().includes(term))
      );
      renderRecords();
    });

    document.querySelectorAll('.filter-checkbox input').forEach(cb => {
      cb.addEventListener('change', () => {
        const checkedTypologies = Array.from(document.querySelectorAll('.filter-checkbox input:checked')).map(c => c.value);
        if (checkedTypologies.length === 0) {
          filteredRecords = [...allRecords];
        } else {
          filteredRecords = allRecords.filter(r => checkedTypologies.includes(r.typology));
        }
        renderRecords();
      });
    });
  }

  // Tab switcher
  window.switchTab = async (tabName) => {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${tabName}`)?.classList.add('active');

    const explorerView = document.getElementById('explorer-view');
    const schemaView = document.getElementById('schema-view');

    if (tabName === 'explorer') {
      explorerView.style.display = 'block';
      schemaView.style.display = 'none';
    } else {
      explorerView.style.display = 'none';
      schemaView.style.display = 'block';

      let fileToFetch = 'okf-explorer.json';
      if (tabName === 'yamlld') fileToFetch = 'okf-bundle.yamlld';
      if (tabName === 'checksums') fileToFetch = 'checksums.json';

      try {
        const resp = await fetch(fileToFetch);
        const data = await resp.text();
        codeViewer.textContent = data;
      } catch (err) {
        codeViewer.textContent = `Error loading file ${fileToFetch}: ${err}`;
      }
    }
  };
});
