<template>
  <div class="notification-center">
    <div class="notification-bell" @click.stop="togglePanel">
      <svg class="bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
      </svg>
      <span v-if="unreadCount > 0" class="badge">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </div>

    <transition name="slide-fade">
      <div v-if="showPanel" class="notification-panel" @click.stop>
        <div class="panel-header">
          <div class="header-title">
            <h3>通知中心</h3>
            <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }} 条未读</span>
          </div>
          <div class="header-actions">
            <button @click="markAllAsRead" class="action-btn" :disabled="unreadCount === 0">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              全部已读
            </button>
            <button @click="showSettings = true" class="action-btn settings-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </button>
            <button @click="showPanel = false" class="close-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        <div class="panel-body">
          <div v-if="loading" class="loading">
            <div class="spinner"></div>
          </div>

          <div v-else-if="notifications.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
            </div>
            <p class="empty-title">暂无通知</p>
            <p class="empty-desc">所有通知都将显示在这里</p>
          </div>

          <div v-else class="notification-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="[`priority-${notification.priority}`, { unread: !notification.read }]"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-icon" :class="`icon-${notification.type}`">
                <span v-html="getTypeIcon(notification.type)"></span>
              </div>
              
              <div class="notification-content">
                <div class="notification-header">
                  <div class="notification-title">{{ notification.title }}</div>
                  <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
                </div>
                <div class="notification-message">{{ notification.message }}</div>
              </div>

              <button
                @click.stop="deleteNotification(notification.id)"
                class="delete-btn"
                title="删除通知"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <button @click="clearAll" class="clear-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
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
            <button @click="showSettings = false" class="close-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="settings-body">
            <div class="settings-section">
              <h4>通知类型</h4>
              <div class="setting-item" v-for="(enabled, type) in config.enabled_types" :key="type">
                <label class="setting-label">
                  <input
                    type="checkbox"
                    v-model="config.enabled_types[type]"
                    @change="updateConfig"
                    class="setting-checkbox"
                  />
                  <span class="setting-text">{{ getTypeLabel(type) }}</span>
                </label>
              </div>
            </div>

            <div class="settings-section">
              <h4>通知渠道</h4>
              <div class="setting-item" v-for="(enabled, channel) in config.enabled_channels" :key="channel">
                <label class="setting-label">
                  <input
                    type="checkbox"
                    v-model="config.enabled_channels[channel]"
                    @change="updateConfig"
                    class="setting-checkbox"
                  />
                  <span class="setting-text">{{ getChannelLabel(channel) }}</span>
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
                <label class="setting-label">
                  <input
                    type="checkbox"
                    v-model="config.quiet_hours.enabled"
                    @change="updateConfig"
                    class="setting-checkbox"
                  />
                  <span class="setting-text">启用免打扰</span>
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
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/notifications`
    console.log('Connecting to notification WebSocket:', wsUrl)
    
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('Notification WebSocket connected successfully')
    }
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('Received notification message:', message)
        
        if (message.type === 'notification') {
          addNotification(message.data)
        } else if (message.type === 'connected') {
          unreadCount.value = message.unread_count || 0
        }
      } catch (error) {
        console.error('Failed to parse notification message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('Notification WebSocket error:', error)
    }
    
    ws.onclose = (event) => {
      console.log('Notification WebSocket closed:', event.code, event.reason)
      setTimeout(() => {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
          connectWebSocket()
        }
      }, 3000)
    }
  } catch (error) {
    console.error('Failed to create WebSocket connection:', error)
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
    console.log('Fetched notifications:', res.data)
    notifications.value = res.data.notifications || []
    unreadCount.value = res.data.unread_count || 0
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
    notifications.value = []
    unreadCount.value = 0
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
  console.log('Toggle notification panel, current state:', showPanel.value)
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    console.log('Panel opened, fetching notifications...')
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
    'performance_alert': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    'device_status': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>',
    'test_complete': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    'report_generated': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>',
    'system_message': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
    'collaboration': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
    'threshold_breach': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
  }
  return icons[type] || '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>'
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
  console.log('NotificationCenter component mounted')
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
  padding: var(--spacing-2);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-bell:hover {
  background: var(--gray-100);
}

.notification-bell:active {
  transform: scale(0.95);
}

.bell-icon {
  width: 24px;
  height: 24px;
  color: var(--text-secondary);
  transition: color var(--transition-fast);
}

.notification-bell:hover .bell-icon {
  color: var(--text-primary);
}

.badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--danger-500);
  color: white;
  font-size: 10px;
  font-weight: var(--font-bold);
  padding: 2px 6px;
  border-radius: var(--radius-full);
  min-width: 18px;
  text-align: center;
  box-shadow: var(--shadow-sm);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.notification-panel {
  position: absolute;
  top: calc(100% + var(--spacing-2));
  right: 0;
  width: 420px;
  max-height: 600px;
  background: var(--bg-primary);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-2xl);
  border: 1px solid var(--border-light);
  z-index: var(--z-dropdown);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.panel-header h3 {
  margin: 0;
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.unread-badge {
  font-size: var(--font-xs);
  color: var(--primary-600);
  background: var(--primary-50);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-weight: var(--font-medium);
}

.header-actions {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}

.action-btn {
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--bg-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-xs);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  color: var(--text-secondary);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.action-btn:hover:not(:disabled) {
  background: var(--gray-50);
  border-color: var(--border-dark);
  color: var(--text-primary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.settings-btn {
  padding: var(--spacing-2);
}

.settings-btn svg {
  width: 16px;
  height: 16px;
}

.close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  padding: var(--spacing-1);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.close-btn:hover {
  background: var(--gray-100);
  color: var(--text-primary);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-3);
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-12);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: var(--spacing-12) var(--spacing-6);
}

.empty-icon {
  margin-bottom: var(--spacing-4);
}

.empty-icon svg {
  width: 64px;
  height: 64px;
  color: var(--gray-300);
}

.empty-title {
  font-size: var(--font-base);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-1);
}

.empty-desc {
  font-size: var(--font-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: var(--spacing-3);
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  border: 1px solid transparent;
}

.notification-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-light);
  transform: translateX(4px);
}

.notification-item.unread {
  background: var(--primary-50);
  border-left: 3px solid var(--primary-500);
}

.notification-item.priority-critical {
  border-left-color: var(--danger-500);
  background: var(--danger-50);
}

.notification-item.priority-high {
  border-left-color: var(--warning-500);
}

.notification-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--spacing-3);
  flex-shrink: 0;
}

.notification-icon svg {
  width: 20px;
  height: 20px;
}

.icon-performance_alert {
  background: var(--warning-50);
  color: var(--warning-600);
}

.icon-device_status {
  background: var(--primary-50);
  color: var(--primary-600);
}

.icon-test_complete {
  background: var(--success-50);
  color: var(--success-600);
}

.icon-report_generated {
  background: var(--primary-50);
  color: var(--primary-600);
}

.icon-system_message {
  background: var(--gray-100);
  color: var(--gray-600);
}

.icon-collaboration {
  background: var(--primary-50);
  color: var(--primary-600);
}

.icon-threshold_breach {
  background: var(--danger-50);
  color: var(--danger-600);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-1);
  gap: var(--spacing-2);
}

.notification-title {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  font-size: var(--font-sm);
  flex: 1;
}

.notification-message {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-1);
  word-wrap: break-word;
  line-height: var(--leading-relaxed);
}

.notification-time {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
}

.delete-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  padding: var(--spacing-1);
  opacity: 0;
  transition: all var(--transition-fast);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.notification-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--danger-50);
  color: var(--danger-600);
}

.panel-footer {
  padding: var(--spacing-3);
  border-top: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.clear-btn {
  width: 100%;
  padding: var(--spacing-3);
  background: var(--danger-500);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
}

.clear-btn svg {
  width: 16px;
  height: 16px;
}

.clear-btn:hover {
  background: var(--danger-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
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
  animation: fadeIn var(--transition-base) ease-out;
}

.settings-content {
  background: var(--bg-primary);
  border-radius: var(--radius-2xl);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-2xl);
  animation: scaleIn var(--transition-slow) ease-out;
  margin: auto;
}

.settings-header {
  padding: var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-header h3 {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.settings-body {
  padding: var(--spacing-6);
}

.settings-section {
  margin-bottom: var(--spacing-6);
}

.settings-section:last-child {
  margin-bottom: 0;
}

.settings-section h4 {
  margin: 0 0 var(--spacing-3);
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.setting-item {
  margin-bottom: var(--spacing-2);
}

.setting-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.setting-label:hover {
  background: var(--gray-50);
}

.setting-checkbox {
  margin-right: var(--spacing-3);
  cursor: pointer;
}

.setting-text {
  flex: 1;
}

.threshold-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-4);
}

.threshold-item {
  display: flex;
  flex-direction: column;
}

.threshold-item label {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-2);
  font-weight: var(--font-medium);
}

.threshold-item input {
  padding: var(--spacing-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  transition: all var(--transition-fast);
}

.threshold-item input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.quiet-hours {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.time-range {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.time-range input {
  padding: var(--spacing-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  flex: 1;
}

.time-range input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.time-range span {
  color: var(--text-tertiary);
  font-size: var(--font-sm);
}

.slide-fade-enter-active {
  animation: slideFadeIn var(--transition-base) ease-out;
}

.slide-fade-leave-active {
  animation: slideFadeOut var(--transition-base) ease-in;
}

@keyframes slideFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideFadeOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity var(--transition-base);
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 768px) {
  .notification-panel {
    position: fixed;
    top: 60px;
    left: var(--spacing-2);
    right: var(--spacing-2);
    width: auto;
    max-height: calc(100vh - 80px);
  }
  
  .threshold-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .notification-panel {
    top: 50px;
    left: var(--spacing-1);
    right: var(--spacing-1);
    max-height: calc(100vh - 70px);
  }
  
  .panel-header {
    padding: var(--spacing-3);
  }
  
  .header-title {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-2);
  }
  
  .header-actions {
    flex-wrap: wrap;
  }
  
  .action-btn {
    flex: 1;
    min-width: 80px;
  }
  
  .settings-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .settings-header,
  .settings-body {
    padding: var(--spacing-4);
  }
  
  .threshold-grid {
    gap: var(--spacing-3);
  }
}
</style>
