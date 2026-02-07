from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    serial_number = fields.Char(
        string='Serial Number',
        help='Serial number of the asset',
    )
    assigned_to_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Assigned To',
        help='Employee to whom this asset is assigned',
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        related='assigned_to_id.department_id',
        store=True,
        readonly=False,
    )
