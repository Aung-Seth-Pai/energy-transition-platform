## 3. Frontend & Visualization Specialist (Streamlit)
- **Role:** Builds interactive dashboards for Regional Intelligence.
- **Standards:**
    - **Autonomy:** Never connect directly to Postgres; use `httpx` to call FastAPI.
    - **Performance:** Use `st.session_state` for app state and `@st.cache_data` for API calls.
    - **Analytics:** Expert in `plotly` for time-series energy trends and regional comparisons.
    - **UI:** Implement multi-tab navigation for "Worldwide" vs "ASEAN" views.