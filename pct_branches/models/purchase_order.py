# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(PurchaseOrder, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res

    def _prepare_invoice(self):
        """Propagate branch to invoice."""
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.branch_id:
            res['branch_id'] = self.branch_id.id
        return res


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    branch_id = fields.Many2one(
        'res.branch',
        string="Branch",
        domain="[('company_id', '=', company_id)]",
        readonly=True
    )
