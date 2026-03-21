#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

FAILED=()
PASSED=()
SKIPPED=()

run_step() {
    local name="$1"
    shift
    echo -e "\n${CYAN}── $name ──${NC}"
    echo -e "${YELLOW}$ $*${NC}"
    if "$@"; then
        PASSED+=("$name")
        echo -e "${GREEN}✓ $name${NC}"
    else
        FAILED+=("$name")
        echo -e "${RED}✗ $name${NC}"
    fi
}

skip_step() {
    local name="$1"
    local reason="$2"
    SKIPPED+=("$name ($reason)")
    echo -e "\n${YELLOW}── $name [SKIPPED: $reason] ──${NC}"
}

usage() {
    echo "Usage: $0 [rust|lint|python|all|fix]"
    echo ""
    echo "Mirrors the GitHub Actions CI workflows locally."
    echo ""
    echo "  rust     Rust CI:    cargo check, test, fmt --check, clippy"
    echo "  lint     Lint PR:    ruff check, isort --check-only"
    echo "  python   Python CI:  nox test suite (current Python version)"
    echo "  all      Everything  (default)"
    echo "  fix      Auto-fix:   cargo fmt, ruff --fix, isort"
    exit 0
}

# ── rust-CI.yml ───────────────────────────────────────────────────────────────
run_rust() {
    echo -e "\n${CYAN}═══ Rust CI (.github/workflows/rust-CI.yml) ═══${NC}"
    run_step "cargo check"   cargo check
    run_step "cargo test"    cargo test
    run_step "cargo fmt"     cargo fmt --check
    run_step "cargo clippy"  cargo clippy
}

# ── lint-pr.yml ───────────────────────────────────────────────────────────────
run_lint() {
    echo -e "\n${CYAN}═══ Lint PR (.github/workflows/lint-pr.yml) ═══${NC}"

    if command -v ruff &>/dev/null; then
        run_step "ruff check" ruff check .
    else
        skip_step "ruff check" "ruff not installed (pip install ruff)"
    fi

    if command -v isort &>/dev/null; then
        run_step "isort check" isort --check-only --diff .
    else
        skip_step "isort check" "isort not installed (pip install isort)"
    fi
}

# ── python-CI.yml ─────────────────────────────────────────────────────────────
run_python() {
    echo -e "\n${CYAN}═══ Python CI (.github/workflows/python-CI.yml) ═══${NC}"
    local pyver
    pyver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    if command -v nox &>/dev/null; then
        run_step "nox (python $pyver)" nox --non-interactive --error-on-missing-interpreter -p "$pyver"
    else
        skip_step "nox tests" "nox not installed (pip install nox)"
    fi
}

# ── fix mode ──────────────────────────────────────────────────────────────────
run_fix() {
    echo -e "\n${CYAN}═══ Auto-fix ═══${NC}"
    run_step "cargo fmt"  cargo fmt
    command -v ruff  &>/dev/null && run_step "ruff fix"  ruff check --fix . || skip_step "ruff fix" "not installed"
    command -v isort &>/dev/null && run_step "isort fix" isort .            || skip_step "isort fix" "not installed"
}

# ── main ──────────────────────────────────────────────────────────────────────
MODE="${1:-all}"

case "$MODE" in
    rust)   run_rust ;;
    lint)   run_lint ;;
    python) run_python ;;
    fix)    run_fix ;;
    all)    run_rust; run_lint; run_python ;;
    -h|--help|help) usage ;;
    *) echo "Unknown mode: $MODE"; usage ;;
esac

# ── summary ───────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}═══ Summary ═══${NC}"
for s in "${PASSED[@]+"${PASSED[@]}"}"; do echo -e "  ${GREEN}✓${NC} $s"; done
for s in "${SKIPPED[@]+"${SKIPPED[@]}"}"; do echo -e "  ${YELLOW}⊘${NC} $s"; done
for s in "${FAILED[@]+"${FAILED[@]}"}"; do echo -e "  ${RED}✗${NC} $s"; done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo -e "\n${RED}CI would fail: ${#FAILED[@]} check(s) failed.${NC}"
    exit 1
else
    echo -e "\n${GREEN}All checks passed. Safe to push.${NC}"
    exit 0
fi
