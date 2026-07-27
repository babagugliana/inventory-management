<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'create' ? t('purchaseOrder.createTitle') : t('purchaseOrder.viewTitle') }}
            </h3>
            <button class="close-button" @click="close" :aria-label="t('common.close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-summary-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="item-summary-sku">SKU: {{ backlogItem.item_sku }}</div>
              <div class="item-summary-shortage">
                {{ t('purchaseOrder.shortageForItem') }}: <strong>{{ shortage }} {{ t('purchaseOrder.units') }}</strong>
              </div>
            </div>

            <!-- Create mode: raise a new PO -->
            <form v-if="mode === 'create'" class="po-form" @submit.prevent="submitForm">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplierName') }}</label>
                <input
                  id="po-supplier"
                  v-model="form.supplierName"
                  type="text"
                  required
                  :placeholder="t('purchaseOrder.supplierNamePlaceholder')"
                  class="form-input"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    required
                    class="form-input"
                  />
                </div>

                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unitCost"
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    class="form-input"
                  />
                </div>
              </div>

              <div class="form-group">
                <label for="po-delivery-date">{{ t('purchaseOrder.expectedDeliveryDate') }}</label>
                <input
                  id="po-delivery-date"
                  v-model="form.expectedDeliveryDate"
                  type="date"
                  required
                  class="form-input"
                />
              </div>

              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea
                  id="po-notes"
                  v-model="form.notes"
                  rows="3"
                  :placeholder="t('purchaseOrder.notesPlaceholder')"
                  class="form-textarea"
                ></textarea>
              </div>

              <div v-if="submitError" class="form-error">{{ submitError }}</div>
            </form>

            <!-- View mode: show the existing PO read-only -->
            <div v-else class="po-view">
              <div v-if="viewLoading" class="po-status-message">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="viewError" class="po-status-message error">{{ viewError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplierName') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatCurrency(purchaseOrder.unit_cost, selectedCurrency) }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.totalCost') }}</div>
                  <div class="info-value">{{ formatCurrency(purchaseOrder.unit_cost * purchaseOrder.quantity, selectedCurrency) }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDeliveryDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value">
                    <span class="badge info">{{ translatePOStatus(purchaseOrder.status) }}</span>
                  </div>
                </div>

                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>

                <div class="info-item full-width" v-if="purchaseOrder.notes">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">
              {{ mode === 'create' ? t('purchaseOrder.cancel') : t('purchaseOrder.close') }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              @click="submitForm"
              :disabled="submitting || !isFormValid"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from '../composables/useI18n'
import { api } from '../api'
import { formatCurrency } from '../utils/currency'

const { t, translateProductName, currentLocale, currentCurrency } = useI18n()
const selectedCurrency = currentCurrency

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created'])

const submitting = ref(false)
const submitError = ref(null)

const viewLoading = ref(false)
const viewError = ref(null)
const purchaseOrder = ref(null)

const form = ref({
  supplierName: '',
  quantity: 1,
  unitCost: '',
  expectedDeliveryDate: '',
  notes: ''
})

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const isFormValid = computed(() => {
  return form.value.supplierName.trim() !== '' &&
    Number(form.value.quantity) > 0 &&
    form.value.unitCost !== '' && Number(form.value.unitCost) >= 0 &&
    form.value.expectedDeliveryDate !== ''
})

const resetForm = () => {
  form.value = {
    supplierName: '',
    quantity: shortage.value > 0 ? shortage.value : 1,
    unitCost: '',
    expectedDeliveryDate: '',
    notes: ''
  }
  submitError.value = null
}

const fetchPurchaseOrder = async () => {
  if (!props.backlogItem) return
  viewLoading.value = true
  viewError.value = null
  purchaseOrder.value = null
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    viewError.value = t('purchaseOrder.loadError')
    console.error(err)
  } finally {
    viewLoading.value = false
  }
}

// Re-initialize whenever the modal is (re)opened for a given item/mode, since
// the component instance is shared across every row rather than remounted.
watch(
  () => [props.isOpen, props.mode, props.backlogItem?.id],
  () => {
    if (!props.isOpen || !props.backlogItem) return
    if (props.mode === 'create') {
      resetForm()
    } else {
      fetchPurchaseOrder()
    }
  },
  { immediate: true }
)

const submitForm = async () => {
  if (!isFormValid.value || submitting.value || !props.backlogItem) return
  submitting.value = true
  submitError.value = null
  try {
    const response = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplierName.trim(),
      quantity: Number(form.value.quantity),
      unit_cost: Number(form.value.unitCost),
      expected_delivery_date: form.value.expectedDeliveryDate,
      notes: form.value.notes.trim() || null
    })
    emit('po-created', response)
    emit('close')
  } catch (err) {
    submitError.value = t('purchaseOrder.submitError')
    console.error(err)
  } finally {
    submitting.value = false
  }
}

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' })
}

const translatePOStatus = (status) => {
  const statusMap = {
    'Pending': t('purchaseOrder.statusPending')
  }
  return statusMap[status] || status
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  max-width: 560px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--color-ink-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.close-button:hover {
  background: var(--color-tint);
  color: var(--color-ink);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.item-summary {
  padding-bottom: var(--space-5);
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.item-summary-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-ink);
  margin-bottom: var(--space-1);
}

.item-summary-sku {
  font-size: 0.875rem;
  color: var(--color-ink-muted);
  font-family: 'Monaco', 'Courier New', monospace;
  margin-bottom: var(--space-2);
}

.item-summary-shortage {
  font-size: 0.875rem;
  color: var(--color-danger);
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

label {
  font-size: 0.813rem;
  font-weight: 600;
  color: var(--color-ink-mid);
}

.form-input,
.form-textarea {
  padding: var(--space-3);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.938rem;
  font-family: inherit;
  color: var(--color-ink);
  transition: border-color 0.15s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-accent-light);
}

.form-textarea {
  resize: vertical;
}

.form-error {
  padding: var(--space-3);
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  font-size: 0.875rem;
}

.po-status-message {
  padding: var(--space-6) 0;
  text-align: center;
  color: var(--color-ink-muted);
  font-size: 0.938rem;
}

.po-status-message.error {
  color: var(--color-danger);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-5);
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink-muted);
  margin-bottom: var(--space-2);
}

.info-value {
  font-size: 0.938rem;
  color: var(--color-ink);
  font-weight: 500;
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary {
  padding: var(--space-3) var(--space-5);
  background: var(--color-tint);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-ink-mid);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--color-border);
  border-color: var(--color-border-strong);
}

.btn-primary {
  padding: var(--space-3) var(--space-5);
  background: var(--color-accent-light);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-surface);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal transition animations */
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
