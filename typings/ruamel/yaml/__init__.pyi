# Only __init__ and main are stubbed: ruamel.yaml declares its stream and
# version types under `if False:`, which leaves YAML.load/dump and friends
# partially Unknown. Pyright falls back to the library for the other modules.
from typing import Final

from ruamel.yaml.cyaml import *
from ruamel.yaml.main import *

version_info: Final[tuple[int, int, int]]
__version__: Final[str]
__with_libyaml__: Final[bool]
