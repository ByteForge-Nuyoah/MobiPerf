<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <div class="auth-logo">
          <span class="logo-icon">📊</span>
        </div>
        <h1 class="auth-title">MobiPerf</h1>
        <p class="auth-subtitle">移动应用性能监控平台</p>
      </div>
      
      <div class="auth-tabs">
        <button 
          :class="['tab-btn', { active: mode === 'login' }]"
          @click="mode = 'login'"
        >
          登录
        </button>
        <button 
          :class="['tab-btn', { active: mode === 'register' }]"
          @click="mode = 'register'"
        >
          注册
        </button>
      </div>
      
      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input 
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
            autocomplete="username"
            class="form-input"
          />
        </div>
        
        <div v-if="mode === 'register'" class="form-group">
          <label class="form-label">邮箱</label>
          <input 
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱"
            required
            autocomplete="email"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">密码</label>
          <input 
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
            autocomplete="current-password"
            class="form-input"
          />
        </div>
        
        <div v-if="mode === 'register'" class="form-group">
          <label class="form-label">确认密码</label>
          <input 
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            autocomplete="new-password"
            class="form-input"
          />
        </div>
        
        <div v-if="mode === 'register'" class="form-group">
          <label class="form-label">全名（可选）</label>
          <input 
            v-model="form.fullName"
            type="text"
            placeholder="请输入您的全名"
            class="form-input"
          />
        </div>
        
        <div v-if="error" class="error-alert">
          <span class="error-icon">⚠️</span>
          <span class="error-text">{{ error }}</span>
        </div>
        
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span>{{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}</span>
        </button>
      </form>
      
      <div class="auth-footer">
        <p v-if="mode === 'login'">
          还没有账户？ <a @click="mode = 'register'" class="auth-link">立即注册</a>
        </p>
        <p v-else>
          已有账户？ <a @click="mode = 'login'" class="auth-link">立即登录</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../composables/useAuthStore'

const { state, login, register, clearError } = useAuthStore()

const mode = ref('login')
const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  fullName: ''
})

const error = ref('')
const loading = ref(false)

const handleSubmit = async () => {
  error.value = ''
  loading.value = true
  
  try {
    if (mode.value === 'login') {
      const success = await login(form.value.username, form.value.password)
      if (!success) {
        error.value = state.error || '登录失败，请检查用户名和密码'
      }
    } else {
      if (form.value.password !== form.value.confirmPassword) {
        error.value = '两次输入的密码不一致'
        loading.value = false
        return
      }
      
      if (form.value.password.length < 6) {
        error.value = '密码长度至少为6位'
        loading.value = false
        return
      }
      
      const success = await register({
        username: form.value.username,
        email: form.value.email,
        password: form.value.password,
        full_name: form.value.fullName
      })
      
      if (!success) {
        error.value = state.error || '注册失败，请重试'
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-700) 50%, var(--primary-900) 100%);
  padding: var(--spacing-6);
  position: relative;
  overflow: hidden;
}

.auth-page::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 50%);
  animation: pulse 15s ease-in-out infinite;
}

.auth-card {
  background: var(--bg-primary);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-2xl);
  padding: var(--spacing-8);
  width: 100%;
  max-width: 420px;
  animation: scaleIn var(--transition-slow) ease-out;
  position: relative;
  z-index: 1;
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-6);
}

.auth-logo {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--spacing-4);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
}

.logo-icon {
  font-size: 32px;
}

.auth-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-1);
}

.auth-subtitle {
  color: var(--text-tertiary);
  font-size: var(--font-sm);
  margin: 0;
}

.auth-tabs {
  display: flex;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-6);
  background: var(--gray-100);
  padding: var(--spacing-1);
  border-radius: var(--radius-xl);
}

.tab-btn {
  flex: 1;
  padding: var(--spacing-3);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary-600);
  box-shadow: var(--shadow-sm);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.form-label {
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.form-input {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: var(--font-base);
  transition: all var(--transition-fast);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--danger-50);
  border: 1px solid var(--danger-200);
  border-radius: var(--radius-lg);
  color: var(--danger-600);
  font-size: var(--font-sm);
}

.error-icon {
  font-size: 16px;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-6);
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  margin-top: var(--spacing-2);
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.auth-footer {
  margin-top: var(--spacing-6);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--font-sm);
}

.auth-link {
  color: var(--primary-600);
  font-weight: var(--font-medium);
  cursor: pointer;
  text-decoration: none;
  transition: color var(--transition-fast);
}

.auth-link:hover {
  color: var(--primary-700);
  text-decoration: underline;
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@media (max-width: 480px) {
  .auth-page {
    padding: var(--spacing-4);
  }
  
  .auth-card {
    padding: var(--spacing-6);
  }
  
  .auth-title {
    font-size: var(--font-xl);
  }
}
</style>
