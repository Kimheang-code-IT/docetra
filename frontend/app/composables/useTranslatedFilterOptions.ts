type FilterOptionValue = string | number

export type TranslatedFilterOption = {
  label: string
  value: FilterOptionValue
}

const FILTER_OPTION_KEYS: Record<string, string> = {
  Login: 'pages.history.actionTypes.login',
  Logout: 'pages.history.actionTypes.logout',
  Create: 'pages.history.actionTypes.create',
  Update: 'pages.history.actionTypes.update',
  Delete: 'pages.history.actionTypes.delete',
  Export: 'pages.history.actionTypes.export',
  SuperAdmin: 'filters.roles.superAdmin',
  'Finance Admin': 'filters.roles.financeAdmin',
  Officer: 'filters.roles.officer',
  Editor: 'filters.roles.editor',
  Viewer: 'filters.roles.viewer',
  'Type A': 'filters.revenueTypes.typeA',
  'Type B': 'filters.revenueTypes.typeB',
  'Type C': 'filters.revenueTypes.typeC',
  'Revenue Type A': 'filters.revenueTypes.revenueTypeA',
  'Revenue Type B': 'filters.revenueTypes.revenueTypeB',
  'Revenue Type C': 'filters.revenueTypes.revenueTypeC',
  'Revenue Type D': 'filters.revenueTypes.revenueTypeD',
  'Kind Alpha': 'filters.revenueTypes.kindAlpha',
  'Kind Beta': 'filters.revenueTypes.kindBeta',
  USD: 'filters.currencies.USD',
  KHR: 'filters.currencies.KHR',
  THB: 'filters.currencies.THB',
  EUR: 'filters.currencies.EUR',
  GBP: 'filters.currencies.GBP',
  JPY: 'filters.currencies.JPY',
  CNY: 'filters.currencies.CNY',
  KRW: 'filters.currencies.KRW',
  SGD: 'filters.currencies.SGD',
  MYR: 'filters.currencies.MYR',
  Finance: 'filters.departments.finance',
  Operations: 'filters.departments.operations',
  'IT Department': 'filters.departments.itDepartment',
  Legal: 'filters.departments.legal',
  'Public Affairs': 'filters.departments.publicAffairs',
  Taxation: 'filters.departments.taxation',
  'MME Central Admin': 'filters.departments.mmeCentralAdmin',
  'DME Central': 'filters.departments.dmeCentral',
  'DME Kampot': 'filters.departments.dmeKampot',
  'DME Siem Reap': 'filters.departments.dmeSiemReap',
  'DME Takeo': 'filters.departments.dmeTakeo',
  'DME Kandal': 'filters.departments.dmeKandal',
  'DME Battambang': 'filters.departments.dmeBattambang',
  'DME Kep': 'filters.departments.dmeKep',
  'DME Phase 1': 'filters.departments.dmePhase1',
  'DME Phase 2': 'filters.departments.dmePhase2',
  'DME North': 'filters.departments.dmeNorth',
  'DME South': 'filters.departments.dmeSouth',
  'Entity Alpha': 'filters.entities.alpha',
  'Entity Beta': 'filters.entities.beta',
  'Entity Gamma': 'filters.entities.gamma',
  'Entity Delta': 'filters.entities.delta',
  'Entity Epsilon': 'filters.entities.epsilon',
}

function baseFilterValue(value: FilterOptionValue): string {
  return String(value)
    .replace(/\s+#\d+$/, '')
    .replace(/\s+\d+$/, '')
}

export function useTranslatedFilterOptions() {
  const { t, te } = useI18n()

  function labelForFilterValue(value: FilterOptionValue): string {
    const raw = String(value)
    const base = baseFilterValue(value)
    const key = FILTER_OPTION_KEYS[raw] ?? FILTER_OPTION_KEYS[base]

    if (!key || !te(key)) return raw

    const translated = t(key)
    if (raw === base) return translated

    return raw.replace(base, translated)
  }

  function toFilterOption(value: FilterOptionValue): TranslatedFilterOption {
    return {
      label: labelForFilterValue(value),
      value,
    }
  }

  function toFilterOptions(values: readonly FilterOptionValue[]): TranslatedFilterOption[] {
    return values.map(toFilterOption)
  }

  return {
    labelForFilterValue,
    toFilterOption,
    toFilterOptions,
  }
}
