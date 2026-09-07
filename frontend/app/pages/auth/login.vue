<script setup lang="ts">
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { useAuthSession } from '~/utils/auth/session'
import { createLoginSchema, createSetupSchema } from '~/utils/auth/login-schema'
import { readRememberMe, writeRememberMe } from '~/utils/auth/remember-me'
import { fetchErrorStatus } from '~/utils/api/error-policy'
import { useAuthApi } from '~/composables/auth/useAuthApi'
import { usePageSeo } from '~/composables/usePageSeo'
import type { AuthUser } from '~/types/auth-user'

definePageMeta({
  layout: 'auth',
})

const { t, locale } = useI18n()
const { getBootstrapStatus, loginWithCredentials, registerFirstAdministrator } = useAuthApi()
const router = useRouter()
const toast = useToast()
const authSession = useAuthSession()
const config = useRuntimeConfig()
const submitting = ref(false)
const setupMode = ref(false)
const showPassword = ref(false)
const rememberMe = ref(readRememberMe().enabled)
const loginForm = useTemplateRef<{ state?: Record<string, unknown> }>('loginForm')

usePageSeo({
  title: () => t(setupMode.value ? 'pages.auth.setupTitle' : 'pages.auth.loginTitle'),
  description: () => t(setupMode.value ? 'pages.auth.setupDesc' : 'pages.auth.loginDesc'),
  robots: 'index, follow',
})

const remembered = readRememberMe()

function buildFields(): AuthFormField[] {
  const emailField: AuthFormField = {
    name: 'email',
    type: 'email',
    size: 'lg',
    label: t('pages.auth.email'),
    placeholder: t('pages.auth.emailPlaceholder'),
    required: true,
    autocomplete: 'username',
    defaultValue: remembered.email || '',
  }
  const passwordField: AuthFormField = {
    name: 'password',
    type: showPassword.value ? 'text' : 'password',
    size: 'lg',
    label: t('pages.auth.password'),
    placeholder: t('pages.auth.passwordPlaceholder'),
    required: true,
    autocomplete: setupMode.value ? 'new-password' : 'current-password',
    defaultValue: '',
  }
  if (!setupMode.value) return [emailField, passwordField]
  return [
    {
      name: 'name',
      type: 'text',
      size: 'lg',
      label: t('pages.auth.name'),
      placeholder: t('pages.auth.namePlaceholder'),
      required: true,
      autocomplete: 'name',
      defaultValue: '',
    },
    emailField,
    passwordField,
    {
      name: 'passwordConfirmation',
      type: 'password',
      size: 'lg',
      label: t('pages.auth.passwordConfirmation'),
      placeholder: t('pages.auth.passwordConfirmationPlaceholder'),
      required: true,
      autocomplete: 'new-password',
      defaultValue: '',
    },
  ]
}

const fields = ref<AuthFormField[]>(buildFields())

watch([locale, setupMode, showPassword], () => {
  fields.value = buildFields()
})

const schema = computed(() => setupMode.value
  ? createSetupSchema({
      emailRequired: t('pages.auth.emailRequired'),
      nameRequired: t('pages.auth.nameRequired'),
      passwordTooShort: t('pages.auth.passwordTooShort'),
      passwordMismatch: t('pages.auth.passwordMismatch'),
    })
  : createLoginSchema(
      t('pages.auth.emailRequired'),
      t('pages.auth.passwordRequired'),
    ))

type LoginSchema = {
  email: string
  password: string
}

type SetupSchema = LoginSchema & {
  name: string
  passwordConfirmation: string
}

onMounted(async () => {
  try {
    const response = await getBootstrapStatus()
    const payload = response as { data?: { needsSetup?: boolean }, needsSetup?: boolean }
    setupMode.value = Boolean(payload.data?.needsSetup ?? payload.needsSetup)
  }
  catch {
    setupMode.value = false
  }
})

async function completeLogin(token: string | undefined, user: AuthUser) {
  authSession.login(config.public.authMode === 'bearer' ? token : undefined, user)
  writeRememberMe({ enabled: rememberMe.value, email: user.email || '' })
  await router.push('/')
}

async function onSubmit(payload: FormSubmitEvent<LoginSchema | SetupSchema>) {
  if (submitting.value) return

  submitting.value = true
  try {
    const formState = loginForm.value?.state || {}
    const email = String(payload.data?.email ?? formState.email ?? '').trim()
    const password = String(payload.data?.password ?? formState.password ?? '')
    const name = String((payload.data as SetupSchema)?.name ?? formState.name ?? '').trim()
    const passwordConfirmation = String(
      (payload.data as SetupSchema)?.passwordConfirmation ?? formState.passwordConfirmation ?? '',
    )

    const result = setupMode.value
      ? await registerFirstAdministrator({ name, email, password, passwordConfirmation })
      : await loginWithCredentials(email, password)
    const envelope = result as { data?: { user?: AuthUser, token?: string } | AuthUser, user?: AuthUser, token?: string }
    const data = envelope.data
    const nestedUser = data && typeof data === 'object' && 'user' in data
      ? (data as { user?: AuthUser, token?: string }).user
      : undefined
    const user = nestedUser
      || (data && typeof data === 'object' && 'email' in data ? data as AuthUser : undefined)
      || envelope.user
    const token = (data && typeof data === 'object' && 'token' in data
      ? (data as { token?: string }).token
      : undefined) || envelope.token

    const requiresToken = config.public.authMode === 'bearer'
    if (!user?.email || (requiresToken && !token)) {
      toast.add({
        title: t(setupMode.value ? 'pages.auth.setupFailed' : 'pages.auth.loginFailed'),
        description: t(setupMode.value ? 'pages.auth.setupFailedDesc' : 'pages.auth.loginFailedDesc'),
        color: 'error',
      })
      return
    }

    await completeLogin(token, user)
  }
  catch (error: unknown) {
    const status = fetchErrorStatus(error)
    let description = ''
    if (status === 429) {
      description = t('pages.auth.rateLimited', { minutes: 15 })
    }
    else if (status && status >= 500) {
      description = t('pages.auth.connectionError')
    }
    else {
      const message = error instanceof Error ? error.message : ''
      description = message || t(setupMode.value ? 'pages.auth.setupFailedDesc' : 'pages.auth.loginFailedDesc')
    }
    toast.add({
      title: t(setupMode.value ? 'pages.auth.setupFailed' : 'pages.auth.loginFailed'),
      description,
      color: 'error',
    })
  }
  finally {
    submitting.value = false
  }
}

</script>

<template>
  <div class="flex flex-col items-center justify-center">
    <UAuthForm
      ref="loginForm"
      :schema="schema"
      :title="t(setupMode ? 'pages.auth.setupTitle' : 'pages.auth.loginTitle')"

      :icon="setupMode ? 'i-lucide-shield-plus' : 'i-lucide-lock'"
      :fields="fields"
      :loading="submitting"
      :submit="{
        label: t(setupMode ? 'pages.auth.setupBtn' : 'pages.auth.loginBtn'),
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
          <template v-if="!setupMode">
            <div class="flex items-center justify-between px-1">
              <UCheckbox
                v-model="rememberMe"
                :label="t('pages.auth.remember')"
                size="sm"
                class="text-muted-foreground"
              />
              <UButton
                variant="link"
                size="sm"
                color="neutral"
                class="text-muted-foreground underline"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? t('pages.auth.hidePassword') : t('pages.auth.showPassword') }}
              </UButton>
            </div>
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
          </template>

          <div class="text-center">
            <span class="text-sm font-normal text-muted">{{ $t('settings.aboutCopyright') }}</span>
          </div>
        </div>
      </template>
    </UAuthForm>
  </div>
</template>
