# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to send email notifications to storekeepers."""
        pickings = super().create(vals_list)
        for picking in pickings:
            picking._send_storekeeper_notifications()
        return pickings

    def _send_storekeeper_notifications(self):
        """Send email notifications to storekeepers when transfer is created."""
        self.ensure_one()

        # Get the email template
        template = self.env.ref(
            "purchase_request.email_template_stock_transfer_notification",
            raise_if_not_found=False,
        )
        if not template:
            return

        picking_type = self.picking_type_id.code

        if picking_type == "internal":
            # Internal transfer - notify both source and destination storekeepers
            source_warehouse = self.location_id.warehouse_id
            dest_warehouse = self.location_dest_id.warehouse_id

            # Send to source storekeeper
            if source_warehouse and source_warehouse.storekeeper_id:
                self._send_notification_email(
                    template,
                    source_warehouse.storekeeper_id,
                    "source",
                )

            # Send to destination storekeeper
            if dest_warehouse and dest_warehouse.storekeeper_id:
                # Only send if different from source storekeeper
                if (
                    not source_warehouse
                    or source_warehouse.storekeeper_id
                    != dest_warehouse.storekeeper_id
                ):
                    self._send_notification_email(
                        template,
                        dest_warehouse.storekeeper_id,
                        "destination",
                    )

        elif picking_type == "incoming":
            # Receipt - notify destination storekeeper
            dest_warehouse = self.location_dest_id.warehouse_id
            if dest_warehouse and dest_warehouse.storekeeper_id:
                self._send_notification_email(
                    template,
                    dest_warehouse.storekeeper_id,
                    "destination",
                )

    def _send_notification_email(self, template, user, location_type):
        """Send notification email to a warehouse manager."""
        if not user.email:
            return

        # Use context to pass additional info to the template
        ctx = {
            "recipient_name": user.name,
            "recipient_email": user.email,
            "location_type": location_type,
            "picking_type_name": self.picking_type_id.name,
        }
        template.with_context(**ctx).send_mail(
            self.id,
            force_send=False,
            email_values={"email_to": user.email},
        )

    def _check_storekeeper_validation(self):
        """Check if the current user can validate this transfer.

        For internal transfers, only the destination storekeeper can validate
        if the user has the Storekeeper (View Only) group. Users without the Storekeeper
        group (e.g., inventory administrators) can still validate any transfer.
        """
        self.ensure_one()
        user = self.env.user

        # Only apply restriction to internal transfers
        if self.picking_type_id.code != "internal":
            return True

        # Check if user has Storekeeper (View Only) group
        is_storekeeper = user.has_group(
            "purchase_request.group_purchase_request_viewer"
        )

        # If user is not a Storekeeper, they can validate (e.g., stock admin)
        if not is_storekeeper:
            return True

        # If user is PR Administrator, they can validate anything
        if user.has_group("purchase_request.group_purchase_request_administrator"):
            return True

        # If user is Warehouse Manager (higher access), they can validate anything
        if user.has_group("purchase_request.group_purchase_request_manager"):
            return True

        # For Storekeepers, check if they are the destination storekeeper
        dest_warehouse = self.location_dest_id.warehouse_id
        if dest_warehouse and dest_warehouse.storekeeper_id == user:
            return True

        # Storekeeper is not the destination storekeeper
        return False

    def button_validate(self):
        """Override to add storekeeper validation check for internal transfers."""
        for picking in self:
            if not picking._check_storekeeper_validation():
                dest_warehouse = picking.location_dest_id.warehouse_id
                storekeeper_name = (
                    dest_warehouse.storekeeper_id.name
                    if dest_warehouse and dest_warehouse.storekeeper_id
                    else _("Not Assigned")
                )
                raise UserError(
                    _(
                        "You cannot validate this internal transfer. "
                        "Only the Storekeeper of the destination warehouse "
                        "(%(warehouse)s - %(storekeeper)s) can validate this transfer."
                    )
                    % {
                        "warehouse": dest_warehouse.name if dest_warehouse else _("Unknown"),
                        "storekeeper": storekeeper_name,
                    }
                )
        return super().button_validate()
