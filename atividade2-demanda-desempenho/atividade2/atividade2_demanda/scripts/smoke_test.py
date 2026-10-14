"""Automated basic tests of all three backends, without external packages."""
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
for i, profile in enumerate(('cpu', 'memory', 'io')):
    port = 18700 + i
    proc = subprocess.Popen([sys.executable, str(ROOT/'apps'/'server.py'), '--profile', profile, '--port', str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for attempt in range(40):
            try:
                with urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as response:
                    health = json.load(response)
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError(f'{profile}: servidor não iniciou')
        assert health['profile'] == profile
        with urlopen(f'http://127.0.0.1:{port}/work?size={dict(cpu=1000,memory=1,io=64)[profile]}', timeout=10) as response:
            result = json.load(response)
            assert response.status == 200 and result['profile'] == profile
        print(f'OK: {profile} /health e /work')
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
print('Todos os testes básicos passaram.')
