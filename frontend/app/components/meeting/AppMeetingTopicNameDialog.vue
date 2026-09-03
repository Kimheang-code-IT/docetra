<script setup lang="ts">
import type { MeetingTopic } from '~/types/docetra/entities'

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

const title = ref('')
const description = ref('')
const touched = ref(false)

const isEdit = computed(() => Boolean(props.topic?.id))
const dialogTitle = computed(() =>
  isEdit.value
    ? t('docetra.meetingBoard.editTopicTitle')
    : t('docetra.meetingBoard.createTopicTitle'),
)
const trimmedTitle = computed(() => title.value.trim())
const trimmedDescription = computed(() => description.value.trim())
const invalid = computed(() => touched.value && !trimmedTitle.value)
const canSubmit = computed(() => Boolean(trimmedTitle.value) && !props.loading)

watch(open, (isOpen) => {
  if (!isOpen) return
  title.value = props.topic?.title || ''
  description.value = props.topic?.description || ''
  touched.value = false
})

function onCancel() {
  if (props.loading) return
  open.value = false
}

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
  <UModal
    v-model:open="open"
    :dismissible="!loading"
    :ui="{ content: 'sm:max-w-md' }"
  >
    <template #content>
      <UCard>
        <template #header>
          <h3 class="text-base font-semibold text-highlighted">
            {{ dialogTitle }}
          </h3>
        </template>

        <form class="space-y-3" @submit.prevent="onSubmit">
          <UFormField
            :label="$t('docetra.meetingBoard.topicName')"
            name="topicName"
            required
            :error="invalid ? $t('docetra.meetingBoard.topicNameRequired') : undefined"
          >
            <UInput
              v-model="title"
              variant="soft"
              autofocus
              :disabled="loading"
              :placeholder="$t('docetra.meetingBoard.topicNamePlaceholder')"
              class="w-full"
              @blur="touched = true"
            />
          </UFormField>

          <UFormField
            :label="$t('docetra.meetingBoard.topicDescription')"
            name="topicDescription"
          >
            <UTextarea
              v-model="description"
              variant="soft"
              :disabled="loading"
              :rows="3"
              :placeholder="$t('docetra.meetingBoard.topicDescriptionPlaceholder')"
              class="w-full"
            />
          </UFormField>
        </form>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton
              color="neutral"
              variant="ghost"
              :disabled="loading"
              @click="onCancel"
            >
              {{ $t('docetra.common.cancel') }}
            </UButton>
            <UButton
              color="primary"
              :loading="loading"
              :disabled="!canSubmit"
              @click="onSubmit"
            >
              {{ isEdit ? $t('docetra.common.save') : $t('docetra.common.create') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
