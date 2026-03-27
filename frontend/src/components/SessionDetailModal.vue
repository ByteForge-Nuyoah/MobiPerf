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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #909399;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #606266;
}

.modal-body {
  padding: 20px;
}

.loading, .error {
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

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.info-item .label {
  font-weight: 500;
  color: #606266;
  margin-right: 12px;
  min-width: 80px;
}

.info-item .value {
  color: #303133;
}

.info-item .value.status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.score-display {
  display: flex;
  justify-content: center;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.score-excellent {
  background: linear-gradient(135deg, #67c23a, #95d475);
  color: white;
}

.score-good {
  background: linear-gradient(135deg, #409eff, #79bbff);
  color: white;
}

.score-fair {
  background: linear-gradient(135deg, #e6a23c, #f3d19e);
  color: white;
}

.score-poor {
  background: linear-gradient(135deg, #f56c6c, #fab6b6);
  color: white;
}

.score-value {
  font-size: 36px;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.9;
}

.recommendations h5 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.recommendations li {
  margin-bottom: 8px;
  color: #606266;
  line-height: 1.6;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.export-btn, .metrics-btn {
  padding: 10px 24px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.export-btn:hover, .metrics-btn:hover {
  background: #66b1ff;
  transform: translateY(-2px);
}
</style>
