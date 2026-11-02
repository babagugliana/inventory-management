<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'
import { parseDate } from '../utils/date'

const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

// Raw data
const forecasts = ref([])
const loading = ref(true)
const loadError = ref(null)
const budget = ref(0)

// Order submission state
const submitting = ref(false)
const submitError = ref(null)
const confirmation = ref(null)

const STEP = 100
const TREND_RANK = { increasing: 0, stable: 1, decreasing: 2 }

// All money math is done in integer cents to avoid float drift.
const toCents = (usd) => Math.round(usd * 100)

// Slider max: cost of restocking every item at its full forecast, rounded UP to the step.
const maxBudget = computed(() => {
  const totalCents = forecasts.value.reduce(
    (sum, f) => sum + toCents(f.unit_cost) * f.forecasted_demand, 0)
  return Math.ceil(totalCents / (STEP * 100)) * STEP
})

// Ranking: trend (increasing, stable, decreasing), then demand gap desc, then sku.
const rankedForecasts = computed(() => {
  return [...forecasts.value].sort((a, b) => {
    const trendDiff = (TREND_RANK[a.trend] ?? 3) - (TREND_RANK[b.trend] ?? 3)
    if (trendDiff !== 0) return trendDiff
    const gapA = a.forecasted_demand - a.current_demand
    const gapB = b.forecasted_demand - b.current_demand
    if (gapA !== gapB) return gapB - gapA
    return a.item_sku.localeCompare(b.item_sku)
  })
})

// Greedy fill over the ranked list. A partially affordable item is included with a
// reduced quantity, and cheaper later items may still use the leftover budget,
// so we deliberately do not stop at the first item that does not fully fit.
const lines = computed(() => {
  let remainingCents = Math.round(budget.value * 100)
  return rankedForecasts.value.map(f => {
    const unitCents = toCents(f.unit_cost)
    const target = f.forecasted_demand
    const qty = unitCents > 0 ? Math.max(0, Math.min(target, Math.floor(remainingCents / unitCents))) : 0
    const lineCents = qty * unitCents
    remainingCents -= lineCents
    return {
      sku: f.item_sku,
      name: f.item_name,
      trend: f.trend,
      target,
      qty,
      unitCost: f.unit_cost,
      lineCents,
      leadTime: f.lead_time_days
    }
  })
})

const recommended = computed(() => lines.value.filter(l => l.qty > 0))
const totalCents = computed(() => recommended.value.reduce((s, l) => s + l.lineCents, 0))
const totalCost = computed(() => totalCents.value / 100)
const remaining = computed(() => (Math.round(budget.value * 100) - totalCents.value) / 100)
const orderLeadTime = computed(() =>
  recommended.value.reduce((m, l) => Math.max(m, l.leadTime), 0))

const money = (usd, decimals = 2) => formatCurrencyWithDecimals(usd, currentCurrency.value, decimals)

const formatDate = (iso) => {
  const d = parseDate(iso)
  if (!d) return ''
  return d.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US',
    { year: 'numeric', month: 'short', day: 'numeric' })
}

const onBudgetInput = () => {
  // A changed plan makes any previous error stale
  submitError.value = null
}

const loadData = async () => {
  try {
    loading.value = true
    loadError.value = null
    forecasts.value = await api.getDemandForecasts()
    // Default to half the max, rounded to the step
    budget.value = Math.round(maxBudget.value / 2 / STEP) * STEP
  } catch (err) {
    loadError.value = t('restocking.loadError') + ': ' + err.message
  } finally {
    loading.value = false
  }
}

const placeOrder = async () => {
  if (submitting.value || recommended.value.length === 0) return
  submitting.value = true
  submitError.value = null
  confirmation.value = null
  try {
    // Budget is always sent in USD (base data currency), regardless of display currency
    confirmation.value = await api.createRestockingOrder({
      budget: budget.value,
      items: recommended.value.map(l => ({ sku: l.sku, quantity: l.qty }))
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    submitError.value = typeof detail === 'string' ? detail : t('restocking.errorFallback')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="loadError" class="error">{{ loadError }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-header">
          <div>
            <div class="budget-label">{{ t('restocking.budget') }}</div>
            <div class="budget-value">{{ money(budget, 0) }}</div>
          </div>
          <div class="budget-max">{{ t('restocking.maxBudget', { amount: money(maxBudget, 0) }) }}</div>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          :step="STEP"
          :aria-label="t('restocking.budget')"
          @input="onBudgetInput"
        />
        <p class="help">{{ t('restocking.budgetHelp') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ money(budget, 0) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.totalCost') }}</div>
          <div class="stat-value">{{ money(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ money(remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.items') }}</div>
          <div class="stat-value">{{ recommended.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.leadTime') }}</div>
          <div class="stat-value">{{ recommended.length ? t('restocking.days', { count: orderLeadTime }) : '-' }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendation') }}</h3>
          <button
            class="place-order"
            type="button"
            :disabled="recommended.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="confirmation" class="confirmation" role="status">
          <strong>{{ t('restocking.confirmationTitle') }}</strong>
          <span>
            {{ t('restocking.confirmationBody', {
              number: confirmation.order_number,
              total: money(confirmation.total_cost),
              date: formatDate(confirmation.expected_delivery)
            }) }}
          </span>
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>
        <div v-if="submitError" class="error submit-error" role="alert">{{ submitError }}</div>

        <p class="note">{{ t('restocking.recommendationNote') }}</p>
        <div v-if="recommended.length === 0" class="empty">{{ t('restocking.noRecommendation') }}</div>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in lines" :key="line.sku" :class="{ unfunded: line.qty === 0 }">
                <td>{{ translateProductName(line.name) }}</td>
                <td><strong>{{ line.sku }}</strong></td>
                <td>
                  <span :class="['badge', line.trend]">{{ t(`trends.${line.trend}`) }}</span>
                </td>
                <td class="num">
                  <template v-if="line.qty === 0">{{ t('restocking.notFunded') }}</template>
                  <template v-else-if="line.qty < line.target">
                    {{ t('restocking.partial', { qty: line.qty, target: line.target }) }}
                  </template>
                  <template v-else>{{ line.qty }}</template>
                </td>
                <td class="num">{{ money(line.unitCost) }}</td>
                <td class="num"><strong>{{ line.qty ? money(line.lineCents / 100) : '-' }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: line.leadTime }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-card {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-max {
  font-size: 0.875rem;
  color: #64748b;
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
}

.help,
.note {
  font-size: 0.813rem;
  color: #64748b;
  margin: 0.5rem 0 0;
}

.note {
  padding: 0 1.5rem 0.75rem;
}

.empty {
  padding: 1rem 1.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

.place-order {
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.place-order:hover:not(:disabled) {
  background: #1e293b;
}

.place-order:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.confirmation {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin: 0 1.5rem 1rem;
  font-size: 0.938rem;
}

.confirmation a {
  color: #2563eb;
  font-weight: 500;
}

.submit-error {
  margin: 0 1.5rem 1rem;
}

.num {
  text-align: right;
}

.unfunded {
  opacity: 0.45;
}
</style>
