from odoo import api, SUPERUSER_ID

def set_default_partner_discount(env):
    reg_discount = env['sale.discount'].search(
        [('code', '=', 'REG')], limit=1
    )

    if not reg_discount:
        return

    partners = env['res.partner'].search([
        ('discount_id', '=', False),
        ('customer_rank', '>', 0),
    ])

    partners.write({'discount_id': reg_discount.id})
