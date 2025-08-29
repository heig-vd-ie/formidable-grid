import subprocess
from pathlib import Path

glm_file = Path("/opt/gridlabd/tools/IEEE Test Models/123node/IEEE-123.glm")

result = subprocess.run(
    ["docker", "exec", "-i", "gridlabd", "gridlabd", str(glm_file)],
    capture_output=True,
    text=True,
)

print("STDOUT:\n", result.stdout)
print("STDERR:\n", result.stderr)
