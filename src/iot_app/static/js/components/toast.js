/* ===== トースト通知 =====
 *
 * 【即時表示】Toast.show(message, type)
 *   ページ遷移・リロードを伴わない通知に使用する。
 *   例: Toast.show('保存に失敗しました', 'error');
 *       Toast.show('処理が完了しました', 'success');
 *
 * 【リロード後表示】Toast.showAfterReload(message, type)
 *   window.location.reload() を伴う操作の直前に呼ぶ。
 *   sessionStorage にメッセージを保存し、リロード後の DOMContentLoaded で表示される。
 *   例: Toast.showAfterReload('登録しました', 'success');
 *       window.location.reload();
 *
 * 【バックエンド起点のリダイレクト後】
 *   Flask が ?error= / ?success= を URL に付与してリダイレクトした場合は
 *   main.js の DOMContentLoaded が自動で Toast.show を呼ぶ。
 *   JS 側での追加実装は不要。
 *
 * 表示条件:
 *   base.html に <div id="toast-container"></div> が必要。
 */
var Toast = (function () {
  'use strict';

  var DURATION = 4000;    // 表示時間（ms）
  var TRANSITION = 250;   // フェードアウト時間（ms、toast.cssと合わせる）

  /**
   * トーストを即時表示する
   * ページ遷移・リロードを伴わない通知に使用する
   * @param {string} message - 表示メッセージ
   * @param {string} type    - 'error'（赤）または 'success'（緑）
   */
  function show(message, type) {
    var container = document.getElementById('toast-container');
    if (!container) return;

    var el = document.createElement('div');
    el.className = 'toast toast--' + type;
    el.textContent = message;
    container.appendChild(el);

    // 2フレーム待ってからクラス付与（CSS transitionを確実に発火させるため）
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        el.classList.add('toast--visible');
      });
    });

    setTimeout(function () {
      el.classList.remove('toast--visible');
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, TRANSITION);
    }, DURATION);
  }

  /**
   * リロード後にトーストを表示する
   * window.location.reload() を伴う操作の直前に呼ぶこと。
   * sessionStorage にメッセージを保存し、リロード後の DOMContentLoaded（main.js）で表示される。
   * @param {string} message - 表示メッセージ
   * @param {string} type    - 'error'（赤）または 'success'（緑）
   */
  function showAfterReload(message, type) {
    sessionStorage.setItem('_pending_toast', JSON.stringify({ message: message, type: type }));
  }

  return { show: show, showAfterReload: showAfterReload };
}());
