# ola_analytics Project Guidelines

## Core Directives
1. **Target Directory**: This folder (`ola_analytics`) is the **ONLY** backend directory to be modified.
2. **ERP Security**: Connect to the ERP database using `ola_ai_readonly` database user credentials with `SELECT` permissions only.
3. **Query Validation**: Use `query_engine.validator.QueryValidator` to validate all dynamic queries.
4. **MCP Server**: Maintain the MCP tools defined in `mcp_server.py` and `mcp_integration/`.
5. **REST API**: All endpoints in `api/` must return structured JSON compliant with the mobile and web UI component schemas.
6. **Sensitive Data & Credential Masking**: Automatically mask all sensitive fields (`password`, `password_hash`, `hashed_password`, `secret`, `token`, `api_key`, sensitive IDs) with `********` using `SensitiveDataMasker` before returning any query data or outputting logs.
7. **Bilingual Support (English & Spanish)**: Provide full bilingual support for English (`en`) and Spanish (`es`) across web portal and mobile UI. Persist user language preferences and support on-the-fly toggling.
8. **Prohibition of Dummy Data & Mandatory Real ERP Analytics**: Dummy, static, or fabricated metrics are strictly forbidden. All business metrics, KPIs, charts, tables, trends, and analytical calculations must be derived directly from the real database collections (`vehicles`, `invoices`, `paymentreceiveds`, `customers`, `drivers`, etc.) inspected from the ERP backend (`OlaCarsBackend`).



