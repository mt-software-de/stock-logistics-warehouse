# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import hashlib
import struct

from odoo import fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    auto_create_group_by_product = fields.Boolean(string="Procurement Group by Product")

    def _get_auto_procurement_group(self, product):
        if self.auto_create_group_by_product:
            if product.auto_create_procurement_group_ids:
                return fields.first(product.auto_create_procurement_group_ids)
            # Make sure that two transactions can not create a procurement group
            # For the same product at the same time.
            lock_name = f"product.product,{product.id}-auto-proc-group"
            hasher = hashlib.sha1(str(lock_name).encode())
            int_lock = struct.unpack("q", hasher.digest()[:8])
            self.env.cr.execute("SELECT pg_try_advisory_xact_lock(%s);", (int_lock,))
            lock_acquired = self.env.cr.fetchone()[0]
            if not lock_acquired:
                # This error will be catched by odoo or the job queue
                # runner and will cause a retry
                self.env.cr.execute(
                    """
                    do $$
                        begin
                            raise SQLSTATE '55P03';
                        end
                    $$ language plpgsql;
                """
                )
        return super()._get_auto_procurement_group(product)

    def _prepare_auto_procurement_group_data(self, product):
        result = super()._prepare_auto_procurement_group_data(product)
        if self.auto_create_group_by_product:
            result["product_id"] = product.id
            result["partner_id"] = False
        return result
