import { reactive } from 'vue'
import axios from 'axios'

const state = reactive({
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  error: null
})

export const useAuthStore = () => {
  const login = async (username, password) => {
    state.loading = true
    state.error = null
    
    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password
      })
      
      const { access_token, refresh_token } = response.data
      
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      
      state.token = access_token
      state.refreshToken = refresh_token
      state.isAuthenticated = true
      
      await fetchCurrentUser()
      
      return true
    } catch (error) {
      state.error = error.response?.data?.detail || '登录失败'
      return false
    } finally {
      state.loading = false
    }
  }
  
  const register = async (userData) => {
    state.loading = true
    state.error = null
    
    try {
      const response = await axios.post('/api/auth/register', userData)
      
      const { access_token, refresh_token } = response.data
      
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      
      state.token = access_token
      state.refreshToken = refresh_token
      state.isAuthenticated = true
      
      await fetchCurrentUser()
      
      return true
    } catch (error) {
      state.error = error.response?.data?.detail || '注册失败'
      return false
    } finally {
      state.loading = false
    }
  }
  
  const logout = async () => {
    try {
      await axios.post('/api/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
    }
  }
  
  const fetchCurrentUser = async () => {
    if (!state.token) {
      return false
    }
    
    try {
      const response = await axios.get('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${state.token}`
        }
      })
      
      state.user = response.data
      state.isAuthenticated = true
      
      return true
    } catch (error) {
      console.error('Fetch user error:', error)
      
      if (error.response?.status === 401) {
        const refreshed = await refreshAccessToken()
        
        if (refreshed) {
          return await fetchCurrentUser()
        } else {
          logout()
        }
      }
      
      return false
    }
  }
  
  const refreshAccessToken = async () => {
    if (!state.refreshToken) {
      return false
    }
    
    try {
      const response = await axios.post('/api/auth/refresh', {
        refresh_token: state.refreshToken
      })
      
      const { access_token, refresh_token } = response.data
      
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      
      state.token = access_token
      state.refreshToken = refresh_token
      
      return true
    } catch (error) {
      console.error('Refresh token error:', error)
      return false
    }
  }
  
  const changePassword = async (oldPassword, newPassword) => {
    state.loading = true
    state.error = null
    
    try {
      await axios.post('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
      
      return true
    } catch (error) {
      state.error = error.response?.data?.detail || '修改密码失败'
      return false
    } finally {
      state.loading = false
    }
  }
  
  const checkAuth = async () => {
    if (!state.token) {
      state.isAuthenticated = false
      return false
    }
    
    try {
      return await fetchCurrentUser()
    } catch (error) {
      console.error('Check auth error:', error)
      state.isAuthenticated = false
      return false
    }
  }
  
  const clearError = () => {
    state.error = null
  }
  
  return {
    state,
    login,
    register,
    logout,
    fetchCurrentUser,
    refreshAccessToken,
    changePassword,
    checkAuth,
    clearError
  }
}

axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = localStorage.getItem('refresh_token')
      
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken
          })
          
          const { access_token } = response.data
          
          localStorage.setItem('access_token', access_token)
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          
          return axios(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          
          window.location.href = '/'
          
          return Promise.reject(refreshError)
        }
      }
    }
    
    return Promise.reject(error)
  }
)
