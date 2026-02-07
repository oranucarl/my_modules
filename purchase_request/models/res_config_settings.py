# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pr_creation_limit = fields.Integer(
        string="PR Creation Limit",
        config_parameter="purchase_request.pr_creation_limit",
        help="Maximum number of Purchase Requests a Project Manager can create per week. "
        "Set to 0 for unlimited.",
    )
