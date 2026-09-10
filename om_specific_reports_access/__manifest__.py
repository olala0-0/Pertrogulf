# -*- coding: utf-8 -*-
{
    "name": "Hide Specific Print Reports Per User",
    "version": "19.0.1.0.0",
    "summary": "Hide specific print reports per user basis",
    "category": "Tools",
    "author": "OdooMatrix",
    "company": "OdooMatrix",
    "maintainer": "OdooMatrix",
    "license": "LGPL-3",
    "website": "https://www.odoomatrix.com",
    "support": "dev.odoomatrix@gmail.com",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users_views.xml",
    ],
    "description": """
Hide Specific Print Reports Per User
=====================================

Hide specific print reports per user basis. Select exactly which reports to hide.

Key Features:
-------------
* Hide specific print reports (not all reports for a model)
* Per user granular control over specific reports
* Select model first, then choose which reports to hide
* Works independently of group permissions
* Easy configuration through user form

Contact:
--------
* Email: dev.odoomatrix@gmail.com
    """,
    "images": [
        "static/description/banner.png"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}