<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { useAuthSession } from '~/utils/auth/session'
import { readRememberMe } from '~/utils/auth/remember-me'
import { loginWithCredentials } from '~/adapters/auth'
import { usePageSeo } from '~/composables/usePageSeo'

definePageMeta({
  layout: 'auth',
})

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const authSession = useAuthSession()
const config = useRuntimeConfig()
const submitting = ref(false)
const googleLoading = ref(false)
const loginForm = useTemplateRef<{ state?: Record<string, unknown> }>('loginForm')

usePageSeo({
  title: () => t('pages.auth.loginTitle'),
  description: () => t('pages.auth.loginDesc'),
  robots: 'index, follow',
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
      defaultValue: remembered.email || '',
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

async function completeLogin(token: string | undefined, user: { name: string }) {
  authSession.login(config.public.authMode === 'bearer' ? token : undefined, user as any)
  await router.push('/')
}

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  if (submitting.value) return

  submitting.value = true
  try {
    const formState = loginForm.value?.state || {}
    const email = String(payload.data?.email ?? formState.email ?? '').trim()
    const password = String(payload.data?.password ?? formState.password ?? '')

    const result = await loginWithCredentials(email, password)
    const payloadData = (result as { data?: { user?: { name: string }, token?: string } }).data
    const user = payloadData?.user

    const requiresToken = config.public.authMode === 'bearer'
    if (!user || (requiresToken && !payloadData?.token)) {
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

  googleLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 0))
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

      <template #footer>
        <div class="space-y-3">
          <USeparator :label="t('pages.auth.orContinueWith')" />

          <UButton
            v-bind="googleProvider"
            class="w-full"
            @click="onGoogleLogin"
          >
            <template #leading>
              <svg
                class="size-5 shrink-0"
                viewBox="0 0 48 48"
                fill="none"
                aria-hidden="true"
              >
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
              </svg>
            </template>
          </UButton>

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
  </div>
</template>
