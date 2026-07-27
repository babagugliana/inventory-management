import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'

const router = createRouter({
  history: createWebHistory(),
  // titleKey/subtitleKey are resolved through t() by PageToolbar, which owns the
  // page heading now that each view no longer renders its own .page-header.
  routes: [
    { path: '/', component: Dashboard, meta: { titleKey: 'dashboard.title', subtitleKey: 'dashboard.description' } },
    { path: '/inventory', component: Inventory, meta: { titleKey: 'inventory.title', subtitleKey: 'inventory.description' } },
    { path: '/orders', component: Orders, meta: { titleKey: 'orders.title', subtitleKey: 'orders.description' } },
    { path: '/demand', component: Demand, meta: { titleKey: 'demand.title', subtitleKey: 'demand.description' } },
    { path: '/spending', component: Spending, meta: { titleKey: 'finance.title', subtitleKey: 'finance.description' } },
    { path: '/reports', component: Reports, meta: { titleKey: 'reports.title', subtitleKey: 'reports.description' } }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
