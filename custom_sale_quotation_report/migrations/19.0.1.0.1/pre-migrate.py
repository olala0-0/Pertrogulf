# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Rename text country_of_origin before ORM converts the column to integer.

    sale.order.country_of_origin was changed from Char to Many2one(res.country).
    Existing rows may store country names (e.g. "United States of America") which
    cannot be cast to integer during _auto_init.
    """
    cr.execute(
        """
        SELECT data_type
          FROM information_schema.columns
         WHERE table_name = 'sale_order'
           AND column_name = 'country_of_origin'
        """
    )
    row = cr.fetchone()
    if not row:
        return
    if row[0] in ('integer', 'bigint'):
        return

    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'sale_order'
           AND column_name = 'country_of_origin_old_char'
        """
    )
    if cr.fetchone():
        return

    cr.execute(
        """
        ALTER TABLE sale_order
        RENAME COLUMN country_of_origin TO country_of_origin_old_char
        """
    )
