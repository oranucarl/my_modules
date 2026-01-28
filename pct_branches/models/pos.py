# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch where this POS order was processed."
    )

    @api.model
    def default_get(self, fields_list):
        res = super(PosOrder, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res


class PosSession(models.Model):
    _inherit = 'pos.session'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch related to this POS session."
    )

    @api.model
    def default_get(self, fields_list):
        res = super(PosSession, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        domain="[('company_id', '=', company_id)]",
        help="Branch linked to this POS payment."
    )
