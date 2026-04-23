from datetime import datetime
from typing import Optional

class PipelineLogger:
    def __init__(self):
        self.logs = []
        self.steps = []
        self.token_usage = {
            "school_api": 0,
            "gemini": 0
        }

    def log_step(self, step: str, status: str, input_data: Optional[str] = None, output_data: Optional[str] = None):
        self.steps.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "step": step,
            "status": status,  # running / done / error
            "input": input_data[:500] if input_data else None,
            "output": output_data[:500] if output_data else None
        })

    def log_llm(self, model: str, prompt: str, response: str, tokens: int = 0):
        self.logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "model": model,
            "prompt": prompt[:300],
            "response": response[:300],
            "tokens": tokens
        })
        if "gpt" in model.lower():
            self.token_usage["school_api"] += tokens
        elif "gemini" in model.lower():
            self.token_usage["gemini"] += tokens

    def reset(self):
        self.logs = []
        self.steps = []
        self.token_usage = {"school_api": 0, "gemini": 0}

# 전역 로거 인스턴스
pipeline_logger = PipelineLogger()
