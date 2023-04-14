# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _apply_source_relocate_rule(self, *args, **kwargs):
        relocated = super()._apply_source_relocate_rule(*args, **kwargs)
        if not relocated:
            return relocated
        relocated._prepare_location_orderpoint_replenishment(
            "location_id",
            self.env["stock.location.orderpoint"]._get_waiting_move_domain(),
        )
        return relocated
