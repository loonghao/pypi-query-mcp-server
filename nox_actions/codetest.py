# Import built-in modules
import os

# Import third-party modules
import nox

from nox_actions.utils import PACKAGE_NAME, THIS_ROOT


def pytest(session: nox.Session) -> None:
    """Run pytest with coverage reporting."""
    session.install(".")
    session.install("pytest", "pytest-cov", "pytest-mock", "pytest-asyncio")
    test_root = os.path.join(THIS_ROOT, "tests")
    session.run("pytest", f"--cov={PACKAGE_NAME}",
                "--cov-report=xml:coverage.xml",
                "--cov-report=term-missing",
                f"--rootdir={test_root}",
                env={"PYTHONPATH": THIS_ROOT.as_posix()})


def mypy(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.install(".")
    session.install("mypy", "types-requests")
    session.run("mypy", PACKAGE_NAME, "--ignore-missing-imports")


def safety(session: nox.Session) -> None:
    """Run safety security checks."""
    session.install(".")
    session.install("safety")
    session.run("safety", "check", "--json")
