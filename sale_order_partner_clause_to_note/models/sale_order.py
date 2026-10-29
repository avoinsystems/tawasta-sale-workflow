from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        result = super().onchange_partner_id()

        partner = self.partner_id
        sale_clause = partner.sale_clause

        if partner and sale_clause and sale_clause.used_for == "sale":
            if self.note:
                self.note += "{}{}".format("\n", sale_clause.clause)
            else:
                self.note += "{}".format(sale_clause.clause)

        return result

    def create(self, vals):
        partner_id = vals.get("partner_id")
        partner = self.env["res.partner"].search([("id", "=", partner_id)])

        if partner and partner.sale_clause and partner.sale_clause.used_for == "sale":
            if vals.get("note"):
                vals["note"] += "{}{}".format("\n", partner.sale_clause.clause)
            else:
                vals["note"] = "{}".format(partner.sale_clause.clause)

        return super().create(vals)
