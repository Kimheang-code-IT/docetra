<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { changePassword } from '~/adapters/auth'
import { useAuthStore } from '~/stores/auth'
import {
  countUserPermissions,
  groupUserPermissions,
  resolveUserPermissionKeys,
} from '~/utils/auth/user-permissions'

const open = defineModel<boolean>('open', { default: false })

const auth = useAuthStore()
const { t, te } = useI18n()
const toast = useToast()

const activeTab = ref('profile')
const submitting = ref(false)

const tabItems = computed(() => [
  {
    label: t('docetra.userProfile.tabs.profile'),
    value: 'profile',
    icon: 'i-lucide-user',
  },
  {
    label: t('docetra.userProfile.tabs.password'),
    value: 'password',
    icon: 'i-lucide-key-round',
  },
])

const profile = computed(() => {
  const user = auth.user
  return {
    name: user?.name || t('docetra.userProfile.unknownUser'),
    email: user?.email || '—',
    role: user?.role || t('docetra.userProfile.noRole'),
    avatar: {
      src: user?.avatar
        || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'User')}&background=random`,
      alt: user?.name || 'User',
    },
  }
})

const permissionGroups = computed(() =>
  groupUserPermissions(resolveUserPermissionKeys(auth.user)),
)

const permissionCount = computed(() => countUserPermissions(permissionGroups.value))

const passwordSchema = computed(() => z.object({
  currentPassword: z.string().min(1, { error: t('docetra.userProfile.currentPasswordRequired') }),
  password: z.string().min(6, { error: t('pages.forgetPassword.passwordMin') }),
  passwordConfirmation: z.string().min(6, { error: t('pages.forgetPassword.passwordMin') }),
}).refine(data => data.password === data.passwordConfirmation, {
  message: t('pages.forgetPassword.passwordMismatch'),
  path: ['passwordConfirmation'],
}))

type PasswordSchema = z.infer<typeof passwordSchema.value>

const passwordState = reactive({
  currentPassword: '',
  password: '',
  passwordConfirmation: '',
})

watch(open, (isOpen) => {
  if (!isOpen) {
    activeTab.value = 'profile'
    passwordState.currentPassword = ''
    passwordState.password = ''
    passwordState.passwordConfirmation = ''
  }
})

function moduleLabel(labelKey: string, documentType: string) {
  if (te(labelKey)) return t(labelKey)
  return documentType.replaceAll('_', ' ')
}

function actionLabel(action: string) {
  const key = `docetra.rolePermissions.actions.${action}`
  return te(key) ? t(key) : action
}

async function onPasswordSubmit(event: FormSubmitEvent<PasswordSchema>) {
  if (submitting.value) return
  submitting.value = true
  try {
    await changePassword({
      currentPassword: event.data.currentPassword,
      password: event.data.password,
      passwordConfirmation: event.data.passwordConfirmation,
    })
    toast.add({
      title: t('docetra.userProfile.passwordChanged'),
      description: t('docetra.userProfile.passwordChangedDesc'),
      color: 'success',
    })
    passwordState.currentPassword = ''
    passwordState.password = ''
    passwordState.passwordConfirmation = ''
    activeTab.value = 'profile'
  }
  catch {
    toast.add({
      title: t('docetra.userProfile.passwordChangeFailed'),
      description: t('docetra.userProfile.passwordChangeFailedDesc'),
      color: 'error',
    })
  }
  finally {
    submitting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    scrollable
    :title="t('docetra.userProfile.title')"
    :description="t('docetra.userProfile.description')"
    :ui="{
      overlay: 'place-items-start justify-items-center pt-[5vh] sm:pt-[5vh]',
      content: 'w-[calc(100%-2rem)] max-w-2xl sm:max-w-2xl',
    }"
  >
    <template #body>
      <UTabs
        v-model="activeTab"
        :items="tabItems"
        :content="false"
        size="sm"
        class="mb-4 w-full"
      />

      <div v-if="activeTab === 'profile'" class="space-y-5">
        <div class="flex items-center gap-4">
          <UAvatar
            :src="profile.avatar.src"
            :alt="profile.avatar.alt"
            size="3xl"
            class="ring-2 ring-default"
          />
          <div class="min-w-0">
            <h3 class="truncate text-lg font-semibold text-highlighted">
              {{ profile.name }}
            </h3>
            <p class="truncate text-sm text-muted">
              {{ profile.email }}
            </p>
            <UBadge color="neutral" variant="subtle" class="mt-2">
              {{ profile.role }}
            </UBadge>
          </div>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between gap-2">
            <h4 class="text-sm font-semibold text-highlighted">
              {{ t('docetra.userProfile.permissionsTitle') }}
            </h4>
            <span class="text-xs text-muted">
              {{ t('docetra.userProfile.permissionCount', { n: permissionCount }) }}
            </span>
          </div>

          <div
            v-if="permissionGroups.length"
            class="max-h-72 space-y-2 overflow-y-auto rounded-md border border-default bg-elevated/40 p-2"
          >
            <div
              v-for="group in permissionGroups"
              :key="group.documentType"
              class="rounded-md border border-default/70 bg-default px-3 py-2.5"
            >
              <p class="text-sm font-medium text-highlighted">
                {{ moduleLabel(group.labelKey, group.documentType) }}
              </p>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <UBadge
                  v-for="action in group.actions"
                  :key="`${group.documentType}-${action}`"
                  color="primary"
                  variant="soft"
                  size="sm"
                >
                  {{ actionLabel(action) }}
                </UBadge>
              </div>
            </div>
          </div>

          <p v-else class="rounded-md border border-dashed border-default px-3 py-6 text-center text-sm text-muted">
            {{ t('docetra.userProfile.noPermissions') }}
          </p>
        </div>
      </div>

      <div v-else class="space-y-4">
        <p class="text-sm text-muted">
          {{ t('docetra.userProfile.passwordHelp') }}
        </p>

        <UForm
          :schema="passwordSchema"
          :state="passwordState"
          class="space-y-4"
          @submit="onPasswordSubmit"
        >
          <UFormField
            :label="t('docetra.userProfile.currentPassword')"
            name="currentPassword"
            required
          >
            <UInput
              v-model="passwordState.currentPassword"
              type="password"
              autocomplete="current-password"
              class="w-full"
            />
          </UFormField>

          <UFormField
            :label="t('pages.forgetPassword.newPassword')"
            name="password"
            required
          >
            <UInput
              v-model="passwordState.password"
              type="password"
              autocomplete="new-password"
              class="w-full"
            />
          </UFormField>

          <UFormField
            :label="t('pages.forgetPassword.confirmPassword')"
            name="passwordConfirmation"
            required
          >
            <UInput
              v-model="passwordState.passwordConfirmation"
              type="password"
              autocomplete="new-password"
              class="w-full"
            />
          </UFormField>

          <div class="flex justify-end pt-1">
            <UButton
              type="submit"
              color="primary"
              :loading="submitting"
            >
              {{ t('docetra.userProfile.updatePassword') }}
            </UButton>
          </div>
        </UForm>
      </div>
    </template>
  </UModal>
</template>
