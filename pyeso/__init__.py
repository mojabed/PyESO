"""PyESO — ESO Addon Linter.

    from pyeso import ESOLinter

    linter = ESOLinter()
    diags = linter.lint_file("MyAddon.lua")
    diags = linter.lint_directory("MyAddon/")
"""

__version__ = "0.1.0"

from pyeso.linter import ESOLinter
