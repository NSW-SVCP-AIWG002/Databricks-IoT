class TableSort {
  constructor(table) {
    this.table = table;
    this.tbody = table.querySelector('tbody');
    if (!this.tbody) return;
    this._originalRows = Array.from(this.tbody.querySelectorAll('tr'));
    this._state = { colIndex: -1, dir: 0 }; // dir: 0=none, 1=asc, -1=desc
    this._init();
  }

  _init() {
    var self = this;
    Array.from(this.table.querySelectorAll('th')).forEach(function(th, i) {
      if (!th.querySelector('.sort-indicator')) return;
      th.style.cursor = 'pointer';
      th.addEventListener('click', function() { self._sort(i); });
    });
  }

  _sort(colIndex) {
    if (this._state.colIndex === colIndex) {
      if (this._state.dir === 0) this._state.dir = 1;
      else if (this._state.dir === 1) this._state.dir = -1;
      else this._state.dir = 0;
    } else {
      this._state.colIndex = colIndex;
      this._state.dir = 1;
    }

    // Reset all indicators
    Array.from(this.table.querySelectorAll('.sort-indicator')).forEach(function(ind) {
      ind.textContent = '\u2195';
    });

    if (this._state.dir === 0) {
      var self = this;
      this._originalRows.forEach(function(row) { self.tbody.appendChild(row); });
      return;
    }

    // Update active indicator
    var ths = Array.from(this.table.querySelectorAll('th'));
    if (ths[colIndex]) {
      var ind = ths[colIndex].querySelector('.sort-indicator');
      if (ind) ind.textContent = this._state.dir === 1 ? '\u2191' : '\u2193';
    }

    var self = this;
    var dir = this._state.dir;
    var rows = Array.from(this._originalRows);
    rows.sort(function(a, b) {
      var aVal = self._getCellValue(a, colIndex);
      var bVal = self._getCellValue(b, colIndex);
      return self._compare(aVal, bVal) * dir;
    });
    rows.forEach(function(row) { self.tbody.appendChild(row); });
  }

  _getCellValue(row, colIndex) {
    var cell = row.cells[colIndex];
    return cell ? cell.innerText.trim() : '';
  }

  _compare(a, b) {
    // Date: YYYY/MM/DD HH:mm:ss format
    if (/^\d{4}\/\d{2}\/\d{2}/.test(a) && /^\d{4}\/\d{2}\/\d{2}/.test(b)) {
      return a < b ? -1 : a > b ? 1 : 0;
    }
    // Number
    var aNum = parseFloat(a);
    var bNum = parseFloat(b);
    if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
    // String (Japanese)
    return a.localeCompare(b, 'ja');
  }
}

// Auto-initialize for all tables containing sort-indicator
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('table').forEach(function(table) {
    if (table.querySelector('.sort-indicator')) {
      new TableSort(table);
    }
  });
});
