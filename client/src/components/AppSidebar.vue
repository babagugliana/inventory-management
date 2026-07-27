<template>
  <aside class="app-sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-brand" :class="{ collapsed: isCollapsed }">
      <template v-if="!isCollapsed">
        <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </template>
      <div v-else class="brand-mark" :title="t('nav.companyName')">CC</div>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path), collapsed: isCollapsed }"
        :title="isCollapsed ? t(item.labelKey) : null"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span v-if="!isCollapsed" class="nav-label">{{ t(item.labelKey) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button
        type="button"
        class="sidebar-toggle"
        :class="{ collapsed: isCollapsed }"
        :aria-label="t(isCollapsed ? 'nav.expandSidebar' : 'nav.collapseSidebar')"
        @click="toggleCollapsed"
      >
        <svg
          class="toggle-icon"
          :class="{ flipped: isCollapsed }"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
        >
          <path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-if="!isCollapsed">{{ t('nav.collapseSidebar') }}</span>
      </button>

      <ProfileMenu
        :collapsed="isCollapsed"
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
      <LanguageSwitcher :collapsed="isCollapsed" />
    </div>
  </aside>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

defineEmits(['show-profile-details', 'show-tasks'])

const route = useRoute()
const { t } = useI18n()
const { isCollapsed, toggleCollapsed, syncCollapsedForViewport } = useSidebar()

onMounted(() => {
  syncCollapsedForViewport()
  window.addEventListener('resize', syncCollapsedForViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncCollapsedForViewport)
})

const navItems = [
  {
    path: '/',
    labelKey: 'nav.overview',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2.5" y="2.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11.5" y="2.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="2.5" y="11.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11.5" y="11.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/></svg>'
  },
  {
    path: '/inventory',
    labelKey: 'nav.inventory',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2.5 6.5L10 2.5L17.5 6.5V13.5L10 17.5L2.5 13.5V6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M2.5 6.5L10 10.5L17.5 6.5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M10 10.5V17.5" stroke="currentColor" stroke-width="1.5"/></svg>'
  },
  {
    path: '/orders',
    labelKey: 'nav.orders',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2.5 3H4.5L6.3 12.2C6.4 12.9 7 13.4 7.7 13.4H14.8C15.5 13.4 16.1 12.9 16.2 12.2L17.5 5.5H5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="8" cy="17" r="1.2" stroke="currentColor" stroke-width="1.5"/><circle cx="14.5" cy="17" r="1.2" stroke="currentColor" stroke-width="1.5"/></svg>'
  },
  {
    path: '/spending',
    labelKey: 'nav.finance',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/><path d="M10 5.5V14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M12.5 7.5C12.5 6.7 11.4 6 10 6C8.6 6 7.5 6.7 7.5 7.6C7.5 8.5 8.3 8.9 10 9.2C11.7 9.5 12.5 9.9 12.5 10.9C12.5 11.9 11.4 12.6 10 12.6C8.6 12.6 7.5 11.9 7.5 11.1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
  },
  {
    path: '/demand',
    labelKey: 'nav.demandForecast',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2.5 17.5H17.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M3.5 13L7.5 9L11 12L17 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M13 5H17V9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  },
  {
    path: '/reports',
    labelKey: 'nav.reports',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5 2.5H12L15.5 6V17.5H5V2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M12 2.5V6H15.5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M7.5 10H12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M7.5 13H12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
  }
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
  transition: width var(--transition-base);
}

.sidebar-brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-6) var(--space-5) var(--space-5);
}

.sidebar-brand.collapsed {
  align-items: center;
  padding: var(--space-6) var(--space-2) var(--space-5);
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

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-accent-bg);
  color: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  letter-spacing: -0.01em;
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
  gap: var(--space-3);
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

.nav-item.collapsed {
  justify-content: center;
  padding: var(--space-3) var(--space-2);
}

.nav-icon {
  display: flex;
  flex-shrink: 0;
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

.sidebar-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-ink-muted);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.sidebar-toggle.collapsed {
  justify-content: center;
}

.sidebar-toggle:hover {
  background: var(--color-tint);
  color: var(--color-ink);
}

.toggle-icon {
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}
</style>
