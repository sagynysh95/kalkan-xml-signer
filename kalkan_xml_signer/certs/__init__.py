import subprocess
import sys
from pathlib import Path


CERTS_DIR = Path(__file__).parent


def install_certs():
    """
    Установка корневых сертификатов PKI Казахстана в систему.
    Требует sudo.
    """
    script = CERTS_DIR / "install_certs.sh"
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(result.stdout)
