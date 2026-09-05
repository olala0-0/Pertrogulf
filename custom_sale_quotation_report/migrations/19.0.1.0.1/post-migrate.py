# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

# Common free-text values saved before the field became a Many2one.
_COUNTRY_ALIASES = {
    'united states of america': 'United States',
    'united states': 'United States',
    'usa': 'United States',
    'u.s.a.': 'United States',
    'u.s.a': 'United States',
    'us': 'United States',
    'uk': 'United Kingdom',
    'uae': 'United Arab Emirates',
    'u.a.e.': 'United Arab Emirates',
}


def _resolve_country(Country, raw_value):
    name = (raw_value or '').strip()
    if not name:
        return Country.browse()
    if name.isdigit():
        return Country.browse(int(name)).exists()

    lookup = _COUNTRY_ALIASES.get(name.lower(), name)
    country = Country.search(
        ['|', ('name', '=ilike', lookup), ('code', '=ilike', lookup)],
        limit=1,
    )
    if country:
        return country

    return Country.search([('name', 'ilike', lookup)], limit=1)


def migrate(cr, version):
    """Copy legacy text country names into the new Many2one column."""
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'sale_order'
           AND column_name = 'country_of_origin_old_char'
        """
    )
    if not cr.fetchone():
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    Country = env['res.country']

    cr.execute(
        """
        SELECT id, country_of_origin_old_char
          FROM sale_order
         WHERE country_of_origin_old_char IS NOT NULL
           AND TRIM(country_of_origin_old_char) <> ''
        """
    )
    for so_id, raw_value in cr.fetchall():
        country = _resolve_country(Country, raw_value)
        if country:
            cr.execute(
                """
                UPDATE sale_order
                   SET country_of_origin = %s
                 WHERE id = %s
                """,
                [country.id, so_id],
            )

    cr.execute(
        """
        ALTER TABLE sale_order
        DROP COLUMN country_of_origin_old_char
        """
    )
