import type { DropdownMenuItem } from '@nuxt/ui'
import { usePreferencesStore } from '~/stores/preferences'
import type { AppLocale } from '~/stores/preferences'

export function useUserMenu() {
  const auth = useAuthStore()
  const preferences = usePreferencesStore()
  const colorMode = useColorMode()
  const i18n = useI18n()
  const { t } = i18n
  const router = useRouter()

  preferences.hydrate()

  const colors = ['red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose']
  const neutrals = ['slate', 'gray', 'zinc', 'neutral', 'stone']

  const user = computed(() => ({
    name: auth.user?.name || auth.user?.email || 'User',
    avatar: {
      src: auth.user?.avatar
        || `https://ui-avatars.com/api/?name=${encodeURIComponent(auth.user?.name || 'User')}&background=random`,
      alt: auth.user?.name || 'User',
    },
  }))

  const items = computed<DropdownMenuItem[][]>(() => [
    [
      {
        type: 'label',
        label: user.value.name,
        avatar: user.value.avatar,
      },
    ],
    [
      {
        label: t('settings.history'),
        icon: 'i-lucide-clock',
        onSelect(e: Event) {
          e.preventDefault()
          router.push('/records/logs')
        },
      },
    ],
    [
      {
        label: t('settings.language'),
        icon: 'i-lucide-languages',
        children: (i18n.locales.value || []).map((loc: { name?: string; icon?: string; code?: string }) => ({
          label: loc.name,
          icon: loc.icon,
          type: 'checkbox',
          checked: i18n.locale.value === loc.code,
          onSelect: (e: Event) => {
            e.preventDefault()
            if (loc.code === 'en' || loc.code === 'km') {
              preferences.setLocale(loc.code as AppLocale)
            }
          },
        })),
      },
      {
        label: t('settings.theme'),
        icon: 'i-lucide-palette',
        children: [
          {
            label: t('settings.primary'),
            slot: 'chip',
            chip: preferences.uiColors.primary || 'blue',
            content: {
              align: 'center',
              collisionPadding: 16,
            },
            children: colors.map((color) => ({
              label: color,
              chip: color,
              slot: 'chip',
              checked: preferences.uiColors.primary === color,
              type: 'checkbox',
              onSelect: (e: Event) => {
                e.preventDefault()
                preferences.applyThemeColor('primary', color)
              },
            })),
          },
          {
            label: t('settings.neutral'),
            slot: 'chip',
            chip:
              preferences.uiColors.neutral === 'neutral'
                ? 'old-neutral'
                : (preferences.uiColors.neutral || 'slate'),
            content: {
              align: 'end',
              collisionPadding: 16,
            },
            children: neutrals.map((color) => ({
              label: color,
              chip: color === 'neutral' ? 'old-neutral' : color,
              slot: 'chip',
              type: 'checkbox',
              checked: preferences.uiColors.neutral === color,
              onSelect: (e: Event) => {
                e.preventDefault()
                preferences.applyThemeColor('neutral', color)
              },
            })),
          },
        ],
      },
      {
        label: t('settings.appearance'),
        icon: 'i-lucide-sun-moon',
        children: [
          {
            label: t('settings.light'),
            icon: 'i-lucide-sun',
            type: 'checkbox',
            checked: colorMode.value === 'light',
            onSelect(e: Event) {
              e.preventDefault()
              colorMode.preference = 'light'
            },
          },
          {
            label: t('settings.dark'),
            icon: 'i-lucide-moon',
            type: 'checkbox',
            checked: colorMode.value === 'dark',
            onUpdateChecked(checked: boolean) {
              if (checked) colorMode.preference = 'dark'
            },
            onSelect(e: Event) {
              e.preventDefault()
            },
          },
        ],
      },
    ],
    [
      {
        label: t('settings.logout'),
        icon: 'i-lucide-log-out',
        color: 'error',
        onSelect(e: Event) {
          e.preventDefault()
          auth.logout()
        },
      },
    ],
  ])

  return {
    user,
    items,
  }
}
