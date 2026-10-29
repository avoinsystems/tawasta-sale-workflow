from odoo import api, models
from odoo.tools.mail import append_content_to_html, is_html_empty, plaintext2html


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _compute_note(self):
        super()._compute_note()
        for order in self:
            order.note = order._note_with_partner_sale_clause(order.note)

    @api.model_create_multi
    def create(self, vals_list):
        partners = {
            partner.id: partner
            for partner in self.env["res.partner"].browse(
                [
                    vals["partner_id"]
                    for vals in vals_list
                    if vals.get("partner_id") and "note" in vals
                ]
            )
        }
        for vals in vals_list:
            partner = partners.get(vals.get("partner_id"))
            if not partner or "note" not in vals:
                continue
            vals["note"] = self._note_with_partner_sale_clause(
                vals.get("note"), partner
            )
        return super().create(vals_list)

    def _note_with_partner_sale_clause(self, note, partner=None):
        partner = self.partner_id if partner is None else partner
        clause = partner.sale_clause
        if not clause or clause.used_for != "sale" or not clause.clause:
            return note
        clause_html = plaintext2html(clause.clause)
        if is_html_empty(note):
            return clause_html
        note_html = str(note)
        if str(clause_html) in note_html:
            return note
        return append_content_to_html(note_html, clause.clause)
