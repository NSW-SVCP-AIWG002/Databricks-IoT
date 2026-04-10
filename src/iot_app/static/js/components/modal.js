'use strict';

/**
 * モーダルフォーム共通処理
 *
 * modal-form クラスを持つフォームの AJAX 送信を共通化する。
 * CustomerDashboard など各モジュールから利用する。
 *
 * ## 使い方
 *
 *   // 1. HTML側: フォームに class="modal-form" を付与する
 *   // <form method="POST" action="..." class="modal-form" novalidate>
 *
 *   // 2. JS側: モーダルのイベントバインド時に呼び出す
 *   Modal.bindForm(container, {
 *     onClose:  _closeModal,       // モーダルを閉じる関数
 *     onRebind: _bindModalEvents,  // 再描画後にイベントを再バインドする関数
 *   });
 *
 * ## レスポンス別の挙動
 *
 *   500以上  : サーバーエラー。レスポンスのHTMLをページ全体に差し替え（500エラーページ表示）
 *   400      : バリデーションエラー。レスポンスのHTML（エラー付きフォーム）をモーダル内に再描画
 *   その他4xx: 権限エラー等。JSONの error フィールドをトースト表示してモーダルを閉じる
 *   200      : 成功。JSONの message をリロード後トーストで表示してページをリロード
 */
const Modal = (function () {

  /**
   * modal-form の AJAX 送信をコンテナにバインドする
   *
   * @param {Element}  container          - モーダルコンテナ要素（form.modal-form を含む）
   * @param {Object}   options
   * @param {Function} options.onClose    - モーダルを閉じる関数
   * @param {Function} options.onRebind   - 再描画後にイベントを再バインドする関数
   * @param {string}  [options.contentId] - 再描画対象要素のID（デフォルト: 'ajax-modal-content'）
   */
  function bindForm(container, options) {
    const onClose   = options.onClose;
    const onRebind  = options.onRebind;
    const contentId = options.contentId || 'ajax-modal-content';

    // modal-form クラスを持つフォームを探す。なければ何もしない
    const modalForm = container.querySelector('form.modal-form');
    if (!modalForm) return;

    // 通常のページ遷移を止め、AJAX送信に差し替える
    modalForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      // フォームの全フィールド（CSRFトークン含む）を取得して送信
      const formData = new FormData(modalForm);
      try {
        const res = await fetch(modalForm.action, {
          method:  'POST',
          body:    formData,
          // X-Requested-With を付与することでサーバー側がAJAXリクエストと判定できる
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });

        // ── 500以上: サーバーエラー ──────────────────────────────
        // レスポンスのHTMLをページ全体に差し替えて500エラーページを表示する
        if (res.status >= 500) {
          const html = await res.text();
          document.documentElement.innerHTML = html;
          return;
        }

        // ── 400: バリデーションエラー ────────────────────────────
        // サーバーがエラー付きのフォームHTMLを返すので、モーダル内を再描画する。
        // 再描画後はHTMLが丸ごと置き換わりイベントが失われるため onRebind で再バインドする
        if (res.status === 400) {
          const html    = await res.text();
          const content = document.getElementById(contentId);
          content.innerHTML = html;
          if (onRebind) onRebind(content);
          return;
        }

        // ── その他4xx: 権限エラー等 ──────────────────────────────
        // JSONの error フィールドをトーストで表示してモーダルを閉じる
        if (!res.ok) {
          const data = await res.json();
          if (onClose) onClose();
          Toast.show(data.error || 'エラーが発生しました', 'error');
          return;
        }

        // ── 200: 成功 ────────────────────────────────────────────
        // 登録・更新後は画面全体を再描画するためリロードする。
        // トーストはリロード後も表示できるよう showAfterReload で SessionStorage に一時保存し、
        // リロード後の DOMContentLoaded（main.js）で表示する
        const data = await res.json();
        if (onClose) onClose();
        Toast.showAfterReload(data.message || '完了しました', 'success');
        window.location.reload();

      } catch (err) {
        // ネットワーク断等の通信エラー → リロードして状態をリセット
        window.location.reload();
      }
    });
  }

  return { bindForm: bindForm };

})();
