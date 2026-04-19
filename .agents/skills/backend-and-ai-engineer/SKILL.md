## 2. Backend & AI Engineer (FastAPI/Groq)
- **Role:** Scaffolds endpoints and integrates LLM reasoning.
- **Standards:**
    - **Pydantic V2:** Use `.model_dump()` and `.model_validate()` exclusively.
    - **Database:** Interface with the local Postgres (BigQuery Mock) via dependency injection.
    - **AI Logic:** Implement async RAG chains using Groq (Llama 3).
    - **Security:** Sanitize all AI-generated SQL and handle exceptions with `HTTPException`.