# budibase-gravity

This repository is a fork and automatic mirror of [Budibase/budibase](https://github.com/Budibase/budibase).

The [`master`](https://github.com/Budibase/budibase-gravity/tree/master) branch mirrors upstream `master` exactly, including its commit history. Only this upstream branch is synchronized; tags and other upstream branches are not synchronized. Changes made directly to this fork's `master` will be overwritten on the next sync, including divergent commits and upstream force updates.

The default branch, `mirror-sync`, contains only mirror administration. Keeping the scheduler here allows `master` to remain an exact mirror. GitHub requires scheduled workflows to exist on the default branch.

The [Mirror upstream master](https://github.com/Budibase/budibase-gravity/actions/workflows/sync-master.yml) workflow checks upstream every five minutes and can also be run manually. GitHub Actions schedules are best effort and may be delayed. The workflow uses a repository-scoped write-enabled SSH deploy key, stored as the `MIRROR_SSH_KEY` Actions secret, to sync commits including workflow changes. GitHub’s built-in Actions token cannot update workflow files. The built-in `GITHUB_TOKEN` with `contents: write` reads the mirrored ref and writes the daily health check. No personal token or external service is required. GitHub’s SSH host key is pinned in the workflow.

Inherited push workflows for CI, QA deployment, automerge, and cloud branch syncing are disabled in this fork. Review any new upstream workflow triggers when upstream adds workflows.

The workflow records a daily health check on `mirror-sync` to prevent GitHub's automatic disabling of scheduled workflows after 60 days without repository activity. Workflow failures are visible in the Actions tab.

Do not change the default branch to `master`: that would stop this scheduler. To clone the mirrored code, select the branch explicitly:

```sh
gh repo clone Budibase/budibase-gravity -- --branch master --single-branch
```
