from odoo import fields, models


class ExpatriateDocumentType(models.Model):
    _name = 'expatriate.document.type'
    _description = 'Expatriate Document Type'
    _order = 'name'

    name = fields.Char(
        string='Document Type',
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
        ('name_uniq', 'unique(name)', 'Document type name must be unique.')
    ]
