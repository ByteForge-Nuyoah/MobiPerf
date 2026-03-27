<template>
  <transition name="toast">
    <div v-if="visible" :class="['error-toast', `toast-${type}`]">
      <div class="toast-icon">
        {{ getIcon(type) }}
      </div>
      <div class="toast-content">
        <div class="toast-title">{{ title }}</div>
        <div v-if="details" class="toast-details">{{ details }}</div>
        <div v-if="showRetry" class="toast-actions">
          <button @click="handleRetry" class="toast-retry-btn">
            🔄 重试
          </button>
        </div>
      </div>
      <button @click="close" class="toast-close">×</button>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'error',
    validator: (value) => ['error', 'warning', 'info', 'success'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  details: {
    type: String,
    default: ''
  },
  duration: {
    type: Number,
    default: 5000
  },
  closable: {
    type: Boolean,
    default: true
  },
  showRetry: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'retry'])

const getIcon = (type) => {
  const icons = {
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️',
    success: '✅'
  }
  return icons[type] || 'ℹ️'
}

const close = () => {
  emit('close')
}

const handleRetry = () => {
  emit('retry')
  close()
}

watch(() => props.visible, (newVal) => {
  if (newVal && props.duration > 0) {
    setTimeout(() => {
      close()
    }, props.duration)
  }
})
</script>

<style scoped>
.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  min-width: 300px;
  max-width: 500px;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  z-index: 9999;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.toast-error {
  background: linear-gradient(135deg, #fee 0%, #fcc 100%);
  border-left: 4px solid #f56c6c;
}

.toast-warning {
  background: linear-gradient(135deg, #fef9e7 0%, #fceea7 100%);
  border-left: 4px solid #e6a23c;
}

.toast-info {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-left: 4px solid #409eff;
}

.toast-success {
  background: linear-gradient(135deg, #f1f8e9 0%, #c8e6c9 100%);
  border-left: 4px solid #67c23a;
}

.toast-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.toast-details {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.toast-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.toast-retry-btn {
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  color: #303133;
}

.toast-retry-btn:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toast-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #909399;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #606266;
}
</style>
