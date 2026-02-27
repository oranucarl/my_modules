from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectProjects(models.Model):
    _inherit = 'project.project'

    # Uses existing account_id (analytic account) from project.project
    prefix = fields.Char(string='Prefix', tracking=True, size=6)
    invoice_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Invoice Sequence',
        readonly=True,
        copy=False,
        help="Sequence used to generate project-prefixed invoice numbers."
    )

    def _get_analytic_distribution(self):
        """Convert project's account_id to analytic_distribution format."""
        self.ensure_one()
        if self.account_id:
            return {str(self.account_id.id): 100}
        return False

    _sql_constraints = [
        ('unique_prefix', 'unique(prefix)', 'Each Project must have a unique Prefix!')
    ]

    @api.constrains('prefix')
    def _check_prefix_length(self):
        for project in self:
            if project.prefix and len(project.prefix) > 6:
                raise ValidationError(_("Prefix must be 6 characters or less."))

    def _create_invoice_sequence(self):
        """Create invoice sequence for this project based on its prefix."""
        self.ensure_one()
        if not self.prefix:
            return False
        # Search for existing sequence by code
        sequence = self.env['ir.sequence'].search([
            ('code', '=', f'pct.project.invoice.{self.prefix}')
        ], limit=1)
        if not sequence:
            sequence = self.env['ir.sequence'].sudo().create({
                'name': f'Project {self.name} Invoice Sequence',
                'code': f'pct.project.invoice.{self.prefix}',
                'prefix': f'{self.prefix}/%(year)s/%(month)s/',
                'padding': 5,
                'company_id': self.company_id.id if self.company_id else False,
            })
        return sequence

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        # Auto-create invoice sequence for projects with prefix
        for project in projects:
            if project.prefix and not project.invoice_sequence_id:
                project.invoice_sequence_id = project._create_invoice_sequence()
        return projects

    def write(self, vals):
        res = super().write(vals)
        # Auto-create invoice sequence if prefix is set/changed
        if 'prefix' in vals:
            for project in self:
                if project.prefix and not project.invoice_sequence_id:
                    project.invoice_sequence_id = project._create_invoice_sequence()
        return res


# =====================================================================
# Purchase Order Integration
# =====================================================================
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('project.project', string='Project', tracking=True)

    def button_confirm(self):
        """Override to require analytic distribution on all lines before confirmation."""
        for order in self:
            for line in order.order_line:
                if line.display_type not in ('line_section', 'line_note') and not line.analytic_distribution:
                    raise ValidationError(_("Analytic distribution is required on all purchase order lines before confirmation."))
        return super().button_confirm()

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.project_id:
            invoice_vals['project_id'] = self.project_id.id
        return invoice_vals


# =====================================================================
# Purchase Order Line Integration
# =====================================================================
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        """Override to ensure analytic distribution is propagated to invoice lines."""
        vals = super()._prepare_account_move_line(move=move)
        # Propagate analytic from PO line to invoice line
        if self.analytic_distribution:
            vals['analytic_distribution'] = self.analytic_distribution
        return vals


# =====================================================================
# Account Move Integration
# =====================================================================
class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        required=True,
    )
    project_sequence_number = fields.Char(
        string='Project Sequence Number',
        readonly=True,
        copy=False,
        help="Project-specific invoice sequence number for reporting."
    )

    @api.onchange('project_id')
    def _onchange_project_id_set_partner(self):
        """For invoices: auto-fill partner from project if project has a partner set."""
        for move in self:
            # Only apply to customer invoices/refunds, not vendor bills
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue
            if move.project_id and move.project_id.partner_id:
                move.partner_id = move.project_id.partner_id

    @api.onchange('partner_id')
    def _onchange_partner_id_set_project(self):
        """For invoices: auto-fill project if partner has exactly one project."""
        for move in self:
            # Only apply to customer invoices/refunds, not vendor bills
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue
            # Only auto-set if project is not already set
            if move.partner_id and not move.project_id:
                projects = self.env['project.project'].search([
                    ('partner_id', '=', move.partner_id.id),
                    ('account_id', '!=', False),
                ], limit=2)
                # Only auto-set if exactly one project exists for this partner
                if len(projects) == 1:
                    move.project_id = projects

    def _assign_project_sequence_number(self):
        """Assign project sequence number only for customer invoices (not bills)."""
        for move in self:
            # Only apply to customer invoices, not vendor bills
            if move.move_type != 'out_invoice':
                continue
            if move.project_sequence_number:
                continue
            if not move.project_id or not move.project_id.invoice_sequence_id:
                continue
            move.project_sequence_number = move.project_id.invoice_sequence_id.next_by_id()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        # Assign project sequence numbers after creation (only for customer invoices)
        for move in moves:
            if move.move_type == 'out_invoice' and move.project_id and move.project_id.invoice_sequence_id and not move.project_sequence_number:
                move._assign_project_sequence_number()
        return moves

    def write(self, vals):
        # Check if project_id needs to be set from invoice_origin (PO reference)
        for move in self:
            if not move.project_id and not vals.get('project_id'):
                origin = vals.get('invoice_origin') or move.invoice_origin
                if origin:
                    project_id = self._get_project_from_order(origin)
                    if project_id:
                        vals['project_id'] = project_id

        res = super().write(vals)

        # Handle project changes - assign sequence number only for customer invoices
        if 'project_id' in vals:
            for move in self:
                if move.move_type == 'out_invoice' and move.project_id and move.project_id.invoice_sequence_id and not move.project_sequence_number:
                    move._assign_project_sequence_number()

        return res

    def _get_project_from_order(self, origin):
        """Fetch project_id from related Purchase Order."""
        if not origin:
            return False
        order = self.env['purchase.order'].search([('name', '=', origin)], limit=1)
        return order.project_id.id if order and order.project_id else False

    def action_post(self):
        """Override to require analytic distribution on all lines before posting."""
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                for line in move.invoice_line_ids:
                    if line.display_type == 'product' and not line.analytic_distribution:
                        raise ValidationError(_("Analytic distribution is required on all invoice/bill lines before posting."))
        return super().action_post()


# =====================================================================
# Account Payment Integration
# =====================================================================
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        required=True,
    )


# =====================================================================
# Payment Register Wizard Integration
# =====================================================================
class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        compute='_compute_project_id',
        store=True,
        readonly=False,
    )

    @api.depends('line_ids')
    def _compute_project_id(self):
        for wizard in self:
            moves = wizard.line_ids.mapped('move_id')
            projects = moves.mapped('project_id')
            wizard.project_id = projects[0] if len(projects) == 1 else False

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.project_id:
            payment_vals['project_id'] = self.project_id.id
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        # Get project from the batch's invoices
        lines = batch_result.get('lines', self.env['account.move.line'])
        moves = lines.mapped('move_id')
        projects = moves.mapped('project_id')
        if len(projects) == 1 and projects:
            payment_vals['project_id'] = projects.id
        return payment_vals


# =====================================================================
# Purchase Report Integration
# =====================================================================
class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        readonly=True
    )

    def _select_additional_fields(self):
        additional_fields = super()._select_additional_fields()
        additional_fields.update({
            'project_id': 'po.project_id'
        })
        return additional_fields

    def _group_by_purchase(self):
        group_by = super()._group_by_purchase()
        return f"""{group_by},
            po.project_id"""
