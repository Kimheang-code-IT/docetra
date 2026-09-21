<script setup lang="ts">
import { useStorageStatus } from '~/composables/storage/useStorageStatus'

const { status, pending, load } = useStorageStatus()
const auth = useAuthStore()
const driveReady = computed(() => status.value ? status.value.googleDrive.ready : true)
const canOpenStorageSettings = computed(() => auth.canAccessPage('settings.app_config.view'))

onMounted(() => void load())
</script>

<template>
  <div v-if="!pending && !driveReady" class="flex h-full items-center justify-center p-6">
    <UAlert
      class="max-w-xl"
      color="warning"
      variant="soft"
      icon="i-lucide-hard-drive-upload"
      :title="$t('docetra.storageStatus.driveMissingTitle')"
      :description="$t('docetra.storageStatus.driveMissingDesc')"
    >
      <template v-if="canOpenStorageSettings" #actions>
        <UButton
          size="sm"
          color="warning"
          variant="subtle"
          icon="i-lucide-settings"
          to="/settings/app-config"
        >
          {{ $t('docetra.storageStatus.openStorageSettings') }}
        </UButton>
      </template>
    </UAlert>
  </div>
  <slot v-else />
</template>
