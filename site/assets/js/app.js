(() => {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('#main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      nav.classList.toggle('open', !expanded);
    });
  }

  const table = document.querySelector('#archive-table');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const search = document.querySelector('#search');
  const type = document.querySelector('#type-filter');
  const city = document.querySelector('#city-filter');
  const region = document.querySelector('#region-filter');
  const count = document.querySelector('#visible-count');
  const form = document.querySelector('[data-table-filters]');

  const normalize = (value) => (value || '').toLocaleLowerCase('it').trim();
  const filterRows = () => {
    const query = normalize(search.value);
    let visible = 0;
    rows.forEach((row) => {
      const searchable = normalize(`${row.dataset.cig} ${row.dataset.title} ${row.dataset.authority}`);
      const show = (!query || searchable.includes(query)) &&
        (!type.value || row.dataset.type === type.value) &&
        (!city.value || row.dataset.city === city.value) &&
        (!region.value || row.dataset.region === region.value);
      row.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = String(visible);
  };
  [search, type, city, region].forEach((control) => control.addEventListener('input', filterRows));
  form.addEventListener('reset', () => window.setTimeout(filterRows, 0));

  table.querySelectorAll('[data-sort]').forEach((button) => {
    button.addEventListener('click', () => {
      const key = button.dataset.sort;
      const numeric = button.dataset.sortType === 'number';
      const ascending = button.dataset.direction !== 'asc';
      table.querySelectorAll('[data-sort]').forEach((other) => other.removeAttribute('aria-sort'));
      button.dataset.direction = ascending ? 'asc' : 'desc';
      button.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
      rows.sort((a, b) => {
        let left = a.dataset[key] || '';
        let right = b.dataset[key] || '';
        if (numeric) {
          left = Number(left || Number.NEGATIVE_INFINITY);
          right = Number(right || Number.NEGATIVE_INFINITY);
          return ascending ? left - right : right - left;
        }
        return ascending ? left.localeCompare(right, 'it') : right.localeCompare(left, 'it');
      }).forEach((row) => tbody.appendChild(row));
    });
  });
})();
