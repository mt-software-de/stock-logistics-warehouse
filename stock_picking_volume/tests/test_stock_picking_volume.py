# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockPickingVolume(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.wh = self.env["stock.warehouse"].create(
            {
                "name": "Base Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "ship_only",
                "code": "BWH",
            }
        )
        self.loc_stock = self.wh.lot_stock_id
        self.loc_customer = self.env.ref("stock.stock_location_customers")
        self.product = self.env["product.product"].create(
            {
                "name": "Unittest P1",
                "product_length": 10.0,
                "product_width": 5.0,
                "product_height": 3.0,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "dimensional_uom_id": self.env.ref("uom.product_uom_meter").id,
                "type": "product",
            }
        )
        self.product.onchange_calculate_volume()
        self.picking_type_out = self.env.ref("stock.picking_type_out")
        self.picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customer.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "product_uom_qty": 5.0,
                            "location_id": self.loc_stock.id,
                            "location_dest_id": self.loc_customer.id,
                        },
                    )
                ],
            }
        )

    def _set_product_qty(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(product, self.loc_stock, qty)

    def test_picking_draft_volume(self):
        """
        Data:
            one picking with one move line with 5 units of product
        Test Case:
            get the volume of the picking
        Expected result:
            volume is 5 * 10 * 5 * 3 = 750
            The volume is computed from the expected quantity
        """
        self.assertEqual(self.picking.volume, 750)

    def test_picking_partially_available_volume(self):
        """
        Data:
            one picking with one move line with 5 units of product
        Test Case:
            set 1 unit of product as available
            get the volume of the picking
        Expected result:
            volume is 1 * 10 * 5 * 3 = 150
            The volume is computed from the available quantity
        """
        self._set_product_qty(self.product, 1)
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.invalidate_cache()
        self.assertEqual(self.picking.volume, 150)

    def test_picking_available_volume(self):
        """
        Data:
            one picking with one move line with 5 units of product
        Test Case:
            set 5 unit of product as available
            get the volume of the picking
        Expected result:
            volume is 5 * 10 * 5 * 3 = 750
            The volume is computed from the expected quantity
        """
        self._set_product_qty(self.product, 5)
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.invalidate_cache()
        self.assertEqual(self.picking.volume, 750)

    def test_picking_done_volume(self):
        """
        Data:
            one picking with one move line with 5 units of product
        Test Case:
            set 1 unit of product as done
            confirm the picking
            get the volume of the picking
        Expected result:
            volume is 1 * 10 * 5 * 3 = 150
            The volume is computed from the done quantity
        """
        self._set_product_qty(self.product, 1)
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_line_ids.qty_done = 1
        self.picking.button_validate()
        self.assertEqual(self.picking.volume, 150)

    def test_picking_cancel_volume(self):
        """
        Data:
            one picking with one move line with 5 units of product
        Test Case:
            set 1 unit of product as done
            confirm the picking
            cancel the picking
            get the volume of the picking
        Expected result:
            volume is 5 * 10 * 5 * 3 = 750
            The volume is computed from the expected quantity
        """
        self._set_product_qty(self.product, 1)
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_line_ids.qty_done = 1
        self.picking.button_validate()
        self.picking.action_cancel()
        self.assertEqual(self.picking.volume, 750)
