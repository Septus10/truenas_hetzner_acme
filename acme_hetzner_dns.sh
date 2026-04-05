#!/bin/bash

### VARIABLES
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LOGFILE="${SCRIPT_DIR}/acme_hetzner_dns.log"
# Uncomment in case you cannot set permanent environment variables on your system.
#HETZNER_CLOUD_API_KEY=""

_log() {
    echo "$(date "+[%F %T]") $1" >> "$LOGFILE"
}

_log "INFO acme_shell_auth.sh script started, calling python..."

PYTHON_PATH=$(which python3)
_log "Python found at location: ${PYTHON_PATH}"
PYTHON_VERSION=$("${PYTHON_PATH}" --version)
_log "Python version: ${PYTHON_VERSION}"

"${PYTHON_PATH}" "${SCRIPT_DIR}"/acme_hetzner_dns.py $1 $2 $3 $4 ${HETZNER_CLOUD_API_KEY}>> "$LOGFILE" 2>&1
