# Uploading results to Clio

Reference for **Step B steps 6-7** of `SKILL.md`, on the **Clio-sourced path only**.

> Skip this file entirely when the user supplied the source document (Step 0.0):
> the markdown is theirs and the PPTX is handed back directly. Uploading it
> publishes a document they only asked you to render.

6. **Upload approved markdown + all PNG images to Clio** — Clio-sourced runs only (the version that produced the PPTX). Repeat for each file (markdown + all PNGs in `outputs/`):

   > **⚠️ CRITICAL — HOW TO UPLOAD:** Step (b) below MUST be executed via the **Bash tool** calling `clio-api.py put`. **NEVER use WebFetch or any other tool** to PUT to presigned S3 URLs — only the Python script works reliably across all environments.

   a. Get file size in bytes:
      ```bash
      VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
      SKILL_DIR="claude/skills/bidding-proposal"

      wc -c < outputs/{file_name}
      ```
      Then call `clio_get_assets_upload_url` MCP tool — **one call per file**:
      ```json
      {
        "project_id": "{project_id}",
        "asset_type": "slide-content",
        "file_name": "{file_name}",
        "content_type": "{mime_type}",
        "file_size": {size_in_bytes}
      }
      ```
      Response: `upload_url`, `storage_path`.

   b. PUT the file to S3 via **Bash tool** (not WebFetch):
      ```bash
      $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py put \
        --url "{upload_url}" \
        --file outputs/{file_name}
      ```

   c. Finalize via `clio_finalize_assets_upload` MCP tool — **one call per file**:
      ```json
      {
        "project_id": "{project_id}",
        "asset_type": "slide-content",
        "file_name": "{file_name}",
        "storage_path": "{storage_path}",
        "content_type": "{mime_type}",
        "file_size": {size_in_bytes}
      }
      ```

   - **Version cleanup (PENDING — no delete API yet):** Ideally keep only the last 3 `SLIDE_CONTENT` markdown versions. Implement once a delete endpoint is available.

7. **Upload generated PPTX to Clio** via MCP tool:

   a. Get PPTX file size in bytes:
      ```bash
      wc -c < outputs/proposal_{id}_{ts}.pptx
      ```

   b. Call `clio_get_artifacts_upload_url` MCP tool:
      - `project_id`: "{project_id}"
      - `artifact_type`: "proposal_slide"
      - `file_name`: "proposal_{id}_{ts}.pptx"
      - `content_type`: "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      - `file_size`: {size_in_bytes}

   c. PUT the PPTX to the returned `upload_url` via **Bash tool** (not WebFetch):
      ```bash
      $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py put \
        --url "{upload_url}" \
        --file outputs/proposal_{id}_{ts}.pptx
      ```
      > **No finalize step** — the server auto-registers artifacts after the S3 PUT.

