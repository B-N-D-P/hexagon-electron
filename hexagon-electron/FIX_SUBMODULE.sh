#!/bin/bash
# Properly remove submodule and add as regular directory

cd /mnt/storage/structural-repair-web

echo "Step 1: Remove the submodule entry from git index..."
git rm --cached hexagon-electron

echo "Step 2: Remove any .git directory inside hexagon-electron..."
rm -rf hexagon-electron/.git

echo "Step 3: Add hexagon-electron as regular files..."
git add hexagon-electron/

echo "Step 4: Check what's staged..."
git status | head -30

echo "Step 5: Commit the fix..."
git commit -m "Fix: Convert hexagon-electron from submodule to regular directory"

echo "Step 6: Push..."
ssh-add ~/.ssh/id_ed25519
git push origin main

echo "✅ Done! The build should work now."
echo "Check: https://github.com/B-N-D-P/hexagon-electron/actions"
