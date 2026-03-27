<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1>MobiPerf 🚀</h1>
        <p>移动应用性能监控平台</p>
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
          <label>用户名</label>
          <input 
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
            autocomplete="username"
          />
        </div>
        
        <div v-if="mode === 'register'" class="form-group">
          <label>邮箱</label>
          <input 
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱"
            required
            autocomplete="email"
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
            autocomplete="current-password"
          />
        </div>
        
        <div v-if="mode === 'register'" class="form-group">
          <label>确认密码</label>
          <input 
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            autocomplete="new-password"
          />
        </div>
        
        <div v-if="mode === 'register'" class="form-group">
          <label>全名（可选）</label>
          <input 
            v-model="form.fullName"
            type="text"
            placeholder="请输入您的全名"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
        </button>
      </form>
      
      <div class="auth-footer">
        <p v-if="mode === 'login'">
          还没有账户？ <a @click="mode = 'register'">立即注册</a>
        </p>
        <p v-else>
          已有账户？ <a @click="mode = 'login'">立即登录</a>
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
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-lg);
}

.auth-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
  padding: var(--spacing-2xl);
  width: 100%;
  max-width: 420px;
  animation: fadeIn 0.5s ease-out;
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.auth-header h1 {
  font-size: var(--font-3xl);
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: var(--spacing-sm);
}

.auth-header p {
  color: var(--text-secondary);
  font-size: var(--font-base);
}

.auth-tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  background: var(--bg-tertiary);
  padding: var(--spacing-xs);
  border-radius: var(--radius-lg);
}

.tab-btn {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--font-base);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.tab-btn:hover {
  color: var(--primary-color);
}

.tab-btn.active {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  font-size: var(--font-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input {
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--font-base);
  transition: all var(--transition-base);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input::placeholder {
  color: var(--text-tertiary);
}

.error-message {
  padding: var(--spacing-md);
  background: #fee;
  border: 1px solid #fcc;
  border-radius: var(--radius-md);
  color: #c33;
  font-size: var(--font-sm);
  text-align: center;
}

.submit-btn {
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  margin-top: var(--spacing-sm);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  margin-top: var(--spacing-xl);
  text-align: center;
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

.auth-footer a {
  color: var(--primary-color);
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.auth-footer a:hover {
  text-decoration: underline;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 480px) {
  .auth-card {
    padding: var(--spacing-lg);
  }
  
  .auth-header h1 {
    font-size: var(--font-2xl);
  }
}
</style>
