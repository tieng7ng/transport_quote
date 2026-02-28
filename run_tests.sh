#!/bin/bash
# ============================================================
# run_tests.sh — Lance les tests backend (unitaires + API)
# Usage :
#   ./run_tests.sh           → tous les tests
#   ./run_tests.sh unit      → tests unitaires seulement
#   ./run_tests.sh api       → tests fonctionnels seulement
#   ./run_tests.sh <module>  → ex: ./run_tests.sh auth
# ============================================================

set -e

SCOPE=${1:-all}
PYTEST_ARGS="-v --tb=short --no-header"

echo ""
echo "══════════════════════════════════════════════════"
echo "  Transport Quote — Tests Backend"
echo "══════════════════════════════════════════════════"
echo ""

case "$SCOPE" in
  all)
    echo "▶ Lancement de tous les tests..."
    TARGET="app/tests/"
    ;;
  unit)
    echo "▶ Tests unitaires (app/tests/unit/)..."
    TARGET="app/tests/unit/"
    ;;
  api|fonctionnels)
    echo "▶ Tests fonctionnels API (app/tests/api/)..."
    TARGET="app/tests/api/"
    ;;
  *)
    # Recherche du module dans api/ ou unit/
    echo "▶ Recherche du module '$SCOPE'..."
    TARGET="app/tests/ -k $SCOPE"
    PYTEST_ARGS="$PYTEST_ARGS"
    ;;
esac

# Lancement via Docker Compose
docker compose run --rm \
  -e PYTHONDONTWRITEBYTECODE=1 \
  backend \
  pytest $TARGET $PYTEST_ARGS \
  --color=yes \
  --durations=10

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Tous les tests ont réussi."
else
  echo "❌ Des tests ont échoué (code $EXIT_CODE)."
fi
echo ""

exit $EXIT_CODE
