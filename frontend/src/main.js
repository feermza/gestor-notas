import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'

// Componentes PrimeVue que usamos en la app
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import Menu from 'primevue/menu'
import Avatar from 'primevue/avatar'
import Sidebar from 'primevue/sidebar'
import Toolbar from 'primevue/toolbar'
import Badge from 'primevue/badge'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import Dropdown from 'primevue/dropdown'
import Tooltip from 'primevue/tooltip'
import Calendar from 'primevue/calendar'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// Tema Aura de PrimeVue
app.use(PrimeVue, {
  theme: {
    preset: Aura,
  },
})
app.use(ToastService)

// Registrar componentes PrimeVue
app.component('Button', Button)
app.component('InputText', InputText)
app.component('Password', Password)
app.component('Card', Card)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Tag', Tag)
app.component('Dialog', Dialog)
app.component('Toast', Toast)
app.component('Menu', Menu)
app.component('Avatar', Avatar)
app.component('Sidebar', Sidebar)
app.component('Toolbar', Toolbar)
app.component('Badge', Badge)
app.component('ProgressBar', ProgressBar)
app.component('Skeleton', Skeleton)
app.component('Dropdown', Dropdown)
app.component('Calendar', Calendar)
app.component('Textarea', Textarea)
app.component('Checkbox', Checkbox)
app.directive('tooltip', Tooltip)

app.use(createPinia())
app.use(router)

app.mount('#app')
