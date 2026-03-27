import { reactive, ref } from 'vue'

const state = reactive({
  dataBuffer: {
    cpu: [],
    memory: [],
    memoryDetail: [],
    fps: [],
    gpu: [],
    jank: [],
    stutter: [],
    batteryTemp: [],
    network: []
  },
  markers: [],
  logList: [],
  screenshotBuffer: [],
  currentScreenshot: '',
  isConnected: false,
  isReconnecting: false,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  lastUpdated: 0,
  lastMetricUpdate: 0,
  lastLogUpdate: 0,
  lastAnalysisUpdate: 0,
  lastReportUpdate: 0,
  currentPackage: '',
  performanceAnalysis: null,
  reportUrl: ''
})

let ws = null
let reconnectTimer = null
let currentSerial = null
let currentTarget = null

const calculateReconnectDelay = (attempt) => {
  return Math.min(1000 * Math.pow(2, attempt), 30000)
}

export const useMonitorStore = () => {

  const connectWs = (serial, target = null) => {
    if (!serial) {
      console.warn('Store: connectWs called without serial')
      return
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
      console.log('Store: WS already connected')
      return
    }

    currentSerial = serial
    currentTarget = target

    if (ws) ws.close()
    if (reconnectTimer) clearTimeout(reconnectTimer)

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/monitor/${serial}`
    
    console.log('Store: Connecting to WS:', wsUrl)
    state.isReconnecting = state.reconnectAttempts > 0
    
    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('Store: WS Connected')
        state.isConnected = true
        state.isReconnecting = false
        state.reconnectAttempts = 0
        const msg = target ? { type: "start", target } : { type: "start" }
        ws.send(JSON.stringify(msg))
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'screenshot') {
          state.screenshotBuffer.push({ time: data.timestamp, url: data.url })
          if (state.screenshotBuffer.length > 50) state.screenshotBuffer.shift()
          state.currentScreenshot = data.url
          return
        }

        if (data.type === 'analysis') {
          state.performanceAnalysis = data.data
          state.lastAnalysisUpdate = Date.now()
          return
        }
        
        if (data.type === 'report_generated') {
          state.reportUrl = data.report_url
          state.lastReportUpdate = Date.now()
          window.dispatchEvent(new CustomEvent('report-generated', { detail: data }))
          return
        }
        
        if (data.type === 'error') {
          console.error('Server error:', data.message)
          window.dispatchEvent(new CustomEvent('report-error', { detail: data }))
          return
        }

        if (data.type === 'log') {
          if (state.logList.length > 1000) state.logList.shift()
          
          const date = new Date(data.timestamp)
          const timeStr = `${date.getHours().toString().padStart(2,'0')}:${date.getMinutes().toString().padStart(2,'0')}:${date.getSeconds().toString().padStart(2,'0')}.${date.getMilliseconds().toString().padStart(3,'0')}`
          
          state.logList.push({
              time: timeStr,
              message: data.message,
              level: data.level,
              isCrash: data.is_crash
          })
          state.lastLogUpdate = Date.now()
          return
        }

        const now = new Date(data.timestamp)
        if (data.package) {
          state.currentPackage = data.package
        }
        
        if (state.dataBuffer.cpu.length > 3600) {
          state.dataBuffer.cpu.shift()
          state.dataBuffer.memory.shift()
          state.dataBuffer.memoryDetail.shift()
          state.dataBuffer.fps.shift()
          state.dataBuffer.gpu.shift()
          state.dataBuffer.jank.shift()
          state.dataBuffer.stutter.shift()
          state.dataBuffer.batteryTemp.shift()
          state.dataBuffer.network.shift()
        }
        
        state.dataBuffer.cpu.push([now, data.cpu])
        state.dataBuffer.memory.push([now, data.memory])
        state.dataBuffer.memoryDetail.push(data.memory_detail || {})
        state.dataBuffer.fps.push([now, data.fps])
        state.dataBuffer.gpu.push([now, data.gpu || 0])
        state.dataBuffer.jank.push([now, data.jank || 0])
        state.dataBuffer.stutter.push([now, data.stutter || 0])
        state.dataBuffer.batteryTemp.push([now, data.battery ? data.battery.temp : 0])
        state.dataBuffer.network.push([now, data.network || {rx: 0, tx: 0}])
        
        state.lastMetricUpdate = Date.now()
      }

      ws.onerror = (e) => {
        console.error('Store: WS Error:', e)
        state.isReconnecting = false
      }
      
      ws.onclose = (e) => {
        console.log('Store: WS Closed:', e.code, e.reason)
        state.isConnected = false
        ws = null
        
        if (e.code !== 1000 && state.reconnectAttempts < state.maxReconnectAttempts) {
          const delay = calculateReconnectDelay(state.reconnectAttempts)
          console.log(`Store: Reconnecting in ${delay}ms (attempt ${state.reconnectAttempts + 1}/${state.maxReconnectAttempts})`)
          
          state.isReconnecting = true
          state.reconnectAttempts++
          
          reconnectTimer = setTimeout(() => {
            if (currentSerial) {
              connectWs(currentSerial, currentTarget)
            }
          }, delay)
        } else if (state.reconnectAttempts >= state.maxReconnectAttempts) {
          console.error('Store: Max reconnect attempts reached')
          state.isReconnecting = false
          window.dispatchEvent(new CustomEvent('ws-reconnect-failed'))
        }
      }
    } catch (error) {
      console.error('Store: Failed to create WebSocket:', error)
      state.isReconnecting = false
    }
  }

  const disconnectWs = () => {
    currentSerial = null
    currentTarget = null
    state.reconnectAttempts = 0
    
    if (ws) {
      ws.onclose = null
      ws.close(1000, 'Client disconnect')
      ws = null
    }
    
    state.isConnected = false
    state.isReconnecting = false
    
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  const clearData = () => {
    state.dataBuffer = {
      cpu: [], memory: [], memoryDetail: [], fps: [], gpu: [], 
      jank: [], stutter: [], batteryTemp: [], network: []
    }
    state.markers = []
    state.logList = []
    state.screenshotBuffer = []
    state.currentScreenshot = ''
  }

  const addMarker = (label) => {
    state.markers.push({
      time: new Date(),
      label: label || 'Mark'
    })
  }

  const generateReport = (deviceModel, appPackage) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('Store: Cannot generate report - WebSocket not connected')
      return false
    }
    
    const msg = {
      type: "generate_report",
      device_model: deviceModel || "Unknown Device",
      app_package: appPackage || "Unknown App"
    }
    
    ws.send(JSON.stringify(msg))
    return true
  }

  return {
    state,
    connectWs,
    disconnectWs,
    clearData,
    addMarker,
    generateReport
  }
}
