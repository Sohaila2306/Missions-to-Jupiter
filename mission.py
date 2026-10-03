"""Mission definition: Galileo."""

MISSION = {
    "name": "Galileo",
    "events": [
        {"label": "Launch (STS-34)", "body": "Earth", "date": "1989-10-18"},
        {"label": "Venus flyby", "body": "Venus", "date": "1990-02-10"},
        {"label": "Earth flyby 1", "body": "Earth", "date": "1990-12-08", "revs": 1, "resonant": True},
        {"label": "Earth flyby 2", "body": "Earth", "date": "1992-12-08"},
        {"label": "Jupiter arrival", "body": "Jupiter", "date": "1995-12-07"},
    ],
}
