#!/usr/bin/env bash
# Merge SOURCE_BRANCH into all branches and push to REMOTE.
# Usage: ./update_branches.sh [SOURCE_BRANCH] [REMOTE]
# Defaults: SOURCE_BRANCH=master, REMOTE=origin

set -euo pipefail

SOURCE_BRANCH="${1:-master}"
REMOTE="${2:-origin}"

# Simple colors
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Ensure we're in a git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not a git repo."; exit 1; }

# Working tree must be clean
if [[ -n "$(git status --porcelain)" ]]; then
  echo -e "${RED}Working tree is dirty. Commit or stash first.${NC}"
  exit 1
fi

# Fetch and prune
git fetch --all --prune

# Ensure source branch exists locally and is up to date
if ! git show-ref --verify --quiet "refs/heads/${SOURCE_BRANCH}"; then
  git checkout -t "${REMOTE}/${SOURCE_BRANCH}"
else
  git checkout "${SOURCE_BRANCH}"
fi
git pull --ff-only "${REMOTE}" "${SOURCE_BRANCH}"
git push "${REMOTE}" "${SOURCE_BRANCH}" || true

# Build list of remote branches (excluding HEAD and SOURCE)
mapfile -t REMOTE_BRANCHES < <(
  git for-each-ref --format='%(refname:short)' "refs/remotes/${REMOTE}/*" \
  | sed "s#^${REMOTE}/##" \
  | grep -vE "^(HEAD|${SOURCE_BRANCH})$"
)

echo -e "${YELLOW}Will merge '${SOURCE_BRANCH}' into: ${REMOTE_BRANCHES[*]}${NC}"

SUCCESS=()
CONFLICT=()
SKIPPED=()

for BR in "${REMOTE_BRANCHES[@]}"; do
  echo -e "${YELLOW}--- Updating branch '${BR}' ---${NC}"

  # Create local tracking branch if missing
  if ! git show-ref --verify --quiet "refs/heads/${BR}"; then
    git checkout -b "${BR}" --track "${REMOTE}/${BR}" || { echo "Skip ${BR} (cannot checkout)"; SKIPPED+=("${BR}"); continue; }
  else
    git checkout "${BR}"
  fi

  # Update branch fast-forward from remote
  git pull --ff-only "${REMOTE}" "${BR}" || true

  # Merge source into this branch
  set +e
  git merge --no-ff --no-edit "${SOURCE_BRANCH}"
  MERGE_RC=$?
  set -e

  if [[ ${MERGE_RC} -ne 0 ]]; then
    echo -e "${RED}Conflict on '${BR}'. Aborting merge and skipping.${NC}"
    git merge --abort || true
    CONFLICT+=("${BR}")
    continue
  fi

  # Push the merged branch
  git push "${REMOTE}" "${BR}" && SUCCESS+=("${BR}") || { echo "Push failed for ${BR}"; SKIPPED+=("${BR}"); }
done

# Go back to source branch
git checkout "${SOURCE_BRANCH}"

echo -e "${GREEN}\nDone.${NC}"
echo -e "${GREEN}Merged & pushed:${NC} ${SUCCESS[*]:-<none>}"
echo -e "${RED}Conflicts (manual fix needed):${NC} ${CONFLICT[*]:-<none>}"
echo -e "${YELLOW}Skipped/failed:${NC} ${SKIPPED[*]:-<none>}"

