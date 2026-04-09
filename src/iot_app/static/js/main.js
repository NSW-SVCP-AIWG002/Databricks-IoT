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
  var params = new URLSearchParams(window.location.search);
  var error = params.get('error');
  if (!error) return;

  Toast.show(error);

  params.delete('error');
  var newSearch = params.toString();
  var newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash;
  history.replaceState(null, '', newUrl);
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
