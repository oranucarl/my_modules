# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        session_info = super().session_info()
        user = self.env.user

        if user.has_group('base.group_user'):
            allowed = user.branch_ids
            session_info.update({
                "user_branches": {
                    "current_branch": user.branch_id.id if user.branch_id else False,
                    "allowed_branches": {
                        b.id: {"id": b.id, "name": b.name, "company": b.company_id.id}
                        for b in allowed
                    },
                },
                "display_switch_branch_menu": len(allowed) > 1,
                "allowed_branches": allowed.ids,
            })
        return session_info