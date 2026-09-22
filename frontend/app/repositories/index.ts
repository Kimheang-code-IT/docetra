import type { RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type { AppConfigRepository, StorageRepository } from '~/repositories/contracts/settings'
import type { PermissionCatalogRepositoryContract } from '~/repositories/contracts/permission-catalog'
import { createHttpRecordAttributeRepository, createHttpRecordTypeRepository } from '~/repositories/http/configuration'
import { createHttpAppConfigRepository } from '~/repositories/http/settings'
import { createHttpStorageRepository } from '~/repositories/http/settings-storage'
import { createHttpPermissionCatalogRepository } from '~/repositories/http/permission-catalog'

export function useConfigurationRepositories() {
  return {
    attributes: createHttpRecordAttributeRepository() as RecordAttributeRepository,
    recordTypes: createHttpRecordTypeRepository() as RecordTypeRepository,
  }
}

export function useSettingsRepositories() {
  return {
    appConfig: createHttpAppConfigRepository() as AppConfigRepository,
    storage: createHttpStorageRepository() as StorageRepository,
  }
}

export function usePermissionCatalogRepository(): PermissionCatalogRepositoryContract {
  return createHttpPermissionCatalogRepository()
}
