# Copyright (C) 2020 - SUNNIT dev@sunnit.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging
import threading

from odoo.addons.mass_mailing_base.tools import helpers

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SmsSms(models.Model):
    _inherit = 'sms.sms'

    message_id = fields.Char(string="SMS ID")

    state = fields.Selection(
        selection_add=[
            ('received', 'Received'),
            ('read', 'Read'),
        ]
    )

    message_type = fields.Selection(
        string="Message Type",
        selection=[
            ('sms', 'SMS Phone'),
            ('whatsapp', 'WhatsApp'),
        ],
    )

    type = fields.Selection(
        string="SMS Type",
        selection=[
            ('input', 'Received'),
            ('output', 'Sent'),
        ],
        default="output",
    )

    error_message = fields.Char(
        string="Error Message",
    )

    scheduled_date = fields.Char(
        string='Scheduled Send Date',
        help="If set, the queue manager will send the email after the date."
             " If not set, the email will be send as soon as possible.",
    )

    @api.model
    def _process_queue(self, ids=None):
        """ Melhorar domínio para não enviar com data agendada o SMS """

        domain = ['&',
                 ('state', '=', 'outgoing'),
                 '|',
                 ('scheduled_date', '<', datetime.datetime.now()),
                 ('scheduled_date', '=', False)]

        filtered_ids = self.search(domain, limit=10000).ids

        if ids:
            ids = list(set(filtered_ids) & set(ids))
        else:
            ids = filtered_ids
        ids.sort()

        res = None
        try:
            # auto-commit except in testing mode
            auto_commit = not getattr(threading.currentThread(), 'testing', False)
            res = self.browse(ids).send(delete_all=False, auto_commit=auto_commit, raise_exception=False)
        except Exception:
            _logger.exception("Failed processing SMS queue")
        return res

    @api.model
    def create(self, values):
        sms_id = super(SmsSms, self).create(values)
        if sms_id.mail_message_id and sms_id.mail_message_id.message_type:
            sms_id.message_type = sms_id.mail_message_id.message_type
        return sms_id

    def create_mail_message(self, model, partner_id=False):
        """Criar mail message no modelo"""
        mail_message_model = self.env['mail.message'].sudo()

        message = mail_message_model.create({
            'subject': 'Message',
            'body': self.body,
            'res_id': model.id,
            'model': model._name,
            'message_type':
                self.message_type if partner_id else "notification",
            "message_id": self.id,
            'email_from': partner_id.email if partner_id else False,
            'author_id': partner_id.id if partner_id else False,
        })
        return message or False

    def find_and_attach_to_lead(self):
        """ Buscar Lead/partner para anexar mensagem de entrada"""

        res_partner_model = self.env['res.partner'].sudo()
        crm_lead_model = self.env['crm.lead'].sudo()

        lead_id = helpers.get_record_from_number(crm_lead_model, self.number)

        # Se já existe uma LEAD, adiciona SMS na thread de comunicação
        if lead_id:
            message = self.create_mail_message(
                model=lead_id,
                partner_id=lead_id.partner_id,
            )

        # Senão, buscar pelo partner e gerar nova LEAD
        else:
            partner_id = helpers.get_record_from_number(
                res_partner_model, self.number)
            if partner_id:

                # Imitate what happens in the controller when somebody
                # creates a new lead from the website form
                lead_id = crm_lead_model.with_context(
                    mail_create_nosubscribe=True).create({
                    "name": "New LEAD from {}".format(self.message_type),
                    "partner_id": partner_id.id,
                    "partner_name": partner_id.name,
                })

                message = self.create_mail_message(
                    model=lead_id,
                    partner_id=lead_id.partner_id,
                )

            # Senão gerar LEAD sem partner mas com numero setado
            else:

                lead_id = self.env['crm.lead'].with_context(
                    mail_create_nosubscribe=True).sudo().create({
                    "name": "New LEAD from {}".format(self.number),
                    "mobile": self.number,
                })
                message = self.create_mail_message(model=lead_id)

        self.mail_message_id = message
        return message
