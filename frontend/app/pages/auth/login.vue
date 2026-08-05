<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { useAuthSession } from '~/utils/auth/session'
import { readRememberMe } from '~/utils/auth/remember-me'
import { loginWithCredentials } from '~/adapters/auth'
import { MOCK_LOGIN_ACCOUNTS } from '~/utils/auth/mock-login'

definePageMeta({
  layout: 'auth',
})

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const authSession = useAuthSession()
const submitting = ref(false)
const googleLoading = ref(false)
const termsOpen = ref(false)
const acceptTerms = ref(false)
const loginForm = useTemplateRef<{ state?: Record<string, unknown> }>('loginForm')

useSeoMeta({
  title: () => t('pages.auth.loginTitle'),
  description: () => t('pages.auth.loginDesc'),
})

const remembered = readRememberMe()

function buildFields(): AuthFormField[] {
  return [
    {
      name: 'email',
      type: 'email',
      size: 'lg',
      label: t('pages.auth.email'),
      placeholder: t('pages.auth.emailPlaceholder'),
      required: true,
      autocomplete: 'username',
      defaultValue: remembered.email || MOCK_LOGIN_ACCOUNTS[0]!.email,
    },
    {
      name: 'password',
      type: 'password',
      size: 'lg',
      label: t('pages.auth.password'),
      placeholder: t('pages.auth.passwordPlaceholder'),
      required: true,
      autocomplete: 'current-password',
      defaultValue: '',
    },
  ]
}

const fields = ref<AuthFormField[]>(buildFields())

watch(locale, () => {
  fields.value = buildFields()
})

const schema = computed(() => z.object({
  email: z.email({ error: t('pages.auth.emailRequired') }),
  password: z.string().min(6, { error: t('pages.auth.passwordRequired') }),
}))

type Schema = {
  email: string
  password: string
}

async function completeLogin(token: string, user: { name: string }) {
  authSession.login(token, user as any)
  await router.push('/')
}

function ensureTermsAccepted(): boolean {
  if (acceptTerms.value) return true
  toast.add({
    title: t('pages.auth.termsRequired'),
    description: t('pages.auth.termsRequiredDesc'),
    color: 'warning',
  })
  return false
}

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  if (submitting.value) return
  if (!ensureTermsAccepted()) return

  submitting.value = true
  try {
    const formState = loginForm.value?.state || {}
    const email = String(payload.data?.email ?? formState.email ?? '').trim()
    const password = String(payload.data?.password ?? formState.password ?? '')

    const result = await loginWithCredentials(email, password)
    const payloadData = (result as { data?: { user?: { name: string }, token?: string } }).data
    const user = payloadData?.user

    if (!user || !payloadData?.token) {
      toast.add({
        title: t('pages.auth.loginFailed'),
        description: t('pages.auth.loginFailedDesc'),
        color: 'error',
      })
      return
    }

    await completeLogin(payloadData.token, user)
  }
  catch {
    toast.add({
      title: t('pages.auth.loginFailed'),
      description: t('pages.auth.loginFailedDesc'),
      color: 'error',
    })
  }
  finally {
    submitting.value = false
  }
}

async function onGoogleLogin() {
  if (googleLoading.value) return
  if (!ensureTermsAccepted()) return

  googleLoading.value = true
  try {
    // OAuth provider wiring comes later — mock success keeps the UI flow usable.
    await new Promise(resolve => setTimeout(resolve, 600))
    toast.add({
      title: t('pages.auth.googleComingSoon'),
      description: t('pages.auth.googleComingSoonDesc'),
      color: 'neutral',
    })
  }
  finally {
    googleLoading.value = false
  }
}

const googleProvider = computed(() => ({
  label: t('pages.auth.loginWithGoogle'),
  icon: 'i-simple-icons-google',
  color: 'neutral' as const,
  variant: 'outline' as const,
  block: true,
  size: 'lg' as const,
  loading: googleLoading.value,
  disabled: submitting.value,
}))
</script>

<template>
  <div class="flex flex-col items-center justify-center">
    <UAuthForm
      ref="loginForm"
      :schema="schema"
      :title="t('pages.auth.loginTitle')"
      icon="i-lucide-lock"
      :fields="fields"
      :loading="submitting"
      :submit="{
        label: t('pages.auth.loginBtn'),
        class: 'w-full h-10! text-xl font-normal',
        loading: submitting,
      }"
      @submit="onSubmit"
    >
      <template #leading>
        <img src="/assets/images/logo.png" alt="Logo" class="mx-auto h-20 w-auto rounded-full shadow">
      </template>

      <template #validation>
        <div class="flex items-center gap-1.5 text-left">
          <UCheckbox
            v-model="acceptTerms"
            size="xs"
          />
          <p class="text-xs leading-tight text-muted">
            <button
              type="button"
              class="font-medium text-toned underline underline-offset-2 hover:text-primary"
              @click="termsOpen = true"
            >
              {{ t('pages.auth.termsLink') }}
            </button>
          </p>
        </div>
      </template>

      <template #footer>
        <div class="space-y-3">
          <USeparator :label="t('pages.auth.orContinueWith')" />

          <UButton
            v-bind="googleProvider"
            class="w-full"
            @click="onGoogleLogin"
          />

          <div class="text-center">
            <UButton
              variant="link"
              size="sm"
              to="/auth/forget-password"
              class="text-muted-foreground underline"
            >
              {{ t('pages.auth.forgotPassword') }}
            </UButton>
          </div>

          <div class="text-center">
            <span class="text-sm font-normal text-muted">{{ $t('settings.aboutCopyright') }}</span>
          </div>
        </div>
      </template>
    </UAuthForm>

    <AuthAppAuthTermsDialog v-model:open="termsOpen" />
  </div>
</template>
