# budibase-gravity

This repository is a fork that automatically merges updates from [Budibase/budibase](https://github.com/Budibase/budibase).

The [`master`](https://github.com/Budibase/budibase-gravity/tree/master) branch includes upstream `master` and preserves commits added directly to Gravity, including commits absent from the open source repository. Only this upstream branch is synchronized; tags and other upstream branches are not synchronized. Updates fast-forward when possible and otherwise create a merge commit retaining both histories. If upstream is already an ancestor of Gravity's `master`, synchronization makes no changes.

The default branch, `mirror-sync`, contains only synchronization administration. GitHub requires scheduled workflows to exist on the default branch.

The [Mirror upstream master](https://github.com/Budibase/budibase-gravity/actions/workflows/sync-master.yml) workflow checks upstream every five minutes and can also be run manually. GitHub Actions schedules are best effort and may be delayed. The workflow uses a repository-scoped write-enabled SSH deploy key, stored as the `MIRROR_SSH_KEY` Actions secret, to sync commits including workflow changes. GitHub’s built-in Actions token cannot update workflow files. The built-in `GITHUB_TOKEN` with `contents: write` reads the mirrored ref and writes the daily health check. No personal token or external service is required. GitHub’s SSH host key is pinned in the workflow.

Inherited push workflows for CI, QA deployment, automerge, and cloud branch syncing are disabled in this fork. Review any new upstream workflow triggers when upstream adds workflows.

The workflow records a daily health check on `mirror-sync` to prevent GitHub's automatic disabling of scheduled workflows after 60 days without repository activity. Workflow failures are visible in the Actions tab.

Synchronization never force-pushes, rebases, or resets Gravity's `master`. Merge conflicts and unrelated histories fail without changing the remote branch and require manual resolution. A concurrent update to Gravity's `master` that would be overwritten causes the push to fail; the next run fetches the new head and retries. Successful updates verify that both the previous Gravity head and the fetched upstream head remain ancestors of the resulting branch. Upstream history rewrites are merged only when Git can reconcile the histories normally; they never replace Gravity's history.

Do not change the default branch to `master`: that would stop this scheduler. To clone the mirrored code, select the branch explicitly:

```sh
gh repo clone Budibase/budibase-gravity -- --branch master --single-branch
```
