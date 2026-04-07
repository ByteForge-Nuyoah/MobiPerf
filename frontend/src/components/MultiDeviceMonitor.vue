<template>
  <div class="multi-device-monitor">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>多设备监控</h1>
          <p class="header-desc">同时监控多台设备的性能指标</p>
        </div>
        <div class="header-actions">
          <button @click="showDeviceSelector = true" class="add-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            添加设备
          </button>
          <button v-if="activeDevices.length > 0" @click="stopAllDevices" class="stop-all-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="6" width="12" height="12" rx="2"></rect>
            </svg>
            停止全部
          </button>
        </div>
      </div>
      
      <div v-if="activeDevices.length > 0" class="stats-bar">
        <div class="stat-item">
          <span class="stat-value">{{ activeDevices.length }}</span>
          <span class="stat-label">监控设备</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ avgFps.toFixed(0) }}</span>
          <span class="stat-label">平均 FPS</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ avgCpu.toFixed(0) }}%</span>
          <span class="stat-label">平均 CPU</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ avgMemory.toFixed(0) }} MB</span>
          <span class="stat-label">平均内存</span>
        </div>
      </div>
    </div>

    <div v-if="activeDevices.length === 0" class="empty-state">
      <div class="empty-illustration">
        <svg viewBox="0 0 400 300" fill="none">
          <rect x="50" y="80" width="100" height="160" rx="12" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
          <rect x="60" y="100" width="80" height="100" rx="4" fill="#e2e8f0"/>
          <circle cx="100" cy="220" r="8" fill="#cbd5e1"/>
          
          <rect x="170" y="60" width="100" height="180" rx="12" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
          <rect x="180" y="80" width="80" height="120" rx="4" fill="#e2e8f0"/>
          <circle cx="220" cy="220" r="8" fill="#cbd5e1"/>
          
          <rect x="290" y="80" width="100" height="160" rx="12" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
          <rect x="300" y="100" width="80" height="100" rx="4" fill="#e2e8f0"/>
          <circle cx="340" cy="220" r="8" fill="#cbd5e1"/>
          
          <circle cx="120" cy="150" r="20" fill="#667eea" opacity="0.2"/>
          <circle cx="220" cy="140" r="25" fill="#667eea" opacity="0.3"/>
          <circle cx="320" cy="150" r="20" fill="#667eea" opacity="0.2"/>
        </svg>
      </div>
      <h3>暂无监控设备</h3>
      <p>点击上方按钮添加设备开始监控</p>
      <button @click="showDeviceSelector = true" class="start-monitoring-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        开始监控
      </button>
    </div>

    <div v-else class="devices-container">
      <div class="devices-grid">
        <div
          v-for="device in activeDevices"
          :key="device.serial"
          class="device-card"
        >
          <div class="card-header">
            <div class="device-info">
              <div class="device-icon" :class="device.platform">
                <svg v-if="device.platform === 'ios'" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85-.29-.15-.65-.06-.83.22l-1.88 3.24c-1.44-.68-3.05-.99-4.71-.99-1.68 0-3.28.31-4.74.99L5.16 5.67c-.19-.29-.54-.38-.84-.23-.31.16-.42.54-.26.85L5.9 9.48C3.77 11.07 2.36 13.54 2 16h20c-.36-2.46-1.76-4.93-3.9-6.52zM7 14c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm10 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/>
                </svg>
              </div>
              <div class="device-details">
                <h4>{{ device.model }}</h4>
                <span class="device-serial">{{ device.serial }}</span>
              </div>
            </div>
            <button @click="stopDevice(device.serial)" class="stop-btn" title="停止监控">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="6" y="6" width="12" height="12" rx="2"></rect>
              </svg>
            </button>
          </div>

          <div class="app-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="9" y1="3" x2="9" y2="21"></line>
            </svg>
            <span>{{ device.target || '未设置应用' }}</span>
          </div>

          <div class="metrics-section">
            <div class="metrics-row">
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-icon fps">🎮</span>
                  <span class="metric-name">FPS</span>
                </div>
                <div class="metric-value" :class="getMetricClass('fps', device.data?.fps)">
                  {{ device.data?.fps || 0 }}
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-icon cpu">💻</span>
                  <span class="metric-name">CPU</span>
                </div>
                <div class="metric-value" :class="getMetricClass('cpu', device.data?.cpu)">
                  {{ (device.data?.cpu || 0).toFixed(1) }}%
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-icon memory">📊</span>
                  <span class="metric-name">内存</span>
                </div>
                <div class="metric-value" :class="getMetricClass('memory', device.data?.memory)">
                  {{ (device.data?.memory || 0).toFixed(0) }}
                </div>
              </div>
            </div>

            <div class="metrics-row">
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-icon gpu">🎨</span>
                  <span class="metric-name">GPU</span>
                </div>
                <div class="metric-value">
                  {{ (device.data?.gpu || 0).toFixed(1) }}%
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-icon battery">🔋</span>
                  <span class="metric-name">电池</span>
                </div>
                <div class="metric-value" :class="getMetricClass('battery', device.data?.battery?.level)">
                  {{ device.data?.battery?.level || 100 }}%
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-icon temp">🌡️</span>
                  <span class="metric-name">温度</span>
                </div>
                <div class="metric-value" :class="getMetricClass('temp', device.data?.battery?.temp)">
                  {{ (device.data?.battery?.temp || 0).toFixed(1) }}°
                </div>
              </div>
            </div>
          </div>

          <div class="chart-section">
            <div class="chart-header">
              <span>实时趋势</span>
              <div class="chart-legend">
                <span class="legend-item fps"><span class="dot"></span>FPS</span>
                <span class="legend-item cpu"><span class="dot"></span>CPU</span>
              </div>
            </div>
            <div class="chart-container">
              <canvas :ref="el => chartRefs[device.serial] = el"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="modal">
      <div v-if="showDeviceSelector" class="modal-overlay" @click.self="showDeviceSelector = false">
        <div class="modal-content">
          <div class="modal-header">
            <div class="modal-title">
              <h3>选择设备</h3>
              <p>选择要监控的设备和应用</p>
            </div>
            <button @click="showDeviceSelector = false" class="modal-close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="step-indicator">
              <div class="step" :class="{ active: !selectedDevice, completed: selectedDevice }">
                <span class="step-number">1</span>
                <span class="step-label">选择设备</span>
              </div>
              <div class="step-line" :class="{ active: selectedDevice }"></div>
              <div class="step" :class="{ active: selectedDevice }">
                <span class="step-number">2</span>
                <span class="step-label">选择应用</span>
              </div>
            </div>

            <div v-if="loading" class="loading-state">
              <div class="loading-spinner"></div>
              <p>加载设备列表...</p>
            </div>

            <div v-else-if="availableDevices.length === 0" class="no-devices-state">
              <div class="no-devices-icon">📱</div>
              <h4>未检测到设备</h4>
              <p>请确保设备已连接并开启调试模式</p>
              <button @click="fetchDevices" class="refresh-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <polyline points="1 20 1 14 7 14"></polyline>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
                刷新设备
              </button>
            </div>

            <div v-else-if="!selectedDevice" class="device-list">
              <div
                v-for="device in availableDevices"
                :key="device.serial"
                class="device-item"
                :class="{ active: isDeviceActive(device.serial), disabled: isDeviceActive(device.serial) }"
                @click="!isDeviceActive(device.serial) && selectDevice(device)"
              >
                <div class="device-item-icon" :class="device.platform">
                  <svg v-if="device.platform === 'ios'" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85-.29-.15-.65-.06-.83.22l-1.88 3.24c-1.44-.68-3.05-.99-4.71-.99-1.68 0-3.28.31-4.74.99L5.16 5.67c-.19-.29-.54-.38-.84-.23-.31.16-.42.54-.26.85L5.9 9.48C3.77 11.07 2.36 13.54 2 16h20c-.36-2.46-1.76-4.93-3.9-6.52zM7 14c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm10 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/>
                  </svg>
                </div>
                <div class="device-item-info">
                  <div class="device-item-name">{{ device.model }}</div>
                  <div class="device-item-meta">
                    <span class="platform-tag" :class="device.platform">
                      {{ device.platform === 'ios' ? 'iOS' : 'Android' }}
                    </span>
                    <span class="serial-tag">{{ device.serial }}</span>
                  </div>
                </div>
                <div v-if="isDeviceActive(device.serial)" class="active-indicator">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  监控中
                </div>
                <svg v-else class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </div>
            </div>

            <div v-else class="app-selector">
              <div class="selected-device">
                <span class="label">已选择设备:</span>
                <span class="value">{{ selectedDevice.model }}</span>
                <button @click="selectedDevice = null; apps = []" class="change-btn">更换</button>
              </div>

              <div v-if="loadingApps" class="loading-state">
                <div class="loading-spinner"></div>
                <p>加载应用列表...</p>
              </div>

              <div v-else-if="apps.length === 0" class="no-apps-state">
                <div class="no-apps-icon">📦</div>
                <h4>未找到应用</h4>
                <p>该设备上没有可监控的应用</p>
              </div>

              <div v-else class="app-list">
                <div
                  v-for="app in apps"
                  :key="app.package"
                  class="app-item"
                  @click="startMonitoring(app.package)"
                >
                  <div class="app-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    </svg>
                  </div>
                  <div class="app-info">
                    <div class="app-name">{{ app.name }}</div>
                    <div class="app-package">{{ app.package }}</div>
                  </div>
                  <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
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

const avgFps = computed(() => {
  if (activeDevices.value.length === 0) return 0
  const total = activeDevices.value.reduce((sum, d) => sum + (d.data?.fps || 0), 0)
  return total / activeDevices.value.length
})

const avgCpu = computed(() => {
  if (activeDevices.value.length === 0) return 0
  const total = activeDevices.value.reduce((sum, d) => sum + (d.data?.cpu || 0), 0)
  return total / activeDevices.value.length
})

const avgMemory = computed(() => {
  if (activeDevices.value.length === 0) return 0
  const total = activeDevices.value.reduce((sum, d) => sum + (d.data?.memory || 0), 0)
  return total / activeDevices.value.length
})

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
  
  const padding = 10
  const chartWidth = width / 2 - padding * 2
  const chartHeight = height / 2 - padding * 2
  
  ctx.strokeStyle = '#667eea'
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
  
  ctx.strokeStyle = '#f56565'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  
  data.forEach((point, index) => {
    const x = padding + (index / (maxPoints - 1)) * chartWidth
    const y = padding + chartHeight - (point.cpu / 100) * chartHeight
    
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
    case 'battery':
      if (value >= 50) return 'good'
      if (value >= 20) return 'warning'
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
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.page-header {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

.header-desc {
  margin: 4px 0 0;
  font-size: 14px;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.add-btn, .stop-all-btn, .start-monitoring-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.add-btn svg, .stop-all-btn svg, .start-monitoring-btn svg {
  width: 18px;
  height: 18px;
}

.stop-all-btn {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #dc2626;
}

.stop-all-btn:hover {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: #e2e8f0;
}

.empty-state {
  text-align: center;
  padding: 80px 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.empty-illustration {
  width: 300px;
  height: 200px;
  margin: 0 auto 24px;
}

.empty-state h3 {
  margin: 0 0 8px;
  font-size: 20px;
  color: #334155;
}

.empty-state p {
  margin: 0 0 24px;
  font-size: 14px;
  color: #64748b;
}

.start-monitoring-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  margin: 0 auto;
}

.start-monitoring-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.devices-container {
  animation: fadeIn 0.5s ease-out;
}

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
}

.device-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #f1f5f9;
}

.device-icon svg {
  width: 24px;
  height: 24px;
}

.device-icon.ios {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #475569;
}

.device-icon.android {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #16a34a;
}

.device-details h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.device-serial {
  font-size: 12px;
  color: #94a3b8;
}

.stop-btn {
  background: #f8fafc;
  border: none;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s ease;
}

.stop-btn:hover {
  background: #fef2f2;
  color: #ef4444;
}

.stop-btn svg {
  width: 20px;
  height: 20px;
}

.app-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #64748b;
}

.app-info svg {
  width: 16px;
  height: 16px;
}

.metrics-section {
  margin-bottom: 20px;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.metrics-row:last-child {
  margin-bottom: 0;
}

.metric-item {
  background: #f8fafc;
  padding: 12px;
  border-radius: 10px;
  text-align: center;
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-bottom: 4px;
}

.metric-icon {
  font-size: 12px;
}

.metric-name {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.metric-value.good {
  color: #16a34a;
}

.metric-value.warning {
  color: #ea580c;
}

.metric-value.bad {
  color: #dc2626;
}

.chart-section {
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
}

.chart-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item.fps .dot {
  background: #667eea;
}

.legend-item.cpu .dot {
  background: #f56565;
}

.chart-container {
  height: 80px;
}

.chart-container canvas {
  width: 100%;
  height: 100%;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 560px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-title h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.modal-title p {
  margin: 4px 0 0;
  font-size: 13px;
  opacity: 0.9;
}

.modal-close {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.25);
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  color: #64748b;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.step.active .step-number {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.step.completed .step-number {
  background: #dcfce7;
  color: #16a34a;
}

.step-label {
  font-size: 12px;
  color: #64748b;
}

.step.active .step-label {
  color: #667eea;
  font-weight: 600;
}

.step-line {
  width: 80px;
  height: 2px;
  background: #e2e8f0;
  margin: 0 16px;
  margin-bottom: 24px;
  transition: background 0.3s ease;
}

.step-line.active {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: #64748b;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-devices-state, .no-apps-state {
  text-align: center;
  padding: 40px;
}

.no-devices-icon, .no-apps-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.no-devices-state h4, .no-apps-state h4 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #334155;
}

.no-devices-state p, .no-apps-state p {
  margin: 0 0 16px;
  font-size: 14px;
  color: #64748b;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  background: #e2e8f0;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.device-list, .app-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-item, .app-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.device-item:hover:not(.disabled), .app-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.device-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.device-item-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  margin-right: 12px;
}

.device-item-icon svg {
  width: 20px;
  height: 20px;
}

.device-item-icon.ios {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #475569;
}

.device-item-icon.android {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #16a34a;
}

.device-item-info, .app-info {
  flex: 1;
}

.device-item-name, .app-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.device-item-meta {
  display: flex;
  gap: 8px;
}

.platform-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.platform-tag.ios {
  background: #e2e8f0;
  color: #475569;
}

.platform-tag.android {
  background: #dcfce7;
  color: #16a34a;
}

.serial-tag {
  font-size: 11px;
  color: #94a3b8;
}

.active-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.active-indicator svg {
  width: 14px;
  height: 14px;
}

.arrow-icon {
  width: 20px;
  height: 20px;
  color: #94a3b8;
}

.app-selector {
  animation: fadeIn 0.3s ease-out;
}

.selected-device {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 13px;
}

.selected-device .label {
  color: #64748b;
}

.selected-device .value {
  font-weight: 600;
  color: #1e293b;
}

.change-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.change-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.app-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
}

.app-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 10px;
  margin-right: 12px;
}

.app-icon svg {
  width: 20px;
  height: 20px;
  color: #64748b;
}

.app-info .app-package {
  font-size: 11px;
  color: #94a3b8;
}

.modal-enter-active, .modal-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(20px);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1024px) {
  .multi-device-monitor {
    padding: 20px;
  }
  
  .devices-grid {
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
  }
  
  .device-card {
    padding: 20px;
  }
  
  .stats-bar {
    gap: 20px;
    padding: 14px 20px;
  }
  
  .stat-value {
    font-size: 22px;
  }
  
  .modal-content {
    max-width: 500px;
  }
  
  .modal-header {
    padding: 20px 24px;
  }
  
  .modal-body {
    padding: 20px 24px;
  }
}

@media (max-width: 768px) {
  .multi-device-monitor {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .header-left h1 {
    font-size: 24px;
  }
  
  .header-desc {
    font-size: 13px;
  }
  
  .header-actions {
    justify-content: stretch;
    gap: 8px;
  }
  
  .add-btn, .stop-all-btn {
    flex: 1;
    justify-content: center;
    padding: 10px 16px;
    font-size: 13px;
  }
  
  .stats-bar {
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
    padding: 12px 16px;
  }
  
  .stat-item {
    min-width: 60px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .stat-divider {
    height: 30px;
  }
  
  .empty-state {
    padding: 60px 24px;
  }
  
  .empty-illustration {
    width: 240px;
    height: 160px;
  }
  
  .empty-state h3 {
    font-size: 18px;
  }
  
  .empty-state p {
    font-size: 13px;
  }
  
  .devices-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .device-card {
    padding: 16px;
  }
  
  .card-header {
    margin-bottom: 12px;
  }
  
  .device-icon {
    width: 40px;
    height: 40px;
  }
  
  .device-icon svg {
    width: 20px;
    height: 20px;
  }
  
  .device-details h4 {
    font-size: 15px;
  }
  
  .device-serial {
    font-size: 11px;
  }
  
  .stop-btn {
    padding: 6px;
  }
  
  .stop-btn svg {
    width: 18px;
    height: 18px;
  }
  
  .app-info {
    padding: 10px 12px;
    margin-bottom: 16px;
    font-size: 12px;
  }
  
  .metrics-section {
    margin-bottom: 16px;
  }
  
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 10px;
  }
  
  .metric-item {
    padding: 10px;
  }
  
  .metric-icon {
    font-size: 11px;
  }
  
  .metric-name {
    font-size: 10px;
  }
  
  .metric-value {
    font-size: 16px;
  }
  
  .chart-section {
    padding: 10px;
  }
  
  .chart-header {
    font-size: 11px;
    margin-bottom: 6px;
  }
  
  .chart-legend {
    gap: 10px;
  }
  
  .legend-item {
    font-size: 10px;
  }
  
  .legend-item .dot {
    width: 6px;
    height: 6px;
  }
  
  .chart-container {
    height: 70px;
  }
  
  .modal-overlay {
    padding: 0;
  }
  
  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .modal-header {
    padding: 16px 20px;
  }
  
  .modal-title h3 {
    font-size: 18px;
  }
  
  .modal-title p {
    font-size: 12px;
  }
  
  .modal-close {
    padding: 6px;
  }
  
  .modal-close svg {
    width: 18px;
    height: 18px;
  }
  
  .modal-body {
    padding: 16px 20px;
  }
  
  .step-indicator {
    margin-bottom: 20px;
  }
  
  .step-number {
    width: 28px;
    height: 28px;
    font-size: 13px;
  }
  
  .step-label {
    font-size: 11px;
  }
  
  .step-line {
    width: 60px;
    margin: 0 12px;
    margin-bottom: 20px;
  }
  
  .loading-state {
    padding: 30px;
  }
  
  .loading-spinner {
    width: 36px;
    height: 36px;
  }
  
  .no-devices-state, .no-apps-state {
    padding: 30px;
  }
  
  .no-devices-icon, .no-apps-icon {
    font-size: 40px;
  }
  
  .no-devices-state h4, .no-apps-state h4 {
    font-size: 15px;
  }
  
  .no-devices-state p, .no-apps-state p {
    font-size: 13px;
  }
  
  .refresh-btn {
    padding: 8px 16px;
    font-size: 13px;
  }
  
  .device-item, .app-item {
    padding: 12px;
  }
  
  .device-item-icon, .app-icon {
    width: 36px;
    height: 36px;
    margin-right: 10px;
  }
  
  .device-item-icon svg, .app-icon svg {
    width: 18px;
    height: 18px;
  }
  
  .device-item-name, .app-name {
    font-size: 13px;
  }
  
  .platform-tag {
    font-size: 10px;
    padding: 2px 6px;
  }
  
  .serial-tag {
    font-size: 10px;
  }
  
  .active-indicator {
    padding: 3px 10px;
    font-size: 11px;
  }
  
  .active-indicator svg {
    width: 12px;
    height: 12px;
  }
  
  .arrow-icon {
    width: 18px;
    height: 18px;
  }
  
  .selected-device {
    padding: 10px 12px;
    font-size: 12px;
    margin-bottom: 12px;
  }
  
  .change-btn {
    padding: 3px 10px;
    font-size: 11px;
  }
  
  .app-item {
    padding: 12px;
  }
  
  .app-info .app-package {
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .multi-device-monitor {
    padding: 12px;
  }
  
  .header-left h1 {
    font-size: 20px;
  }
  
  .header-desc {
    font-size: 12px;
  }
  
  .header-actions {
    flex-direction: column;
  }
  
  .add-btn, .stop-all-btn {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .add-btn svg, .stop-all-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .stats-bar {
    gap: 12px;
    padding: 10px 12px;
  }
  
  .stat-item {
    min-width: 50px;
  }
  
  .stat-value {
    font-size: 18px;
  }
  
  .stat-label {
    font-size: 10px;
  }
  
  .stat-divider {
    height: 24px;
  }
  
  .empty-state {
    padding: 40px 16px;
  }
  
  .empty-illustration {
    width: 200px;
    height: 140px;
  }
  
  .empty-state h3 {
    font-size: 16px;
  }
  
  .empty-state p {
    font-size: 12px;
    margin-bottom: 16px;
  }
  
  .start-monitoring-btn {
    padding: 8px 16px;
    font-size: 12px;
  }
  
  .start-monitoring-btn svg {
    width: 14px;
    height: 14px;
  }
  
  .device-card {
    padding: 12px;
  }
  
  .device-icon {
    width: 36px;
    height: 36px;
  }
  
  .device-details h4 {
    font-size: 14px;
  }
  
  .device-serial {
    font-size: 10px;
  }
  
  .stop-btn {
    padding: 4px;
  }
  
  .stop-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .app-info {
    padding: 8px 10px;
    margin-bottom: 12px;
    font-size: 11px;
  }
  
  .app-info svg {
    width: 14px;
    height: 14px;
  }
  
  .metrics-row {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .metric-item {
    padding: 8px;
  }
  
  .metric-icon {
    font-size: 10px;
  }
  
  .metric-name {
    font-size: 9px;
  }
  
  .metric-value {
    font-size: 14px;
  }
  
  .chart-section {
    padding: 8px;
  }
  
  .chart-header {
    font-size: 10px;
    margin-bottom: 4px;
  }
  
  .chart-legend {
    gap: 8px;
  }
  
  .legend-item {
    font-size: 9px;
  }
  
  .legend-item .dot {
    width: 5px;
    height: 5px;
  }
  
  .chart-container {
    height: 60px;
  }
  
  .modal-header {
    padding: 12px 16px;
  }
  
  .modal-title h3 {
    font-size: 16px;
  }
  
  .modal-title p {
    font-size: 11px;
  }
  
  .modal-close {
    padding: 4px;
  }
  
  .modal-close svg {
    width: 16px;
    height: 16px;
  }
  
  .modal-body {
    padding: 12px 16px;
  }
  
  .step-indicator {
    margin-bottom: 16px;
  }
  
  .step-number {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }
  
  .step-label {
    font-size: 10px;
  }
  
  .step-line {
    width: 40px;
    margin: 0 8px;
    margin-bottom: 16px;
  }
  
  .loading-state {
    padding: 24px;
  }
  
  .loading-spinner {
    width: 32px;
    height: 32px;
    margin-bottom: 12px;
  }
  
  .loading-state p {
    font-size: 12px;
  }
  
  .no-devices-state, .no-apps-state {
    padding: 24px;
  }
  
  .no-devices-icon, .no-apps-icon {
    font-size: 36px;
    margin-bottom: 12px;
  }
  
  .no-devices-state h4, .no-apps-state h4 {
    font-size: 14px;
    margin-bottom: 6px;
  }
  
  .no-devices-state p, .no-apps-state p {
    font-size: 12px;
    margin-bottom: 12px;
  }
  
  .refresh-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .refresh-btn svg {
    width: 14px;
    height: 14px;
  }
  
  .device-item, .app-item {
    padding: 10px;
  }
  
  .device-item-icon, .app-icon {
    width: 32px;
    height: 32px;
    margin-right: 8px;
  }
  
  .device-item-icon svg, .app-icon svg {
    width: 16px;
    height: 16px;
  }
  
  .device-item-name, .app-name {
    font-size: 12px;
    margin-bottom: 2px;
  }
  
  .device-item-meta {
    gap: 6px;
  }
  
  .platform-tag {
    font-size: 9px;
    padding: 1px 5px;
  }
  
  .serial-tag {
    font-size: 9px;
  }
  
  .active-indicator {
    padding: 2px 8px;
    font-size: 10px;
  }
  
  .active-indicator svg {
    width: 10px;
    height: 10px;
  }
  
  .arrow-icon {
    width: 16px;
    height: 16px;
  }
  
  .selected-device {
    padding: 8px 10px;
    font-size: 11px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }
  
  .change-btn {
    padding: 2px 8px;
    font-size: 10px;
  }
  
  .app-item {
    padding: 10px;
  }
  
  .app-info .app-package {
    font-size: 9px;
  }
}
</style>
