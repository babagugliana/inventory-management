<template>
  <div class="page-toolbar">
    <div class="page-toolbar-heading">
      <h2>{{ title }}</h2>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <FilterBar />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import FilterBar from './FilterBar.vue'

const route = useRoute()
const { t } = useI18n()

// route.meta is briefly {} on the synchronous first render, before the
// router finishes resolving the initial navigation — guard both keys
// (not just subtitleKey) so t() never gets called with undefined.
const title = computed(() => (route.meta.titleKey ? t(route.meta.titleKey) : ''))
const subtitle = computed(() => (route.meta.subtitleKey ? t(route.meta.subtitleKey) : ''))
</script>

<style scoped>
.page-toolbar {
  margin-bottom: var(--space-6);
}

.page-toolbar-heading {
  margin-bottom: var(--space-4);
}

.page-toolbar-heading h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  letter-spacing: -0.025em;
  margin-bottom: var(--space-1);
}

.page-toolbar-heading p {
  font-size: var(--text-md);
  color: var(--color-ink-muted);
}
</style>
