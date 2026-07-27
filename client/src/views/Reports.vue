<template>
  <div class="reports">
    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th>{{ t('reports.quarterly.totalOrders') }}</th>
                <th>{{ t('reports.quarterly.totalRevenue') }}</th>
                <th>{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ formatCurrency(q.total_revenue) }}</td>
                <td>{{ formatCurrency(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyTrend.title') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatCurrency(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.monthOverMonth.month') }}</th>
                <th>{{ t('reports.monthOverMonth.orders') }}</th>
                <th>{{ t('reports.monthOverMonth.revenue') }}</th>
                <th>{{ t('reports.monthOverMonth.change') }}</th>
                <th>{{ t('reports.monthOverMonth.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ formatCurrency(month.revenue) }}</td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalRevenueYTD') }}</div>
          <div class="stat-value">{{ formatCurrency(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalOrdersYTD') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'

const { t, currentCurrency } = useI18n()

const {
  selectedPeriod,
  selectedLocation,
  selectedCategory,
  selectedStatus,
  getCurrentFilters
} = useFilters()

const loading = ref(true)
const error = ref(null)
const quarterlyData = ref([])
const monthlyData = ref([])

// Derived summary stats - pure derivations of the fetched data, kept as
// computed so they can never go stale relative to quarterlyData/monthlyData.
const totalRevenue = computed(() => monthlyData.value.reduce((sum, m) => sum + m.revenue, 0))

const avgMonthlyRevenue = computed(() => {
  return monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
})

const totalOrders = computed(() => monthlyData.value.reduce((sum, m) => sum + m.order_count, 0))

const bestQuarter = computed(() => {
  return quarterlyData.value.reduce((best, q) => {
    return q.total_revenue > best.revenue ? { quarter: q.quarter, revenue: q.total_revenue } : best
  }, { quarter: '', revenue: 0 }).quarter
})

// Hoisted out of getBarHeight so the max isn't recomputed by scanning the
// whole array on every single bar render (was O(n^2) across the chart).
const maxMonthlyRevenue = computed(() => {
  return monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0)
})

const loadData = async () => {
  error.value = null
  try {
    loading.value = true
    const filters = getCurrentFilters()
    const [quarterlyRes, monthlyRes] = await Promise.all([
      api.getQuarterlyReports(filters),
      api.getMonthlyTrends(filters)
    ])
    quarterlyData.value = quarterlyRes
    monthlyData.value = monthlyRes
  } catch (err) {
    error.value = t('reports.loadError')
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Watch for filter changes and reload data
watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
  loadData()
})

const formatCurrency = (value) => formatCurrencyUtil(value, currentCurrency.value)

const formatMonth = (monthStr) => {
  // Convert YYYY-MM to a localized "Mon YYYY" label
  const [year, month] = monthStr.split('-')
  const monthKeys = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
  const monthIndex = parseInt(month, 10) - 1
  return `${t(`months.${monthKeys[monthIndex]}`)} ${year}`
}

const getBarHeight = (revenue) => {
  // Max height 200px
  if (maxMonthlyRevenue.value === 0) return 0
  return (revenue / maxMonthlyRevenue.value) * 200
}

const getFulfillmentClass = (rate) => {
  if (rate >= 90) return 'badge success'
  if (rate >= 75) return 'badge warning'
  return 'badge danger'
}

const getChangeValue = (current, previous) => {
  const change = current - previous
  if (change > 0) return `+${formatCurrency(change)}`
  if (change < 0) return `-${formatCurrency(Math.abs(change))}`
  return formatCurrency(0)
}

const getChangeClass = (current, previous) => {
  const change = current - previous
  if (change > 0) return 'positive-change'
  if (change < 0) return 'negative-change'
  return ''
}

const getGrowthRate = (current, previous) => {
  if (previous === 0) return t('reports.monthOverMonth.notApplicable')
  const rate = ((current - previous) / previous) * 100
  const sign = rate > 0 ? '+' : ''
  return `${sign}${rate.toFixed(1)}%`
}

onMounted(loadData)
</script>

<style scoped>
.reports {
  padding: 0;
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: var(--color-tint);
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--color-ink-muted);
  border-bottom: 2px solid var(--color-border);
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.reports-table tr:hover {
  background: var(--color-surface-sunk);
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  /* #60a5fa has no token equivalent; mapped to the nearest existing token,
     --color-accent-light, which also matches the first stop and flattens
     this into a single-tone bar rather than a two-tone gradient. */
  background: linear-gradient(to top, var(--color-accent-light), var(--color-accent-light));
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, var(--color-accent), var(--color-accent-light));
}

.bar-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-ink-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--color-ink-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-ink);
}

.positive-change {
  /* #16a34a has no exact token; mapped to the nearest existing token, --color-success. */
  color: var(--color-success);
  font-weight: 600;
}

.negative-change {
  color: var(--color-danger);
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--color-ink-muted);
}

.error {
  /* #fee2e2/#991b1b have no exact tokens; mapped to the nearest existing
     tokens, --color-danger-bg / --color-danger. */
  background: var(--color-danger-bg);
  color: var(--color-danger);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}
</style>
