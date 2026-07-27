<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed }">
    <AppSidebar
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />
    <main class="main-content">
      <PageToolbar />
      <router-view />
    </main>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import { useSidebar } from './composables/useSidebar'
import AppSidebar from './components/AppSidebar.vue'
import PageToolbar from './components/PageToolbar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    PageToolbar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { isCollapsed } = useSidebar()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      isCollapsed,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ---------------------------------------------------------------------------
 * Design tokens — Factory Inventory Management System
 *
 * Every value here is derived from a hex already present in client/src/ —
 * this is a structural redesign, NOT a rebrand. The slate identity is preserved.
 * ------------------------------------------------------------------------- */

:root {
  /* --- Surfaces ------------------------------------------------------- */
  --color-canvas:        #f8fafc;  /* page background */
  --color-surface:       #ffffff;  /* cards, sidebar, toolbars */
  --color-surface-sunk:  #f8fafc;  /* nested wells inside cards */
  --color-tint:          #f1f5f9;  /* hover states, table header rows */

  /* --- Borders -------------------------------------------------------- */
  --color-border:        #e2e8f0;  /* default hairline */
  --color-border-strong: #cbd5e1;  /* emphasis, form controls */

  /* --- Text ----------------------------------------------------------- */
  --color-ink:           #0f172a;  /* headings, primary numbers */
  --color-ink-body:      #1e293b;  /* body copy */
  --color-ink-mid:       #334155;  /* secondary copy */
  --color-ink-muted:     #64748b;  /* labels, captions, inactive nav */
  --color-ink-subtle:    #94a3b8;  /* placeholder, disabled */

  /* --- Accent --------------------------------------------------------- */
  --color-accent:        #2563eb;
  --color-accent-hover:  #1d4ed8;
  --color-accent-light:  #3b82f6;
  --color-accent-bg:     #eff6ff;  /* active nav pill, info surfaces */

  /* --- Status --------------------------------------------------------- */
  --color-success:       #059669;
  --color-success-bg:    #ecfdf5;
  --color-warning:       #b45309;
  --color-warning-bg:    #fffbeb;
  --color-danger:        #dc2626;
  --color-danger-bg:     #fef2f2;
  --color-info:          #2563eb;
  --color-info-bg:       #eff6ff;

  /* --- Spacing scale --------------------------------------------------
   * Use these instead of ad-hoc rem values. The app previously mixed
   * 0.375rem / 0.625rem / 0.813rem / 0.938rem / 1.25rem arbitrarily.
   * ------------------------------------------------------------------- */
  --space-1:   4px;
  --space-2:   8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;

  /* --- Radius --------------------------------------------------------- */
  --radius-sm:   6px;
  --radius-md:   8px;
  --radius-lg:  10px;   /* default for cards */
  --radius-xl:  14px;
  --radius-full: 999px;

  /* --- Elevation ------------------------------------------------------
   * Modern SaaS leans on borders, not drop shadows. Keep these subtle;
   * --shadow-md is for overlays only (modals, popovers).
   * ------------------------------------------------------------------- */
  --shadow-xs: 0 1px 2px 0 rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 1px 3px 0 rgba(15, 23, 42, 0.06);
  --shadow-md: 0 8px 24px -4px rgba(15, 23, 42, 0.12);

  /* --- Typography ----------------------------------------------------- */
  --text-xs:    0.75rem;    /* 12px - micro labels */
  --text-sm:    0.8125rem;  /* 13px - captions, table cells */
  --text-base:  0.875rem;   /* 14px - body, nav */
  --text-md:    0.9375rem;  /* 15px - emphasised body */
  --text-lg:    1.125rem;   /* 18px - card titles */
  --text-xl:    1.5rem;     /* 24px - page title */
  --text-2xl:   1.875rem;   /* 30px - stat values */

  --weight-normal:   400;
  --weight-medium:   500;
  --weight-semibold: 600;
  --weight-bold:     700;

  --leading-tight:  1.25;
  --leading-normal: 1.5;

  /* --- Layout --------------------------------------------------------- */
  --sidebar-width:    240px;
  --content-max:     1440px;
  --content-pad-x: var(--space-8);
  --content-pad-y: var(--space-6);

  /* --- Motion --------------------------------------------------------- */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-canvas);
  color: var(--color-ink-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
}

.app.sidebar-collapsed {
  --sidebar-width: 64px;
}

.main-content {
  /* AppSidebar is position: fixed (out of grid flow), so this rule pins
     main-content to the second track explicitly rather than relying on
     auto-placement, which is unreliable once a preceding grid item is
     taken out of flow. */
  grid-column: 2;
  min-width: 0;
  max-width: var(--content-max);
  width: 100%;
  margin: 0 auto;
  padding: var(--content-pad-y) var(--content-pad-x);
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-ink-muted);
  font-size: var(--text-md);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--color-ink-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-tint);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: var(--weight-semibold);
  color: var(--color-ink-mid);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border);
  color: var(--color-ink-mid);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--color-surface-sunk);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.badge.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.badge.danger {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.badge.info {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.badge.increasing {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.badge.decreasing {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.badge.stable {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.badge.high {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.badge.medium {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.badge.low {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-ink-muted);
  font-size: var(--text-md);
}

.error {
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-md);
}
</style>
