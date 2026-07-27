<template>
  <aside class="app-sidebar">
    <div class="sidebar-brand">
      <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
      <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        {{ t(item.labelKey) }}
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
      <LanguageSwitcher />
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

defineEmits(['show-profile-details', 'show-tasks'])

const route = useRoute()
const { t } = useI18n()

const navItems = [
  { path: '/', labelKey: 'nav.overview' },
  { path: '/inventory', labelKey: 'nav.inventory' },
  { path: '/orders', labelKey: 'nav.orders' },
  { path: '/spending', labelKey: 'nav.finance' },
  { path: '/demand', labelKey: 'nav.demandForecast' },
  { path: '/reports', labelKey: 'nav.reports' }
]

// '/' must match exactly or every route would light up Overview (prefix match
// would make '/' a prefix of everything). The rest match by prefix.
const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  /* No overflow-y here on purpose: setting overflow-y (even to 'auto') forces
     the UA to compute overflow-x as 'auto' too, which clips the profile/
     language dropdowns since their containing block is inside this element.
     Six nav items + brand + footer comfortably fit 100vh without scrolling. */
  z-index: 50;
}

.sidebar-brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-6) var(--space-5) var(--space-5);
}

.brand-name {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  letter-spacing: -0.025em;
  line-height: var(--leading-tight);
}

.brand-subtitle {
  font-size: var(--text-sm);
  font-weight: var(--weight-normal);
  color: var(--color-ink-muted);
  line-height: var(--leading-tight);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
}

.nav-item {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
  color: var(--color-ink-muted);
  text-decoration: none;
  font-weight: var(--weight-medium);
  font-size: var(--text-base);
  line-height: var(--leading-tight);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.nav-item:hover {
  background: var(--color-tint);
  color: var(--color-ink);
}

.nav-item.active {
  background: var(--color-accent-bg);
  border-left-color: var(--color-accent);
  color: var(--color-accent);
  font-weight: var(--weight-semibold);
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--color-border);
}
</style>
