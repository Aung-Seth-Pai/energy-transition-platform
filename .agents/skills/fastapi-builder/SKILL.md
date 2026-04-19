---
name: fastapi-builder
description: Scaffolds or updates FastAPI endpoints, particularly those interacting with Groq LLMs and local Postgres.
---

# FastAPI Development Standards

1. **Validation:** All request/response models must use Pydantic V2 `BaseModel`.
2. **Database:** Use dependency injection for the local PostgreSQL database (which mocks BigQuery). Refer to `resources/mock_schema.sql` for table structures.
3. **Async:** Use `async def` for routes performing network I/O (e.g., calling Groq API).
4. **Errors:** Catch internal exceptions and raise sanitized `HTTPException`s.