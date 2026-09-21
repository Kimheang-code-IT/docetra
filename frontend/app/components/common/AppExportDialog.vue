<script setup lang="ts">
import type { ExportFieldOption, ExportFormat, ExportRequest, ExportScope } from '~/types/docetra/export'
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
const format = ref<ExportFormat>('csv')
const selectedFields = ref<string[]>([])

const formatItems = computed(() => [
  { label: t('docetra.exportDialog.formatCsv'), value: 'csv' },
  { label: t('docetra.exportDialog.formatExcel'), value: 'xlsx' },
])

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
  format.value = 'csv'
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
    format: format.value,
    fieldCodes: [...selectedFields.value],
    fieldLabels: Object.fromEntries(props.fields.map(field => [field.value, field.label])),
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
        <UFormField :label="$t('docetra.exportDialog.format')">
          <USelect
            v-model="format"
            :items="formatItems"
            value-key="value"
            class="w-full"
            :color="FORM_CONTROL.color"
            :variant="FORM_CONTROL.variant"
            :size="FORM_CONTROL.size"
          />
        </UFormField>

        <div class="grid gap-4 sm:grid-cols-2">
          <UFormField :label="$t('docetra.exportDialog.startDate')">
            <CommonAppInputDate v-model="startDate" class="w-full" />
          </UFormField>
          <UFormField
            :label="$t('docetra.exportDialog.endDate')"
            :error="invalidRange ? $t('docetra.exportDialog.invalidRange') : undefined"
          >
            <CommonAppInputDate v-model="endDate" class="w-full" />
          </UFormField>
        </div>

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
