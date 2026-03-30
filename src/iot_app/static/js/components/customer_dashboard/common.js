/**
 * 顧客作成ダッシュボード クライアントサイドJS
 *
 * CustomerDashboard.init(options) で初期化する。
 * options: { selectedOrganizationId, selectedDeviceId, dashboardUuid }
 */
const CustomerDashboard = (function () {
  'use strict';

  /* ── 状態 ─────────────────────────────────────── */
  let _editMode = false;
  let _autoRefreshEnabled = true;
  let _autoRefreshTimer = null;
  const AUTO_REFRESH_INTERVAL = 60000; // 60秒

  /* ── 初期化 ──────────────────────────────────── */
  function init(options) {
    _setupSettingMenus();
    _setupAjaxModalTriggers();
    _setupDataSourceForm(options);
    _setupEditModeToggle();
    _setupSaveLayoutBtn();
    _setupDatetimeTools();
    // _setupAutoRefresh();  // TODO: ガジェット個別設計（自動更新要否・パラメータ体系）確定後に有効化。UC接続コストリスクのためE2Eテスト前に保留。
    _setupGroupCollapseButtons();
    _updateLastUpdatedTime();
  }

  /* =========================================================
   * モーダル
   * ========================================================= */

  /**
   * URLからモーダルHTMLを取得してオーバーレイに表示する
   */
  async function _loadModal(url) {
    const overlay = document.getElementById('ajax-modal-overlay');
    const content = document.getElementById('ajax-modal-content');

    content.innerHTML = '<div style="padding:24px;text-align:center;">読み込み中...</div>';
    overlay.classList.add('active');

    try {
      const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (res.status >= 500) {
        // 500以上 → 500エラーページを表示
        const html = await res.text();
        document.documentElement.innerHTML = html;
        return;
      }
      if (!res.ok) {
        // 4xx → モーダル内にエラー表示
        content.innerHTML = `<div style="padding:24px;color:red;">エラーが発生しました（${res.status}）</div>`;
        return;
      }
      content.innerHTML = await res.text();
      _bindModalEvents(content);
    } catch (e) {
      // ネットワーク断等の通信エラー → リロード
      window.location.reload();
    }
  }

  /**
   * モーダルを閉じる
   */
  function _closeModal() {
    const overlay = document.getElementById('ajax-modal-overlay');
    overlay.classList.remove('active');
    document.getElementById('ajax-modal-content').innerHTML = '';
  }

  /**
   * モーダル内イベントのバインド（モーダルHTML注入後に呼ぶ）
   */
  function _bindModalEvents(container) {
    // キャンセル・閉じるボタン
    const closeBtn = container.querySelector('#modal-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', _closeModal);
    }

    // data-ajax-submit フォーム
    const form = container.querySelector('form[data-ajax-submit]');
    if (form) {
      form.addEventListener('submit', _handleFormSubmit);
    }

    // ダッシュボード管理モーダル専用
    _bindDashboardManagementEvents(container);

    // ガジェット追加モーダル専用
    _bindGadgetAddEvents(container);

    // 棒グラフ登録モーダル専用
    _bindBarChartRegisterEvents(container);
  }

  /**
   * フォーム AJAX 送信ハンドラ
   * - 成功（リダイレクト後のURL がダッシュボードURL）→ ページリロード
   * - 400 → モーダル内容をエラーレスポンスで更新
   * - 500+ → エラー表示
   */
  async function _handleFormSubmit(e) {
    e.preventDefault();
    const form = e.currentTarget;

    await withSubmitLock(form, async function () {
      const formData = new FormData(form);

      const res = await fetch(form.action, {
        method: 'POST',
        body: formData,
        redirect: 'follow',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });

      if (res.status === 200 && res.redirected) {
        // リダイレクト後に成功 → ページリロード
        window.location.reload();
        return;
      }

      if (res.status === 200) {
        // リダイレクトなし 200 → 成功としてリロード（POST-Redirect-GET の fetch 追従）
        window.location.reload();
        return;
      }

      if (res.status >= 400 && res.status < 500) {
        // 4xx → モーダル内容を更新（400: フォームエラーHTML、403/404/409: エラーフラグメントHTML）
        const html = await res.text();
        const content = document.getElementById('ajax-modal-content');
        content.innerHTML = html;
        _bindModalEvents(content);
        return;
      }

      // 500以上 → 500エラーページを表示（仕様: 500エラーページ表示）
      const html = await res.text();
      document.documentElement.innerHTML = html;
    }).catch(function () {
      // ネットワーク断等の通信エラー → リロード（サーバー復旧で通常ページへ、未復旧でブラウザエラー画面）
      window.location.reload();
    });
  }

  /* =========================================================
   * AJAXモーダルトリガーセットアップ
   * ========================================================= */

  function _setupAjaxModalTriggers() {
    // data-modal-url を持つ要素クリックでモーダルを開く
    document.addEventListener('click', function (e) {
      const trigger = e.target.closest('[data-modal-url]');
      if (!trigger) return;
      e.preventDefault();
      _loadModal(trigger.dataset.modalUrl);
    });
  }

  /* =========================================================
   * ダッシュボード管理モーダル専用イベント
   * ========================================================= */

  function _bindDashboardManagementEvents(container) {
    const deleteBtn = container.querySelector('#mgmt-delete-btn');
    const changeBtn = container.querySelector('#mgmt-change-btn');
    const registerBtn = container.querySelector('#mgmt-register-btn');

    if (registerBtn) {
      registerBtn.addEventListener('click', function () {
        _closeModal();
        _loadModal(registerBtn.dataset.modalUrl);
      });
    }

    if (deleteBtn) {
      deleteBtn.addEventListener('click', function () {
        const selected = container.querySelector('input[name="dashboard_uuid"]:checked');
        if (!selected) {
          alert('削除するダッシュボードを選択してください');
          return;
        }
        const deleteUrl = selected.dataset.deleteUrl;
        _closeModal();
        _loadModal(deleteUrl);
      });
    }

    if (changeBtn) {
      changeBtn.addEventListener('click', async function () {
        const selected = container.querySelector('input[name="dashboard_uuid"]:checked');
        if (!selected) {
          alert('切り替えるダッシュボードを選択してください');
          return;
        }
        const switchUrl = selected.dataset.switchUrl;
        try {
          const formData = new FormData();
          // CSRF トークン取得（ページ内のどこかのフォームから）
          const csrfToken = document.querySelector('input[name="csrf_token"]');
          if (csrfToken) formData.append('csrf_token', csrfToken.value);

          await fetch(switchUrl, { method: 'POST', body: formData, redirect: 'follow' });
          window.location.reload();
        } catch (err) {
          alert('ダッシュボードの切り替えに失敗しました');
        }
      });
    }
  }

  /* =========================================================
   * ガジェット追加モーダル専用イベント
   * ========================================================= */

  function _bindGadgetAddEvents(container) {
    const items = container.querySelectorAll('.gadget-add__item');
    const tabs = container.querySelectorAll('.gadget-add__tab');
    const previewImage = container.querySelector('#gadget-preview-image');
    const previewPlaceholder = container.querySelector('#gadget-preview-placeholder');
    const previewDesc = container.querySelector('#gadget-preview-description');
    const registerBtn = container.querySelector('#gadget-register-screen-btn');

    // タブ切り替え
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('gadget-add__tab--active'); });
        tab.classList.add('gadget-add__tab--active');
        const sourceType = tab.dataset.sourceType;
        items.forEach(function (item) {
          item.style.display = item.dataset.sourceType === sourceType ? '' : 'none';
        });
        const firstVisible = Array.from(items).find(function (item) {
          return item.dataset.sourceType === sourceType;
        });
        if (firstVisible) firstVisible.click();
      });
    });

    // 初期タブ: デバイス(1) ※ data_source_type: 0=組織, 1=デバイス（app-database-specification.md 32番テーブル参照）
    items.forEach(function (item) {
      if (item.dataset.sourceType !== '1') {
        item.style.display = 'none';
      }
    });

    // ガジェット種別選択
    items.forEach(function (item) {
      item.addEventListener('click', function () {
        items.forEach(function (i) { i.classList.remove('gadget-add__item--selected'); });
        item.classList.add('gadget-add__item--selected');

        // プレビュー更新
        if (previewImage && item.dataset.image) {
          previewImage.src = item.dataset.image;
          previewImage.style.display = '';
          if (previewPlaceholder) previewPlaceholder.style.display = 'none';
        }
        if (previewDesc) previewDesc.textContent = item.dataset.description || '';

        // 登録画面ボタン活性化
        if (registerBtn) {
          registerBtn.disabled = false;
          registerBtn.dataset.baseUrl = item.dataset.createUrl;
        }
      });
    });

    // 初期選択: デバイスタブの先頭アイテムを自動選択
    const firstVisible = Array.from(items).find(function (item) {
      return item.dataset.sourceType === '1';
    });
    if (firstVisible) firstVisible.click();

    // 登録画面ボタン
    if (registerBtn) {
      registerBtn.addEventListener('click', function () {
        if (registerBtn.dataset.baseUrl) {
          _closeModal();
          _loadModal(registerBtn.dataset.baseUrl);
        }
      });
    }
  }

  /* =========================================================
   * 棒グラフ登録モーダル専用イベント
   * ========================================================= */

  function _bindBarChartRegisterEvents(container) {
    const modeButtons = container.querySelectorAll('.bar-chart-register__device-mode-btn');
    if (!modeButtons.length) return;

    const deviceModeInput = container.querySelector('#device_mode');
    const deviceFixedArea = container.querySelector('#device-fixed-area');
    const deviceNameArea  = container.querySelector('#device-name-area');
    const orgFilter       = container.querySelector('#organization-filter');
    const deviceSelect    = container.querySelector('#device-select');

    // デバイスモード切替
    modeButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        modeButtons.forEach(function (b) {
          b.classList.remove('bar-chart-register__device-mode-btn--active');
        });
        btn.classList.add('bar-chart-register__device-mode-btn--active');
        const mode = btn.dataset.mode;
        if (deviceModeInput) deviceModeInput.value = mode;
        const isFixed = mode === 'fixed';
        if (deviceFixedArea) deviceFixedArea.style.visibility = isFixed ? '' : 'hidden';
        if (deviceNameArea)  deviceNameArea.style.visibility  = isFixed ? '' : 'hidden';
      });
    });

    if (!orgFilter || !deviceSelect) return;

    // 組織フィルターによるデバイス選択絞り込み
    const allDeviceOptions = Array.from(deviceSelect.querySelectorAll('option[value]'));
    orgFilter.addEventListener('change', function () {
      const orgId = orgFilter.value;
      deviceSelect.innerHTML = '<option value="">選択してください</option>';
      allDeviceOptions.forEach(function (opt) {
        if (!orgId || opt.dataset.org === orgId) {
          deviceSelect.appendChild(opt.cloneNode(true));
        }
      });
      deviceSelect.disabled = !orgId;
      const nameEl = container.querySelector('#selected-device-name');
      if (nameEl) nameEl.textContent = '-';
    });

    // デバイス選択時デバイス名表示
    deviceSelect.addEventListener('change', function () {
      const selected = deviceSelect.options[deviceSelect.selectedIndex];
      const nameEl = container.querySelector('#selected-device-name');
      if (nameEl) nameEl.textContent = selected ? (selected.dataset.name || '-') : '-';
    });
  }

  /* =========================================================
   * 設定メニュー（⚙ ドロップダウン）
   * ========================================================= */

  function _setupSettingMenus() {
    // ⚙ボタンクリックで対応するドロップダウンをトグル
    document.addEventListener('click', function (e) {
      const trigger = e.target.closest('.setting-menu__trigger');
      if (trigger) {
        e.stopPropagation();
        const menu = trigger.closest('.setting-menu');
        const list = menu.querySelector('.setting-menu__list');
        const isHidden = list.hasAttribute('hidden');

        // 他のすべてのメニューを閉じる
        document.querySelectorAll('.setting-menu__list').forEach(function (m) {
          m.setAttribute('hidden', '');
        });

        if (isHidden) {
          list.removeAttribute('hidden');
        }
        return;
      }

      // メニュー外クリックで閉じる
      const inMenu = e.target.closest('.setting-menu');
      if (!inMenu) {
        document.querySelectorAll('.setting-menu__list').forEach(function (m) {
          m.setAttribute('hidden', '');
        });
      }
    });
  }

  /* =========================================================
   * グループ展開・縮小
   * ========================================================= */

  function _setupGroupCollapseButtons() {
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.dashboard-group__collapse-btn');
      if (!btn) return;

      const group = btn.closest('.dashboard-group');
      const contentId = btn.getAttribute('aria-controls');
      const content = document.getElementById(contentId);
      if (!content) return;

      const expanded = btn.getAttribute('aria-expanded') === 'true';
      if (expanded) {
        content.style.display = 'none';
        btn.setAttribute('aria-expanded', 'false');
        btn.textContent = '▶';
      } else {
        content.style.display = '';
        btn.setAttribute('aria-expanded', 'true');
        btn.textContent = '▼';
      }
    });
  }

  /* =========================================================
   * データソース選択フォーム
   * ========================================================= */

  function _setupDataSourceForm(options) {
    const orgSelect = document.getElementById('select-organization');
    const deviceSelect = document.getElementById('select-device');
    if (!orgSelect || !deviceSelect) return;

    // 組織選択変更時: デバイス一覧を取得 + データソース保存
    orgSelect.addEventListener('change', async function () {
      const orgId = orgSelect.value;

      // デバイス選択をリセット
      deviceSelect.innerHTML = '<option value="">-- 選択してください --</option>';
      deviceSelect.disabled = true;

      if (!orgId) {
        _saveDataSource(null, null);
        return;
      }

      // デバイス一覧取得
      try {
        const baseUrl = orgSelect.dataset.devicesUrl;
        const url = baseUrl.replace(/\/devices$/, `/${orgId}/devices`);
        const res = await fetch(url);
        if (!res.ok) throw new Error('fetch failed');
        const data = await res.json();

        data.devices.forEach(function (d) {
          const opt = document.createElement('option');
          opt.value = d.device_id;
          opt.textContent = d.device_name;
          deviceSelect.appendChild(opt);
        });
        deviceSelect.disabled = false;
      } catch (e) {
        console.error('デバイス一覧取得エラー', e);
      }

      _saveDataSource(orgId, null);
    });

    // デバイス選択変更時: データソース保存
    deviceSelect.addEventListener('change', function () {
      const orgId = orgSelect.value || null;
      const deviceId = deviceSelect.value || null;
      _saveDataSource(orgId, deviceId);
      _updateGadgetDatasourceDisplay(orgId, deviceId);
    });

    // 初期表示: user_setting に保存済みのデバイスがあればガジェットのデータソース名を反映
    if (options.selectedDeviceId) {
      _updateGadgetDatasourceDisplay(orgSelect.value || null, deviceSelect.value || null);
    }
  }

  async function _saveDataSource(organizationId, deviceId) {
    const saveUrl = document.getElementById('select-organization')?.dataset.saveUrl;
    if (!saveUrl) return;

    try {
      await fetch(saveUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          organization_id: organizationId ? parseInt(organizationId, 10) : null,
          device_id: deviceId ? parseInt(deviceId, 10) : null,
        }),
      });
    } catch (e) {
      console.error('データソース保存エラー', e);
    }
  }

  function _updateGadgetDatasourceDisplay(organizationId, deviceId) {
    const deviceSelect = document.getElementById('select-device');
    const deviceName = deviceId
      ? (deviceSelect.options[deviceSelect.selectedIndex]?.textContent || '--')
      : '--';

    document.querySelectorAll('.gadget__datasource-name').forEach(function (el) {
      el.textContent = deviceName;
    });
  }

  /* =========================================================
   * 編集モード切替
   * ========================================================= */

  function _setupEditModeToggle() {
    const toggle = document.getElementById('edit-mode-toggle');
    const savBtn = document.getElementById('save-layout-btn');
    const banner = document.getElementById('edit-mode-banner');
    const dashboard = document.querySelector('.customer-dashboard');
    if (!toggle) return;

    toggle.addEventListener('change', function () {
      _editMode = toggle.checked;
      if (dashboard) {
        dashboard.classList.toggle('customer-dashboard--edit-mode', _editMode);
      }
      if (savBtn) savBtn.disabled = !_editMode;
      if (banner) banner.hidden = !_editMode;

      if (_editMode) {
        _enableDragAndDrop();
      } else {
        _disableDragAndDrop();
      }
    });
  }

  /* =========================================================
   * レイアウト保存
   * ========================================================= */

  function _setupSaveLayoutBtn() {
    const btn = document.getElementById('save-layout-btn');
    if (!btn) return;

    btn.addEventListener('click', async function () {
      const saveUrl = btn.dataset.url;
      if (!saveUrl) return;

      const gadgets = _collectLayoutData();
      try {
        const res = await fetch(saveUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ gadgets }),
        });
        const data = await res.json();
        if (res.ok) {
          alert(data.message || 'レイアウトを保存しました');
        } else {
          alert(data.error || 'レイアウトの保存に失敗しました');
        }
      } catch (e) {
        alert('通信エラーが発生しました');
      }
    });
  }

  /**
   * 現在のガジェット配置からレイアウトデータを収集する
   */
  function _collectLayoutData() {
    const gadgets = [];
    document.querySelectorAll('.gadget').forEach(function (el, idx) {
      gadgets.push({
        gadget_uuid: el.dataset.gadgetUuid,
        position_x: parseInt(el.dataset.positionX, 10) || 0,
        position_y: parseInt(el.dataset.positionY, 10) || 0,
        display_order: idx,
      });
    });
    return gadgets;
  }

  /* =========================================================
   * ドラッグ＆ドロップ（HTML5 DnD API）
   * ========================================================= */

  let _dragSrcEl = null;

  function _enableDragAndDrop() {
    document.querySelectorAll('.gadget').forEach(function (gadget) {
      gadget.setAttribute('draggable', 'true');
      gadget.addEventListener('dragstart', _onDragStart);
      gadget.addEventListener('dragover', _onDragOver);
      gadget.addEventListener('dragleave', _onDragLeave);
      gadget.addEventListener('drop', _onDrop);
      gadget.addEventListener('dragend', _onDragEnd);
    });
  }

  function _disableDragAndDrop() {
    document.querySelectorAll('.gadget').forEach(function (gadget) {
      gadget.removeAttribute('draggable');
      gadget.removeEventListener('dragstart', _onDragStart);
      gadget.removeEventListener('dragover', _onDragOver);
      gadget.removeEventListener('dragleave', _onDragLeave);
      gadget.removeEventListener('drop', _onDrop);
      gadget.removeEventListener('dragend', _onDragEnd);
      gadget.classList.remove('gadget--dragging');
    });
    document.querySelectorAll('.dashboard-content').forEach(function (area) {
      area.classList.remove('gadget--drag-over');
    });
  }

  function _onDragStart(e) {
    _dragSrcEl = this;
    this.classList.add('gadget--dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.gadgetUuid);
  }

  function _onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (this !== _dragSrcEl) {
      this.closest('.dashboard-content')?.classList.add('gadget--drag-over');
    }
    return false;
  }

  function _onDragLeave() {
    this.closest('.dashboard-content')?.classList.remove('gadget--drag-over');
  }

  function _onDrop(e) {
    e.stopPropagation();
    const content = this.closest('.dashboard-content');
    if (content) content.classList.remove('gadget--drag-over');

    if (_dragSrcEl && _dragSrcEl !== this) {
      // DOM上でドラッグ元とドロップ先を入れ替える
      const parent = this.parentNode;
      const srcNext = _dragSrcEl.nextSibling;
      const targetNext = this.nextSibling;

      if (srcNext === this) {
        parent.insertBefore(_dragSrcEl, targetNext);
      } else {
        parent.insertBefore(this, _dragSrcEl);
        if (srcNext) {
          parent.insertBefore(_dragSrcEl, srcNext);
        } else {
          parent.appendChild(_dragSrcEl);
        }
      }
    }
    return false;
  }

  function _onDragEnd() {
    this.classList.remove('gadget--dragging');
    document.querySelectorAll('.dashboard-content').forEach(function (area) {
      area.classList.remove('gadget--drag-over');
    });
  }

  /* =========================================================
   * 日時設定ツール
   * ========================================================= */

  function _setupDatetimeTools() {
    // 日時設定ボタン（今日/昨日/今週/今月/今年）
    document.querySelectorAll('.datetime-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const range = btn.dataset.range;
        _fetchAllGadgetsData({ range });
      });
    });

    // カスタムボタン
    const customBtn = document.getElementById('custom-datetime-btn');
    const customDropdown = document.getElementById('custom-datetime-dropdown');
    if (customBtn && customDropdown) {
      customBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        customDropdown.hidden = !customDropdown.hidden;
      });

      const applyBtn = document.getElementById('custom-apply-btn');
      const cancelBtn = document.getElementById('custom-cancel-btn');

      if (applyBtn) {
        applyBtn.addEventListener('click', function () {
          const start = document.getElementById('custom-start').value;
          const end = document.getElementById('custom-end').value;
          if (!start) { alert('開始日時を入力してください'); return; }
          if (!end) { alert('終了日時を入力してください'); return; }
          if (new Date(start) >= new Date(end)) {
            alert('開始日時は終了日時より前に設定してください');
            return;
          }
          customDropdown.hidden = true;
          _fetchAllGadgetsData({ start, end, range: 'custom' });
        });
      }

      if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
          customDropdown.hidden = true;
        });
      }
    }

    // 日時初期化ボタン
    const resetBtn = document.getElementById('datetime-reset-btn');
    const resetModal = document.getElementById('datetime-reset-modal');
    if (resetBtn && resetModal) {
      resetBtn.addEventListener('click', function () {
        resetModal.classList.add('active');
      });

      const confirmBtn = document.getElementById('datetime-reset-confirm-btn');
      const cancelBtn2 = document.getElementById('datetime-reset-cancel-btn');

      if (confirmBtn) {
        confirmBtn.addEventListener('click', function () {
          resetModal.classList.remove('active');
          _fetchAllGadgetsData({ range: 'today' });
        });
      }
      if (cancelBtn2) {
        cancelBtn2.addEventListener('click', function () {
          resetModal.classList.remove('active');
        });
      }
    }
  }

  /* =========================================================
   * ガジェットデータ取得（AJAX）
   * ========================================================= */

  /**
   * 全ガジェットのデータを取得する
   */
  function _fetchAllGadgetsData(params) {
    const gadgets = document.querySelectorAll('.gadget[data-data-url]');
    const deviceId = document.getElementById('select-device')?.value || null;
    const orgId = document.getElementById('select-organization')?.value || null;

    gadgets.forEach(function (gadget) {
      _fetchGadgetData(gadget, params, orgId, deviceId);
    });
    _updateLastUpdatedTime();
  }

  /**
   * 単一ガジェットのデータを取得してグラフを更新する
   */
  function _fetchGadgetData(gadgetEl, params, orgId, deviceId) {
    // データ取得・描画はガジェット種別ごとの JS に委譲する
    // CustomEvent で日時範囲を通知し、各ガジェット JS が自身のエンドポイントを呼ぶ
    gadgetEl.dispatchEvent(new CustomEvent('gadget:daterange-changed', {
      bubbles: false,
      detail: {
        ...params,
        organization_id: orgId ? parseInt(orgId, 10) : null,
        device_id: deviceId ? parseInt(deviceId, 10) : null,
      },
    }));
  }

  /* =========================================================
   * 自動更新
   * ========================================================= */

  function _setupAutoRefresh() {
    const toggle = document.getElementById('auto-refresh-toggle');
    if (!toggle) return;

    // 初期状態: ON
    if (toggle.checked) {
      _startAutoRefresh();
    }

    toggle.addEventListener('change', function () {
      _autoRefreshEnabled = toggle.checked;
      if (_autoRefreshEnabled) {
        _startAutoRefresh();
      } else {
        _stopAutoRefresh();
      }
    });
  }

  function _startAutoRefresh() {
    _stopAutoRefresh();
    _autoRefreshTimer = setInterval(function () {
      if (!_autoRefreshEnabled) {
        _stopAutoRefresh();
        return;
      }
      _fetchAllGadgetsData({ range: 'today' });
    }, AUTO_REFRESH_INTERVAL);
  }

  function _stopAutoRefresh() {
    if (_autoRefreshTimer !== null) {
      clearInterval(_autoRefreshTimer);
      _autoRefreshTimer = null;
    }
  }

  /* =========================================================
   * 最終更新時刻表示
   * ========================================================= */

  function _updateLastUpdatedTime() {
    const el = document.getElementById('last-updated-time');
    if (!el) return;
    const now = new Date();
    const pad = function (n) { return String(n).padStart(2, '0'); };
    el.textContent = [
      now.getFullYear(),
      '/',
      pad(now.getMonth() + 1),
      '/',
      pad(now.getDate()),
      ' ',
      pad(now.getHours()),
      ':',
      pad(now.getMinutes()),
      ':',
      pad(now.getSeconds()),
    ].join('');
  }

  /* =========================================================
   * 公開API
   * ========================================================= */
  return { init };

}());
