from odoo import models
from odoo.exceptions import AccessError


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def check_access_rights(self, operation, raise_exception=True):
        """Override to restrict delete access based on group membership."""
        res = super().check_access_rights(operation, raise_exception=False)

        if operation == 'unlink' and res:
            # Superuser bypasses this check
            if not self.env.su:
                has_delete_access = self.env.user.has_group(
                    'pct_delete_removal.group_delete_records'
                )
                if not has_delete_access:
                    if raise_exception:
                        raise AccessError("")
                    return False

        if not res and raise_exception:
            raise AccessError("")

        return res
