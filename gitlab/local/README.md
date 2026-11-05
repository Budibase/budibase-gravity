# Local GitLab pipeline validation

Requires Docker Compose, Git, Python 3, and enough Docker memory for GitLab and
the compatibility build. GitLab and Runner images are pinned to multi-platform
digests. The runner executes one job at a time with Docker CLI and Buildx.

From the repository root:

```sh
python3 gitlab/local/manage.py setup
python3 gitlab/local/manage.py run
python3 gitlab/local/manage.py status
```

Setup starts GitLab, waits for readiness, imports the current committed branch
through a Git bundle, and creates a project runner. It does not create commits,
stage files, change remotes, or push to GitHub. Run setup again to import newer
commits. Uncommitted working tree edits are not imported.

Open <http://localhost:8929/root/budibase-gravity>. Log in as `root` with the
password in `gitlab/local/.state/root-password`. Pipelines, job logs, and image
metadata artifacts are available in the GitLab UI. You can also start a pipeline
using **Build > Pipelines > New pipeline** and selecting the imported branch.

The pipeline only permits the `web` source. The `run` command uses GitLab's
pipeline service with that source; the ordinary pipelines REST endpoint uses
`api` and is intentionally excluded by the branch's workflow rules.

The runner uses the host Docker socket for the existing Docker/Buildx jobs.
Use this sandbox for trusted local jobs. Gravity registry access and AMD64
container execution are required by the existing pipeline. On ARM64 hosts,
Docker must support AMD64 emulation for the compatibility build.

Credentials and the import bundle stay under the ignored `.state/` directory.
The local API token expires after 30 days; rerun setup to refresh it. GitLab data
and runner configuration persist in dedicated Docker volumes.

Stop or restart the sandbox without deleting its data:

```sh
docker compose -f gitlab/local/compose.yml --profile runner stop
docker compose -f gitlab/local/compose.yml --profile runner up -d
```

Inspect service logs:

```sh
docker compose -f gitlab/local/compose.yml logs --tail 100 gitlab runner
```
