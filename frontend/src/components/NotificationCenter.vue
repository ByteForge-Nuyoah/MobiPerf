<template>
  <div class="notification-center">
    <div class="notification-trigger" @click="togglePanel">
      <div class="bell-container">
        <svg class="bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <span v-if="unreadCount > 0" class="badge">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </div>
    </div>

    <transition name="panel">
      <div v-if="showPanel" class="notification-panel">
        <div class="panel-header">
          <div class="header-left">
            <h3>通知中心</h3>
            <span class="unread-badge" v-if="unreadCount > 0">{{ unreadCount }} 条未读</span>
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
          <div v-if="loading" class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="error" class="error-state">
            <div class="error-icon">⚠️</div>
            <h4>{{ error }}</h4>
            <button @click="fetchNotifications" class="retry-btn">重试</button>
          </div>

          <div v-else-if="notifications.length === 0" class="empty-state">
            <div class="empty-illustration">
              <svg viewBox="0 0 200 200" fill="none">
                <circle cx="100" cy="100" r="80" fill="#f0f4f8"/>
                <path d="M100 60 L100 100 L130 100" stroke="#94a3b8" stroke-width="4" stroke-linecap="round"/>
                <circle cx="100" cy="100" r="60" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="8 4"/>
                <rect x="70" y="130" width="60" height="8" rx="4" fill="#cbd5e1"/>
              </svg>
            </div>
            <h4>暂无通知</h4>
            <p>当有新的通知时，您会在这里看到</p>
          </div>

          <div v-else class="notification-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-card"
              :class="[`type-${notification.type}`, { unread: !notification.read }]"
              @click="handleNotificationClick(notification)"
            >
              <div class="card-indicator"></div>
              
              <div class="card-icon">
                <component :is="getTypeIcon(notification.type)" />
              </div>
              
              <div class="card-content">
                <div class="card-header">
                  <span class="card-title">{{ notification.title }}</span>
                  <span class="card-time">{{ formatTime(notification.created_at) }}</span>
                </div>
                <p class="card-message">{{ notification.message }}</p>
                <div class="card-meta" v-if="notification.priority">
                  <span class="priority-tag" :class="`priority-${notification.priority}`">
                    {{ getPriorityLabel(notification.priority) }}
                  </span>
                </div>
              </div>

              <div class="card-actions">
                <button
                  @click.stop="deleteNotification(notification.id)"
                  class="delete-btn"
                  title="删除"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <button @click="clearAll" class="clear-all-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            清空所有通知
          </button>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showSettings" class="settings-overlay" @click.self="showSettings = false">
        <div class="settings-modal">
          <div class="modal-header">
            <h3>通知设置</h3>
            <button @click="showSettings = false" class="modal-close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="settings-group">
              <div class="group-header">
                <h4>通知类型</h4>
                <span class="group-desc">选择您想接收的通知类型</span>
              </div>
              <div class="toggle-list">
                <div class="toggle-item" v-for="(enabled, type) in config.enabled_types" :key="type">
                  <div class="toggle-info">
                    <span class="toggle-icon">{{ getTypeEmoji(type) }}</span>
                    <span class="toggle-label">{{ getTypeLabel(type) }}</span>
                  </div>
                  <label class="toggle-switch">
                    <input
                      type="checkbox"
                      v-model="config.enabled_types[type]"
                      @change="updateConfig"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>

            <div class="settings-group">
              <div class="group-header">
                <h4>通知渠道</h4>
                <span class="group-desc">选择通知的接收方式</span>
              </div>
              <div class="toggle-list">
                <div class="toggle-item" v-for="(enabled, channel) in config.enabled_channels" :key="channel">
                  <div class="toggle-info">
                    <span class="toggle-icon">{{ getChannelEmoji(channel) }}</span>
                    <span class="toggle-label">{{ getChannelLabel(channel) }}</span>
                  </div>
                  <label class="toggle-switch">
                    <input
                      type="checkbox"
                      v-model="config.enabled_channels[channel]"
                      @change="updateConfig"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>

            <div class="settings-group">
              <div class="group-header">
                <h4>阈值设置</h4>
                <span class="group-desc">配置性能告警的触发阈值</span>
              </div>
              <div class="threshold-grid">
                <div class="threshold-card">
                  <div class="threshold-header">
                    <span class="threshold-icon">🎮</span>
                    <span class="threshold-title">FPS 阈值</span>
                  </div>
                  <div class="threshold-inputs">
                    <div class="input-group">
                      <label>低</label>
                      <input
                        type="number"
                        v-model.number="config.thresholds.fps_low"
                        @change="updateConfig"
                        min="0"
                        max="60"
                      />
                    </div>
                    <div class="input-group">
                      <label>严重</label>
                      <input
                        type="number"
                        v-model.number="config.thresholds.fps_critical"
                        @change="updateConfig"
                        min="0"
                        max="60"
                      />
                    </div>
                  </div>
                </div>

                <div class="threshold-card">
                  <div class="threshold-header">
                    <span class="threshold-icon">💻</span>
                    <span class="threshold-title">CPU 阈值</span>
                  </div>
                  <div class="threshold-inputs">
                    <div class="input-group">
                      <label>高 (%)</label>
                      <input
                        type="number"
                        v-model.number="config.thresholds.cpu_high"
                        @change="updateConfig"
                        min="0"
                        max="100"
                      />
                    </div>
                    <div class="input-group">
                      <label>严重 (%)</label>
                      <input
                        type="number"
                        v-model.number="config.thresholds.cpu_critical"
                        @change="updateConfig"
                        min="0"
                        max="100"
                      />
                    </div>
                  </div>
                </div>

                <div class="threshold-card">
                  <div class="threshold-header">
                    <span class="threshold-icon">📊</span>
                    <span class="threshold-title">内存阈值</span>
                  </div>
                  <div class="threshold-inputs">
                    <div class="input-group">
                      <label>高 (MB)</label>
                      <input
                        type="number"
                        v-model.number="config.thresholds.memory_high"
                        @change="updateConfig"
                        min="0"
                      />
                    </div>
                    <div class="input-group">
                      <label>严重 (MB)</label>
                      <input
                        type="number"
                        v-model.number="config.thresholds.memory_critical"
                        @change="updateConfig"
                        min="0"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="settings-group">
              <div class="group-header">
                <h4>免打扰时段</h4>
                <span class="group-desc">在指定时间段内不发送通知</span>
              </div>
              <div class="quiet-hours-card">
                <div class="quiet-toggle">
                  <span class="toggle-icon">🌙</span>
                  <span class="toggle-label">启用免打扰</span>
                  <label class="toggle-switch">
                    <input
                      type="checkbox"
                      v-model="config.quiet_hours.enabled"
                      @change="updateConfig"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
                <div v-if="config.quiet_hours.enabled" class="time-picker">
                  <div class="time-input">
                    <label>开始时间</label>
                    <input
                      type="time"
                      v-model="config.quiet_hours.start"
                      @change="updateConfig"
                    />
                  </div>
                  <div class="time-separator">—</div>
                  <div class="time-input">
                    <label>结束时间</label>
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
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, h } from 'vue'
import axios from 'axios'

const showPanel = ref(false)
const showSettings = ref(false)
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const error = ref(null)

const defaultConfig = {
  enabled_types: {
    'performance_alert': true,
    'device_status': true,
    'test_complete': true,
    'report_generated': true,
    'system_message': true,
    'collaboration': true,
    'threshold_breach': true
  },
  enabled_channels: {
    'in_app': true,
    'email': false,
    'browser': false,
    'websocket': true
  },
  thresholds: {
    fps_low: 30,
    fps_critical: 20,
    cpu_high: 80,
    cpu_critical: 95,
    memory_high: 500,
    memory_critical: 800
  },
  quiet_hours: {
    enabled: false,
    start: '22:00',
    end: '08:00'
  }
}

const config = reactive({ ...defaultConfig })

let ws = null
let wsConnected = false

const connectWebSocket = () => {
  if (wsConnected) return
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/notifications`
  
  try {
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('Notification WebSocket connected')
      wsConnected = true
    }
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      
      if (message.type === 'notification') {
        addNotification(message.data)
      } else if (message.type === 'connected') {
        unreadCount.value = message.unread_count || 0
      }
    }
    
    ws.onerror = (error) => {
      console.error('Notification WebSocket error:', error)
      wsConnected = false
    }
    
    ws.onclose = () => {
      wsConnected = false
      setTimeout(() => {
        if (!wsConnected) {
          connectWebSocket()
        }
      }, 3000)
    }
  } catch (e) {
    console.error('Failed to create WebSocket:', e)
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
  error.value = null
  try {
    const res = await axios.get('/api/notifications/', { timeout: 5000 })
    notifications.value = res.data.notifications || []
    unreadCount.value = res.data.unread_count || 0
  } catch (err) {
    console.error('Failed to fetch notifications:', err)
    error.value = '加载失败，请重试'
    notifications.value = []
    unreadCount.value = 0
  } finally {
    loading.value = false
  }
}

const fetchConfig = async () => {
  try {
    const res = await axios.get('/api/notifications/config', { timeout: 5000 })
    if (res.data) {
      Object.assign(config, defaultConfig, res.data)
    }
  } catch (err) {
    console.error('Failed to fetch notification config:', err)
    Object.assign(config, defaultConfig)
  }
}

const updateConfig = async () => {
  try {
    await axios.put('/api/notifications/config', config, { timeout: 5000 })
  } catch (err) {
    console.error('Failed to update notification config:', err)
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
    await axios.delete('/api/notifications/')
    notifications.value = []
    unreadCount.value = 0
  } catch (error) {
    console.error('Failed to clear notifications:', error)
  }
}

const getTypeIcon = (type) => {
  const icons = {
    'performance_alert': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { d: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z' }),
      h('line', { x1: '12', y1: '9', x2: '12', y2: '13' }),
      h('line', { x1: '12', y1: '17', x2: '12.01', y2: '17' })
    ]),
    'device_status': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('rect', { x: '5', y: '2', width: '14', height: '20', rx: '2', ry: '2' }),
      h('line', { x1: '12', y1: '18', x2: '12.01', y2: '18' })
    ]),
    'test_complete': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { d: 'M22 11.08V12a10 10 0 1 1-5.93-9.14' }),
      h('polyline', { points: '22 4 12 14.01 9 11.01' })
    ]),
    'report_generated': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
      h('polyline', { points: '14 2 14 8 20 8' }),
      h('line', { x1: '16', y1: '13', x2: '8', y2: '13' }),
      h('line', { x1: '16', y1: '17', x2: '8', y2: '17' }),
      h('polyline', { points: '10 9 9 9 8 9' })
    ]),
    'system_message': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('circle', { cx: '12', cy: '12', r: '10' }),
      h('line', { x1: '12', y1: '16', x2: '12', y2: '12' }),
      h('line', { x1: '12', y1: '8', x2: '12.01', y2: '8' })
    ]),
    'collaboration': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { d: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2' }),
      h('circle', { cx: '9', cy: '7', r: '4' }),
      h('path', { d: 'M23 21v-2a4 4 0 0 0-3-3.87' }),
      h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' })
    ]),
    'threshold_breach': () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('polygon', { points: '7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2' }),
      h('line', { x1: '12', y1: '8', x2: '12', y2: '12' }),
      h('line', { x1: '12', y1: '16', x2: '12.01', y2: '16' })
    ])
  }
  return icons[type] || icons['system_message']
}

const getTypeEmoji = (type) => {
  const emojis = {
    'performance_alert': '⚠️',
    'device_status': '📱',
    'test_complete': '✅',
    'report_generated': '📊',
    'system_message': 'ℹ️',
    'collaboration': '👥',
    'threshold_breach': '🚨'
  }
  return emojis[type] || '📢'
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

const getChannelEmoji = (channel) => {
  const emojis = {
    'in_app': '📱',
    'email': '📧',
    'browser': '🌐',
    'websocket': '⚡'
  }
  return emojis[channel] || '📡'
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

const getPriorityLabel = (priority) => {
  const labels = {
    'critical': '严重',
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[priority] || priority
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

.notification-trigger {
  cursor: pointer;
  padding: 8px;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.notification-trigger:hover {
  background: rgba(102, 126, 234, 0.1);
}

.bell-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bell-icon {
  width: 24px;
  height: 24px;
  color: #4a5568;
  transition: color 0.2s ease;
}

.notification-trigger:hover .bell-icon {
  color: #667eea;
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 12px;
  min-width: 18px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(245, 101, 101, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.notification-panel {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 420px;
  max-height: 580px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.unread-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.settings-btn {
  padding: 8px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.close-btn:hover {
  opacity: 1;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8fafc;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
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

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #64748b;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-state h4 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #334155;
}

.retry-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.empty-illustration {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
}

.empty-state h4 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #334155;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-card {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  background: white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.notification-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notification-card.unread {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

.notification-card.unread .card-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px 0 0 4px;
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 10px;
  margin-right: 12px;
  flex-shrink: 0;
}

.card-icon svg {
  width: 20px;
  height: 20px;
  color: #667eea;
}

.notification-card.type-performance_alert .card-icon,
.notification-card.type-threshold_breach .card-icon {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.notification-card.type-performance_alert .card-icon svg,
.notification-card.type-threshold_breach .card-icon svg {
  color: #ef4444;
}

.notification-card.type-test_complete .card-icon {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.notification-card.type-test_complete .card-icon svg {
  color: #22c55e;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

.card-title {
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}

.card-time {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
  margin-left: 8px;
}

.card-message {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 8px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: 8px;
}

.priority-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.priority-tag.priority-critical {
  background: #fef2f2;
  color: #dc2626;
}

.priority-tag.priority-high {
  background: #fff7ed;
  color: #ea580c;
}

.priority-tag.priority-medium {
  background: #fefce8;
  color: #ca8a04;
}

.priority-tag.priority-low {
  background: #f0fdf4;
  color: #16a34a;
}

.card-actions {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.delete-btn {
  background: none;
  border: none;
  padding: 6px;
  cursor: pointer;
  color: #94a3b8;
  border-radius: 6px;
  transition: all 0.2s ease;
  opacity: 0;
}

.notification-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fef2f2;
  color: #ef4444;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.panel-footer {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #e2e8f0;
}

.clear-all-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: none;
  border-radius: 10px;
  color: #dc2626;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-all-btn svg {
  width: 18px;
  height: 18px;
}

.clear-all-btn:hover {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
}

.settings-overlay {
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
  z-index: 2000;
  padding: 20px;
}

.settings-modal {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 640px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  padding: 24px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
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

.settings-group {
  margin-bottom: 28px;
}

.settings-group:last-child {
  margin-bottom: 0;
}

.group-header {
  margin-bottom: 16px;
}

.group-header h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.group-desc {
  font-size: 13px;
  color: #64748b;
}

.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toggle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  transition: background 0.2s ease;
}

.toggle-item:hover {
  background: #f1f5f9;
}

.toggle-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-icon {
  font-size: 20px;
}

.toggle-label {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #cbd5e1;
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-switch input:checked + .toggle-slider {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.threshold-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.threshold-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
}

.threshold-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.threshold-icon {
  font-size: 20px;
}

.threshold-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.threshold-inputs {
  display: flex;
  gap: 12px;
}

.input-group {
  flex: 1;
}

.input-group label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.input-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.quiet-hours-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
}

.quiet-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quiet-toggle .toggle-icon {
  font-size: 20px;
}

.quiet-toggle .toggle-label {
  flex: 1;
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.time-picker {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.time-input {
  flex: 1;
}

.time-input label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.time-input input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.time-input input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.time-separator {
  color: #94a3b8;
  font-size: 18px;
  margin-top: 20px;
}

.panel-enter-active, .panel-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-enter-from, .panel-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.modal-enter-active, .modal-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .settings-modal,
.modal-leave-to .settings-modal {
  transform: scale(0.95) translateY(20px);
}

@media (max-width: 1024px) {
  .notification-panel {
    width: 380px;
    max-height: 520px;
  }
  
  .settings-modal {
    max-width: 580px;
  }
  
  .threshold-grid {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }
}

@media (max-width: 768px) {
  .notification-panel {
    position: fixed;
    top: 0;
    right: 0;
    left: 0;
    bottom: 0;
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
    box-shadow: none;
  }
  
  .panel-header {
    padding: 16px 20px;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .header-left h3 {
    font-size: 16px;
  }
  
  .unread-badge {
    font-size: 11px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .action-btn {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .action-btn svg {
    width: 14px;
    height: 14px;
  }
  
  .panel-body {
    padding: 12px;
  }
  
  .notification-card {
    padding: 12px;
  }
  
  .card-icon {
    width: 36px;
    height: 36px;
  }
  
  .card-icon svg {
    width: 18px;
    height: 18px;
  }
  
  .card-title {
    font-size: 13px;
  }
  
  .card-message {
    font-size: 12px;
  }
  
  .card-time {
    font-size: 11px;
  }
  
  .panel-footer {
    padding: 12px 20px;
  }
  
  .clear-all-btn {
    padding: 10px;
    font-size: 13px;
  }
  
  .settings-overlay {
    padding: 0;
  }
  
  .settings-modal {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .modal-header {
    padding: 16px 20px;
  }
  
  .modal-header h3 {
    font-size: 18px;
  }
  
  .modal-body {
    padding: 16px 20px;
  }
  
  .settings-group {
    margin-bottom: 20px;
  }
  
  .group-header h4 {
    font-size: 15px;
  }
  
  .group-desc {
    font-size: 12px;
  }
  
  .toggle-item {
    padding: 10px 12px;
  }
  
  .toggle-icon {
    font-size: 18px;
  }
  
  .toggle-label {
    font-size: 13px;
  }
  
  .threshold-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .threshold-card {
    padding: 12px;
  }
  
  .threshold-header {
    margin-bottom: 10px;
  }
  
  .threshold-icon {
    font-size: 18px;
  }
  
  .threshold-title {
    font-size: 13px;
  }
  
  .threshold-inputs {
    gap: 8px;
  }
  
  .input-group label {
    font-size: 11px;
  }
  
  .input-group input {
    padding: 6px 10px;
    font-size: 13px;
  }
  
  .quiet-hours-card {
    padding: 12px;
  }
  
  .quiet-toggle .toggle-icon {
    font-size: 18px;
  }
  
  .quiet-toggle .toggle-label {
    font-size: 13px;
  }
  
  .time-picker {
    flex-direction: column;
    gap: 12px;
    margin-top: 12px;
    padding-top: 12px;
  }
  
  .time-separator {
    display: none;
  }
  
  .time-input input {
    padding: 8px 10px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .notification-trigger {
    padding: 6px;
  }
  
  .bell-icon {
    width: 20px;
    height: 20px;
  }
  
  .badge {
    font-size: 10px;
    padding: 2px 5px;
    min-width: 16px;
  }
  
  .panel-header {
    padding: 12px 16px;
  }
  
  .header-left h3 {
    font-size: 15px;
  }
  
  .action-btn {
    padding: 6px 8px;
    font-size: 11px;
    gap: 4px;
  }
  
  .panel-body {
    padding: 8px;
  }
  
  .notification-card {
    padding: 10px;
    flex-direction: column;
  }
  
  .card-icon {
    width: 32px;
    height: 32px;
    margin-right: 0;
    margin-bottom: 8px;
  }
  
  .card-content {
    width: 100%;
  }
  
  .card-header {
    flex-direction: column;
    gap: 4px;
  }
  
  .card-time {
    margin-left: 0;
  }
  
  .card-actions {
    margin-left: 0;
    margin-top: 8px;
    width: 100%;
    justify-content: flex-end;
  }
  
  .delete-btn {
    opacity: 1;
  }
  
  .panel-footer {
    padding: 10px 16px;
  }
  
  .clear-all-btn {
    padding: 8px;
    font-size: 12px;
  }
  
  .clear-all-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .modal-header {
    padding: 12px 16px;
  }
  
  .modal-header h3 {
    font-size: 16px;
  }
  
  .modal-body {
    padding: 12px 16px;
  }
  
  .toggle-item {
    padding: 8px 10px;
  }
  
  .toggle-switch {
    width: 40px;
    height: 22px;
  }
  
  .toggle-slider:before {
    height: 16px;
    width: 16px;
  }
  
  .toggle-switch input:checked + .toggle-slider:before {
    transform: translateX(18px);
  }
}
</style>
