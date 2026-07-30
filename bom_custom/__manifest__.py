# -*- coding: utf-8 -*-
{
    'name': 'BOM Custom (Production Blend Sheet)',
    'version': '19.0.1.1.0',
    'category': 'Manufacturing',
    'summary': 'Production Blend Sheet fields, encrypted component names on BoM',
    'depends': ['mrp'],
    'data': [
        'views/mrp_bom_views.xml',
        'views/product_encrypted_name_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
