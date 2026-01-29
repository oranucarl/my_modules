# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    branch_ids = fields.Many2many(
        'res.branch',
        string="Allowed Branches",
        domain="[('company_id', 'in', company_ids)]"
    )
    branch_id = fields.Many2one(
        'res.branch',
        string='Default Branch',
        domain="[('company_id', '=', company_id)]"
    )

    def write(self, values):
        if 'branch_id' in values or 'branch_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
        return super(ResUsers, self).write(values)

    @api.constrains('branch_id', 'branch_ids')
    def _check_branch_id(self):
        for user in self:
            if user.branch_ids and user.branch_id:
                if user.branch_id.id not in user.branch_ids.ids:
                    raise UserError(_("Please select a branch from the Allowed Branches."))

    @api.constrains('branch_id', 'branch_ids', 'active')
    def _check_branch(self):
        for user in self.filtered(lambda u: u.active):
            if user.branch_ids and user.branch_id:
                if user.branch_id not in user.branch_ids:
                    raise ValidationError(
                        _('Branch %(branch_name)s is not in the allowed branches for user %(user_name)s (%(branch_allowed)s).',
                          branch_name=user.branch_id.name,
                          user_name=user.name,
                          branch_allowed=', '.join(user.mapped('branch_ids.name')))
                    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['branch_ids', 'branch_id']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['branch_ids', 'branch_id']
