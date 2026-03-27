<script setup>
import { ref, onMounted, onUnmounted, onActivated, onDeactivated, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { useMonitorStore } from '../composables/useMonitorStore'

const props = defineProps({
  serial: String,
  active: Boolean,
  target: String
})

const chartRef = ref(null)
let chartInstance = null
const isChartActive = ref(true) // Track visibility
const { state, connectWs, disconnectWs, clearData, addMarker } = useMonitorStore()
const markerLabel = ref('')
const selectedSeriesName = ref('')

const handleAddMarker = () => {
  if (!props.active) {
    alert('请先开始测试')
    return
  }
  const label = prompt('请输入标记名称', markerLabel.value)
  if (label !== null) {
      addMarker(label || 'Marker')
      markerLabel.value = '' // Reset
  }
}

// Use computed for screenshot to stay reactive
const currentScreenshot = computed(() => state.currentScreenshot)

const exportData = () => {
  const dataBuffer = state.dataBuffer
  const headers = ['时间戳', 'CPU(%)', 'GPU(%)', '帧率(FPS)', '卡顿(Jank)', '卡顿率(Stutter%)', '内存(MB)', '电池温度(C)', '网络下行(KB)', '网络上行(KB)']
  const rows = [headers.join(',')]
  
  const formatTime = (date) => {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    const h = String(date.getHours()).padStart(2, '0')
    const min = String(date.getMinutes()).padStart(2, '0')
    const s = String(date.getSeconds()).padStart(2, '0')
    return `${y}${m}${d} ${h}:${min}:${s}`
  }

  const len = dataBuffer.cpu.length
  for (let i = 0; i < len; i++) {
    const time = formatTime(dataBuffer.cpu[i][0])
    const cpu = dataBuffer.cpu[i][1]
    const gpu = dataBuffer.gpu[i] ? dataBuffer.gpu[i][1] : 0
    const fps = dataBuffer.fps[i] ? dataBuffer.fps[i][1] : 0
    const mem = dataBuffer.memory[i] ? dataBuffer.memory[i][1] : 0
    
    // New metrics
    const jank = dataBuffer.jank[i] ? dataBuffer.jank[i][1] : 0
    const stutter = dataBuffer.stutter[i] ? dataBuffer.stutter[i][1] : 0
    const batt = dataBuffer.batteryTemp[i] ? dataBuffer.batteryTemp[i][1] : 0
    
    // Network is cumulative in buffer
    const net = dataBuffer.network[i] ? dataBuffer.network[i][1] : {rx: 0, tx: 0}
    const rx = net.rx || 0
    const tx = net.tx || 0
    
    // Find markers in this second (approx)
    // CSV doesn't support random markers well unless we add a separate column
    // Or we just append them to the last column
    const marker = state.markers.find(m => Math.abs(m.time - dataBuffer.cpu[i][0]) < 1000)
    const markerText = marker ? marker.label : ''

    rows.push(`${time},${cpu},${gpu},${fps},${jank},${stutter},${mem},${batt},${rx},${tx},${markerText}`) 
  }
  
  // Update header
  rows[0] += ',标记(Label)'
  
  // Add BOM for Excel/WPS compatibility
  const blob = new Blob(['\uFEFF' + rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  
  // Generate filename with YYYYMMDD_HHMMSS format
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  const fileTimestamp = `${y}${m}${d}_${h}${min}${s}`
  
  // Include package name in filename if available
  const pkgName = props.target || 'unknown'
  a.download = `perf_data_${pkgName}_${props.serial}_${fileTimestamp}.csv`
  a.click()
}

// 初始化图表配置
let resizeObserver = null

const initChart = () => {
  if (chartInstance) {
    // Check if DOM is disconnected
    if (chartInstance.getDom() !== chartRef.value) {
        chartInstance.dispose()
        chartInstance = null
        if (resizeObserver) {
            resizeObserver.disconnect()
            resizeObserver = null
        }
    } else {
        // Resize just in case
        chartInstance.resize()
        return
    }
  }
  
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  
  // Setup ResizeObserver for robust resizing
  resizeObserver = new ResizeObserver(() => {
      chartInstance?.resize()
  })
  resizeObserver.observe(chartRef.value)
  
  const option = {
    tooltip: { 
      trigger: 'axis',
      order: 'valueDesc', // Sort tooltip by value descending
      confine: true, // Keep tooltip within chart area
      backgroundColor: 'rgba(255, 255, 255, 0.9)', // Semi-transparent
      extraCssText: 'box-shadow: 0 0 8px rgba(0, 0, 0, 0.2); border-radius: 4px;',
      position: function (pos, params, dom, rect, size) {
          // Strictly put in opposite corner to avoid occlusion
          const isRight = pos[0] > size.viewSize[0] / 2;
          return {
              top: 10,
              left: isRight ? 10 : null,
              right: isRight ? null : 120 // Avoid covering the right axis labels/legend
          };
      },
      formatter: (params) => {
        if (params && params.length > 0) {
           const time = params[0].axisValue
           updateScreenshot(time)
           
           let res = new Date(time).toLocaleTimeString() + '<br/>'

           // Add markers info if any match this time
           const timeVal = new Date(time).getTime()
           const marker = state.markers.find(m => Math.abs(m.time.getTime() - timeVal) < 2000)
           if (marker) {
               res += `<span style="color:red;font-weight:bold;display:block;margin-bottom:4px;">🚩 ${marker.label}</span>`
           }
           
           // Sort params by value descending for better visibility
           const sortedParams = [...params].sort((a, b) => (b.value[1] || 0) - (a.value[1] || 0))

           // Add Memory Detail if hovering memory
           const dataIndex = params[0].dataIndex
           const memDetail = state.dataBuffer.memoryDetail[dataIndex]
           
           sortedParams.forEach(item => {
             const value = item.value[1] !== undefined ? item.value[1] : '-'
             // Bold the value
             res += `${item.marker} ${item.seriesName}: <b>${value}</b><br/>`
             
             // If this is the memory series and we have detail
             if (item.seriesName.includes('内存') && memDetail && Object.keys(memDetail).length > 0) {
                 res += `<div style="font-size:10px;color:#aaa;padding-left:15px;margin-bottom:4px;">`
                 if (memDetail.java) res += `Java: ${memDetail.java.toFixed(1)} MB<br/>`
                 if (memDetail.native) res += `Native: ${memDetail.native.toFixed(1)} MB<br/>`
                 if (memDetail.graphics) res += `Graphics: ${memDetail.graphics.toFixed(1)} MB<br/>`
                 if (memDetail.code) res += `Code: ${memDetail.code.toFixed(1)} MB<br/>`
                 if (memDetail.stack) res += `Stack: ${memDetail.stack.toFixed(1)} MB<br/>`
                 res += `</div>`
             }
           })
           return res
        }
        return ''
      }
    },
    legend: { 
      data: ['CPU (%)', 'GPU (%)', '帧率 (FPS)', '卡顿 (Jank)', '卡顿率 (Stutter %)', '内存 (MB)', '电池温度 (°C)'],
      bottom: 0,
      top: 'auto',
      type: 'scroll' 
    },
    grid: { 
      left: '3%', 
      right: '120px',  // Increase right margin for endLabels
      bottom: '15%', 
      top: '12%',    
      containLabel: true 
    },
    dataZoom: [
      {
        type: 'slider',
        show: true,
        xAxisIndex: [0],
        bottom: 5,
        start: 0,
        end: 100
      },
      {
        type: 'inside',
        xAxisIndex: [0],
        start: 0,
        end: 100
      }
    ],
    xAxis: { 
      type: 'time', 
      splitLine: { show: false },
      axisLabel: {
        hideOverlap: true,
        formatter: (value) => {
          const d = new Date(value)
          const h = String(d.getHours()).padStart(2, '0')
          const m = String(d.getMinutes()).padStart(2, '0')
          return `${h}:${m}`
        },
        margin: 12
      }
    },
    yAxis: [
      { type: 'value', name: '使用率 / 帧率', min: 0, nameGap: 15 }, 
      { type: 'value', name: '内存 (MB)', position: 'right', nameGap: 15 }, 
    ],
    series: [
      { 
        name: 'CPU (%)', type: 'line', showSymbol: false, 
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [],
        markLine: {
          symbol: ['none', 'none'],
          label: { show: true, position: 'end', formatter: '{b}' },
          lineStyle: { color: 'red', type: 'dashed' },
          data: []
        }
      },
      { 
        name: 'GPU (%)', type: 'line', showSymbol: false,
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [] 
      },
      { 
        name: '帧率 (FPS)', type: 'line', showSymbol: false,
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [] 
      },
      { 
        name: '卡顿 (Jank)', type: 'bar', stack: 'jank', showSymbol: false,
        emphasis: { focus: 'series' },
        data: [] 
      },
      { 
        name: '卡顿率 (Stutter %)', type: 'line', showSymbol: false,
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [] 
      },
      { 
        name: '内存 (MB)', type: 'line', yAxisIndex: 1, showSymbol: false,
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [] 
      },
      { 
        name: '电池温度 (°C)', type: 'line', showSymbol: false,
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [] 
      }
    ]
  }
  chartInstance.setOption(option)

  const setActiveSeriesLabels = (activeName = '') => {
    const names = [
      'CPU (%)','GPU (%)','帧率 (FPS)','卡顿 (Jank)','卡顿率 (Stutter %)','内存 (MB)','电池温度 (°C)'
    ]
    chartInstance.setOption({
      series: names.map(n => {
        if (n === '卡顿 (Jank)') {
          return { name: n } 
        }
        return { 
          name: n,
          endLabel: { show: activeName && n === activeName }
        }
      })
    })
  }

  // Click handler to select series
  chartInstance.on('click', (params) => {
    if (params.componentType === 'series') {
        selectedSeriesName.value = params.seriesName
        setActiveSeriesLabels(params.seriesName)
        // Optional: Trigger highlight action
        chartInstance.dispatchAction({
            type: 'highlight',
            seriesName: params.seriesName
        })
        
        // Downplay others? ECharts highlight works cumulatively or exclusively depending on impl.
        // For simplicity, we just rely on displaying the name in UI.
    }
  })

  chartInstance.on('mouseover', (params) => {
    if (params.componentType === 'series') {
      setActiveSeriesLabels(params.seriesName)
    }
  })
  chartInstance.on('mouseout', () => {
    setActiveSeriesLabels('')
  })

  // Clear selection when clicking empty area
  chartInstance.getZr().on('click', (params) => {
    if (!params.target) {
        selectedSeriesName.value = ''
        chartInstance.dispatchAction({
            type: 'downplay'
        })
        setActiveSeriesLabels('')
    }
  })
}

// Watch markers to update chart immediately
watch(() => state.markers.length, () => {
    if (chartInstance) {
        const markLineData = state.markers.map(m => ({
            xAxis: m.time,
            label: { formatter: m.label },
            lineStyle: { color: 'red', type: 'dashed' }
        }))
        
        chartInstance.setOption({
            series: [{
                name: 'CPU (%)',
                markLine: {
                    symbol: ['none', 'none'],
                    data: markLineData
                }
            }]
        })
    }
})

const updateScreenshot = (time) => {
    const screenshotBuffer = state.screenshotBuffer
    if (!screenshotBuffer.length) return
    
    // Find closest screenshot
    let closest = screenshotBuffer[0]
    let minDiff = Math.abs(time - closest.time)
    
    for (let i = 1; i < screenshotBuffer.length; i++) {
        const diff = Math.abs(time - screenshotBuffer[i].time)
        if (diff < minDiff) {
            minDiff = diff
            closest = screenshotBuffer[i]
        }
    }
    
    if (minDiff < 3000) { // Only show if within 3 seconds
        state.currentScreenshot = closest.url
    }
}

// Watch lastMetricUpdate to refresh chart
watch(() => state.lastMetricUpdate, () => {
    if (!chartInstance || !isChartActive.value) return
    const dataBuffer = state.dataBuffer
    
    chartInstance.setOption({
      series: [
        { data: dataBuffer.cpu },
        { data: dataBuffer.gpu },
        { data: dataBuffer.fps },
        { data: dataBuffer.jank },
        { data: dataBuffer.stutter },
        { data: dataBuffer.memory },
        { data: dataBuffer.batteryTemp }
      ]
    })
})

watch(() => props.active, (newVal) => {
  if (newVal) {
    clearData() // Clear previous data to avoid mixing sessions
    connectWs(props.serial, props.target)
  } else {
    disconnectWs()
  }
})

watch(() => props.serial, () => {
  if (props.active) {
    disconnectWs()
    connectWs(props.serial, props.target)
  }
  clearData()
  if (chartInstance) {
    chartInstance.setOption({ 
      series: [
        { data: [] }, { data: [] }, { data: [] }, 
        { data: [] }, { data: [] }, { data: [] }, { data: [] }
      ] 
    })
  }
})

onMounted(() => {
  isChartActive.value = true
  nextTick(() => {
    initChart()
    window.addEventListener('resize', () => chartInstance?.resize())
  })
})

onActivated(() => {
  isChartActive.value = true
  nextTick(() => {
    initChart()
    chartInstance?.resize()
    // Force update chart with latest buffer
    if (chartInstance) {
        const dataBuffer = state.dataBuffer
        chartInstance.setOption({
            series: [
                { data: dataBuffer.cpu },
                { data: dataBuffer.gpu },
                { data: dataBuffer.fps },
                { data: dataBuffer.jank },
                { data: dataBuffer.stutter },
                { data: dataBuffer.memory },
                { data: dataBuffer.batteryTemp }
            ]
        })
    }
  })
})

onDeactivated(() => {
  isChartActive.value = false
})

onUnmounted(() => {
  // Don't disconnect here because LogViewer might need the connection
  // disconnectWs() 
  // Actually, if we switch tabs, we want connection to stay. 
  // App.vue keeps <keep-alive> so unmounted won't fire on tab switch.
  // But if user navigates away? Vue 3 unmounted.
  // Since we use keep-alive in App.vue, this component stays mounted.
  chartInstance?.dispose()
  if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
  }
})
</script>

<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>性能监控</h3>
      <div style="font-size: 12px; color: #666; margin-left: 10px;">
        <span v-if="state.isConnected" style="color: green;">● 连接正常</span>
        <span v-else style="color: red;">● 连接断开</span> |
        <span v-if="selectedSeriesName" style="color: #409eff; font-weight: bold;">👉 {{ selectedSeriesName }} |</span>
        CPU: {{ state.dataBuffer.cpu.slice(-1)[0]?.[1] ?? '-' }}% |
        FPS: {{ state.dataBuffer.fps.slice(-1)[0]?.[1] ?? '-' }} |
        Stutter: {{ state.dataBuffer.stutter.slice(-1)[0]?.[1] ?? '-' }}% |
        Update: {{ new Date(state.lastMetricUpdate).toLocaleTimeString() }}
      </div>
      <div class="btn-group">
        <button @click="handleAddMarker" :disabled="!active" class="marker-btn">🚩 添加标记</button>
        <button @click="exportData" :disabled="state.dataBuffer.cpu.length === 0" class="export-btn">导出 CSV</button>
        <button @click="clearData" class="clear-btn">清空数据</button>
      </div>
    </div>
    <div class="monitor-layout">
      <div ref="chartRef" class="chart"></div>
      <div class="screenshot-panel" v-if="currentScreenshot">
        <h4>屏幕截图</h4>
        <img :src="currentScreenshot" alt="设备截图" class="screenshot-img" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  position: relative;
  box-sizing: border-box;
  animation: fadeIn 0.6s ease-out;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--border-light);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.btn-group {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.btn-group button {
  padding: var(--spacing-xs) var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  cursor: pointer;
  font-size: var(--font-xs);
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-group button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.btn-group button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.marker-btn {
  background: linear-gradient(135deg, #ffecd2, #fcb69f) !important;
  color: #c05621 !important;
  border-color: #fbd38d !important;
}

.marker-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #fcb69f, #ff8a5b) !important;
}

.clear-btn {
  background: linear-gradient(135deg, #fed7d7, #feb2b2) !important;
  color: #c53030 !important;
  border-color: #fc8181 !important;
}

.clear-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #feb2b2, #fc8181) !important;
}

.export-btn {
  background: linear-gradient(135deg, #bee3f8, #90cdf4) !important;
  color: #2b6cb0 !important;
  border-color: #63b3ed !important;
}

.export-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #90cdf4, #63b3ed) !important;
}

.monitor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  width: 100%;
  gap: var(--spacing-md);
}

.chart {
  flex: 1;
  height: 100%;
  min-height: 400px;
  min-width: 0;
}

.screenshot-panel {
  width: 200px;
  display: flex;
  flex-direction: column;
  border-left: 2px solid var(--border-light);
  padding-left: var(--spacing-md);
  animation: slideIn 0.3s ease-out;
}

.screenshot-panel h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--border-light);
}

.screenshot-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.screenshot-item {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.screenshot-item:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-md);
}

.screenshot-item img {
  width: 100%;
  height: auto;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
}

.screenshot-time {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  color: white;
  font-size: var(--font-xs);
  padding: var(--spacing-sm);
  text-align: center;
}

@media (max-width: 1024px) {
  .chart-container {
    padding: var(--spacing-md);
  }
  
  .screenshot-panel {
    width: 150px;
  }
}

@media (max-width: 768px) {
  .chart-container {
    padding: var(--spacing-sm);
  }
  
  .chart-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .btn-group {
    justify-content: center;
  }
  
  .monitor-layout {
    flex-direction: column;
  }
  
  .screenshot-panel {
    width: 100%;
    border-left: none;
    border-top: 2px solid var(--border-light);
    padding-left: 0;
    padding-top: var(--spacing-md);
    max-height: 200px;
  }
  
  .screenshot-list {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
  }
  
  .screenshot-item {
    min-width: 120px;
  }
}

@media (max-width: 480px) {
  .btn-group button {
    padding: 4px var(--spacing-sm);
    font-size: 11px;
  }
  
  .screenshot-panel {
    max-height: 150px;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
