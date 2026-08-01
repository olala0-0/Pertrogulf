# -*- coding: utf-8 -*-
{
    'name': 'BOM Custom (Production Blend Sheet)',
    'version': '19.0.1.2.0',
    'category': 'Manufacturing',
    'summary': 'Production Blend Sheet, encrypted names, QC Controls on BoM',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom_views.xml',
        'views/product_encrypted_name_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
