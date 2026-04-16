'use strict';

/**
 * テーブルコンテナの max-height を動的に計算してセットする
 * テーブルコンテナ上端からウィンドウ下端までの高さを基準に、
 * ページネーション等の下部余白分を差し引いた値を適用する
 */
function resizeAlertHistoryTable() {
  var container = document.getElementById('alert-history-table-container');
  if (!container) return;
  var top           = container.getBoundingClientRect().top;
  var bottomPadding = 72; // ページネーション + 下部余白の想定高さ
  var maxHeight     = window.innerHeight - top - bottomPadding;
  container.style.maxHeight = (maxHeight > 100 ? maxHeight : 100) + 'px';
}

/**
 * 検索フォーム 開閉トグル
 */
(function () {
  var toggle = document.getElementById('search-form-toggle');
  var body   = document.getElementById('search-form-body');
  var icon   = document.getElementById('search-toggle-icon');
  if (!toggle || !body || !icon) return;

  toggle.addEventListener('click', function () {
    var isOpen = body.style.display !== 'none';
    body.style.display = isOpen ? 'none' : '';
    icon.textContent   = isOpen ? '▶' : '▼';
    resizeAlertHistoryTable();
  });
})();

// ページロード時・リサイズ時に高さを再計算
window.addEventListener('load',   resizeAlertHistoryTable);
window.addEventListener('resize', resizeAlertHistoryTable);

/**
 * アラート履歴参照モーダル
 *
 * openAlertHistoryModal(uuid) : 参照ボタンクリック時にモーダルを開く
 * closeAlertHistoryModal()    : 閉じるボタン / オーバーレイクリック時に閉じる
 */

function openAlertHistoryModal(uuid) {
  const overlay = document.getElementById('ah-modal-overlay');
  const content = document.getElementById('ah-modal-content');

  content.innerHTML = '<div class="ah-modal-loading">読み込み中...</div>';
  overlay.style.display = 'flex';

  fetch('/alert/alert-history/' + uuid, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
  })
    .then(function (res) {
      if (res.status >= 500) {
        return res.text().then(function (html) {
          document.documentElement.innerHTML = html;
        });
      }
      if (!res.ok) {
        content.innerHTML = '<div class="ah-modal-error">データの取得に失敗しました。</div>';
        return;
      }
      return res.text().then(function (html) {
        content.innerHTML = html;
      });
    })
    .catch(function () {
      content.innerHTML = '<div class="ah-modal-error">データの取得に失敗しました。</div>';
    });
}

function closeAlertHistoryModal() {
  const overlay = document.getElementById('ah-modal-overlay');
  overlay.style.display = 'none';
  document.getElementById('ah-modal-content').innerHTML = '';
}

// テーブルソート初期化
new TableSort(document.getElementById('alert-history-table'));

// flatpickr 初期化（期間・開始）
flatpickr('#start_datetime', {
  locale:        'ja',
  enableTime:    true,
  enableSeconds: false,
  dateFormat:    'Y/m/d H:i',
  allowInput:    false,
});

// flatpickr 初期化（期間・終了）
flatpickr('#end_datetime', {
  locale:        'ja',
  enableTime:    true,
  enableSeconds: false,
  dateFormat:    'Y/m/d H:i',
  allowInput:    false,
});
