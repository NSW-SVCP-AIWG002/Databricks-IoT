/* ===== トースト通知 =====
 *
 * 使い方:
 *   Toast.show('メッセージ');
 *
 * 表示条件:
 *   base.html に <div id="toast-container"></div> が必要。
 */
var Toast = (function () {
  'use strict';

  var DURATION = 4000;    // 表示時間（ms）
  var TRANSITION = 250;   // フェードアウト時間（ms、toast.cssと合わせる）

  function show(message) {
    var container = document.getElementById('toast-container');
    if (!container) return;

    var el = document.createElement('div');
    el.className = 'toast';
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

  return { show: show };
}());
