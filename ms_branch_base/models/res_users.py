from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    ms_branch_ids = fields.Many2many(
        'ms.branch', 'ms_branch_users_rel', 'user_id', 'branch_id',
        string='Allowed Branches',
        help='Which branches this person may see. Only enforced on users in '
             'the Branch User group - leave the group off and nothing changes '
             'for them.')
    ms_default_branch_id = fields.Many2one(
        'ms.branch', string='Default Branch',
        help='Filled in on new orders, bills and transfers this person creates.')
    ms_branch_restricted = fields.Boolean(
        string='Restricted to Their Branches',
        compute='_compute_ms_branch_restricted', store=True,
        help='Worked out from the two branch groups. It exists as a stored '
             'field because the record rule has to read it, and a rule domain '
             'can only follow plain fields on the user.')

    @api.depends('group_ids.all_implied_ids')
    def _compute_ms_branch_restricted(self):
        """Dihitung dari grup BESERTA implikasinya, bukan grup langsung.

        `group_ids` hanya berisi grup yang diberikan langsung. Kalau seseorang
        mendapat grup cabang lewat grup lain yang meng-`implied` -nya, memeriksa
        `group_ids` saja membuat orang itu dianggap TIDAK dibatasi - kegagalan
        yang terbuka, bukan tertutup. `all_group_ids` sudah termasuk implikasi.
        """
        pengguna = self.env.ref('ms_branch_base.group_ms_branch_user',
                                raise_if_not_found=False)
        manajer = self.env.ref('ms_branch_base.group_ms_branch_manager',
                               raise_if_not_found=False)
        for user in self:
            grup = user.all_group_ids
            user.ms_branch_restricted = bool(
                pengguna and pengguna in grup
                and not (manajer and manajer in grup))

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            'ms_branch_ids', 'ms_default_branch_id']

    @api.constrains('ms_branch_ids', 'ms_default_branch_id')
    def _check_ms_default_branch(self):
        for user in self:
            cabang = user.ms_default_branch_id
            if cabang and user.ms_branch_ids and cabang not in user.ms_branch_ids:
                raise ValidationError(self.env._(
                    'The default branch must be one of the allowed branches.'))

    def write(self, vals):
        """Bersihkan cache aturan setelah cabang atau grup berubah.

        Domain ir.rule di-cache per pengguna (`ormcache` pada uid + model +
        mode). Tanpa pembersihan ini, mengubah daftar cabang seseorang tidak
        terasa apa-apa sampai server dimulai ulang - dan itu terlihat persis
        seperti pembatasannya tidak jalan.
        """
        res = super().write(vals)
        if {'ms_branch_ids', 'ms_branch_restricted', 'group_ids',
                'all_group_ids'} & set(vals):
            self.env.registry.clear_cache()
        return res

    def _ms_cabang_default(self):
        """Cabang yang dipakai untuk dokumen baru.

        Kalau tidak ada yang disetel tapi orangnya hanya boleh satu cabang,
        itulah jawabannya - tidak ada gunanya memaksa memilih dari daftar
        berisi satu baris.
        """
        self.ensure_one()
        if self.ms_default_branch_id:
            return self.ms_default_branch_id.id
        if len(self.ms_branch_ids) == 1:
            return self.ms_branch_ids.id
        return False
