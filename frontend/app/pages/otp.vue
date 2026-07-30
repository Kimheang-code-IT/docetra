<script setup lang="ts">


definePageMeta({
  layout: 'auth'
})

const { t } = useI18n()

useSeoMeta({
  title: () => t('pages.otp.title'),
  description: () => t('pages.otp.desc')
})


const otp = ref(['', '', '', '', '', ''])
const loading = ref(false)
const resendLoading = ref(false)
const resendMessage = ref('')
const toast = useToast()
const router = useRouter()

function isOtpComplete() {
  return otp.value.every(d => d && d.length === 1)
}

async function onSubmit() {
  if (!isOtpComplete()) return
  loading.value = true
  setTimeout(async () => {
    loading.value = false
    await router.push('/')
  }, 1200)
}

async function onResend() {
  resendLoading.value = true
  resendMessage.value = ''
  setTimeout(() => {
    resendLoading.value = false
    resendMessage.value = t('pages.otp.newCodeSent')
    toast.add({
      title: t('pages.otp.newCodeSent'),
      color: 'primary'
    })
  }, 1200)
}
</script>

<template>
  <div class="flex items-center justify-center">
    <div class="w-full max-w-xl">
      <div class="flex flex-col items-center gap-4">
        <img src="/assets/images/logo.png" alt="MOEYS Logo" class="h-20 w-20 rounded-full shadow" />
        <h2 class="text-2xl font-normal">{{ $t('pages.otp.title') }}</h2>
      </div>
      <form class="flex flex-col items-center justify-center gap-6 mt-8" @submit.prevent="onSubmit">
        <UPinInput
          v-model="otp"
          :length="6"
          size="xl" 
          placeholder="○"
          autofocus
          required
        />
      <div class="flex items-center justify-center">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('pages.otp.didntGetCode') }}</span>
        <UButton
          variant="link"
          size="sm"
          class="text-primary"
          :loading="resendLoading"
          :disabled="resendLoading"
          @click="onResend"
        >{{ $t('pages.otp.resend') }}</UButton>
      </div>
        <UButton
          type="submit"
          color="primary"
          sizemd="md"
          class="text-md font-normal w-full flex items-center justify-center"
          :loading="loading"
          :disabled="!isOtpComplete()"
        >
          {{ $t('pages.otp.verify') }}
        </UButton>
      </form>

      <div class="text-center mt-4 space-y-2">
        <UButton variant="link" size="sm" to="/login" class="text-muted-foreground">
          <UIcon name="i-lucide-arrow-left" class="mr-1" />
          {{ $t('pages.forgetPassword.backToLogin') }}
        </UButton>
        <div>
          <span class="font-black">© <span class="font-normal text-sm">{{ $t('pages.auth.departmentLine') }}</span></span>
        </div>
      </div>
    </div>
  </div>
</template>


