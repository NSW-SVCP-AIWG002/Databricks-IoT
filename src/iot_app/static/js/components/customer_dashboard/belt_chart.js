'use strict';

/**
 * 帯グラフガジェット管理
 * 各ガジェットのECharts描画・AJAX・UI操作を担当する
 */
(function () {

  // ============================================================
  // 定数
  // ============================================================
  const DATA_ENDPOINT = '/analysis/customer-dashboard/gadgets/{uuid}/data';
  const CSV_ENDPOINT  = '/analysis/customer-dashboard/gadgets/{uuid}';
  const DEFAULT_UNIT     = 'hour';
  const DEFAULT_INTERVAL = '10min';

  // ECharts 系列カラー
  const SERIES_COLORS = ['#E8877F', '#7CB5D2', '#A8D88E', '#F0C87A', '#B39CD0'];

  // ============================================================
  // ガジェット初期化
  // ============================================================
  function initAllGadgets() {
    document.querySelectorAll('.belt-chart[data-gadget-uuid]').forEach(function (el) {
      initGadget(el);
    });
  }

  function initGadget(el) {
    const uuid    = el.dataset.gadgetUuid;
    const chartEl = el.querySelector('.belt-chart__canvas');
    if (!chartEl) return;

    const chart = echarts.init(chartEl);
    setEmptyChart(chart);

    const state = {
      uuid:         uuid,
      chart:        chart,
      displayUnit:  DEFAULT_UNIT,
      interval:     DEFAULT_INTERVAL,
      baseDatetime: nowString(),
      fp:           null,
    };

    bindControls(el, state);
    fetchAndRender(state);
  }

  // ============================================================
  // UI バインド
  // ============================================================
  function bindControls(el, state) {
    // 表示単位ボタン
    el.querySelectorAll('.belt-chart__unit-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        el.querySelectorAll('.belt-chart__unit-btn').forEach(function (b) {
          b.classList.remove('belt-chart__unit-btn--active');
        });
        btn.classList.add('belt-chart__unit-btn--active');
        state.displayUnit = btn.dataset.unit;
        updateDatetimeLabel(el, state.displayUnit);
        toggleIntervalSelector(el, state.displayUnit);
        const datetimeInput = el.querySelector('.belt-chart__datetime-input');
        if (datetimeInput && state.fp) {
          state.fp.destroy();
          state.fp = createFlatpickr(datetimeInput, state);
        }
        fetchAndRender(state);
      });
    });

    // 集計時間幅セレクト
    const intervalSelect = el.querySelector('.belt-chart__interval-select');
    if (intervalSelect) {
      intervalSelect.addEventListener('change', function () {
        state.interval = intervalSelect.value;
        fetchAndRender(state);
      });
    }

    // 時間帯 DateTimePicker (flatpickr)
    const datetimeInput = el.querySelector('.belt-chart__datetime-input');
    if (datetimeInput) {
      state.fp = createFlatpickr(datetimeInput, state);
    }

    // カレンダーアイコンボタン
    const calendarBtn = el.querySelector('.belt-chart__calendar-btn');
    if (calendarBtn) {
      calendarBtn.addEventListener('click', function () {
        if (state.fp) state.fp.open();
      });
    }

    // 更新ボタン
    const refreshBtn = el.querySelector('.belt-chart__refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', function () {
        const config = getUnitConfig(state.displayUnit);
        state.baseDatetime = config.defaultDate;
        if (state.fp) state.fp.setDate(state.baseDatetime, false);
        fetchAndRender(state);
      });
    }

    // CSVエクスポートボタン
    const gadgetEl = el.closest('.gadget');
    if (gadgetEl) {
      const csvBtn = gadgetEl.querySelector('.gadget__csv-btn');
      if (csvBtn) {
        csvBtn.addEventListener('click', function (e) {
          e.preventDefault();
          exportCsv(state);
        });
      }

      // ツールバー日時ボタン連動
      gadgetEl.addEventListener('gadget:daterange-changed', function (e) {
        const { range, start } = e.detail;
        const config = _rangeToBeltChartConfig(range, start);

        if (config.unit !== state.displayUnit) {
          state.displayUnit = config.unit;
          const datetimeInput = el.querySelector('.belt-chart__datetime-input');
          if (datetimeInput && state.fp) {
            state.fp.destroy();
            state.fp = createFlatpickr(datetimeInput, state);
          }
          updateDatetimeLabel(el, state.displayUnit);
          toggleIntervalSelector(el, state.displayUnit);
          el.querySelectorAll('.belt-chart__unit-btn').forEach(function (btn) {
            btn.classList.toggle('belt-chart__unit-btn--active', btn.dataset.unit === state.displayUnit);
          });
        }

        state.baseDatetime = config.datetime;
        if (state.fp) state.fp.setDate(state.baseDatetime, false);

        fetchAndRender(state);
      });
    }
  }

  // ============================================================
  // データ取得 & 描画
  // ============================================================
  function fetchAndRender(state) {
    const url = DATA_ENDPOINT.replace('{uuid}', state.uuid);
    fetch(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        display_unit:  state.displayUnit,
        interval:      state.interval,
        base_datetime: toFullDatetime(state.baseDatetime, state.displayUnit),
      }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        renderChart(state.chart, data.chart_data, state.displayUnit);
      })
      .catch(function (err) {
        console.error('帯グラフデータ取得エラー:', err);
        setEmptyChart(state.chart);
      });
  }

  // ============================================================
  // ECharts 描画（積み上げ棒グラフ）
  // ============================================================
  function renderChart(chart, chartData, displayUnit) {
    const labels = chartData.labels  || [];
    const series = chartData.series  || [];

    const echartsSeriesList = series.map(function (s, i) {
      return {
        name:      s.name,
        type:      'bar',
        stack:     'total',
        data:      s.values,
        itemStyle: { color: SERIES_COLORS[i % SERIES_COLORS.length] },
      };
    });

    const legendData = series.map(function (s) { return s.name; });

    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend:  { bottom: 0, data: legendData },
      xAxis:   { type: 'category', data: labels },
      yAxis:   { type: 'value' },
      series:  echartsSeriesList,
    });
  }

  function setEmptyChart(chart) {
    chart.setOption({
      xAxis:  { type: 'category', data: [] },
      yAxis:  { type: 'value' },
      series: [{ type: 'bar', stack: 'total', data: [] }],
    });
  }

  // ============================================================
  // CSV エクスポート
  // ============================================================
  function exportCsv(state) {
    const params = new URLSearchParams({
      export:        'csv',
      display_unit:  state.displayUnit,
      interval:      state.interval,
      base_datetime: toFullDatetime(state.baseDatetime, state.displayUnit),
    });
    const url = CSV_ENDPOINT.replace('{uuid}', state.uuid) + '?' + params.toString();
    window.location.href = url;
  }

  // ============================================================
  // ユーティリティ
  // ============================================================
  function nowString() {
    const now = new Date();
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return now.getFullYear() + '/' +
      pad(now.getMonth() + 1) + '/' +
      pad(now.getDate()) + ' ' +
      pad(now.getHours()) + ':' +
      pad(now.getMinutes()) + ':' +
      pad(now.getSeconds());
  }

  function yesterdayString() {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return d.getFullYear() + '/' + pad(d.getMonth() + 1) + '/' + pad(d.getDate());
  }

  function prevMonthString() {
    const d = new Date();
    d.setDate(1);
    d.setMonth(d.getMonth() - 1);
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return d.getFullYear() + '/' + pad(d.getMonth() + 1);
  }

  function thisMonthString() {
    const d = new Date();
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return d.getFullYear() + '/' + pad(d.getMonth() + 1);
  }

  function toFullDatetime(baseDatetime, displayUnit) {
    if (displayUnit === 'day' || displayUnit === 'week') {
      return baseDatetime + ' 00:00:00';
    }
    if (displayUnit === 'month') {
      return baseDatetime + '/01 00:00:00';
    }
    return baseDatetime;
  }

  function getUnitConfig(displayUnit) {
    switch (displayUnit) {
      case 'day':
        return { dateFormat: 'Y/m/d', enableTime: false, enableSeconds: false, defaultDate: yesterdayString() };
      case 'week':
        return { dateFormat: 'Y/m/d', enableTime: false, enableSeconds: false, defaultDate: yesterdayString() };
      case 'month':
        return { dateFormat: 'Y/m', enableTime: false, enableSeconds: false, defaultDate: prevMonthString() };
      default: // hour
        return { dateFormat: 'Y/m/d H:i:S', enableTime: true, enableSeconds: true, defaultDate: nowString() };
    }
  }

  function createFlatpickr(datetimeInput, state) {
    const config = getUnitConfig(state.displayUnit);
    state.baseDatetime = config.defaultDate;
    return flatpickr(datetimeInput, {
      locale:        'ja',
      enableTime:    config.enableTime,
      enableSeconds: config.enableSeconds,
      time_24hr:     true,
      dateFormat:    config.dateFormat,
      defaultDate:   config.defaultDate,
      onChange: function (_selectedDates, dateStr) {
        state.baseDatetime = dateStr;
        fetchAndRender(state);
      },
    });
  }

  function _rangeToBeltChartConfig(range, start) {
    switch (range) {
      case 'today':      return { unit: 'hour',  datetime: nowString() };
      case 'yesterday':  return { unit: 'day',   datetime: yesterdayString() };
      case 'this_week':  return { unit: 'week',  datetime: yesterdayString() };
      case 'this_month': return { unit: 'month', datetime: thisMonthString() };
      case 'this_year':  return { unit: 'hour',  datetime: nowString() };
      case 'custom':
        return { unit: 'hour', datetime: start ? start.replace(/-/g, '/').replace('T', ' ') : nowString() };
      default:           return { unit: 'hour',  datetime: nowString() };
    }
  }

  function updateDatetimeLabel(el, displayUnit) {
    const labelMap = { hour: '時間帯：', day: '表示日：', week: '表示週：', month: '表示月：' };
    const labelEl = el.querySelector('.belt-chart__datetime-label');
    if (labelEl) labelEl.textContent = labelMap[displayUnit] || '時間帯：';
  }

  function toggleIntervalSelector(el, displayUnit) {
    const selectorEl = el.querySelector('.belt-chart__interval-selector');
    if (selectorEl) {
      selectorEl.style.display = displayUnit === 'hour' ? '' : 'none';
    }
  }

  // ============================================================
  // エントリーポイント
  // ============================================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllGadgets);
  } else {
    initAllGadgets();
  }

})();

// ---------------------------------------------------------------------------
// 登録モーダル イベントバインド（common.js の _bindModalEvents から呼ばれる）
// ---------------------------------------------------------------------------

/**
 * 帯グラフ登録モーダルのイベントをバインドする
 * @param {Element} container - モーダルコンテナ要素
 */
function bindBeltChartGadgetRegister(container) {
  var modeBtns = container.querySelectorAll('.belt-chart-register__device-mode-btn');
  if (!modeBtns.length) return;

  var deviceModeInput = container.querySelector('#device_mode');
  var deviceFixedArea = container.querySelector('#device-fixed-area');
  var deviceNameArea  = container.querySelector('#device-name-area');
  var deviceSelect    = container.querySelector('#device-select');

  function applyMode(mode) {
    modeBtns.forEach(function (btn) {
      btn.classList.toggle('belt-chart-register__device-mode-btn--active', btn.dataset.mode === mode);
    });
    if (deviceModeInput) deviceModeInput.value = mode;
    var isFixed = mode === 'fixed';
    if (deviceFixedArea) deviceFixedArea.style.visibility = isFixed ? 'visible' : 'hidden';
    if (deviceNameArea)  deviceNameArea.style.visibility  = isFixed ? 'visible' : 'hidden';
    if (!isFixed && deviceSelect) {
      deviceSelect.value = '';
      var nameEl = container.querySelector('#selected-device-name');
      if (nameEl) nameEl.textContent = '-';
    }
  }

  modeBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyMode(btn.dataset.mode);
    });
  });

  var orgFilter = container.querySelector('#organization-filter');

  if (orgFilter && deviceSelect) {
    var allDeviceOptions = Array.from(deviceSelect.querySelectorAll('option[value]'));

    orgFilter.addEventListener('change', function () {
      var orgId   = orgFilter.value;
      var prevVal = deviceSelect.value;
      deviceSelect.innerHTML = '<option value="">選択してください</option>';
      allDeviceOptions.forEach(function (opt) {
        if (!orgId || opt.dataset.org === orgId) {
          deviceSelect.appendChild(opt.cloneNode(true));
        }
      });
      deviceSelect.value    = prevVal;
      deviceSelect.disabled = !orgId;
      if (!deviceSelect.value) {
        var nameEl = container.querySelector('#selected-device-name');
        if (nameEl) nameEl.textContent = '-';
      }
    });
  }

  if (deviceSelect) {
    deviceSelect.addEventListener('change', function () {
      var opt    = deviceSelect.options[deviceSelect.selectedIndex];
      var nameEl = container.querySelector('#selected-device-name');
      if (nameEl) nameEl.textContent = opt ? (opt.dataset.name || '-') : '-';
    });
  }

  // 422再描画時：選択済みデバイス名を復元
  if (deviceSelect) {
    var selectedOpt = deviceSelect.options[deviceSelect.selectedIndex];
    if (selectedOpt && selectedOpt.value) {
      var nameEl = container.querySelector('#selected-device-name');
      if (nameEl) nameEl.textContent = selectedOpt.dataset.name || '-';
    }
  }

  // チェックボックス最大5個制限
  var checkboxes = container.querySelectorAll('.belt-chart-register__item-checkbox');
  checkboxes.forEach(function (cb) {
    cb.addEventListener('change', function () {
      var checked = container.querySelectorAll('.belt-chart-register__item-checkbox:checked');
      if (checked.length >= 5) {
        checkboxes.forEach(function (c) { if (!c.checked) c.disabled = true; });
      } else {
        checkboxes.forEach(function (c) { c.disabled = false; });
      }
    });
  });
  // 初期状態で5個チェック済みの場合も制限を適用
  var initialChecked = container.querySelectorAll('.belt-chart-register__item-checkbox:checked');
  if (initialChecked.length >= 5) {
    checkboxes.forEach(function (c) { if (!c.checked) c.disabled = true; });
  }

  // 初期状態を適用（hidden inputの現在値に合わせる）
  applyMode(deviceModeInput ? deviceModeInput.value : 'fixed');
}

CustomerDashboard.registerModalBinder(bindBeltChartGadgetRegister);
