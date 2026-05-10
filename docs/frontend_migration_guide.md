# CorRes Frontend Migration Guide — v0.9.0 → v0.9.1

**Repository:** `correlating-resonance`
**Files affected:** `cr_phase1_typology.html`, `cr_phase2_saturation.html`, `cr_phase3_1_coding.html`, `cr_phase4_analysis.html`
**Files unaffected:** `index.html`

This guide gives the exact edits needed for each file. Line numbers are from the v0.9.0 committed versions and may shift slightly if other edits have been made.

---

## 1. Common edits — apply to all four phase files

### 1.1 Add `config.js` to `<head>`

In each phase file, find the `<head>` section. Add a `<script>` tag for `config.js` immediately after the existing `<link>` and external `<script>` tags, before `<style>`. Example for Phase 1 (similar location in all four):

**Before** (Phase 1, around line 8):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>
```

**After:**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="config.js"></script>
<style>
```

### 1.2 Delete the `API_KEY` constant

Find the line declaring `API_KEY` in the inline `<script>` block:

| File | Line | Content |
|---|---|---|
| Phase 1 | 688 | `const API_KEY = 'YOUR_API_KEY_HERE';` |
| Phase 2 | 817 | `const API_KEY = 'YOUR_API_KEY_HERE';` |
| Phase 3 | 552 | `const API_KEY  = 'YOUR_API_KEY_HERE';` |
| Phase 4 | 536 | `const API_KEY = 'YOUR_API_KEY_HERE';` |

**Delete the line entirely.** The `MODEL` constant immediately below it stays — it's the methodology-level model pin per platform contract §6 and design decision D2.

### 1.3 Replace the `callAPI` function body

Each file has a `callAPI` function that looks substantially the same. Replace its entire body with the new implementation. The function signature `(system, user, maxTokens = N)` is preserved — call sites do not change.

| File | Line range | Default `maxTokens` |
|---|---|---|
| Phase 1 | 1077–1101 | 3000 |
| Phase 2 | 1151–1173 | 4096 |
| Phase 3 | 1322–end of function | 4096 |
| Phase 4 | 1464–1481 | 2048 |

**Replacement** (preserve each file's specific default for `maxTokens`):

```javascript
async function callAPI(system, user, maxTokens = 4096) {
  const cfg = window.CORRES_CONFIG;
  if (!cfg || !cfg.apiBase) {
    throw new Error('CORRES_CONFIG not loaded — check config.js is deployed');
  }

  const requestId = (crypto.randomUUID && crypto.randomUUID()) ||
                    (Date.now() + '-' + Math.random().toString(36).slice(2));

  const res = await fetch(`${cfg.apiBase}/v1/corres/llm/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-Id': requestId,
    },
    body: JSON.stringify({
      system,
      user,
      max_tokens: maxTokens,
      model_pin:  MODEL,
    }),
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const err = await res.json();
      detail = err?.detail?.message || err?.error?.message || detail;
    } catch (_) { /* keep statusText */ }
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  const data = await res.json();
  return data.text;
}
```

Things to keep when copy-pasting:

- The `maxTokens` default value in the function signature must match what's currently in each file (3000 / 4096 / 4096 / 2048). Only the body is being replaced.
- `MODEL` is referenced by name; the constant declaration on the line below where `API_KEY` used to be remains unchanged.

---

## 2. Phase 3 — additional edit (multimodal vision call)

Phase 3's `codeDocumentVision` function (line 1195 in the current file) contains a second `fetch` to the Anthropic API at lines 1253–1267, used for the vision-mode PDF call. This call must also be migrated.

### 2.1 What the current code does

The function:
1. Builds `userContent` — an array containing a `document` block (base64-encoded PDF) and a `text` block with the typology and instructions.
2. Inline `fetch` to `https://api.anthropic.com/v1/messages` with `messages: [{ role: 'user', content: userContent }]`.
3. Reads `data.content.map(b => b.text || '').join('')` from the response.
4. Calls `repairJSON(text)` on that string.
5. Returns structured scores.

### 2.2 What changes

The new `callAPI` accepts a content array as its `user` argument — the platform wraps it as the user message content unchanged. So the inline `fetch` collapses to a single `callAPI` invocation. **The `repairJSON()` call stays** — it's part of the application layer per design decision D3.

### 2.3 The edit

**Before** (lines 1253–1276 in the current file):

```javascript
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true'
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 4096,
      system: systemPrompt,
      messages: [{ role: 'user', content: userContent }]
    })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || `API error ${res.status}`);
  }

  const data   = await res.json();
  const text   = data.content.map(b => b.text || '').join('');
  const parsed = repairJSON(text);
```

**After:**

```javascript
  const text   = await callAPI(systemPrompt, userContent, 4096);
  const parsed = repairJSON(text);
```

The 24 lines collapse to 2. Error handling moves into `callAPI`'s implementation; `repairJSON` is unchanged. The rest of the function (the `scores` mapping that follows `parsed`) is untouched.

---

## 3. Verification

After making all edits in all four files:

### 3.1 Sanity checks on the source

```bash
cd correlating-resonance/

# No API_KEY constants should remain.
grep -n "API_KEY" cr_phase*.html
# Expected output: nothing.

# No direct calls to the Anthropic API should remain.
grep -n "api.anthropic.com" cr_phase*.html
# Expected output: nothing.

# Every phase file should reference config.js.
grep -n "config.js" cr_phase*.html
# Expected: one match per phase file.

# Every phase file should reference CORRES_CONFIG.
grep -n "CORRES_CONFIG" cr_phase*.html
# Expected: one match per phase file (in the new callAPI body).
```

### 3.2 Local config

Create `config.js` in the repo root (do not commit — it's in `.gitignore`):

```javascript
window.CORRES_CONFIG = {
  apiBase:    'https://api-local.ebono.net',
  appId:      'corres',
  appVersion: '0.9.1',
};
```

### 3.3 Behavioural-parity test

The release gate per design §6.3: each phase produces analytical output indistinguishable from the v0.9.0 build on the same corpus. Because the model identifier is pinned to `claude-sonnet-4-20250514` in both versions, behaviour should match modulo provider-side noise.

Run each phase against a small test corpus (3–5 documents) and compare the output to the v0.9.0 baseline. If they match, the migration is clean.

---

## 4. Rollback

If the migration causes problems, the rollback is `git revert` of the migration commit. Because the v0.9.0 tag is on GitHub, you can also `git checkout v0.9.0` to recover the pre-migration state and continue from there. The platform code in the `artie` repo is unaffected by frontend rollback — it remains deployed and ready when you're ready to retry.
