import type { AiSearchAnswer, SearchHit, SearchQueryOptions } from '~/types/docetra/search'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

export async function searchKeyword(query: string, options: SearchQueryOptions = {}) {
  const limit = options.limit ?? 12
  const response = await useApi().get<{ data: SearchHit[] }>(ApiEndpoints.SEARCH, {
    query: { q: query, mode: 'keyword', limit },
    requestKey: 'search-keyword',
    cancelPrevious: true,
  })
  return response.data || []
}

export async function searchSemantic(query: string, options: SearchQueryOptions = {}) {
  const limit = options.limit ?? 12
  const response = await useApi().get<{ data: SearchHit[] }>(ApiEndpoints.SEARCH, {
    query: { q: query, mode: 'semantic', limit },
    requestKey: 'search-semantic',
    cancelPrevious: true,
  })
  return response.data || []
}

export async function askAi(query: string, hits: SearchHit[]): Promise<AiSearchAnswer> {
  const response = await useApi().post<{ data: AiSearchAnswer }>(ApiEndpoints.SEARCH_ASK, {
    q: query,
    hitIds: hits.map(h => h.id),
  }, {
    requestKey: 'search-ask',
    cancelPrevious: true,
  })
  return response.data
}
