from odoo import models, fields, api, _


class SaleDiscount(models.Model):
    _name = 'sale.discount'
    _description = 'Customer Discount Category'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)

    discount_rate = fields.Float(
        string='Discount %',
        help='Logical discount identifier (not applied directly)'
    )

    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )

    _sql_constraints = [
        ('code_company_unique', 'unique(code, company_id)',
         'Discount code must be unique per company.')
    ]
class ResPartner(models.Model):
    _inherit = 'res.partner'

    discount_id = fields.Many2one(
        'sale.discount',
        string='Discount Category',
        company_dependent=True,
        default=lambda self: self._default_discount(),
        ondelete='restrict'
    )

    @api.model
    def _default_discount(self):
        # default REG for the CURRENT company
        return self.env['sale.discount'].search([
            ('code', '=', 'REG'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
    

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    discount_id = fields.Many2one(
        'sale.discount',
        string='Discount Category',
        domain="[('company_id', '=', company_id)]"
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_matching_pricelist(self):
        self.ensure_one()

        if not self.partner_id or not self.branch_id:
            return False

        # get partner discount in the context of the SO company
        discount = self.partner_id.with_company(self.company_id).discount_id
        if not discount:
            return False

        pricelist = self.env['product.pricelist'].search([
            ('company_id', '=', self.company_id.id),
            ('branch_id', '=', self.branch_id.id),
            ('discount_id', '=', discount.id),
            ('active', '=', True),
        ], limit=1)

        return pricelist

    @api.onchange('partner_id', 'branch_id')
    def _onchange_partner_branch_pricelist(self):
        for order in self:
            pricelist = order._get_matching_pricelist()
            if pricelist:
                order.pricelist_id = pricelist

    def write(self, vals):
        res = super().write(vals)

        for order in self:
            pricelist = order._get_matching_pricelist()
            if pricelist and order.pricelist_id != pricelist:
                super(SaleOrder, order).write({'pricelist_id': pricelist.id})

        return res