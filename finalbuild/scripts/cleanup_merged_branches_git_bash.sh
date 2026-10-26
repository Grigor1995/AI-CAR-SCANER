#!/usr/bin/env bash
# Safely prune ONLY named, fully-merged remote branches. Never force or rewrite history.
# Usage: bash scripts/cleanup_merged_branches_git_bash.sh
set -euo pipefail

remote="${1:-origin}"
repo_url="$(git remote get-url "$remote")"
if [[ "$repo_url" != *"Grigor1995/AI-CAR-SCANER"* ]]; then
  echo "[ABORT] Refusing cleanup on unexpected remote: $repo_url" >&2
  exit 2
fi

git fetch "$remote" '+refs/heads/*:refs/remotes/origin/*' --prune
main_ref="refs/remotes/$remote/main"
git rev-parse --verify "$main_ref" >/dev/null || { echo "[ABORT] Missing $main_ref" >&2; exit 2; }

branches=(
  'docs/mobile-ui-demo-screenshots-20261026'
  'integrate/branch-audit-cleanup-20261026'
  'feature/backend-unified-vehicle-obd-audit-20261022'
  'feature/neon-ui-desktop-android-ios'
  'fix/desktop-v1-fastapi-recovery-20261021'
  'fix/mobile-desktop-catalog-parity-20261022'
)

for branch in "${branches[@]}"; do
  ref="refs/remotes/$remote/$branch"
  if ! git show-ref --verify --quiet "$ref"; then
    echo "[SKIP] Already absent: $branch"
    continue
  fi
  if ! git merge-base --is-ancestor "$ref" "$main_ref"; then
    echo "[KEEP] Unique commits still exist: $branch"
    continue
  fi
  echo "[DELETE] Fully merged: $branch"
  git push "$remote" --delete "$branch" || echo "[WARN] Deletion blocked for $branch"
done

echo "[PRESERVED] main, design/neon-3d-ui-review-20261023, feat/backend-obd-vehicle-registry-20261022"
echo "[DONE] Run git fetch --prune origin on other clones to update remote-tracking refs."
