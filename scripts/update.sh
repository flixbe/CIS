#! /bin/bash

source ./scripts/assert.sh

rm -f .commit_hash

assert "Repository folder not found!" pushd $1 1> /dev/null
assert "Can't reset git" git reset --hard HEAD

COMMIT=$(assert "Can't call 'git log' on repository" git log -n1)
if [ $? != 0 ]; then
    echo "Can't call 'git log' on repository"
    exit 1
fi
HASH=`echo $COMMIT | awk '{ print $2}'`

assert "Can't pull from repository" git pull

COMMIT=$(assert "Can't call 'git log' on repository" git log -n1)
if [ $? != 0 ]; then
    echo "Can't call 'git log' on repository"
    exit 1
fi
NEW_HASH=`echo $COMMIT | awk '{ print $2 }'`

if [$NEW_COMMIT_ID != $HASH]; then
    popd 1> /dev/null
    echo $NEW_HASH > .commit_hash
fi