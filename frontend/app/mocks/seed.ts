import type { PersonSummary, OrganizationSummary, EntityComment, ActivityEvent, AttachmentMeta } from '~/types/docetra/common'
import { createId, nowIso } from './query'

export const people: PersonSummary[] = [
  { id: 'p1', name: 'Sokha Chan', email: 'sokha@docetra.local' },
  { id: 'p2', name: 'Dara Kim', email: 'dara@docetra.local' },
  { id: 'p3', name: 'Sreymom Lim', email: 'sreymom@docetra.local' },
  { id: 'p4', name: 'Vannak Ouk', email: 'vannak@docetra.local' },
  { id: 'p5', name: 'Chenda Meas', email: 'chenda@docetra.local' },
]

export const orgs: OrganizationSummary[] = [
  { id: 'o1', name: 'Ministry of Economy', code: 'MEF' },
  { id: 'o2', name: 'General Department of Taxation', code: 'GDT' },
  { id: 'o3', name: 'Docetra HQ', code: 'DOC' },
  { id: 'o4', name: 'Partner Corp', code: 'PRT' },
  { id: 'o5', name: 'Legal Affairs Bureau', code: 'LAB' },
]

export function person(i = 0) {
  return people[i % people.length]!
}

export function org(i = 0) {
  return orgs[i % orgs.length]!
}

export function daysAgo(n: number) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString()
}

export function dateOnly(n: number) {
  return daysAgo(n).slice(0, 10)
}

export function seedComments(entityType: string, entityId: string, count = 2): EntityComment[] {
  return Array.from({ length: count }, (_, i) => ({
    id: createId('cmt'),
    entityType,
    entityId,
    body: i === 0 ? 'Please review the attached files before the next meeting.' : 'Noted. Will follow up with the department.',
    author: person(i),
    createdAt: daysAgo(i + 1),
  }))
}

export function seedActivity(entityType: string, entityId: string, count = 5): ActivityEvent[] {
  const samples: Array<{
    action: string
    summary: string
    metadata?: Record<string, unknown>
    actorIndex: number
  }> = [
    {
      action: 'attachment_added',
      summary: 'attached cover-letter.pdf',
      metadata: { fileName: 'cover-letter.pdf' },
      actorIndex: 0,
    },
    {
      action: 'assigned',
      summary: 'Sokha Chan assigned Dara Kim',
      actorIndex: 0,
    },
    {
      action: 'created',
      summary: 'created this',
      actorIndex: 0,
    },
    {
      action: 'updated',
      summary: 'last edited this',
      actorIndex: 0,
    },
    {
      action: 'stage_changed',
      summary: 'changed the stage',
      metadata: { field: 'stage' },
      actorIndex: 1,
    },
  ]

  return Array.from({ length: count }, (_, i) => {
    const sample = samples[i % samples.length]!
    const actor = person(sample.actorIndex)
    return {
      id: createId('act'),
      entityType,
      entityId,
      action: sample.action,
      actor,
      summary: sample.summary.includes('assigned')
        ? sample.summary
        : `${actor.name} ${sample.summary}`,
      occurredAt: daysAgo(i),
      metadata: sample.metadata,
    }
  })
}

export function seedAttachments(count = 2): AttachmentMeta[] {
  return Array.from({ length: count }, (_, i) => ({
    id: createId('att'),
    name: i === 0 ? 'cover-letter.pdf' : 'supporting-docs.zip',
    mimeType: i === 0 ? 'application/pdf' : 'application/zip',
    sizeBytes: 120_000 + i * 80_000,
    uploadedBy: person(i),
    uploadedAt: daysAgo(i),
    storageSource: i === 0 ? 'local' : 'google_drive',
  }))
}

export { nowIso, createId }
