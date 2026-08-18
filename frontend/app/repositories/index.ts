import type { RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type { AppConfigRepository, AppInfoRepository, StorageRepository } from '~/repositories/contracts/settings'
import { createHttpRecordAttributeRepository, createHttpRecordTypeRepository } from '~/repositories/http/configuration'
import { createHttpAppConfigRepository, createHttpAppInfoRepository } from '~/repositories/http/settings'
import { createHttpStorageRepository } from '~/repositories/http/settings-storage'

export function useConfigurationRepositories() {
  return {
    attributes: createHttpRecordAttributeRepository() as RecordAttributeRepository,
    recordTypes: createHttpRecordTypeRepository() as RecordTypeRepository,
  }
}

export function useSettingsRepositories() {
  return {
    appInfo: createHttpAppInfoRepository() as AppInfoRepository,
    appConfig: createHttpAppConfigRepository() as AppConfigRepository,
    storage: createHttpStorageRepository() as StorageRepository,
  }
}
