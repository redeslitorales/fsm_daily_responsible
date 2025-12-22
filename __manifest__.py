{
    "name": "FSM Daily Responsible (2-week scheduler)",
    "summary": "Assign the daily responsible for Field Service activities; auto-assign FSM activities by date.",
    "version": "17.0.1.0.0",
    "author": "Redes Litorales SA de CV",
    "license": "LGPL-3",
    "category": "Services/Field Service",
    "depends": ["industry_fsm", "project", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/fsm_responsible_views.xml",
        "data/ir_cron.xml"
    ],
    "application": False,
    "installable": True
}
