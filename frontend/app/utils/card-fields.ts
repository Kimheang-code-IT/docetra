/**
 * Board card field catalogs — shared by App Config schema, seed, and card renderers.
 *
 * Product source: prompt/idea + prompt/specification (unified record model).
 * Meetings are a special record type — share core record summary fields
 * (title, status, stage, tags, record_time) plus meeting extras.
 *
 * Title is always shown. sortOrder + status render in the title row.
 * Footer slots render in the bordered footer with left/right alignment.
 */
import type { CardDisplayEntityKey } from '~/types/docetra/settings'

export const TOPIC_CARD_SLOTS = [
  'status',
  'stage',
  'tags',
  'recordTime',
] as const

export const MEETING_CARD_SLOTS = [
  'topicTitle',
  'status',
  'sortOrder',
  'letterNumber',
  'stage',
  'tags',
  'participants',
  'internalUnits',
  'externalUnits',
  'letterDate',
  'meetingDate',
  'recordTime',
  'location',
  'meetingMode',
  'meetingUrl',
  'durationMinutes',
  'attendeesCount',
  'createdAt',
  'updatedAt',
] as const

export const RECORD_CARD_SLOTS = [
  'referenceNumber',
  'recordType',
  'party',
  'owner',
  'assignee',
  'status',
  'stage',
  'waiting',
  'tags',
  'description',
  'recordTime',
  'dateRange',
  'receivedDate',
  'sentDate',
  'createdAt',
  'updatedAt',
  'attachmentCount',
  'commentCount',
  'recordFlowCode',
  'recordContent',
  'documentType',
  'letterNumber',
  'letterSubject',
  'documentDate',
  'letterDate',
  'directorGeneralDate',
  'directorDate',
  'involvedOfficers',
  'externalUnits',
  'officeInCharge',
  'officerInCharge',
] as const

export type TopicCardSlot = (typeof TOPIC_CARD_SLOTS)[number]
export type MeetingCardSlot = (typeof MEETING_CARD_SLOTS)[number]
export type RecordCardSlot = (typeof RECORD_CARD_SLOTS)[number]
export type CardFooterAlign = 'left' | 'right'

/** Defaults: core record fields + meeting date/location footer (date L, location R). */
export const DEFAULT_MEETING_CARD_FIELDS: string[] = [
  'sortOrder',
  'status',
  'stage',
  'tags',
  'topicTitle',
  'letterNumber',
  'meetingDate',
  'location',
]

/** Defaults align with draft record columns: title, stage, tags, record_time, content. */
export const DEFAULT_RECORD_CARD_FIELDS: string[] = [
  'status',
  'stage',
  'tags',
  'description',
  'recordTime',
  'referenceNumber',
  'recordType',
  'party',
  'attachmentCount',
  'commentCount',
]

export const DEFAULT_CARD_FIELDS: Record<CardDisplayEntityKey, string[]> = {
  /** Topic rail: no date on folder cards by default */
  meetingTopics: ['status', 'stage', 'tags'],
  meetingHistory: DEFAULT_MEETING_CARD_FIELDS,
  incomingDocuments: [...DEFAULT_RECORD_CARD_FIELDS, 'documentType', 'letterSubject', 'officeInCharge', 'involvedOfficers', 'externalUnits'],
  outgoingDocuments: [...DEFAULT_RECORD_CARD_FIELDS, 'documentType', 'letterSubject', 'officeInCharge', 'involvedOfficers', 'externalUnits'],
  documents: [...DEFAULT_RECORD_CARD_FIELDS, 'documentType', 'letterSubject', 'officeInCharge', 'involvedOfficers', 'externalUnits'],
  masterListRequests: ['status', 'stage', 'tags', 'letterNumber', 'letterSubject', 'officeInCharge', 'officerInCharge', 'externalUnits', 'letterDate'],
}

export const CARD_DISPLAY_ENTITIES: Array<{
  key: CardDisplayEntityKey
  labelKey: string
  kind: 'meeting' | 'record'
}> = [
  { key: 'meetingTopics', labelKey: 'docetra.settings.cardFields.meetingTopics', kind: 'meeting' },
  { key: 'meetingHistory', labelKey: 'docetra.settings.cardFields.meetingHistory', kind: 'meeting' },
  { key: 'incomingDocuments', labelKey: 'docetra.settings.cardFields.incomingDocuments', kind: 'record' },
  { key: 'outgoingDocuments', labelKey: 'docetra.settings.cardFields.outgoingDocuments', kind: 'record' },
  { key: 'documents', labelKey: 'docetra.settings.cardFields.documents', kind: 'record' },
  { key: 'masterListRequests', labelKey: 'docetra.settings.cardFields.masterListRequests', kind: 'record' },
]

export const TOPIC_CARD_BLOCKS: CardSlotBlock[] = [
  { id: 'titleRow', labelKey: 'docetra.cardSlotBlocks.titleRow', slots: ['status'] },
  { id: 'context', labelKey: 'docetra.cardSlotBlocks.context', slots: ['stage', 'tags'] },
  { id: 'footer', labelKey: 'docetra.cardSlotBlocks.footer', slots: ['recordTime'] },
]

export interface CardSlotBlock {
  id: string
  labelKey: string
  slots: string[]
}

export const MEETING_CARD_BLOCKS: CardSlotBlock[] = [
  { id: 'titleRow', labelKey: 'docetra.cardSlotBlocks.titleRow', slots: ['sortOrder', 'status'] },
  { id: 'identity', labelKey: 'docetra.cardSlotBlocks.identity', slots: ['letterNumber'] },
  {
    id: 'context',
    labelKey: 'docetra.cardSlotBlocks.context',
    slots: ['topicTitle', 'stage', 'tags', 'participants', 'internalUnits', 'externalUnits'],
  },
  {
    id: 'footer',
    labelKey: 'docetra.cardSlotBlocks.footer',
    slots: ['letterDate', 'meetingDate', 'recordTime', 'location', 'meetingMode', 'meetingUrl', 'durationMinutes', 'attendeesCount', 'createdAt', 'updatedAt'],
  },
]

export const RECORD_CARD_BLOCKS: CardSlotBlock[] = [
  { id: 'titleRow', labelKey: 'docetra.cardSlotBlocks.titleRow', slots: ['status'] },
  {
    id: 'identity',
    labelKey: 'docetra.cardSlotBlocks.identity',
    slots: [
      'referenceNumber',
      'recordType',
      'description',
      'recordFlowCode',
      'recordContent',
      'documentType',
      'letterNumber',
      'letterSubject',
    ],
  },
  { id: 'party', labelKey: 'docetra.cardSlotBlocks.party', slots: ['party'] },
  {
    id: 'people',
    labelKey: 'docetra.cardSlotBlocks.people',
    slots: ['owner', 'assignee', 'involvedOfficers', 'externalUnits', 'officeInCharge', 'officerInCharge'],
  },
  { id: 'extra', labelKey: 'docetra.cardSlotBlocks.extra', slots: ['stage', 'waiting', 'tags'] },
  {
    id: 'footer',
    labelKey: 'docetra.cardSlotBlocks.footer',
    slots: [
      'recordTime',
      'dateRange',
      'receivedDate',
      'sentDate',
      'documentDate',
      'letterDate',
      'directorGeneralDate',
      'directorDate',
      'createdAt',
      'updatedAt',
      'attachmentCount',
      'commentCount',
    ],
  },
]

export function catalogForEntity(entityKey: CardDisplayEntityKey): readonly string[] {
  if (entityKey === 'meetingTopics') return TOPIC_CARD_SLOTS
  return entityKey === 'meetingHistory' ? MEETING_CARD_SLOTS : RECORD_CARD_SLOTS
}

export function blocksForEntity(entityKey: CardDisplayEntityKey): CardSlotBlock[] {
  if (entityKey === 'meetingTopics') return TOPIC_CARD_BLOCKS
  return entityKey === 'meetingHistory' ? MEETING_CARD_BLOCKS : RECORD_CARD_BLOCKS
}

/** Renders in the title row (order # before title, status with title). */
export const TITLE_CHROME_SLOTS = new Set(['sortOrder', 'status'])

export function isTitleChromeSlot(slot: string): boolean {
  return TITLE_CHROME_SLOTS.has(slot)
}

export const MEETING_FOOTER_SLOTS = new Set([
  'letterDate',
  'meetingDate',
  'recordTime',
  'location',
  'attendeesCount',
  'createdAt',
  'updatedAt',
])

export const TOPIC_FOOTER_SLOTS = new Set(['recordTime'])

export const RECORD_FOOTER_SLOTS = new Set([
  'recordTime',
  'dateRange',
  'receivedDate',
  'sentDate',
  'documentDate',
  'letterDate',
  'directorGeneralDate',
  'directorDate',
  'createdAt',
  'updatedAt',
  'attachmentCount',
  'commentCount',
])

export function isCardFooterSlot(entityKey: CardDisplayEntityKey, slot: string): boolean {
  if (entityKey === 'meetingTopics') return TOPIC_FOOTER_SLOTS.has(slot)
  return entityKey === 'meetingHistory'
    ? MEETING_FOOTER_SLOTS.has(slot)
    : RECORD_FOOTER_SLOTS.has(slot)
}

export function defaultFooterAlign(slot: string): CardFooterAlign {
  // Meeting: date left, location right
  if (slot === 'location') return 'right'
  if (slot === 'attachmentCount' || slot === 'commentCount' || slot === 'attendeesCount') {
    return 'right'
  }
  return 'left'
}

export function resolveFooterAlign(
  entityKey: CardDisplayEntityKey,
  slot: string,
  map: Partial<Record<CardDisplayEntityKey, Partial<Record<string, CardFooterAlign>>>> | null | undefined,
): CardFooterAlign {
  const saved = map?.[entityKey]?.[slot]
  if (saved === 'left' || saved === 'right') return saved
  return defaultFooterAlign(slot)
}

export function splitCardSlots(
  entityKey: CardDisplayEntityKey,
  slots: string[],
): { titleChrome: string[], body: string[], footer: string[] } {
  const titleChrome: string[] = []
  const body: string[] = []
  const footer: string[] = []
  for (const slot of slots) {
    if (isTitleChromeSlot(slot)) titleChrome.push(slot)
    else if (isCardFooterSlot(entityKey, slot)) footer.push(slot)
    else body.push(slot)
  }
  return { titleChrome, body, footer }
}

export function resolveVisibleSlots(
  entityKey: CardDisplayEntityKey,
  selected: string[] | null | undefined,
): string[] {
  const catalog = new Set(catalogForEntity(entityKey))
  if (!Array.isArray(selected)) return [...DEFAULT_CARD_FIELDS[entityKey]]
  return selected.filter(slot => catalog.has(slot))
}
