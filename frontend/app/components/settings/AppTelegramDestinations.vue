<script setup lang="ts">
/**
 * Telegram destinations editor: add/remove chats, detect chat IDs from recent
 * bot messages, and send a real test message to verify delivery.
 */
import type { TelegramDestination, TelegramDestinationType } from '~/types/docetra/settings'
import { createClientId } from '~/utils/client-id'
import { FORM_CONTROL } from '~/utils/form-field-ui'
import { useSettingsRepositories } from '~/repositories'

const model = defineModel<TelegramDestination[]>({ default: () => [] })

const props = withDefaults(defineProps<{
  disabled?: boolean
  canConfigure?: boolean
}>(), {
  disabled: false,
  canConfigure: false,
})

const { t } = useI18n()
const toast = useToast()
const { appConfig } = useSettingsRepositories()

const detecting = ref(false)
const testingId = ref<string | null>(null)

const destinationTypeItems = [
  { label: 'Chat', value: 'chat' },
  { label: 'Channel', value: 'channel' },
  { label: 'Group', value: 'group' },
  { label: 'Organization', value: 'organization' },
]

function telegramTypeToDestination(type: string): TelegramDestinationType {
  if (type === 'channel') return 'channel'
  if (type === 'group' || type === 'supergroup') return 'group'
  return 'chat'
}

const locked = computed(() => props.disabled || !props.canConfigure)

function addDestination() {
  const next: TelegramDestination = {
    id: createClientId('td'),
    name: t('docetra.settings.newDestination'),
    type: 'chat',
    chatId: '',
    enabledEvents: ['record_created'],
    status: 'not_tested',
    enabled: true,
  }
  model.value = [...model.value, next]
}

function removeDestination(id: string) {
  model.value = model.value.filter(d => d.id !== id)
}

async function detectChats() {
  if (locked.value || detecting.value) return
  detecting.value = true
  try {
    const chats = await appConfig.discoverTelegramChats()
    const known = new Set(model.value.map(d => String(d.chatId || '')))
    const added = chats.filter(chat => !known.has(String(chat.chatId)))
    if (!added.length) {
      toast.add({ title: t('docetra.settings.detectChatsEmpty'), color: 'info' })
      return
    }
    model.value = [...model.value, ...added.map((chat): TelegramDestination => ({
      id: createClientId('td'),
      name: chat.title || chat.chatId,
      type: telegramTypeToDestination(chat.type),
      chatId: chat.chatId,
      enabledEvents: ['record_created'],
      status: 'connected',
      verified: true,
      enabled: true,
    }))]
    toast.add({ title: t('docetra.settings.detectChatsAdded', { count: added.length }), color: 'success' })
  }
  catch {
    toast.add({ title: t('docetra.settings.detectChatsFailed'), color: 'error' })
  }
  finally {
    detecting.value = false
  }
}

async function sendTest(destination: TelegramDestination) {
  if (locked.value || testingId.value) return
  if (!destination.chatId) {
    toast.add({ title: t('docetra.settings.chatIdRequired'), color: 'warning' })
    return
  }
  testingId.value = destination.id
  try {
    const result = await appConfig.sendTestTelegramMessage({
      destinationId: destination.id,
      chatId: destination.chatId,
    })
    if (result.status === 'connected') {
      destination.verified = true
      destination.status = 'connected'
      destination.lastTestedAt = result.testedAt
      toast.add({ title: t('docetra.settings.testMessageSent'), color: 'success' })
    }
    else {
      destination.verified = false
      destination.status = result.status === 'disabled' ? 'disabled' : 'failed'
      const needsStart = /not found/i.test(result.message || '')
      toast.add({
        title: result.message || t('docetra.settings.testMessageFailed'),
        description: needsStart ? t('docetra.settings.chatNotFoundHint') : undefined,
        color: 'error',
      })
    }
  }
  catch {
    destination.verified = false
    destination.status = 'failed'
    toast.add({ title: t('docetra.settings.testMessageFailed'), color: 'error' })
  }
  finally {
    testingId.value = null
  }
}
</script>

<template>
  <div class="space-y-3 md:col-span-2">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h4 class="text-sm font-semibold">
        {{ t('docetra.settings.destinations') }}
      </h4>
      <div class="flex items-center gap-2">
        <UButton
          size="sm"
          color="neutral"
          variant="outline"
          icon="i-lucide-radar"
          :loading="detecting"
          :disabled="locked"
          @click="detectChats"
        >
          {{ t('docetra.settings.detectChats') }}
        </UButton>
        <UButton
          size="sm"
          icon="i-lucide-plus"
          :disabled="locked"
          @click="addDestination"
        >
          {{ t('docetra.settings.addDestination') }}
        </UButton>
      </div>
    </div>

    <p v-if="!model.length" class="text-sm text-muted">
      {{ t('docetra.settings.noDestinations') }}
    </p>

    <div
      v-for="dest in model"
      :key="dest.id"
      class="space-y-2 rounded-lg border border-default p-3"
    >
      <div class="grid gap-2 md:grid-cols-4">
        <UInput
          v-model="dest.name"
          :placeholder="t('docetra.fields.placeholderEnter', { label: t('docetra.fields.name') })"
          :disabled="disabled || !canConfigure"
          :color="FORM_CONTROL.color"
          :variant="FORM_CONTROL.variant"
          :size="FORM_CONTROL.size"
        />
        <UInput
          v-model="dest.chatId"
          :placeholder="t('docetra.fields.placeholderEnter', { label: t('docetra.settings.chatId') })"
          :disabled="disabled || !canConfigure"
          :color="FORM_CONTROL.color"
          :variant="FORM_CONTROL.variant"
          :size="FORM_CONTROL.size"
        />
        <USelect
          v-model="dest.type"
          :items="destinationTypeItems"
          value-key="value"
          label-key="label"
          :placeholder="t('docetra.fields.placeholderSelect', { label: t('docetra.settings.destinationType') })"
          :disabled="disabled || !canConfigure"
          :color="FORM_CONTROL.color"
          :variant="FORM_CONTROL.variant"
          :size="FORM_CONTROL.size"
        />
        <div class="flex items-center justify-between gap-2">
          <USwitch v-model="dest.enabled" :disabled="disabled || !canConfigure" />
          <div class="flex items-center gap-1">
            <UButton
              icon="i-lucide-send"
              color="neutral"
              variant="ghost"
              size="xs"
              :loading="testingId === dest.id"
              :disabled="locked || testingId !== null"
              :aria-label="t('docetra.settings.testDestination')"
              @click="sendTest(dest)"
            />
            <UButton
              icon="i-lucide-trash-2"
              color="error"
              variant="ghost"
              size="xs"
              :disabled="disabled || !canConfigure"
              @click="removeDestination(dest.id)"
            />
          </div>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2 text-xs text-muted">
        <UBadge
          :color="dest.verified ? 'success' : 'neutral'"
          variant="subtle"
          size="sm"
        >
          {{ dest.verified ? t('docetra.settings.verified') : t('docetra.settings.notVerified') }}
        </UBadge>
        <span v-if="dest.lastTestedAt">{{ dest.lastTestedAt }}</span>
        <span v-if="dest.lastTestMessage">{{ dest.lastTestMessage }}</span>
      </div>
    </div>
  </div>
</template>
