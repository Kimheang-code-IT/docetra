import type {
  DocumentTypeRepository,
  RecordAttributeRepository,
  RecordTypeRepository,
} from '~/repositories/contracts/configuration'
import type {
  AppConfigRepository,
  AppInfoRepository,
  StorageRepository,
} from '~/repositories/contracts/settings'
import {
  createMockDocumentTypeRepository,
  createMockRecordAttributeRepository,
  createMockRecordTypeRepository,
} from '~/repositories/mock/configuration'
import {
  createMockAppConfigRepository,
  createMockAppInfoRepository,
  createMockStorageRepository,
} from '~/repositories/mock/settings'

/**
 * Repository factory. Mock implementations persist to localStorage.
 * Swap to HTTP repositories later without changing page components.
 *
 * Singletons keep in-memory + localStorage state consistent across navigations.
 */

let recordAttributeRepo: RecordAttributeRepository | null = null
let recordTypeRepo: RecordTypeRepository | null = null
let documentTypeRepo: DocumentTypeRepository | null = null
let appInfoRepo: AppInfoRepository | null = null
let appConfigRepo: AppConfigRepository | null = null
let storageRepo: StorageRepository | null = null

export function useConfigurationRepositories() {
  recordAttributeRepo ||= createMockRecordAttributeRepository()
  recordTypeRepo ||= createMockRecordTypeRepository()
  documentTypeRepo ||= createMockDocumentTypeRepository()

  return {
    attributes: recordAttributeRepo,
    recordTypes: recordTypeRepo,
    documentTypes: documentTypeRepo,
  }
}

export function useSettingsRepositories() {
  appInfoRepo ||= createMockAppInfoRepository()
  appConfigRepo ||= createMockAppConfigRepository()
  storageRepo ||= createMockStorageRepository()

  return {
    appInfo: appInfoRepo,
    appConfig: appConfigRepo,
    storage: storageRepo,
  }
}
