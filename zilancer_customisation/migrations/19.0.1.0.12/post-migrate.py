# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Post-migration script: Ensure all business_unit values are non-null after schema upgrade."""
    tables = ('calendar_event', 'res_partner', 'helpdesk_ticket', 'event_event')
    for table in tables:
        cr.execute(
            """
            SELECT column_name
              FROM information_schema.columns
             WHERE table_name = %s
               AND column_name = 'business_unit'
            """,
            [table],
        )
        if cr.fetchone():
            cr.execute(
                f'UPDATE "{table}" SET business_unit = \'pg_marine\' WHERE business_unit IS NULL'
            )
