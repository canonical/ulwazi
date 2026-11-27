"""Track the adoption of Ulwazi and the Sphinx Stack across Read the Docs projects.

The tool has three layers that communicate through versioned JSON files:

1. :mod:`tools.adoption.detect` lists the public Read the Docs projects and their
   repositories (``rtd-projects.json``).
2. :mod:`tools.adoption.process` applies the tracking configuration, inspects
   each repository and live site, and detects the Sphinx Stack and Ulwazi
   versions (``adoption.json`` and ``history.jsonl``).
3. :mod:`tools.adoption.render` turns ``adoption.json`` into a static dashboard.

See ``tools/adoption/README.md`` for usage.
"""

SCHEMA_VERSION = 1
USER_AGENT = (
    "ulwazi-adoption-dashboard (+https://github.com/canonical/ulwazi; "
    "documentation adoption statistics)"
)
