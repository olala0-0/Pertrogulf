# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2024 (https://www.bistasolutions.com)
#
##############################################################################

import base64
import io

from odoo import models, fields, api
from odoo.addons.sale_order_enquiry.business_unit_data import BUSINESS_UNIT_SELECTION


class ResCompany(models.Model):
    _inherit = 'res.company'

    business_unit = fields.Selection(
        BUSINESS_UNIT_SELECTION,
        string="Business Unit",
        required=False,
    )
    aviation_logo = fields.Binary(string="PG Aviation Logo")

    def get_logo_on_background(self, hex_color='#d1d3d4'):
        """Logo flattened onto a solid background, as a data URI.

        Some wkhtmltopdf builds paint PNG alpha transparency as opaque white
        instead of compositing it, so a transparent logo shows with a white
        box around it on a colored background. Pre-flattening removes the
        alpha channel entirely so there is nothing left for the renderer to
        get wrong.
        """
        self.ensure_one()
        if not self.logo:
            return False
        from PIL import Image
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        img = Image.open(io.BytesIO(base64.b64decode(self.logo))).convert('RGBA')
        background = Image.new('RGBA', img.size, (r, g, b, 255))
        flattened = Image.alpha_composite(background, img).convert('RGB')
        buf = io.BytesIO()
        flattened.save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
