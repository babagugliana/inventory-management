import { ref } from 'vue'

// Shared sidebar collapse state (singleton pattern, matches useFilters.js)
const isCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')

const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebar-collapsed', isCollapsed.value)
}

// Below 1024px the sidebar is always icons-only; at/above 1024px it
// follows whatever the user last chose. Call on mount and on resize.
const syncCollapsedForViewport = () => {
  if (window.innerWidth <= 1024) {
    isCollapsed.value = true
  } else {
    isCollapsed.value = localStorage.getItem('sidebar-collapsed') === 'true'
  }
}

export function useSidebar() {
  return {
    isCollapsed,
    toggleCollapsed,
    syncCollapsedForViewport
  }
}
