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
  <div class="app-container">
    <AuthForm v-if="!authState.isAuthenticated" />
    
    <div v-else class="app-layout">
      <header class="app-header">
        <div class="header-content">
          <div class="header-top">
            <div class="brand">
              <div class="brand-icon">📊</div>
              <div class="brand-text">
                <span class="brand-name">MobiPerf</span>
                <span class="brand-tagline">移动性能监控平台</span>
              </div>
            </div>
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
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                    <polyline points="16 17 21 12 16 7"></polyline>
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                  </svg>
                </button>
              </div>
              <NotificationCenter />
            </div>
          </div>
        
          <div class="control-bar" v-if="currentTab === 'monitor'">
            <select v-model="selectedSerial" class="device-select">
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

            <button @click="fetchDevices" class="btn-refresh">刷新设备</button>
            <button 
              @click="toggleMonitor" 
              :class="['btn-start', { 'btn-stop': isMonitoring }]" 
              :disabled="!selectedSerial && !isMonitoring"
            >
              {{ isMonitoring ? '停止测试' : '开始测试' }}
            </button>
          </div>
        </div>
      </header>

      <main class="app-main">
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
          <div class="empty-icon">📱</div>
          <div class="empty-title">请连接设备</div>
          <div class="empty-desc">连接 USB 设备并开启调试模式后，即可开始性能监控测试</div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-app);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border-bottom: 1px solid var(--border-light);
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: var(--spacing-4) var(--spacing-6);
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-6);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.brand-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  border-radius: var(--radius-lg);
  font-size: 20px;
  box-shadow: var(--shadow-md);
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-name {
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  background: linear-gradient(135deg, var(--primary-600), var(--primary-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.brand-tagline {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  font-weight: var(--font-normal);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.nav-tabs {
  display: flex;
  background: var(--gray-100);
  border-radius: var(--radius-xl);
  padding: var(--spacing-1);
  gap: var(--spacing-1);
}

.tab-item {
  padding: var(--spacing-2) var(--spacing-4);
  cursor: pointer;
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  transition: all var(--transition-base);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  border: none;
  background: transparent;
}

.tab-icon {
  font-size: 16px;
}

.tab-item:hover {
  color: var(--primary-600);
  background: var(--bg-primary);
}

.tab-item.active {
  background: var(--bg-primary);
  color: var(--primary-600);
  box-shadow: var(--shadow-sm);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2);
  padding-right: var(--spacing-3);
  background: var(--gray-50);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary-500), var(--accent-500));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-semibold);
  font-size: var(--font-base);
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 70px;
}

.user-name {
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  line-height: 1.3;
}

.user-role {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  line-height: 1.3;
  text-transform: capitalize;
}

.logout-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background: var(--danger-50);
  color: var(--danger-500);
}

.control-bar {
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: var(--spacing-3);
  align-items: center;
  flex-wrap: wrap;
}

.device-select {
  min-width: 200px;
  max-width: 280px;
}

.input-wrapper {
  position: relative;
  flex: 1;
  min-width: 240px;
  max-width: 420px;
}

.pkg-input {
  width: 100%;
}

.dropdown-list {
  position: absolute;
  top: calc(100% + var(--spacing-2));
  left: 0;
  width: 100%;
  max-height: 320px;
  overflow-y: auto;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-1);
  list-style: none;
  z-index: var(--z-dropdown);
  animation: slideUp var(--transition-base) ease-out;
}

.dropdown-list li {
  padding: var(--spacing-3) var(--spacing-4);
  cursor: pointer;
  font-size: var(--font-sm);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.dropdown-list li:hover {
  background: var(--primary-50);
  color: var(--primary-700);
}

.pkg-sub {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.dropdown-list li:hover .pkg-sub {
  color: var(--primary-500);
}

.btn-refresh {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
}

.btn-refresh:hover {
  background: var(--gray-50);
  border-color: var(--border-dark);
  transform: none;
}

.btn-start {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  box-shadow: var(--shadow-md);
  min-width: 100px;
}

.btn-start:hover {
  background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.btn-stop {
  background: linear-gradient(135deg, var(--danger-500), var(--danger-600));
}

.btn-stop:hover {
  background: linear-gradient(135deg, var(--danger-600), #b91c1c);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-6);
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

.main-content {
  flex: 1;
  background: var(--bg-primary);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
  overflow: hidden;
  animation: fadeIn var(--transition-slow) ease-out;
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 400px;
  color: var(--text-tertiary);
  font-size: var(--font-lg);
  gap: var(--spacing-4);
  padding: var(--spacing-8);
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gray-100);
  border-radius: var(--radius-2xl);
  font-size: 36px;
  margin-bottom: var(--spacing-2);
}

.empty-title {
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.empty-desc {
  font-size: var(--font-base);
  color: var(--text-tertiary);
  max-width: 320px;
  line-height: var(--leading-relaxed);
}

@media (max-width: 1024px) {
  .app-main {
    padding: var(--spacing-4);
  }
  
  .header-content {
    padding: var(--spacing-3) var(--spacing-4);
  }
  
  .header-top {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-4);
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .nav-tabs {
    flex: 1;
    justify-content: center;
  }
  
  .control-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .device-select {
    max-width: 100%;
  }
  
  .input-wrapper {
    max-width: 100%;
  }
  
  .main-content {
    border-radius: var(--radius-xl);
  }
}

@media (max-width: 768px) {
  .app-main {
    padding: var(--spacing-2);
  }
  
  .header-content {
    padding: var(--spacing-2) var(--spacing-3);
  }
  
  .brand-name {
    font-size: var(--font-lg);
  }
  
  .nav-tabs {
    gap: 2px;
    padding: 2px;
  }
  
  .tab-item {
    padding: var(--spacing-2) var(--spacing-3);
    font-size: var(--font-xs);
  }
  
  .tab-icon {
    font-size: 14px;
  }
  
  .user-info {
    display: none;
  }
  
  .control-bar {
    gap: var(--spacing-2);
  }
  
  .main-content {
    border-radius: var(--radius-lg);
  }
}

@media (max-width: 480px) {
  .app-main {
    padding: var(--spacing-1);
  }
  
  .header-content {
    padding: var(--spacing-2);
  }
  
  .header-right {
    flex-direction: column;
    gap: var(--spacing-3);
  }
  
  .nav-tabs {
    width: 100%;
    justify-content: space-between;
  }
  
  .tab-item {
    flex: 1;
    justify-content: center;
    padding: var(--spacing-2);
  }
  
  .tab-text {
    display: none;
  }
  
  .tab-icon {
    font-size: 18px;
  }
  
  .main-content {
    border-radius: var(--radius-md);
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

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
