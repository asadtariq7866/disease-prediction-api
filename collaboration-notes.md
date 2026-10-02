# Git Collaboration Notes

## 1. Branch
Created `feature/health-check` off `main`, added a `model_loaded` boolean
to the `/health` response, committed, and pushed the branch to GitHub.

## 2. Pull Request
Opened PR #1 (`feature/health-check` -> `main`) with a What / Why /
How-to-test description.

## 3. Code review
Added two review comments on my own PR:
- An improvement: the `model_loaded` check only confirms the key exists
  in the dict, not that it's non-None.
- A positive: `/health` stays cheap (no prediction call), so monitoring
  can hit it frequently.

## 4. Merge conflict
Created a deliberate conflict on `notes.txt`: `main` and a
`feature/new-title` branch both changed the same `title:` line to
different values. Git couldn't decide which to keep, so it marked the
file with `<<<<<<< HEAD` (main's version), `=======` (divider), and
`>>>>>>> feature/new-title` (incoming version). I resolved it by
deleting the markers and combining both into `title: Team Awesome Notes`,
then ran `git add notes.txt` and `git commit` to finish the merge.

## 5. Sync branch with main
Pushed `main` (with the conflict-resolution merge commit), then checked
out `feature/health-check`, ran `git merge main` to bring the latest
`main` into it (no conflict this time, since `notes.txt` didn't exist on
that branch), and pushed the branch again.

## 6. Merge the PR
Merged PR #1 into `main` on GitHub and deleted the `feature/health-check`
branch.