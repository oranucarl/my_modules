# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res
