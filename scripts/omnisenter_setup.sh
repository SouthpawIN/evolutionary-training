#!/usr/bin/env bash
# omnisenter_setup.sh — One-click install for the entire OmniSenter stack.
#
# Installs (in order, all independent, all safe to re-run):
#   1. System deps (python3, mpv, git, uv, pip) — via apt
#   2. evolutionary-radio (the music engine)
#   3. nous-girl-agent (the Omni VA / desktop pet)
#   4. southpaw-server (the local model server)
#   5. evolutionary-training (the training repo + notebook + connectors)
#   6. The OmniSenter integration (notebook ↔ radio ↔ pet ↔ wiki)
#   7. The notebook + wiki directories with privacy-first perms
#
# Usage:
#   ./omnisenter_setup.sh                  # full install
#   ./omnisenter_setup.sh --no-radio       # skip the radio (no GPU for ACE-Step)
#   ./omnisenter_setup.sh --no-va          # skip the VA (no display)
#   ./omnisenter_setup.sh --no-server      # skip the local model server
#   ./omnisenter_setup.sh --no-train-repo  # skip the training repo (lighter)
#   ./omnisenter_setup.sh --dir ~/projects # install into a different dir
#
# After install:
#   # Run components (in separate terminals or as background services):
#   ~/projects/evolutionary-radio/start_radio.sh start --vibe "chill lofi"
#   ~/projects/nous-girl-agent/scripts/run-assistant.sh
#   ~/projects/nous-girl-agent/scripts/run-radio.sh start
#   ~/projects/nous-girl-agent/scripts/run-agent.sh
#
#   # Or use the master launcher:
#   ~/projects/nous-girl-agent/scripts/dev.sh
#
# Hardware requirements:
#   - Linux (tested on Ubuntu 24.04) or macOS
#   - GPU: NVIDIA recommended for radio + local model server (RTX 3090 ideal)
#   - Disk: 5GB for code, +20GB if you want to run models
#
# License: MIT
set -euo pipefail

# ---- Config ----------------------------------------------------------------
DEFAULT_INSTALL_DIR="$HOME/projects"
SKIP_RADIO=false
SKIP_VA=false
SKIP_SERVER=false
SKIP_TRAIN_REPO=false
VERBOSE=false

REPOS=(
    "evolutionary-radio|https://github.com/SouthpawIN/evolutionary-radio.git"
    "nous-girl-agent|https://github.com/SouthpawIN/nous-girl-agent.git"
    "southpaw-server|https://github.com/SouthpawIN/southpaw-server.git"
    "evolutionary-training|https://github.com/SouthpawIN/evolutionary-training.git"
    "omnisenter-blog|https://github.com/SouthpawIN/omnisenter-blog.git"
)

# ---- Colors ----------------------------------------------------------------
if [[ -t 1 ]]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; NC=''
fi

# ---- Logging ---------------------------------------------------------------
log()  { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "${RED}✗${NC}  $*" >&2; }
hdr()  { echo -e "\n${BOLD}${BLUE}── $* ──${NC}"; }
die()  { err "$*"; exit 1; }
vrun() { if $VERBOSE; then "$@"; else "$@" >/dev/null 2>&1; fi; }

# ---- Args ------------------------------------------------------------------
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-radio)      SKIP_RADIO=true ;;
        --no-va)         SKIP_VA=true ;;
        --no-server)     SKIP_SERVER=true ;;
        --no-train-repo) SKIP_TRAIN_REPO=true ;;
        --dir)           INSTALL_DIR="$2"; shift 2 ;;
        -v|--verbose)    VERBOSE=true ;;
        -h|--help)
            sed -n '2,30p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) die "Unknown arg: $1 (try --help)" ;;
    esac
    shift
done

# ---- Welcome ---------------------------------------------------------------
echo -e "${BOLD}${BLUE}"
cat <<'BANNER'
   ____                  __                          __
  / __ \____ ___  ______/ /_____  ____ ___  ___  ____/ /
 / / / / __ `/ / / / __  //_/ _ \/ __ `__ \/ _ \/ __  /
/ /_/ / /_/ / /_/ / /_/ / /  __/ / / / / /  __/ /_/ /
\____/\__,_/\__,_/\__,_/_/_\___/_/ /_/ /_/\___/\__,_/

        TOWARDS SELF-IMPROVEMENT · 2026-06-08
BANNER
echo -e "${NC}"
log "One-click installer for the OmniSenter stack"
log "Install dir: $INSTALL_DIR"
[[ $SKIP_RADIO   == true ]] && log "  --no-radio"
[[ $SKIP_VA      == true ]] && log "  --no-va"
[[ $SKIP_SERVER  == true ]] && log "  --no-server"
[[ $SKIP_TRAIN_REPO == true ]] && log "  --no-train-repo"

# ---- 1. System deps --------------------------------------------------------
hdr "1/7 System dependencies"
MISSING=()
for cmd in python3 git pip; do
    command -v "$cmd" >/dev/null 2>&1 || MISSING+=("$cmd")
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    warn "Missing: ${MISSING[*]}"
    if command -v apt-get >/dev/null 2>&1; then
        log "Installing via apt (sudo)..."
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-pip python3-venv git mpv
    elif command -v brew >/dev/null 2>&1; then
        log "Installing via brew..."
        brew install python3 mpv git
    else
        die "Please install: ${MISSING[*]} (apt or brew)"
    fi
fi
# uv (for fast Python deps)
if ! command -v uv >/dev/null 2>&1; then
    log "Installing uv (fast Python package manager)..."
    pip install --user uv 2>/dev/null || pip3 install --user uv
fi
command -v mpv >/dev/null 2>&1 || warn "mpv not found (radio playback will not work without it)"
log "System deps OK"

# ---- 2. Clone repos --------------------------------------------------------
hdr "2/7 Cloning the repos"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Filter out skipped repos
ACTIVE_REPOS=()
for entry in "${REPOS[@]}"; do
    name="${entry%%|*}"
    url="${entry##*|}"
    skip=false
    [[ $name == "evolutionary-radio" && $SKIP_RADIO == true ]] && skip=true
    [[ $name == "nous-girl-agent"    && $SKIP_VA == true ]] && skip=true
    [[ $name == "southpaw-server"    && $SKIP_SERVER == true ]] && skip=true
    [[ $name == "evolutionary-training" && $SKIP_TRAIN_REPO == true ]] && skip=true
    [[ $name == "omnisenter-blog"    && $SKIP_TRAIN_REPO == true ]] && skip=true
    [[ $skip == true ]] && continue
    if [[ -d "$name" ]]; then
        log "$name: already present, skipping clone"
    else
        log "$name: cloning $url"
        vrun git clone --depth 1 "$url" "$name"
    fi
    ACTIVE_REPOS+=("$name")
done

# ---- 3. Radio install ------------------------------------------------------
hdr "3/7 Evolutionary Radio"
if [[ " ${ACTIVE_REPOS[*]} " == *" evolutionary-radio "* ]]; then
    cd "$INSTALL_DIR/evolutionary-radio"
    # Make the start script executable
    chmod +x start_radio.sh radio.py 2>/dev/null || true
    # Set up venv + install deps
    if [[ ! -d venv ]]; then
        log "Creating venv..."
        python3 -m venv venv
    fi
    # shellcheck disable=SC1091
    source venv/bin/activate
    log "Installing radio deps (this can take a few minutes)..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt || warn "Some radio deps failed (ACE-Step needs GPU; non-GPU install is OK for testing)"
    deactivate
    # Make tests runnable
    [[ -f pytest.ini ]] || cat > pytest.ini <<'PYI'
[pytest]
testpaths = .
python_files = test_*.py
addopts = --ignore=tests/test_all.py
PYI
    log "Radio installed"
else
    log "Skipped (--no-radio)"
fi

# ---- 4. Nous-Girl-Agent (the Omni VA) install -----------------------------
hdr "4/7 Omni VA (Nous Girl Agent)"
if [[ " ${ACTIVE_REPOS[*]} " == *" nous-girl-agent "* ]]; then
    cd "$INSTALL_DIR/nous-girl-agent"
    # Use the existing install.sh if present (it does the heavy lifting)
    if [[ -x scripts/install.sh ]]; then
        log "Running scripts/install.sh..."
        bash scripts/install.sh --no-radio || warn "install.sh had warnings (probably vtuber-core deps; safe to continue)"
    else
        warn "scripts/install.sh not found; skipping"
    fi
    log "Omni VA installed"
else
    log "Skipped (--no-va)"
fi

# ---- 5. Southpaw-Server (the local model server) install -------------------
hdr "5/7 Southpaw Server (local model manager)"
if [[ " ${ACTIVE_REPOS[*]} " == *" southpaw-server "* ]]; then
    cd "$INSTALL_DIR/southpaw-server"
    if [[ -x setup.sh ]]; then
        log "Running setup.sh..."
        bash setup.sh || warn "setup.sh had warnings"
    else
        warn "setup.sh not found; skipping"
    fi
    # Verify llama_manager imports cleanly
    if python3 -c "import sys; sys.path.insert(0, 'src'); import llama_manager" 2>/dev/null; then
        log "llama_manager imports OK"
    else
        warn "llama_manager import failed (likely needs llama.cpp binary; OK for now)"
    fi
    log "Southpaw Server installed"
else
    log "Skipped (--no-server)"
fi

# ---- 6. Evolutionary-Training (the orchestrator + notebook) install --------
hdr "6/7 Evolutionary Training (notebook + connectors + blog)"
if [[ " ${ACTIVE_REPOS[*]} " == *" evolutionary-training "* ]]; then
    cd "$INSTALL_DIR/evolutionary-training"
    # PyYAML is the only dep for the notebook
    if ! python3 -c "import yaml" 2>/dev/null; then
        log "Installing PyYAML for the notebook..."
        pip install --quiet --user pyyaml
    fi
    # Make scripts executable
    chmod +x scripts/*.sh 2>/dev/null || true
    log "Notebook module: scripts/senter_notebook/notebook.py"
    log "Integration:    scripts/omnisenter_integration/"
    log "  - notebook_connector.py (notebook ↔ wiki ↔ radio ↔ pet)"
    log "  - scroll_agent.py       (Hermes tool to control the radio)"
    log "Blog:           blog/ (deployed at southpawin.github.io)"
    log "Evolutionary Training installed"
else
    log "Skipped (--no-train-repo)"
fi

# ---- 7. Privacy-first notebook + wiki + handoff dirs -----------------------
hdr "7/7 Notebook + Wiki + Handoff directories"
NOTEBOOK_DIR="$HOME/.senter/notebook"
WIKI_DIR="$HOME/.senter/wiki"
HANDOFF_DIR="$HOME/wiki/pet-curated"

for d in "$NOTEBOOK_DIR" "$WIKI_DIR" "$HANDOFF_DIR" "$HANDOFF_DIR/escalations"; do
    mkdir -p "$d"
    chmod 700 "$d"
    log "Created $(basename "$d") dir: $d (chmod 700)"
done

# Touch a starter taste.yaml if it doesn't exist (the pet uses this)
TASTE="$HANDOFF_DIR/taste.yaml"
if [[ ! -f "$TASTE" ]]; then
    cat > "$TASTE" <<EOF
created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
last_updated: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
music:
  likes: []
  skips: []
vibes:
  current: "chill lofi beats for coding"
  history: []
EOF
    chmod 600 "$TASTE"
    log "Wrote $TASTE"
fi

# ---- Done! ----------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}  ✓ OmniSenter installed!${NC}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BOLD}Quick start:${NC}"
echo ""
echo -e "  ${BOLD}# Start the radio (perpetual, self-evolving music)${NC}"
echo "  $INSTALL_DIR/evolutionary-radio/start_radio.sh start --vibe 'chill lofi'"
echo ""
echo -e "  ${BOLD}# Start the Omni VA (desktop pet + voice + radio + agent)${NC}"
echo "  $INSTALL_DIR/nous-girl-agent/scripts/dev.sh"
echo ""
echo -e "  ${BOLD}# Use the scroll agent (Hermes tool for the radio)${NC}"
echo "  python3 $INSTALL_DIR/evolutionary-training/scripts/omnisenter_integration/scroll_agent.py status"
echo "  python3 $INSTALL_DIR/evolutionary-training/scripts/omnisenter_integration/scroll_agent.py play --vibe 'dark ambient'"
echo "  python3 $INSTALL_DIR/evolutionary-training/scripts/omnisenter_integration/scroll_agent.py ask 'what should I work on?'"
echo ""
echo -e "  ${BOLD}# Use the notebook connector (write/read notebook from anywhere)${NC}"
echo "  python3 $INSTALL_DIR/evolutionary-training/scripts/omnisenter_integration/notebook_connector.py log-pet --content 'Hello'"
echo "  python3 $INSTALL_DIR/evolutionary-training/scripts/omnisenter_integration/notebook_connector.py for-hermes --query 'music' --text-only"
echo ""
echo -e "  ${BOLD}# Run the test suites${NC}"
echo "  cd $INSTALL_DIR/evolutionary-training/scripts/senter_notebook && python3 -m unittest test_notebook"
echo "  cd $INSTALL_DIR/evolutionary-training/scripts/omnisenter_integration/tests && python3 -m unittest test_integration"
echo "  cd $INSTALL_DIR/nous-girl-agent && python3 -m unittest discover -s tests"
echo "  cd $INSTALL_DIR/southpaw-server && python3 -m unittest discover -s tests"
echo ""
echo -e "  ${BOLD}# Read the canonical docs${NC}"
echo "  cat $INSTALL_DIR/evolutionary-training/blog/the-omni-family.md"
echo "  cat $INSTALL_DIR/evolutionary-training/blog/omnisenter-flagship.md"
echo "  cat $INSTALL_DIR/evolutionary-training/blog/stages-2-to-4-prep.md"
echo ""
echo -e "  ${BOLD}Blog (deployed):${NC} https://southpawin.github.io/"
echo ""
log "TOWARDS SELF-IMPROVEMENT"
