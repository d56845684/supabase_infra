#!/bin/sh
# Wrapper to run Supabase CLI in a container attached to the docker-compose network.
# This is useful when the CLI is not installed on the host.

set -e

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

image="${SUPABASE_CLI_IMAGE:-supabase/cli:v1.188.3}"
network="${SUPABASE_NETWORK:-supabase_default}"

usage() {
    cat <<USAGE
Usage: $(basename "$0") [supabase arguments]

Examples:
  SUPABASE_ACCESS_TOKEN=... $(basename "$0") db pull
  SUPABASE_ACCESS_TOKEN=... $(basename "$0") db push

Environment variables:
  SUPABASE_ACCESS_TOKEN  Token for remote operations (passed through to the container)
  SUPABASE_CLI_IMAGE     Override the Supabase CLI image (default: $image)
  SUPABASE_NETWORK       Override the Compose network name (default: $network)
USAGE
}

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is required but not found." >&2
    exit 1
fi

if [ ! -d "$project_root/supabase" ]; then
    echo "Error: supabase directory not found in $project_root" >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

# Preserve interactivity only when a TTY is available to avoid hanging in CI
run_flags="--rm -i"
if [ -t 0 ]; then
    run_flags="--rm -it"
fi

docker run $run_flags \
    --network "$network" \
    -v "$project_root":/workspace \
    -w /workspace \
    -e SUPABASE_ACCESS_TOKEN \
    "$image" "$@"
