<script setup>
import { computed, ref, nextTick, watch, onActivated } from 'vue'
import { useMonitorStore } from '../composables/useMonitorStore'

const props = defineProps({
  serial: String
})

const { state } = useMonitorStore()
const logContainer = ref(null)
const autoScroll = ref(true)

// Computed logs from store
const logs = computed(() => state.logList)

// Watch logs to auto-scroll
watch(() => state.lastLogUpdate, () => {
  if (autoScroll.value) {
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    })
  }
})

onActivated(() => {
  if (autoScroll.value) {
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    })
  }
})

const exportLogs = () => {
  if (state.logList.length === 0) {
    alert('暂无日志')
    return
  }
  
  const lines = state.logList.map(l => `[${l.time}] ${l.message}`)
  // Add BOM for Windows compatibility
  const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/plain;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  const fileTimestamp = `${y}${m}${d}_${h}${min}${s}`
  
  a.download = `crash_logs_${props.serial}_${fileTimestamp}.txt`
  a.click()
}

const clearLogs = () => {
  state.logList = []
}
</script>

<template>
  <div class="log-viewer">
    <div class="toolbar">
      <div class="left">
        <h3>系统日志分析</h3>
        <span class="count">共 {{ logs.length }} 条</span>
      </div>
      <div class="right">
        <label class="checkbox">
          <input type="checkbox" v-model="autoScroll"> 自动滚动
        </label>
        <button @click="clearLogs" class="btn clear-btn">清空</button>
        <button @click="exportLogs" class="btn export-btn">导出日志</button>
      </div>
    </div>
    
      <div class="log-container" ref="logContainer">
      <div v-for="(log, index) in logs" :key="index" class="log-item" :class="[`log-${log.level}`, { 'log-crash': log.isCrash }]">
        <span class="log-time">{{ log.time }}</span>
        <span class="log-level-tag">{{ log.level ? log.level.toUpperCase() : 'INFO' }}</span>
        <span class="log-msg">{{ log.message }}</span>
      </div>
      <div v-if="logs.length === 0" class="empty-state">
        暂无日志数据，请在监控页面开始测试...
      </div>
    </div>
  </div>
</template>

<style scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.toolbar h3 {
  margin: 0;
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.count {
  margin-left: var(--spacing-2);
  font-size: var(--font-xs);
  color: var(--text-tertiary);
  background: var(--gray-200);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-weight: var(--font-medium);
}

.right {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.checkbox {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.checkbox:hover {
  color: var(--text-primary);
}

.checkbox input {
  margin-right: var(--spacing-2);
  cursor: pointer;
}

.btn {
  padding: var(--spacing-2) var(--spacing-4);
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

.export-btn {
  background: var(--primary-500);
  color: white;
}

.export-btn:hover {
  background: var(--primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.clear-btn {
  background: var(--bg-primary);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
}

.clear-btn:hover {
  background: var(--gray-50);
  color: var(--text-primary);
  border-color: var(--border-dark);
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-3);
  background: #1a1b26;
  font-family: var(--font-mono);
  font-size: var(--font-sm);
  line-height: var(--leading-relaxed);
}

.log-item {
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-sm);
  color: #a9b1d6;
  transition: background var(--transition-fast);
}

.log-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.log-time {
  color: #565f89;
  flex-shrink: 0;
  width: 100px;
  font-size: var(--font-xs);
}

.log-level-tag {
  flex-shrink: 0;
  width: 60px;
  font-weight: var(--font-semibold);
  text-align: center;
  margin-right: var(--spacing-2);
  font-size: var(--font-xs);
  padding: 2px var(--spacing-2);
  border-radius: var(--radius-sm);
}

.log-msg {
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
}

.log-verbose .log-level-tag {
  color: #565f89;
  background: rgba(86, 95, 137, 0.2);
}

.log-debug .log-level-tag {
  color: #73daca;
  background: rgba(115, 218, 202, 0.2);
}

.log-info .log-level-tag {
  color: #7aa2f7;
  background: rgba(122, 162, 247, 0.2);
}

.log-warn .log-level-tag {
  color: #e0af68;
  background: rgba(224, 175, 104, 0.2);
}

.log-error .log-level-tag {
  color: #f7768e;
  background: rgba(247, 118, 142, 0.2);
}

.log-verbose {
  color: #565f89;
}

.log-debug {
  color: #9aa5ce;
}

.log-info {
  color: #a9b1d6;
}

.log-warn {
  color: #e0af68;
}

.log-error {
  color: #f7768e;
}

.log-crash {
  background: rgba(247, 118, 142, 0.15);
  border-left: 3px solid #f7768e;
  color: #f7768e;
  font-weight: var(--font-semibold);
}

.empty-state {
  color: #565f89;
  text-align: center;
  margin-top: 100px;
  font-size: var(--font-base);
  font-style: italic;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
