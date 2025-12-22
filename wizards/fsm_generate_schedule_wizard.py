from odoo import fields, models

class FSMGenerateScheduleWizard(models.TransientModel):
    _name = "fsm.generate.schedule.wizard"
    _description = "Generate next 14 days of FSM responsibles"

    default_user_id = fields.Many2one("res.users", required=True)
    overwrite = fields.Boolean(default=False)

    def action_generate(self):
        model = self.env["fsm.responsible.day"]
        today = fields.Date.context_today(self)
        for i in range(15):
            day = fields.Date.add(today, days=i)
            rec = model.search([("date", "=", day)], limit=1)
            if rec:
                if self.overwrite:
                    rec.user_id = self.default_user_id
            else:
                model.create({"date": day, "user_id": self.default_user_id.id})
        return {"type": "ir.actions.act_window", "res_model": "fsm.responsible.day", "view_mode": "tree,calendar,form"}
