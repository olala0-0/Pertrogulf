# -*- coding: utf-8 -*-

PRODUCT_TEMPLATE_FLOAT_COLUMNS = (
    "weight_per_unit",
    "height",
    "width",
    "gross_weight",
    "net_weight",
)


def _backfill_product_template_floats(cr):
    """Set NULL float values to 0 so upgrades do not fail on constraints."""
    cr.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_name = 'product_template'
           AND column_name = ANY(%s)
        """,
        [list(PRODUCT_TEMPLATE_FLOAT_COLUMNS)],
    )
    existing = {row[0] for row in cr.fetchall()}
    for column in PRODUCT_TEMPLATE_FLOAT_COLUMNS:
        if column in existing:
            cr.execute(
                f'UPDATE product_template SET "{column}" = 0 WHERE "{column}" IS NULL'
            )


def pre_init_hook(env):
    """Odoo 19: pre_init_hook receives env (install only)."""
    _backfill_product_template_floats(env.cr)


def post_init_hook(env):
    """Odoo 19: post_init_hook receives env (install only)."""
    _backfill_product_template_floats(env.cr)
