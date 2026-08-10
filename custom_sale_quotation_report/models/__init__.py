from . import sale_order
from . import sale_order_line
from . import account_move
from . import ir_actions_report

# NOTE: `business_unit` already exists on res.company in this instance
# (confirmed by the client) — this module does NOT redefine it, it only
# reads it in the report templates below. If it does not exist yet on a
# given database, add it via Studio or a one-line inherit before installing:
#
#   class ResCompany(models.Model):
#       _inherit = 'res.company'
#       business_unit = fields.Char(string="Business Unit")
