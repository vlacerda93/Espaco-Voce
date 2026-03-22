import time
from collections import defaultdict
from typing import Dict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.history: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Limpa o histórico com mais de 60 segundos
        self.history[client_ip] = [t for t in self.history[client_ip] if now - t < 60]
        
        if len(self.history[client_ip]) < self.requests_per_minute:
            self.history[client_ip].append(now)
            return True
        return False

limiter = RateLimiter(requests_per_minute=20) # 20 reqs/min para IA
