"""Background work for Docetra processes.

- ``jobs.publishers`` / ``jobs.topology`` — RabbitMQ publish helpers
- ``jobs.consumers`` — worker handlers (email, meetings, Drive, exports, outbox)
- ``jobs.scheduler`` — APScheduler tick handlers (publish due work only)

Process entry is ``app.main``: ``uvicorn app.main:app``, ``python -m app.main worker``,
``python -m app.main scheduler``.
"""
