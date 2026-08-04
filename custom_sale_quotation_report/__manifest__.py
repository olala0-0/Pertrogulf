{
    'name': 'Custom Sale Quotation Report by Business Unit',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Quotation PDF report layout varies by company business_unit',
    'description': """
        Renders a different quotation table/content layout depending on the
        sale order's company business_unit field, while keeping Odoo's
        native Document Layout (logo, colors, watermark) untouched.

        Business units covered:
        - Power X
        - Petrogulf Automotive
        - Petrogulf Aviation
        - Petrogulf Toll Blending (standard)
        - Petrogulf Toll Blending (ADNOC)
    """,
    'depends': ['sale', 'sale_management', 'stock'],
    'data': [
        'report/report_actions.xml',
        'report/sale_report_main.xml',
        'report/template_power_x.xml',
        'report/template_petrogulf_automotive.xml',
        'report/template_petrogulf_aviation.xml',
        'report/template_toll_blending.xml',
        'report/template_petrogulf_marine.xml',
        'report/template_pgm_lube_eu.xml',
        'report/template_pgm_singapore.xml',
        'report/template_golden.xml',
        'report/template_delivery_note_power_x.xml',
        'report/header_labels.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
