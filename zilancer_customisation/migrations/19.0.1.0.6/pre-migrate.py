# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Backfill NULLs before schema updates that may add NOT NULL constraints."""
    columns = (
        "weight_per_unit",
        "height",
        "width",
        "gross_weight",
        "net_weight",
    )
    cr.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_name = 'product_template'
           AND column_name = ANY(%s)
        """,
        [list(columns)],
    )
    existing = {row[0] for row in cr.fetchall()}
    for column in columns:
        if column in existing:
            cr.execute(
                f'UPDATE product_template SET "{column}" = 0 WHERE "{column}" IS NULL'
            )
