<script setup lang="ts">
import type { MeetingTopic } from '~/types/docetra/entities'
import type { DocumentFieldSchema } from '~/types/docetra/common'

const open = defineModel<boolean>('open', { default: false })

const props = defineProps<{
  /** When set, dialog edits an existing topic; otherwise creates. */
  topic?: MeetingTopic | null
  loading?: boolean
}>()

const emit = defineEmits<{
  save: [payload: { title: string, description: string }]
}>()

const { t } = useI18n()

const form = reactive({
  title: '',
  description: '',
})
const touched = ref(false)

const isEdit = computed(() => Boolean(props.topic?.id))
const dialogTitle = computed(() =>
  isEdit.value
    ? t('docetra.meetingBoard.editTopicTitle')
    : t('docetra.meetingBoard.createTopicTitle'),
)
const trimmedTitle = computed(() => form.title.trim())
const trimmedDescription = computed(() => form.description.trim())
const invalid = computed(() => touched.value && !trimmedTitle.value)
const canSubmit = computed(() => Boolean(trimmedTitle.value) && !props.loading)

const titleField: DocumentFieldSchema = {
  key: 'title',
  labelKey: 'docetra.meetingBoard.topicName',
  type: 'text',
  required: true,
  placeholderKey: 'docetra.meetingBoard.topicNamePlaceholder',
}

const descriptionField: DocumentFieldSchema = {
  key: 'description',
  labelKey: 'docetra.meetingBoard.topicDescription',
  type: 'textarea',
  placeholderKey: 'docetra.meetingBoard.topicDescriptionPlaceholder',
  rows: 3,
}

watch(open, (isOpen) => {
  if (!isOpen) return
  form.title = props.topic?.title || ''
  form.description = props.topic?.description || ''
  touched.value = false
})

function onSubmit() {
  touched.value = true
  if (!canSubmit.value) return
  emit('save', {
    title: trimmedTitle.value,
    description: trimmedDescription.value,
  })
}
</script>

<template>
  <CommonAppDialogShell
    v-model:open="open"
    :title="dialogTitle"
    :loading="loading"
    :can-submit="canSubmit"
    :confirm-label="isEdit ? $t('docetra.common.save') : $t('docetra.common.create')"
    @confirm="onSubmit"
  >
    <form class="space-y-3" @submit.prevent="onSubmit">
      <UFormField
        :label="$t('docetra.meetingBoard.topicName')"
        name="topicName"
        required
        :error="invalid ? $t('docetra.meetingBoard.topicNameRequired') : undefined"
      >
        <CommonAppFormControl
          :field="titleField"
          v-model="form.title"
          :disabled="loading"
          @blur="touched = true"
        />
      </UFormField>

      <UFormField
        :label="$t('docetra.meetingBoard.topicDescription')"
        name="topicDescription"
      >
        <CommonAppFormControl
          :field="descriptionField"
          v-model="form.description"
          :disabled="loading"
        />
      </UFormField>
    </form>
  </CommonAppDialogShell>
</template>
