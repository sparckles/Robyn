#!/bin/sh

# Benchmark script to get info about Robyn's performances
# You can use this benchmark when developping on Robyn to test if your changes had a huge
# impact on performances. You cannot compare benchmarks from different machine and even
# several runs on the same machine can give very different results sometimes.
# Be aware of this when using this script!

Help() {
    echo "Benchmark script to get info about Robyn's performances."
    echo
    echo "USAGE:"
    echo "    benchmark [-h|m|n|y]"
    echo
    echo "OPTIONS:"
    echo "    -h              Print this help."
    echo "    -m              Run 'maturin develop' to compile the Rust part of Robyn."
    echo "    -n <number>     Set the number of requests that oha sends."
    echo "    -y              Skip prompt"
    exit 0
}

yes_flag=false
run_maturin=false
number=100000
while getopts hymn: opt; do
    case $opt in
        h)
            Help
            ;;
        y)
            yes_flag=true
            ;;
        m)
            run_maturin=true
            ;;
        n)
            number=$OPTARG
            ;;
        ?)
            echo 'Error in command line parsing' >&2
            Help
            exit 1
            ;;
    esac
done

# Prompt user to check if he installed the requirements for running the benchmark
if [ "$yes_flag" = false ]; then
    echo "Make sure you are running this in your venv and you installed 'oha' using 'cargo install oha'"
    echo "Do you want to proceed?"
    while true; do
        read -p "" yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
fi


# Compile Rust
if $run_maturin; then
    maturin develop
fi

# Run the server in the background
python3 ./integration_tests/base_routes.py &
sleep 1

# oha will display benchmark results
oha -n "$number" http://localhost:8080/sync

# Kill subprocesses after exiting the script (python + robyn server)
# (see https://stackoverflow.com/questions/360201/how-do-i-kill-background-processes-jobs-when-my-shell-script-exits)
trap "trap - TERM && kill 0" INT TERM EXIT
