#!/usr/bin/env python3
"""Manage a local GitLab sandbox using Docker and the Python standard library."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import urllib.request


LOCAL = Path(__file__).resolve().parent
ROOT = LOCAL.parent.parent
STATE = LOCAL / ".state"
COMPOSE = ["docker", "compose", "-f", str(LOCAL / "compose.yml")]
URL = "http://localhost:8929"


def command(args, **kwargs):
    return subprocess.run(args, check=True, cwd=ROOT, text=True, **kwargs)


def api(path, data=None):
    settings = json.loads((STATE / "settings.json").read_text())
    request = urllib.request.Request(
        f"{URL}/api/v4/{path}",
        data=json.dumps(data).encode() if data is not None else None,
        headers={"PRIVATE-TOKEN": settings["token"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def setup():
    STATE.mkdir(mode=0o700, exist_ok=True)
    password = STATE / "root-password"
    if not password.exists():
        password.write_text(secrets.token_urlsafe(24) + "\n")
        password.chmod(0o600)
    command(COMPOSE + ["up", "-d", "--wait", "--wait-timeout", "900", "gitlab"])
    branch = command(["git", "branch", "--show-current"], capture_output=True).stdout.strip()
    if not branch:
        raise RuntimeError("Check out a branch before importing")
    bundle = STATE / "branch.bundle"
    command(["git", "bundle", "create", str(bundle), branch])
    command(COMPOSE + ["cp", str(bundle), "gitlab:/tmp/gravity.bundle"])
    command(COMPOSE + ["cp", str(LOCAL / "bootstrap.rb"), "gitlab:/tmp/gravity-bootstrap.rb"])
    command(COMPOSE + ["exec", "-T", "-e", f"VALIDATION_BRANCH={branch}", "gitlab",
                       "gitlab-rails", "runner", "/tmp/gravity-bootstrap.rb"])
    settings_path = STATE / "settings.json"
    command(COMPOSE + ["cp", "gitlab:/tmp/gravity-settings.json", str(settings_path)])
    settings_path.chmod(0o600)
    settings = json.loads(settings_path.read_text())
    runners = api(f"projects/{settings['project_id']}/runners")
    if not any(runner["description"] == "Local Docker validation" for runner in runners):
        runner = api("user/runners", {
            "runner_type": "project_type",
            "project_id": settings["project_id"],
            "description": "Local Docker validation",
            "run_untagged": True,
            "locked": True,
        })
        config = f'''concurrent = 1
check_interval = 3

[[runners]]
  name = "Local Docker validation"
  url = "http://gitlab:8929"
  clone_url = "http://gitlab:8929"
  token = {json.dumps(runner["token"])}
  executor = "docker"
  [runners.docker]
    image = "docker:29-cli@sha256:4d742ab934c2149b628bf26369ac3ec51cb91e2e28fe6722a0e86a6d6efc4bd5"
    network_mode = "budibase-gitlab-local"
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
'''
        command(COMPOSE + ["run", "--rm", "--no-deps", "-T", "--entrypoint", "sh", "runner",
                           "-c", "umask 077; cat > /etc/gitlab-runner/config.toml"], input=config)
    command(COMPOSE + ["--profile", "runner", "up", "-d", "runner"])
    print(f"GitLab: {URL}/root/budibase-gravity")
    print(f"Login: root; password file: {password}")


def run_pipeline():
    branch = command(["git", "branch", "--show-current"], capture_output=True).stdout.strip()
    script = '''
project = Project.find_by_full_path!("root/budibase-gravity")
result = Ci::CreatePipelineService.new(project, User.find_by_username!("root"), ref: ENV.fetch("VALIDATION_BRANCH")).execute(:web)
raise result.message unless result.success?
puts "Pipeline: http://localhost:8929/root/budibase-gravity/-/pipelines/#{result.payload.id}"
'''
    command(COMPOSE + ["exec", "-T", "-e", f"VALIDATION_BRANCH={branch}", "gitlab",
                       "gitlab-rails", "runner", script])


def status():
    settings = json.loads((STATE / "settings.json").read_text())
    project = settings["project_id"]
    pipelines = api(f"projects/{project}/pipelines?per_page=1")
    if not pipelines:
        print("No pipelines yet")
        return
    pipeline = pipelines[0]
    print(f"Pipeline {pipeline['id']}: {pipeline['status']} ({pipeline['web_url']})")
    for job in api(f"projects/{project}/pipelines/{pipeline['id']}/jobs"):
        print(f"  {job['name']}: {job['status']}")


if __name__ == "__main__":
    os.umask(0o077)
    actions = {"setup": setup, "run": run_pipeline, "status": status}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        sys.exit("Usage: python3 gitlab/local/manage.py {setup|run|status}")
    actions[sys.argv[1]]()
