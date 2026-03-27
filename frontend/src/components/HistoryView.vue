<template>
  <div class="history-view">
    <div class="header">
      <h2>历史测试记录</h2>
      <div class="filters">
        <input 
          v-model="searchQuery" 
          placeholder="搜索应用包名..." 
          class="search-input"
          @keyup.enter="handleSearch"
        >
        <button @click="handleSearch" class="search-btn">🔍 搜索</button>
        <button @click="loadSessions" class="refresh-btn">🔄 刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-message">
      ❌ {{ error }}
    </div>

    <div v-else-if="sessions.length === 0" class="no-data">
      <div class="no-data-icon">📊</div>
      <div class="no-data-text">暂无测试记录</div>
    </div>

    <div v-else class="sessions-list">
      <div 
        v-for="session in sessions" 
        :key="session.session_id" 
        class="session-card"
        @click="viewSessionDetail(session.session_id)"
      >
        <div class="session-header">
          <div class="session-title">
            <span class="app-package">{{ session.app_package || 'Unknown App' }}</span>
            <span class="session-status" :class="`status-${session.status}`">
              {{ getStatusText(session.status) }}
            </span>
          </div>
          <div class="session-time">{{ formatTime(session.start_time) }}</div>
        </div>

        <div class="session-body">
          <div class="info-row">
            <span class="info-label">📱 设备:</span>
            <span class="info-value">{{ session.device_model || 'Unknown' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">📦 包名:</span>
            <span class="info-value">{{ session.app_package || 'Unknown' }}</span>
          </div>
          <div class="info-row" v-if="session.duration">
            <span class="info-label">⏱️ 时长:</span>
            <span class="info-value">{{ formatDuration(session.duration) }}</span>
          </div>
          <div class="info-row" v-if="session.overall_score">
            <span class="info-label">📊 评分:</span>
            <span class="info-value score" :class="getScoreClass(session.overall_score)">
              {{ session.overall_score }}
            </span>
          </div>
        </div>

        <div class="session-actions">
          <button @click.stop="viewSessionDetail(session.session_id)" class="action-btn">
            📋 查看详情
          </button>
          <button @click.stop="deleteSession(session.session_id)" class="action-btn delete-btn">
            🗑️ 删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="sessions.length > 0" class="pagination">
      <button 
        :disabled="offset === 0" 
        @click="prevPage"
        class="page-btn"
      >
        上一页
      </button>
      <span class="page-info">第 {{ currentPage }} 页</span>
      <button 
        :disabled="sessions.length < limit"
        @click="nextPage"
        class="page-btn"
      >
        下一页
      </button>
    </div>

    <SessionDetailModal
      v-if="showDetailModal"
      :session-id="selectedSessionId"
      @close="closeDetailModal"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import SessionDetailModal from './SessionDetailModal.vue'

const sessions = ref([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const offset = ref(0)
const limit = ref(20)
const showDetailModal = ref(false)
const selectedSessionId = ref('')

const currentPage = computed(() => Math.floor(offset.value / limit.value) + 1)

const loadSessions = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.get('/api/sessions', {
      params: {
        limit: limit.value,
        offset: offset.value
      }
    })
    
    if (response.data.error) {
      error.value = response.data.error
    } else {
      sessions.value = response.data.sessions || []
    }
  } catch (err) {
    error.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    loadSessions()
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.post('/api/sessions/search', {
      app_package: searchQuery.value,
      limit: limit.value,
      offset: offset.value
    })
    
    if (response.data.error) {
      error.value = response.data.error
    } else {
      sessions.value = response.data.sessions || []
    }
  } catch (err) {
    error.value = err.message || '搜索失败'
  } finally {
    loading.value = false
  }
}

const viewSessionDetail = (sessionId) => {
  selectedSessionId.value = sessionId
  showDetailModal.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedSessionId.value = ''
}

const deleteSession = async (sessionId) => {
  if (!confirm('确定要删除此测试记录吗？')) {
    return
  }
  
  try {
    const response = await axios.delete(`/api/sessions/${sessionId}`)
    if (response.data.success) {
      await loadSessions()
    } else {
      alert('删除失败: ' + response.data.error)
    }
  } catch (err) {
    alert('删除失败: ' + err.message)
  }
}

const prevPage = () => {
  if (offset.value >= limit.value) {
    offset.value -= limit.value
    loadSessions()
  }
}

const nextPage = () => {
  offset.value += limit.value
  loadSessions()
}

const formatTime = (timeStr) => {
  if (!timeStr) return 'Unknown'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const formatDuration = (seconds) => {
  if (!seconds) return '0秒'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`
}

const getStatusText = (status) => {
  const statusMap = {
    'running': '运行中',
    'completed': '已完成',
    'error': '错误'
  }
  return statusMap[status] || '未知'
}

const getScoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 75) return 'score-good'
  if (score >= 60) return 'score-fair'
  return 'score-poor'
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.history-view {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 20px;
  overflow-y: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.filters {
  display: flex;
  gap: 10px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  width: 250px;
}

.search-btn, .refresh-btn {
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.search-btn:hover, .refresh-btn:hover {
  background: #66b1ff;
}

.loading {
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

.error-message {
  text-align: center;
  padding: 20px;
  color: #f56c6c;
  font-size: 16px;
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #909399;
}

.no-data-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-data-text {
  font-size: 18px;
}

.sessions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.session-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.3s;
}

.session-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
}

.session-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-package {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.session-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-running {
  background: #e3f2fd;
  color: #409eff;
}

.status-completed {
  background: #f1f8e9;
  color: #67c23a;
}

.status-error {
  background: #fee;
  color: #f56c6c;
}

.session-time {
  font-size: 13px;
  color: #909399;
}

.session-body {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 14px;
}

.info-label {
  color: #606266;
  margin-right: 8px;
}

.info-value {
  color: #303133;
  font-weight: 500;
}

.info-value.score {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.score-excellent {
  background: #f1f8e9;
  color: #67c23a;
}

.score-good {
  background: #e3f2fd;
  color: #409eff;
}

.score-fair {
  background: #fef9e7;
  color: #e6a23c;
}

.score-poor {
  background: #fee;
  color: #f56c6c;
}

.session-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 6px 12px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.delete-btn:hover {
  background: #fef0f0;
  border-color: #f56c6c;
  color: #f56c6c;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:disabled {
  background: #dcdfe6;
  cursor: not-allowed;
}

.page-btn:not(:disabled):hover {
  background: #66b1ff;
}

.page-info {
  font-size: 14px;
  color: #606266;
}
</style>
