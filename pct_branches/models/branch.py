# -*- coding: utf-8 -*-
from odoo import models, fields


class Branch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']

    name = fields.Char(
        string='Branch Name',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Branch Code',
        help="Short code to identify this branch (e.g. LAG001)."
    )

    company_id = fields.Many2one(
        'res.company',
        string='Parent Company',
        default=lambda self: self.env.company,
        required=True,
        tracking=True,
        help="The subsidiary or main company this branch belongs to.",
    )

    analytic_distribution_id = fields.Many2one(
        'account.analytic.distribution.model',
        string='Analytic Distribution',
        help="Defines how costs and revenues from this branch are distributed analytically."
    )
