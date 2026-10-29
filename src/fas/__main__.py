"""Allow ``python -m fas``."""

import sys

from .cli import main

sys.exit(main())
