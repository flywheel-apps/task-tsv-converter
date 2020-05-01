#!/usr/bin/env sh
set -eu
unset CDPATH
cd "$( dirname "$0" )/../.."

USAGE="
Usage:
    $0 [OPTION...] [[--] TEST_ARGS...]
Run tests in a docker container.
Options:
    -h, --help      Print this help and exit
    -- TEST_ARGS    Arguments passed to tests.sh
"

main() {
    BUILD_IMAGE=1
    DOCKERFILE="Dockerfile"
    DOCKER_TAG="testing"
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                printf "$USAGE" >&2
                exit 0
                ;;
            -B|--no-build)
                BUILD_IMAGE=
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

    DOCKER_IMAGE="flywheel/task-tsv-converter:${DOCKER_TAG}"

    if [ "${BUILD_IMAGE}" == "1" ]; then
        docker build -f "${DOCKERFILE}" -t "${DOCKER_IMAGE}" --target testing .
    fi

    docker run -it --rm \
        --volume "$(pwd):/src" \
        "${DOCKER_IMAGE}" \
        bash /src/tests/bin/tests.sh "$@"
}

main "$@"
