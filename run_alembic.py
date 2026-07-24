
import os
import subprocess
import sys

# Change to the backend directory
os.chdir("backend")

# Path to the python executable in the venv
python_executable = os.path.join("venv", "Scripts", "python.exe")

# Command to run alembic heads
command = [python_executable, "-m", "alembic", "heads"]

# Execute the command
result = subprocess.run(command, capture_output=True, text=True)

# Print the output
print(result.stdout)
print(result.stderr)

# Exit with the same code as the subprocess
sys.exit(result.returncode)
