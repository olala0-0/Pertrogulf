from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    business_unit = fields.Selection(
        [
            ("pg_marine", "PG-Marine"),
            ("pg_auto", "PG-Auto"),
            ("pg_powerx", "PG-PowerX"),
            ("pg_aviation", "PG-Aviation"),
            ("pg_tblnd", "PG-Toll Blending"),
            ("pg_sing", "PG-SING"),
            ("pg_greece", "PG-GREECE"),
            ("pg_golden", "PG-GOLDEN"),
            ("pg_fujairah", "PG-FUJAIRAH"),
            ("pg_ajman", "PG-AJMAN"),
        ],
        string="Business Unit",
    )
