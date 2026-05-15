# Usage Guide

Using QueryTune is straightforward, but understanding the two modes and the "Context" area will help you get much better results.

## 1. Optimize Mode (Structured Analysis)
This is the default mode. When you click **"Optimize"**, QueryTune sends your query to the AI with a specific system prompt designed for DBA-level analysis.

The result is split into three areas:
*   **Refactored Query:** The optimized SQL code.
*   **Suggested Indices:** Specific `CREATE INDEX` statements.
*   **Technical Explanation:** A detailed breakdown of *why* the changes were made.

## 2. Chat Mode (Conversational)
Switch to **"Chat Mode"** when you want to brainstorm or ask general questions about a query.
*   The AI will provide a streaming, word-by-word response.
*   Ideal for explaining complex legacy queries or discussing architectural trade-offs.

## 3. The Power of "Context"
The collapsible **Context** area is your most powerful tool. AI performance improves drastically when you provide:
*   **Schema Details:** Copy-paste the `CREATE TABLE` statements for the tables involved.
*   **Data Volume:** Tell the AI how many rows are in each table (e.g., "Table users has 5M rows, table logs has 100M rows").
*   **Database Engine:** Ensure you selected the correct engine (PostgreSQL, MySQL, etc.) in Settings.

## 4. History Log
Your previous optimizations are saved automatically in the sidebar. 
*   Click any item to reload the query and the AI's response.
*   History is stored locally in a SQLite database (`~/.querytune_history.db`).
