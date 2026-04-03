<template>
  <div class="notification-center">
    <div class="notification-bell" @click="togglePanel">
      <span class="bell-icon">🔔</span>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </div>

    <transition name="slide">
      <div v-if="showPanel" class="notification-panel">
        <div class="panel-header">
          <h3>通知中心</h3>
          <div class="header-actions">
            <button @click="markAllAsRead" class="action-btn" :disabled="unreadCount === 0">
              全部已读
            </button>
            <button @click="showSettings = true" class="action-btn">
              ⚙️ 设置
            </button>
            <button @click="showPanel = false" class="close-btn">×</button>
          </div>
        </div>

        <div class="panel-body">
          <div v-if="loading" class="loading">
            <div class="spinner"></div>
          </div>

          <div v-else-if="notifications.length === 0" class="empty-state">
            <div class="empty-icon">📭</div>
            <p>暂无通知</p>
          </div>

          <div v-else class="notification-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="[`priority-${notification.priority}`, { unread: !notification.read }]"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-icon">
                {{ getTypeIcon(notification.type) }}
              </div>
              
              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
              </div>

              <button
                @click.stop="deleteNotification(notification.id)"
                class="delete-btn"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <button @click="clearAll" class="clear-btn">
            清空所有通知
          </button>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showSettings" class="settings-modal" @click.self="showSettings = false">
        <div class="settings-content">
          <div class="settings-header">
            <h3>通知设置</h3>
            <button @click="showSettings = false" class="close-btn">×</button>
          </div>

          <div class="settings-body">
            <div class="settings-section">
              <h4>通知类型</h4>
              <div class="setting-item" v-for="(enabled, type) in config.enabled_types" :key="type">
                <label>
                  <input
                    type="checkbox"
                    v-model="config.enabled_types[type]"
                    @change="updateConfig"
                  />
                  {{ getTypeLabel(type) }}
                </label>
              </div>
            </div>

            <div class="settings-section">
              <h4>通知渠道</h4>
              <div class="setting-item" v-for="(enabled, channel) in config.enabled_channels" :key="channel">
                <label>
                  <input
                    type="checkbox"
                    v-model="config.enabled_channels[channel]"
                    @change="updateConfig"
                  />
                  {{ getChannelLabel(channel) }}
                </label>
              </div>
            </div>

            <div class="settings-section">
              <h4>阈值设置</h4>
              <div class="threshold-grid">
                <div class="threshold-item">
                  <label>FPS 低阈值</label>
                  <input
                    type="number"
                    v-model.number="config.thresholds.fps_low"
                    @change="updateConfig"
                    min="0"
                    max="60"
                  />
                </div>
                <div class="threshold-item">
                  <label>FPS 严重阈值</label>
                  <input
                    type="number"
                    v-model.number="config.thresholds.fps_critical"
                    @change="updateConfig"
                    min="0"
                    max="60"
                  />
                </div>
                <div class="threshold-item">
                  <label>CPU 高阈值 (%)</label>
                  <input
                    type="number"
                    v-model.number="config.thresholds.cpu_high"
                    @change="updateConfig"
                    min="0"
                    max="100"
                  />
                </div>
                <div class="threshold-item">
                  <label>CPU 严重阈值 (%)</label>
                  <input
                    type="number"
                    v-model.number="config.thresholds.cpu_critical"
                    @change="updateConfig"
                    min="0"
                    max="100"
                  />
                </div>
                <div class="threshold-item">
                  <label>内存高阈值 (MB)</label>
                  <input
                    type="number"
                    v-model.number="config.thresholds.memory_high"
                    @change="updateConfig"
                    min="0"
                  />
                </div>
                <div class="threshold-item">
                  <label>内存严重阈值 (MB)</label>
                  <input
                    type="number"
                    v-model.number="config.thresholds.memory_critical"
                    @change="updateConfig"
                    min="0"
                  />
                </div>
              </div>
            </div>

            <div class="settings-section">
              <h4>免打扰时段</h4>
              <div class="quiet-hours">
                <label>
                  <input
                    type="checkbox"
                    v-model="config.quiet_hours.enabled"
                    @change="updateConfig"
                  />
                  启用免打扰
                </label>
                <div v-if="config.quiet_hours.enabled" class="time-range">
                  <input
                    type="time"
                    v-model="config.quiet_hours.start"
                    @change="updateConfig"
                  />
                  <span>至</span>
                  <input
                    type="time"
                    v-model="config.quiet_hours.end"
                    @change="updateConfig"
                  />
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
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const showPanel = ref(false)
const showSettings = ref(false)
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)

const config = reactive({
  enabled_types: {},
  enabled_channels: {},
  thresholds: {},
  quiet_hours: {}
})

let ws = null

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/notifications`)
  
  ws.onopen = () => {
    console.log('Notification WebSocket connected')
  }
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    if (message.type === 'notification') {
      addNotification(message.data)
    } else if (message.type === 'connected') {
      unreadCount.value = message.unread_count
    }
  }
  
  ws.onerror = (error) => {
    console.error('Notification WebSocket error:', error)
  }
  
  ws.onclose = () => {
    setTimeout(() => {
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        connectWebSocket()
      }
    }, 3000)
  }
}

const addNotification = (notification) => {
  notifications.value.unshift(notification)
  if (!notification.read) {
    unreadCount.value++
  }
  
  showBrowserNotification(notification)
}

const showBrowserNotification = (notification) => {
  if (!('Notification' in window)) return
  if (Notification.permission !== 'granted') return
  
  new Notification(notification.title, {
    body: notification.message,
    icon: '/favicon.ico',
    tag: notification.id
  })
}

const fetchNotifications = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/notifications')
    notifications.value = res.data.notifications
    unreadCount.value = res.data.unread_count
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
  } finally {
    loading.value = false
  }
}

const fetchConfig = async () => {
  try {
    const res = await axios.get('/api/notifications/config')
    Object.assign(config, res.data)
  } catch (error) {
    console.error('Failed to fetch notification config:', error)
  }
}

const updateConfig = async () => {
  try {
    await axios.put('/api/notifications/config', config)
  } catch (error) {
    console.error('Failed to update notification config:', error)
  }
}

const togglePanel = () => {
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    fetchNotifications()
  }
}

const handleNotificationClick = async (notification) => {
  if (!notification.read) {
    await markAsRead(notification.id)
  }
}

const markAsRead = async (notificationId) => {
  try {
    await axios.post(`/api/notifications/${notificationId}/read`)
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification && !notification.read) {
      notification.read = true
      unreadCount.value--
    }
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
  }
}

const markAllAsRead = async () => {
  try {
    await axios.post('/api/notifications/mark-all-read')
    notifications.value.forEach(n => n.read = true)
    unreadCount.value = 0
  } catch (error) {
    console.error('Failed to mark all notifications as read:', error)
  }
}

const deleteNotification = async (notificationId) => {
  try {
    await axios.delete(`/api/notifications/${notificationId}`)
    const index = notifications.value.findIndex(n => n.id === notificationId)
    if (index !== -1) {
      const notification = notifications.value[index]
      if (!notification.read) {
        unreadCount.value--
      }
      notifications.value.splice(index, 1)
    }
  } catch (error) {
    console.error('Failed to delete notification:', error)
  }
}

const clearAll = async () => {
  if (!confirm('确定要清空所有通知吗？')) return
  
  try {
    await axios.delete('/api/notifications')
    notifications.value = []
    unreadCount.value = 0
  } catch (error) {
    console.error('Failed to clear notifications:', error)
  }
}

const getTypeIcon = (type) => {
  const icons = {
    'performance_alert': '⚠️',
    'device_status': '📱',
    'test_complete': '✅',
    'report_generated': '📊',
    'system_message': 'ℹ️',
    'collaboration': '👥',
    'threshold_breach': '🚨'
  }
  return icons[type] || '📢'
}

const getTypeLabel = (type) => {
  const labels = {
    'performance_alert': '性能告警',
    'device_status': '设备状态',
    'test_complete': '测试完成',
    'report_generated': '报告生成',
    'system_message': '系统消息',
    'collaboration': '协作通知',
    'threshold_breach': '阈值告警'
  }
  return labels[type] || type
}

const getChannelLabel = (channel) => {
  const labels = {
    'in_app': '应用内通知',
    'email': '邮件通知',
    'browser': '浏览器通知',
    'websocket': '实时推送'
  }
  return labels[channel] || channel
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  
  return date.toLocaleDateString()
}

const requestNotificationPermission = () => {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission()
  }
}

onMounted(() => {
  connectWebSocket()
  fetchConfig()
  requestNotificationPermission()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-bell {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.3s;
}

.notification-bell:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.bell-icon {
  font-size: 24px;
}

.badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #f56565;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.notification-panel {
  position: absolute;
  top: 100%;
  right: 0;
  width: 400px;
  max-height: 600px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  color: #2d3748;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-btn {
  padding: 6px 12px;
  background: #edf2f7;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: #e2e8f0;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #a0aec0;
  padding: 0;
  width: 24px;
  height: 24px;
  line-height: 1;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #a0aec0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: #f7fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.notification-item:hover {
  background: #edf2f7;
}

.notification-item.unread {
  background: #ebf8ff;
  border-left: 3px solid #4299e1;
}

.notification-item.priority-critical {
  border-left-color: #f56565;
}

.notification-item.priority-high {
  border-left-color: #ed8936;
}

.notification-icon {
  font-size: 24px;
  margin-right: 12px;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 14px;
  color: #4a5568;
  margin-bottom: 4px;
  word-wrap: break-word;
}

.notification-time {
  font-size: 12px;
  color: #a0aec0;
}

.delete-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #a0aec0;
  cursor: pointer;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.notification-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #f56565;
}

.panel-footer {
  padding: 12px 20px;
  border-top: 1px solid #e2e8f0;
}

.clear-btn {
  width: 100%;
  padding: 10px;
  background: #f56565;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.clear-btn:hover {
  background: #e53e3e;
}

.settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.settings-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.settings-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-header h3 {
  margin: 0;
  font-size: 20px;
}

.settings-body {
  padding: 20px;
}

.settings-section {
  margin-bottom: 24px;
}

.settings-section h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #2d3748;
}

.setting-item {
  margin-bottom: 8px;
}

.setting-item label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #4a5568;
}

.setting-item input[type="checkbox"] {
  margin-right: 8px;
}

.threshold-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.threshold-item {
  display: flex;
  flex-direction: column;
}

.threshold-item label {
  font-size: 13px;
  color: #718096;
  margin-bottom: 4px;
}

.threshold-item input {
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.quiet-hours {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.time-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-range input {
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.time-range span {
  color: #718096;
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.3s;
}

.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
