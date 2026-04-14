/* ===== グローバル fetch インターセプター =====
 * JWTトークン期限切れ（401 token_expired）を全AJAXで一括ハンドリングする。
 * サーバーが {"error": "token_expired"} + 401 を返した場合、
 * ページリロードすることで通常ページ遷移として token_refresh.html フローに乗せる。
 */
(function () {
  var _originalFetch = window.fetch;
  window.fetch = function () {
    return _originalFetch.apply(this, arguments).then(function (response) {
      if (response.status === 401) {
        return response.clone().json().then(function (data) {
          if (data && data.error === 'token_expired') {
            window.location.reload();
            // reload後のレスポンスを止めるため pending の Promise を返す
            return new Promise(function () {});
          }
          return response;
        }).catch(function () {
          return response;
        });
      }
      return response;
    });
  };
}());

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
 * 送信ボタンを submit イベント時に disabled にする。
 * ページ遷移によって自動リセットされるため、再活性化処理は不要。
 */
document.addEventListener('submit', function (e) {
  var form = e.target;
  var submitBtn = form.querySelector('[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;
});

/* ===== エラートースト表示（?error= パラメータ） =====
 * サーバーが referrer へリダイレクトする際に付与した ?error= を読み取り、
 * トーストで表示したうえで URL からパラメータを消去する。
 */
document.addEventListener('DOMContentLoaded', function () {
  /* ── URL パラメータ経由トースト（バックエンド起点のリダイレクト後） ──
   * Flask が ?error= / ?success= を付与してリダイレクトした場合に表示する。
   * JS 起点のトーストは Toast.show() / Toast.showAfterReload() を使うこと。
   */
  var params  = new URLSearchParams(window.location.search);
  var error   = params.get('error');
  var success = params.get('success');

  if (error)   Toast.show(error,   'error');
  if (success) Toast.show(success, 'success');

  if (error || success) {
    params.delete('error');
    params.delete('success');
    var newSearch = params.toString();
    var newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash;
    history.replaceState(null, '', newUrl);
  }

  /* ── sessionStorage 経由トースト（JS 起点のリロード後） ──
   * Toast.showAfterReload() で保存されたメッセージをリロード後に表示する。
   */
  var pending = sessionStorage.getItem('_pending_toast');
  if (pending) {
    sessionStorage.removeItem('_pending_toast');
    try {
      var t = JSON.parse(pending);
      Toast.show(t.message, t.type);
    } catch (e) {}
  }
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
