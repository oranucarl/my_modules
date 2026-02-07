# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        tracking=True,
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrder, self).default_get(fields_list)
        if self.env.user.branch_id:
            if 'branch_id' in fields_list:
                res['branch_id'] = self.env.user.branch_id.id
            # Set default warehouse based on user's default branch
            if 'warehouse_id' in fields_list:
                warehouse = self.env['stock.warehouse'].search(
                    [('branch_id', '=', self.env.user.branch_id.id)],
                    limit=1
                )
                if warehouse:
                    res['warehouse_id'] = warehouse.id
        return res

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            pricelist = self.env['product.pricelist'].search(
                [('branch_id', '=', self.branch_id.id)],
                limit=1
            )
            if pricelist:
                self.pricelist_id = pricelist.id

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id_branch(self):
        if self.warehouse_id:
            if self.warehouse_id.branch_id:
                self.branch_id = self.warehouse_id.branch_id
            if self.warehouse_id.bank_information:
                self.note = self.warehouse_id.bank_information

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.warehouse_id and order.warehouse_id.bank_information:
                order.note = order.warehouse_id.bank_information
        return orders

    @api.constrains('branch_id', 'warehouse_id', 'pricelist_id')
    def _check_branch_consistency(self):
        for order in self:
            if not order.branch_id:
                continue

            if order.warehouse_id and order.warehouse_id.branch_id and \
               order.warehouse_id.branch_id != order.branch_id:
                raise ValidationError(
                    "Branch mismatch:\n\n"
                    f"- Sales Order Branch: {order.branch_id.name}\n"
                    f"- Warehouse Branch: {order.warehouse_id.branch_id.name}\n\n"
                    "Please select a warehouse that belongs to the same branch."
                )

            if order.pricelist_id and order.pricelist_id.branch_id and \
               order.pricelist_id.branch_id != order.branch_id:
                raise ValidationError(
                    "Branch mismatch:\n\n"
                    f"- Sales Order Branch: {order.branch_id.name}\n"
                    f"- Pricelist Branch: {order.pricelist_id.branch_id.name}\n\n"
                    "Please select a pricelist that belongs to the same branch."
                )

    def _prepare_invoice(self):
        """Propagate branch to invoice."""
        res = super(SaleOrder, self)._prepare_invoice()
        if self.branch_id:
            res['branch_id'] = self.branch_id.id
        return res


class SaleReport(models.Model):
    _inherit = "sale.report"

    branch_id = fields.Many2one(
        'res.branch',
        string="Branch",
        readonly=True
    )

    def _select_additional_fields(self):
        additional_fields = super()._select_additional_fields()
        additional_fields['branch_id'] = "s.branch_id"
        return additional_fields

    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        return f"{group_by}, s.branch_id"
