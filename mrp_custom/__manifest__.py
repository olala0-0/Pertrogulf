# -*- coding: utf-8 -*-
{
    'name': 'MRP Custom',
    'version': '19.0.1.3.0',
    'category': 'Manufacturing',
    'summary': 'Create MOs and Purchase RFQs from Delivery Orders with BOM dependencies',
    'depends': [
        'mrp',
        'stock',
        'sale_stock',
        'purchase',
        'quality_mrp',
    ],
    'data': [
        'views/stock_picking_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
