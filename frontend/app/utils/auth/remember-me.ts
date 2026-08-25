import { localStore } from '~/utils/storage/local'

const AuthKeys = {
  REMEMBER_EMAIL: 'login:remember:email',
  REMEMBER_ENABLED: 'login:remember:enabled',
} as const

type RememberMeState = {
  enabled: boolean
  email: string
}

function isEnabledFlag(value: unknown): boolean {
  return value === '1' || value === 1 || value === true
}

export function readRememberMe(): RememberMeState {
  const enabled = isEnabledFlag(localStore.get(AuthKeys.REMEMBER_ENABLED))
  const email = enabled ? String(localStore.get(AuthKeys.REMEMBER_EMAIL) || '') : ''
  return { enabled, email }
}

export function writeRememberMe(state: RememberMeState) {
  if (state.enabled && state.email) {
    localStore.set(AuthKeys.REMEMBER_ENABLED, '1')
    localStore.set(AuthKeys.REMEMBER_EMAIL, state.email)
    return
  }
  localStore.remove(AuthKeys.REMEMBER_ENABLED)
  localStore.remove(AuthKeys.REMEMBER_EMAIL)
}
