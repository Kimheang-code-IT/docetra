<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { changePassword, removeProfileAvatar, updateProfileAvatar } from '~/adapters/auth'
import { useAuthStore } from '~/stores/auth'
import { resolveUserAvatar } from '~/utils/auth/user-avatar'
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
const avatarSubmitting = ref(false)
const avatarInputRef = ref<HTMLInputElement | null>(null)
const photoPreviewOpen = ref(false)

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
      src: resolveUserAvatar(user),
      alt: user?.name || 'User',
    },
  }
})

const hasCustomAvatar = computed(() => Boolean(auth.user?.avatar))

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
    photoPreviewOpen.value = false
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

function openAvatarPicker() {
  if (avatarSubmitting.value) return
  avatarInputRef.value?.click()
}

function openPhotoPreview() {
  if (avatarSubmitting.value) return
  photoPreviewOpen.value = true
}

function onCameraClick(event: Event) {
  event.stopPropagation()
  openAvatarPicker()
}

async function onAvatarPick(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || avatarSubmitting.value) return

  if (!SAFE_RASTER_IMAGE_TYPES.includes(file.type as (typeof SAFE_RASTER_IMAGE_TYPES)[number])) {
    toast.add({ title: t('docetra.common.imageInvalidType'), color: 'error' })
    return
  }
  if (!isSafeRasterImage(file, 2)) {
    toast.add({ title: t('docetra.common.imageTooLarge', { size: 2 }), color: 'error' })
    return
  }

  avatarSubmitting.value = true
  try {
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result || ''))
      reader.onerror = () => reject(new Error('read failed'))
      reader.readAsDataURL(file)
    })
    await updateProfileAvatar(dataUrl)
    photoPreviewOpen.value = true
    toast.add({
      title: t('docetra.userProfile.photoUpdated'),
      description: t('docetra.userProfile.photoUpdatedDesc'),
      color: 'success',
    })
  }
  catch {
    toast.add({
      title: t('docetra.userProfile.photoUpdateFailed'),
      description: t('docetra.userProfile.photoUpdateFailedDesc'),
      color: 'error',
    })
  }
  finally {
    avatarSubmitting.value = false
  }
}

async function onRemoveAvatar() {
  if (avatarSubmitting.value || !hasCustomAvatar.value) return
  avatarSubmitting.value = true
  try {
    await removeProfileAvatar()
    photoPreviewOpen.value = false
    toast.add({
      title: t('docetra.userProfile.photoRemoved'),
      description: t('docetra.userProfile.photoRemovedDesc'),
      color: 'success',
    })
  }
  catch {
    toast.add({
      title: t('docetra.userProfile.photoRemoveFailed'),
      description: t('docetra.userProfile.photoRemoveFailedDesc'),
      color: 'error',
    })
  }
  finally {
    avatarSubmitting.value = false
  }
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
        <div class="flex flex-col items-center gap-4 pb-1 text-center">
          <div class="relative inline-flex">
            <button
              type="button"
              class="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              :aria-label="t('docetra.userProfile.viewPhoto')"
              @click="openPhotoPreview"
            >
              <img
                :src="profile.avatar.src"
                :alt="profile.avatar.alt"
                class="size-16 rounded-full object-cover ring-2 ring-default sm:size-20"
                referrerpolicy="no-referrer"
              >
            </button>
            <span
              class="absolute -inset-e-2 -top-2 z-10 max-w-[6.5rem] truncate rounded-full bg-elevated px-2 py-0.5 text-[10px] font-semibold leading-none text-toned ring-1 ring-default shadow-sm"
              :title="profile.role"
            >
              {{ profile.role }}
            </span>
            <button
              type="button"
              class="absolute -bottom-1 -end-1 z-10 inline-flex size-7 items-center justify-center rounded-full border-2 border-default bg-default text-highlighted shadow-sm transition hover:bg-elevated disabled:opacity-60"
              :aria-label="t('docetra.userProfile.changePhoto')"
              :disabled="avatarSubmitting"
              @click="onCameraClick"
            >
              <UIcon
                :name="avatarSubmitting ? 'i-lucide-loader-circle' : 'i-lucide-camera'"
                class="size-4"
                :class="avatarSubmitting ? 'animate-spin' : ''"
              />
            </button>
            <input
              ref="avatarInputRef"
              type="file"
              class="hidden"
              :accept="SAFE_RASTER_IMAGE_ACCEPT"
              @change="onAvatarPick"
            >
          </div>
          <div class="min-w-0 max-w-full space-y-1">
            <h3 class="truncate text-lg font-semibold text-highlighted sm:text-xl">
              {{ profile.name }}
            </h3>
            <p class="truncate text-sm text-muted">
              {{ profile.email }}
            </p>
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

  <UModal
    v-model:open="photoPreviewOpen"
    :title="profile.name"
    :ui="{
      overlay: 'place-items-center justify-items-center',
      content: 'w-[calc(100%-2rem)] max-w-lg sm:max-w-2xl',
    }"
  >
    <template #body>
      <div class="relative overflow-hidden rounded-xl border border-default bg-elevated/30">
        <img
          :src="profile.avatar.src"
          :alt="profile.avatar.alt"
          class="mx-auto max-h-[min(80vh,36rem)] w-full object-contain"
          referrerpolicy="no-referrer"
        >
        <button
          v-if="hasCustomAvatar"
          type="button"
          class="absolute top-2 end-2 inline-flex size-9 items-center justify-center rounded-full bg-error text-white shadow-md transition hover:bg-error/90 disabled:opacity-60"
          :aria-label="t('docetra.userProfile.removePhoto')"
          :disabled="avatarSubmitting"
          @click="onRemoveAvatar"
        >
          <UIcon
            :name="avatarSubmitting ? 'i-lucide-loader-circle' : 'i-lucide-trash-2'"
            class="size-4"
            :class="avatarSubmitting ? 'animate-spin' : ''"
          />
        </button>
      </div>
    </template>
  </UModal>
</template>
