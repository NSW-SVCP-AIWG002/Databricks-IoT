/**
 * 業種別ダッシュボード（冷蔵冷凍庫）JavaScript
 *
 * 機能:
 * - タスク6-3: 時系列グラフ初期化（Apache ECharts）
 * - タスク6-4: 自動更新チェックボックス連動
 * - タスク6-5: 店舗名ドロップダウン検索
 * - タスク6-6: センサー情報欄表示切り替え
 *
 * 参照:
 * - ui-specification.md「(12)時系列グラフ」「(13)凡例」「(10.4)自動更新」
 */

/* global echarts */

const IndustryDashboard = (() => {

  // --------------------------------------------------------------------------
  // グラフ系列定義（ui-specification.md「12-1 時系列グラフ」の色・線種に準拠）
  // --------------------------------------------------------------------------
  const SERIES_DEFS = [
    { key: 'external_temp',                    name: '外気温度',                  color: '#000000', lineStyle: 'solid',  yAxis: 0 },
    { key: 'set_temp_freezer_1',               name: '第1冷凍 設定温度',           color: '#007DFF', lineStyle: 'dashed', yAxis: 0 },
    { key: 'internal_sensor_temp_freezer_1',   name: '第1冷凍 庫内センサー温度',   color: '#007DFF', lineStyle: 'solid',  yAxis: 0 },
    { key: 'internal_temp_freezer_1',          name: '第1冷凍 庫内温度',           color: '#FF8800', lineStyle: 'solid',  yAxis: 0 },
    { key: 'df_temp_freezer_1',                name: '第1冷凍 DF温度',             color: '#FF8800', lineStyle: 'dashed', yAxis: 0 },
    { key: 'condensing_temp_freezer_1',        name: '第1冷凍 凝縮温度',           color: '#CC65FF', lineStyle: 'solid',  yAxis: 0 },
    { key: 'adjusted_internal_temp_freezer_1', name: '第1冷凍 微調整後庫内温度',   color: '#005885', lineStyle: 'solid',  yAxis: 0 },
    { key: 'set_temp_freezer_2',               name: '第2冷凍 設定温度',           color: '#A7D672', lineStyle: 'dashed', yAxis: 0 },
    { key: 'internal_sensor_temp_freezer_2',   name: '第2冷凍 庫内センサー温度',   color: '#621C97', lineStyle: 'solid',  yAxis: 0 },
    { key: 'internal_temp_freezer_2',          name: '第2冷凍 庫内温度',           color: '#621C97', lineStyle: 'dashed', yAxis: 0 },
    { key: 'df_temp_freezer_2',                name: '第2冷凍 DF温度',             color: '#00A02F', lineStyle: 'solid',  yAxis: 0 },
    { key: 'condensing_temp_freezer_2',        name: '第2冷凍 凝縮温度',           color: '#00A02F', lineStyle: 'dashed', yAxis: 0 },
    { key: 'adjusted_internal_temp_freezer_2', name: '第2冷凍 微調整後庫内温度',   color: '#009EEC', lineStyle: 'solid',  yAxis: 0 },
    { key: 'compressor_freezer_1',             name: '第1冷凍 圧縮機',             color: '#CC65FF', lineStyle: 'dashed', yAxis: 1 },
    { key: 'compressor_freezer_2',             name: '第2冷凍 圧縮機',             color: '#9ED262', lineStyle: 'dashed', yAxis: 1 },
    { key: 'fan_motor_1',                      name: '第1ファンモータ',             color: '#000000', lineStyle: 'dashed', yAxis: 1 },
    { key: 'fan_motor_2',                      name: '第2ファンモータ',             color: '#767676', lineStyle: 'solid',  yAxis: 1 },
    { key: 'fan_motor_3',                      name: '第3ファンモータ',             color: '#767676', lineStyle: 'dashed', yAxis: 1 },
    { key: 'fan_motor_4',                      name: '第4ファンモータ',             color: '#D6D6D6', lineStyle: 'solid',  yAxis: 1 },
    { key: 'fan_motor_5',                      name: '第5ファンモータ',             color: '#D6D6D6', lineStyle: 'dashed', yAxis: 1 },
    { key: 'defrost_heater_output_1',          name: '防露ヒータ出力(1)',           color: '#005280', lineStyle: 'dashed', yAxis: 2 },
    { key: 'defrost_heater_output_2',          name: '防露ヒータ出力(2)',           color: '#009CEC', lineStyle: 'dashed', yAxis: 2 },
  ];

  let _chartInstance = null;
  let _autoUpdateTimer = null;

  // --------------------------------------------------------------------------
  // タスク6-3: 時系列グラフ初期化
  // --------------------------------------------------------------------------

  /**
   * EChartsグラフを初期化する
   *
   * @param {string} containerId - グラフ描画先要素のID
   * @param {Array}  rawData     - サーバーから受け取ったセンサーデータ配列
   * @param {string} updatedTimeId - 最終更新時刻表示要素のID
   */
  function initGraph(containerId, rawData, updatedTimeId) {
    const el = document.getElementById(containerId);
    if (!el || typeof echarts === 'undefined') return;

    _chartInstance = echarts.init(el);
    _renderGraph(rawData, updatedTimeId);

    // レスポンシブ対応
    window.addEventListener('resize', () => {
      _chartInstance && _chartInstance.resize();
    });
  }

  function _renderGraph(rawData, updatedTimeId) {
    if (!_chartInstance) return;

    const timestamps = rawData.map(row => row.event_timestamp);

    const series = SERIES_DEFS.map(def => ({
      name: def.name,
      type: 'line',
      yAxisIndex: def.yAxis,
      data: rawData.map(row => row[def.key] !== null ? row[def.key] : null),
      itemStyle: { color: def.color },
      lineStyle: {
        color: def.color,
        type: def.lineStyle,
        width: 1.5,
      },
      symbol: 'none',
      connectNulls: false,
    }));

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: { show: false },
      grid: { left: 60, right: 60, top: 20, bottom: 60, containLabel: false },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0 },
        { type: 'slider',  xAxisIndex: 0, bottom: 10 },
        { type: 'inside', yAxisIndex: [0, 1, 2] },
      ],
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: {
          formatter: val => val ? val.slice(0, 16).replace('T', '\n') : '',
          fontSize: 10,
        },
      },
      yAxis: [
        { type: 'value', axisLabel: { formatter: '{value}℃', fontSize: 10 } },
        { type: 'value', axisLabel: { formatter: '{value}rpm', fontSize: 10 } },
        { type: 'value', axisLabel: { formatter: '{value}%', fontSize: 10 } },
      ],
      series,
    };

    _chartInstance.setOption(option);

    // 最終更新時刻
    const el = document.getElementById(updatedTimeId);
    if (el) {
      el.textContent = _formatDateTime(new Date());
    }
  }

  function _formatDateTime(date) {
    const pad = n => String(n).padStart(2, '0');
    return `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())} `
      + `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  }

  // --------------------------------------------------------------------------
  // タスク6-4: 自動更新
  // --------------------------------------------------------------------------

  /**
   * 自動更新チェックボックスの挙動を初期化する
   *
   * @param {string} checkboxId       - 自動更新チェックボックスのID
   * @param {string} submitBtnId      - 表示期間変更ボタンのID
   * @param {string} startInputId     - 開始日時入力のID
   * @param {string} endInputId       - 終了日時入力のID
   * @param {number} intervalMs       - 自動更新間隔（ミリ秒）
   */
  function initAutoUpdate(checkboxId, submitBtnId, startInputId, endInputId, intervalMs) {
    const checkbox = document.getElementById(checkboxId);
    const submitBtn = document.getElementById(submitBtnId);
    const startInput = document.getElementById(startInputId);
    const endInput = document.getElementById(endInputId);

    if (!checkbox) return;

    checkbox.addEventListener('change', function () {
      if (this.checked) {
        _enableAutoUpdate(submitBtn, startInput, endInput, intervalMs);
      } else {
        _disableAutoUpdate(submitBtn, startInput, endInput);
      }
    });
  }

  function _enableAutoUpdate(submitBtn, startInput, endInput, intervalMs) {
    if (submitBtn) submitBtn.disabled = true;
    if (startInput) startInput.disabled = true;
    if (endInput) endInput.disabled = true;

    _autoUpdateTimer = setInterval(() => {
      // 表示期間を直近24時間に更新してフォーム送信
      const now = new Date();
      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      if (startInput) startInput.value = _toDatetimeLocal(oneDayAgo);
      if (endInput) endInput.value = _toDatetimeLocal(now);
      if (submitBtn) submitBtn.form && submitBtn.form.submit();
    }, intervalMs);
  }

  function _disableAutoUpdate(submitBtn, startInput, endInput) {
    clearInterval(_autoUpdateTimer);
    _autoUpdateTimer = null;
    if (submitBtn) submitBtn.disabled = false;
    if (startInput) startInput.disabled = false;
    if (endInput) endInput.disabled = false;
  }

  function _toDatetimeLocal(date) {
    const pad = n => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
      + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }

  // --------------------------------------------------------------------------
  // タスク6-5: 店舗名ドロップダウン検索
  //   input[name="organization_name"] に対してインクリメンタルサーチを提供する。
  //   候補一覧は既存の #deviceTableBody から取得する（クライアントサイドフィルタ）。
  // --------------------------------------------------------------------------

  /**
   * 店舗名入力欄のドロップダウン検索を初期化する
   *
   * @param {string} inputId       - 店舗名入力のID
   * @param {string} tableBodyId   - デバイス一覧のtbody ID（候補取得元）
   */
  function initOrganizationSearch(inputId, tableBodyId) {
    const input = document.getElementById(inputId);
    const tableBody = document.getElementById(tableBodyId);
    if (!input || !tableBody) return;

    // 既存の組織名を収集してユニーク化
    const orgSet = new Set();
    tableBody.querySelectorAll('tr[data-device-uuid]').forEach(row => {
      const cell = row.querySelector('td');
      if (cell && cell.textContent.trim()) {
        orgSet.add(cell.textContent.trim());
      }
    });

    const candidates = Array.from(orgSet);
    const dropdown = _createDropdown(input, candidates);

    input.addEventListener('input', function () {
      const query = this.value.toLowerCase();
      const filtered = candidates.filter(c => c.toLowerCase().includes(query));
      _updateDropdown(dropdown, filtered, input);
    });

    input.addEventListener('focus', function () {
      const query = this.value.toLowerCase();
      const filtered = candidates.filter(c => c.toLowerCase().includes(query));
      _updateDropdown(dropdown, filtered, input);
    });

    document.addEventListener('click', function (e) {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = 'none';
      }
    });
  }

  function _createDropdown(input, candidates) {
    const wrapper = input.parentElement;
    wrapper.style.position = 'relative';
    const ul = document.createElement('ul');
    ul.className = 'org-dropdown';
    ul.style.cssText = [
      'position:absolute', 'top:100%', 'left:0', 'right:0',
      'background:#fff', 'border:1px solid #dee2e6', 'border-radius:4px',
      'max-height:200px', 'overflow-y:auto', 'z-index:1000', 'display:none',
      'list-style:none', 'margin:0', 'padding:0',
    ].join(';');
    wrapper.appendChild(ul);
    return ul;
  }

  function _updateDropdown(dropdown, items, input) {
    dropdown.innerHTML = '';
    if (!items.length) { dropdown.style.display = 'none'; return; }

    items.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      li.style.cssText = 'padding:6px 12px;cursor:pointer;font-size:13px;';
      li.addEventListener('mouseenter', () => { li.style.background = '#f0f4ff'; });
      li.addEventListener('mouseleave', () => { li.style.background = ''; });
      li.addEventListener('mousedown', (e) => {
        e.preventDefault();
        input.value = item;
        dropdown.style.display = 'none';
      });
      dropdown.appendChild(li);
    });

    dropdown.style.display = 'block';
  }

  // --------------------------------------------------------------------------
  // タスク6-6: 凡例の初期化（チェックボックス → グラフ系列表示切り替え）
  // --------------------------------------------------------------------------

  /**
   * 凡例チェックボックスを動的生成し、グラフ系列と連動させる
   *
   * @param {string} legendContainerId - 凡例項目を追加するコンテナのID
   * @param {string} selectAllId       - 全選択チェックボックスのID
   * @param {string} chartContainerId  - グラフ要素のID
   */
  function initLegend(legendContainerId, selectAllId, chartContainerId) {
    const container = document.getElementById(legendContainerId);
    const selectAll = document.getElementById(selectAllId);
    if (!container || !_chartInstance) return;

    const checkboxes = [];

    SERIES_DEFS.forEach((def, idx) => {
      const label = document.createElement('label');
      label.className = 'graph-legend__item';

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = true;
      cb.dataset.seriesIndex = idx;

      // 線の色見本
      const colorBar = document.createElement('span');
      colorBar.className = 'graph-legend__color';
      colorBar.style.cssText = [
        `background:${def.color}`,
        def.lineStyle === 'dashed'
          ? 'background:repeating-linear-gradient(90deg,'
            + `${def.color} 0,${def.color} 4px,transparent 4px,transparent 8px)`
          : '',
      ].filter(Boolean).join(';');

      const text = document.createTextNode(def.name);

      label.appendChild(cb);
      label.appendChild(colorBar);
      label.appendChild(text);
      container.appendChild(label);
      checkboxes.push(cb);

      cb.addEventListener('change', () => {
        _toggleSeries(idx, cb.checked);
        selectAll.checked = checkboxes.every(c => c.checked);
        selectAll.indeterminate = !selectAll.checked && checkboxes.some(c => c.checked);
      });
    });

    // 全選択/全解除
    if (selectAll) {
      selectAll.addEventListener('change', function () {
        checkboxes.forEach((cb, idx) => {
          cb.checked = this.checked;
          _toggleSeries(idx, this.checked);
        });
      });
    }
  }

  function _toggleSeries(seriesIndex, visible) {
    if (!_chartInstance) return;
    _chartInstance.dispatchAction({
      type: visible ? 'legendSelect' : 'legendUnSelect',
      name: SERIES_DEFS[seriesIndex].name,
    });
  }

  // --------------------------------------------------------------------------
  // Public API
  // --------------------------------------------------------------------------
  return { initGraph, initLegend, initAutoUpdate, initOrganizationSearch };

})();
