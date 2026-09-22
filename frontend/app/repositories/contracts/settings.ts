import type {
  AppConfig,
  ConnectionStatus,
  CreateStorageProviderInput,
  StorageProvider,
  TelegramChat,
  TelegramTestResult,
  UpdateStorageProviderInput,
} from '~/types/docetra/settings'

export interface AppConfigRepository {
  get: () => Promise<AppConfig>
  update: (input: Partial<AppConfig>) => Promise<AppConfig>
  testEmailConnection: () => Promise<{ status: ConnectionStatus, message: string }>
  sendTestEmail: (to: string) => Promise<{ status: ConnectionStatus, message: string }>
  testTelegramConnection: () => Promise<TelegramTestResult>
  sendTestTelegramMessage: (input: { destinationId?: string, chatId?: string }) => Promise<TelegramTestResult>
  discoverTelegramChats: () => Promise<TelegramChat[]>
}

export interface StorageRepository {
  list: () => Promise<StorageProvider[]>
  getById: (id: string) => Promise<StorageProvider>
  create: (input: CreateStorageProviderInput) => Promise<StorageProvider>
  update: (id: string, input: UpdateStorageProviderInput) => Promise<StorageProvider>
  setDefault: (id: string) => Promise<StorageProvider>
  setActive: (id: string, active: boolean) => Promise<StorageProvider>
  testConnection: (id: string) => Promise<{ status: ConnectionStatus, message: string }>
  remove: (id: string) => Promise<void>
}
