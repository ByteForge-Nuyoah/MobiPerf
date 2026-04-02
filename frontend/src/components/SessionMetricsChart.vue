<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>详细指标图表</h3>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>

      <div v-if="loading" class="modal-body loading">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="modal-body error">
        ❌ {{ error }}
      </div>

      <div v-else class="modal-body">
        <div class="chart-controls">
          <div class="control-group">
            <label>显示指标:</label>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.cpu" />
                <span>CPU(%)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.gpu" />
                <span>GPU(%)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.fps" />
                <span>帧率(FPS)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.jank" />
                <span>卡顿(Jank)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.stutter" />
                <span>卡顿率(Stutter%)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.memory" />
                <span>内存(MB)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.temp" />
                <span>电池温度(℃)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.networkRx" />
                <span>网络下行(KB/s)</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="visibleSeries.networkTx" />
                <span>网络上行(KB/s)</span>
              </label>
            </div>
          </div>
        </div>

        <div class="chart-container" ref="chartContainer">
          <div class="chart" ref="chartRef"></div>
        </div>

        <div class="metrics-summary">
          <div class="summary-card" v-if="summary.cpu">
            <div class="summary-title">CPU(%)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.cpu.avg.toFixed(1) }}%</span>
              <span>最大: {{ summary.cpu.max.toFixed(1) }}%</span>
              <span>最小: {{ summary.cpu.min.toFixed(1) }}%</span>
            </div>
          </div>
          <div class="summary-card" v-if="summary.gpu">
            <div class="summary-title">GPU(%)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.gpu.avg.toFixed(1) }}%</span>
              <span>最大: {{ summary.gpu.max.toFixed(1) }}%</span>
              <span>最小: {{ summary.gpu.min.toFixed(1) }}%</span>
            </div>
          </div>
          <div class="summary-card" v-if="summary.fps">
            <div class="summary-title">帧率(FPS)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.fps.avg.toFixed(1) }}</span>
              <span>最大: {{ summary.fps.max }}</span>
              <span>最小: {{ summary.fps.min }}</span>
            </div>
          </div>
          <div class="summary-card" v-if="summary.jank">
            <div class="summary-title">卡顿(Jank)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.jank.avg.toFixed(2) }}</span>
              <span>最大: {{ summary.jank.max }}</span>
              <span>最小: {{ summary.jank.min }}</span>
            </div>
          </div>
          <div class="summary-card" v-if="summary.stutter">
            <div class="summary-title">卡顿率(Stutter%)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.stutter.avg.toFixed(2) }}%</span>
              <span>最大: {{ summary.stutter.max.toFixed(2) }}%</span>
              <span>最小: {{ summary.stutter.min.toFixed(2) }}%</span>
            </div>
          </div>
          <div class="summary-card" v-if="summary.memory">
            <div class="summary-title">内存(MB)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.memory.avg.toFixed(1) }}MB</span>
              <span>最大: {{ summary.memory.max.toFixed(1) }}MB</span>
              <span>最小: {{ summary.memory.min.toFixed(1) }}MB</span>
            </div>
          </div>
          <div class="summary-card" v-if="summary.temp">
            <div class="summary-title">电池温度(℃)</div>
            <div class="summary-stats">
              <span>平均: {{ summary.temp.avg.toFixed(1) }}℃</span>
              <span>最大: {{ summary.temp.max.toFixed(1) }}℃</span>
              <span>最小: {{ summary.temp.min.toFixed(1) }}℃</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref('')
const metrics = ref([])
const chartRef = ref(null)
const chartContainer = ref(null)
let chartInstance = null

const visibleSeries = ref({
  cpu: true,
  gpu: true,
  fps: true,
  jank: false,
  stutter: false,
  memory: true,
  temp: false,
  networkRx: false,
  networkTx: false
})

const summary = ref({
  cpu: null,
  gpu: null,
  fps: null,
  jank: null,
  stutter: null,
  memory: null,
  temp: null
})

const loadMetrics = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.get(`/api/sessions/${props.sessionId}/metrics`, {
      params: { limit: 5000 }
    })
    
    if (response.data.error) {
      error.value = response.data.error
    } else {
      metrics.value = response.data.metrics || []
      if (metrics.value.length > 0) {
        calculateSummary()
        await nextTick()
        initChart()
      } else {
        error.value = '暂无性能数据'
      }
    }
  } catch (err) {
    error.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const calculateSummary = () => {
  const data = metrics.value
  if (data.length === 0) return

  const cpuValues = data.map(m => m.cpu_usage).filter(v => v != null)
  const gpuValues = data.map(m => m.gpu_usage).filter(v => v != null)
  const memValues = data.map(m => m.memory_usage).filter(v => v != null)
  const fpsValues = data.map(m => m.fps).filter(v => v != null)
  const jankValues = data.map(m => m.jank_count).filter(v => v != null)
  const stutterValues = data.map(m => m.stutter_rate).filter(v => v != null)
  const tempValues = data.map(m => m.battery_temp).filter(v => v != null)

  if (cpuValues.length > 0) {
    summary.value.cpu = {
      avg: cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length,
      max: Math.max(...cpuValues),
      min: Math.min(...cpuValues)
    }
  }
  if (gpuValues.length > 0) {
    summary.value.gpu = {
      avg: gpuValues.reduce((a, b) => a + b, 0) / gpuValues.length,
      max: Math.max(...gpuValues),
      min: Math.min(...gpuValues)
    }
  }
  if (fpsValues.length > 0) {
    summary.value.fps = {
      avg: fpsValues.reduce((a, b) => a + b, 0) / fpsValues.length,
      max: Math.max(...fpsValues),
      min: Math.min(...fpsValues)
    }
  }
  if (jankValues.length > 0) {
    summary.value.jank = {
      avg: jankValues.reduce((a, b) => a + b, 0) / jankValues.length,
      max: Math.max(...jankValues),
      min: Math.min(...jankValues)
    }
  }
  if (stutterValues.length > 0) {
    summary.value.stutter = {
      avg: stutterValues.reduce((a, b) => a + b, 0) / stutterValues.length,
      max: Math.max(...stutterValues),
      min: Math.min(...stutterValues)
    }
  }
  if (memValues.length > 0) {
    summary.value.memory = {
      avg: memValues.reduce((a, b) => a + b, 0) / memValues.length,
      max: Math.max(...memValues),
      min: Math.min(...memValues)
    }
  }
  if (tempValues.length > 0) {
    summary.value.temp = {
      avg: tempValues.reduce((a, b) => a + b, 0) / tempValues.length,
      max: Math.max(...tempValues),
      min: Math.min(...tempValues)
    }
  }
}

const initChart = () => {
  if (!chartRef.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  const data = metrics.value
  const times = data.map(m => {
    const date = new Date(m.timestamp)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
  })

  const series = []
  const yAxis = []

  if (visibleSeries.value.cpu) {
    series.push({
      name: 'CPU (%)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.cpu_usage),
      yAxisIndex: 0
    })
    yAxis.push({
      type: 'value',
      name: 'CPU (%)',
      min: 0,
      max: 100,
      position: 'left'
    })
  }

  if (visibleSeries.value.gpu) {
    series.push({
      name: 'GPU (%)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.gpu_usage),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: 'GPU (%)',
      min: 0,
      max: 100,
      position: 'right'
    })
  }

  if (visibleSeries.value.fps) {
    series.push({
      name: '帧率 (FPS)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.fps),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: 'FPS',
      min: 0,
      max: 120,
      position: 'left',
      offset: yAxis.length > 1 ? 60 : 0
    })
  }

  if (visibleSeries.value.jank) {
    series.push({
      name: '卡顿 (Jank)',
      type: 'bar',
      barWidth: 4,
      itemStyle: { color: '#e74c3c', opacity: 0.6 },
      data: data.map(m => m.jank_count),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: 'Jank',
      min: 0,
      position: 'right',
      offset: yAxis.length > 1 ? 60 : 0
    })
  }

  if (visibleSeries.value.stutter) {
    series.push({
      name: '卡顿率 (Stutter%)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2, type: 'dashed' },
      areaStyle: { opacity: 0.15 },
      data: data.map(m => m.stutter_rate),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: 'Stutter %',
      min: 0,
      max: 50,
      position: 'right',
      offset: yAxis.length > 1 ? 120 : 0
    })
  }

  if (visibleSeries.value.memory) {
    series.push({
      name: '内存 (MB)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.memory_usage),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: '内存 (MB)',
      min: 0,
      position: 'left',
      offset: yAxis.length > 1 ? 60 : 0
    })
  }

  if (visibleSeries.value.temp) {
    series.push({
      name: '电池温度 (℃)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.battery_temp),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: '温度 (℃)',
      min: 20,
      max: 55,
      position: 'right',
      offset: yAxis.length > 1 ? 120 : 0
    })
  }

  if (visibleSeries.value.networkRx) {
    series.push({
      name: '网络下行 (KB/s)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.network_rx),
      yAxisIndex: yAxis.length
    })
    yAxis.push({
      type: 'value',
      name: '网络下行 (KB/s)',
      min: 0,
      position: 'left',
      offset: yAxis.length > 1 ? 180 : 0
    })
  }

  if (visibleSeries.value.networkTx) {
    series.push({
      name: '网络上行 (KB/s)',
      type: 'line',
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 },
      data: data.map(m => m.network_tx),
      yAxisIndex: yAxis.length
    })
    if (!visibleSeries.value.networkRx) {
      yAxis.push({
        type: 'value',
        name: '网络上行 (KB/s)',
        min: 0,
        position: 'right',
        offset: yAxis.length > 1 ? 180 : 0
      })
    }
  }

  const option = {
    title: {
      text: '性能指标趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 30
    },
    grid: {
      left: yAxis.length > 2 ? 180 : 60,
      right: yAxis.length > 1 ? 60 : 20,
      top: 80,
      bottom: 60
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(times.length / 10)
      }
    },
    yAxis: yAxis,
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100
      }
    ],
    series: series
  }

  chartInstance.setOption(option)
}

watch(visibleSeries, () => {
  if (metrics.value.length > 0) {
    initChart()
  }
}, { deep: true })

const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  loadMetrics()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chartInstance?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 95%;
  max-width: 1200px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #909399;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #606266;
}

.modal-body {
  padding: 20px;
}

.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chart-controls {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group label {
  font-weight: 500;
  color: #606266;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.checkbox-item input {
  cursor: pointer;
}

.chart-container {
  width: 100%;
  height: 600px;
  margin-bottom: 20px;
}

.chart {
  width: 100%;
  height: 100%;
}

.metrics-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  opacity: 0.9;
}
</style>
