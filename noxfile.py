# Import built-in modules
import os
import sys

# Import third-party modules
import nox

ROOT = os.path.dirname(__file__)

# Ensure pypi_query_mcp is importable.
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import local modules (after sys.path setup)
from nox_actions import codetest, lint, release  # noqa: E402

# Configure nox sessions
nox.session(lint.lint, name="lint")
nox.session(lint.lint_fix, name="lint-fix")
nox.session(codetest.pytest, name="pytest")
nox.session(codetest.mypy, name="mypy")
nox.session(codetest.safety, name="safety")
nox.session(release.build, name="build")
