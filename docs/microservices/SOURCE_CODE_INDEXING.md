# Source indexing

Run from repo root:

```sh
python -m pip install -r scripts/architecture/requirements.txt
python scripts/architecture/generate_index.py
```

The generator enumerates Git tracked plus nonignored new source, never imports
application modules or executes target source. Python AST extracts declarations,
annotations, async/access markers, exact spans, literal route decorators/prefixes,
imports (including deferred scope) and calls. Tree-sitter 0.25.2 + language-pack
0.13.0 parse Kotlin, Swift, JS/TS and C++ structurally in bounded subprocesses;
parser crashes/timeouts are diagnostics, not invented symbols or whole-run failure.
0.26.0 exhibited a native Kotlin traversal crash in this environment and is pinned
out. Syntax recovery is explicitly reported. C++ has no semantic compilation DB.

Stable IDs use repository path + qualified name/kind/signature, independent of line
movement. Duplicate definitions get deterministic ordinal suffixes. Source hashes,
line ranges, parameters, return annotations and declaration parser are recorded.
Only direct Python lexical/import calls are statically bound; dynamic receiver and
native overload calls are unresolved. Static bindings are not runtime traces;
conditional imports, shadowing/monkey-patching and legacy __path__ aliases limit
certainty. Native imports remain unresolved, never falsely labeled verified.

Outputs: services/files/symbols/dependencies/call_graph/service_contracts.json,
summary.json (parser diagnostics/import SCCs), configuration.json (safe defaults)
and source-index.js (same data bundled for file:// offline viewing). Owner rules
are explicit conservative prefixes, with UNASSIGNED and shared composition visible.
Preview capped at 30,000 characters/file, plus 70-line/6,000-character per-symbol
previews for declarations later in large files, rendered through textContent. Python
credential-like literal assignments are redacted. No ENV/local JSON, binary assets,
symlinks, ignored secrets, venv/build caches or arbitrary host files are served.
The index is a public source artifact, not a secret scanner; never commit secrets
in source. Rebuild after source changes; hashes permit stale-index checks.
