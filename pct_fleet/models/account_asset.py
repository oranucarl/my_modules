from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id_sync_values(self):
        """When a vehicle is linked to an asset, sync asset values to the vehicle."""
        if self.vehicle_id:
            # Update vehicle with asset values
            values = {}
            if self.original_value:
                values['net_car_value'] = self.original_value
            if self.book_value:
                values['residual_value'] = self.book_value
            if values:
                self.vehicle_id.write(values)

    def write(self, vals):
        """Override write to sync original_value and book_value changes to linked vehicle."""
        res = super().write(vals)

        # Check if relevant fields changed
        if 'original_value' in vals or 'book_value' in vals or 'vehicle_id' in vals:
            for asset in self:
                if asset.vehicle_id:
                    vehicle_vals = {}
                    if 'original_value' in vals or 'vehicle_id' in vals:
                        vehicle_vals['net_car_value'] = asset.original_value
                    if 'book_value' in vals or 'vehicle_id' in vals:
                        vehicle_vals['residual_value'] = asset.book_value
                    if vehicle_vals:
                        asset.vehicle_id.write(vehicle_vals)

        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to sync values to vehicle if vehicle_id is set on creation."""
        records = super().create(vals_list)

        for asset in records:
            if asset.vehicle_id:
                vehicle_vals = {}
                if asset.original_value:
                    vehicle_vals['net_car_value'] = asset.original_value
                if asset.book_value:
                    vehicle_vals['residual_value'] = asset.book_value
                if vehicle_vals:
                    asset.vehicle_id.write(vehicle_vals)

        return records
