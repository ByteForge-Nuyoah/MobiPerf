<template>
  <div class="history-container">
    <div class="history-header">
      <div class="header-left">
        <h2 class="header-title">历史测试记录</h2>
        <p class="header-subtitle">查看和管理您的性能测试历史</p>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <input 
            v-model="searchQuery" 
            placeholder="搜索应用包名..." 
            class="search-input"
            @keyup.enter="handleSearch"
          >
        </div>
        <button @click="handleSearch" class="action-btn primary-btn">
          <span class="btn-icon">🔍</span>
          <span class="btn-text">搜索</span>
        </button>
        <button @click="loadSessions" class="action-btn secondary-btn">
          <span class="btn-icon">🔄</span>
          <span class="btn-text">刷新</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <span class="error-icon">❌</span>
      <span class="error-text">{{ error }}</span>
    </div>

    <div v-else-if="sessions.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-title">暂无测试记录</div>
      <div class="empty-desc">开始您的第一次性能测试吧</div>
    </div>

    <div v-else class="sessions-grid">
      <div 
        v-for="session in sessions" 
        :key="session.session_id" 
        class="session-card"
        @click="viewSessionDetail(session.session_id)"
      >
        <div class="card-header">
          <div class="card-title">
            <span class="app-icon">📱</span>
            <span class="app-name">{{ session.app_package || 'Unknown App' }}</span>
          </div>
          <span class="session-status" :class="`status-${session.status}`">
            {{ getStatusText(session.status) }}
          </span>
        </div>

        <div class="card-body">
          <div class="info-item">
            <span class="info-icon">📱</span>
            <span class="info-label">设备</span>
            <span class="info-value">{{ session.device_model || 'Unknown' }}</span>
          </div>
          <div class="info-item">
            <span class="info-icon">📦</span>
            <span class="info-label">包名</span>
            <span class="info-value">{{ session.app_package || 'Unknown' }}</span>
          </div>
          <div class="info-item" v-if="session.duration">
            <span class="info-icon">⏱️</span>
            <span class="info-label">时长</span>
            <span class="info-value">{{ formatDuration(session.duration) }}</span>
          </div>
          <div class="info-item" v-if="session.overall_score">
            <span class="info-icon">📊</span>
            <span class="info-label">评分</span>
            <span class="info-value score-badge" :class="getScoreClass(session.overall_score)">
              {{ session.overall_score }}
            </span>
          </div>
        </div>

        <div class="card-footer">
          <span class="session-time">{{ formatTime(session.start_time) }}</span>
          <div class="card-actions">
            <button @click.stop="viewSessionDetail(session.session_id)" class="card-btn view-btn">
              查看详情
            </button>
            <button @click.stop="deleteSession(session.session_id)" class="card-btn delete-btn">
              删除
            </button>
          </div>
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
.history-container {
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-5) var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.header-title {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.header-subtitle {
  margin: 0;
  font-size: var(--font-sm);
  color: var(--text-tertiary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
}

.search-input {
  width: 260px;
  padding: var(--spacing-2) var(--spacing-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
}

.primary-btn {
  background: var(--primary-500);
  color: white;
  border-color: var(--primary-500);
}

.primary-btn:hover {
  background: var(--primary-600);
  border-color: var(--primary-600);
}

.secondary-btn {
  background: var(--bg-primary);
  color: var(--text-secondary);
}

.secondary-btn:hover {
  background: var(--gray-50);
  color: var(--text-primary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  gap: var(--spacing-4);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  color: var(--text-tertiary);
  font-size: var(--font-sm);
}

.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-6);
  color: var(--danger-500);
  font-size: var(--font-base);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  gap: var(--spacing-3);
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.empty-desc {
  font-size: var(--font-sm);
  color: var(--text-tertiary);
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--spacing-4);
  padding: var(--spacing-5) var(--spacing-6);
}

.session-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: all var(--transition-base);
}

.session-card:hover {
  border-color: var(--primary-200);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-light);
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.app-icon {
  font-size: 18px;
}

.app-name {
  font-weight: var(--font-semibold);
  font-size: var(--font-base);
  color: var(--text-primary);
}

.session-status {
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: var(--font-medium);
}

.status-running {
  background: var(--primary-50);
  color: var(--primary-600);
}

.status-completed {
  background: var(--success-50);
  color: var(--success-600);
}

.status-error {
  background: var(--danger-50);
  color: var(--danger-600);
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-sm);
}

.info-icon {
  font-size: 14px;
  opacity: 0.7;
}

.info-label {
  color: var(--text-tertiary);
  min-width: 40px;
}

.info-value {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.score-badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-md);
  font-weight: var(--font-semibold);
}

.score-excellent {
  background: var(--success-50);
  color: var(--success-600);
}

.score-good {
  background: var(--primary-50);
  color: var(--primary-600);
}

.score-fair {
  background: var(--warning-50);
  color: var(--warning-600);
}

.score-poor {
  background: var(--danger-50);
  color: var(--danger-600);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--border-light);
}

.session-time {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.card-actions {
  display: flex;
  gap: var(--spacing-2);
}

.card-btn {
  padding: var(--spacing-2) var(--spacing-4);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-size: var(--font-xs);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.view-btn {
  background: var(--primary-500);
  color: white;
  border-color: var(--primary-500);
}

.view-btn:hover {
  background: var(--primary-600);
  border-color: var(--primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.delete-btn {
  background: var(--bg-primary);
  color: var(--danger-600);
  border-color: var(--danger-300);
}

.delete-btn:hover {
  background: var(--danger-500);
  color: white;
  border-color: var(--danger-500);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-4);
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-light);
}

.page-btn {
  padding: var(--spacing-2) var(--spacing-5);
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) {
  background: var(--primary-50);
  border-color: var(--primary-500);
  color: var(--primary-600);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .history-header {
    padding: var(--spacing-4);
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
  }
  
  .action-btn {
    width: 100%;
    justify-content: center;
  }
  
  .sessions-grid {
    padding: var(--spacing-4);
    grid-template-columns: 1fr;
  }
  
  .pagination {
    padding: var(--spacing-3) var(--spacing-4);
  }
}

@media (max-width: 480px) {
  .btn-text {
    display: none;
  }
  
  .card-footer {
    flex-direction: column;
    gap: var(--spacing-2);
    align-items: stretch;
  }
  
  .card-actions {
    justify-content: stretch;
  }
  
  .card-btn {
    flex: 1;
    text-align: center;
  }
}
</style>
