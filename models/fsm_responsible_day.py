from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

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
