/**
 * Offline-capable discovery page for the generated OKF Planning bundle.
 *
 * All source-derived strings are assigned through textContent. The page loads
 * every dataset shard declared by the manifest rather than assuming shard 0.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const datasetGrid = document.getElementById('dataset-grid');
  const searchInput = document.getElementById('search-input');
  const recordCount = document.getElementById('record-count');
  const codeViewer = document.getElementById('code-viewer');
  let allRecords = [];

  const element = (name, className, text) => {
    const node = document.createElement(name);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  const applyFilters = () => {
    const term = (searchInput?.value || '').trim().toLocaleLowerCase();
    const selected = new Set(
      Array.from(document.querySelectorAll('.filter-checkbox input:checked'))
        .map((checkbox) => checkbox.value),
    );
    const records = allRecords.filter((record) => {
      const matchesText = !term || [
        record.title,
        record.description,
        record.collection,
        record.publisher_title,
      ].some((value) => String(value || '').toLocaleLowerCase().includes(term));
      const matchesTypology = selected.size === 0 || selected.has(record.typology);
      return matchesText && matchesTypology;
    });
    renderRecords(records);
  };

  const renderRecords = (records) => {
    if (!datasetGrid || !recordCount) return;
    datasetGrid.replaceChildren();
    recordCount.textContent = `${records.length} of ${allRecords.length} records`;

    records.forEach((record) => {
      const card = element('article', 'dataset-card');
      const header = element('div', 'card-header');
      const tags = element('div', 'card-tags');
      tags.append(
        element('span', `tag tag-${record.typology || 'geography'}`, record.typology || 'unspecified'),
        element('span', 'tag tag-phase', record.phase || 'unspecified'),
      );
      header.append(
        tags,
        element('h3', 'card-title', record.title || record.id),
        element('p', 'card-desc', record.description || 'No description provided.'),
      );
      const metadata = element('div', 'card-meta');
      metadata.append(
        element('span', '', `Entities: ${Number(record.entity_count || 0).toLocaleString()}`),
        element('span', '', `Publisher: ${record.publisher_title || record.publisher || 'Not specified'}`),
      );
      card.append(header, metadata);
      datasetGrid.append(card);
    });
  };

  const updateSummary = (manifest) => {
    const values = {
      'stat-records': manifest.counts?.records,
      'stat-entities': manifest.counts?.entities,
      'stat-relationships': manifest.counts?.relationships,
      'stat-publishers': manifest.counts?.publishers,
    };
    Object.entries(values).forEach(([id, value]) => {
      const node = document.getElementById(id);
      if (node && Number.isFinite(value)) node.textContent = Number(value).toLocaleString();
    });

    const typologyCounts = new Map();
    allRecords.forEach((record) => {
      typologyCounts.set(record.typology, (typologyCounts.get(record.typology) || 0) + 1);
    });
    document.querySelectorAll('[data-typology-count]').forEach((node) => {
      const typology = node.dataset.typologyCount;
      node.textContent = String(typologyCounts.get(typology) || 0);
    });
  };

  try {
    const manifestResponse = await fetch('data/manifest.json');
    if (!manifestResponse.ok) throw new Error(`manifest HTTP ${manifestResponse.status}`);
    const manifest = await manifestResponse.json();
    const shards = manifest.chunks?.datasets || [];
    const payloads = await Promise.all(shards.map(async (path) => {
      const response = await fetch(path);
      if (!response.ok) throw new Error(`${path} HTTP ${response.status}`);
      const payload = await response.json();
      if (!Array.isArray(payload)) throw new Error(`${path} is not an array`);
      return payload;
    }));
    allRecords = payloads.flat();
    updateSummary(manifest);
    applyFilters();
  } catch (error) {
    console.error('Failed to load planning metadata records:', error);
    if (recordCount) recordCount.textContent = `Could not load records: ${error.message}`;
  }

  searchInput?.addEventListener('input', applyFilters);
  document.querySelectorAll('.filter-checkbox input').forEach((checkbox) => {
    checkbox.addEventListener('change', applyFilters);
  });

  window.switchTab = async (tabName) => {
    document.querySelectorAll('.tab-btn').forEach((button) => {
      button.classList.toggle('active', button.id === `tab-${tabName}`);
    });
    const explorerView = document.getElementById('explorer-view');
    const schemaView = document.getElementById('schema-view');
    if (tabName === 'explorer') {
      explorerView.style.display = 'block';
      schemaView.style.display = 'none';
      return;
    }

    explorerView.style.display = 'none';
    schemaView.style.display = 'block';
    const files = {
      descriptor: 'okf-explorer.json',
      markdown: 'index.md',
      yamlld: 'okf-bundle.yamlld',
      checksums: 'checksums.json',
    };
    const path = files[tabName] || files.descriptor;
    try {
      const response = await fetch(path);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      codeViewer.textContent = await response.text();
    } catch (error) {
      codeViewer.textContent = `Error loading ${path}: ${error.message}`;
    }
  };
});
