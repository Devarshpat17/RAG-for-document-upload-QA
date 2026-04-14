# Troubleshooting Guide: 500 Error on Document Upload

## Problem
When running `python example_usage.py`, you get a `500 Server Error` on the first document upload attempt.

## Root Cause
The **embedding model** (sentence-transformers) needs to be downloaded and loaded on first use. This can take 30-120 seconds depending on your internet speed and system performance, causing a timeout.

## Solutions

### Solution 1: Pre-load the Embedding Model (RECOMMENDED)
Before running example_usage.py, warm up the services:

```bash
# In a terminal with the virtual environment activated:
python manage.py warmup_services
```

This command will:
- Download and cache the embedding model
- Pre-load it into memory
- Verify everything is working

After this completes successfully, run the example:
```bash
python example_usage.py
```

### Solution 2: Use the Debug Test Script
Instead of example_usage.py, use the simpler debug script:

```bash
python test_api.py
```

This script:
- Has better timeout handling (120 seconds)
- Provides more detailed error messages
- Tests the API step by step
- Tells you exactly what's happening

### Solution 3: Increase Timeout in example_usage.py
The timeout has already been increased to 120 seconds in the updated files. The script will now wait up to 2 minutes for the first request.

### Solution 4: Check Server Logs
If you're still getting timeout errors:

1. Keep the Django development server running in one terminal
2. In another terminal, run the test script
3. Watch the server terminal for detailed error messages

The server logs will show you exactly what failed.

## Expected Behavior

**First Run (after warm-up):**
- Document upload: 5-10 seconds
- Processing: Should complete without errors

**After First Run:**
- Much faster (model is already loaded)
- Should be instantaneous

## If you still have issues:

1. **Check internet connection:** The model needs to be downloaded from HuggingFace
2. **Check disk space:** About 500MB is needed for the embedding model
3. **Check RAM:** The embedding model requires at least 1-2GB of free RAM
4. **Check if model is already cached:**
   ```bash
   # Look in ~/.cache/huggingface/
   # The model files should be there after first load
   ```

5. **Try a smaller embedding model:**
   Edit `.env` and change:
   ```
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```
   to:
   ```
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```
   (this is already the smallest recommended model)

## Quick Start
```bash
# 1. Start Django server in terminal 1
python manage.py runserver

# 2. In terminal 2, warm up services
python manage.py warmup_services

# 3. Run examples
python test_api.py
# or
python example_usage.py
```

## Files Changed
- `views.py` - Added detailed logging to track processing steps
- `example_usage.py` - Increased timeout to 120 seconds
- `apps.py` - Added optional auto-warmup capability
- `chatbot/management/commands/warmup_services.py` - New command to pre-load models
- `test_api.py` - New debug/test script with better error handling
