# -*- coding: utf-8 -*-
from odoo import fields, models

class CrmLead(models.Model):
    _inherit = "crm.lead"

    b2b_category_ids = fields.Many2many(
        comodel_name="b2b.category",
        string="B2B Category",
        related="partner_id.b2b_category_ids",
        readonly=True, 
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    b2b_category_ids = fields.Many2many(
        comodel_name="b2b.category",
        string="B2B Category",
        related="partner_id.b2b_category_ids",
        readonly=True, 
    )
