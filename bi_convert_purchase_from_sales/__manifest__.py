# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name' : "Convert Purchase from Sales Order",
    'version' : "19.0.0.0",
    'category' : "Purchases",
    'license': 'OPL-1',
    'summary': 'This apps helps to Covert Purchase order from Sales Order',
    'description' : """
        Convert Purchase from Sales Order
        Convert Purchases from Sales Order
        Convert Purchase order from Sales Order
        Convert Purchases order from Sales Order

        create Purchase from Sales Order
        create Purchases from Sales Order
        create Purchase order from Sales Order
        create Purchases order from Sales Order


        Add Purchase from Sales Order
        Add Purchases from Sales Order
        ADD Purchase order from Sales Order
        ADD Purchases order from Sales Order

    """,
    'author' : "BROWSEINFO",
    'website'  : "https://www.browseinfo.com/demo-request?app=bi_convert_purchase_from_sales&version=19&edition=Community",
    'depends'  : [ 'base','sale_management','purchase','stock'],
    'data'     : [  'security/ir.model.access.csv',
                    'wizard/purchase_order_wizard_view.xml',
                    'views/inherit_sale_order_view.xml',
            ],
    'assets': {
        'web_editor.wysiwyg_iframe_editor_assets': [
            'bi_convert_purchase_from_sales/static/src/css/custom.scss',
        ],
    },    
    'installable' : True,
    'application' :  False,
    "images":['static/description/Banner.gif'],
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_convert_purchase_from_sales&version=19&edition=Community',
}
