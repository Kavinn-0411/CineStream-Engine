import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { setUnauthorizedHandler } from './api/client'

const app = createApp(App)
app.use(router)

setUnauthorizedHandler(() => {
  if (router.currentRoute.value.name !== 'login') {
    router.push({
      name: 'login',
      query: { redirect: router.currentRoute.value.fullPath },
    })
  }
})

app.mount('#app')
