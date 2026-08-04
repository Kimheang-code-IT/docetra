import type { RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type { AppConfigRepository, AppInfoRepository, StorageRepository } from '~/repositories/contracts/settings'
import { createHttpRecordAttributeRepository, createHttpRecordTypeRepository } from '~/repositories/http/configuration'
import { createHttpAppConfigRepository, createHttpAppInfoRepository } from '~/repositories/http/settings'
import { createHttpStorageRepository } from '~/repositories/http/settings-storage'
import { createMockRecordAttributeRepository, createMockRecordTypeRepository } from '~/repositories/mock/configuration'
import { createMockAppConfigRepository, createMockAppInfoRepository, createMockStorageRepository } from '~/repositories/mock/settings'

let mode: 'mock' | 'http' | null = null
let recordAttributeRepo: RecordAttributeRepository
let recordTypeRepo: RecordTypeRepository
let appInfoRepo: AppInfoRepository
let appConfigRepo: AppConfigRepository
let storageRepo: StorageRepository

function ensureRepositories() {
  const nextMode = useRuntimeConfig().public.useMockData !== false ? 'mock' : 'http'
  if (mode === nextMode) return
  mode = nextMode
  recordAttributeRepo = nextMode === 'mock' ? createMockRecordAttributeRepository() : createHttpRecordAttributeRepository()
  recordTypeRepo = nextMode === 'mock' ? createMockRecordTypeRepository() : createHttpRecordTypeRepository()
  appInfoRepo = nextMode === 'mock' ? createMockAppInfoRepository() : createHttpAppInfoRepository()
  appConfigRepo = nextMode === 'mock' ? createMockAppConfigRepository() : createHttpAppConfigRepository()
  storageRepo = nextMode === 'mock' ? createMockStorageRepository() : createHttpStorageRepository()
}

export function useConfigurationRepositories() {
  ensureRepositories()
  return { attributes: recordAttributeRepo!, recordTypes: recordTypeRepo! }
}

export function useSettingsRepositories() {
  ensureRepositories()
  return { appInfo: appInfoRepo!, appConfig: appConfigRepo!, storage: storageRepo! }
}
