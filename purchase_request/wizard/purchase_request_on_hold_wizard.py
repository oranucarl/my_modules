# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseRequestOnHoldWizard(models.TransientModel):
    _name = "purchase.request.on.hold.wizard"
    _description = "Purchase Request On Hold Wizard"

    purchase_request_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Purchase Request",
        required=True,
        readonly=True,
    )
    previous_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To be approved"),
            ("approved", "Approved"),
            ("in_progress", "In progress"),
            ("on_hold", "On Hold"),
            ("done", "Done"),
            ("rejected", "Rejected"),
        ],
        string="Current State",
        readonly=True,
    )
    on_hold_reason = fields.Text(
        string="On Hold Reason",
        required=True,
    )

    def action_put_on_hold(self):
        """Put the purchase request on hold with the provided reason."""
        self.ensure_one()
        if not self.on_hold_reason:
            raise UserError(_("Please provide a reason for putting this request on hold."))

        self.purchase_request_id.write({
            "state": "on_hold",
            "previous_state": self.previous_state,
            "on_hold_reason": self.on_hold_reason,
        })
        return {"type": "ir.actions.act_window_close"}
