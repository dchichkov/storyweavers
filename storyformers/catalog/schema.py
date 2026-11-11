"""Small authoring helpers for linked attribute/head/grammar candidate records.

The catalog is data, not a trained parameter bank. Native records use the existing
neuron JSON DSL. Adapter contracts deliberately do not pretend to be executable.
"""

from copy import deepcopy


VERSION = "storyformers-catalog-v1"
CONTEXT_SIZE = 256
EXTERNAL_FIELDS = {
    "token": "string", "surface": "string", "kind": "string",
    "index": "number", "start": "number", "end": "number", "position": "object",
}


def ref(path):
    return {"$ref": path}


def present():
    return {"$present": True}


def one_of(*values):
    return {"$one_of": list(values)}


def tok(bind=None, **tests):
    result = {"kind": "token", "tests": tests}
    if bind:
        result["bind"] = bind
    return result


def seq(*children):
    return {"kind": "seq", "children": list(children)}


def gap(maximum=CONTEXT_SIZE):
    return {"kind": "repeat", "children": [tok()], "minimum": 0, "maximum": maximum}


def alt(*children):
    return {"kind": "alt", "children": list(children), "weights": [1.0] * len(children)}


def neuron(pattern, emit, *, tables=None, weight=1.0):
    return {"name": "unnamed", "rules": [{"pattern": pattern, "emit": emit, "weight": weight}],
            "tables": tables or {}, "max_states": 20000}


def rule_reads(spec):
    """Collect fields used by native tests and captured/query references."""
    fields = set()

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            if value.get("kind") == "token":
                fields.update(key.split(".")[0] for key in value["tests"])
            if "$ref" in value:
                fields.add(value["$ref"].split(".")[1])
            for item in value.values():
                visit(item)
    visit(spec)
    return sorted(fields)


class Catalog:
    """One independently authored, disjoint shard of the linked catalog."""

    def __init__(self, shard, start):
        self.shard, self.start = shard, start
        self.attributes, self.heads, self.grammars = [], [], []

    def add(self, key, type, description, family, *, value, scope,
            head, function, mechanism, positive, negative,
            native=None, contract=None, requires=(), reads=(), writes=None,
            operation="add", sources=(), values=None, aliases=(),
            evidence="derived", notes="", intervention=None):
        """Add one distinct typed field and a linked proposed producing/using rule.

        positive/negative are {context: [latent,...], expect: patch, why: prose}.
        For native negative examples expect={} means no activations, not a false
        value. Contracts additionally require match/emit/guards structured data.
        """
        if (native is None) == (contract is None):
            raise ValueError("supply exactly one of native or contract")
        n = self.start + len(self.attributes)
        aid, hid, gid = f"A{n:04d}", f"H{n:04d}", f"G{n:04d}"
        writes = list(writes or [key])
        common = dict(schema_version=VERSION, family=family, source_ids=list(sources),
                      evidence_status="authored_candidate")
        attribute = dict(common, id=aid, key=key, type=type, description=description,
                         scope=scope, nullable=True, missing_means="unknown",
                         availability="prefix_only", evidence=evidence,
                         example_value=deepcopy(value), aliases=list(aliases),
                         producer_head_ids=[hid], grammar_ids=[gid])
        if values is not None:
            attribute["values"] = list(values)
        if notes:
            attribute["notes"] = notes
        if native is not None:
            native = deepcopy(native)
            native["name"] = head[:100]
            reads = sorted(set(reads) | set(rule_reads(native)))
            support = "native"
            if requires:
                raise ValueError("native grammar cannot hide an unsupported requirement")
        else:
            reads = sorted(set(reads))
            support = "adapter_required"
            if not requires:
                raise ValueError("an adapter contract must declare required capabilities")
        grammar = dict(common, id=gid, name=head, intent=function,
                       attribute_ids=[aid], head_ids=[hid], reads=reads, writes=writes,
                       runtime_support=support, requires=list(requires),
                       causal_policy="prefix_read_current_query_write",
                       input_convention="word_and_punctuation_records",
                       examples=[dict(deepcopy(positive), polarity="positive"),
                                 dict(deepcopy(negative), polarity="contrastive")],
                       learning=dict(structure="candidate_for_data_driven_revision",
                                     weights="positive_rule_mass_initially_1",
                                     statistics=["support", "false_activation", "joint_target_loss_delta",
                                                 "attribute_agreement", "scope_conflicts"]),
                       ambiguity_notes=notes)
        grammar["neuron" if native is not None else "contract"] = native or deepcopy(contract)
        head_record = dict(common, id=hid, name=head, function=function, mechanism=mechanism,
                           attribute_ids=[aid], grammar_ids=[gid], reads=reads, writes=writes,
                           operation=operation, write_target="current_query",
                           runtime_support=support, requires=list(requires),
                           routing="candidate_for_top1_or_noop; current_runtime_sums_derivations",
                           query="last visible latent of the causal prefix",
                           evaluation=dict(examples_in=gid, intervention=intervention or
                               f"Ablate this head and compare held-out joint latent loss and {key} accuracy."))
        self.attributes.append(attribute)
        self.heads.append(head_record)
        self.grammars.append(grammar)
        return aid, hid, gid

    def records(self):
        return {"attributes": self.attributes, "heads": self.heads, "grammars": self.grammars}


def example(context, expect, why):
    return {"context": context, "expect": expect, "why": why}
