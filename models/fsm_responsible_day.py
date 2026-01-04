import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class FSMResponsibleDay(models.Model):
    _name = "fsm.responsible.day"
    _description = "FSM Daily Responsible"
    _order = "date"
    _sql_constraints = [("date_unique", "unique(date)", "Only one responsible per day.")]

    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    user_id = fields.Many2one("res.users", string="Responsible", required=True)

    @api.constrains("date")
    def _check_date(self):
        today = fields.Date.context_today(self)
        limit = fields.Date.add(today, days=14)
        for rec in self:
            if not today <= rec.date <= limit:
                raise ValidationError(_("Date %s must be between %s and %s.") % (rec.date, today, limit))

    @api.model
    def get_responsible_for_date(self, target_date=None):
        target_date = target_date or fields.Date.context_today(self)
        rec = self.search([("date", "=", target_date)], limit=1)
        return rec.user_id if rec else False

    def _reassign_activities_for_date(self, date):
        responsible = self.get_responsible_for_date(date)
        if not responsible:
            return
        acts = self.env["mail.activity"].search([("date_deadline", "=", date), ("res_model", "=", "project.task")])
        fsm_acts = acts.filtered(lambda a: self.env["project.task"].browse(a.res_id).project_id.is_fsm if a.res_id else False)
        fsm_acts.write({"user_id": responsible.id})

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ("date", "user_id")):
            for rec in self:
                self._reassign_activities_for_date(rec.date)
        return res

    @api.model
    def _cron_fsm_responsible_coverage_check(self):
        today = fields.Date.context_today(self)
        upcoming_dates = [fields.Date.add(today, days=offset) for offset in range(7)]
        existing_dates = set(self.search([("date", "in", upcoming_dates)]).mapped("date"))
        missing_dates = sorted(set(upcoming_dates) - existing_dates)
        if not missing_dates:
            return True
        group = self.env.ref("fsm_daily_responsible.group_fsm_responsible_admin", raise_if_not_found=False)
        if not group:
            _logger.warning("FSM Responsible admin group not found; cannot send missing coverage alert.")
            return True
        emails = [user.email for user in group.users if user.email]
        if not emails:
            _logger.warning("FSM Responsible admin group has no users with email addresses.")
            return True
        body = _(
            "The following dates do not have an assigned daily FSM responsible: %s.<br/>"
            "Please assign a user today in the Daily FSM Responsible schedule."
        ) % ", ".join(fields.Date.to_string(d) for d in missing_dates)
        mail_from = self.env['ir.config_parameter'].sudo().get_param('mail.default.from') or 'administracion@redeslitorales.com'
        mail = self.env["mail.mail"].create(
            {
                "subject": _("FSM Responsible coverage is missing for the next 7 days"),
                "body_html": body,
                "email_to": ",".join(emails),
                "reply_to": mail_from,
                "email_from": mail_from,
            }
        )
        mail.send()
        return True
