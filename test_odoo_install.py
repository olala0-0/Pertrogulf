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
    "-d", "test_migration_db_v19",
    "-i", "base_multi_company,partner_multi_company,product_multi_company,company_structure,division_company_structure,helpdesk_mgmt,print_minutes_of_meeting,sale_order_enquiry,zilancer_customisation,bom_custom,mrp_custom,mrp_approval_flow,stock_no_negative,custom_list_view,custom_sale_quotation_report,employee_purchase_requisition,hide_menu_user,mst_advanced_login_history,zilancer_reports,web_chatter_position_cr,bi_convert_purchase_from_sales",
    "--addons-path=/home/parth.dave/v19/odoo/addons,/home/parth.dave/v19/odoo_enterprise,/home/parth.dave/v19/custom_modules/Pertrogulf",
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
