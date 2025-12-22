from odoo import api, fields, models

class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _is_fsm_task_activity(self, vals=None):
        res_model = vals.get("res_model") if vals else self.res_model
        if res_model != "project.task":
            return False
        res_id = vals.get("res_id") if vals else self.res_id
        if not res_id:
            return False
        task = self.env["project.task"].browse(res_id).exists()
        return bool(task and task.project_id.is_fsm)

    def _resolve_responsible_user_for_date(self, date_deadline):
        fsm_day = self.env["fsm.responsible.day"]
        return fsm_day.get_responsible_for_date(date_deadline or fields.Date.context_today(self))

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("fsm_activity_assign_bypass"):
            return super().create(vals_list)
        updated = []
        for vals in vals_list:
            vals = dict(vals)
            if self._is_fsm_task_activity(vals):
                resp = self._resolve_responsible_user_for_date(vals.get("date_deadline"))
                if resp:
                    vals["user_id"] = resp.id
            updated.append(vals)
        return super().create(updated)

    def write(self, vals):
        if not self.env.context.get("fsm_activity_assign_bypass") and ("date_deadline" in vals or "res_id" in vals):
            for act in self:
                data = {"res_model": vals.get("res_model", act.res_model), "res_id": vals.get("res_id", act.res_id), "date_deadline": vals.get("date_deadline", act.date_deadline)}
                if self._is_fsm_task_activity(data):
                    resp = self._resolve_responsible_user_for_date(data["date_deadline"])
                    if resp:
                        vals = dict(vals, user_id=resp.id)
        return super().write(vals)

    @api.model
    def _cron_fsm_realign_upcoming(self):
        today = fields.Date.context_today(self)
        end = fields.Date.add(today, days=14)
        acts = self.search([("res_model", "=", "project.task"), ("date_deadline", ">=", today), ("date_deadline", "<=", end)])
        Task = self.env["project.task"]
        fsm_acts = acts.filtered(lambda a: Task.browse(a.res_id).project_id.is_fsm if a.res_id else False)
        fsm_day = self.env["fsm.responsible.day"]
        for d in set(fsm_acts.mapped("date_deadline")):
            resp = fsm_day.get_responsible_for_date(d)
            if resp:
                fsm_acts.filtered(lambda a: a.date_deadline == d).write({"user_id": resp.id})
        return True
