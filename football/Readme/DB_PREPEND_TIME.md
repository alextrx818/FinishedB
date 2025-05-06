# DB Prepend & Time/Date Format

This README outlines all the changes and steps performed to achieve "newest-first" (prepend) ordering and correct Eastern Time (MM/DD/YYYY HH:MM:SS AM/PM) formatting for both raw JSON and human-readable logs in the Supabase database.

---

## 1. Base Table Schemas

* **archived_json**

  ```sql
  CREATE TABLE archived_json (
    id SERIAL PRIMARY KEY,
    raw_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```

* **main_logger_logs**

  ```sql
  CREATE TABLE main_logger_logs (
    id SERIAL PRIMARY KEY,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```

These tables store raw JSON from `live.py` and formatted text chunks from `main_logger.py` respectively.

---

## 2. Python Code Modifications

### 2.1 Centralize Supabase Client

* Moved Supabase client initialization into **logger/db_api.py**:

  ```python
  from supabase import create_client
  SUPABASE_URL = os.getenv("SUPABASE_URL")
  SUPABASE_KEY = os.getenv("SUPABASE_KEY")
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
  ```

### 2.2 live.py Changes

1. **Imports**

   ```python
   import json
   from logger.db_api import supabase
   ```
2. **Payload print & insert** (replaces `archive_match_json` helper):

   ```python
   print("▶️ PAYLOAD:", json.dumps(match_data, indent=2), flush=True)
   response = supabase.table("archived_json").insert({"raw_json": match_data}).execute()
   if getattr(response, "error", None):
       print("   ❌ INSERT FAILED:", response.error, flush=True)
   else:
       print("   ✅ Inserted, DB row id:", response.data[0]["id"], flush=True)
   ```

### 2.3 main_logger.py Changes

1. **Import shared client**

   ```python
   from logger.db_api import supabase
   ```
2. **send_to_db(chunk) listener** prints & inserts:

   ```python
   print("▶️ PAYLOAD:", chunk, flush=True)
   response = supabase.table("main_logger_logs").insert({"content": chunk}).execute()
   if getattr(response, "error", None):
       print("   ❌ INSERT FAILED:", response.error, flush=True)
   else:
       print("   ✅ Inserted, DB row id:", response.data[0]["id"], flush=True)
   ```

---

## 3. SQL Views for "Newest-First" & Formatted Timestamps

### 3.1 Drop Old Views

```sql
DROP VIEW IF EXISTS archived_json_newest_first;
DROP VIEW IF EXISTS main_logger_logs_newest_first;
```

### 3.2 Create `archived_json_newest_first`

```sql
CREATE VIEW archived_json_newest_first AS
SELECT
  id,
  raw_json,
  to_char(
    created_at AT TIME ZONE 'America/New_York',
    'MM/DD/YYYY HH12:MI:SS AM'
  ) AS created_at
FROM archived_json
ORDER BY created_at DESC;
```

### 3.3 Create `main_logger_logs_newest_first`

```sql
CREATE VIEW main_logger_logs_newest_first AS
SELECT
  id,
  content,
  to_char(
    created_at AT TIME ZONE 'America/New_York',
    'MM/DD/YYYY HH12:MI:SS AM'
  ) AS created_at
FROM main_logger_logs
ORDER BY created_at DESC;
```

These views present rows in **newest-first** order, with `created_at` formatted in Eastern Time, 12-hour clock with AM/PM.

---

## 4. Verification Steps

1. **Confirm views exist**:

   ```sql
   SELECT table_name
   FROM information_schema.views
   WHERE table_schema = 'public'
     AND table_name IN ('archived_json_newest_first', 'main_logger_logs_newest_first');
   ```

2. **Check sample rows**:

   ```sql
   SELECT * FROM archived_json_newest_first LIMIT 1;
   SELECT * FROM main_logger_logs_newest_first LIMIT 1;
   ```

3. **AM/PM test**:

   ```sql
   INSERT INTO main_logger_logs (content, created_at)
   VALUES ('Manual PM test', '2025-05-06 20:15:00+00'::timestamptz);
   SELECT * FROM main_logger_logs_newest_first WHERE content = 'Manual PM test';
   ```

---

## 5. Usage in Python

* **Writing** remains pointed at base tables:

  ```python
  supabase.table("archived_json").insert(...)
  supabase.table("main_logger_logs").insert(...)
  ```

* **Reading** can use the views:

  ```python
  supabase.from_("archived_json_newest_first").select("*").execute()
  supabase.from_("main_logger_logs_newest_first").select("*").execute()
  ```

Or add explicit ordering on base tables:

```python
supabase.from_("main_logger_logs").select("*").order("created_at", desc=True).execute()
```

---

## 6. Optional: Real-Time in Supabase Studio

* In **Table Editor**, open each view and toggle **Realtime** on.

---

With this setup, your database will store incoming JSON and formatted logs in their base tables, but display them prepended (newest-first) with accurate Eastern Time, AM/PM timestamps via the SQL views.
