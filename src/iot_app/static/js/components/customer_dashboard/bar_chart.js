'use strict';

/**
 * 棒グラフガジェット管理
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

  // ============================================================
  // ガジェット初期化
  // ============================================================
  function initAllGadgets() {
    document.querySelectorAll('.bar-chart[data-gadget-uuid]').forEach(function (el) {
      initGadget(el);
    });
  }

  function initGadget(el) {
    const uuid    = el.dataset.gadgetUuid;
    const chartEl = el.querySelector('.bar-chart__canvas');
    if (!chartEl) return;
    const _rawConfig = el.closest('.gadget')?.dataset.chartConfig || '{}';
    const _parsed = JSON.parse(_rawConfig);
    const chartConfig = typeof _parsed === 'string' ? JSON.parse(_parsed) : _parsed;

    const chart = echarts.init(chartEl);
    setEmptyChart(chart);

    const state = {
      uuid:        uuid,
      chart:       chart,
      displayUnit: DEFAULT_UNIT,
      interval:    DEFAULT_INTERVAL,
      baseDatetime: nowString(),
      fp:          null,
      minValue:    chartConfig.min_value ?? null,
      maxValue:    chartConfig.max_value ?? null,
      errorEl:     el.querySelector('.bar-chart__error'),
    };

    bindControls(el, state);
    fetchAndRender(state);
  }

  // ============================================================
  // UI バインド
  // ============================================================
  function bindControls(el, state) {
    // 表示単位ボタン
    el.querySelectorAll('.bar-chart__unit-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        el.querySelectorAll('.bar-chart__unit-btn').forEach(function (b) {
          b.classList.remove('bar-chart__unit-btn--active');
        });
        btn.classList.add('bar-chart__unit-btn--active');
        state.displayUnit = btn.dataset.unit;
        updateDatetimeLabel(el, state.displayUnit);
        toggleIntervalSelector(el, state.displayUnit);
        // flatpickr を単位に合わせて再初期化
        const datetimeInput = el.querySelector('.bar-chart__datetime-input');
        if (datetimeInput && state.fp) {
          state.fp.destroy();
          state.fp = createFlatpickr(datetimeInput, state);
        }
        fetchAndRender(state);
      });
    });

    // 集計時間幅セレクト
    const intervalSelect = el.querySelector('.bar-chart__interval-select');
    if (intervalSelect) {
      intervalSelect.addEventListener('change', function () {
        state.interval = intervalSelect.value;
        fetchAndRender(state);
      });
    }

    // 時間帯 DateTimePicker (flatpickr)
    const datetimeInput = el.querySelector('.bar-chart__datetime-input');
    if (datetimeInput) {
      state.fp = createFlatpickr(datetimeInput, state);
    }

    // カレンダーアイコンボタン
    const calendarBtn = el.querySelector('.bar-chart__calendar-btn');
    if (calendarBtn) {
      calendarBtn.addEventListener('click', function () {
        if (state.fp) state.fp.open();
      });
    }

    // 更新ボタン
    const refreshBtn = el.querySelector('.bar-chart__refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', function () {
        const config = getUnitConfig(state.displayUnit);
        state.baseDatetime = config.defaultDate;
        if (state.fp) state.fp.setDate(state.baseDatetime, false);
        fetchAndRender(state);
      });
    }

    // CSVエクスポートボタン（ガジェット共通ツールバー）
    const gadgetEl = el.closest('.gadget');
    if (gadgetEl) {
      const csvBtn = gadgetEl.querySelector('.gadget__csv-btn');
      if (csvBtn) {
        csvBtn.addEventListener('click', function (e) {
          e.preventDefault();
          exportCsv(state);
        });
      }

      // ツールバー日時ボタン連動（common.js からの CustomEvent を受信）
      gadgetEl.addEventListener('gadget:daterange-changed', function (e) {
        const { range, start } = e.detail;
        const config = _rangeToBarChartConfig(range, start);

        // displayUnit が変わる場合は flatpickr を再初期化
        if (config.unit !== state.displayUnit) {
          state.displayUnit = config.unit;
          const datetimeInput = el.querySelector('.bar-chart__datetime-input');
          if (datetimeInput && state.fp) {
            state.fp.destroy();
            state.fp = createFlatpickr(datetimeInput, state);
          }
          updateDatetimeLabel(el, state.displayUnit);
          toggleIntervalSelector(el, state.displayUnit);
          // UIアクティブボタン更新
          el.querySelectorAll('.bar-chart__unit-btn').forEach(function (btn) {
            btn.classList.toggle('bar-chart__unit-btn--active', btn.dataset.unit === state.displayUnit);
          });
        }

        // baseDatetime を上書き（createFlatpickr がデフォルト値をセットするため後から上書き）
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
        if (!res.ok) {
          return res.json().then(function (data) {
            if (state.errorEl) state.errorEl.textContent = data.error;
          }).catch(function () {});
        }
        return res.json().then(function (data) {
          if (state.errorEl) state.errorEl.textContent = '';
          renderChart(state.chart, data.chart_data, state.displayUnit, state.minValue, state.maxValue);
        });
      })
      .catch(function (err) {
        console.error('棒グラフデータ取得エラー:', err);
        setEmptyChart(state.chart);
      });
  }

  // ============================================================
  // ECharts 描画
  // ============================================================
  function renderChart(chart, chartData, displayUnit, minValue, maxValue) {
    const labels      = chartData.labels       || [];
    const values      = chartData.values       || [];
    const legendLabel = chartData.legend_label || '';

    const yAxis = { type: 'value' };
    if (minValue !== null && minValue !== undefined) yAxis.min = minValue;
    if (maxValue !== null && maxValue !== undefined) yAxis.max = maxValue;

    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: {
        bottom: 0,
        data:   [legendLabel],
      },
      xAxis: {
        type: 'category',
        data: labels,
      },
      yAxis: yAxis,
      series: [{
        name:      legendLabel,
        type:      'bar',
        data:      values,
        itemStyle: { color: '#2272B4' },
      }],
    });
  }

  function setEmptyChart(chart) {
    chart.setOption({
      xAxis:  { type: 'category', data: [] },
      yAxis:  { type: 'value' },
      series: [{ type: 'bar', data: [] }],
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
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (data) {
            Toast.show(data.error || MESSAGES.ERR_CSV_DOWNLOAD_FAILED, 'error');
          });
        }
        return res.blob().then(function (blob) {
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = 'sensor_data.csv';
          a.click();
          URL.revokeObjectURL(a.href);
        });
      })
      .catch(function () {
        Toast.show(MESSAGES.ERR_CSV_DOWNLOAD_FAILED, 'error');
      });
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

  function mondayString() {
    const d = new Date();
    const day = d.getDay();
    d.setDate(d.getDate() - ((day + 6) % 7));
    const pad = function (n) { return String(n).padStart(2, '0'); };
    return d.getFullYear() + '/' + pad(d.getMonth() + 1) + '/' + pad(d.getDate());
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

  function _rangeToBarChartConfig(range, start) {
    switch (range) {
      case 'today':      return { unit: 'hour',  datetime: nowString() };
      case 'yesterday':  return { unit: 'day',   datetime: yesterdayString() };
      case 'this_week':  return { unit: 'week',  datetime: mondayString() };
      case 'this_month': return { unit: 'month', datetime: thisMonthString() };
      case 'this_year':  return { unit: 'hour',  datetime: nowString() };
      case 'custom':
        return { unit: 'hour', datetime: start ? start.replace(/-/g, '/').replace('T', ' ') : nowString() };
      default:           return { unit: 'hour',  datetime: nowString() };
    }
  }

  function updateDatetimeLabel(el, displayUnit) {
    const labelMap = { hour: '時間帯：', day: '表示日：', week: '表示週：', month: '表示月：' };
    const labelEl = el.querySelector('.bar-chart__datetime-label');
    if (labelEl) labelEl.textContent = labelMap[displayUnit] || '時間帯：';
  }

  function toggleIntervalSelector(el, displayUnit) {
    const selectorEl = el.querySelector('.bar-chart__interval-selector');
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

// ============================================================
// 棒グラフ登録モーダル UIバインド
// ============================================================

/**
 * 棒グラフ登録モーダルのUIイベントをバインドする
 * @param {Element} container - モーダルコンテナ要素
 */
function bindBarChartGadgetRegister(container) {
  const modeButtons = container.querySelectorAll('.bar-chart-register__device-mode-btn');
  if (!modeButtons.length) return;

  const deviceModeInput = container.querySelector('#device_mode');
  const deviceFixedArea = container.querySelector('#device-fixed-area');
  const deviceNameArea  = container.querySelector('#device-name-area');
  const orgFilter       = container.querySelector('#organization-filter');
  const deviceSelect    = container.querySelector('#device-select');

  modeButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      modeButtons.forEach(function (b) {
        b.classList.remove('bar-chart-register__device-mode-btn--active');
      });
      btn.classList.add('bar-chart-register__device-mode-btn--active');
      const mode = btn.dataset.mode;
      if (deviceModeInput) deviceModeInput.value = mode;
      const isFixed = mode === 'fixed';
      if (deviceFixedArea) deviceFixedArea.style.visibility = isFixed ? 'visible' : 'hidden';
      if (deviceNameArea)  deviceNameArea.style.visibility  = isFixed ? 'visible' : 'hidden';
    });
  });

  if (!orgFilter || !deviceSelect) return;

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

  deviceSelect.addEventListener('change', function () {
    const selected = deviceSelect.options[deviceSelect.selectedIndex];
    const nameEl = container.querySelector('#selected-device-name');
    if (nameEl) nameEl.textContent = selected ? (selected.dataset.name || '-') : '-';
  });
}

CustomerDashboard.registerModalBinder(bindBarChartGadgetRegister);
