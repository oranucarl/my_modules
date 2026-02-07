# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestCreateTransferWizard(models.TransientModel):
    _name = "purchase.request.create.transfer.wizard"
    _description = "Purchase Request Create Transfer Wizard"

    purchase_request_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Purchase Request",
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name="purchase.request.create.transfer.wizard.line",
        inverse_name="wizard_id",
        string="Lines",
    )
    dest_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination Location",
        compute="_compute_dest_location_id",
        readonly=True,
        help="Destination location from the PR's picking type.",
    )
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        compute="_compute_picking_type_id",
        store=True,
        help="Internal transfer picking type.",
    )

    @api.depends("purchase_request_id")
    def _compute_dest_location_id(self):
        """Get destination location from PR's picking type."""
        for rec in self:
            rec.dest_location_id = (
                rec.purchase_request_id.picking_type_id.default_location_dest_id
            )

    @api.depends("line_ids.source_location_id")
    def _compute_picking_type_id(self):
        """Find internal transfer picking type from the source location's warehouse."""
        for rec in self:
            picking_type = False
            if rec.line_ids:
                # Get warehouse from first source location
                source_location = rec.line_ids[0].source_location_id
                if source_location:
                    warehouse = source_location.warehouse_id
                    if not warehouse:
                        warehouse = self.env["stock.warehouse"].search(
                            [("company_id", "=", rec.purchase_request_id.company_id.id)],
                            limit=1,
                        )
                    if warehouse:
                        picking_type = self.env["stock.picking.type"].search(
                            [
                                ("code", "=", "internal"),
                                ("warehouse_id", "=", warehouse.id),
                            ],
                            limit=1,
                        )
            rec.picking_type_id = picking_type

    def _find_internal_transfer_picking_type(self, source_location):
        """Find internal transfer picking type from warehouse."""
        warehouse = source_location.warehouse_id
        if not warehouse:
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.purchase_request_id.company_id.id)],
                limit=1,
            )
        if warehouse:
            return self.env["stock.picking.type"].search(
                [
                    ("code", "=", "internal"),
                    ("warehouse_id", "=", warehouse.id),
                ],
                limit=1,
            )
        return False

    def action_create_transfer(self):
        """Create stock.picking with stock.moves and link to PR."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No lines to transfer."))

        # Group lines by source location to potentially create multiple pickings
        # or a single picking with moves from different locations
        StockPicking = self.env["stock.picking"]
        StockMove = self.env["stock.move"]
        Allocation = self.env["purchase.request.allocation"]

        # Find the picking type
        picking_type = self._find_internal_transfer_picking_type(
            self.line_ids[0].source_location_id
        )
        if not picking_type:
            raise UserError(
                _("Could not find an internal transfer operation type for the selected warehouse.")
            )

        # Create a single picking for all lines
        picking_vals = {
            "picking_type_id": picking_type.id,
            "location_id": self.line_ids[0].source_location_id.id,
            "location_dest_id": self.dest_location_id.id,
            "origin": self.purchase_request_id.name,
            "company_id": self.purchase_request_id.company_id.id,
        }
        picking = StockPicking.create(picking_vals)

        # Create stock moves for each line
        for line in self.line_ids:
            move_vals = {
                "name": line.product_id.display_name,
                "product_id": line.product_id.id,
                "product_uom_qty": line.transfer_qty,
                "product_uom": line.product_uom_id.id,
                "picking_id": picking.id,
                "location_id": line.source_location_id.id,
                "location_dest_id": self.dest_location_id.id,
                "company_id": self.purchase_request_id.company_id.id,
                "created_purchase_request_line_id": line.pr_line_id.id,
            }
            move = StockMove.create(move_vals)

            # Create allocation to link move to PR line
            Allocation.create({
                "purchase_request_line_id": line.pr_line_id.id,
                "stock_move_id": move.id,
                "requested_product_uom_qty": line.transfer_qty,
            })

        # Update PR state to in_progress if not already
        if self.purchase_request_id.state == "approved":
            self.purchase_request_id.button_in_progress()

        # Return action to view the created picking
        return {
            "name": _("Internal Transfer"),
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "view_mode": "form",
            "res_id": picking.id,
            "target": "current",
        }


class PurchaseRequestCreateTransferWizardLine(models.TransientModel):
    _name = "purchase.request.create.transfer.wizard.line"
    _description = "Purchase Request Create Transfer Wizard Line"

    wizard_id = fields.Many2one(
        comodel_name="purchase.request.create.transfer.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    pr_line_id = fields.Many2one(
        comodel_name="purchase.request.line",
        string="PR Line",
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        readonly=True,
    )
    source_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Source Location",
        required=True,
        domain="[('usage', '=', 'internal')]",
        help="Location from which to transfer stock.",
    )
    transfer_qty = fields.Float(
        string="Transfer Qty",
        digits="Product Unit of Measure",
        required=True,
        help="Quantity to transfer.",
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UoM",
        required=True,
    )
