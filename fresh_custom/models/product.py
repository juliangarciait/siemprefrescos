from odoo import models, api

import logging
import lxml as etree


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == 'search' and view_id == self.env.ref("stock.product_search_form_view_stock_report").id:
            search_xml = etree.etree.XML(res.get("arch"))
            filter_element = etree.etree.Element("filter")
            filter_element.set("string", "User location")
            filter_element.set("name", "filter_user_location")
            # import pdb;pdb.set_trace()
            domain = [("property_stock_inventory", "=", self.env.user.default_warehouse_id.id)]
            filter_element.set("domain", str(domain))
            search_xml.append(filter_element)
            res["arch"] = etree.etree.tostring(search_xml)
            # for node in arch.xpath("//filter[-1]"):
            print(options)
        return res
