# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    petty_cash_default_journal_id = fields.Many2one(
        'account.journal',
        string='Default Petty Cash Journal',
        config_parameter='pct_petty_cash.default_journal_id',
        domain="[('type', '=', 'cash')]",
        help="Default journal used for new petty cash records.",
    )
    petty_cash_require_analytic = fields.Boolean(
        string='Require Analytic Distribution',
        config_parameter='pct_petty_cash.require_analytic',
        help="If enabled, analytic distribution will be required on expense lines.",
    )
