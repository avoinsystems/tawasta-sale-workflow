from odoo.tests import TransactionCase


class TestSaleOrderPartnerClauseToNote(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_clause_obj = cls.env["partner.clause"]
        cls.res_partner_obj = cls.env["res.partner"]
        cls.sale_order_obj = cls.env["sale.order"]
        cls.sale_clause = cls.partner_clause_obj.create(
            {
                "name": "Standard sale clause",
                "clause": "Goods remain our property until paid.",
                "used_for": "sale",
            }
        )
        cls.invoice_clause = cls.partner_clause_obj.create(
            {
                "name": "Standard invoice clause",
                "clause": "Interest on overdue invoices.",
                "used_for": "invoice",
            }
        )
        cls.partner = cls.res_partner_obj.create(
            {
                "name": "Example Corp",
                "sale_clause": cls.sale_clause.id,
                "invoice_clause": cls.invoice_clause.id,
            }
        )
        cls.other_partner = cls.res_partner_obj.create(
            {
                "name": "Jane Doe",
                "sale_clause": cls.partner_clause_obj.create(
                    {
                        "name": "Warehouse clause",
                        "clause": "Delivery at the warehouse gate.",
                        "used_for": "sale",
                    }
                ).id,
            }
        )

    def test_sale_clause_is_added_to_the_order_note(self):
        param_obj = self.env["ir.config_parameter"].sudo()
        param_obj.set_param("account.use_invoice_terms", False)

        order = self.sale_order_obj.create({"partner_id": self.partner.id})
        self.assertIn("Goods remain our property until paid.", order.note)
        self.assertNotIn("Interest on overdue invoices.", order.note)

        order._compute_note()
        self.assertEqual(
            order.note.count("Goods remain our property until paid."),
            1,
        )

        noted = self.sale_order_obj.create(
            {
                "partner_id": self.partner.id,
                "note": "<p>Customer asked for a pallet.</p>",
            }
        )
        self.assertIn("Customer asked for a pallet.", noted.note)
        self.assertIn("Goods remain our property until paid.", noted.note)
        self.assertEqual(
            noted.note.count("Goods remain our property until paid."),
            1,
        )

        plain_partner = self.res_partner_obj.create({"name": "Acme Ltd"})
        plain_order = self.sale_order_obj.create({"partner_id": plain_partner.id})
        self.assertFalse(plain_order.note)

        order.partner_id = self.other_partner
        self.assertIn("Delivery at the warehouse gate.", order.note)

        self.env.company.invoice_terms = "<p>Company terms apply.</p>"
        param_obj.set_param("account.use_invoice_terms", True)
        order.partner_id = self.partner
        self.assertIn("Company terms apply.", order.note)
        self.assertIn("Goods remain our property until paid.", order.note)
        self.assertNotIn("Delivery at the warehouse gate.", order.note)
