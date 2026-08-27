# -*- coding: utf-8 -*-
##############################################################################
#
#    ERP Artists
#    Copyright (C) 2025-TODAY ERP Artists (<https://www.erpartists.com>).
#    Author: ERP Artists (<https://www.erpartists.com>)
#
##############################################################################
{
    "name": "Save & Discard Buttons",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Save & Discard Buttons",
    "description": """
Save & Discard Buttons
======================

This module adds convenient **Save** and **Discard** buttons to Odoo form
views when creating or editing records.

Key Features
------------
* Adds a clearly visible **Save** button for saving record changes.
* Adds a **Discard** button for cancelling unsaved changes.
* Improves the usability of form views by providing easily accessible actions.
* Works with the standard Odoo web backend.
* Provides a simple and lightweight interface enhancement.""",
    "author": "ERP Artists",
    "website": "https://www.erpartists.com",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "ea_web_save_discard_button/static/src/xml/template.xml",
        ],
    },
    "images": ["static/description/banner.png", ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "price": 0.00,
    "currency": "USD",
}
