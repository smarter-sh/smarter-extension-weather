#!/usr/bin/env bash
# Run this Smarter Extension's tests in the local Smarter development container, smarter-app, the
# way CI runs them: against Smarter's code, without its database, and with coverage.
#
# usage, from the extension repository's root:
#   scripts/run-tests.sh            # tests + coverage report
#   scripts/run-tests.sh --validate # also run manage.py validate_extension
#
# It copies the working tree (without .git, node_modules, dist or CI's .smarter checkout) to
# /tmp/<repository name> in the container, replacing the previous copy that this script made.
# Nothing else in the container is changed. CONTAINER defaults to smarter-app.
#
# exit status: 0 if the tests (and validation, if asked) pass, 1 otherwise.
set -euo pipefail

CONTAINER="${CONTAINER:-smarter-app}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="$(basename "$ROOT")"
TARGET="/tmp/$NAME"
SMARTER="/home/smarter_user/smarter"

[ -f "$ROOT/pyproject.toml" ] || { echo "no pyproject.toml in $ROOT" >&2; exit 1; }
docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true \
  || { echo "$CONTAINER is not running: start the Smarter development environment (make run in ../smarter)" >&2; exit 1; }

# tar rather than docker cp: docker cp nests into an existing directory, and can't exclude anything.
# as root, because a copy made earlier with docker cp is owned by root.
docker exec -u root "$CONTAINER" bash -c "rm -rf '$TARGET' && mkdir -p '$TARGET' && chown smarter_user '$TARGET'"
tar -C "$ROOT" --exclude=.git --exclude=node_modules --exclude=dist --exclude=.smarter \
  --exclude=__pycache__ --exclude=.coverage --exclude=.mypy_cache -cf - . \
  | docker exec -i "$CONTAINER" tar -C "$TARGET" -xf -

STATUS=0
docker exec "$CONTAINER" bash -c "cd '$TARGET' && PYTHONPATH='$TARGET:$SMARTER' \
  python -m coverage run --data-file=/tmp/.coverage-$NAME --source=. --omit='tests/*,scripts/*,skills/*' \
  -m unittest discover -s tests -t . -v && python -m coverage report -m --data-file=/tmp/.coverage-$NAME" \
  || STATUS=1

if [ "${1:-}" = "--validate" ]; then
  # the platform's startup logging is noisy: show only what validate_extension itself prints.
  RC=0
  OUTPUT="$(docker exec "$CONTAINER" bash -c "cd '$SMARTER' && python manage.py validate_extension '$TARGET'" 2>&1)" || RC=$?
  printf '%s\n' "$OUTPUT" | grep -v -E ' - (DEBUG|INFO) - |UserWarning|warnings.warn|smarter_settings|SECRET_KEY' || true
  [ "$RC" -eq 0 ] || STATUS=1
fi
exit $STATUS
