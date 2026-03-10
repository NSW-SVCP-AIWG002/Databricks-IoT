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

    const chart = echarts.init(chartEl);
    setEmptyChart(chart);

    const state = {
      uuid:        uuid,
      chart:       chart,
      displayUnit: DEFAULT_UNIT,
      interval:    DEFAULT_INTERVAL,
      baseDatetime: nowString(),
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

    // 時間帯 DateTimePicker
    const datetimeInput = el.querySelector('.bar-chart__datetime-input');
    if (datetimeInput) {
      datetimeInput.value = state.baseDatetime;
      datetimeInput.addEventListener('change', function () {
        state.baseDatetime = datetimeInput.value;
        fetchAndRender(state);
      });
    }

    // 更新ボタン
    const refreshBtn = el.querySelector('.bar-chart__refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', function () {
        state.baseDatetime = nowString();
        if (datetimeInput) datetimeInput.value = state.baseDatetime;
        fetchAndRender(state);
      });
    }

    // CSVエクスポートボタン（ガジェット共通ツールバー）
    const gadgetEl = el.closest('.gadget');
    if (gadgetEl) {
      const csvBtn = gadgetEl.querySelector('.gadget__csv-btn');
      if (csvBtn) {
        csvBtn.addEventListener('click', function () {
          exportCsv(state);
        });
      }
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
        base_datetime: state.baseDatetime,
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
        console.error('棒グラフデータ取得エラー:', err);
        setEmptyChart(state.chart);
      });
  }

  // ============================================================
  // ECharts 描画
  // ============================================================
  function renderChart(chart, chartData, displayUnit) {
    const labels = chartData.labels || [];
    const values = chartData.values || [];

    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: labels,
      },
      yAxis: { type: 'value' },
      series: [{
        type:      'bar',
        data:      values,
        itemStyle: { color: '#2272B4' },
      }],
      legend: { bottom: 0 },
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
      base_datetime: state.baseDatetime,
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
