# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PctReassignCustodianWizard(models.TransientModel):
    _name = 'pct.reassign.custodian.wizard'
    _description = 'Reassign Custodian Wizard'

    petty_cash_id = fields.Many2one(
        'pct.petty.cash',
        string='Petty Cash',
        required=True,
        readonly=True,
    )
    current_custodian_id = fields.Many2one(
        'res.users',
        string='Current Custodian',
        readonly=True,
    )
    new_custodian_id = fields.Many2one(
        'res.users',
        string='New Custodian',
        required=True,
        domain="[('id', '!=', current_custodian_id)]",
        help='Select the new custodian for this petty cash',
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values from active petty cash record"""
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'pct.petty.cash':
            petty_cash = self.env['pct.petty.cash'].browse(active_id)
            res['petty_cash_id'] = petty_cash.id
            res['current_custodian_id'] = petty_cash.custodian_id.id
        return res

    def action_reassign_custodian(self):
        """Reassign the custodian of the petty cash"""
        self.ensure_one()
        if not self.new_custodian_id:
            raise UserError(_('Please select a new custodian.'))
        if self.new_custodian_id == self.current_custodian_id:
            raise UserError(_('The new custodian must be different from the current custodian.'))

        # Update the custodian
        self.petty_cash_id.write({
            'custodian_id': self.new_custodian_id.id,
        })

        # Post a message on the petty cash record
        self.petty_cash_id.message_post(
            body=_('Custodian reassigned from %s to %s') % (
                self.current_custodian_id.name,
                self.new_custodian_id.name,
            ),
            message_type='notification',
        )

        return {'type': 'ir.actions.act_window_close'}
