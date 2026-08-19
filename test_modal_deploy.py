import subprocess
import sys

# Force UTF-8 encoding
sys.stdout.encoding = 'utf-8'
sys.stderr.encoding = 'utf-8'

result = subprocess.run(
    ['modal', 'deploy', 'modal_app.py'],
    capture_output=True,
    text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr[:1000] if result.stderr else "none")
print("Return code:", result.returncode)