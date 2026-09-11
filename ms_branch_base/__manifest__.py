{
    "name": "Branch Dimension: Base",
    "summary": "Branch dimension base: the list of branches, the branch field other modules add to their documents, and the per branch access rights",
    "description": """
        A branch is not an app. It is a dimension that several apps have to
        agree on - sales, purchase, accounting, inventory, helpdesk,
        subscriptions - and the moment each app keeps its own list, the same
        shop exists three times under three different names and nothing can be
        reported across them.

        This module holds the branch and nothing else: the list, the field
        other modules reuse, who may see which branch, and the default a new
        document picks up. Install the module for the app you actually run and
        it will use this one.

        IT CHANGES NOTHING ON ITS OWN. The two branch groups are opt-in; until
        somebody is put in them, everybody keeps seeing everything - which is
        what you want on a database that already has three years of documents
        in it.
    """,
    "author": "Miftahussalam",
    "website": "https://blog.miftahussalam.com/",
    "category": "Technical",
    "version": "19.0.1.2.0",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/ms_branch_base_groups.xml",
        "security/ir.model.access.csv",
        "security/ms_branch_base_rules.xml",
        "views/ms_branch_views.xml",
        "views/res_users_views.xml",
        "views/ms_branch_menus.xml",
    ],
    "demo": [

    ],
    "images": [
        "static/description/images/main_screenshot.png",
    ],
    "license": "OPL-1",
    "price": 0.0,
    "currency": "USD",
}
