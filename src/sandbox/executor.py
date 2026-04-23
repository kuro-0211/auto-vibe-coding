import os
import docker
import tempfile
import yaml

def execute_code(code: str) -> dict:
    """Docker 샌드박스에서 코드 실행"""

    with open("config/sandbox.yaml") as f:
        config = yaml.safe_load(f)["sandbox"]

    client = docker.from_env()

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        dir="/tmp"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        container = client.containers.run(
            image=config["image"],
            command=f"python /code/{os.path.basename(tmp_path)}",
            volumes={
                "/tmp": {"bind": "/code", "mode": "ro"}
            },
            mem_limit=config["memory_limit"],
            nano_cpus=int(float(config["cpu_limit"]) * 1e9),
            network_mode=config["network"],
            remove=True,
            detach=False,
            stdout=True,
            stderr=True
        )

        output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
        return {"success": True, "output": output, "error": None}

    except docker.errors.ContainerError as e:
        error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
        return {"success": False, "output": None, "error": error_msg}

    except Exception as e:
        print(f"샌드박스 에러: {str(e)}")
        return {"success": False, "output": None, "error": str(e)}

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
