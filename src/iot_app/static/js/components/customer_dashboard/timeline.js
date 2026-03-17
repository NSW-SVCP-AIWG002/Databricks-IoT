/**
 * 顧客作成ダッシュボード 時系列グラフガジェット JS
 *
 * 参照設計書:
 *   - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
 *   - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
 */

'use strict';

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const CHART_COLOR_LEFT   = '#2272B4';  // --color-primary
const CHART_COLOR_RIGHT  = '#F5A623';

// ---------------------------------------------------------------------------
// ユーティリティ
// ---------------------------------------------------------------------------

/**
 * Date → "YYYY/MM/DD HH:mm:ss" 文字列に変換
 * @param {Date} date
 * @returns {string}
 */
function formatDatetime(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return (
    date.getFullYear() + '/' +
    pad(date.getMonth() + 1) + '/' +
    pad(date.getDate()) + ' ' +
    pad(date.getHours()) + ':' +
    pad(date.getMinutes()) + ':' +
    pad(date.getSeconds())
  );
}

/**
 * 現在日時を返す
 * @returns {Date}
 */
function now() {
  return new Date();
}

/**
 * 現在日時 - 1時間を返す
 * @returns {Date}
 */
function oneHourAgo() {
  const d = now();
  d.setHours(d.getHours() - 1);
  return d;
}

// ---------------------------------------------------------------------------
// ECharts グラフ描画
// ---------------------------------------------------------------------------

/**
 * ECharts オプションを生成する
 * @param {object} chartData  - { labels, left_values, right_values, left_label, right_label, left_unit, right_unit, left_min, left_max, right_min, right_max }
 * @returns {object} ECharts option
 */
function buildChartOption(chartData) {
  const {
    labels,
    left_values,
    right_values,
    left_label  = '左軸',
    right_label = '右軸',
    left_unit   = '',
    right_unit  = '',
    left_min,
    left_max,
    right_min,
    right_max,
  } = chartData;

  const leftYAxis = {
    type: 'value',
    splitNumber: 10,
    axisLabel: { fontSize: 10 },
  };
  if (left_min !== null && left_min !== undefined) leftYAxis.min = left_min;
  if (left_max !== null && left_max !== undefined) leftYAxis.max = left_max;

  const rightYAxis = {
    type: 'value',
    splitNumber: 10,
    axisLabel: { fontSize: 10 },
  };
  if (right_min !== null && right_min !== undefined) rightYAxis.min = right_min;
  if (right_max !== null && right_max !== undefined) rightYAxis.max = right_max;

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        if (!params || !params.length) return '';
        let html = `${params[0].axisValue}<br>`;
        params.forEach((p) => {
          html += `${p.marker}${p.seriesName}: ${p.value}<br>`;
        });
        return html;
      },
    },
    legend: { show: false },
    grid: { left: '60px', right: '60px', bottom: '40px', top: '20px' },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 0,
        fontSize: 10,
        interval: (index) => index === 0 || index === labels.length - 1,
        formatter: (v) => v ? v.slice(5, 16) : '',
      },
    },
    yAxis: [leftYAxis, rightYAxis],
    series: [
      {
        name: left_label,
        type: 'line',
        yAxisIndex: 0,
        data: left_values,
        lineStyle: { color: CHART_COLOR_LEFT, width: 2 },
        itemStyle: { color: CHART_COLOR_LEFT },
        showSymbol: false,
      },
      {
        name: right_label,
        type: 'line',
        yAxisIndex: 1,
        data: right_values,
        lineStyle: { color: CHART_COLOR_RIGHT, width: 2 },
        itemStyle: { color: CHART_COLOR_RIGHT },
        showSymbol: false,
      },
    ],
  };
}

/**
 * 凡例エリアを描画する
 * @param {HTMLElement} legendEl
 * @param {object} chartData
 */
function renderLegends(legendEl, chartData) {
  const {
    left_label   = '左軸',
    right_label  = '右軸',
    left_unit    = '',
    right_unit   = '',
    left_min,
    left_max,
    right_min,
    right_max,
  } = chartData;

  let html = '';

  // 左凡例
  html += `<span class="timeline__legend-item" style="color:${CHART_COLOR_LEFT}">■ ${left_label}（${left_unit}）</span>`;
  // 右凡例
  html += `<span class="timeline__legend-item" style="color:${CHART_COLOR_RIGHT}">■ ${right_label}（${right_unit}）</span>`;

  // 上限/下限凡例（設定値がある場合のみ）
  if (left_max !== null && left_max !== undefined) {
    html += `<span class="timeline__legend-item">上限（${left_label}）: ${left_max}</span>`;
  }
  if (left_min !== null && left_min !== undefined) {
    html += `<span class="timeline__legend-item">下限（${left_label}）: ${left_min}</span>`;
  }
  if (right_max !== null && right_max !== undefined) {
    html += `<span class="timeline__legend-item">上限（${right_label}）: ${right_max}</span>`;
  }
  if (right_min !== null && right_min !== undefined) {
    html += `<span class="timeline__legend-item">下限（${right_label}）: ${right_min}</span>`;
  }

  legendEl.innerHTML = html;
}

// ---------------------------------------------------------------------------
// AJAX
// ---------------------------------------------------------------------------

/**
 * ガジェットデータを取得してグラフを更新する
 * @param {string}      gadgetUuid
 * @param {echarts}     chart
 * @param {HTMLElement} legendEl
 * @param {string}      startDatetime
 * @param {string}      endDatetime
 */
async function fetchAndRender(gadgetUuid, chart, legendEl, startDatetime, endDatetime) {
  try {
    const resp = await fetch(
      `/analysis/customer-dashboard/gadgets/${gadgetUuid}/data`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_datetime: startDatetime,
          end_datetime:   endDatetime,
        }),
      }
    );

    if (!resp.ok) {
      console.error(`[timeline] データ取得失敗: gadget_uuid=${gadgetUuid} status=${resp.status}`);
      return;
    }

    const data = await resp.json();
    if (data.error) {
      console.error(`[timeline] サーバーエラー: ${data.error}`);
      return;
    }

    const chartData = data.chart_data || {};
    chart.setOption(buildChartOption(chartData));
    renderLegends(legendEl, chartData);

    // デバイス名を更新
    const deviceNameEl = document.querySelector(
      `.gadget[data-gadget-uuid="${gadgetUuid}"] .timeline__device-name`
    );
    if (deviceNameEl && chartData.device_name) {
      deviceNameEl.textContent = chartData.device_name;
    }

  } catch (err) {
    console.error(`[timeline] fetchAndRender エラー:`, err);
  }
}

// ---------------------------------------------------------------------------
// ガジェット初期化
// ---------------------------------------------------------------------------

/**
 * 1つのガジェットを初期化する
 * @param {HTMLElement} gadgetEl
 */
function initGadget(gadgetEl) {
  const gadgetUuid = gadgetEl.dataset.gadgetUuid;

  // ECharts 初期化
  const canvasEl = document.getElementById(`chart-${gadgetUuid}`);
  if (!canvasEl) return;
  const chart = echarts.init(canvasEl);

  // 凡例エリア
  const legendEl = document.getElementById(`legends-${gadgetUuid}`);

  // 初期日時
  const initStart = oneHourAgo();
  const initEnd   = now();

  // flatpickr 初期化（開始日時）
  const startFp = flatpickr(`#start-datetime-${gadgetUuid}`, {
    locale:         'ja',
    enableTime:     true,
    enableSeconds:  true,
    dateFormat:     'Y/m/d H:i:S',
    defaultDate:    initStart,
    onChange: (_dates, dateStr) => {
      const endInput = document.getElementById(`end-datetime-${gadgetUuid}`);
      fetchAndRender(gadgetUuid, chart, legendEl, dateStr, endInput.value);
    },
  });

  // flatpickr 初期化（終了日時）
  const endFp = flatpickr(`#end-datetime-${gadgetUuid}`, {
    locale:         'ja',
    enableTime:     true,
    enableSeconds:  true,
    dateFormat:     'Y/m/d H:i:S',
    defaultDate:    initEnd,
    onChange: (_dates, dateStr) => {
      const startInput = document.getElementById(`start-datetime-${gadgetUuid}`);
      fetchAndRender(gadgetUuid, chart, legendEl, startInput.value, dateStr);
    },
  });

  // 🔄 開始日時リセットボタン（現在日時-1時間）
  const refreshBtns = gadgetEl.querySelectorAll('.timeline__refresh-btn');
  if (refreshBtns[0]) {
    refreshBtns[0].addEventListener('click', () => {
      startFp.setDate(oneHourAgo(), true);
    });
  }
  // 🔄 終了日時リセットボタン（現在日時）
  if (refreshBtns[1]) {
    refreshBtns[1].addEventListener('click', () => {
      endFp.setDate(now(), true);
    });
  }

  // CSV エクスポートボタン
  const csvBtn = gadgetEl.querySelector('.gadget__csv-btn');
  if (csvBtn) {
    csvBtn.addEventListener('click', () => {
      const startInput = document.getElementById(`start-datetime-${gadgetUuid}`);
      const endInput   = document.getElementById(`end-datetime-${gadgetUuid}`);
      const start = encodeURIComponent(startInput.value);
      const end   = encodeURIComponent(endInput.value);
      window.location.href =
        `/analysis/customer-dashboard/gadgets/${gadgetUuid}?export=csv&start_datetime=${start}&end_datetime=${end}`;
    });
  }

  // ウィンドウリサイズ対応
  window.addEventListener('resize', () => chart.resize());

  // 初期データ取得
  fetchAndRender(gadgetUuid, chart, legendEl, formatDatetime(initStart), formatDatetime(initEnd));
}

// ---------------------------------------------------------------------------
// エントリーポイント
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  const gadgetEls = document.querySelectorAll('.gadget[data-gadget-uuid]');
  gadgetEls.forEach((el) => initGadget(el));
});
