<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>测试详情</h3>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>

      <div v-if="loading" class="modal-body loading">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="modal-body error">
        ❌ {{ error }}
      </div>

      <div v-else class="modal-body">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">设备型号:</span>
              <span class="value">{{ session.device_model || 'Unknown' }}</span>
            </div>
            <div class="info-item">
              <span class="label">应用包名:</span>
              <span class="value">{{ session.app_package || 'Unknown' }}</span>
            </div>
            <div class="info-item">
              <span class="label">开始时间:</span>
              <span class="value">{{ formatTime(session.start_time) }}</span>
            </div>
            <div class="info-item">
              <span class="label">结束时间:</span>
              <span class="value">{{ formatTime(session.end_time) }}</span>
            </div>
            <div class="info-item">
              <span class="label">测试时长:</span>
              <span class="value">{{ formatDuration(session.duration) }}</span>
            </div>
            <div class="info-item">
              <span class="label">测试状态:</span>
              <span class="value status" :class="`status-${session.status}`">
                {{ getStatusText(session.status) }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="statistics" class="detail-section">
          <h4>性能统计</h4>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">平均 FPS</div>
              <div class="stat-value">{{ statistics.avg_fps || 0 }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">平均 CPU</div>
              <div class="stat-value">{{ statistics.avg_cpu || 0 }}%</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">平均内存</div>
              <div class="stat-value">{{ statistics.avg_memory || 0 }} MB</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">平均温度</div>
              <div class="stat-value">{{ statistics.avg_temp || 0 }}°C</div>
            </div>
          </div>
        </div>

        <div v-if="analysis" class="detail-section">
          <h4>性能分析</h4>
          <div class="analysis-content">
            <div class="score-display">
              <div class="score-circle" :class="getScoreClass(analysis.overall_score)">
                <div class="score-value">{{ analysis.overall_score }}</div>
                <div class="score-label">综合评分</div>
              </div>
            </div>

            <div v-if="analysis.recommendations && analysis.recommendations.length" class="recommendations">
              <h5>优化建议</h5>
              <ul>
                <li v-for="(rec, index) in analysis.recommendations" :key="index">
                  {{ rec }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div class="detail-section actions">
          <button @click="exportSession" class="export-btn">
            📥 导出数据
          </button>
          <button @click="viewMetrics" class="metrics-btn">
            📊 查看详细指标
          </button>
        </div>
      </div>
    </div>

    <SessionMetricsChart 
      v-if="showMetricsChart" 
      :session-id="sessionId" 
      @close="showMetricsChart = false" 
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import SessionMetricsChart from './SessionMetricsChart.vue'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const session = ref({})
const statistics = ref(null)
const analysis = ref(null)
const loading = ref(false)
const error = ref('')
const showMetricsChart = ref(false)

const loadSessionDetail = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.get(`/api/sessions/${props.sessionId}`)
    
    if (response.data.error) {
      error.value = response.data.error
    } else {
      session.value = response.data.session || {}
      statistics.value = response.data.statistics || null
      analysis.value = response.data.analysis || null
    }
  } catch (err) {
    error.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const exportSession = async () => {
  try {
    const response = await axios.get(`/api/sessions/${props.sessionId}/metrics`)
    const metrics = response.data.metrics || []
    
    if (metrics.length === 0) {
      alert('没有可导出的数据')
      return
    }
    
    const csvContent = convertToCSV(metrics)
    downloadCSV(csvContent, `session_${props.sessionId}.csv`)
  } catch (err) {
    alert('导出失败: ' + err.message)
  }
}

const viewMetrics = () => {
  showMetricsChart.value = true
}

const convertToCSV = (metrics) => {
  if (metrics.length === 0) return ''
  
  const headers = Object.keys(metrics[0])
  const csvRows = [headers.join(',')]
  
  for (const row of metrics) {
    const values = headers.map(header => {
      const value = row[header]
      return typeof value === 'string' ? `"${value}"` : value
    })
    csvRows.push(values.join(','))
  }
  
  return csvRows.join('\n')
}

const downloadCSV = (content, filename) => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
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
  loadSessionDetail()
})
</script>

<style scoped>
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
  animation: fadeIn var(--transition-base) ease-out;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-2xl);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-2xl);
  animation: scaleIn var(--transition-slow) ease-out;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.close-btn {
  background: transparent;
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
  background: var(--gray-100);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-6);
}

.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  gap: var(--spacing-4);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.detail-section {
  margin-bottom: var(--spacing-6);
}

.detail-section h4 {
  margin: 0 0 var(--spacing-4);
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  padding-bottom: var(--spacing-2);
  border-bottom: 2px solid var(--primary-500);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-3);
}

.info-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  transition: all var(--transition-fast);
}

.info-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-200);
}

.info-item .label {
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  margin-right: var(--spacing-3);
  min-width: 80px;
}

.info-item .value {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.info-item .value.status {
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: var(--font-semibold);
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-4);
}

.stat-card {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  color: white;
  padding: var(--spacing-5);
  border-radius: var(--radius-xl);
  text-align: center;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stat-label {
  font-size: var(--font-sm);
  opacity: 0.9;
  margin-bottom: var(--spacing-2);
}

.stat-value {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.score-display {
  display: flex;
  justify-content: center;
}

.score-circle {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-bold);
  box-shadow: var(--shadow-xl);
  transition: all var(--transition-base);
}

.score-circle:hover {
  transform: scale(1.05);
}

.score-excellent {
  background: linear-gradient(135deg, var(--success-500), #34d399);
  color: white;
}

.score-good {
  background: linear-gradient(135deg, var(--primary-500), #818cf8);
  color: white;
}

.score-fair {
  background: linear-gradient(135deg, var(--warning-500), #fbbf24);
  color: white;
}

.score-poor {
  background: linear-gradient(135deg, var(--danger-500), #f87171);
  color: white;
}

.score-value {
  font-size: 42px;
  line-height: 1;
}

.score-label {
  font-size: var(--font-xs);
  margin-top: var(--spacing-1);
  opacity: 0.9;
}

.recommendations {
  background: var(--bg-secondary);
  padding: var(--spacing-5);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.recommendations h5 {
  margin: 0 0 var(--spacing-3);
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.recommendations ul {
  margin: 0;
  padding-left: var(--spacing-5);
}

.recommendations li {
  margin-bottom: var(--spacing-2);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
}

.actions {
  display: flex;
  gap: var(--spacing-3);
  justify-content: center;
  padding-top: var(--spacing-5);
  border-top: 1px solid var(--border-light);
}

.export-btn, .metrics-btn {
  padding: var(--spacing-3) var(--spacing-6);
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.export-btn:hover, .metrics-btn:hover {
  background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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
</style>
