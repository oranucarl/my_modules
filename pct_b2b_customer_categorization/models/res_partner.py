# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo import api, fields, models
from odoo.tools import float_is_zero


class ResPartner(models.Model):
    _inherit = "res.partner"

    # B2B category assignment
    b2b_category_ids = fields.Many2many(
        "b2b.category",
        "res_partner_b2b_category_rel",
        "partner_id",
        "category_id",
        string="B2B Category",
        help="Auto-managed nightly based on invoiced totals.",
    )

    # STORED: Total amount spent
    b2b_total_spend = fields.Monetary(
        string="Total Amount Spent",
        currency_field="currency_id",
        compute="_compute_b2b_total_spend",
        store=True,
        compute_sudo=True,
    )

    # STORED: Progress % toward next tier
    b2b_progress_pct = fields.Float(
        string="Progress to next tier",
        compute="_compute_b2b_progress_pct",
        store=True,
        compute_sudo=True,
        help="Progress within current tier toward its upper limit.",
    )

    b2b_last_notification_datetime = fields.Datetime(
        string="Last B2B Notification",
        readonly=True,
        copy=False,
    )

    # =========================================================================
    # COMPUTE: STORED TOTAL SPEND
    # =========================================================================
    @api.depends_context("uid")
    def _compute_b2b_total_spend(self):
        """
        STORED FIELD.
        Only updates b2b_total_spend.
        Cannot update b2b_progress_pct here (would cause warning).
        """
        ICP = self.env["ir.config_parameter"].sudo()
        mode = ICP.get_param("pct_b2b_customer_categorization.eval_mode", "mtd")
        last_x = int(ICP.get_param("pct_b2b_customer_categorization.last_x_days", 30))

        date_from, date_to, _ = self._b2b_window(mode, last_x)

        # Group totals
        moves = self.env["account.move"].sudo().read_group(
            [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("invoice_date", ">=", date_from),
                ("invoice_date", "<=", date_to),
                ("partner_id", "in", self.ids),
                ("company_id", "=", self.env.company.id),
            ],
            ["partner_id", "amount_total_signed:sum"],
            ["partner_id"],
        )
        totals = {r["partner_id"][0]: r["amount_total_signed"] for r in moves}

        for partner in self:
            partner.b2b_total_spend = totals.get(partner.id, 0.0)

    # =========================================================================
    # COMPUTE: NON-STORED PROGRESS PERCENT
    # =========================================================================
    @api.depends("b2b_total_spend", "b2b_category_ids")
    def _compute_b2b_progress_pct(self):
        """
        NON-STORED FIELD.
        Uses only safe dependencies, no writes.
        """
        for partner in self:
            spend = partner.b2b_total_spend

            tiers = partner.b2b_category_ids.filtered(lambda c: c.active).sorted("lower_limit")

            current = next(
                (c for c in tiers if spend >= c.lower_limit and (not c.upper_limit or spend < c.upper_limit)),
                None,
            )

            if not current:
                partner.b2b_progress_pct = 0.0
                continue

            if not current.upper_limit:
                partner.b2b_progress_pct = 100.0
                continue

            span = current.upper_limit - current.lower_limit
            if span <= 0:
                partner.b2b_progress_pct = 0.0
                continue

            partner.b2b_progress_pct = max(
                0.0, min(100.0, ((spend - current.lower_limit) / span) * 100.0)
            )

    # =========================================================================
    # DATE WINDOW
    # =========================================================================
    @api.model
    def _b2b_window(self, mode, last_x):
        today = date.today()

        if mode == "last_x_days":
            start = today - timedelta(days=last_x - 1)
            return start, today, f"LAST-{last_x}-{today.isoformat()}"

        if mode == "ytd":
            start = date(today.year, 1, 1)
            return start, today, f"YTD-{today.year}"

        # default: MTD
        start = date(today.year, today.month, 1)
        return start, today, f"MTD-{today.year}-{today.month:02d}"

    # =========================================================================
    # CRON: NIGHTLY CATEGORIZATION
    # =========================================================================
    @api.model
    def b2b_run_categorization(self):
        ICP = self.env["ir.config_parameter"].sudo()
        mode = ICP.get_param("pct_b2b_customer_categorization.eval_mode", "mtd")
        last_x = int(ICP.get_param("pct_b2b_customer_categorization.last_x_days", 30))
        threshold_pct = int(ICP.get_param("pct_b2b_customer_categorization.threshold_pct", 90))

        date_from, date_to, window_key = self._b2b_window(mode, last_x)

        categories = self.env["b2b.category"].sudo().search(
            [("active", "=", True)], order="lower_limit asc"
        )

        partners = self.env["res.partner"].sudo().search([("customer_rank", ">", 0)])

        # Recompute stored totals
        partners._compute_b2b_total_spend()
        partners._compute_b2b_progress_pct()

        # Aggregate totals per commercial partner
        moves = self.env["account.move"].sudo().read_group(
            [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("invoice_date", ">=", date_from),
                ("invoice_date", "<=", date_to),
                ("company_id", "=", self.env.company.id),
            ],
            ["commercial_partner_id", "amount_total_signed:sum"],
            ["commercial_partner_id"],
        )

        totals = {r["commercial_partner_id"][0]: r["amount_total_signed"] for r in moves}

        Log = self.env["b2b.notification.log"].sudo()
        template = self.env.ref(
            "pct_b2b_customer_categorization.mail_template_b2b_threshold",
            raise_if_not_found=False,
        )

        for p in partners:
            spend = totals.get(p.id, 0.0)

            # select category per spend
            if spend <= 0:
                new_cats = self.env["b2b.category"]
            else:
                new_cats = categories.filtered(
                    lambda c: spend >= c.lower_limit and (not c.upper_limit or spend < c.upper_limit)
                )

            p.sudo().write({"b2b_category_ids": [(6, 0, new_cats.ids)]})

            # threshold notifications
            if new_cats and new_cats[0].upper_limit:
                c = new_cats[0]
                span = c.upper_limit - c.lower_limit
                progress = 0 if span <= 0 else ((spend - c.lower_limit) / span) * 100

                if progress >= threshold_pct:
                    already = Log.search_count(
                        [
                            ("partner_id", "=", p.id),
                            ("category_id", "=", c.id),
                            ("window_key", "=", window_key),
                        ]
                    )

                    if not already:
                        recipients = c.contact_line_ids.filtered(
                            lambda l: l.notify_active and l.partner_id.email
                        )

                        if template and recipients:
                            for rcpt in recipients:
                                template.with_context(
                                    partner=p,
                                    category=c,
                                    spend=spend,
                                    progress=progress,
                                    date_from=date_from,
                                    date_to=date_to,
                                ).send_mail(rcpt.partner_id.id, force_send=True)

                        Log.create(
                            {
                                "partner_id": p.id,
                                "category_id": c.id,
                                "window_key": window_key,
                            }
                        )
