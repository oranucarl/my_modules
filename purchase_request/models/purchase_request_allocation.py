# Copyright 2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.tools import html_escape


class PurchaseRequestAllocation(models.Model):
    _name = "purchase.request.allocation"
    _description = "Purchase Request Allocation"

    purchase_request_line_id = fields.Many2one(
        string="Purchase Request Line",
        comodel_name="purchase.request.line",
        required=True,
        ondelete="cascade",
        copy=True,
        index=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        readonly=True,
        related="purchase_request_line_id.request_id.company_id",
        store=True,
        index=True,
    )
    stock_move_id = fields.Many2one(
        string="Stock Move",
        comodel_name="stock.move",
        ondelete="cascade",
        index=True,
    )
    purchase_line_id = fields.Many2one(
        string="Purchase Line",
        comodel_name="purchase.order.line",
        copy=True,
        ondelete="cascade",
        help="Service Purchase Order Line",
        index=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
        related="purchase_request_line_id.product_id",
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        string="UoM",
        comodel_name="uom.uom",
        related="purchase_request_line_id.product_uom_id",
        readonly=True,
    )
    requested_product_uom_qty = fields.Float(
        string="Requested Quantity",
        help="Quantity of the purchase request line allocated to the"
        "stock move, in the UoM of the Purchase Request Line",
    )

    allocated_product_qty = fields.Float(
        string="Allocated Quantity",
        copy=False,
        help="Quantity of the purchase request line allocated to the stock"
        "move, in the default UoM of the product",
    )
    open_product_qty = fields.Float(
        string="Open Quantity", compute="_compute_open_product_qty"
    )

    purchase_state = fields.Selection(related="purchase_line_id.state")

    @api.depends(
        "requested_product_uom_qty",
        "allocated_product_qty",
        "stock_move_id",
        "stock_move_id.state",
        "stock_move_id.product_uom_qty",
        "stock_move_id.move_line_ids.quantity",
        "purchase_line_id",
        "purchase_line_id.qty_received",
        "purchase_state",
    )
    def _compute_open_product_qty(self):
        for rec in self:
            if rec.purchase_state in ["cancel", "done"]:
                rec.open_product_qty = 0.0
            else:
                rec.open_product_qty = (
                    rec.requested_product_uom_qty - rec.allocated_product_qty
                )
                if rec.open_product_qty < 0.0:
                    rec.open_product_qty = 0.0

    @api.model
    def _purchase_request_confirm_done_message_content(self, message_data):
        message = ""
        message += _(
            "From last reception this quantity has been "
            "allocated to this purchase request"
        )
        message += "<ul>"
        message += _(
            "<li><b>%(product_name)s</b>: "
            "Received quantity %(product_qty)s %(product_uom)s</li>"
        ) % {
            "product_name": html_escape(message_data["product_name"]),
            "product_qty": message_data["product_qty"],
            "product_uom": message_data["product_uom"],
        }
        message += "</ul>"
        return message

    def _prepare_message_data(self, po_line, request, allocated_qty):
        return {
            "request_name": request.name,
            "po_name": po_line.order_id.name,
            "product_name": po_line.product_id.display_name,
            "product_qty": allocated_qty,
            "product_uom": po_line.product_uom.name,
        }

    def _notify_allocation(self, allocated_qty):
        if not allocated_qty:
            return
        for allocation in self:
            request = allocation.purchase_request_line_id.request_id
            po_line = allocation.purchase_line_id
            message_data = self._prepare_message_data(po_line, request, allocated_qty)
            message = self._purchase_request_confirm_done_message_content(message_data)
            request.message_post(
                body=Markup(message),
                subtype_id=self.env.ref("mail.mt_note").id,
            )

    def _trigger_pr_line_recompute(self, pr_lines=None):
        """Trigger recomputation of PR line quantities."""
        if pr_lines is None:
            pr_lines = self.mapped("purchase_request_line_id")
        if pr_lines:
            # Invalidate cache and trigger recomputation
            pr_lines.invalidate_recordset(["qty_in_transfer", "unfulfilled_qty", "purchased_qty"])
            pr_lines._compute_transfer_qty()
            pr_lines._compute_unfulfilled_qty()
            pr_lines._compute_purchased_qty()

    @api.model_create_multi
    def create(self, vals_list):
        allocations = super().create(vals_list)
        # Trigger recomputation on related PR lines
        allocations._trigger_pr_line_recompute()
        return allocations

    def write(self, vals):
        # Get PR lines before write (in case purchase_request_line_id changes)
        pr_lines_before = self.mapped("purchase_request_line_id")
        res = super().write(vals)
        # Get PR lines after write
        pr_lines_after = self.mapped("purchase_request_line_id")
        # Trigger recomputation on all affected PR lines
        self._trigger_pr_line_recompute(pr_lines_before | pr_lines_after)
        return res

    def unlink(self):
        pr_lines = self.mapped("purchase_request_line_id")
        res = super().unlink()
        # Trigger recomputation on PR lines after unlinking
        if pr_lines:
            pr_lines.invalidate_recordset(["qty_in_transfer", "unfulfilled_qty", "purchased_qty"])
            pr_lines._compute_transfer_qty()
            pr_lines._compute_unfulfilled_qty()
            pr_lines._compute_purchased_qty()
        return res
