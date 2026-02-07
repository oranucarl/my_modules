# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models


class PurchaseRequestConfirmDoneWizard(models.TransientModel):
    _name = "purchase.request.confirm.done.wizard"
    _description = "Purchase Request Confirm Done Wizard"

    purchase_request_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Purchase Request",
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name="purchase.request.confirm.done.wizard.line",
        inverse_name="wizard_id",
        string="Unfulfilled Lines",
        readonly=True,
    )
    total_unfulfilled_count = fields.Integer(
        string="Total Unfulfilled Products",
        compute="_compute_totals",
    )
    total_unfulfilled_qty = fields.Float(
        string="Total Unfulfilled Quantity",
        compute="_compute_totals",
    )

    @api.depends("line_ids")
    def _compute_totals(self):
        for rec in self:
            rec.total_unfulfilled_count = len(rec.line_ids)
            rec.total_unfulfilled_qty = sum(rec.line_ids.mapped("unfulfilled_qty"))

    def action_confirm_done(self):
        """Confirm and mark the PR as done despite unfulfilled quantities."""
        self.ensure_one()
        self.purchase_request_id.write({"state": "done"})
        return {"type": "ir.actions.act_window_close"}


class PurchaseRequestConfirmDoneWizardLine(models.TransientModel):
    _name = "purchase.request.confirm.done.wizard.line"
    _description = "Purchase Request Confirm Done Wizard Line"

    wizard_id = fields.Many2one(
        comodel_name="purchase.request.confirm.done.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    pr_line_id = fields.Many2one(
        comodel_name="purchase.request.line",
        string="PR Line",
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        readonly=True,
    )
    requested_qty = fields.Float(
        string="Requested Qty",
        digits="Product Unit of Measure",
        readonly=True,
    )
    fulfilled_qty = fields.Float(
        string="Fulfilled Qty",
        digits="Product Unit of Measure",
        readonly=True,
    )
    unfulfilled_qty = fields.Float(
        string="Unfulfilled Qty",
        digits="Product Unit of Measure",
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UoM",
        readonly=True,
    )
