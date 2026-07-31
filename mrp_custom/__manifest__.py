# -*- coding: utf-8 -*-
{
    'name': 'MRP Custom',
    'version': '19.0.1.5.0',
    'category': 'Manufacturing',
    'summary': 'Create MOs from Delivery; QC Controls; Purchase RFQs from MO',
    'depends': [
        'mrp',
        'stock',
        'sale_stock',
        'purchase',
        'quality_mrp',
        'bom_custom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
