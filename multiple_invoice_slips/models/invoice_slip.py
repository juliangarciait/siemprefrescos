# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InvoiceSlips(models.Model):
    _name = 'invoice.slips'

    number = fields.Integer()
    value = fields.Char()
