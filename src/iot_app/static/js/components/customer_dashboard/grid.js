'use strict';

/**
 * 表ガジェット管理
 * テーブル描画・AJAX・ページネーション・日時ピッカーを担当する
 */
(function () {

  // ============================================================
  // 定数
  // ============================================================
  const DATA_ENDPOINT = '/analysis/customer-dashboard/gadgets/{uuid}/data';
  const CSV_ENDPOINT  = '/analysis/customer-dashboard/gadgets/{uuid}';
  const COOKIE_KEY    = 'grid_gadget_search_params_{uuid}';
  const COOKIE_MAX_AGE = 86400; // 24時間

  // ============================================================
  // ガジェット初期化
  // ============================================================

  function initAllGadgets() {
    document.querySelectorAll('.grid-gadget[data-gadget-uuid]').forEach(function (el) {
      initGadget(el);
    });
    initRegisterModal();
  }

  function initGadget(el) {
    const uuid = el.dataset.gadgetUuid;

    const state = {
      uuid:          uuid,
      startDatetime: null,
      endDatetime:   null,
      page:          1,
      fpStart:       null,
      fpEnd:         null,
    };

    // Cookie から検索条件を復元
    restoreFromCookie(state);

    // 初期日時が未設定の場合はデフォルト設定
    if (!state.startDatetime) {
      const now = new Date();
      now.setHours(now.getHours() - 1);
      state.startDatetime = formatDatetime(now);
    }
    if (!state.endDatetime) {
      state.endDatetime = formatDatetime(new Date());
    }

    bindControls(el, state);
    bindCsvButton(el, state);
    fetchAndRender(state);
  }

  // ============================================================
  // UI バインド
  // ============================================================

  function bindControls(el, state) {
    const uuid = state.uuid;

    // flatpickr 開始日時
    const startInput = document.getElementById('start-datetime-' + uuid);
    if (startInput) {
      startInput.value = state.startDatetime || '';
      state.fpStart = flatpickr(startInput, {
        enableTime: true,
        enableSeconds: true,
        dateFormat: 'Y/m/d H:i:S',
        time_24hr: true,
        defaultDate: state.startDatetime || null,
        onChange: function (selectedDates, dateStr) {
          state.startDatetime = dateStr;
          state.page = 1;
          fetchAndRender(state);
        },
      });
    }

    // flatpickr 終了日時
    const endInput = document.getElementById('end-datetime-' + uuid);
    if (endInput) {
      endInput.value = state.endDatetime || '';
      state.fpEnd = flatpickr(endInput, {
        enableTime: true,
        enableSeconds: true,
        dateFormat: 'Y/m/d H:i:S',
        time_24hr: true,
        defaultDate: state.endDatetime || null,
        onChange: function (selectedDates, dateStr) {
          state.endDatetime = dateStr;
          state.page = 1;
          fetchAndRender(state);
        },
      });
    }

    // 開始日時リフレッシュボタン
    const startRefreshBtn = document.getElementById('start-refresh-' + uuid);
    if (startRefreshBtn) {
      startRefreshBtn.addEventListener('click', function () {
        const d = new Date();
        d.setHours(d.getHours() - 1);
        state.startDatetime = formatDatetime(d);
        if (state.fpStart) state.fpStart.setDate(state.startDatetime, true);
        state.page = 1;
        fetchAndRender(state);
      });
    }

    // 終了日時リフレッシュボタン
    const endRefreshBtn = document.getElementById('end-refresh-' + uuid);
    if (endRefreshBtn) {
      endRefreshBtn.addEventListener('click', function () {
        state.endDatetime = formatDatetime(new Date());
        if (state.fpEnd) state.fpEnd.setDate(state.endDatetime, true);
        state.page = 1;
        fetchAndRender(state);
      });
    }
  }

  function bindCsvButton(el, state) {
    const gadgetEl = el.closest('.gadget');
    if (!gadgetEl) return;
    const csvBtn = gadgetEl.querySelector('.gadget__csv-btn');
    if (!csvBtn) return;
    csvBtn.addEventListener('click', function (e) {
      e.preventDefault();
      exportCsv(state);
    });
  }

  // ============================================================
  // CSV エクスポート
  // ============================================================

  function exportCsv(state) {
    const params = new URLSearchParams({
      export:         'csv',
      start_datetime: state.startDatetime,
      end_datetime:   state.endDatetime,
    });
    const url = CSV_ENDPOINT.replace('{uuid}', state.uuid) + '?' + params.toString();
    window.location.href = url;
  }

  // ============================================================
  // データ取得・描画
  // ============================================================

  function fetchAndRender(state) {
    if (!state.startDatetime || !state.endDatetime) return;

    const url = DATA_ENDPOINT.replace('{uuid}', state.uuid);
    saveToCookie(state);

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({
        start_datetime: state.startDatetime,
        end_datetime:   state.endDatetime,
        page:           state.page,
      }),
    })
      .then(function (res) {
        if (res.status === 400) {
          showDatetimeError(state.uuid);
          return null;
        }
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        if (data === null) return;
        clearError(state.uuid);
        console.log('[grid] fetchAndRender data:', data);
        renderTable(state, data);
        renderPagination(state, data);
      })
      .catch(function (err) {
        console.error('表ガジェットデータ取得エラー:', err);
        showError(state.uuid);
      });
  }

  function renderTable(state, data) {
    const uuid   = state.uuid;
    const thead  = document.getElementById('thead-' + uuid);
    const tbody  = document.getElementById('tbody-' + uuid);
    if (!thead || !tbody) return;

    // ヘッダー描画
    const tr = document.createElement('tr');

    // 固定列
    ['受信日時', 'デバイス名称'].forEach(function (label) {
      const th = document.createElement('th');
      th.textContent = label;
      tr.appendChild(th);
    });

    // 動的列
    (data.columns || []).forEach(function (col) {
      const th = document.createElement('th');
      th.textContent = col.display_name;
      tr.appendChild(th);
    });

    thead.innerHTML = '';
    thead.appendChild(tr);

    // ボディ描画
    tbody.innerHTML = '';
    (data.grid_data || []).forEach(function (row) {
      const tr = document.createElement('tr');

      const tdTs = document.createElement('td');
      tdTs.textContent = row.event_timestamp || '';
      tr.appendChild(tdTs);

      const tdDev = document.createElement('td');
      tdDev.textContent = row.device_name || '';
      tdDev.title = row.device_name || '';
      tr.appendChild(tdDev);

      (data.columns || []).forEach(function (col) {
        const td = document.createElement('td');
        const val = row[col.column_name];
        td.textContent = (val !== null && val !== undefined) ? val : '';
        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });
  }

  function renderPagination(state, data) {
    const container = document.getElementById('pagination-' + state.uuid);
    if (!container) return;

    const totalCount = data.total_count || 0;
    const perPage    = data.per_page || 25;
    const page       = data.page || 1;
    const totalPages = Math.ceil(totalCount / perPage) || 1;

    container.innerHTML = '';
    if (totalPages <= 1) return;

    const nav = document.createElement('nav');
    nav.className = 'pagination';

    // 前へ
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination__button';
    prevBtn.textContent = '«';
    prevBtn.disabled = (page <= 1);
    prevBtn.addEventListener('click', function () {
      if (state.page > 1) {
        state.page--;
        fetchAndRender(state);
      }
    });
    nav.appendChild(prevBtn);

    // ページ番号
    for (let i = 1; i <= totalPages; i++) {
      const btn = document.createElement('button');
      btn.className = 'pagination__button' + (i === page ? ' pagination__button--active' : '');
      btn.textContent = i;
      btn.dataset.page = i;
      btn.addEventListener('click', function () {
        state.page = parseInt(this.dataset.page, 10);
        fetchAndRender(state);
      });
      nav.appendChild(btn);
    }

    // 次へ
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination__button';
    nextBtn.textContent = '»';
    nextBtn.disabled = (page >= totalPages);
    nextBtn.addEventListener('click', function () {
      if (state.page < totalPages) {
        state.page++;
        fetchAndRender(state);
      }
    });
    nav.appendChild(nextBtn);

    container.appendChild(nav);
  }

  const DATETIME_ERROR_MSG = '日時の指定が不正です（取得期間は24時間以内、終了は開始より後に設定してください）';

  function showDatetimeError(uuid) {
    const errEl = document.getElementById('error-msg-' + uuid);
    if (errEl) errEl.innerHTML = '<span class="form__error">' + DATETIME_ERROR_MSG + '</span>';
    const thead = document.getElementById('thead-' + uuid);
    if (thead) thead.innerHTML = '<tr></tr>';
    const tbody = document.getElementById('tbody-' + uuid);
    if (tbody) tbody.innerHTML = '';
    const pagination = document.getElementById('pagination-' + uuid);
    if (pagination) pagination.innerHTML = '';
  }

  function clearError(uuid) {
    const errEl = document.getElementById('error-msg-' + uuid);
    if (errEl) errEl.innerHTML = '';
  }

  function showError(uuid) {
    const tbody = document.getElementById('tbody-' + uuid);
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="99" style="text-align:center">データの取得に失敗しました</td></tr>';
    }
  }

  // ============================================================
  // 登録モーダル プレビュー
  // ============================================================

  function initRegisterModal() {
    const startInput = document.getElementById('preview-start-datetime');
    const endInput   = document.getElementById('preview-end-datetime');
    if (!startInput || !endInput) return;

    const now = new Date();
    const startDefault = formatDatetime(new Date(now.getTime() - 3600000));
    const endDefault   = formatDatetime(now);

    startInput.value = startDefault;
    endInput.value   = endDefault;

    var previewPage = 1;

    const fpStart = flatpickr(startInput, {
      enableTime: true,
      enableSeconds: true,
      dateFormat: 'Y/m/d H:i:S',
      time_24hr: true,
      defaultDate: startDefault,
      onChange: function () { previewPage = 1; fetchPreview(); },
    });

    const fpEnd = flatpickr(endInput, {
      enableTime: true,
      enableSeconds: true,
      dateFormat: 'Y/m/d H:i:S',
      time_24hr: true,
      defaultDate: endDefault,
      onChange: function () { previewPage = 1; fetchPreview(); },
    });

    // 開始日時リフレッシュボタン
    const startRefreshBtn = document.getElementById('preview-start-refresh');
    if (startRefreshBtn) {
      startRefreshBtn.addEventListener('click', function () {
        const d = new Date();
        d.setHours(d.getHours() - 1);
        const val = formatDatetime(d);
        startInput.value = val;
        if (fpStart) fpStart.setDate(val, true);
        previewPage = 1;
        fetchPreview();
      });
    }

    // 終了日時リフレッシュボタン
    const endRefreshBtn = document.getElementById('preview-end-refresh');
    if (endRefreshBtn) {
      endRefreshBtn.addEventListener('click', function () {
        const val = formatDatetime(new Date());
        endInput.value = val;
        if (fpEnd) fpEnd.setDate(val, true);
        previewPage = 1;
        fetchPreview();
      });
    }

    // 初回プレビュー
    fetchPreview();

    function fetchPreview() {
      const start = startInput.value;
      const end   = endInput.value;
      if (!start || !end) return;

      fetch('/analysis/customer-dashboard/gadgets/preview/grid/data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ start_datetime: start, end_datetime: end, page: previewPage }),
      })
        .then(function (res) {
          if (res.status === 400) {
            showPreviewDatetimeError();
            return null;
          }
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (data) {
          if (data === null) return;
          clearPreviewError();
          renderPreviewTable(data);
          renderPreviewPagination(data, function (page) {
            previewPage = page;
            fetchPreview();
          });
        })
        .catch(function (err) {
          console.error('プレビューデータ取得エラー:', err);
        });
    }
  }

  function showPreviewDatetimeError() {
    const errEl = document.getElementById('preview-error-msg');
    if (errEl) errEl.innerHTML = '<span class="form__error">' + DATETIME_ERROR_MSG + '</span>';
    const thead = document.getElementById('preview-thead');
    if (thead) thead.innerHTML = '<tr></tr>';
    const tbody = document.getElementById('preview-tbody');
    if (tbody) tbody.innerHTML = '';
    const pagination = document.getElementById('preview-pagination');
    if (pagination) pagination.innerHTML = '';
  }

  function clearPreviewError() {
    const errEl = document.getElementById('preview-error-msg');
    if (errEl) errEl.innerHTML = '';
  }

  function renderPreviewPagination(data, onPageChange) {
    const container = document.getElementById('preview-pagination');
    if (!container) return;

    const totalCount = data.total_count || 0;
    const perPage    = data.per_page || 25;
    const page       = data.page || 1;
    const totalPages = Math.ceil(totalCount / perPage) || 1;

    container.innerHTML = '';
    if (totalPages <= 1) return;

    const nav = document.createElement('nav');
    nav.className = 'pagination';

    // 前へ
    const prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = 'pagination__button';
    prevBtn.textContent = '«';
    prevBtn.disabled = (page <= 1);
    prevBtn.addEventListener('click', function () {
      if (page > 1) onPageChange(page - 1);
    });
    nav.appendChild(prevBtn);

    // ページ番号
    for (let i = 1; i <= totalPages; i++) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pagination__button' + (i === page ? ' pagination__button--active' : '');
      btn.textContent = i;
      btn.dataset.page = i;
      btn.addEventListener('click', function () {
        onPageChange(parseInt(this.dataset.page, 10));
      });
      nav.appendChild(btn);
    }

    // 次へ
    const nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = 'pagination__button';
    nextBtn.textContent = '»';
    nextBtn.disabled = (page >= totalPages);
    nextBtn.addEventListener('click', function () {
      if (page < totalPages) onPageChange(page + 1);
    });
    nav.appendChild(nextBtn);

    container.appendChild(nav);
  }

  function renderPreviewTable(data) {
    const thead = document.getElementById('preview-thead');
    const tbody = document.getElementById('preview-tbody');
    if (!thead || !tbody) return;

    // ヘッダー描画
    const tr = document.createElement('tr');
    ['受信日時', 'デバイス名称'].forEach(function (label) {
      const th = document.createElement('th');
      th.textContent = label;
      tr.appendChild(th);
    });
    (data.columns || []).forEach(function (col) {
      const th = document.createElement('th');
      th.textContent = col.display_name;
      tr.appendChild(th);
    });
    thead.innerHTML = '';
    thead.appendChild(tr);

    // ボディ描画
    tbody.innerHTML = '';
    (data.grid_data || []).forEach(function (row) {
      const tr = document.createElement('tr');

      const tdTs = document.createElement('td');
      tdTs.textContent = row.event_timestamp || '';
      tr.appendChild(tdTs);

      const tdDev = document.createElement('td');
      tdDev.textContent = row.device_name || '';
      tdDev.title = row.device_name || '';
      tr.appendChild(tdDev);

      (data.columns || []).forEach(function (col) {
        const td = document.createElement('td');
        const val = row[col.column_name];
        td.textContent = (val !== null && val !== undefined) ? val : '';
        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });
  }

  // ============================================================
  // Cookie
  // ============================================================

  function saveToCookie(state) {
    const key = COOKIE_KEY.replace('{uuid}', state.uuid);
    const val = JSON.stringify({
      start_datetime: state.startDatetime,
      end_datetime:   state.endDatetime,
      page:           state.page,
    });
    document.cookie = key + '=' + encodeURIComponent(val)
      + '; max-age=' + COOKIE_MAX_AGE + '; path=/';
  }

  function restoreFromCookie(state) {
    const key = COOKIE_KEY.replace('{uuid}', state.uuid);
    const match = document.cookie.match(new RegExp('(?:^|; )' + key + '=([^;]*)'));
    if (!match) return;
    try {
      const parsed = JSON.parse(decodeURIComponent(match[1]));
      if (parsed.start_datetime) state.startDatetime = parsed.start_datetime;
      if (parsed.end_datetime)   state.endDatetime   = parsed.end_datetime;
      if (parsed.page)           state.page          = parsed.page;
    } catch (e) {
      // ignore
    }
  }

  // ============================================================
  // ユーティリティ
  // ============================================================

  function formatDatetime(d) {
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return d.getFullYear() + '/' +
      pad(d.getMonth() + 1) + '/' +
      pad(d.getDate()) + ' ' +
      pad(d.getHours()) + ':' +
      pad(d.getMinutes()) + ':' +
      pad(d.getSeconds());
  }

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  // ============================================================
  // 登録モーダルバインダー登録
  // ============================================================

  function bindGridGadgetRegister() {
    // 登録モーダル用の追加バインド（共通フレームワークから呼ばれる）
    initRegisterModal();
  }

  // ============================================================
  // エントリーポイント
  // ============================================================

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllGadgets);
  } else {
    initAllGadgets();
  }

  if (typeof CustomerDashboard !== 'undefined' && CustomerDashboard.registerModalBinder) {
    CustomerDashboard.registerModalBinder(bindGridGadgetRegister);
  }

}());
