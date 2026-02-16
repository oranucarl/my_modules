from odoo import models, _
from odoo.exceptions import UserError

# Models where deletion is restricted
RESTRICTED_MODELS = [
    'res.partner',
    'res.partner.category',
    'sale.order',
    'purchase.order',
    'account.move',
    'account.journal',
    'account.account',
    'account.tax',
    'mrp.production',
    'mrp.bom',
    'quality.check',
    'quality.point',
]


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def unlink(self):
        if self._name in RESTRICTED_MODELS and not self.env.su:
            has_delete_access = self.env.user.has_group(
                'pct_delete_removal.group_delete_records'
            )
            if not has_delete_access:
                raise UserError(_("Records in the system cannot be deleted! 🗑️❌\n"
                                  "Cancel or Archive and log a note instead. ✍️"))
        return super().unlink()
