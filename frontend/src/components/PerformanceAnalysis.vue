<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useMonitorStore } from '../composables/useMonitorStore'
import ErrorToast from './ErrorToast.vue'

const { state, generateReport } = useMonitorStore()

const analysisData = computed(() => state.performanceAnalysis)
const reportUrl = ref('')
const isGenerating = ref(false)
const showReportLink = ref(false)
const retryCount = ref(0)
const maxRetries = 3

const toastVisible = ref(false)
const toastType = ref('error')
const toastTitle = ref('')
const toastDetails = ref('')

const showToast = (type, title, details = '') => {
  toastType.value = type
  toastTitle.value = title
  toastDetails.value = details
  toastVisible.value = true
}

const closeToast = () => {
  toastVisible.value = false
}

const retryGenerateReport = () => {
  if (retryCount.value < maxRetries) {
    retryCount.value++
    showToast('info', '正在重试', `第 ${retryCount.value} 次尝试生成报告...`)
    handleGenerateReport()
  } else {
    showToast('error', '重试次数超限', `已重试 ${maxRetries} 次，请稍后再试`)
    retryCount.value = 0
  }
}

const getStabilityLevelClass = (level) => {
  const levelMap = {
    'excellent': 'level-excellent',
    'good': 'level-good',
    'fair': 'level-fair',
    'poor': 'level-poor'
  }
  return levelMap[level] || 'level-unknown'
}

const getStabilityLevelText = (level) => {
  const textMap = {
    'excellent': '优秀',
    'good': '良好',
    'fair': '一般',
    'poor': '较差'
  }
  return textMap[level] || '未知'
}

const getLeakRiskClass = (risk) => {
  const riskMap = {
    'high': 'risk-high',
    'medium': 'risk-medium',
    'low': 'risk-low'
  }
  return riskMap[risk] || 'risk-unknown'
}

const getLeakRiskText = (risk) => {
  const textMap = {
    'high': '高风险',
    'medium': '中等风险',
    'low': '低风险'
  }
  return textMap[risk] || '未知'
}

const getThermalRiskClass = (risk) => {
  const riskMap = {
    'high': 'risk-high',
    'medium': 'risk-medium',
    'low': 'risk-low'
  }
  return riskMap[risk] || 'risk-unknown'
}

const getThermalRiskText = (risk) => {
  const textMap = {
    'high': '高风险',
    'medium': '中等风险',
    'low': '低风险'
  }
  return textMap[risk] || '未知'
}

const getOverallScoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 75) return 'score-good'
  if (score >= 60) return 'score-fair'
  return 'score-poor'
}

const getTrendIcon = (trend) => {
  const iconMap = {
    'increasing_fast': '📈',
    'increasing': '📊',
    'stable': '➡️',
    'decreasing': '📉',
    'decreasing_fast': '⬇️'
  }
  return iconMap[trend] || '➡️'
}

const getTrendText = (trend) => {
  const textMap = {
    'increasing_fast': '快速上升',
    'increasing': '上升',
    'stable': '稳定',
    'decreasing': '下降',
    'decreasing_fast': '快速下降'
  }
  return textMap[trend] || '稳定'
}

const handleGenerateReport = () => {
  if (!analysisData.value) {
    showToast('warning', '数据不足', '请先开始测试以收集性能数据')
    return
  }
  
  if (isGenerating.value) {
    showToast('info', '正在生成报告', '请稍候，报告正在生成中...')
    return
  }
  
  if (!state.isConnected) {
    showToast('error', '连接断开', '请检查 WebSocket 连接状态')
    return
  }
  
  isGenerating.value = true
  showReportLink.value = false
  
  const deviceModel = 'Test Device'
  const appPackage = state.currentPackage || 'Unknown App'
  
  const success = generateReport(deviceModel, appPackage)
  
  if (!success) {
    showToast('error', '生成失败', '无法生成报告，请检查连接状态')
    isGenerating.value = false
  }
}

watch(() => state.isConnected, (isConnected) => {
  if (!isConnected) {
    isGenerating.value = false
  }
})

const handleReportGenerated = (event) => {
  const data = event.detail
  if (data.type === 'report_generated') {
    reportUrl.value = data.report_url
    showReportLink.value = true
    isGenerating.value = false
    showToast('success', '报告生成成功', '点击"查看报告"按钮打开报告')
  } else if (data.type === 'error') {
    const errorMessages = {
      'insufficient_data': { title: '数据不足', details: data.details || '请至少收集 5 秒的性能数据后再生成报告' },
      'template_not_found': { title: '模板错误', details: data.details || '报告模板文件未找到' },
      'invalid_data': { title: '数据无效', details: data.details || '性能数据无效，请重新收集' },
      'missing_field': { title: '数据不完整', details: data.details || '性能分析数据不完整' },
      'permission_error': { title: '权限错误', details: data.details || '没有保存权限' },
      'os_error': { title: '文件系统错误', details: data.details || '保存文件时发生错误' },
      'unknown_error': { title: '生成失败', details: data.details || '发生未知错误，请稍后重试' }
    }
    
    const errorInfo = errorMessages[data.error_type] || errorMessages['unknown_error']
    showToast('error', errorInfo.title, errorInfo.details)
    isGenerating.value = false
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('report-generated', handleReportGenerated)
  window.addEventListener('report-error', handleReportGenerated)
}

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('report-generated', handleReportGenerated)
    window.removeEventListener('report-error', handleReportGenerated)
  }
})
</script>

<template>
  <div class="performance-analysis">
    <div v-if="!analysisData" class="no-data">
      <div class="no-data-icon">📊</div>
      <div class="no-data-text">性能分析数据收集中...</div>
      <div class="no-data-hint">开始测试后将自动显示分析结果</div>
    </div>

    <div v-else class="analysis-content">
      <div class="action-bar">
        <button 
          @click="handleGenerateReport" 
          :disabled="isGenerating"
          class="generate-btn"
        >
          {{ isGenerating ? '生成中...' : '📄 生成 HTML 报告' }}
        </button>
        <a 
          v-if="showReportLink && reportUrl" 
          :href="reportUrl" 
          target="_blank"
          download
          class="download-link"
        >
          📥 下载报告
        </a>
      </div>

      <div class="overall-score-section">
        <div class="score-circle" :class="getOverallScoreClass(analysisData.overall_score)">
          <div class="score-value">{{ analysisData.overall_score }}</div>
          <div class="score-label">综合评分</div>
        </div>
        <div class="score-details">
          <div class="detail-item">
            <span class="detail-label">FPS 稳定性</span>
            <span class="detail-value" :class="getStabilityLevelClass(analysisData.fps.stability_level)">
              {{ getStabilityLevelText(analysisData.fps.stability_level) }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">内存泄漏风险</span>
            <span class="detail-value" :class="getLeakRiskClass(analysisData.memory.leak_risk)">
              {{ getLeakRiskText(analysisData.memory.leak_risk) }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">热节流风险</span>
            <span class="detail-value" :class="getThermalRiskClass(analysisData.battery_temp.thermal_throttle_risk)">
              {{ getThermalRiskText(analysisData.battery_temp.thermal_throttle_risk) }}
            </span>
          </div>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-card fps-card">
          <div class="card-header">
            <span class="card-title">FPS 稳定性</span>
            <span class="card-badge" :class="getStabilityLevelClass(analysisData.fps.stability_level)">
              {{ getStabilityLevelText(analysisData.fps.stability_level) }}
            </span>
          </div>
          <div class="card-body">
            <div class="metric-row">
              <span class="metric-label">平均 FPS</span>
              <span class="metric-value">{{ analysisData.fps.fps_avg }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">FPS 范围</span>
              <span class="metric-value">{{ analysisData.fps.fps_min }} - {{ analysisData.fps.fps_max }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">标准差</span>
              <span class="metric-value">{{ analysisData.fps.fps_std }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">卡顿率</span>
              <span class="metric-value" :class="{ 'warning': analysisData.fps.jank_rate > 5 }">
                {{ analysisData.fps.jank_rate }}%
              </span>
            </div>
            <div class="metric-row">
              <span class="metric-label">严重卡顿</span>
              <span class="metric-value" :class="{ 'warning': analysisData.fps.big_jank_count > 0 }">
                {{ analysisData.fps.big_jank_count }} 次
              </span>
            </div>
          </div>
        </div>

        <div class="metric-card memory-card">
          <div class="card-header">
            <span class="card-title">内存趋势</span>
            <span class="card-badge" :class="getLeakRiskClass(analysisData.memory.leak_risk)">
              {{ getLeakRiskText(analysisData.memory.leak_risk) }}
            </span>
          </div>
          <div class="card-body">
            <div class="metric-row">
              <span class="metric-label">当前内存</span>
              <span class="metric-value">{{ analysisData.memory.memory_current }} MB</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">平均内存</span>
              <span class="metric-value">{{ analysisData.memory.memory_avg }} MB</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">峰值内存</span>
              <span class="metric-value">{{ analysisData.memory.memory_max }} MB</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">增长趋势</span>
              <span class="metric-value">
                {{ getTrendIcon(analysisData.memory.memory_trend) }}
                {{ getTrendText(analysisData.memory.memory_trend) }}
              </span>
            </div>
            <div class="metric-row">
              <span class="metric-label">内存波动</span>
              <span class="metric-value" :class="{ 'warning': analysisData.memory.memory_spike_count > 3 }">
                {{ analysisData.memory.memory_spike_count }} 次峰值
              </span>
            </div>
          </div>
        </div>

        <div class="metric-card cpu-card">
          <div class="card-header">
            <span class="card-title">CPU 使用</span>
            <span class="card-badge">
              {{ getTrendIcon(analysisData.cpu.cpu_trend) }}
              {{ getTrendText(analysisData.cpu.cpu_trend) }}
            </span>
          </div>
          <div class="card-body">
            <div class="metric-row">
              <span class="metric-label">当前 CPU</span>
              <span class="metric-value" :class="{ 'warning': analysisData.cpu.cpu_current > 70 }">
                {{ analysisData.cpu.cpu_current }}%
              </span>
            </div>
            <div class="metric-row">
              <span class="metric-label">平均 CPU</span>
              <span class="metric-value">{{ analysisData.cpu.cpu_avg }}%</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">CPU 范围</span>
              <span class="metric-value">{{ analysisData.cpu.cpu_min }}% - {{ analysisData.cpu.cpu_max }}%</span>
            </div>
          </div>
        </div>

        <div class="metric-card gpu-card">
          <div class="card-header">
            <span class="card-title">GPU 使用</span>
            <span class="card-badge">
              {{ getTrendIcon(analysisData.gpu.gpu_trend) }}
              {{ getTrendText(analysisData.gpu.gpu_trend) }}
            </span>
          </div>
          <div class="card-body">
            <div class="metric-row">
              <span class="metric-label">当前 GPU</span>
              <span class="metric-value" :class="{ 'warning': analysisData.gpu.gpu_current > 70 }">
                {{ analysisData.gpu.gpu_current }}%
              </span>
            </div>
            <div class="metric-row">
              <span class="metric-label">平均 GPU</span>
              <span class="metric-value">{{ analysisData.gpu.gpu_avg }}%</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">GPU 范围</span>
              <span class="metric-value">{{ analysisData.gpu.gpu_min }}% - {{ analysisData.gpu.gpu_max }}%</span>
            </div>
          </div>
        </div>

        <div class="metric-card temp-card">
          <div class="card-header">
            <span class="card-title">电池温度</span>
            <span class="card-badge" :class="getThermalRiskClass(analysisData.battery_temp.thermal_throttle_risk)">
              {{ getThermalRiskText(analysisData.battery_temp.thermal_throttle_risk) }}
            </span>
          </div>
          <div class="card-body">
            <div class="metric-row">
              <span class="metric-label">当前温度</span>
              <span class="metric-value" :class="{ 'warning': analysisData.battery_temp.temp_current > 40 }">
                {{ analysisData.battery_temp.temp_current }}°C
              </span>
            </div>
            <div class="metric-row">
              <span class="metric-label">平均温度</span>
              <span class="metric-value">{{ analysisData.battery_temp.temp_avg }}°C</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">温度范围</span>
              <span class="metric-value">{{ analysisData.battery_temp.temp_min }}°C - {{ analysisData.battery_temp.temp_max }}°C</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">温度趋势</span>
              <span class="metric-value">
                {{ getTrendIcon(analysisData.battery_temp.temp_trend) }}
                {{ getTrendText(analysisData.battery_temp.temp_trend) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="recommendations-section" v-if="analysisData.recommendations && analysisData.recommendations.length">
        <h3 class="section-title">💡 优化建议</h3>
        <ul class="recommendations-list">
          <li v-for="(recommendation, index) in analysisData.recommendations" :key="index" class="recommendation-item">
            {{ recommendation }}
          </li>
        </ul>
      </div>
    </div>
    
    <ErrorToast
      :visible="toastVisible"
      :type="toastType"
      :title="toastTitle"
      :details="toastDetails"
      :showRetry="toastType === 'error' && retryCount < maxRetries"
      @close="closeToast"
      @retry="retryGenerateReport"
    />
  </div>
</template>

<style scoped>
.performance-analysis {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 20px;
  overflow-y: auto;
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.no-data-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-data-text {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
}

.no-data-hint {
  font-size: 14px;
  opacity: 0.7;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
}

.generate-btn {
  padding: 10px 24px;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.download-link {
  padding: 10px 24px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.download-link:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.overall-score-section {
  display: flex;
  gap: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  align-items: center;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 3px solid rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.score-excellent {
  background: rgba(103, 194, 58, 0.8);
  border-color: #67c23a;
}

.score-good {
  background: rgba(64, 158, 255, 0.8);
  border-color: #409eff;
}

.score-fair {
  background: rgba(230, 162, 60, 0.8);
  border-color: #e6a23c;
}

.score-poor {
  background: rgba(245, 108, 108, 0.8);
  border-color: #f56c6c;
}

.score-value {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.9;
}

.score-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
}

.detail-label {
  font-size: 14px;
  opacity: 0.9;
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.level-excellent {
  background: rgba(103, 194, 58, 0.3);
  color: #67c23a;
}

.level-good {
  background: rgba(64, 158, 255, 0.3);
  color: #409eff;
}

.level-fair {
  background: rgba(230, 162, 60, 0.3);
  color: #e6a23c;
}

.level-poor {
  background: rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

.risk-high {
  background: rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

.risk-medium {
  background: rgba(230, 162, 60, 0.3);
  color: #e6a23c;
}

.risk-low {
  background: rgba(103, 194, 58, 0.3);
  color: #67c23a;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.metric-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e9ecef;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #dee2e6;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.metric-label {
  font-size: 13px;
  color: #606266;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.metric-value.warning {
  color: #f56c6c;
}

.recommendations-section {
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.recommendations-list {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.recommendation-item {
  position: relative;
  padding: 8px 0 8px 24px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.recommendation-item::before {
  content: '💡';
  position: absolute;
  left: 0;
  top: 8px;
  font-size: 12px;
}
</style>