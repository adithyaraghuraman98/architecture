#!/usr/bin/env bash

SCRIPT="prolific-project.sh"
PROLIFIC_FILE=""
CONF_LEVEL=.95
SEED=895
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
	printf "The following command line options are recognized: ${BOLD}$SCRIPT ${NC} (-r) -i file [-c (.95|.99) -s SEED]\n"
	printf "\t ${BOLD}-r ${NC}\t  - ${UNDER}mutually exclusive${NC}, will reset temp folder, avoiding the script to resume upon interrupts.\n"
    printf "\t ${BOLD}-i file ${NC} - ${UNDER}mandatory${NC}, the path to the file with the list of prolific developers.\n"
    printf "\t ${BOLD}-c conf ${NC} - ${UNDER}optional${NC}, confidence interval, either .95 (default) or .99.\n"
    printf "\t ${BOLD}-s seed ${NC} - ${UNDER}optional${NC}, the seed number to subsample the set of prolific developers (default 895).\n"
    printf "\t ${BOLD}-h ${NC}\t  - displays this help message.\n\n"
}

set_up() {
    # set up
    mkdir -p ./tmp/prolific
    mkdir -p ./tmp/prolific_out
}

reset() {
    # clean up
    rm -rf ./tmp/prolific
    rm -rf ./tmp/prolific_out
    rm -f ./tmp/prolific_done.txt
}

chunks() {
    echo "$PROLIFIC_FILE"
    python parse_prolifics.py --in="$PROLIFIC_FILE" --random --conflev="$CONF_LEVEL" --seed="$SEED"
    exit_code=$?
    if [ "$exit_code" -ne 0 ]; then
        exit
    else
        PROLIFIC_SUBSAMPLE_FILE="prolifics-${SEED}.txt"

        cp "$PROLIFIC_SUBSAMPLE_FILE" ./tmp/prolific
        cd tmp/prolific
        filename=$(basename "$PROLIFIC_SUBSAMPLE_FILE")
        #EXT="${filename##*.}"
        PREFIX="${filename%.*}"

        # splitting file into smaller ones of N lines
        SUFFIX_LEN=4
        N=$(wc ../../github-api-tokens.txt)
        N=$(echo $N|cut -d' ' -f1)
        split -a "$SUFFIX_LEN" -l "$N" "$PROLIFIC_SUBSAMPLE_FILE" "$PREFIX"
        rm "$PROLIFIC_SUBSAMPLE_FILE"
        cd ../..
    fi
}

run() {
    echo "Retrieving repositories for developers listed in $PROLIFIC_FILE"
    chunks
    for file in tmp/prolific/"$PREFIX"*; do
        [ -e "$file" ] || continue
        echo "Retrieving repositories for prolific devs in file $file"
        filename=$(basename "$file")
        f="${filename%.*}"
        python parse_prolifics.py --in="$file" --out="tmp/prolific_out/"${f}"_project-list.txt" --conflev="$CONF_LEVEL" --seed="$SEED"
        exit_code=$?
        if [ "$exit_code" -ne 0 ]; then
            echo "Error processing $f"
        else
            echo "$f" >> tmp/prolific_done.txt
            rm "$file"
            echo "Done processing $f"
        fi
    done
    concat
}

concat() {
    rm -f "projects-${SEED}.txt"
    cat tmp/prolific_out/*.txt >> temp_sort.txt
    # sort and remove duplicates
    sort -u temp_sort.txt > "projects-${SEED}.txt"
    rm -f temp_sort.txt
}

# parse args
while getopts "ri:c:s:h" FLAG; do
    case "$FLAG" in
        i ) PROLIFIC_FILE=$OPTARG;;
        c ) CONF_LEVEL=$OPTARG;;
        s ) SEED=$OPTARG;;
        r ) RESET=true;;
        h ) print_help;;
        \?) #unrecognized option - show help
            printf "INFO" "Run $SCRIPT -h to see the help documentation."
            exit 2;;
        : ) printf "ERROR" "Missing option argument for -$OPTARG"
            exit 2;;
        * ) printf "ERROR" "Unimplemented option: -$OPTARG"
            exit 2;;
        esac
done
shift $((OPTIND-1))  #This tells getopts to move on to the next argument.
### end getopts code ###

if [ "$RESET" = true ]; then
    reset
    echo "Reset complete"
    exit
else
    echo "Generating a sample of projects from prolific devs"
    set_up
    run
    echo "Done"
fi
