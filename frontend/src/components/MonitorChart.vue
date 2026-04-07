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
  console.log('MonitorChart: initChart called, chartInstance:', !!chartInstance, 'chartRef.value:', !!chartRef.value)
  if (chartInstance) {
    // Check if DOM is disconnected
    if (chartInstance.getDom() !== chartRef.value) {
        console.log('MonitorChart: Disposing old chartInstance')
        chartInstance.dispose()
        chartInstance = null
        if (resizeObserver) {
            resizeObserver.disconnect()
            resizeObserver = null
        }
    } else {
        // Resize just in case
        console.log('MonitorChart: Resizing existing chartInstance')
        chartInstance.resize()
        return
    }
  }
  
  if (!chartRef.value) {
    console.warn('MonitorChart: chartRef.value is null, cannot init chart')
    return
  }

  console.log('MonitorChart: Creating new chartInstance')
  chartInstance = echarts.init(chartRef.value)
  console.log('MonitorChart: chartInstance created:', !!chartInstance)
  
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
      data: ['CPU (%)', 'GPU (%)', '帧率 (FPS)', '卡顿 (Jank)', '卡顿率 (Stutter %)', '内存 (MB)', '电池温度 (°C)', '网络下行 (KB/s)', '网络上行 (KB/s)'],
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
      },
      { 
        name: '网络下行 (KB/s)', type: 'line', showSymbol: false,
        endLabel: { show: false, formatter: '{a}', color: 'inherit' },
        labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
        emphasis: { focus: 'series' },
        data: [] 
      },
      { 
        name: '网络上行 (KB/s)', type: 'line', showSymbol: false,
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
      'CPU (%)','GPU (%)','帧率 (FPS)','卡顿 (Jank)','卡顿率 (Stutter %)','内存 (MB)','电池温度 (°C)','网络下行 (KB/s)','网络上行 (KB/s)'
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
  
  console.log('MonitorChart: Chart initialized with legend config')
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
    console.log('MonitorChart: lastMetricUpdate changed, chartInstance:', !!chartInstance, 'isChartActive:', isChartActive.value)
    if (!chartInstance || !isChartActive.value) {
      console.log('MonitorChart: Skipping update - chartInstance or isChartActive is false')
      return
    }
    const dataBuffer = state.dataBuffer
    
    console.log('MonitorChart: dataBuffer sizes:', {
      cpu: dataBuffer.cpu.length,
      gpu: dataBuffer.gpu.length,
      fps: dataBuffer.fps.length,
      jank: dataBuffer.jank.length,
      stutter: dataBuffer.stutter.length,
      memory: dataBuffer.memory.length,
      batteryTemp: dataBuffer.batteryTemp.length,
      network: dataBuffer.network.length
    })
    
    if (dataBuffer.cpu.length === 0) {
      console.log('MonitorChart: No data in buffer, skipping update')
      return
    }
    
    const networkRx = dataBuffer.network.map(item => {
      const [time, value] = item
      return [time, value?.rx || 0]
    })
    
    const networkTx = dataBuffer.network.map(item => {
      const [time, value] = item
      return [time, value?.tx || 0]
    })
    
    console.log('MonitorChart: Updating chart with data, cpu data:', dataBuffer.cpu.slice(-1))
    
    chartInstance.setOption({
      series: [
        { data: dataBuffer.cpu },
        { data: dataBuffer.gpu },
        { data: dataBuffer.fps },
        { data: dataBuffer.jank },
        { data: dataBuffer.stutter },
        { data: dataBuffer.memory },
        { data: dataBuffer.batteryTemp },
        { data: networkRx },
        { data: networkTx }
      ]
    })
    
    // Always force resize after update
    nextTick(() => {
      if (chartInstance) {
        console.log('MonitorChart: Forcing resize after data update')
        chartInstance.resize()
      }
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
        { data: [] }, { data: [] }, { data: [] }, { data: [] },
        { data: [] }, { data: [] }
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
        
        const networkRx = dataBuffer.network.map(item => {
          const [time, value] = item
          return [time, value?.rx || 0]
        })
        
        const networkTx = dataBuffer.network.map(item => {
          const [time, value] = item
          return [time, value?.tx || 0]
        })
        
        chartInstance.setOption({
            series: [
                { data: dataBuffer.cpu },
                { data: dataBuffer.gpu },
                { data: dataBuffer.fps },
                { data: dataBuffer.jank },
                { data: dataBuffer.stutter },
                { data: dataBuffer.memory },
                { data: dataBuffer.batteryTemp },
                { data: networkRx },
                { data: networkTx }
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
  <div class="monitor-container">
    <div class="monitor-header">
      <div class="header-left">
        <h3 class="header-title">实时性能监控</h3>
        <div class="status-bar">
          <span class="status-item" :class="{ connected: state.isConnected }">
            <span class="status-dot"></span>
            {{ state.isConnected ? '连接正常' : '连接断开' }}
          </span>
          <span class="status-divider">|</span>
          <span class="status-item" v-if="selectedSeriesName">
            <span class="status-highlight">{{ selectedSeriesName }}</span>
          </span>
          <span class="status-divider" v-if="selectedSeriesName">|</span>
          <span class="status-item">
            CPU: <strong>{{ state.dataBuffer.cpu.slice(-1)[0]?.[1] ?? '-' }}</strong>%
          </span>
          <span class="status-divider">|</span>
          <span class="status-item">
            FPS: <strong>{{ state.dataBuffer.fps.slice(-1)[0]?.[1] ?? '-' }}</strong>
          </span>
          <span class="status-divider">|</span>
          <span class="status-item">
            Stutter: <strong>{{ state.dataBuffer.stutter.slice(-1)[0]?.[1] ?? '-' }}</strong>%
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button @click="handleAddMarker" :disabled="!active" class="action-btn marker-btn">
          <span class="btn-icon">🚩</span>
          <span class="btn-text">添加标记</span>
        </button>
        <button @click="exportData" :disabled="state.dataBuffer.cpu.length === 0" class="action-btn export-btn">
          <span class="btn-icon">📥</span>
          <span class="btn-text">导出 CSV</span>
        </button>
        <button @click="() => {
          console.log('=== Manual Refresh Test ===')
          console.log('chartInstance:', !!chartInstance)
          console.log('dataBuffer sizes:', {
            cpu: state.dataBuffer.cpu.length,
            gpu: state.dataBuffer.gpu.length,
            fps: state.dataBuffer.fps.length
          })
          if (chartInstance && state.dataBuffer.cpu.length > 0) {
            chartInstance.resize()
            console.log('Manual resize called')
          }
        }" :disabled="state.dataBuffer.cpu.length === 0" class="action-btn" style="background: #e3f2fd; color: #1976d2; border-color: #1976d2;">
          <span class="btn-icon">🔄</span>
          <span class="btn-text">测试刷新</span>
        </button>
        <button @click="clearData" class="action-btn clear-btn">
          <span class="btn-icon">🗑️</span>
          <span class="btn-text">清空数据</span>
        </button>
      </div>
    </div>
    
    <div class="monitor-body">
      <div ref="chartRef" class="chart-area"></div>
      <div class="screenshot-panel" v-if="currentScreenshot">
        <div class="panel-header">
          <span class="panel-title">屏幕截图</span>
        </div>
        <div class="screenshot-content">
          <img :src="currentScreenshot" alt="设备截图" class="screenshot-img" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.monitor-container {
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  position: relative;
  box-sizing: border-box;
  animation: fadeIn var(--transition-slow) ease-out;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-5) var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.header-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger-500);
}

.status-item.connected .status-dot {
  background: var(--success-500);
}

.status-divider {
  color: var(--gray-300);
}

.status-highlight {
  color: var(--primary-600);
  font-weight: var(--font-medium);
}

.status-item strong {
  color: var(--text-primary);
  font-weight: var(--font-semibold);
}

.header-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  cursor: pointer;
  font-size: var(--font-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  transition: all var(--transition-base);
  white-space: nowrap;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
  box-shadow: none;
}

.btn-icon {
  font-size: 14px;
}

.marker-btn {
  background: var(--warning-50);
  color: var(--warning-600);
  border-color: var(--warning-500);
}

.marker-btn:hover:not(:disabled) {
  background: var(--warning-500);
  color: white;
}

.export-btn {
  background: var(--primary-50);
  color: var(--primary-600);
  border-color: var(--primary-500);
}

.export-btn:hover:not(:disabled) {
  background: var(--primary-500);
  color: white;
}

.clear-btn {
  background: var(--danger-50);
  color: var(--danger-600);
  border-color: var(--danger-500);
}

.clear-btn:hover:not(:disabled) {
  background: var(--danger-500);
  color: white;
}

.monitor-body {
  display: flex;
  flex: 1;
  min-height: 0;
  width: 100%;
}

.chart-area {
  flex: 1;
  height: 100%;
  min-height: 400px;
  min-width: 0;
  padding: var(--spacing-4);
}

.screenshot-panel {
  width: 220px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--border-light);
  background: var(--gray-50);
  animation: slideIn var(--transition-base) ease-out;
}

.panel-header {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-light);
}

.panel-title {
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.screenshot-content {
  flex: 1;
  padding: var(--spacing-3);
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.screenshot-img {
  width: 100%;
  height: auto;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

@media (max-width: 1024px) {
  .monitor-header {
    padding: var(--spacing-4);
  }
  
  .screenshot-panel {
    width: 180px;
  }
}

@media (max-width: 768px) {
  .monitor-header {
    padding: var(--spacing-3);
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: flex-end;
  }
  
  .monitor-body {
    flex-direction: column;
  }
  
  .chart-area {
    min-height: 300px;
    padding: var(--spacing-3);
  }
  
  .screenshot-panel {
    width: 100%;
    border-left: none;
    border-top: 1px solid var(--border-light);
    max-height: 200px;
  }
  
  .screenshot-content {
    padding: var(--spacing-2);
  }
}

@media (max-width: 480px) {
  .action-btn {
    padding: var(--spacing-2) var(--spacing-3);
  }
  
  .btn-text {
    display: none;
  }
  
  .btn-icon {
    font-size: 16px;
  }
  
  .status-bar {
    flex-wrap: wrap;
    gap: var(--spacing-1);
  }
  
  .status-divider {
    display: none;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(16px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
