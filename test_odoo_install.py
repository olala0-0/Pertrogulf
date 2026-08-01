import os
import sys
import subprocess

def find_python():
    candidates = ['python3.12', 'python3.11', 'python3.10', '/home/parth.dave/v19/odoo/.venv/bin/python', 'python']
    for cand in candidates:
        try:
            result = subprocess.run([cand, "-c", "import sys; print(sys.version_info >= (3, 10))"], capture_output=True, text=True)
            if "True" in result.stdout:
                return cand
        except Exception:
            pass
    return sys.executable

python_exe = find_python()
print("Using Python executable:", python_exe)

odoo_path = "/home/parth.dave/v19/odoo/odoo-bin"
cmd = [
    python_exe, odoo_path,
    "-d", "test_migration_db",
    "-i", "helpdesk_mgmt,print_minutes_of_meeting,sale_order_enquiry,zilancer_customisation",
    "--addons-path=/home/parth.dave/v19/odoo/addons,/home/parth.dave/v19/custom_modules/test_project",
    "--stop-after-init",
    "--log-level=warn"
]

print("Running command:", " ".join(cmd))
result = subprocess.run(cmd, capture_output=True, text=True)

print("--- STDOUT ---")
print(result.stdout)
print("--- STDERR ---")
print(result.stderr)
print("Exit code:", result.returncode)

# Dump to file so we can view it nicely
with open("test_results.log", "w") as f:
    f.write(result.stdout + "\n" + result.stderr)

if result.returncode != 0:
    print("FAILED")
else:
    print("SUCCESS")
