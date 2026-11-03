from collections.abc import Callable, Iterator
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Literal, Self

from ruamel.yaml.comments import (
    C_PRE as C_PRE,
    CommentedMap as CommentedMap,
    CommentedSeq as CommentedSeq,
)
from ruamel.yaml.compat import (
    BytesIO as BytesIO,
    StringIO as StringIO,
    nprint as nprint,
    nprintf as nprintf,
)
from ruamel.yaml.constructor import (
    BaseConstructor as BaseConstructor,
    Constructor as Constructor,
    RoundTripConstructor as RoundTripConstructor,
    SafeConstructor as SafeConstructor,
)
from ruamel.yaml.docinfo import DocInfo as DocInfo, Version as Version
from ruamel.yaml.dumper import (
    BaseDumper as BaseDumper,
    Dumper as Dumper,
    RoundTripDumper as RoundTripDumper,
    SafeDumper as SafeDumper,
)
from ruamel.yaml.error import (
    UnsafeLoaderWarning as UnsafeLoaderWarning,
    YAMLError as YAMLError,
)
from ruamel.yaml.events import *
from ruamel.yaml.loader import (
    BaseLoader as BaseLoader,
    Loader as Loader,
    RoundTripLoader as RoundTripLoader,
    SafeLoader as SafeLoader,
)
from ruamel.yaml.nodes import *
from ruamel.yaml.representer import (
    BaseRepresenter as BaseRepresenter,
    Representer as Representer,
    RoundTripRepresenter as RoundTripRepresenter,
    SafeRepresenter as SafeRepresenter,
)
from ruamel.yaml.resolver import (
    Resolver as Resolver,
    VersionedResolver as VersionedResolver,
)
from ruamel.yaml.tokens import *

UnsafeLoader = Loader

# Declared here rather than re-exported: their annotations use names that
# ruamel.yaml only imports under `if False:`.
def with_metaclass(meta: type, *bases: type) -> Any: ...
def version(
    major: int | str | tuple[int, int] | None, minor: int | None = None
) -> Version | None: ...

# What load() reads from and dump() writes to. A Path is opened (and closed)
# by ruamel.yaml.
type _Input = Path | str | bytes | IO[str] | IO[bytes]
type _Output = Path | IO[str] | IO[bytes]
type _VersionInput = str | tuple[int, int] | list[int] | Version | None
type _Typ = Literal['rt', 'safe', 'base', 'unsafe', 'full', 'rtsc'] | str

class YAML:
    typ: list[str]
    pure: bool
    plug_ins: list[Any]

    # The classes that make up the pipeline; which ones depends on typ.
    Resolver: Any
    Reader: Any
    Scanner: Any
    Parser: Any
    Composer: Any
    Constructor: Any
    Representer: Any
    Serializer: Any
    Emitter: Any

    # Loading
    allow_duplicate_keys: bool
    # Round-trip only.
    preserve_quotes: bool | None
    max_depth: int

    # Dumping
    allow_unicode: bool
    # False: block style; True: flow style; None: flow for leaf collections.
    default_flow_style: bool | None
    default_style: str | None
    canonical: bool | None
    width: int | None
    line_break: str | None
    encoding: str
    explicit_start: bool | None
    explicit_end: bool | None
    map_indent: int | None
    sequence_indent: int | None
    sequence_dash_offset: int
    compact_seq_seq: bool | None
    compact_seq_map: bool | None
    # None or True sorts dict keys with the safe dumper.
    sort_base_mapping_type_on_output: bool | None
    top_level_colon_align: bool | None
    prefix_colon: str | None
    scalar_after_indicator: bool | None
    brace_single_entry_mapping_in_flow_sequence: bool
    comment_handling: int | None
    doc_infos: list[DocInfo]

    # output is the stream or Path to dump to when used as a context manager.
    def __init__(
        self,
        *,
        typ: _Typ | list[_Typ] | None = None,
        pure: bool = False,
        output: _Output | None = None,
        plug_ins: list[str] | None = None,
    ) -> None: ...
    @property
    def reader(self) -> Any: ...
    @property
    def scanner(self) -> Any: ...
    @property
    def parser(self) -> Any: ...
    @property
    def composer(self) -> Any: ...
    @property
    def constructor(self) -> BaseConstructor: ...
    @property
    def resolver(self) -> Any: ...
    @property
    def emitter(self) -> Any: ...
    @property
    def serializer(self) -> Any: ...
    # add_representer() on this changes the representer class, so it affects
    # every YAML instance of the same typ.
    @property
    def representer(self) -> BaseRepresenter: ...
    def scan(self, stream: _Input) -> Iterator[Any]: ...
    def parse(self, stream: _Input) -> Iterator[Any]: ...
    def compose(self, stream: _Input) -> Any: ...
    def compose_all(self, stream: _Input) -> Iterator[Any]: ...
    def load(self, stream: _Input) -> Any: ...
    def load_all(self, stream: _Input) -> Iterator[Any]: ...
    def emit(self, events: Any, stream: Any) -> None: ...
    def serialize(self, node: Any, stream: _Output | None) -> Any: ...
    def serialize_all(self, nodes: Any, stream: _Output | None) -> Any: ...
    # stream is required unless dumping inside `with YAML(output=...)`.
    def dump(
        self,
        data: Any,
        stream: _Output | None = None,
        *,
        transform: Callable[[str], str] | None = None,
    ) -> None: ...
    def dump_all(
        self,
        documents: Any,
        stream: _Output,
        *,
        transform: Callable[[str], str] | None = None,
    ) -> None: ...
    def map(self, **kw: Any) -> CommentedMap: ...
    def seq(self, *args: Any) -> CommentedSeq: ...
    def official_plug_ins(self) -> list[str]: ...
    def register_class[T: type](self, cls: T) -> T: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        typ: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    @property
    def version(self) -> tuple[int, int] | None: ...
    @version.setter
    def version(self, val: _VersionInput) -> None: ...
    @property
    def tags(self) -> Any: ...
    @tags.setter
    def tags(self, val: Any) -> None: ...
    # The indent property also accepts an int (old API) when assigned.
    def indent(
        self,
        mapping: int | None = None,
        sequence: int | None = None,
        offset: int | None = None,
    ) -> None: ...
    @property
    def block_seq_indent(self) -> int: ...
    @block_seq_indent.setter
    def block_seq_indent(self, val: int) -> None: ...
    def compact(
        self, seq_seq: bool | None = None, seq_map: bool | None = None
    ) -> None: ...

class YAMLContextManager:
    def __init__(
        self, yaml: YAML, transform: Callable[[str], str] | None = None
    ) -> None: ...
    def teardown_output(self) -> None: ...
    def init_output(self, first_data: Any) -> None: ...
    def dump(self, data: Any) -> None: ...

# Class decorator: registers the class with yml for dumping and loading.
def yaml_object[T: type](yml: YAML) -> Callable[[T], T]: ...

class YAMLObjectMetaclass(type): ...

class YAMLObject(metaclass=YAMLObjectMetaclass):
    yaml_constructor: Any
    yaml_representer: Any
    yaml_tag: Any
    yaml_flow_style: Any

    @classmethod
    def from_yaml(cls, constructor: Any, node: Any) -> Any: ...
    @classmethod
    def to_yaml(cls, representer: Any, data: Any) -> Any: ...
