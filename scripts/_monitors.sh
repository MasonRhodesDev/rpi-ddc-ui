# Sourced by the monitor scripts. Not meant to be run directly.
# Reads monitor serial numbers from scripts/monitors.env (gitignored; copy
# scripts/monitors.env.example) or from the environment. Find your serials with:
#   sudo ddcutil detect
_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_env="${DESK_MONITORS_ENV:-$_dir/monitors.env}"
if [ -f "$_env" ]; then
    # shellcheck disable=SC1090
    . "$_env"
fi
if [ -z "${DESK_PRIMARY_SN:-}" ]; then
    echo "DESK_PRIMARY_SN is not set. Copy scripts/monitors.env.example to scripts/monitors.env and fill in your monitor serial numbers (or set DESK_MONITORS_ENV)." >&2
    exit 1
fi
require_secondary() {
    if [ -z "${DESK_SECONDARY_SN:-}" ]; then
        echo "DESK_SECONDARY_SN is not set. See scripts/monitors.env.example." >&2
        exit 1
    fi
}
