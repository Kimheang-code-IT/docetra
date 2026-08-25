/**
 * Phase 2 search index — localStorage-backed document corpus for Cmd+K.
 */
import type { IndexedDocument } from '~/types/docetra/search'
import { localStore } from '~/utils/storage/local'

const INDEX_KEY = 'docetra:search:index:v1'

function readAll(): IndexedDocument[] {
  return localStore.get<IndexedDocument[]>(INDEX_KEY) || []
}

function writeAll(docs: IndexedDocument[]) {
  localStore.set(INDEX_KEY, docs)
}

export function upsertIndexedDocument(doc: IndexedDocument) {
  if (!import.meta.client) return
  const rows = readAll()
  const idx = rows.findIndex(r => r.id === doc.id)
  if (idx >= 0) rows[idx] = doc
  else rows.push(doc)
  writeAll(rows)
}
