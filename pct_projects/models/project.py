from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Analytic plan IDs for project and project stage validation
PROJECT_PLAN_ID = 1
PROJECT_STAGE_PLAN_ID = 2


def validate_analytic_distribution(env, analytic_distribution, record_name="record"):
    """Validate analytic distribution has both project and project stage.

    Args:
        env: Odoo environment
        analytic_distribution: The analytic distribution dict to validate
        record_name: Name to use in error messages

    Raises:
        ValidationError if validation fails
    """
    if not analytic_distribution:
        raise ValidationError(_('Analytic distribution is required on %s.') % record_name)

    # Get analytic accounts from distribution
    # Keys can be single IDs or comma-separated IDs (e.g., '242' or '242,410')
    analytic_account_ids = set()
    for key in analytic_distribution.keys():
        for aid in str(key).split(','):
            try:
                analytic_account_ids.add(int(aid.strip()))
            except ValueError:
                continue

    if not analytic_account_ids:
        raise ValidationError(_('Analytic distribution is required on %s.') % record_name)

    # Check for project and project stage analytic accounts
    analytic_accounts = env['account.analytic.account'].browse(list(analytic_account_ids))

    has_project = False
    has_project_stage = False

    for account in analytic_accounts:
        if account.plan_id.id == PROJECT_PLAN_ID:
            has_project = True
        if account.plan_id.id == PROJECT_STAGE_PLAN_ID:
            has_project_stage = True

    if not has_project:
        raise ValidationError(_('Please select a Project in the analytic distribution on %s.') % record_name)
    if not has_project_stage:
        raise ValidationError(_('Please select a Project Stage in the analytic distribution on %s.') % record_name)


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
def replace_project_analytic(env, existing_distribution, new_project_account_id):
    """Replace the project analytic account in a distribution, keeping other plans.

    Args:
        env: Odoo environment
        existing_distribution: Current analytic distribution dict (or None)
        new_project_account_id: ID of the new project's analytic account

    Returns:
        Updated analytic distribution dict
    """
    if not existing_distribution:
        return {str(new_project_account_id): 100}

    new_distribution = {}

    # Process existing distribution - remove old project plan accounts, keep others
    for key, percentage in existing_distribution.items():
        # Keys can be single IDs or comma-separated IDs
        account_ids = [int(aid.strip()) for aid in str(key).split(',') if aid.strip().isdigit()]

        # Check if any of these accounts belong to the Project plan (id=1)
        accounts = env['account.analytic.account'].browse(account_ids)
        non_project_accounts = accounts.filtered(lambda a: a.plan_id.id != PROJECT_PLAN_ID)

        if non_project_accounts:
            # Keep the non-project accounts with their percentage
            if len(non_project_accounts) == len(accounts):
                # All accounts are non-project, keep the key as-is
                new_distribution[key] = percentage
            else:
                # Some accounts were project accounts, rebuild key with only non-project ones
                new_key = ','.join(str(a.id) for a in non_project_accounts)
                new_distribution[new_key] = percentage

    # Add the new project analytic account
    new_distribution[str(new_project_account_id)] = 100

    return new_distribution


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('project.project', string='Project', tracking=True)

    @api.onchange('project_id')
    def _onchange_project_id_set_analytic(self):
        """Auto-fill analytic distribution on lines when project is set."""
        if self.project_id and self.project_id.account_id:
            for line in self.order_line:
                if line.display_type not in ('line_section', 'line_note'):
                    # Replace project analytic, keep other plans (like project stage)
                    line.analytic_distribution = replace_project_analytic(
                        self.env,
                        line.analytic_distribution,
                        self.project_id.account_id.id
                    )

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

    @api.onchange('product_id')
    def _onchange_product_id_set_analytic_from_project(self):
        """Auto-fill analytic distribution from order's project when product is set."""
        if (
            self.product_id
            and self.order_id.project_id
            and self.order_id.project_id.account_id
            and self.display_type not in ('line_section', 'line_note')
            and not self.analytic_distribution
        ):
            self.analytic_distribution = self.order_id.project_id._get_analytic_distribution()

    @api.constrains('analytic_distribution')
    def _check_analytic_distribution(self):
        """Validate analytic distribution has project and project stage."""
        for line in self:
            if line.display_type in ('line_section', 'line_note'):
                continue
            if line.analytic_distribution:
                validate_analytic_distribution(
                    self.env,
                    line.analytic_distribution,
                    _("Purchase Order Line '%s'") % (line.name or line.product_id.name or 'Unknown')
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-fill analytic distribution from order's project on line creation."""
        lines = super().create(vals_list)
        for line in lines:
            if (
                line.order_id.project_id
                and line.order_id.project_id.account_id
                and line.display_type not in ('line_section', 'line_note')
                and not line.analytic_distribution
            ):
                line.analytic_distribution = line.order_id.project_id._get_analytic_distribution()
        return lines

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
    def _onchange_project_id_set_analytic(self):
        """Auto-fill analytic distribution on invoice lines when project is set."""
        for move in self:
            if move.project_id and move.project_id.account_id:
                for line in move.invoice_line_ids:
                    if line.display_type == 'product':
                        # Replace project analytic, keep other plans (like project stage)
                        line.analytic_distribution = replace_project_analytic(
                            self.env,
                            line.analytic_distribution,
                            move.project_id.account_id.id
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
# Account Move Line Integration
# =====================================================================
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _onchange_product_id_set_analytic_from_project(self):
        """Auto-fill analytic distribution from move's project when product is set."""
        if (
            self.product_id
            and self.move_id.project_id
            and self.move_id.project_id.account_id
            and self.display_type == 'product'
            and not self.analytic_distribution
        ):
            self.analytic_distribution = self.move_id.project_id._get_analytic_distribution()

    @api.constrains('analytic_distribution')
    def _check_analytic_distribution(self):
        """Validate analytic distribution has project and project stage."""
        for line in self:
            # Only validate product lines on invoices/bills
            if line.display_type != 'product':
                continue
            if not line.move_id or line.move_id.move_type not in (
                'out_invoice', 'out_refund', 'in_invoice', 'in_refund'
            ):
                continue
            if line.analytic_distribution:
                validate_analytic_distribution(
                    self.env,
                    line.analytic_distribution,
                    _("Invoice/Bill Line '%s'") % (line.name or line.product_id.name or 'Unknown')
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-fill analytic distribution from move's project on line creation."""
        lines = super().create(vals_list)
        for line in lines:
            if (
                line.move_id
                and line.move_id.project_id
                and line.move_id.project_id.account_id
                and line.display_type == 'product'
                and not line.analytic_distribution
            ):
                line.analytic_distribution = line.move_id.project_id._get_analytic_distribution()
        return lines


# =====================================================================
# Account Payment Integration
# =====================================================================
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
    )

    @api.constrains('payment_type', 'project_id')
    def _check_project_required(self):
        """Project is required except for internal transfers."""
        for payment in self:
            if payment.payment_type != 'transfer' and not payment.project_id:
                raise ValidationError(_("Project is required for this payment type."))

    def _synchronize_to_moves(self, changed_fields):
        """Extend to sync project_id from payment to its journal entry."""
        res = super()._synchronize_to_moves(changed_fields)
        if 'project_id' in changed_fields:
            for payment in self.filtered(lambda p: p.move_id):
                payment.move_id.project_id = payment.project_id
                # Also update analytic distribution on bank lines
                if payment.project_id:
                    payment._set_analytic_on_bank_lines()
        return res

    def _set_analytic_on_bank_lines(self):
        """Set analytic distribution from project on bank/liquidity lines."""
        self.ensure_one()
        if not self.project_id or not self.move_id:
            return

        analytic_distribution = self.project_id._get_analytic_distribution()
        if not analytic_distribution:
            return

        # Get bank/liquidity accounts from journals
        bank_accounts = self.journal_id.default_account_id
        if hasattr(self, 'destination_journal_id') and self.destination_journal_id:
            bank_accounts |= self.destination_journal_id.default_account_id

        # Update analytic distribution on bank lines
        for line in self.move_id.line_ids:
            if line.account_id in bank_accounts:
                line.analytic_distribution = analytic_distribution

    def action_post(self):
        """Override to ensure project_id and analytic distribution are set on the journal entry after posting."""
        res = super().action_post()
        for payment in self:
            if payment.move_id and payment.project_id:
                payment.move_id.project_id = payment.project_id
                payment._set_analytic_on_bank_lines()
        return res


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
