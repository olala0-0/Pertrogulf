{
    'name': 'Purchase Order Report - Petro Gulf Ajman',
    'version': '19.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Petro Gulf Ajman-branded Purchase Order, Despatch Note and GRN PDF layouts',
    'description': """
        Adds "Print" options on Purchase Orders and stock pickings that
        render the Petro Gulf letterhead layouts: Purchase Order
        (Supplier box, PO Details box, line items, Amount in Words,
        signatory footer), Delivery Note (sale deliveries), and Goods
        Receipt Note (incoming receipts).

        Despatch Note (sale deliveries) uses the same letterhead but
        pulls company name/logo/address dynamically, so it is available
        for any company with no scope restriction - avoids one dropdown
        entry per business unit.

        Also adds an RFQ (Request for Quotation) layout for Purchase
        Orders, using the same letterhead but available for any company,
        with no scope restriction.

        Also adds a Blend Sheet layout for Bills of Materials / Production
        Blend Sheets, using the same letterhead and pulling the Ketal No,
        Previous Product, Flushing, Batch/Lot No, Density and component
        formulation (percentage / qty kg / qty ltr / density) fields
        already defined by bom_custom - available for any company, with
        no scope restriction.
    """,
    'depends': ['purchase', 'purchase_stock', 'stock', 'zilancer_customisation', 'mrp', 'bom_custom'],
    'data': [
        'views/purchase_order_views.xml',
        'report/report_actions.xml',
        'report/purchase_order_ajman_report.xml',
        'report/despatch_note_report_actions.xml',
        'report/despatch_note_report.xml',
        'report/delivery_note_report_actions.xml',
        'report/delivery_note_ajman_report.xml',
        'report/grn_report_actions.xml',
        'report/grn_ajman_report.xml',
        'report/rfq_report_actions.xml',
        'report/rfq_report.xml',
        'report/blend_sheet_report_actions.xml',
        'report/blend_sheet_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}