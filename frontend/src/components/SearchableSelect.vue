<template>
  <div class="searchable-select">
    <label v-if="label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>

    <div class="field-wrapper" :class="{ disabled }" ref="wrapperRef">
      <div v-if="modelValue && showSelectionChip" class="selected-chip">
        <div class="chip-text">
          <div class="chip-title">{{ modelValue.label }}</div>
          <div v-if="modelValue.subtitle" class="chip-subtitle">
            {{ modelValue.subtitle }}
          </div>
        </div>
        <button
          type="button"
          class="chip-clear"
          @click.stop="clearSelection"
          aria-label="Clear selection"
        >
          ×
        </button>
      </div>

      <input
        ref="inputRef"
        type="text"
        v-model="query"
        :placeholder="activePlaceholder"
        :disabled="disabled"
        @focus="openPanel"
        @keydown.down.prevent="navigate(1)"
        @keydown.up.prevent="navigate(-1)"
        @keydown.enter.prevent="selectHighlighted"
      />

      <span v-if="loading" class="spinner" aria-hidden="true"></span>
    </div>

    <div v-if="hint" class="hint">{{ hint }}</div>

    <div
      v-if="open && !disabled"
      class="options-panel"
      ref="panelRef"
      @scroll.passive="handleScroll"
    >
      <div v-if="!options.length && !loading" class="empty-state">
        {{ emptyText }}
      </div>

      <button
        v-for="(option, idx) in options"
        :key="option.id ?? idx"
        type="button"
        class="option"
        :class="{ active: idx === highlightedIndex }"
        @mousedown.prevent="select(option)"
      >
        <span class="option-label">{{ option.label }}</span>
        <span v-if="option.subtitle" class="option-subtitle">{{ option.subtitle }}</span>
        <span v-if="option.meta" class="option-meta">{{ option.meta }}</span>
      </button>

      <div v-if="loadingMore" class="loading-more">
        Loading more…
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue';

const props = defineProps({
  modelValue: {
    type: Object,
    default: null
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Type to search…'
  },
  hint: {
    type: String,
    default: ''
  },
  fetcher: {
    type: Function,
    required: true
  },
  minChars: {
    type: Number,
    default: 0
  },
  debounce: {
    type: Number,
    default: 200
  },
  autoLoad: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  emptyText: {
    type: String,
    default: 'No matches found'
  },
  showSelectionChip: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:modelValue', 'select', 'clear']);

const query = ref('');
const options = ref([]);
const loading = ref(false);
const loadingMore = ref(false);
const open = ref(false);
const highlightedIndex = ref(-1);
const cursor = ref(null);
const hasMore = ref(false);
const inputRef = ref(null);
const panelRef = ref(null);
const wrapperRef = ref(null);
let debounceTimer;

const activePlaceholder = computed(() => {
  if (props.modelValue && props.showSelectionChip) {
    return 'Search to change selection';
  }
  return props.placeholder;
});

watch(
  () => query.value,
  () => {
    if (props.minChars && query.value.length < props.minChars) {
      options.value = [];
      highlightedIndex.value = -1;
      cursor.value = null;
      hasMore.value = false;
      return;
    }
    scheduleFetch(true);
  }
);

function scheduleFetch(reset = false) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchOptions({ reset });
  }, props.debounce);
}

async function fetchOptions({ reset = false } = {}) {
  if (props.disabled) return;

  try {
    if (reset) {
      loading.value = true;
      cursor.value = null;
      hasMore.value = false;
      if (!open.value) open.value = true;
    } else {
      loadingMore.value = true;
    }

    const response = await props.fetcher(query.value.trim(), reset ? null : cursor.value);
    const newOptions = normalizeOptions(response);
    const nextCursor = response?.nextCursor ?? response?.next ?? null;

    options.value = reset ? newOptions : [...options.value, ...newOptions];
    highlightedIndex.value = options.value.length ? 0 : -1;
    cursor.value = nextCursor;
    hasMore.value = Boolean(nextCursor);
  } catch (err) {
    console.error('SearchableSelect fetch failed', err);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function normalizeOptions(response) {
  if (!response) return [];
  if (Array.isArray(response)) return response;
  if (Array.isArray(response.items)) return response.items;
  if (Array.isArray(response.results)) return response.results;
  if (Array.isArray(response.data)) return response.data;
  return [];
}

function openPanel() {
  if (props.disabled) return;
  open.value = true;
  if (!options.value.length && props.autoLoad) {
    fetchOptions({ reset: true });
  }
}

function closePanel() {
  open.value = false;
  highlightedIndex.value = -1;
}

function navigate(delta) {
  if (!options.value.length) return;
  const nextIndex = (highlightedIndex.value + delta + options.value.length) % options.value.length;
  highlightedIndex.value = nextIndex;
  ensureOptionInView();
}

function ensureOptionInView() {
  if (!panelRef.value || highlightedIndex.value < 0) return;
  const optionEl = panelRef.value.children[highlightedIndex.value];
  if (!optionEl) return;
  const { offsetTop, offsetHeight } = optionEl;
  const { scrollTop, clientHeight } = panelRef.value;
  if (offsetTop < scrollTop) {
    panelRef.value.scrollTop = offsetTop;
  } else if (offsetTop + offsetHeight > scrollTop + clientHeight) {
    panelRef.value.scrollTop = offsetTop - clientHeight + offsetHeight;
  }
}

function select(option) {
  emit('update:modelValue', option);
  emit('select', option);
  query.value = '';
  closePanel();
}

function selectHighlighted() {
  if (highlightedIndex.value >= 0 && options.value[highlightedIndex.value]) {
    select(options.value[highlightedIndex.value]);
  }
}

function clearSelection() {
  emit('update:modelValue', null);
  emit('clear');
  query.value = '';
  if (props.autoLoad) {
    fetchOptions({ reset: true });
  }
  if (inputRef.value) {
    inputRef.value.focus();
  }
}

function handleScroll() {
  if (!panelRef.value || loadingMore.value || !hasMore.value) return;
  const { scrollTop, scrollHeight, clientHeight } = panelRef.value;
  if (scrollTop + clientHeight >= scrollHeight - 20) {
    fetchOptions({ reset: false });
  }
}

function handleClickOutside(event) {
  if (!wrapperRef.value) return;
  if (wrapperRef.value.contains(event.target) || panelRef.value?.contains(event.target)) {
    return;
  }
  closePanel();
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  if (props.autoLoad && !props.minChars) {
    fetchOptions({ reset: true });
  }
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
  clearTimeout(debounceTimer);
});
</script>

<style scoped>
.searchable-select {
  position: relative;
}

label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #2d3436;
}

.required {
  color: #d63031;
  margin-left: 4px;
}

.field-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid #dfe6e9;
  border-radius: 6px;
  padding: 8px;
  background: #fff;
}

.field-wrapper input {
  border: none;
  outline: none;
  font-size: 0.95rem;
  padding: 4px 2px;
}

.field-wrapper.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.selected-chip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #e8f4ff;
  border: 1px solid #74b9ff;
  border-radius: 6px;
  padding: 8px;
  gap: 8px;
}

.chip-title {
  font-weight: 600;
}

.chip-subtitle {
  font-size: 0.85em;
  color: #555;
}

.chip-clear {
  border: none;
  background: transparent;
  font-size: 1.2rem;
  cursor: pointer;
  color: #0984e3;
  line-height: 1;
}

.spinner {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 16px;
  height: 16px;
  border: 2px solid #dfe6e9;
  border-top-color: #0984e3;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.hint {
  margin-top: 4px;
  font-size: 0.85em;
  color: #636e72;
}

.options-panel {
  position: absolute;
  width: 100%;
  max-height: 260px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #dfe6e9;
  border-radius: 6px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
  margin-top: 6px;
  z-index: 10;
}

.option {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-bottom: 1px solid #f1f2f6;
  transition: background 0.15s ease;
}

.option:last-child {
  border-bottom: none;
}

.option.active,
.option:hover {
  background: #f2f6ff;
}

.option-label {
  font-weight: 600;
  color: #2d3436;
}

.option-subtitle {
  display: block;
  font-size: 0.85em;
  color: #555;
}

.option-meta {
  display: block;
  font-size: 0.8em;
  color: #888;
}

.empty-state,
.loading-more {
  padding: 12px;
  text-align: center;
  color: #636e72;
  font-size: 0.9em;
}
</style>

