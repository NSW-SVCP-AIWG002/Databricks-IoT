'use strict';

/**
 * 円グラフガジェット管理
 * 各ガジェットのECharts描画・AJAX通信を担当する
 */
(function () {

  const DATA_ENDPOINT = '/analysis/customer-dashboard/gadgets/{uuid}/data';

  // ============================================================
  // ガジェット初期化
  // ============================================================
  function initAllGadgets() {
    document.querySelectorAll('.circle-chart[data-gadget-uuid]').forEach(function (el) {
      initGadget(el);
    });
  }

  function initGadget(el) {
    const uuid    = el.dataset.gadgetUuid;
    const chartEl = el.querySelector('.circle-chart__canvas');
    if (!chartEl) return;

    const chart = echarts.init(chartEl);
    setEmptyChart(chart);

    const state = {
      uuid:  uuid,
      chart: chart,
    };

    fetchAndRender(state, el);
  }

  // ============================================================
  // データ取得 & 描画
  // ============================================================
  function fetchAndRender(state, el) {
    const url = DATA_ENDPOINT.replace('{uuid}', state.uuid);
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      body: JSON.stringify({}),
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.error) {
          setEmptyChart(state.chart);
          return;
        }
        renderChart(state.chart, data.chart_data);
      })
      .catch(function () {
        setEmptyChart(state.chart);
      });
  }

  // ============================================================
  // ECharts 描画
  // ============================================================
  function setEmptyChart(chart) {
    chart.setOption({
      series: [{ type: 'pie', data: [] }],
    });
  }

  function renderChart(chart, chartData) {
    if (!chartData || !chartData.labels || chartData.labels.length === 0) {
      setEmptyChart(chart);
      return;
    }

    const pieData = chartData.labels.map(function (label, i) {
      return { name: label, value: chartData.values[i] };
    });

    chart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        show: true,
        orient: 'horizontal',
        bottom: 0,
        data: chartData.labels,
      },
      series: [
        {
          type: 'pie',
          radius: '55%',
          center: ['50%', '43%'],
          data: pieData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }, true);
  }

  // ============================================================
  // ユーティリティ
  // ============================================================
  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  // ============================================================
  // 外部公開 & 自動更新フック
  // ============================================================

  /**
   * CustomerDashboard.refreshAll() から呼び出される自動更新フック
   * 各円グラフを再描画する
   */
  function refreshAll() {
    document.querySelectorAll('.circle-chart[data-gadget-uuid]').forEach(function (el) {
      const uuid = el.dataset.gadgetUuid;
      const chartEl = el.querySelector('.circle-chart__canvas');
      if (!chartEl) return;
      const chart = echarts.getInstanceByDom(chartEl);
      if (!chart) return;
      fetchAndRender({ uuid: uuid, chart: chart }, el);
    });
  }

  // CustomerDashboard 共通モジュールへのフック登録
  document.addEventListener('DOMContentLoaded', function () {
    initAllGadgets();
    if (window.CustomerDashboard && typeof window.CustomerDashboard.registerRefreshHook === 'function') {
      window.CustomerDashboard.registerRefreshHook(refreshAll);
    }
  });

}());

// ---------------------------------------------------------------------------
// 登録モーダル イベントバインド（common.js の _bindModalEvents から呼ばれる）
// ---------------------------------------------------------------------------

/**
 * 円グラフ登録モーダルのイベントをバインドする
 * @param {Element} container - モーダルコンテナ要素
 */
function bindCircleChartGadgetRegister(container) {
  var modeBtns = container.querySelectorAll('.circle-chart-register__device-mode-btn');
  if (!modeBtns.length) return;

  var deviceModeInput = container.querySelector('#device_mode');
  var deviceFixedArea = container.querySelector('#device-fixed-area');
  var deviceNameArea  = container.querySelector('#device-name-area');
  var deviceSelect    = container.querySelector('#device-select');

  function applyMode(mode) {
    modeBtns.forEach(function (btn) {
      btn.classList.toggle('circle-chart-register__device-mode-btn--active', btn.dataset.mode === mode);
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
  var checkboxes = container.querySelectorAll('.circle-chart-register__item-checkbox');
  checkboxes.forEach(function (cb) {
    cb.addEventListener('change', function () {
      var checked = container.querySelectorAll('.circle-chart-register__item-checkbox:checked');
      if (checked.length >= 5) {
        checkboxes.forEach(function (c) { if (!c.checked) c.disabled = true; });
      } else {
        checkboxes.forEach(function (c) { c.disabled = false; });
      }
    });
  });
  // 初期状態で5個チェック済みの場合も制限を適用
  var initialChecked = container.querySelectorAll('.circle-chart-register__item-checkbox:checked');
  if (initialChecked.length >= 5) {
    checkboxes.forEach(function (c) { if (!c.checked) c.disabled = true; });
  }

  // 初期状態を適用（hidden inputの現在値に合わせる）
  applyMode(deviceModeInput ? deviceModeInput.value : 'fixed');
}
