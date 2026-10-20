# Las Palmas adaptation

This directory is the fork-specific layer. Keep upstream files unchanged wherever
possible. Never deploy to Juanjo's NAS, IONOS, Telegram bots or public repositories.
Use `python3 -m unittest discover -s lpa/tests -v` and the upstream test suite.
Build with `python3 -m lpa.build /tmp/meteo-lpa`. Run browser and accessibility
checks against the generated site. Use the independent LPA version in profile.py;
do not create upstream release tags. No training data from Montflorit may be used.
A missing regional provider must remain unavailable, never an empty success.
