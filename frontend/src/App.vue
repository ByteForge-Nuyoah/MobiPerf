<script setup>
import { ref, onMounted, onUnmounted, watch, computed, defineAsyncComponent } from 'vue'
import axios from 'axios'

const MonitorChart = defineAsyncComponent(() => import('./components/MonitorChart.vue'))
const LogViewer = defineAsyncComponent(() => import('./components/LogViewer.vue'))
const AnalysisReport = defineAsyncComponent(() => import('./components/AnalysisReport.vue'))
const PerformanceAnalysis = defineAsyncComponent(() => import('./components/PerformanceAnalysis.vue'))
const HistoryView = defineAsyncComponent(() => import('./components/HistoryView.vue'))
const MultiDeviceMonitor = defineAsyncComponent(() => import('./components/MultiDeviceMonitor.vue'))
const NotificationCenter = defineAsyncComponent(() => import('./components/NotificationCenter.vue'))
const AuthForm = defineAsyncComponent(() => import('./components/AuthForm.vue'))

import { useMonitorStore } from './composables/useMonitorStore'
import { useAuthStore } from './composables/useAuthStore'

const devices = ref([])
const appList = ref([])
const selectedSerial = ref('')
const targetPackage = ref('')
const isMonitoring = ref(false)
const selectedDevice = ref(null)
const currentTab = ref('monitor')
const showAppDropdown = ref(false)
let pollTimer = null
const { state: monitorState } = useMonitorStore()
const { state: authState, checkAuth, logout } = useAuthStore()

const filteredApps = computed(() => {
  if (!targetPackage.value) return appList.value
  const lower = targetPackage.value.toLowerCase()
  return appList.value.filter(app => 
    app.name.toLowerCase().includes(lower) || 
    app.package.toLowerCase().includes(lower)
  )
})

const selectApp = (app) => {
  targetPackage.value = app.package
  showAppDropdown.value = false
}

const handleBlur = () => {
  // Delay hide to allow click event to register
  setTimeout(() => {
    showAppDropdown.value = false
  }, 200)
}

const fetchDevices = async (isPoll = false) => {
  try {
    const res = await axios.get('/api/devices')
    const newDevices = res.data.devices
    
    // Check if current device is disconnected
    if (selectedSerial.value) {
        const stillConnected = newDevices.find(d => d.serial === selectedSerial.value)
        if (!stillConnected) {
             if (isMonitoring.value) {
                 isMonitoring.value = false
                 alert('设备已断开连接')
             }
             selectedSerial.value = ''
        }
    }

    devices.value = newDevices
    
    // Auto select first if none selected
    if (devices.value.length > 0 && !selectedSerial.value) {
      selectedSerial.value = devices.value[0].serial
    }
    
    updateSelectedDevice()
    
    if (!isPoll) {
        fetchApps()
    }
  } catch (err) {
    if (!isPoll) console.error(err)
  }
}

const fetchApps = async () => {
  if (!selectedSerial.value) {
      appList.value = []
      return
  }
  try {
    const res = await axios.get(`/api/apps/${selectedSerial.value}`)
    appList.value = res.data.apps
  } catch (err) {
    console.error("Failed to fetch apps", err)
    appList.value = []
  }
}

const updateSelectedDevice = () => {
  selectedDevice.value = devices.value.find(d => d.serial === selectedSerial.value)
}

// Watch selection change
watch(selectedSerial, () => {
  updateSelectedDevice()
  isMonitoring.value = false
  fetchApps()
})

onMounted(async () => {
  const isAuthenticated = await checkAuth()
  
  if (isAuthenticated) {
    fetchDevices()
    pollTimer = setInterval(() => fetchDevices(true), 3000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const handleLogout = async () => {
  await logout()
  if (pollTimer) clearInterval(pollTimer)
}

const toggleMonitor = () => {
    if (!selectedSerial.value) {
      alert('请先连接并选择设备')
      return
    }

    if (!isMonitoring.value) {
     if (selectedDevice.value?.platform === 'ios' && !targetPackage.value) {
       alert('iOS 设备请填写 Bundle ID')
       return
     }
  }
  isMonitoring.value = !isMonitoring.value
}

watch(() => monitorState.currentPackage, (pkg) => {
  if (!pkg) return
  if (isMonitoring.value && !targetPackage.value) {
    targetPackage.value = pkg
  }
})
</script>

<template>
  <div class="container">
    <AuthForm v-if="!authState.isAuthenticated" />
    
    <div v-else>
      <header>
        <div class="header-top">
          <h1>
            <span class="logo-icon">📊</span>
            MobiPerf
          </h1>
          <div class="header-right">
            <nav class="nav-tabs">
              <div 
                class="tab-item" 
                :class="{ active: currentTab === 'monitor' }"
                @click="currentTab = 'monitor'"
              >
                <span class="tab-icon">📈</span>
                <span class="tab-text">监控</span>
              </div>
              <div 
                class="tab-item" 
                :class="{ active: currentTab === 'multi' }"
                @click="currentTab = 'multi'"
              >
                <span class="tab-icon">📱</span>
                <span class="tab-text">多设备</span>
              </div>
              <div 
                class="tab-item" 
                :class="{ active: currentTab === 'analysis' }"
                @click="currentTab = 'analysis'"
              >
                <span class="tab-icon">📊</span>
                <span class="tab-text">分析</span>
              </div>
              <div 
                class="tab-item" 
                :class="{ active: currentTab === 'history' }"
                @click="currentTab = 'history'"
              >
                <span class="tab-icon">📁</span>
                <span class="tab-text">历史</span>
              </div>
              <div 
                class="tab-item" 
                :class="{ active: currentTab === 'logs' }"
                @click="currentTab = 'logs'"
              >
                <span class="tab-icon">📝</span>
                <span class="tab-text">日志</span>
              </div>
            </nav>
            <div class="user-menu">
              <div class="user-avatar">
                {{ authState.user?.username?.charAt(0).toUpperCase() || 'U' }}
              </div>
              <div class="user-info">
                <span class="user-name">{{ authState.user?.username }}</span>
                <span class="user-role">{{ authState.user?.role || 'developer' }}</span>
              </div>
              <button @click="handleLogout" class="logout-btn" title="退出登录">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
              </button>
            </div>
            <NotificationCenter />
          </div>
        </div>
      
      <div class="controls" v-if="currentTab === 'monitor'">
        <select v-model="selectedSerial">
          <option v-for="d in devices" :key="d.serial" :value="d.serial">
            {{ d.model }} ({{ d.platform }})
          </option>
        </select>
        
        <div class="input-wrapper">
          <input 
            v-model="targetPackage" 
            type="text"
            placeholder="应用包名 / Bundle ID (可选择或输入)" 
            class="pkg-input"
            @focus="showAppDropdown = true"
            @blur="handleBlur"
          />
          <ul v-if="showAppDropdown && filteredApps.length" class="dropdown-list">
            <li 
              v-for="app in filteredApps" 
              :key="app.package" 
              @click="selectApp(app)"
            >
              {{ app.name }} <span class="pkg-sub">{{ app.package }}</span>
            </li>
          </ul>
        </div>

        <button @click="fetchDevices">刷新设备</button>
        <button @click="toggleMonitor" :class="{ stop: isMonitoring }" :disabled="!selectedSerial && !isMonitoring">
          {{ isMonitoring ? '停止测试' : '开始测试' }}
        </button>
      </div>
    </header>

    <main>
      <keep-alive>
        <MonitorChart 
          v-if="currentTab === 'monitor'"
          :serial="selectedSerial" 
          :active="isMonitoring" 
          :target="targetPackage"
          class="main-content"
        />
        <MultiDeviceMonitor
          v-else-if="currentTab === 'multi'"
          class="main-content"
        />
        <PerformanceAnalysis
          v-else-if="currentTab === 'performance'"
          class="main-content"
        />
        <LogViewer
          v-else-if="currentTab === 'logs'"
          :serial="selectedSerial"
          class="main-content"
        />
        <AnalysisReport 
          v-else-if="currentTab === 'analysis'"
          class="main-content"
        />
        <HistoryView
          v-else-if="currentTab === 'history'"
          class="main-content"
        />
      </keep-alive>
      
      <div v-if="currentTab === 'monitor' && !selectedSerial" class="empty-state">
        请连接 USB 设备并开启调试模式。
      </div>
    </main>
    </div>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-lg);
  gap: var(--spacing-lg);
}

header {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-lg);
  animation: fadeIn 0.5s ease-out;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

h1 {
  font-size: var(--font-2xl);
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  font-size: 1.5em;
  -webkit-text-fill-color: initial;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

.nav-tabs {
  display: flex;
  background: var(--bg-tertiary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xs);
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.tab-item {
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition-base);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.tab-icon {
  font-size: 1.1em;
}

.tab-text {
  font-size: var(--font-sm);
}

.tab-item:hover {
  color: var(--primary-color);
  background: var(--bg-primary);
}

.tab-item.active {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs);
  background: var(--bg-tertiary);
  border-radius: var(--radius-xl);
  padding-right: var(--spacing-sm);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: var(--font-md);
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 60px;
}

.user-name {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
}

.user-role {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  line-height: 1.2;
  text-transform: capitalize;
}

.logout-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 50%;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background: linear-gradient(135deg, var(--danger-color), #e53e3e);
  color: white;
  transform: scale(1.1);
}

.logout-btn:active {
  transform: scale(0.95);
}

.controls {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  flex-wrap: wrap;
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 2px solid var(--border-light);
}

.input-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}

.pkg-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--font-sm);
  transition: all var(--transition-fast);
}

.pkg-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.pkg-input::placeholder {
  color: var(--text-tertiary);
}

.dropdown-list {
  position: absolute;
  top: calc(100% + var(--spacing-xs));
  left: 0;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-xs);
  list-style: none;
  z-index: var(--z-dropdown);
  animation: slideIn 0.2s ease-out;
}

.dropdown-list li {
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  font-size: var(--font-sm);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.dropdown-list li:hover {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  transform: translateX(4px);
}

.pkg-sub {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.dropdown-list li:hover .pkg-sub {
  color: rgba(255, 255, 255, 0.8);
}

select {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-width: 180px;
}

select:hover {
  border-color: var(--primary-color);
}

select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

button {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-sm);
  font-weight: 600;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-md);
  white-space: nowrap;
}

button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

button:active {
  transform: translateY(0);
}

button.stop {
  background: linear-gradient(135deg, var(--danger-color), #e53e3e);
}

button.stop:hover {
  background: linear-gradient(135deg, #e53e3e, #c53030);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.main-content {
  flex: 1;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  animation: fadeIn 0.6s ease-out;
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  color: var(--text-tertiary);
  font-size: var(--font-lg);
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  text-align: center;
}

.empty-state::before {
  content: '📱';
  font-size: 64px;
  opacity: 0.5;
}

@media (max-width: 1024px) {
  .container {
    padding: var(--spacing-md);
    gap: var(--spacing-md);
  }
  
  header {
    padding: var(--spacing-md);
  }
  
  .header-top {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .nav-tabs {
    width: 100%;
    justify-content: center;
  }
  
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .input-wrapper {
    max-width: 100%;
  }
  
  select {
    width: 100%;
  }
  
  button {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .container {
    padding: var(--spacing-sm);
    gap: var(--spacing-sm);
  }
  
  header {
    padding: var(--spacing-sm);
  }
  
  h1 {
    font-size: var(--font-xl);
  }
  
  .nav-tabs {
    gap: 4px;
    padding: 4px;
  }
  
  .tab-item {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-xs);
  }
  
  .controls {
    gap: var(--spacing-sm);
  }
  
  select, .pkg-input {
    font-size: var(--font-xs);
    padding: 6px var(--spacing-sm);
  }
  
  button {
    padding: 6px var(--spacing-sm);
    font-size: var(--font-xs);
  }
}

@media (max-width: 480px) {
  .header-right {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .nav-tabs {
    flex-direction: column;
  }
  
  .tab-item {
    text-align: center;
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
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
