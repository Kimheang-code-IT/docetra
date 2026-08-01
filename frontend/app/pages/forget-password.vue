<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import {
  requestPasswordReset,
  resendPasswordResetCode,
  verifyPasswordResetCode,
} from '~/adapters/auth'

definePageMeta({
  layout: 'auth',
})

const { t } = useI18n()
const router = useRouter()
const toast = useToast()
const submitting = ref(false)
const verifying = ref(false)
const resending = ref(false)
const sent = ref(false)
const sentEmail = ref('')
const code = ref<string[]>(['', '', '', '', '', ''])

useSeoMeta({
  title: () => t('pages.forgetPassword.title'),
  description: () => t('pages.forgetPassword.desc'),
})

const schema = computed(() => z.object({
  email: z.email({ error: t('pages.auth.emailRequired') }),
}))

const fields = computed(() => [
  {
    name: 'email',
    type: 'email' as const,
    size: 'lg' as const,
    label: t('pages.auth.email'),
    placeholder: t('pages.auth.emailPlaceholder'),
    required: true,
    autocomplete: 'email',
  },
])

type Schema = { email: string }

const codeComplete = computed(() =>
  code.value.every(digit => digit && digit.length === 1),
)

const codeValue = computed(() => code.value.join(''))

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  if (submitting.value) return
  submitting.value = true
  try {
    await requestPasswordReset(payload.data.email)
    sentEmail.value = payload.data.email
    sent.value = true
    code.value = ['', '', '', '', '', '']
    toast.add({
      title: t('pages.forgetPassword.sentTitle'),
      description: t('pages.forgetPassword.sentDesc', { email: payload.data.email }),
      color: 'success',
    })
  }
  finally {
    submitting.value = false
  }
}

async function onVerifyCode() {
  if (!codeComplete.value || verifying.value || !sentEmail.value) return
  verifying.value = true
  try {
    await verifyPasswordResetCode(sentEmail.value, codeValue.value)
    toast.add({
      title: t('pages.forgetPassword.codeVerified'),
      description: t('pages.forgetPassword.codeVerifiedDesc'),
      color: 'success',
    })
    await router.push('/login')
  }
  catch {
    toast.add({
      title: t('pages.forgetPassword.codeInvalid'),
      description: t('pages.forgetPassword.codeInvalidDesc'),
      color: 'error',
    })
  }
  finally {
    verifying.value = false
  }
}

async function onResendCode() {
  if (resending.value || !sentEmail.value) return
  resending.value = true
  try {
    await resendPasswordResetCode(sentEmail.value)
    code.value = ['', '', '', '', '', '']
    toast.add({
      title: t('pages.forgetPassword.codeResent'),
      color: 'success',
    })
  }
  catch {
    toast.add({
      title: t('pages.forgetPassword.codeResendFailed'),
      color: 'error',
    })
  }
  finally {
    resending.value = false
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center">
    <div v-if="!sent" class="w-full">
      <UAuthForm
        :schema="schema"
        :title="t('pages.forgetPassword.title')"
        icon="i-lucide-key-round"
        :fields="fields"
        :loading="submitting"
        :submit="{
          label: t('pages.forgetPassword.submitBtn'),
          class: 'w-full h-10! text-xl font-normal',
          loading: submitting,
        }"
        @submit="onSubmit"
      >
        <template #leading>
          <img src="/assets/images/logo.png" alt="Logo" class="h-20 w-auto mx-auto rounded-full shadow">
        </template>

        <template #footer>
          <div class="text-center space-y-2">
            <UButton variant="link" size="sm" to="/login" class="text-muted-foreground underline">
              <UIcon name="i-lucide-arrow-left" class="mr-1" />
              {{ t('pages.forgetPassword.backToLogin') }}
            </UButton>
            <div>
              <span class="font-normal text-sm text-muted">{{ $t('settings.aboutCopyright') }}</span>
            </div>
          </div>
        </template>
      </UAuthForm>
    </div>

    <div v-else class="w-full max-w-xl">
      <div class="flex flex-col items-center gap-4 mb-6">
        <img src="/assets/images/logo.png" alt="Logo" class="h-20 w-auto rounded-full shadow">
        <h2 class="text-2xl font-normal text-center">{{ t('pages.forgetPassword.sentTitle') }}</h2>
      </div>

      <form class="flex flex-col items-center gap-5" @submit.prevent="onVerifyCode">
        <UPinInput
          v-model="code"
          :length="6"
          size="xl"
          placeholder="○"
          autofocus
          otp
          required
          :aria-label="t('pages.forgetPassword.enterCode')"
        />

        <div class="flex items-center justify-center gap-1">
          <span class="text-sm text-muted">{{ t('pages.forgetPassword.didntGetCode') }}</span>
          <UButton
            variant="link"
            size="sm"
            class="underline"
            :loading="resending"
            :disabled="resending"
            @click="onResendCode"
          >
            {{ t('pages.forgetPassword.resendCode') }}
          </UButton>
        </div>

        <UButton
          type="submit"
          color="primary"
          size="lg"
          class="h-10 w-full justify-center text-base font-normal"
          :loading="verifying"
          :disabled="!codeComplete || verifying"
        >
          {{ t('pages.forgetPassword.verifyCode') }}
        </UButton>
      </form>

      <div class="mt-4 flex flex-col gap-3">
        <UButton
          variant="link"
          size="sm"
          class="w-full justify-center text-muted-foreground underline"
          to="/login"
        >
          <UIcon name="i-lucide-arrow-left" class="mr-1" />
          {{ t('pages.forgetPassword.backToLogin') }}
        </UButton>
      </div>

      <div class="mt-4 text-center">
        <span class="font-normal text-sm text-muted">{{ $t('settings.aboutCopyright') }}</span>
      </div>
    </div>
  </div>
</template>
