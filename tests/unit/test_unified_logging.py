"""Legacy unit tests for unified logging system.

The unified logging implementation has been significantly refactored; these
tests target obsolete APIs (`CorrelationContext`, internal DatabaseLogger).
The entire module is therefore skipped during the legacy-removal phase.
"""

import pytest

pytest.skip("Skipping legacy unified logging tests during cleanup", allow_module_level=True)
