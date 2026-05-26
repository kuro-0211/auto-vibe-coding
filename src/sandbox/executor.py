import os
import re
import docker
import yaml
import time

def clean_code(code: str) -> str:
    code = re.sub(r"```[\w]*\n?", "", code)
    code = re.sub(r"```", "", code)
    code = code.strip()
    return code

def execute_code(code: str) -> dict:
    # Resolve sandbox.yaml relative to project root, not CWD (which differs
    # between Streamlit/Reflex/CLI launchers). `executor.py` lives at
    # `<root>/src/sandbox/executor.py`, so go up two levels.
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(_here))
    _cfg_path = os.path.join(_root, "config", "sandbox.yaml")
    if not os.path.exists(_cfg_path):
        # fallback: original CWD-relative path (in case someone overrides root)
        _cfg_path = "config/sandbox.yaml"
    with open(_cfg_path) as f:
        config = yaml.safe_load(f)["sandbox"]

    clean = clean_code(code)
    print(f"[샌드박스] 실행 코드:\n{clean[:200]}")

    client = docker.from_env()
    start_time = time.time()

    try:
        container = client.containers.run(
            image=config["image"],
            command=["python", "-c", clean],
            mem_limit=config["memory_limit"],
            nano_cpus=int(float(config["cpu_limit"]) * 1e9),
            network_mode=config["network"],
            remove=True,
            detach=False,
            stdout=True,
            stderr=True
        )

        elapsed = round(time.time() - start_time, 2)
        output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
        output = output.strip()

        return {
            "success": True,
            "output": output,
            "error": None,
            "elapsed": elapsed,
            "lines": len(output.splitlines())
        }

    except docker.errors.ContainerError as e:
        elapsed = round(time.time() - start_time, 2)
        error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
        return {
            "success": False,
            "output": None,
            "error": error_msg,
            "elapsed": elapsed,
            "lines": 0
        }

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        print(f"샌드박스 에러: {str(e)}")
        return {
            "success": False,
            "output": None,
            "error": str(e),
            "elapsed": elapsed,
            "lines": 0
        }