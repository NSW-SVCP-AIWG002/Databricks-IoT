/* ===== サイドバー：サブメニュークリック開閉（アコーディオン） ===== */
document.querySelectorAll('.nav__item--parent > .nav__link').forEach(function(link) {
  link.addEventListener('click', function() {
    var parent = this.closest('.nav__item--parent');
    var isOpen = parent.classList.contains('is-open');

    // 他の開いているサブメニューを閉じる（アコーディオン）
    document.querySelectorAll('.nav__item--parent.is-open').forEach(function(el) {
      el.classList.remove('is-open');
    });

    // クリックした項目をトグル
    if (!isOpen) {
      parent.classList.add('is-open');
    }
  });
});

/* ===== CSVインポートモーダル ===== */
function openImportModal() {
  var modal = document.getElementById('csv-import-modal');
  if (modal) {
    modal.classList.add('active');
  }
}

function closeImportModal() {
  var modal = document.getElementById('csv-import-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}
