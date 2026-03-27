<template>
  <div class="projects-view">
    <div class="header">
      <h2>项目管理</h2>
      <button @click="showCreateModal = true" class="create-btn">
        ➕ 创建项目
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="projects.length === 0" class="empty-state">
      <div class="empty-icon">📁</div>
      <p>暂无项目</p>
      <button @click="showCreateModal = true" class="create-btn">
        创建第一个项目
      </button>
    </div>

    <div v-else class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="viewProject(project)"
      >
        <div class="project-header">
          <h3>{{ project.name }}</h3>
          <span :class="['status-badge', project.status]">
            {{ project.status }}
          </span>
        </div>
        
        <p class="project-description">{{ project.description || '暂无描述' }}</p>
        
        <div class="project-meta">
          <div class="meta-item">
            <span class="label">平台:</span>
            <span class="value">{{ getPlatformText(project.platform) }}</span>
          </div>
          <div class="meta-item">
            <span class="label">应用:</span>
            <span class="value">{{ project.app_package || '未设置' }}</span>
          </div>
          <div class="meta-item">
            <span class="label">角色:</span>
            <span class="value">{{ getRoleText(project.user_role) }}</span>
          </div>
        </div>

        <div class="project-footer">
          <span class="date">{{ formatDate(project.created_at) }}</span>
          <div class="actions">
            <button @click.stop="editProject(project)" class="action-btn">✏️ 编辑</button>
            <button @click.stop="shareProject(project)" class="action-btn">🔗 分享</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingProject ? '编辑项目' : '创建项目' }}</h3>
          <button @click="closeModal" class="close-btn">×</button>
        </div>

        <form @submit.prevent="handleSubmit" class="modal-form">
          <div class="form-group">
            <label>项目名称 *</label>
            <input v-model="projectForm.name" type="text" required placeholder="请输入项目名称" />
          </div>

          <div class="form-group">
            <label>项目描述</label>
            <textarea v-model="projectForm.description" placeholder="请输入项目描述" rows="3"></textarea>
          </div>

          <div class="form-group">
            <label>应用包名</label>
            <input v-model="projectForm.app_package" type="text" placeholder="com.example.app" />
          </div>

          <div class="form-group">
            <label>平台</label>
            <select v-model="projectForm.platform">
              <option value="android">Android</option>
              <option value="ios">iOS</option>
              <option value="both">双平台</option>
            </select>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="projectForm.is_public" type="checkbox" />
              <span>公开项目</span>
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="cancel-btn">取消</button>
            <button type="submit" class="submit-btn" :disabled="submitting">
              {{ submitting ? '处理中...' : (editingProject ? '保存' : '创建') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const projects = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const editingProject = ref(null)
const submitting = ref(false)

const projectForm = reactive({
  name: '',
  description: '',
  app_package: '',
  platform: 'both',
  is_public: false
})

const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

const loadProjects = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/auth/projects', {
      headers: getAuthHeaders()
    })
    projects.value = response.data.projects
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingProject.value) {
      await axios.put(`/api/auth/projects/${editingProject.value.id}`, projectForm, {
        headers: getAuthHeaders()
      })
    } else {
      await axios.post('/api/auth/projects', projectForm, {
        headers: getAuthHeaders()
      })
    }
    
    await loadProjects()
    closeModal()
  } catch (err) {
    console.error('Failed to save project:', err)
    alert('保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

const editProject = (project) => {
  editingProject.value = project
  Object.assign(projectForm, {
    name: project.name,
    description: project.description || '',
    app_package: project.app_package || '',
    platform: project.platform,
    is_public: project.is_public
  })
  showCreateModal.value = true
}

const shareProject = (project) => {
  alert(`分享功能开发中：${project.name}`)
}

const viewProject = (project) => {
  alert(`查看项目详情：${project.name}`)
}

const closeModal = () => {
  showCreateModal.value = false
  editingProject.value = null
  Object.assign(projectForm, {
    name: '',
    description: '',
    app_package: '',
    platform: 'both',
    is_public: false
  })
}

const getPlatformText = (platform) => {
  const map = {
    'android': 'Android',
    'ios': 'iOS',
    'both': '双平台'
  }
  return map[platform] || platform
}

const getRoleText = (role) => {
  const map = {
    'owner': '所有者',
    'admin': '管理员',
    'developer': '开发者',
    'viewer': '查看者'
  }
  return map[role] || role
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.header h2 {
  margin: 0;
  font-size: 28px;
  color: #1a202c;
}

.create-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.create-btn:hover {
  transform: translateY(-2px);
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1a202c;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.active {
  background: #c6f6d5;
  color: #22543d;
}

.status-badge.archived {
  background: #e2e8f0;
  color: #4a5568;
}

.project-description {
  color: #718096;
  font-size: 14px;
  margin: 0 0 16px;
  line-height: 1.5;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.meta-item .label {
  color: #a0aec0;
  min-width: 60px;
}

.meta-item .value {
  color: #4a5568;
  font-weight: 500;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.date {
  color: #a0aec0;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #edf2f7;
}

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
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #a0aec0;
}

.modal-form {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 10px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input {
  width: 18px;
  height: 18px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 8px;
}

.cancel-btn, .submit-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.cancel-btn {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  color: #4a5568;
}

.submit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
