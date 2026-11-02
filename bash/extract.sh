#!/bin/bash
#
#
#
#

VERBOSE=0
RECURSIVE=0
DECOMPRESSED=0
NOT_DECOMPRESSED=0

help() {
    cat <<'EOF'
Usage: extract [-h] [-r] [-v] file [file...]

Unpacks compressed files according to their real type (as reported by the
`file` command), ignoring file names and extensions. Files are unpacked into
their own folder; existing files are overwritten. Uncompressed files are
left untouched.

Supported: gzip, bzip2, zip, compress (.Z)

Options:
  -h    show this help and exit
  -r    recursive: traverse folders and unpack every archive inside them
  -v    verbose: print each file decompressed, warn on each file that was not

If an argument is a directory, every file in it is processed (and, with -r,
every file in every sub-directory).

Output: the number of archives decompressed.
Exit status: the number of files that were NOT decompressed.

Functions in this script:
  help              print this notice
  detect_type       map a file to its unpack handler using `file`
  extract_file      unpack a single file and update the counters
  process_directory find the files inside a directory and extract each
  main              parse options and run over all arguments
EOF
}

detect_type() {
    local desc key
    desc=$(file -b -- "$1" 2>/dev/null) || return 1
    for key in "${!UNPACKERS[@]}"; do
        if [[ $desc == *"$key"* ]]; then
            echo "${UNPACKERS[$key]}"
            return 0
        fi
    done
    return 1
}

extract_file()

process_directory() {
    local dir=$1 depth=() f files=()
    (( RECURSIVE )) || depth=(-maxdepth 1)

    mapfile -d '' -t files < <(find "$dir" "${depth[@]}" -type f -print0)
    for f in "${files[@]}"; do
        extract_file "$f"
    done
}

main() {

    if (( $# == 0 )); then
    echo "extract error: no files given" >&2
    help >&2
    exit 255
    fi

    for target in "$@"; do
        if [[ -d $target ]]; then
            process_directory "$target"
        elif [[ -f $target ]]; then
            extract_file "$target"
        else 
            NOT_DECOMPRESSED=$((NOT_DECOMPRESSED + 1))
            echo "Warning: $target does not exist or cannot be decompressed" >&2
        fi
    done

    echo "Decompressed $DECOMPRESSED archive(s)"
    exit $(( NOT_DECOMPRESSED > 255 ? 255 : NOT_DECOMPRESSED ))
}

main "$@"