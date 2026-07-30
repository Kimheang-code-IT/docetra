<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({
  layout: 'auth',
})

const { t } = useI18n()
const router = useRouter()
const toast = useToast()
const submitting = ref(false)
const sent = ref(false)
const sentEmail = ref('')

useSeoMeta({
  title: () => t('pages.forgetPassword.title'),
  description: () => t('pages.forgetPassword.desc'),
})

const schema = computed(() => z.object({
  email: z.email({ error: t('pages.auth.emailRequired') }),
}))

type Schema = { email: string }

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  if (submitting.value) return
  submitting.value = true
  try {
    await new Promise((resolve) => setTimeout(resolve, 800))
    sentEmail.value = payload.data.email
    sent.value = true
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

function goToOtp() {
  router.push('/otp')
}
</script>

<template>
  <div class="flex flex-col items-center justify-center">
    <div v-if="!sent" class="w-full">
      <UAuthForm
        :schema="schema"
        :title="t('pages.forgetPassword.title')"
        :description="t('pages.forgetPassword.desc')"
        icon="i-lucide-key-round"
        :fields="[
          {
            name: 'email',
            type: 'email',
            size: 'lg',
            label: t('pages.auth.email'),
            placeholder: t('pages.auth.emailPlaceholder'),
            required: true,
            autocomplete: 'email',
          },
        ]"
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
            <UButton variant="link" size="sm" to="/login" class="text-muted-foreground">
              <UIcon name="i-lucide-arrow-left" class="mr-1" />
              {{ t('pages.forgetPassword.backToLogin') }}
            </UButton>
            <div>
              <span class="font-black">© <span class="font-normal text-sm">{{ $t('pages.auth.departmentLine') }}</span></span>
            </div>
          </div>
        </template>
      </UAuthForm>
    </div>

    <div v-else class="w-full max-w-xl">
      <div class="flex flex-col items-center gap-4 mb-6">
        <img src="/assets/images/logo.png" alt="Logo" class="h-20 w-auto rounded-full shadow">
        <div class="flex items-center justify-center w-16 h-16 rounded-full bg-success/15">
          <UIcon name="i-lucide-mail-check" class="text-success text-3xl" />
        </div>
        <h2 class="text-2xl font-normal text-center">{{ t('pages.forgetPassword.sentTitle') }}</h2>
        <p class="text-center text-muted-foreground text-sm leading-relaxed px-4">
          {{ t('pages.forgetPassword.sentDesc', { email: sentEmail }) }}
        </p>
      </div>

      <div class="flex flex-col gap-3">
        <UButton
          color="primary"
          size="lg"
          class="w-full justify-center h-10 text-base font-normal"
          @click="goToOtp"
        >
          {{ t('pages.forgetPassword.enterOtp') }}
        </UButton>
        <UButton
          variant="ghost"
          size="sm"
          class="w-full justify-center text-muted-foreground"
          to="/login"
        >
          <UIcon name="i-lucide-arrow-left" class="mr-1" />
          {{ t('pages.forgetPassword.backToLogin') }}
        </UButton>
      </div>

      <div class="text-center mt-4">
        <span class="font-black">© <span class="font-normal text-sm">{{ $t('pages.auth.departmentLine') }}</span></span>
      </div>
    </div>
  </div>
</template>
