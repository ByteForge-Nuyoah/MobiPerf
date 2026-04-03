import { createApp } from 'vue'
import axios from 'axios'
import './style.css'
import './styles/design-system.css'
import App from './App.vue'

axios.defaults.baseURL = 'http://localhost:8000'
axios.defaults.timeout = 10000

createApp(App).mount('#app')
