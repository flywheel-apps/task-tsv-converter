#!/usr/bin/env sh

set -eu
unset CDPATH
cd "$( dirname $0 )/.."


USAGE="
Usage:
    $0 [OPTION...] [[--] PYTEST_ARGS...]
Runs all tests and linting.
Assumes running in test container or that flywheel_migration and all of its
dependencies are installed.
Options:
    -h, --help              Print this help and exit
    -s, --shell             Enter shell instead of running tests
    -- PYTEST_ARGS          Arguments passed to py.test
"


main() {
    PYTHONPATH=".."
    ls "$PYTHONPATH"
    export PYTHONPATH

    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                log "$USAGE"
                exit 0
                ;;
            -s|--shell)
                sh
                exit
                ;;
            --)
                shift
                break
                ;;
            *)
                break
                ;;
        esac
        shift
    done

    RUN_UNIT=true
    if ${RUN_UNIT}; then
        log "INFO: Running unit tests ...\n"
        python unit_tests/task-tsv-converter-tests.py
    fi
}

log() {
    printf "\n%s\n" "$@" >&2
}


main "$@"
