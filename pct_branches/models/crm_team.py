# -*- coding: utf-8 -*-
from odoo import models, fields


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch assigned to this sales team."
    )
