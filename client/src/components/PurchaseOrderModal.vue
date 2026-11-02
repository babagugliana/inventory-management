<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" @click="close" :aria-label="t('common.close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <form class="modal-form" @submit.prevent="submit" novalidate>
            <div class="modal-body">
              <div class="item-header">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-meta">
                  <span>{{ t('purchaseOrder.sku') }}: <span class="mono">{{ backlogItem.item_sku }}</span></span>
                  <span>{{ t('purchaseOrder.shortage') }}: <strong>{{ t('purchaseOrder.units', { count: shortage }) }}</strong></span>
                </div>
              </div>

              <!-- View mode -->
              <template v-if="mode === 'view'">
                <div v-if="loading" class="state-message">{{ t('purchaseOrder.loading') }}</div>
                <div v-else-if="loadError" class="state-message error">{{ loadError }}</div>
                <div v-else-if="purchaseOrder" class="info-grid">
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.poId') }}</div>
                    <div class="info-value mono">{{ purchaseOrder.id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                    <div class="info-value"><span class="badge">{{ translateStatus(purchaseOrder.status) }}</span></div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                    <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                    <div class="info-value">{{ purchaseOrder.quantity }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                    <div class="info-value">{{ money(purchaseOrder.unit_cost) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                    <div class="info-value"><strong>{{ money(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</strong></div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                    <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                    <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                  </div>
                  <div class="info-item full">
                    <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                    <div class="info-value notes">{{ purchaseOrder.notes || t('purchaseOrder.noNotes') }}</div>
                  </div>
                </div>
              </template>

              <!-- Create mode -->
              <template v-else>
                <div class="form-grid">
                  <div class="form-group full">
                    <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                    <input id="po-supplier" v-model="form.supplier_name" type="text" required
                      :placeholder="t('purchaseOrder.supplierPlaceholder')" />
                  </div>
                  <div class="form-group">
                    <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                    <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" required />
                  </div>
                  <div class="form-group">
                    <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }} (USD)</label>
                    <input id="po-unit-cost" v-model.number="form.unit_cost" type="number" min="0" step="0.01" required />
                  </div>
                  <div class="form-group full">
                    <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                    <input id="po-date" v-model="form.expected_delivery_date" type="date" required />
                  </div>
                  <div class="form-group full">
                    <label for="po-notes">{{ t('purchaseOrder.notes') }} ({{ t('purchaseOrder.optional') }})</label>
                    <textarea id="po-notes" v-model="form.notes" rows="3"
                      :placeholder="t('purchaseOrder.notesPlaceholder')"></textarea>
                  </div>
                </div>

                <div class="total-row">
                  <span class="info-label">{{ t('purchaseOrder.total') }}</span>
                  <span class="total-value">{{ money(total) }}</span>
                </div>

                <div v-if="submitError" class="state-message error">{{ submitError }}</div>
              </template>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
              <button v-if="mode !== 'view'" type="submit" class="btn-primary" :disabled="!isValid || submitting">
                {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { parseDate } from '../utils/date'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: { type: String, default: 'create', validator: (v) => ['create', 'view'].includes(v) }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    const form = reactive({
      supplier_name: '',
      quantity: 1,
      unit_cost: 0,
      expected_delivery_date: '',
      notes: ''
    })
    const submitting = ref(false)
    const submitError = ref(null)
    const purchaseOrder = ref(null)
    const loading = ref(false)
    const loadError = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    const total = computed(() => (Number(form.quantity) || 0) * (Number(form.unit_cost) || 0))

    const isValid = computed(() =>
      form.supplier_name.trim().length > 0 &&
      Number.isFinite(form.quantity) && form.quantity > 0 &&
      Number.isFinite(form.unit_cost) && form.unit_cost >= 0 &&
      !!form.expected_delivery_date
    )

    // Amounts are entered in USD; the display helper converts to JPY for the Japanese locale.
    const money = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    const translateStatus = (status) => {
      const key = `purchaseOrder.statuses.${status}`
      const translated = t(key)
      return translated === key ? status : translated
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      // parseDate reads YYYY-MM-DD as a local day (not UTC midnight)
      const date = parseDate(dateString)
      if (!date) return dateString
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      })
    }

    // Extract a user-facing message from an axios error, preferring the server's `detail`.
    const errorMessage = (err, fallback) => {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string') return detail
      // FastAPI 422 returns a list of validation errors
      if (Array.isArray(detail) && detail.length) return detail.map(d => d.msg).join('; ')
      return fallback
    }

    const resetForm = () => {
      form.supplier_name = ''
      form.quantity = shortage.value || 1
      form.unit_cost = 0
      form.expected_delivery_date = ''
      form.notes = ''
      submitError.value = null
      submitting.value = false
    }

    const loadPO = async () => {
      purchaseOrder.value = null
      loadError.value = null
      loading.value = true
      try {
        purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        loadError.value = err?.response?.status === 404
          ? t('purchaseOrder.notFound')
          : errorMessage(err, t('purchaseOrder.loadError'))
        if (err?.response?.status !== 404) console.error('PO load error:', err)
      } finally {
        loading.value = false
      }
    }

    // Re-initialise each time the modal opens (or switches item/mode)
    watch(
      () => [props.isOpen, props.backlogItem?.id, props.mode],
      () => {
        if (!props.isOpen || !props.backlogItem) return
        if (props.mode === 'view') loadPO()
        else resetForm()
      },
      { immediate: true }
    )

    const submit = async () => {
      if (!isValid.value || submitting.value) return
      submitting.value = true
      submitError.value = null
      try {
        const notes = form.notes.trim()
        const po = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: form.quantity,
          unit_cost: form.unit_cost,
          expected_delivery_date: form.expected_delivery_date,
          notes: notes || null
        })
        emit('po-created', po)
      } catch (err) {
        submitError.value = errorMessage(err, t('purchaseOrder.createError'))
      } finally {
        submitting.value = false
      }
    }

    const close = () => emit('close')

    return {
      t, form, shortage, total, isValid, money, submitting, submitError,
      purchaseOrder, loading, loadError, translateProductName, translateStatus,
      formatDate, submit, close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-form {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
}

.item-header {
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
}

.item-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.5rem 0;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: #64748b;
}

.item-meta strong {
  color: #dc2626;
}

.mono {
  font-family: 'Monaco', 'Courier New', monospace;
}

.form-grid,
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem 1.25rem;
}

.full {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label,
.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-group input,
.form-group textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
  resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.notes {
  white-space: pre-wrap;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  background: #fef3c7;
  color: #92400e;
}

.state-message {
  padding: 1rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

.state-message.error {
  margin-top: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  text-align: left;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  background: #0f172a;
  border: 1px solid #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
