# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch responsible for this manufacturing order."
    )

    @api.model
    def default_get(self, fields_list):
        res = super(MrpProduction, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        domain="[('company_id', '=', company_id)]",
        help="Branch for this work order."
    )


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch for this unbuild order."
    )

    @api.model
    def default_get(self, fields_list):
        res = super(MrpUnbuild, self).default_get(fields_list)
        if 'branch_id' in fields_list and self.env.user.branch_id:
            res['branch_id'] = self.env.user.branch_id.id
        return res


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch related to this Bill of Materials."
    )


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch operating this work center."
    )


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        help="Branch associated with this manufacturing operation."
    )
