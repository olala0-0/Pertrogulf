# -*- coding: utf-8 -*-
{
    'name': 'MRP Approval Flow',
    'version': '19.0.1.4.0',
    'category': 'Manufacturing',
    'summary': 'MO dual approval before Confirm: QC then Store In-ward',
    'description': """
MRP Approval Flow
=================
Manufacturing Orders require sequential approval before Confirm / start:

1. **QC Approval** — approved by QC users
2. **Store Approval** — approved by Store In-ward users
3. **Both** — implies QC + Store (can perform both approvals)

Confirm is allowed only after both approvals. One statusbar shows the full flow.
    """,
    'author': 'Zilancer',
    'license': 'LGPL-3',
    'depends': [
        'mrp',
    ],
    'data': [
        'security/mrp_approval_security.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
