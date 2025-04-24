from collections import defaultdict

import markupsafe

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict, SQL


class AccountPaymentRegister(models.TransientModel):
    _inherit  = 'account.payment.register'


    @api.depends('line_ids')
    def _compute_batches(self):
        ''' Group the account.move.line linked to the wizard together.
        Lines are grouped if they share 'partner_id','account_id','currency_id' & 'partner_type' and if
        0 or 1 partner_bank_id can be determined for the group.

        Computes a list of batches, each one containing:
            * payment_values:   A dictionary of payment values.
            * moves:        An account.move recordset.
        '''
        for wizard in self:
            lines = wizard.line_ids._origin.sorted('id')
            print("aqui")
            print(lines)

            if len(lines.company_id.root_id) > 1:
                raise UserError(_("You can't create payments for entries belonging to different companies."))
            if not lines:
                raise UserError(_("You can't open the register payment wizard without at least one receivable/payable line."))

            batches = defaultdict(lambda: {'lines': self.env['account.move.line']})
            banks_per_partner = defaultdict(lambda: {'inbound': set(), 'outbound': set()})
            for line in lines:
                batch_key = self._get_line_batch_key(line)
                vals = batches[frozendict(batch_key)]
                vals['payment_values'] = batch_key
                vals['lines'] += line
                banks_per_partner[batch_key['partner_id']]['inbound' if line.balance > 0.0 else 'outbound'].add(
                    batch_key['partner_bank_id']
                )

            partner_unique_inbound = {p for p, b in banks_per_partner.items() if len(b['inbound']) == 1}
            partner_unique_outbound = {p for p, b in banks_per_partner.items() if len(b['outbound']) == 1}

            # Compute 'payment_type'.
            batch_vals = []
            seen_keys = set()
            for i, key in enumerate(list(batches)):
                if key in seen_keys:
                    continue
                vals = batches[key]
                lines = vals['lines']
                merge = (
                    batch_key['partner_id'] in partner_unique_inbound
                    and batch_key['partner_id'] in partner_unique_outbound
                )
                if merge:
                    for other_key in list(batches)[i + 1:]:
                        if other_key in seen_keys:
                            continue
                        other_vals = batches[other_key]
                        if all(
                            other_vals['payment_values'][k] == v
                            for k, v in vals['payment_values'].items()
                            if k not in ('partner_bank_id', 'payment_type')
                        ):
                            # add the lines in this batch and mark as seen
                            lines += other_vals['lines']
                            seen_keys.add(other_key)
                balance = sum(lines.mapped('balance'))
                vals['payment_values']['payment_type'] = 'inbound' if balance > 0.0 else 'outbound'
                if merge:
                    partner_banks = banks_per_partner[batch_key['partner_id']]
                    vals['partner_bank_id'] = partner_banks[vals['payment_values']['payment_type']]
                    vals['lines'] = lines
                batch_vals.append(vals)

            wizard.batches = batch_vals

    
    def action_create_payments(self):
        # Ordenamos las líneas a pagar por fecha
        self = self.with_context(
            active_ids=sorted(
                self._context.get('active_ids', []),
                key=lambda id: self.env['account.move'].browse(id).invoice_date or self.env['account.move'].browse(id).date
            )
        )
        return super().action_create_payments()