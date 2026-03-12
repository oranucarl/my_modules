from odoo import api, fields, models


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    is_expatriate = fields.Boolean(
        string='Expatriate Batch',
        compute='_compute_is_expatriate',
        store=True,
        help='Indicates if this batch contains any expatriate payslips.',
    )

    @api.depends('slip_ids', 'slip_ids.contract_id', 'slip_ids.contract_id.structure_type_id',
                 'slip_ids.contract_id.structure_type_id.is_expatriate')
    def _compute_is_expatriate(self):
        for batch in self:
            batch.is_expatriate = any(
                slip.contract_id.structure_type_id.is_expatriate
                for slip in batch.slip_ids
                if slip.contract_id and slip.contract_id.structure_type_id
            )
