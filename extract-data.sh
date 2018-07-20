#!/usr/bin/env bash

SCRIPT="extract-data.sh"
PROJECT_FILE=""
DONE_FILE="./tmp/extracted/done.txt"
RESET=false
SETUP=false

BOLD='\e[1m'
UNDER='\e[4m'
# reset to No Color
NC='\e[0m'

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

ctrl_c() {
        echo "** Received Ctrl-C or another break signal. Exiting."
        exit 1
}

print_help() {
    printf "\nHelp documentation for ${BOLD}$SCRIPT ${NC}\n\n"
	printf "The following command line options are recognized: ${BOLD}$SCRIPT ${NC} (-r|-i) -f file [-n N]\n"
	printf "\t ${BOLD}-i ${NC}\t  - ${UNDER}mutually exclusive${NC}, will setup temp folder, enabling the script to resume upon interrupts.\n"
	printf "\t ${BOLD}-r ${NC}\t  - ${UNDER}mutually exclusive${NC}, will reset temp folder, avoiding the script to resume upon interrupts.\n"
    printf "\t ${BOLD}-f file ${NC} - ${UNDER}mandatory${NC}, the path to the file with projects.\n"
    printf "\t ${BOLD}-n N ${NC} - ${UNDER}optional${NC}, the size of the chucks in which the file will be split.\n"
    printf "\t ${BOLD}-h ${NC}\t  - displays this help message.\n\n"
}

set_up() {
    mkdir -p ./tmp/extracted
    mkdir -p ./tmp/data/
    cp "$PROJECT_FILE" ./tmp/data
    cd tmp/data
    filename=$(basename "$PROJECT_FILE")
    #EXT="${filename##*.}"
    PREFIX="${filename%.*}"

    # splitting file into smaller ones of N lines
    SUFFIX_LEN=4
    if [ -z "$N" ]; then
        N=$(wc ../../github-api-tokens.txt)
        N=$(echo $N|cut -d' ' -f1)
    fi
    split -a "$SUFFIX_LEN" -l "$N" "$PROJECT_FILE" "$PREFIX"
    rm "$PROJECT_FILE"
    cd ../..
}

clean_up() {
    rm -rf ./tmp/extracted
    rm -rf ./tmp/data/
}

run() {
    echo "Extracting issues and comments from projects listed in $PROJECT_FILE"
    for file in tmp/data/"$PREFIX"*; do
        [ -e "$file" ] || continue
        echo "Analyzing file $file"
        filename=$(basename "$file")
        f="${filename%.*}"
        python szzExtractIssuesAndComments.py --from="$file" --issues=./tmp/extracted/"$f"_issues.csv --comments=./tmp/extracted/"$f"_comments.csv
        exit_code=$?
        if [ "$exit_code" -ne 0 ]; then
            echo "Error processing $f"
        else
            cat "$file" >> "$DONE_FILE"
            rm "$file"
            echo "Done processing $f"
        fi
    done
    echo "Done"
}


# parse args
while getopts "rif:n:h" FLAG; do
    case "$FLAG" in
        f ) PROJECT_FILE=$OPTARG;;
        n ) N=$OPTARG;;
        r ) RESET=true;;
        i ) SETUP=true;;
        h ) print_help;;
        \?) # unrecognized option - show help
            printf "INFO" "Run $SCRIPT -h to see the help documentation."
            exit 2;;
        : ) printf "ERROR" "Missing option argument for -$OPTARG"
            exit 2;;
        * ) printf "ERROR" "Unimplemented option: -$OPTARG"
            exit 2;;
        esac
done
shift $((OPTIND-1))  # This tells getopts to move on to the next argument.
### end getopts code ###

if [ "$RESET" = true ]; then
    clean_up
    echo "Reset complete"
    exit
elif [ "$SETUP" = true ]; then
    set_up
fi
run
