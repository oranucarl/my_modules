# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class B2BCategory(models.Model):
    _name = "b2b.category"
    _description = "B2B Customer Spend Category"
    _order = "lower_limit asc, upper_limit asc, id asc"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color")
    lower_limit = fields.Monetary(required=True, string="Lower Limit")
    upper_limit = fields.Monetary(string="Upper Limit (leave empty for no cap)")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id, required=True)
    contact_line_ids = fields.One2many("b2b.category.contact", "category_id", string="Notify Contacts")
    code = fields.Char(help="Optional short code, e.g., BRONZE/SILVER/GOLD", index=True)

    @api.constrains("lower_limit", "upper_limit")
    def _check_range(self):
        for rec in self:
            if rec.upper_limit and rec.upper_limit <= rec.lower_limit:
                raise ValidationError(_("Upper limit must be greater than lower limit."))

    @api.constrains("lower_limit", "upper_limit", "active")
    def _check_overlap(self):
        for rec in self:
            if not rec.active:
                continue
            domain = [("id", "!=", rec.id), ("active", "=", True)]
            others = self.search(domain)
            for other in others:
                lo1, hi1 = rec.lower_limit, rec.upper_limit or float("inf")
                lo2, hi2 = other.lower_limit, other.upper_limit or float("inf")
                if max(lo1, lo2) < min(hi1, hi2):
                    raise ValidationError(_("Active category ranges must not overlap: '%s' overlaps with '%s'.") % (rec.name, other.name))

class B2BCategoryContact(models.Model):
    _name = "b2b.category.contact"
    _description = "B2B Category Notification Contact"

    category_id = fields.Many2one("b2b.category", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", required=True, domain=[("email", "!=", False)])
    email = fields.Char(related="partner_id.email", store=False)
    notify_active = fields.Boolean(string="Notify", default=True)

class B2BNotificationLog(models.Model):
    _name = "b2b.notification.log"
    _description = "B2B Category Threshold Notification Log"
    _order = "create_date desc"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    category_id = fields.Many2one("b2b.category", required=True, ondelete="cascade")
    window_key = fields.Char(required=True)
