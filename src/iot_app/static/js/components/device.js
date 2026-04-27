'use strict';

var DeviceModule = (function () {
  var overlay, content;

  function init() {
    overlay = document.getElementById('dm-modal-overlay');
    content = document.getElementById('dm-modal-content');

    // 検索フォームトグル
    var toggle = document.getElementById('search-form-toggle');
    var body   = document.getElementById('search-form-body');
    var icon   = document.getElementById('search-toggle-icon');
    if (toggle && body && icon) {
      toggle.style.cursor = 'pointer';
      toggle.addEventListener('click', function () {
        var isOpen = body.style.display !== 'none';
        body.style.display = isOpen ? 'none' : '';
        icon.textContent = isOpen ? '▶' : '▼';
        resizeTable();
      });
    }

    // 全選択チェックボックス
    var checkAll  = document.getElementById('check-all');
    var deleteBtn = document.getElementById('delete-btn');

    function updateDeleteBtn() {
      if (!deleteBtn) return;
      deleteBtn.disabled = document.querySelectorAll('.row-check:checked').length === 0;
    }

    if (checkAll) {
      checkAll.addEventListener('change', function () {
        document.querySelectorAll('.row-check').forEach(function (cb) {
          cb.checked = checkAll.checked;
        });
        updateDeleteBtn();
      });
      document.querySelectorAll('.row-check').forEach(function (cb) {
        cb.addEventListener('change', function () {
          var all     = document.querySelectorAll('.row-check');
          var checked = document.querySelectorAll('.row-check:checked');
          checkAll.checked       = all.length === checked.length;
          checkAll.indeterminate = checked.length > 0 && checked.length < all.length;
          updateDeleteBtn();
        });
      });
    }

    // 削除ボタン
    var deleteModal      = document.getElementById('delete-confirm-modal');
    var deleteCancelBtn  = document.getElementById('delete-cancel-btn');
    var deleteConfirmBtn = document.getElementById('delete-confirm-btn');
    var deleteForm       = document.getElementById('delete-form');
    if (deleteBtn && deleteModal) {
      deleteBtn.addEventListener('click', function () {
        deleteModal.classList.add('active');
      });
      deleteCancelBtn.addEventListener('click', function () {
        deleteModal.classList.remove('active');
      });
      deleteConfirmBtn.addEventListener('click', function () {
        deleteModal.classList.remove('active');
        deleteForm.submit();
      });
      deleteModal.addEventListener('click', function (e) {
        if (e.target === deleteModal) deleteModal.classList.remove('active');
      });
    }

    // 検索・ページネーション時にスケルトン表示
    var searchForm = document.getElementById('search-form');
    if (searchForm) {
      searchForm.addEventListener('submit', showTableSkeleton);
    }
    document.querySelectorAll('.pagination__button').forEach(function (a) {
      a.addEventListener('click', showTableSkeleton);
    });

    window.addEventListener('load', resizeTable);
    window.addEventListener('resize', resizeTable);
  }

  function showTableSkeleton() {
    var tbody = document.querySelector('#device-table tbody');
    if (!tbody) return;
    var colCount = document.querySelectorAll('#device-table thead th').length;
    var html = '';
    for (var i = 0; i < 5; i++) {
      html += '<tr>';
      for (var j = 0; j < colCount; j++) {
        html += '<td><div class="dm-skeleton-cell"></div></td>';
      }
      html += '</tr>';
    }
    tbody.innerHTML = html;
  }

  function resizeTable() {
    var container = document.getElementById('device-table-container');
    if (!container) return;
    var top           = container.getBoundingClientRect().top;
    var bottomPadding = 72;
    var maxHeight     = window.innerHeight - top - bottomPadding;
    container.style.maxHeight = (maxHeight > 100 ? maxHeight : 100) + 'px';
  }

  function openModal(url) {
    content.innerHTML = '<div class="dm-modal-loading">読み込み中...</div>';
    overlay.classList.add('active');

    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) {
        if (res.status >= 500) {
          return res.text().then(function (html) {
            document.documentElement.innerHTML = html;
          });
        }
        if (!res.ok) {
          content.innerHTML = '<div class="dm-modal-error">データの取得に失敗しました。</div>';
          return;
        }
        return res.text().then(function (html) {
          content.innerHTML = html;
        });
      })
      .catch(function () {
        content.innerHTML = '<div class="dm-modal-error">データの取得に失敗しました。</div>';
      });
  }

  function closeModal() {
    overlay.classList.remove('active');
    content.innerHTML = '';
  }

  function submitForm(form, successMessage) {
    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function (res) {
        if (res.ok) {
          return res.json().then(function (data) {
            closeModal();
            Toast.show(data.message || successMessage, 'success');
            setTimeout(function () { window.location.reload(); }, 600);
          });
        }
        if (res.status === 400) {
          return res.text().then(function (html) {
            content.innerHTML = html;
          });
        }
        if (res.status === 403) {
          return res.json().then(function (data) {
            closeModal();
            Toast.show(data.error || '操作する権限がありません', 'error');
          });
        }
        if (res.status === 404) {
          return res.json().then(function (data) {
            closeModal();
            Toast.show(data.error || 'データが見つかりません', 'error');
          });
        }
        return res.text().then(function (html) {
          document.documentElement.innerHTML = html;
        });
      })
      .catch(function () {
        Toast.show('エラーが発生しました', 'error');
      });
  }

  document.addEventListener('DOMContentLoaded', init);

  return {
    openDetailModal: function (uuid) { openModal('/admin/devices/' + uuid); },
    openCreateModal: function ()     { openModal('/admin/devices/create'); },
    openEditModal:   function (uuid) { openModal('/admin/devices/' + uuid + '/edit'); },
    closeModal:      closeModal,
    submitForm:      submitForm,
  };
})();
