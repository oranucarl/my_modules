from odoo import fields, models


class ExpatriateSponsorCompany(models.Model):
    _name = 'expatriate.sponsor.company'
    _description = 'Expatriate Sponsor Company'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True
    )
    code = fields.Char(
        string='Code'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    notes = fields.Text(
        string='Notes'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Sponsor company name must be unique.')
    ]
