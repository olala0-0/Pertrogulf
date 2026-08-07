{
    'name': 'Purchase Order Report - Petro Gulf Ajman',
    'version': '19.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Petro Gulf Ajman-branded Purchase Order and Despatch Note PDF layouts',
    'description': """
        Adds a second "Print" option on Purchase Orders that renders the
        Petro Gulf Ajman letterhead layout (Supplier box, PO Details box,
        line items table, Amount in Words, signatory footer), and a
        similar Despatch Note print option on stock pickings.

        Both are only available for records whose company is Petro Gulf
        Ajman (business_unit = 'pg_ajman') or one of its direct branch
        companies - printing them for any other company raises an error
        instead of generating the PDF.
    """,
    'depends': ['purchase', 'stock', 'zilancer_customisation'],
    'data': [
        'report/report_actions.xml',
        'report/purchase_order_ajman_report.xml',
        'report/despatch_note_report_actions.xml',
        'report/despatch_note_ajman_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}