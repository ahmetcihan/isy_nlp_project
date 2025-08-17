#!/bin/bash

git fetch origin

for branch in $(git branch -r | grep origin/ | grep -v 'HEAD' | sed 's|origin/||'); do
    echo ">>> $branch branch updating..."

    # create branch if not in the local
    if ! git show-ref --verify --quiet refs/heads/$branch; then
        git checkout -b $branch origin/$branch
    else
        git checkout $branch
        git pull origin $branch
    fi
done

# return to the old branch
git checkout main 2>/dev/null || git checkout master

