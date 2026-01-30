# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    b2b_eval_mode = fields.Selection([("last_x_days", "Last X days"),("mtd", "Month to date"),("ytd", "Year to date")],
        default="mtd", config_parameter="pct_b2b_customer_categorization.eval_mode", string="Categorization Window")
    b2b_last_x_days = fields.Integer(default=30, config_parameter="pct_b2b_customer_categorization.last_x_days", string="Last X Days (when applicable)")
    b2b_threshold_pct = fields.Integer(default=90, config_parameter="pct_b2b_customer_categorization.threshold_pct",
        string="Notify at % of upper limit", help="Send notifications when customer progress is at or above this percent.")
