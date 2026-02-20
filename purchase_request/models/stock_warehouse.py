# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    project_manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Project Manager",
        domain=lambda self: [
            ("groups_id", "in", self.env.ref("purchase_request.group_purchase_request_user").id)
        ],
        help="Project Manager assigned to this warehouse. "
        "This user will only see PRs and picking types from warehouses they are assigned to.",
    )
    storekeeper_id = fields.Many2one(
        comodel_name="res.users",
        string="Storekeeper",
        domain=lambda self: [
            ("groups_id", "in", self.env.ref("purchase_request.group_purchase_request_viewer").id)
        ],
        help="Storekeeper assigned to this warehouse. "
        "This user has read-only access to PRs and restricted access to warehouse inventory.",
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
        help="Project linked to this warehouse. "
        "The project's analytic account will be used for purchase requests.",
    )

    @api.model
    def _get_warehouse_from_project(self, project):
        """Find the warehouse linked to a specific project."""
        if not project:
            return False
        return self.search([("project_id", "=", project.id)], limit=1)
