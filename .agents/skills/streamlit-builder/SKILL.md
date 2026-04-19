---
name: streamlit-builder
description: Generates or modifies Streamlit frontend components and dashboards.
---

# Streamlit UI Standards

1. **State:** Use `st.session_state` to prevent unnecessary re-renders.
2. **Caching:** Utilize `@st.cache_data` for fetching data from the FastAPI backend.
3. **Visuals:** Use `plotly` for complex charting and geospatial maps.
4. **Network:** Always use `httpx` or `requests` to fetch data from the FastAPI backend. NEVER connect Streamlit directly to the Postgres database.