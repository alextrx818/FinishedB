# PREPENDING UNIVERSAL RULE

This document outlines the universal buffering and prepending logic to be used for all logger implementations in the sports bot system.

## Implementation Logic

When adding a new logger, implement the following buffering logic to ensure a "newest-first" order while preserving intra-block structure:

### Step 1: Open logger/main_logger.py

Add these two module-level globals right under your imports:

```python
buffering = False
buffer_lines = []
```

### Step 2: In the body of new_print(*args, **kwargs)

After computing text (honoring sep/end), insert the block-start detector:

```python
if text.startswith("="*50):
    buffering = True
    buffer_lines.clear()
    buffer_lines.append(text)
    return
```

### Step 3: Add buffering logic to collect and flush entire blocks

Immediately after the block-start detector, add:

```python
if buffering:
    buffer_lines.append(text)
    # end of block is indicated by a blank line
    if text.strip() == "":
        # flush the whole chunk in one prepend
        chunk = "".join(buffer_lines)
        try:
            with open(LOG_FILE_PATH, 'r+') as f:
                old = f.read()
                f.seek(0)
                f.write(chunk + old)
                f.truncate()
        except Exception as e:
            original_print("Logger write error:", e)
        buffering = False
        buffer_lines.clear()
    return
```

### Step 4: Leave existing fallback intact

Leave your existing fallback (per-line prepend) unchanged for prints outside match blocks.

## Benefits

This universal approach provides:

1. Detection of the start of a logical block at your 50-character header
2. Buffering of every print() in that block—SUMMARY, ODDS, ENVIRONMENT—preserving the original order
3. Flushing and prepending the entire block at once when it hits the blank line
4. "Newest-first" order for log files without mangling intra-block structure

## Usage

This pattern should be used for all new loggers to ensure consistency and proper block ordering.
