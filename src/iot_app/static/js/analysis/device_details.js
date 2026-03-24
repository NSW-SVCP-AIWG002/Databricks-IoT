// Apache ECharts 初期化
var chartDom = document.getElementById('time-series-chart');
if (chartDom && typeof echarts !== 'undefined') {
  var myChart = echarts.init(chartDom);

  // タイムスタンプリスト
  var timestamps = graphData.map(function(row) { return row.event_timestamp; });

  // yAxisIndex: 0=℃, 1=%, 2=rpm
  var seriesConfig = [
    { name: '外気温度',               field: 'external_temp',                    color: '#000000', type: 'solid',  yAxisIndex: 0 },
    { name: '第1冷凍 設定温度',        field: 'set_temp_freezer_1',               color: '#007DFF', type: 'dashed', yAxisIndex: 0 },
    { name: '第1冷凍 庫内センサー温度', field: 'internal_sensor_temp_freezer_1',   color: '#007DFF', type: 'solid',  yAxisIndex: 0 },
    { name: '第1冷凍 表示温度',        field: 'internal_temp_freezer_1',          color: '#FF8800', type: 'solid',  yAxisIndex: 0 },
    { name: '第1冷凍 DF温度',          field: 'df_temp_freezer_1',                color: '#FF8800', type: 'dashed', yAxisIndex: 0 },
    { name: '第1冷凍 凝縮温度',        field: 'condensing_temp_freezer_1',        color: '#CC65FF', type: 'solid',  yAxisIndex: 0 },
    { name: '第1冷凍 微調整後庫内温度', field: 'adjusted_internal_temp_freezer_1', color: '#005885', type: 'solid',  yAxisIndex: 0 },
    { name: '第2冷凍 設定温度',        field: 'set_temp_freezer_2',               color: '#A7D672', type: 'dashed', yAxisIndex: 0 },
    { name: '第2冷凍 庫内センサー温度', field: 'internal_sensor_temp_freezer_2',   color: '#621C97', type: 'solid',  yAxisIndex: 0 },
    { name: '第2冷凍 表示温度',        field: 'internal_temp_freezer_2',          color: '#621C97', type: 'dashed', yAxisIndex: 0 },
    { name: '第2冷凍 DF温度',          field: 'df_temp_freezer_2',                color: '#00A02F', type: 'solid',  yAxisIndex: 0 },
    { name: '第2冷凍 凝縮温度',        field: 'condensing_temp_freezer_2',        color: '#00A02F', type: 'dashed', yAxisIndex: 0 },
    { name: '第2冷凍 微調整後庫内温度', field: 'adjusted_internal_temp_freezer_2', color: '#009EEC', type: 'solid',  yAxisIndex: 0 },
    { name: '第1冷凍 圧縮機',          field: 'compressor_freezer_1',             color: '#CC65FF', type: 'dashed', yAxisIndex: 2 },
    { name: '第2冷凍 圧縮機',          field: 'compressor_freezer_2',             color: '#9ED262', type: 'dashed', yAxisIndex: 2 },
    { name: '第1ファンモータ',          field: 'fan_motor_1',                     color: '#000000', type: 'dashed', yAxisIndex: 2 },
    { name: '第2ファンモータ',          field: 'fan_motor_2',                     color: '#767676', type: 'solid',  yAxisIndex: 2 },
    { name: '第3ファンモータ',          field: 'fan_motor_3',                     color: '#767676', type: 'dashed', yAxisIndex: 2 },
    { name: '第4ファンモータ',          field: 'fan_motor_4',                     color: '#D6D6D6', type: 'solid',  yAxisIndex: 2 },
    { name: '第5ファンモータ',          field: 'fan_motor_5',                     color: '#D6D6D6', type: 'dashed', yAxisIndex: 2 },
    { name: '防露ヒータ出力(1)',        field: 'defrost_heater_output_1',          color: '#005280', type: 'dashed', yAxisIndex: 1 },
    { name: '防露ヒータ出力(2)',        field: 'defrost_heater_output_2',          color: '#009CEC', type: 'dashed', yAxisIndex: 1 },
  ];

  var series = seriesConfig.map(function(cfg) {
    return {
      name: cfg.name,
      type: 'line',
      yAxisIndex: cfg.yAxisIndex,
      data: graphData.map(function(row) { return row[cfg.field]; }),
      lineStyle: { color: cfg.color, type: cfg.type },
      itemStyle: { color: cfg.color },
      smooth: false,
      showSymbol: false,
    };
  });

  var option = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLabel: { formatter: function(val) { return val ? val.substring(0, 16) : ''; } }
    },
    yAxis: [
      { type: 'value', name: '℃', position: 'left', nameTextStyle: { align: 'right' } },
      { type: 'value', name: '%',   position: 'right', nameTextStyle: { align: 'left' }, offset: 0 },
      { type: 'value', name: 'rpm', position: 'right', nameTextStyle: { align: 'left' }, offset: 60 },
    ],
    grid: { right: 100 },
    dataZoom: [{ type: 'inside' }, { type: 'slider' }],
    series: series,
    legend: { show: false }
  };

  myChart.setOption(option);

  // 最終更新時刻
  var now = new Date();
  var pad = function(n) { return n < 10 ? '0' + n : n; };
  document.getElementById('graph-updated-time').textContent =
    '最終更新時刻: ' + now.getFullYear() + '/' + pad(now.getMonth()+1) + '/' + pad(now.getDate()) +
    ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());

  // 凡例チェックボックス
  var seriesCbs = document.querySelectorAll('.legend__series-cb');
  var selectAll = document.getElementById('select-all');

  seriesCbs.forEach(function(cb) {
    cb.addEventListener('change', function() {
      myChart.dispatchAction({
        type: cb.checked ? 'legendSelect' : 'legendUnSelect',
        name: cb.value
      });
      selectAll.checked = Array.from(seriesCbs).every(function(c) { return c.checked; });
    });
  });

  selectAll.addEventListener('change', function() {
    seriesCbs.forEach(function(cb) {
      cb.checked = selectAll.checked;
      myChart.dispatchAction({
        type: selectAll.checked ? 'legendSelect' : 'legendUnSelect',
        name: cb.value
      });
    });
  });

  // 自動更新（60秒ごと）
  var autoUpdateCb = document.getElementById('auto_update');
  var autoUpdateTimer = null;
  if (autoUpdateCb) {
    autoUpdateCb.addEventListener('change', function() {
      if (autoUpdateCb.checked) {
        autoUpdateTimer = setInterval(function() { location.reload(); }, 60000);
      } else {
        if (autoUpdateTimer) clearInterval(autoUpdateTimer);
      }
    });
  }
}