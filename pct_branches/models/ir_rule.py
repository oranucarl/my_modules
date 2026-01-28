# -*- coding: utf-8 -*-
from odoo import api, models


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def _eval_context(self):
        """Extend context evaluation to include branch_ids for record rules."""
        res = super(IrRule, self)._eval_context()
        branch_ids = self.env.context.get('allowed_branch_ids', [])
        branches = self.env['res.branch']

        if branch_ids:
            branches = self.env['res.branch'].sudo().browse(branch_ids)

        if branches:
            res['branch_ids'] = branches.ids
        else:
            # Fallback: use ALL user's allowed branches (not just current branch)
            user = self.env.user.sudo()
            if user.branch_ids:
                res['branch_ids'] = user.branch_ids.ids
            elif user.branch_id:
                res['branch_ids'] = user.branch_id.ids
            else:
                res['branch_ids'] = []

        return res

    def _compute_domain_keys(self):
        """Add branch context to cache key for domain computation."""
        return super(IrRule, self)._compute_domain_keys() + ['allowed_branch_ids']
