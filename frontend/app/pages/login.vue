<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { useAuthSession } from '~/utils/auth/session'
import { readRememberMe, writeRememberMe } from '~/utils/auth/remember-me'
import { MOCK_LOGIN_ACCOUNTS } from '~/utils/auth/mock-login'
import { loginWithCredentials } from '~/adapters/auth'

definePageMeta({
  layout: 'auth',
})

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const authSession = useAuthSession()
const submitting = ref(false)

// UAuthForm owns its own internal state — do NOT use v-model:state
// (it overrides Form validation with a separate object and breaks password sync).
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
    {
      name: 'remember',
      type: 'checkbox',
      label: t('pages.auth.remember'),
      defaultValue: remembered.enabled,
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
  remember: z.boolean().optional(),
}))

type Schema = {
  email: string
  password: string
  remember?: boolean
}

const demoHint = computed(() => {
  const accounts = MOCK_LOGIN_ACCOUNTS
    .map((account) => `${account.email} / ${account.password}`)
    .join(' · ')
  return t('pages.auth.demoHint', { accounts })
})

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  if (submitting.value) return
  submitting.value = true

  try {
    const formState = loginForm.value?.state || {}
    const email = String(payload.data?.email ?? formState.email ?? '').trim()
    const password = String(payload.data?.password ?? formState.password ?? '')
    const remember = Boolean(payload.data?.remember ?? formState.remember)

    const result = await loginWithCredentials(email, password)
    const payloadData = (result as { data?: { user?: { name: string }; token?: string } }).data
    const user = payloadData?.user

    if (!user || !payloadData?.token) {
      toast.add({
        title: t('pages.auth.loginFailed'),
        description: t('pages.auth.loginFailedDesc'),
        color: 'error',
      })
      return
    }

    writeRememberMe(email, remember)
    authSession.login(payloadData.token, user as any)

    toast.add({
      title: t('pages.auth.loginSuccess'),
      description: t('pages.auth.loginSuccessDesc', { name: user.name }),
      color: 'success',
    })

    await router.push('/')
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
        <img src="/assets/images/logo.png" alt="Logo" class="h-20 w-auto mx-auto rounded-full shadow">
      </template>

      <template #footer>
        <div class="text-center space-y-2">
          <UButton variant="link" size="sm" to="/forget-password" class="text-muted-foreground">
            {{ t('pages.auth.forgotPassword') }}
          </UButton>
          <div>
            <span class="font-black">© <span class="font-normal text-sm">{{ $t('pages.auth.departmentLine') }}</span></span>
          </div>
        </div>
      </template>
    </UAuthForm>
  </div>
</template>
