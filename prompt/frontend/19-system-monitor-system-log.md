# Prompt 19 — System Log

## Copy/paste prompt

Implement `/system-monitor/system-logs` in the existing Nuxt UI frontend. Follow the shared foundation, administrative logging requirements, and strict access-control rules.

### Implement now

Add only a localized System Log header, System Monitor breadcrumb, high-privilege route/permission metadata, and placeholder card. Do not connect to runtime logs or fabricate events.

### Future UI contract

Build this later as a read-only operational log explorer using cursor pagination, bounded date windows, debounced search, and filters for severity, service/module, environment, correlation/request ID, and time. Support optional controlled live-tail behavior that pauses when the page is hidden and caps retained rows. Escape untrusted messages and redact credentials, tokens, personal data, stack internals, and request bodies according to policy. Export must be asynchronous and access-aware for large result sets.

### Acceptance

The protected route is represented in navigation, renders only the scaffold, starts no polling/request, and passes project checks.

