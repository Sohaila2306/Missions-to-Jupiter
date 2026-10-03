"""Mission definition: Juno."""

MISSION = {
    "name": "Juno",
    "events": [
        {"label": "Launch", "body": "Earth", "date": "2011-08-05", "revs": 1, "branch": 0},
        {"label": "Earth flyby", "body": "Earth", "date": "2013-10-09"},
        {"label": "Jupiter orbit insertion", "body": "Jupiter", "date": "2016-07-05"},
    ],
}
