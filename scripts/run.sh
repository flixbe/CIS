#!/bin/bash
REPOSITORY=$1
COMMIT=$2

source ./scripts/assert.sh

assert "Repository folder not found" pushd "$REPOSITORY" 1> /dev/null
assert "Can't clear repository" git clean -d -f -x
assert "Can't call git pull" git pull
assert "Can't update to given commit hash" git reset --hard "$COMMIT"