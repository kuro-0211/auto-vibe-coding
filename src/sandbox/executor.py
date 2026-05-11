import os
import re
import docker
import yaml

def clean_code(code: str) -> str:
    """LLM이 생성한 코드에서 순수 Python 코드만 추출"""
    # 백틱 코드블록 제거
    code = re.sub(r"```python\s*", "", code)
    code = re.sub(r"```\s*", "", code)
    return code.strip()

def execute_code(code: str) -> dict:
    """Docker 샌드박스에서 코드 실행"""

    with open("config/sandbox.yaml") as f:
        config = yaml.safe_load(f)["sandbox"]

    # 코드 정제
    clean = clean_code(code)
    print(f"[샌드박스] 실행 코드:\n{clean}")

    client = docker.from_env()

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

        output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
        return {"success": True, "output": output, "error": None}

    except docker.errors.ContainerError as e:
        error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
        return {"success": False, "output": None, "error": error_msg}

    except Exception as e:
        print(f"샌드박스 에러: {str(e)}")
        return {"success": False, "output": None, "error": str(e)}
