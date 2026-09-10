import base64
import io

from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def get_logo_on_background(self, hex_color='#d1d3d4'):
        """Logo flattened onto a solid background, as a data URI.

        Some wkhtmltopdf builds paint PNG alpha transparency as opaque white
        instead of compositing it, so a transparent logo shows with a white
        box around it on a colored background. Pre-flattening removes the
        alpha channel entirely so there is nothing left for the renderer to
        get wrong.

        Some logo files also have a genuinely opaque white background baked
        in (not real alpha transparency) - alpha-compositing alone can't fix
        those, so near-white pixels are also treated as transparent before
        compositing.
        """
        self.ensure_one()
        if not self.logo:
            return False
        from PIL import Image
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        img = Image.open(io.BytesIO(base64.b64decode(self.logo))).convert('RGBA')
        img.putdata([
            (pr, pg, pb, 0) if pr > 240 and pg > 240 and pb > 240 else (pr, pg, pb, pa)
            for pr, pg, pb, pa in img.getdata()
        ])
        background = Image.new('RGBA', img.size, (r, g, b, 255))
        flattened = Image.alpha_composite(background, img).convert('RGB')
        buf = io.BytesIO()
        flattened.save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
