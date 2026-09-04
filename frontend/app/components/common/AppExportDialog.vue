<script setup lang="ts">
import type { ExportFieldOption, ExportRequest, ExportScope } from '~/types/docetra/export'
import { FORM_CONTROL } from '~/utils/form-field-ui'

const open = defineModel<boolean>('open', { default: false })

const props = withDefaults(defineProps<{
  fields?: ExportFieldOption[]
  selectedCount?: number
  loading?: boolean
}>(), {
  fields: () => [],
  selectedCount: 0,
  loading: false,
})

const emit = defineEmits<{
  submit: [request: ExportRequest]
}>()

const { t } = useI18n()
const startDate = ref('')
const endDate = ref('')
const scope = ref<ExportScope>('all_matching')
const selectedFields = ref<string[]>([])

const scopeItems = computed(() => [
  { label: t('docetra.exportDialog.allMatching'), value: 'all_matching' },
  { label: t('docetra.exportDialog.currentPage'), value: 'current_page' },
  {
    label: t('docetra.exportDialog.selectedRows', { n: props.selectedCount }),
    value: 'selected',
    disabled: props.selectedCount < 1,
  },
])

const invalidRange = computed(() => Boolean(
  startDate.value && endDate.value && startDate.value > endDate.value,
))
const noFields = computed(() => props.fields.length > 0 && selectedFields.value.length === 0)
const canSubmit = computed(() => !invalidRange.value && !noFields.value && !props.loading)

watch(open, (isOpen) => {
  if (!isOpen) return
  startDate.value = ''
  endDate.value = ''
  scope.value = 'all_matching'
  selectedFields.value = props.fields.map(field => field.value)
})

watch(() => props.selectedCount, (count) => {
  if (count < 1 && scope.value === 'selected') scope.value = 'all_matching'
})

function toggleField(value: string, checked: boolean | 'indeterminate') {
  selectedFields.value = checked === true
    ? [...new Set([...selectedFields.value, value])]
    : selectedFields.value.filter(field => field !== value)
}

function submit() {
  if (!canSubmit.value) return
  emit('submit', {
    startDate: startDate.value || undefined,
    endDate: endDate.value || undefined,
    scope: scope.value,
    fieldCodes: [...selectedFields.value],
  })
}
</script>

<template>
  <CommonAppDialogShell
    v-model:open="open"
    variant="modal"
    size="lg"
    :title="$t('docetra.exportDialog.title')"
    :description="$t('docetra.exportDialog.description')"
    :loading="loading"
    :can-submit="canSubmit"
    confirm-icon="i-lucide-download"
    :confirm-label="$t('actions.export')"
    @confirm="submit"
  >
      <div class="space-y-5">
        <UFormField
          :label="$t('docetra.exportDialog.dateRange')"
          :error="invalidRange ? $t('docetra.exportDialog.invalidRange') : undefined"
        >
          <CommonAppFilterControl
            :filter="{ key: 'dateRange', labelKey: 'docetra.exportDialog.dateRange', type: 'daterange' }"
            :start="startDate"
            :end="endDate"
            size="md"
            inline
            class="w-full"
            @update:start="startDate = $event"
            @update:end="endDate = $event"
          />
        </UFormField>

        <UFormField :label="$t('docetra.exportDialog.scope')">
          <USelect
            v-model="scope"
            :items="scopeItems"
            value-key="value"
            class="w-full"
            :placeholder="$t('docetra.fields.placeholderSelect', { label: $t('docetra.exportDialog.scope') })"
            :color="FORM_CONTROL.color"
            :variant="FORM_CONTROL.variant"
            :size="FORM_CONTROL.size"
          />
        </UFormField>

        <fieldset v-if="fields.length" class="rounded-lg border border-default p-3">
          <legend class="px-1 text-sm font-medium text-highlighted">
            {{ $t('docetra.exportDialog.fields') }}
          </legend>
          <p class="mb-3 text-xs text-muted">{{ $t('docetra.exportDialog.fieldsHint') }}</p>
          <div class="grid gap-2 sm:grid-cols-2">
            <UCheckbox
              v-for="field in fields"
              :key="field.value"
              :model-value="selectedFields.includes(field.value)"
              :label="field.label"
              @update:model-value="toggleField(field.value, $event)"
            />
          </div>
          <p v-if="noFields" class="mt-2 text-xs text-error">
            {{ $t('docetra.exportDialog.fieldRequired') }}
          </p>
        </fieldset>
      </div>
  </CommonAppDialogShell>
</template>
