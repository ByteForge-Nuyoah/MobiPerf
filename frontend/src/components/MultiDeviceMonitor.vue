<template>
  <div class="multi-device-monitor">
    <div class="header">
      <h2>多设备监控</h2>
      <div class="controls">
        <button @click="showDeviceSelector = true" class="add-device-btn">
          ➕ 添加设备
        </button>
        <button @click="stopAllDevices" class="stop-all-btn" v-if="activeDevices.length > 0">
          ⏹️ 停止全部
        </button>
      </div>
    </div>

    <div v-if="activeDevices.length === 0" class="empty-state">
      <div class="empty-icon">📱</div>
      <p>暂无监控设备</p>
      <button @click="showDeviceSelector = true" class="start-btn">
        开始监控
      </button>
    </div>

    <div v-else class="devices-grid" :class="`grid-${Math.min(activeDevices.length, 3)}`">
      <div
        v-for="device in activeDevices"
        :key="device.serial"
        class="device-card"
      >
        <div class="device-header">
          <div class="device-info">
            <h3>{{ device.model }}</h3>
            <span class="platform-badge" :class="device.platform">
              {{ device.platform === 'ios' ? 'iOS' : 'Android' }}
            </span>
          </div>
          <button @click="stopDevice(device.serial)" class="stop-btn">
            ⏹️
          </button>
        </div>

        <div class="device-target">
          <span class="label">应用:</span>
          <span class="value">{{ device.target || '未设置' }}</span>
        </div>

        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-label">FPS</div>
            <div class="metric-value" :class="getMetricClass('fps', device.data?.fps)">
              {{ device.data?.fps || 0 }}
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-label">CPU</div>
            <div class="metric-value" :class="getMetricClass('cpu', device.data?.cpu)">
              {{ (device.data?.cpu || 0).toFixed(1) }}%
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-label">内存</div>
            <div class="metric-value" :class="getMetricClass('memory', device.data?.memory)">
              {{ (device.data?.memory || 0).toFixed(0) }} MB
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-label">GPU</div>
            <div class="metric-value">
              {{ (device.data?.gpu || 0).toFixed(1) }}%
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-label">电池</div>
            <div class="metric-value">
              {{ device.data?.battery?.level || 100 }}%
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-label">温度</div>
            <div class="metric-value" :class="getMetricClass('temp', device.data?.battery?.temp)">
              {{ (device.data?.battery?.temp || 0).toFixed(1) }}°C
            </div>
          </div>
        </div>

        <div class="mini-chart">
          <canvas :ref="el => chartRefs[device.serial] = el"></canvas>
        </div>
      </div>
    </div>

    <div v-if="showDeviceSelector" class="modal-overlay" @click.self="showDeviceSelector = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>选择设备</h3>
          <button @click="showDeviceSelector = false" class="close-btn">×</button>
        </div>

        <div class="modal-body">
          <div v-if="loading" class="loading">
            <div class="spinner"></div>
            <p>加载设备列表...</p>
          </div>

          <div v-else-if="availableDevices.length === 0" class="no-devices">
            <p>未检测到设备</p>
            <p class="hint">请确保设备已连接并开启调试模式</p>
          </div>

          <div v-else class="device-list">
            <div
              v-for="device in availableDevices"
              :key="device.serial"
              class="device-item"
              :class="{ active: isDeviceActive(device.serial) }"
              @click="selectDevice(device)"
            >
              <div class="device-item-info">
                <div class="device-name">{{ device.model }}</div>
                <div class="device-meta">
                  <span class="platform">{{ device.platform }}</span>
                  <span class="serial">{{ device.serial }}</span>
                </div>
              </div>
              <div v-if="isDeviceActive(device.serial)" class="active-badge">
                ✓ 监控中
              </div>
            </div>
          </div>

          <div v-if="selectedDevice" class="app-selector">
            <h4>选择应用</h4>
            <div v-if="loadingApps" class="loading">
              <div class="spinner"></div>
            </div>
            <div v-else-if="apps.length === 0" class="no-apps">
              <p>未找到应用</p>
            </div>
            <div v-else class="app-list">
              <div
                v-for="app in apps"
                :key="app.package"
                class="app-item"
                @click="startMonitoring(app.package)"
              >
                <div class="app-name">{{ app.name }}</div>
                <div class="app-package">{{ app.package }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'

const showDeviceSelector = ref(false)
const loading = ref(false)
const loadingApps = ref(false)
const availableDevices = ref([])
const apps = ref([])
const selectedDevice = ref(null)
const activeDevices = ref([])
const chartRefs = reactive({})
const chartInstances = reactive({})

let ws = null
let pollTimer = null

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/multi-monitor`)
  
  ws.onopen = () => {
    console.log('Multi-device WebSocket connected')
    ws.send(JSON.stringify({ type: 'get_status' }))
  }
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    handleWebSocketMessage(message)
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected')
    setTimeout(() => {
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        connectWebSocket()
      }
    }, 3000)
  }
}

const handleWebSocketMessage = (message) => {
  switch (message.type) {
    case 'data':
      updateDeviceData(message.serial, message.data)
      break
    case 'device_started':
      console.log('Device started:', message.serial)
      break
    case 'device_stopped':
      removeDevice(message.serial)
      break
    case 'status':
      console.log('Active devices:', message.active_devices)
      break
    case 'error':
      console.error('Error:', message.error)
      break
  }
}

const updateDeviceData = (serial, data) => {
  const device = activeDevices.value.find(d => d.serial === serial)
  if (device) {
    device.data = data
    updateChart(serial, data)
  }
}

const updateChart = (serial, data) => {
  const canvas = chartRefs[serial]
  if (!canvas) return
  
  if (!chartInstances[serial]) {
    const ctx = canvas.getContext('2d')
    chartInstances[serial] = {
      ctx,
      data: [],
      maxPoints: 30
    }
  }
  
  const chart = chartInstances[serial]
  chart.data.push({
    fps: data.fps,
    cpu: data.cpu,
    memory: data.memory
  })
  
  if (chart.data.length > chart.maxPoints) {
    chart.data.shift()
  }
  
  drawChart(chart)
}

const drawChart = (chart) => {
  const { ctx, data, maxPoints } = chart
  const canvas = ctx.canvas
  const width = canvas.width = canvas.offsetWidth * 2
  const height = canvas.height = canvas.offsetHeight * 2
  ctx.scale(2, 2)
  
  ctx.clearRect(0, 0, width, height)
  
  if (data.length < 2) return
  
  const padding = 20
  const chartWidth = width / 2 - padding * 2
  const chartHeight = height / 2 - padding * 2
  
  ctx.strokeStyle = '#4CAF50'
  ctx.lineWidth = 2
  ctx.beginPath()
  
  data.forEach((point, index) => {
    const x = padding + (index / (maxPoints - 1)) * chartWidth
    const y = padding + chartHeight - (point.fps / 60) * chartHeight
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  
  ctx.stroke()
}

const fetchDevices = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/devices')
    availableDevices.value = res.data.devices
  } catch (error) {
    console.error('Failed to fetch devices:', error)
  } finally {
    loading.value = false
  }
}

const selectDevice = async (device) => {
  if (isDeviceActive(device.serial)) {
    return
  }
  
  selectedDevice.value = device
  loadingApps.value = true
  apps.value = []
  
  try {
    const endpoint = device.platform === 'ios' 
      ? `/api/apps/ios/${device.serial}`
      : `/api/apps/${device.serial}`
    
    const res = await axios.get(endpoint)
    apps.value = res.data.apps
  } catch (error) {
    console.error('Failed to fetch apps:', error)
  } finally {
    loadingApps.value = false
  }
}

const startMonitoring = (targetPackage) => {
  if (!selectedDevice.value || !ws) return
  
  ws.send(JSON.stringify({
    type: 'start_device',
    serial: selectedDevice.value.serial,
    target: targetPackage
  }))
  
  activeDevices.value.push({
    serial: selectedDevice.value.serial,
    model: selectedDevice.value.model,
    platform: selectedDevice.value.platform,
    target: targetPackage,
    data: null
  })
  
  showDeviceSelector.value = false
  selectedDevice.value = null
  apps.value = []
}

const stopDevice = (serial) => {
  if (!ws) return
  
  ws.send(JSON.stringify({
    type: 'stop_device',
    serial
  }))
  
  removeDevice(serial)
}

const removeDevice = (serial) => {
  const index = activeDevices.value.findIndex(d => d.serial === serial)
  if (index !== -1) {
    activeDevices.value.splice(index, 1)
  }
  
  if (chartInstances[serial]) {
    delete chartInstances[serial]
  }
}

const stopAllDevices = () => {
  activeDevices.value.forEach(device => {
    stopDevice(device.serial)
  })
}

const isDeviceActive = (serial) => {
  return activeDevices.value.some(d => d.serial === serial)
}

const getMetricClass = (type, value) => {
  if (value === undefined || value === null) return ''
  
  switch (type) {
    case 'fps':
      if (value >= 55) return 'good'
      if (value >= 45) return 'warning'
      return 'bad'
    case 'cpu':
      if (value <= 50) return 'good'
      if (value <= 80) return 'warning'
      return 'bad'
    case 'memory':
      if (value <= 300) return 'good'
      if (value <= 500) return 'warning'
      return 'bad'
    case 'temp':
      if (value <= 40) return 'good'
      if (value <= 50) return 'warning'
      return 'bad'
    default:
      return ''
  }
}

onMounted(() => {
  connectWebSocket()
  fetchDevices()
  
  pollTimer = setInterval(fetchDevices, 5000)
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})
</script>

<style scoped>
.multi-device-monitor {
  padding: var(--spacing-xl);
  max-width: 1600px;
  margin: 0 auto;
  animation: fadeIn 0.6s ease-out;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2xl);
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.header h2 {
  margin: 0;
  font-size: var(--font-3xl);
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.controls {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.add-device-btn, .stop-all-btn, .start-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-md);
  white-space: nowrap;
}

.add-device-btn {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
}

.add-device-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stop-all-btn {
  background: linear-gradient(135deg, var(--danger-color), #e53e3e);
  color: white;
}

.stop-all-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.start-btn {
  background: linear-gradient(135deg, var(--success-color), #38a169);
  color: white;
  margin-top: var(--spacing-md);
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-2xl) var(--spacing-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
}

.empty-icon {
  font-size: 80px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

.empty-state p {
  font-size: var(--font-lg);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-md);
}

.devices-grid {
  display: grid;
  gap: var(--spacing-lg);
  animation: fadeIn 0.8s ease-out;
}

.grid-1 {
  grid-template-columns: 1fr;
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.device-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-xl);
  transition: all var(--transition-base);
  animation: slideIn 0.5s ease-out;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--border-light);
}

.device-info h3 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.platform-badge {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
}

.platform-badge.ios {
  background: linear-gradient(135deg, #e2e8f0, #cbd5e0);
  color: #4a5568;
}

.platform-badge.android {
  background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
  color: #22543d;
}

.stop-btn {
  background: var(--bg-tertiary);
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.stop-btn:hover {
  background: linear-gradient(135deg, var(--danger-color), #e53e3e);
  transform: scale(1.1);
}

.device-target {
  margin-bottom: var(--spacing-md);
  font-size: var(--font-sm);
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.device-target .label {
  color: var(--text-tertiary);
  margin-right: var(--spacing-xs);
}

.device-target .value {
  color: var(--text-primary);
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.metric-card {
  background: var(--bg-tertiary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  text-align: center;
  transition: all var(--transition-fast);
}

.metric-card:hover {
  background: var(--bg-secondary);
  transform: translateY(-2px);
}

.metric-label {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.metric-value {
  font-size: var(--font-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.metric-value.good {
  color: var(--success-color);
}

.metric-value.warning {
  color: var(--warning-color);
}

.metric-value.bad {
  color: var(--danger-color);
}

.mini-chart {
  height: 120px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-top: var(--spacing-sm);
}

.mini-chart canvas {
  width: 100%;
  height: 100%;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal-backdrop);
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
  animation: slideIn 0.3s ease-out;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 2px solid var(--border-light);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.device-selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-group label {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.form-group select,
.form-group input {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--font-sm);
  transition: all var(--transition-fast);
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 2px solid var(--border-light);
}

.modal-footer button {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
}

.cancel-btn {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--bg-secondary);
}

.confirm-btn {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  box-shadow: var(--shadow-md);
}

.confirm-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 1200px) {
  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .multi-device-monitor {
    padding: var(--spacing-md);
  }
  
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .grid-2, .grid-3 {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-content {
    width: 95%;
    max-height: 90vh;
  }
}

@media (max-width: 480px) {
  .multi-device-monitor {
    padding: var(--spacing-sm);
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .mini-chart {
    height: 100px;
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
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
