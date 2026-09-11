from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MsBranch(models.Model):
    """Cabang: satu badan hukum, banyak tempat usaha."""

    _name = 'ms.branch'
    _description = 'Branch'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help='Short code, used where the full name will not fit.')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company)
    address_id = fields.Many2one(
        'res.partner', string='Address',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help='Where this branch actually is. Used on printouts that need the '
             'branch address rather than the head office one.')
    manager_id = fields.Many2one('res.users', string='Manager')
    note = fields.Text()

    _code_uniq = models.Constraint(
        'unique (code, company_id)',
        'That branch code is already used in this company.')

    def _ms_dashboard_metrics(self):
        """Angka yang boleh ditampilkan sebuah dasbor untuk cabang ini.

        Kaitnya sengaja ditaruh di basis, bukan di modul dasbor: modul yang
        menyumbang angka - helpdesk, langganan, dokumen dagang - cukup
        mewarisi `ms.branch` yang memang sudah mereka pakai, tanpa harus
        depends ke modul dasbor. Kalau kaitnya ada di modul dasbor, setiap
        penyumbang jadi ikut menyeretnya, dan pemakai yang tidak memasang
        dasbor tetap kena bebannya.

        Kembalikan list of dict:
            {'key': 'helpdesk_open',   # unik antar modul
             'label': 'Open Tickets',
             'count': 12,               # wajib
             'amount': 0.0,             # opsional, ditampilkan sebagai uang
             'sequence': 30,            # urutan tampil
             'action': {...}}           # opsional, act_window saat diklik
        """
        self.ensure_one()
        return []

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for branch in self:
            branch.display_name = '%s - %s' % (branch.code, branch.name) \
                if branch.code else (branch.name or '')


class MsBranchMixin(models.AbstractModel):
    """Satu field cabang, dipasang di semua dokumen yang memerlukannya.

    Dibuat mixin supaya aturan pengisian default, penjagaan perusahaan, dan
    nama fieldnya persis sama di mana-mana. Kalau tiap model menulis
    field-nya sendiri, cepat atau lambat ada satu yang lupa memeriksa
    perusahaan - dan cabang milik perusahaan lain di sebuah faktur adalah
    kesalahan yang baru ketahuan saat laporan per cabang tidak imbang.
    """

    _name = 'ms.branch.mixin'
    _description = 'Branch Dimension'

    ms_branch_id = fields.Many2one(
        'ms.branch', string='Branch', index=True,
        domain="[('company_id', '=', company_id)]",
        help='Which branch this document belongs to. Filled in from the user '
             'and passed on to whatever this document creates.')

    @api.model
    def default_get(self, fields_list):
        """Cabang default diisi di sini, BUKAN lewat `default=` pada field.

        Saat kolomnya pertama kali dibuat, Odoo memanggil `default` field untuk
        MENGISI SELURUH BARIS LAMA. Artinya seluruh faktur dan pesanan
        bertahun-tahun ke belakang akan ditandai dengan cabang orang yang
        kebetulan memasang modulnya - diam-diam, dan tanpa cara mudah untuk
        membatalkannya. `default_get` hanya berjalan saat orang membuka form
        baru, jadi riwayat dibiarkan kosong sebagaimana mestinya.
        """
        nilai = super().default_get(fields_list)
        if 'ms_branch_id' in fields_list and not nilai.get('ms_branch_id'):
            cabang = self.env.user._ms_cabang_default()
            if cabang:
                nilai['ms_branch_id'] = cabang
        return nilai

    @api.constrains('ms_branch_id', 'company_id')
    def _check_ms_branch_company(self):
        for doc in self:
            cabang = doc.ms_branch_id
            if cabang and doc.company_id and cabang.company_id != doc.company_id:
                raise ValidationError(self.env._(
                    'Branch %(cabang)s belongs to %(pemilik)s, but this '
                    'document is in %(dokumen)s.',
                    cabang=cabang.display_name,
                    pemilik=cabang.company_id.display_name,
                    dokumen=doc.company_id.display_name))
