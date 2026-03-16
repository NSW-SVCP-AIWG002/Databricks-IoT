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

/* ===== 通常フォーム 二重送信防止 =====
 * data-ajax-submit 属性を持たない通常フォーム（ページ遷移あり）の送信ボタンを
 * submit イベント時に disabled にする。
 * ページ遷移によって自動リセットされるため、再活性化処理は不要。
 */
document.addEventListener('submit', function (e) {
  var form = e.target;
  if (form.hasAttribute('data-ajax-submit')) return; // AJAXフォームは対象外
  var submitBtn = form.querySelector('[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;
});

/* ===== withSubmitLock: AJAXフォーム 二重送信防止 =====
 *
 * 用途:
 *   AJAXで送信するフォーム（ページ遷移なし）の二重送信を防ぐ共通ユーティリティ。
 *   非同期処理の開始時にボタンを非活性化し、完了（成功・失敗問わず）後に再活性化する。
 *
 * 引数:
 *   form    {HTMLFormElement} - 対象フォーム要素。[type="submit"] ボタンが制御対象。
 *   asyncFn {Function}        - 送信処理を行う非同期関数（Promise を返すこと）。
 *
 * 使い方:
 *   async function _handleFormSubmit(e) {
 *     e.preventDefault();
 *     await withSubmitLock(e.currentTarget, async function () {
 *       const res = await fetch(form.action, { method: 'POST', ... });
 *       // レスポンス処理...
 *     });
 *   }
 *
 * 注意:
 *   - asyncFn 内でページリロード（window.location.reload()）が発生する場合、
 *     finally の再活性化は実行されるが画面が切り替わるため実質無害。
 *   - 400 等でモーダル内容が差し替えられた場合、元のボタン要素はDOMから除去済みの
 *     ため再活性化は no-op になる（問題なし）。
 */
function withSubmitLock(form, asyncFn) {
  var btn = form.querySelector('[type="submit"]');
  if (btn) btn.disabled = true;
  return asyncFn().finally(function () {
    if (btn) btn.disabled = false;
  });
}

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
