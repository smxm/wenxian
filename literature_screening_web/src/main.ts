import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { darkTheme, dateZhCN, NConfigProvider, NDialogProvider, NLoadingBarProvider, NMessageProvider, zhCN } from 'naive-ui'
import App from './App.vue'
import { router } from './router'
import './styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.component('NConfigProvider', NConfigProvider)
app.component('NDialogProvider', NDialogProvider)
app.component('NLoadingBarProvider', NLoadingBarProvider)
app.component('NMessageProvider', NMessageProvider)

app.provide('naive-locale', zhCN)
app.provide('naive-date-locale', dateZhCN)
app.provide('naive-theme', darkTheme)

app.mount('#app')
