# Cache and RabbitMQ Contract

This document defines how Docetra uses Redis and RabbitMQ to keep interactive pages fast without weakening consistency or durability. PostgreSQL remains the source of truth.

## 1. Responsibilities


| Component  | Responsibility                                             | Never use it for               |
| ---------- | ---------------------------------------------------------- | ------------------------------ |
| Redis DB 0 | Session/operational coordination, rate limits, short locks | Durable business records       |
| Redis DB 1 | Short cache tier for frequently changing reads             | Secrets or authorization proof |
| Redis DB 2 | Long cache tier for stable reference/configuration reads   | Indefinite storage             |
| RabbitMQ   | Durable delivery of background work and domain events      | Request/response data storage  |
| PostgreSQL | Authoritative state, job/outbox records, audit history     | Disposable cache entries       |


Logical Redis databases are appropriate for local development. In staging/production, use separate managed instances or clusters for operational state and cache workloads when memory pressure, eviction, scaling, or failure isolation requires it. Redis Cluster uses key namespaces rather than numbered logical databases.

## 2. Cache tiers and suggested TTLs



### Short cache

Default TTL: 30 seconds, normally 5–60 seconds.


| Data                                  | Suggested TTL     |
| ------------------------------------- | ----------------- |
| Dashboard counters and summaries      | 15 seconds        |
| Board/list query results              | 20–30 seconds     |
| Mention/typeahead results             | 30 seconds        |
| Lightweight availability/count checks | 10 seconds        |
| Negative “not found” result           | At most 5 seconds |




### Long cache

Default TTL: 1 hour, normally 5 minutes–24 hours.


| Data                                   | Suggested TTL |
| -------------------------------------- | ------------- |
| App localization/display configuration | 5 minutes     |
| Permission catalog structure           | 10 minutes    |
| Published Record Type schemas/stages   | 15 minutes    |
| Organization/reference option metadata | 10 minutes    |
| Stable public branding metadata        | 1 hour        |


“Long” never means permanent. Add ±10% TTL jitter to reduce synchronized expiration. TTL values are environment configuration, not literals scattered through handlers.

## 3. Cache behavior

- Use cache-aside: read Redis, load from PostgreSQL on miss, then cache the safe serialized result.
- Key format: `docetra:v2:{tier}:{tenant}:{resource}:{version}:{queryHash}`. Include tenant and permission scope before a result can vary by access.
- Never share a user-scoped or permission-filtered value through a global key.
- Do not cache passwords, session secrets, CSRF values, raw storage credentials, or unmasked settings.
- Prevent stampedes with a short distributed fill lock, request coalescing, TTL jitter, and optional stale-while-revalidate for non-security-sensitive reads.
- Use bounded payload sizes and compression only after measurement. Large exports and files belong in object storage, not Redis.
- Redis failure must degrade to a safe database read or a controlled `503`; it must never bypass authorization.



## 4. Invalidation and consistency

Invalidate after the PostgreSQL transaction commits, never before. A mutation evicts both the resource key and affected list/count/search keys. Important mappings include:

- Role/user/permission changes: permission catalogs, effective permissions, menus/search scopes, and affected sessions. Authorization is recomputed immediately; it must not wait for TTL.
- App Config changes: localization, card-field, page-size, and branding caches.
- Record Type/Attribute changes: published schemas, forms, filters, card metadata, and exports.
- Organization changes: mention/options, denormalized labels, and relevant board/list results.
- Record/meeting/topic create, update, archive, delete, restore, assignment, or stage transition: detail, board/list, count, search, dashboard, and archive keys.

Use a transactional outbox row written with the business transaction. A publisher sends the committed event to RabbitMQ; consumers invalidate secondary caches and update projections. Direct local eviction provides read-your-own-write behavior, while the event repairs other instances. Consumers must tolerate duplicated or out-of-order events using entity version numbers.

## 5. RabbitMQ topology

Use durable topic exchanges, durable quorum queues in production, persistent messages, publisher confirms, manual acknowledgements, and dead-letter exchanges.


| Queue                        | Work                                          |
| ---------------------------- | --------------------------------------------- |
| `docetra.default`            | Small general background jobs                 |
| `docetra.files`              | Malware scan, metadata extraction, thumbnails |
| `docetra.drive_sync`         | Google Drive synchronization and recovery     |
| `docetra.exports`            | CSV/PDF/report generation                     |
| `docetra.notifications`      | Email plus separately routed meeting and development Telegram delivery |
| `docetra.search_index`       | Permission-aware index/projection updates     |
| `docetra.cache_invalidation` | Cross-instance cache invalidation             |
| `docetra.dead_letter`        | Exhausted or rejected jobs for investigation  |


Do not put file binaries or full sensitive records in messages. Send IDs, tenant, event type, schema version, entity version, correlation/request ID, attempt, and trace context; workers load authorized data from the source of truth.

## 6. Delivery and retry rules

- Delivery is at least once. Every consumer is idempotent using a job/event ID and durable processed marker or naturally idempotent update.
- Acknowledge only after the side effect and durable job state commit.
- Retry transient failures with exponential backoff and jitter, for example 5 seconds, 30 seconds, 2 minutes, 10 minutes, and 30 minutes.
- Do not retry validation, permission, missing-configuration, or unsupported-file errors indefinitely; route them directly to a failed state/dead letter.
- After the configured maximum attempts, dead-letter the message and persist a safe failure summary for operators and the frontend job endpoint.
- Set message expiry, maximum queue length/bytes, consumer timeout, and per-queue prefetch. Apply backpressure rather than exhausting database/API connections.
- Graceful shutdown stops intake, finishes or requeues in-flight work, and then exits.



## 7. API and frontend behavior

Long operations return `202 Accepted` with `{ data: { jobId, status: "pending" } }`. The frontend polls a bounded job-status endpoint with backoff and stops on `ready`, `failed`, or cancellation. It must not continuously poll while the page is hidden or after navigation.

Normal authenticated API responses are `Cache-Control: private, no-store` unless a resource has an explicit safe revalidation policy. Use ETags/`If-None-Match` for safe GET revalidation. Hashed frontend assets use `public, max-age=31536000, immutable`; the application HTML uses short/no cache so deployments are discovered quickly.

## 8. Operations and observability

Monitor cache hit/miss ratio, latency, memory, evictions, key count by namespace, RabbitMQ ready/unacknowledged messages, publish/ack rates, redeliveries, consumer lag, dead letters, job age, failures, and worker saturation. Alert on sustained queue growth, oldest-job age, cache eviction spikes, connection exhaustion, and any dead-lettered security/storage job.

Health endpoints distinguish liveness from readiness. The API may remain live during a cache outage but should report degraded readiness; workers are not ready without RabbitMQ and their required database/storage dependencies.

Production uses private networking, TLS for Redis/AMQP where supported, unique least-privilege credentials, secret rotation, disk alarms, memory limits, encrypted persistent volumes/backups where required, and no public management console.

## 9. Verification checklist

- Unit tests cover key construction, tenant/permission separation, TTL class, and invalidation mapping.
- Integration tests prove mutation visibility, cache failure fallback, stampede protection, and permission revocation without stale access.
- Worker tests prove duplicate delivery, retry/backoff, poison messages, dead-letter routing, and restart recovery.
- Load tests verify API latency while exports, uploads, and Drive sync run concurrently.
- Operational drills verify Redis loss, RabbitMQ restart, worker scale-out, queue backlog recovery, and safe job replay.
