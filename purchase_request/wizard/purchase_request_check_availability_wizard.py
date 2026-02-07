# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestCheckAvailabilityWizard(models.TransientModel):
    _name = "purchase.request.check.availability.wizard"
    _description = "Purchase Request Check Availability Wizard"

    purchase_request_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Purchase Request",
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name="purchase.request.check.availability.wizard.line",
        inverse_name="wizard_id",
        string="Lines",
    )

    def _create_wizard_lines(self):
        """Create wizard lines for each PR line showing all locations with stock."""
        self.ensure_one()
        WizardLine = self.env["purchase.request.check.availability.wizard.line"]
        StockQuant = self.env["stock.quant"]

        for pr_line in self.purchase_request_id.line_ids.filtered(
            lambda l: not l.cancelled and l.unfulfilled_qty > 0
        ):
            if not pr_line.product_id:
                continue

            # Find all internal locations with available stock for this product
            # across all warehouses in the company
            quants = StockQuant.search([
                ("product_id", "=", pr_line.product_id.id),
                ("location_id.usage", "=", "internal"),
                ("quantity", ">", 0),
                ("company_id", "=", self.purchase_request_id.company_id.id),
            ])

            locations_with_stock = {}
            for quant in quants:
                location = quant.location_id
                if location not in locations_with_stock:
                    # Get available quantity (excluding reserved)
                    available = StockQuant._get_available_quantity(
                        pr_line.product_id,
                        location,
                    )
                    if available > 0:
                        locations_with_stock[location] = available

            if locations_with_stock:
                # Create a line for each location that has stock
                for location, available_qty in locations_with_stock.items():
                    WizardLine.create({
                        "wizard_id": self.id,
                        "pr_line_id": pr_line.id,
                        "product_id": pr_line.product_id.id,
                        "location_id": location.id,
                        "requested_qty": pr_line.unfulfilled_qty,
                        "transfer_qty": 0.0,
                    })
            else:
                # No stock found anywhere - create line without location
                WizardLine.create({
                    "wizard_id": self.id,
                    "pr_line_id": pr_line.id,
                    "product_id": pr_line.product_id.id,
                    "location_id": False,
                    "requested_qty": pr_line.unfulfilled_qty,
                    "transfer_qty": 0.0,
                })

    def action_convert_to_transfer(self):
        """Open the create transfer wizard with selected lines."""
        self.ensure_one()
        lines_to_transfer = self.line_ids.filtered(lambda l: l.transfer_qty > 0)
        if not lines_to_transfer:
            raise UserError(_("Please enter a transfer quantity for at least one line."))

        # Validate quantities
        for line in lines_to_transfer:
            if line.transfer_qty > line.available_qty:
                raise UserError(
                    _("Transfer quantity for %s exceeds available quantity (%s > %s).")
                    % (line.product_id.display_name, line.transfer_qty, line.available_qty)
                )
            if line.transfer_qty > line.requested_qty:
                raise UserError(
                    _("Transfer quantity for %s exceeds requested quantity (%s > %s).")
                    % (line.product_id.display_name, line.transfer_qty, line.requested_qty)
                )

        # Create the transfer wizard
        TransferWizard = self.env["purchase.request.create.transfer.wizard"]
        transfer_wizard = TransferWizard.create({
            "purchase_request_id": self.purchase_request_id.id,
        })

        # Create transfer wizard lines
        TransferWizardLine = self.env["purchase.request.create.transfer.wizard.line"]
        for line in lines_to_transfer:
            TransferWizardLine.create({
                "wizard_id": transfer_wizard.id,
                "pr_line_id": line.pr_line_id.id,
                "product_id": line.product_id.id,
                "source_location_id": line.location_id.id,
                "transfer_qty": line.transfer_qty,
                "product_uom_id": line.pr_line_id.product_uom_id.id,
            })

        return {
            "name": _("Create Internal Transfer"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.request.create.transfer.wizard",
            "view_mode": "form",
            "res_id": transfer_wizard.id,
            "target": "new",
        }


class PurchaseRequestCheckAvailabilityWizardLine(models.TransientModel):
    _name = "purchase.request.check.availability.wizard.line"
    _description = "Purchase Request Check Availability Wizard Line"

    wizard_id = fields.Many2one(
        comodel_name="purchase.request.check.availability.wizard",
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
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Source Location",
        domain="[('usage', '=', 'internal')]",
        help="Select the location from which to transfer stock.",
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
        compute="_compute_warehouse_id",
        store=True,
        help="Warehouse of the source location.",
    )
    available_qty = fields.Float(
        string="Available Qty",
        compute="_compute_available_qty",
        digits="Product Unit of Measure",
        help="Stock on hand at the selected location.",
    )
    requested_qty = fields.Float(
        string="Requested Qty",
        digits="Product Unit of Measure",
        readonly=True,
        help="Unfulfilled quantity from the PR line.",
    )
    transfer_qty = fields.Float(
        string="Transfer Qty",
        digits="Product Unit of Measure",
        help="Quantity to transfer (max is available quantity).",
    )

    @api.depends("location_id")
    def _compute_warehouse_id(self):
        """Get the warehouse from the location."""
        for rec in self:
            if rec.location_id:
                rec.warehouse_id = rec.location_id.warehouse_id
            else:
                rec.warehouse_id = False

    @api.depends("product_id", "location_id")
    def _compute_available_qty(self):
        """Compute available quantity at the selected location."""
        for rec in self:
            if rec.product_id and rec.location_id:
                quant = self.env["stock.quant"]._get_available_quantity(
                    rec.product_id,
                    rec.location_id,
                )
                rec.available_qty = quant
            else:
                rec.available_qty = 0.0

    @api.onchange("location_id")
    def _onchange_location_id(self):
        """Reset transfer_qty when location changes."""
        self.transfer_qty = 0.0

    @api.onchange("transfer_qty")
    def _onchange_transfer_qty(self):
        """Validate transfer quantity doesn't exceed available or requested."""
        if self.transfer_qty > self.available_qty:
            self.transfer_qty = self.available_qty
        if self.transfer_qty > self.requested_qty:
            self.transfer_qty = self.requested_qty
        if self.transfer_qty < 0:
            self.transfer_qty = 0.0
