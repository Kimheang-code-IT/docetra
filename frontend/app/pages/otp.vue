<script setup lang="ts">
import { resendOtp, verifyOtp } from '~/adapters/auth'

definePageMeta({
  layout: 'auth',
})

const { t } = useI18n()

useSeoMeta({
  title: () => t('pages.otp.title'),
  description: () => t('pages.otp.desc'),
})

const otp = ref<string[]>(['', '', '', '', '', ''])
const loading = ref(false)
const resendLoading = ref(false)
const toast = useToast()
const router = useRouter()

function isOtpComplete() {
  return otp.value.every(d => d && d.length === 1)
}

async function onSubmit() {
  if (!isOtpComplete()) return
  loading.value = true
  try {
    await verifyOtp(otp.value.join(''))
    toast.add({ title: t('pages.otp.verify'), color: 'success' })
    await router.push('/login')
  }
  catch {
    toast.add({ title: t('pages.auth.loginFailed'), color: 'error' })
  }
  finally {
    loading.value = false
  }
}

async function onResend() {
  resendLoading.value = true
  try {
    await resendOtp()
    toast.add({
      title: t('pages.otp.newCodeSent'),
      color: 'primary',
    })
  }
  finally {
    resendLoading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center">
    <div class="w-full max-w-xl">
      <div class="flex flex-col items-center gap-4">
        <img src="/assets/images/logo.png" alt="Logo" class="h-20 w-20 rounded-full shadow">
        <h2 class="text-2xl font-normal">{{ $t('pages.otp.title') }}</h2>
        <p class="text-center text-sm text-muted">{{ $t('pages.otp.desc') }}</p>
      </div>
      <form class="mt-8 flex flex-col items-center justify-center gap-6" @submit.prevent="onSubmit">
        <UPinInput
          v-model="otp"
          :length="6"
          size="xl"
          placeholder="○"
          autofocus
          required
        />
        <div class="flex items-center justify-center">
          <span class="text-sm text-muted">{{ $t('pages.otp.didntGetCode') }}</span>
          <UButton
            variant="link"
            size="sm"
            class="text-primary"
            :loading="resendLoading"
            :disabled="resendLoading"
            @click="onResend"
          >
            {{ $t('pages.otp.resend') }}
          </UButton>
        </div>
        <UButton
          type="submit"
          color="primary"
          class="text-md flex w-full items-center justify-center font-normal"
          :loading="loading"
          :disabled="!isOtpComplete()"
        >
          {{ $t('pages.otp.verify') }}
        </UButton>
      </form>

      <div class="mt-4 space-y-2 text-center">
        <UButton variant="link" size="sm" to="/login" class="text-muted">
          <UIcon name="i-lucide-arrow-left" class="mr-1" />
          {{ $t('pages.forgetPassword.backToLogin') }}
        </UButton>
        <div>
          <span class="font-black">© <span class="text-sm font-normal">{{ $t('pages.auth.departmentLine') }}</span></span>
        </div>
      </div>
    </div>
  </div>
</template>
