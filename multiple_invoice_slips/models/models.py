# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_slip = fields.Integer(default_model='account.move', string="No. of Invoice Slip", default=1)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = (self.env['ir.config_parameter'].sudo())
        res.update(
            invoice_slip=int(ICPSudo.get_param('multiple_invoice_slips.invoice_slip')),
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        if self.invoice_slip:
            self.env['ir.config_parameter'].sudo().set_param('multiple_invoice_slips.invoice_slip',
                                                             self.invoice_slip)
        return res


class InvoicingInherit(models.Model):
    _inherit = 'account.move'

    def get_num_of_slips(self):
        partner_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'multiple_invoice_slips.invoice_slip') or False
        return int(partner_invoice)

    def get_num_text(self, num):
        if num:
            val = self.env['invoice.slips'].search([('number', '=', num)])
            if val:
                return val.value
