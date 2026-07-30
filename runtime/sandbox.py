import subprocess
from pathlib import Path
from typing import Dict, Any

class ExecutionResult:
    def __init__(self, exit_code: int, stdout: str, stderr: str):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

class Sandbox:
    def run_command(self, cmd: str, cwd: Path, env: Dict[str, str] = None) -> ExecutionResult:
        pass

class SubprocessSandbox(Sandbox):
    def run_command(self, cmd: str, cwd: Path, env: Dict[str, str] = None) -> ExecutionResult:
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                env=env,
                timeout=120
            )
            return ExecutionResult(res.returncode, res.stdout, res.stderr)
        except Exception as e:
            return ExecutionResult(1, "", str(e))

class DockerSandbox(Sandbox):
    def __init__(self, image: str = "python:3.12-slim"):
        self.image = image
        self.fallback = SubprocessSandbox()

    def run_command(self, cmd: str, cwd: Path, env: Dict[str, str] = None) -> ExecutionResult:
        try:
            import docker
            client = docker.from_env()
            client.ping()
            container = client.containers.run(
                self.image,
                command=f"bash -c '{cmd}'",
                volumes={str(cwd.resolve()): {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                detach=False,
                remove=True
            )
            return ExecutionResult(0, container.decode("utf-8"), "")
        except Exception:
            return self.fallback.run_command(cmd, cwd, env)
