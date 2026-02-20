# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_STATES = [
    ("draft", "Draft"),
    ("to_approve", "To be approved"),
    ("on_hold", "On Hold"),
    ("approved", "Approved"),
    ("in_progress", "In progress"),
    ("done", "Done"),
    ("rejected", "Rejected"),
]


class PurchaseRequest(models.Model):
    _name = "purchase.request"
    _description = "Purchase Request"
    _mail_post_access = "read"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    @api.model
    def _company_get(self):
        return self.env["res.company"].browse(self.env.company.id)

    @api.model
    def _get_can_create(self):
        """Check if current user can create purchase requests."""
        user = self.env.user
        # PR Administrators can always create
        if user.has_group("purchase_request.group_purchase_request_administrator"):
            return True
        # Storekeepers cannot create
        if user.has_group("purchase_request.group_purchase_request_manager"):
            return False
        # Project Managers can create
        if user.has_group("purchase_request.group_purchase_request_user"):
            return True
        return False

    @api.model
    def _get_default_requested_by(self):
        return self.env["res.users"].browse(self.env.uid)

    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("purchase.request")

    @api.model
    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return types[:1]

    @api.depends("state")
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in (
                "to_approve",
                "approved",
                "rejected",
                "in_progress",
                "on_hold",
                "done",
            ):
                rec.is_editable = False
            else:
                rec.is_editable = True

    name = fields.Char(
        string="Request Reference",
        required=True,
        default=lambda self: _("New"),
        tracking=True,
    )
    is_name_editable = fields.Boolean(
        default=lambda self: self.env.user.has_group("base.group_no_one"),
    )
    origin = fields.Char(string="Source Document")
    date_start = fields.Date(
        string="Creation date",
        help="Date when the user initiated the request.",
        default=fields.Date.context_today,
        tracking=True,
    )
    requested_by = fields.Many2one(
        comodel_name="res.users",
        required=True,
        copy=False,
        tracking=True,
        default=_get_default_requested_by,
        index=True,
    )
    assigned_to = fields.Many2one(
        comodel_name="res.users",
        string="Approved by",
        tracking=True,
        domain=lambda self: [
            (
                "groups_id",
                "in",
                self.env.ref("purchase_request.group_purchase_request_manager").id,
            )
        ],
        index=True,
        readonly=True,
        copy=False,
    )
    description = fields.Text()
    on_hold_reason = fields.Text(
        string="On Hold Reason",
        tracking=True,
    )
    previous_state = fields.Selection(
        selection=_STATES,
        string="Previous State",
        copy=False,
        help="Stores the state before on hold for restoration",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=False,
        default=_company_get,
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name="purchase.request.line",
        inverse_name="request_id",
        string="Products to Purchase",
        readonly=False,
        copy=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        related="line_ids.product_id",
        string="Product",
        readonly=True,
    )
    state = fields.Selection(
        selection=_STATES,
        string="Status",
        index=True,
        tracking=True,
        required=True,
        copy=False,
        default="draft",
    )
    is_editable = fields.Boolean(compute="_compute_is_editable", readonly=True)
    to_approve_allowed = fields.Boolean(compute="_compute_to_approve_allowed")
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        required=True,
        default=_default_picking_type,
        domain="[('code', '=', 'incoming')]",
    )
    group_id = fields.Many2one(
        comodel_name="procurement.group",
        string="Procurement Group",
        copy=False,
        index=True,
    )
    line_count = fields.Integer(
        string="Purchase Request Line count",
        compute="_compute_line_count",
        readonly=True,
    )
    move_count = fields.Integer(
        string="Stock Move count", compute="_compute_move_count", readonly=True
    )
    purchase_count = fields.Integer(
        string="Purchases count", compute="_compute_purchase_count", readonly=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    estimated_cost = fields.Monetary(
        compute="_compute_estimated_cost",
        string="Total Estimated Cost",
        store=True,
    )
    transfer_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Internal Transfers",
        compute="_compute_transfer_count",
        store=True,
    )
    transfer_count = fields.Integer(
        string="Transfer count",
        compute="_compute_transfer_count",
        store=True,
    )

    @api.depends("line_ids", "line_ids.estimated_cost")
    def _compute_estimated_cost(self):
        for rec in self:
            rec.estimated_cost = sum(rec.line_ids.mapped("estimated_cost"))

    @api.depends(
        "line_ids.purchase_request_allocation_ids.stock_move_id.picking_id"
    )
    def _compute_transfer_count(self):
        for rec in self:
            transfers = rec.mapped(
                "line_ids.purchase_request_allocation_ids.stock_move_id.picking_id"
            ).filtered(lambda p: p.picking_type_id.code == "internal")
            rec.transfer_ids = transfers
            rec.transfer_count = len(transfers)

    @api.depends("line_ids")
    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.mapped("line_ids.purchase_lines.order_id"))

    def action_view_purchase_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        lines = self.mapped("line_ids.purchase_lines.order_id")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("purchase.purchase_order_form").id, "form")
            ]
            action["res_id"] = lines.id
        return action

    @api.depends("line_ids")
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(
                rec.mapped("line_ids.purchase_request_allocation_ids.stock_move_id")
            )

    def action_view_stock_picking(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        # remove default filters
        action["context"] = {}
        lines = self.mapped(
            "line_ids.purchase_request_allocation_ids.stock_move_id.picking_id"
        )
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = lines.id
        return action

    @api.depends("line_ids")
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.mapped("line_ids"))

    def action_view_purchase_request_line(self):
        action = (
            self.env.ref("purchase_request.purchase_request_line_form_action")
            .sudo()
            .read()[0]
        )
        lines = self.mapped("line_ids")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("purchase_request.purchase_request_line_form").id, "form")
            ]
            action["res_id"] = lines.ids[0]
        return action

    @api.depends("state", "line_ids.product_qty", "line_ids.cancelled")
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state == "draft" and any(
                not line.cancelled and line.product_qty for line in rec.line_ids
            )

    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({"state": "draft", "name": self._get_default_name()})
        return super().copy(default)

    @api.model
    def _get_partner_id(self, request):
        user_id = request.assigned_to or self.env.user
        return user_id.partner_id.id

    def _check_pr_creation_permission(self, user):
        """Check if user is allowed to create purchase requests.

        Warehouse Managers (group_purchase_request_manager) cannot create PRs,
        unless they are also PR Administrators.
        """
        # PR Administrators can always create
        if user.has_group("purchase_request.group_purchase_request_administrator"):
            return True

        # Warehouse Managers cannot create PRs
        if user.has_group("purchase_request.group_purchase_request_manager"):
            raise UserError(
                _("Warehouse Managers are not allowed to create Purchase Requests.")
            )

        return True

    def _check_pr_creation_limit(self, user):
        """Check if user has exceeded the weekly PR creation limit."""
        # Only check for users who are NOT PR Administrators
        if user.has_group("purchase_request.group_purchase_request_administrator"):
            return True

        # Only apply limit to project managers (group_purchase_request_user)
        if not user.has_group("purchase_request.group_purchase_request_user"):
            return True

        # Get the limit from config settings
        pr_limit = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("purchase_request.pr_creation_limit", default="0")
        )

        if pr_limit <= 0:
            return True  # No limit set

        # Calculate start of current week (Monday)
        today = fields.Date.context_today(self)
        start_of_week = today - timedelta(days=today.weekday())

        # Count PRs created by this user this week
        pr_count = self.sudo().search_count([
            ("requested_by", "=", user.id),
            ("create_date", ">=", start_of_week),
        ])

        if pr_count >= pr_limit:
            raise UserError(
                _(
                    "You have reached your weekly limit of %(limit)s purchase requests. "
                    "You have already created %(count)s this week."
                )
                % {"limit": pr_limit, "count": pr_count}
            )
        return True

    @api.model_create_multi
    def create(self, vals_list):
        # Check if user is allowed to create PRs (Storekeepers cannot)
        self._check_pr_creation_permission(self.env.user)
        # Check PR creation limit for current user
        self._check_pr_creation_limit(self.env.user)

        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self._get_default_name()
        requests = super().create(vals_list)
        for vals, request in zip(vals_list, requests, strict=True):
            if vals.get("assigned_to"):
                partner_id = self._get_partner_id(request)
                request.message_subscribe(partner_ids=[partner_id])
        return requests

    def write(self, vals):
        res = super().write(vals)
        for request in self:
            if vals.get("assigned_to"):
                partner_id = self._get_partner_id(request)
                request.message_subscribe(partner_ids=[partner_id])
        return res

    def _can_be_deleted(self):
        self.ensure_one()
        return self.state == "draft"

    def unlink(self):
        for request in self:
            if not request._can_be_deleted():
                raise UserError(
                    _("You cannot delete a purchase request which is not draft.")
                )
        return super().unlink()

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        return self.write({"state": "draft"})

    def button_to_approve(self):
        self.to_approve_allowed_check()
        return self.write({"state": "to_approve"})

    def button_approved(self):
        return self.write({"state": "approved", "assigned_to": self.env.uid})

    def button_rejected(self):
        self.mapped("line_ids").do_cancel()
        return self.write({"state": "rejected"})

    def button_in_progress(self):
        return self.write({"state": "in_progress"})

    def button_done(self):
        """Mark PR as done, with confirmation if there are unfulfilled quantities."""
        self.ensure_one()
        # Check for unfulfilled quantities
        unfulfilled_lines = self.line_ids.filtered(
            lambda l: not l.cancelled and l.unfulfilled_qty > 0
        )
        if unfulfilled_lines:
            # Create confirmation wizard
            wizard = self.env["purchase.request.confirm.done.wizard"].create({
                "purchase_request_id": self.id,
            })
            # Create wizard lines for unfulfilled items
            WizardLine = self.env["purchase.request.confirm.done.wizard.line"]
            for line in unfulfilled_lines:
                fulfilled = line.product_qty - line.unfulfilled_qty
                WizardLine.create({
                    "wizard_id": wizard.id,
                    "pr_line_id": line.id,
                    "product_id": line.product_id.id,
                    "requested_qty": line.product_qty,
                    "fulfilled_qty": fulfilled,
                    "unfulfilled_qty": line.unfulfilled_qty,
                    "product_uom_id": line.product_uom_id.id,
                })
            return {
                "name": _("Confirm Close Purchase Request"),
                "type": "ir.actions.act_window",
                "res_model": "purchase.request.confirm.done.wizard",
                "view_mode": "form",
                "res_id": wizard.id,
                "target": "new",
            }
        return self.write({"state": "done"})

    def button_on_hold(self):
        """Open wizard to request on hold reason."""
        self.ensure_one()
        return {
            "name": _("Put On Hold"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.request.on.hold.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_purchase_request_id": self.id,
                "default_previous_state": self.state,
            },
        }

    def button_remove_on_hold(self):
        """Remove on hold status and restore previous state."""
        for rec in self:
            if rec.state == "on_hold" and rec.previous_state:
                rec.write({
                    "state": rec.previous_state,
                    "previous_state": False,
                    "on_hold_reason": False,
                })
        return True

    def check_auto_reject(self):
        """When all lines are cancelled the purchase request should be
        auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda line: line.cancelled is False):
                pr.write({"state": "rejected"})

    def to_approve_allowed_check(self):
        for rec in self:
            if not rec.to_approve_allowed:
                raise UserError(
                    _(
                        "You can't request an approval for a purchase request "
                        "which is empty. (%s)"
                    )
                    % rec.name
                )

    def action_view_transfers(self):
        """Open the list of internal transfers related to this PR."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        action["context"] = {}
        transfers = self.transfer_ids
        if len(transfers) > 1:
            action["domain"] = [("id", "in", transfers.ids)]
        elif transfers:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = transfers.id
        else:
            action["domain"] = [("id", "=", False)]
        return action

    def action_check_availability(self):
        """Open the check availability wizard."""
        self.ensure_one()
        # Create wizard with lines for each PR line
        wizard = self.env["purchase.request.check.availability.wizard"].create({
            "purchase_request_id": self.id,
        })
        wizard._create_wizard_lines()
        return {
            "name": _("Check Availability"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.request.check.availability.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def check_auto_done(self):
        """Check if all lines are fulfilled and auto-set PR to done."""
        for pr in self:
            if pr.state not in ("approved", "in_progress"):
                continue
            # Check if all lines have unfulfilled_qty = 0
            all_fulfilled = all(
                line.unfulfilled_qty <= 0 and not line.cancelled
                for line in pr.line_ids.filtered(lambda l: not l.cancelled)
            )
            if all_fulfilled and pr.line_ids:
                pr.button_done()

    @api.onchange("picking_type_id")
    def _onchange_picking_type_id(self):
        """Set analytic account on PR lines based on project linked to warehouse."""
        if self.picking_type_id and self.picking_type_id.warehouse_id:
            warehouse = self.picking_type_id.warehouse_id
            if warehouse.project_id and warehouse.project_id.account_id:
                analytic_account = warehouse.project_id.account_id
                for line in self.line_ids:
                    line.analytic_distribution = {str(analytic_account.id): 100.0}
