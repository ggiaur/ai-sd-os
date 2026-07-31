"""Single source of truth for the motor's own version.

Every place that needs to display or reference the engine version (CLI banner,
README, future release tooling) must import this instead of hardcoding a
string — that mismatch (CLI banner said "V5" while README said "V6.1.0") is
exactly the kind of drift proper version control is supposed to prevent.

Bump this, and add a CHANGELOG.md entry, whenever kernel/, agents/, contracts/,
or sdk/ change in a way a user of the engine (not a generated project) would
care about. See CONTRIBUTING.md.
"""

__version__ = "6.1.0"
