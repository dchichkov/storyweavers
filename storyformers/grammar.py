"""Small weighted attribute grammars: match context, bind records, project values.

No eval, external parser or model. The same neuron emits residual patches or
complete output bundles. Patterns consume the entire supplied context; Search
and Gap make selective, nonlocal context matching explicit.
"""

from copy import deepcopy
from dataclasses import dataclass, field, fields, is_dataclass
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def positive(value, name, *, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise ValueError(f"{name} must be finite and {'nonnegative' if zero else 'positive'}")


@dataclass(frozen=True)
class Ref:
    path: str


@dataclass(frozen=True)
class Lookup:
    table: str
    key: object


@dataclass(frozen=True)
class OneOf:
    values: tuple


@dataclass(frozen=True)
class Present:
    """An explicit non-null feature, not an unknown treated as a wildcard."""


def resolve(value, bindings, tables):
    if isinstance(value, Ref):
        result = bindings
        for key in value.path.split("."):
            result = result[int(key)] if isinstance(result, (list, tuple)) else result[key]
        return deepcopy(result)
    if isinstance(value, Lookup):
        key = resolve(value.key, bindings, tables)
        key = key if isinstance(key, str) else canonical(key)
        return deepcopy(tables[value.table][key])
    if isinstance(value, dict):
        return {k: resolve(v, bindings, tables) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [resolve(v, bindings, tables) for v in value]
    return deepcopy(value)


@dataclass(frozen=True)
class Pattern:
    kind: str
    children: tuple = ()
    tests: dict = field(default_factory=dict)
    bind: str | None = None
    weights: tuple = ()
    minimum: int = 0
    maximum: int = 256

    def __post_init__(self):
        if self.kind not in {"token", "seq", "alt", "repeat"}:
            raise ValueError("unknown grammar pattern")
        if self.kind == "alt":
            if not self.children or len(self.children) != len(self.weights):
                raise ValueError("Alt needs one weight per alternative")
            for weight in self.weights:
                positive(weight, "alternative weight")
        if self.kind == "repeat" and (len(self.children) != 1 or type(self.minimum) is not int or type(self.maximum) is not int or not 0 <= self.minimum <= self.maximum):
            raise ValueError("Repeat needs one child and finite integer bounds")
        if self.bind == "query":
            raise ValueError("query is a reserved binding")


def Token(bind=None, **tests):
    return Pattern("token", tests=tests, bind=bind)


def Seq(*patterns):
    return Pattern("seq", children=patterns)


def Alt(*patterns, weights=None):
    return Pattern("alt", children=patterns, weights=tuple(weights) if weights is not None else (1.,) * len(patterns))


def Repeat(pattern, minimum=0, maximum=256):
    return Pattern("repeat", children=(pattern,), minimum=minimum, maximum=maximum)


def Gap(maximum=256):
    return Repeat(Token(), maximum=maximum)


def Search(pattern):
    return Seq(Gap(), pattern, Gap())


@dataclass
class Rule:
    pattern: Pattern
    emit: dict
    weight: float = 1.

    def __post_init__(self):
        positive(self.weight, "rule weight")
        if not isinstance(self.emit, dict):
            raise ValueError("a rule projects a dictionary")


@dataclass(frozen=True)
class Activation:
    value: dict
    mass: float
    rule: int
    sources: dict


class MatchBudgetExceeded(RuntimeError):
    pass


@dataclass
class GrammarNeuron:
    name: str
    rules: tuple = ()
    tables: dict = field(default_factory=dict)
    max_states: int = 20000

    def __post_init__(self):
        if not self.name or type(self.max_states) is not int or self.max_states < 1:
            raise ValueError("neurons need a name and positive match budget")

    def activate(self, context):
        """Return all weighted projecting matches; a missing binding/KV abstains.

        Captures bind terminal records. Shared NP patterns can capture their
        head terminal. Binding the same name twice requires record equality.
        """
        visited = 0

        def walk(pattern, at, bindings, sources, mass):
            nonlocal visited
            visited += 1
            if visited > self.max_states:
                raise MatchBudgetExceeded(f"{self.name}: exceeded {self.max_states} matching states")
            if pattern.kind == "token":
                if at >= len(context):
                    return
                record = context[at]
                try:
                    for path, expected in pattern.tests.items():
                        actual = resolve(Ref("record." + path), {"record": record}, {})
                        if isinstance(expected, Present):
                            matches = actual is not None
                        elif isinstance(expected, OneOf):
                            matches = any(canonical(actual) == canonical(value) for value in expected.values)
                        else:
                            matches = canonical(actual) == canonical(resolve(expected, bindings, self.tables))
                        if not matches:
                            return
                except (KeyError, IndexError):
                    return
                if pattern.bind:
                    if pattern.bind in bindings and canonical(bindings[pattern.bind]) != canonical(record):
                        return
                    bindings = {**bindings, pattern.bind: record}
                    sources = {**sources, pattern.bind: record.get("position", {"token": at})}
                yield at + 1, bindings, sources, mass
            elif pattern.kind == "seq":
                def sequence(index, state):
                    if index == len(pattern.children):
                        yield state
                    else:
                        for next_state in walk(pattern.children[index], *state):
                            yield from sequence(index + 1, next_state)
                yield from sequence(0, (at, bindings, sources, mass))
            elif pattern.kind == "alt":
                total = math.fsum(pattern.weights)
                for child, weight in zip(pattern.children, pattern.weights):
                    yield from walk(child, at, bindings, sources, mass * weight / total)
            else:
                def repeat(count, state):
                    if count >= pattern.minimum:
                        yield state
                    if count < pattern.maximum:
                        for next_state in walk(pattern.children[0], *state):
                            if next_state[0] == state[0]:
                                raise ValueError("Repeat cannot contain a nullable pattern")
                            yield from repeat(count + 1, next_state)
                yield from repeat(0, (at, bindings, sources, mass))

        result = []
        for index, rule in enumerate(self.rules):
            positive(rule.weight, "rule weight")
            bindings = {"query": context[-1] if context else {}}
            for end, captured, sources, mass in walk(rule.pattern, 0, bindings, {}, rule.weight):
                if end != len(context):
                    continue
                try:
                    value = resolve(rule.emit, captured, self.tables)
                except (KeyError, IndexError):
                    continue
                canonical(value)  # Require finite, serializable projected values.
                result.append(Activation(value, mass, index, deepcopy(sources)))
        return result


_TYPES = {cls.__name__: cls for cls in (Ref, Lookup, OneOf, Present, Pattern, Rule, GrammarNeuron)}


def register_types(*classes):
    _TYPES.update({cls.__name__: cls for cls in classes})


def pack(value, memo=None):
    """Explicit JSON AST; checkpoints never deserialize executable code."""
    memo = {} if memo is None else memo
    if is_dataclass(value):
        if id(value) in memo:
            return {"$ref": memo[id(value)]}
        identity = memo[id(value)] = len(memo)
        return {"$type": type(value).__name__, "$id": identity,
                **{f.name: pack(getattr(value, f.name), memo) for f in fields(value)}}
    if isinstance(value, dict):
        return {"$map": {k: pack(v, memo) for k, v in value.items()}}
    if isinstance(value, (list, tuple)):
        return [pack(v, memo) for v in value]
    return value


def unpack(value, memo=None):
    memo = {} if memo is None else memo
    if isinstance(value, list):
        return [unpack(v, memo) for v in value]
    if isinstance(value, dict):
        if "$ref" in value:
            return memo[value["$ref"]]
        if "$map" in value:
            return {k: unpack(v, memo) for k, v in value["$map"].items()}
        if "$type" in value:
            result = _TYPES[value["$type"]](**{k: unpack(v, memo) for k, v in value.items() if k not in {"$type", "$id"}})
            memo[value["$id"]] = result
            return result
        raise ValueError("malformed grammar checkpoint object")
    return value
