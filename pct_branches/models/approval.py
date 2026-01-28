# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        domain="[('company_id', '=', company_id)]"
    )


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(ApprovalRequest, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    @api.onchange('category_id')
    def _onchange_category_branch(self):
        if self.category_id and self.category_id.branch_id:
            self.branch_id = self.category_id.branch_id
