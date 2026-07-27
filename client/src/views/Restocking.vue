<template>
  <div class="restocking">
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-control">
        <input
          type="range"
          min="10000"
          max="500000"
          step="10000"
          v-model.number="budget"
          class="budget-slider"
        />
        <div class="budget-value">
          {{ t('restocking.budgetLabel') }}: <strong>{{ formattedBudget }}</strong>
        </div>
      </div>
    </div>

    <div v-if="loading && !recommendations" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(recommendations?.budget ?? budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(recommendations?.total_cost ?? 0, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(recommendations?.remaining ?? 0, currentCurrency) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }}</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="!items.length || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderSuccess" class="success-banner">{{ t('restocking.orderPlaced') }}</div>
        <div v-if="orderError" class="error">{{ orderError }}</div>

        <div v-if="!items.length" class="empty-state">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.table.sku') }}</th>
                <th>{{ t('inventory.table.itemName') }}</th>
                <th>{{ t('restocking.demandGap') }}</th>
                <th>{{ t('restocking.recommendedQty') }}</th>
                <th>{{ t('inventory.table.unitCost') }}</th>
                <th>{{ t('inventory.table.totalValue') }}</th>
                <th>{{ t('restocking.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.demand_gap }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                <td><strong>{{ formatCurrency(item.line_total, currentCurrency) }}</strong></td>
                <td>{{ item.lead_time_days }} {{ t('restocking.leadTimeDays') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const { t, currentCurrency } = useI18n()

const budget = ref(100000)
const recommendations = ref(null)
const loading = ref(false)
const error = ref(null)
const placing = ref(false)
const orderError = ref(null)
const orderSuccess = ref(false)

const items = computed(() => recommendations.value?.items || [])

const formattedBudget = computed(() => formatCurrency(budget.value, currentCurrency.value))

// Debounce the API call so dragging the slider doesn't hammer the endpoint.
let debounceTimer = null

const loadRecommendations = async () => {
  loading.value = true
  error.value = null
  try {
    recommendations.value = await api.getRestockRecommendations(budget.value)
  } catch (err) {
    error.value = 'Failed to load restock recommendations: ' + err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

watch(budget, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadRecommendations, 300)
})

const placeOrder = async () => {
  if (!items.value.length || placing.value) return
  placing.value = true
  orderError.value = null
  orderSuccess.value = false
  try {
    await api.createRestockOrder({ budget: budget.value, items: items.value })
    orderSuccess.value = true
    await loadRecommendations()
    setTimeout(() => { orderSuccess.value = false }, 3000)
  } catch (err) {
    orderError.value = t('restocking.orderError')
    console.error(err)
  } finally {
    placing.value = false
  }
}

onMounted(loadRecommendations)
</script>

<style scoped>
.budget-card {
  margin-bottom: var(--space-6);
}

.budget-control {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.budget-slider {
  flex: 1;
  accent-color: var(--color-accent);
}

.budget-value {
  white-space: nowrap;
  color: var(--color-ink-mid);
  font-size: var(--text-md);
  min-width: 220px;
  text-align: right;
}

.place-order-btn {
  background: var(--color-accent);
  color: var(--color-surface);
  border: none;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.place-order-btn:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.place-order-btn:disabled {
  background: var(--color-border-strong);
  cursor: not-allowed;
}

.success-banner {
  background: var(--color-success-bg);
  color: var(--color-success);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  font-size: var(--text-md);
}

.empty-state {
  text-align: center;
  padding: var(--space-10);
  color: var(--color-ink-muted);
  font-size: var(--text-md);
}
</style>
