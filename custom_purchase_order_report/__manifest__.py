{
    'name': 'Purchase Order Report - Petro Gulf Ajman',
    'version': '19.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Petro Gulf Ajman-branded Purchase Order, Despatch Note and GRN PDF layouts',
    'description': """
        Adds "Print" options on Purchase Orders and stock pickings that
        render the Petro Gulf Ajman letterhead layouts: Purchase Order
        (Supplier box, PO Details box, line items, Amount in Words,
        signatory footer), Despatch Note (sale deliveries), and Goods
        Receipt Note (incoming receipts).

        All are only available for records whose company is Petro Gulf
        Ajman (business_unit = 'pg_ajman') or one of its direct branch
        companies - printing them for any other company/document type
        raises an error instead of generating the PDF.
    """,
    'depends': ['purchase', 'purchase_stock', 'stock', 'zilancer_customisation'],
    'data': [
        'views/purchase_order_views.xml',
        'report/report_actions.xml',
        'report/purchase_order_ajman_report.xml',
        'report/despatch_note_report_actions.xml',
        'report/despatch_note_ajman_report.xml',
        'report/grn_report_actions.xml',
        'report/grn_ajman_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}