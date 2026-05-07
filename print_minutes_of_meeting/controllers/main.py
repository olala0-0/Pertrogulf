import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class BinaryFileDownloadController(http.Controller):

    @http.route(['/binary_download/<int:record_id>'], type='http', auth="user")
    def binary_file_download(self, record_id):
        record = request.env['meeting.actions'].sudo().browse(record_id)
        if not record or not record.attachment_data:
            return request.not_found()

        filename = record.attachment_name or 'downloaded_file'
        filedata = record.attachment_data
        return request.make_response(
            base64.b64decode(filedata),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
