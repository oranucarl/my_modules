# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(AccountPayment, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res
class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments = super()._create_payments()

        # Get invoices from the wizard lines
        invoices = self.line_ids.move_id
        if invoices:
            # If the invoice has a branch, use that for the payment
            branch = invoices[0].branch_id
            if branch:
                payments.write({'branch_id': branch.id})

        return payments