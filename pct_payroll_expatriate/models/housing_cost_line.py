from odoo import api, fields, models


class HousingCostLine(models.Model):
    _name = 'housing.cost.line'
    _description = 'Housing Cost Line'

    housing_id = fields.Many2one(
        'expatriate.housing',
        string='Housing',
        required=True,
        ondelete='cascade'
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        'housing_cost_line_employee_rel',
        'cost_line_id',
        'employee_id',
        string='Assigned Employees',
        help='Leave empty to split cost among all housing occupants. '
             'Select specific employees to assign cost only to them.'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Cost Item',
        required=True,
        domain="[('type', '=', 'service')]",
        help='Select the type of housing cost (service products only)'
    )
    name = fields.Char(
        string='Description',
        compute='_compute_name',
        store=True,
        readonly=False
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if line.product_id and not line.name:
                line.name = line.product_id.name
            elif not line.product_id:
                line.name = False
