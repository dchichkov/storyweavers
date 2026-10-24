"""Bounded second looks and divided loads using the existing effect writers."""
from dataclasses import replace

from .capabilities.core import Action, Entity, Query
from .capabilities.epistemic import Exposure
from .capabilities.physical import Parent


SPLIT_STEPS = (
    ("lift_part_one", "pickup", "clue", "crate"),
    ("park_part_one", "put", "clue", "bench"),
    ("lift_part_two", "pickup", "second_slab", "crate"),
    ("park_part_two", "put", "second_slab", "cart"),
    ("lift_empty", "pickup", "crate", "workshop"),
    ("load_empty", "put", "crate", "cart"),
    ("fetch_part_one", "pickup", "clue", "bench"),
    ("pack_part_one", "put", "clue", "crate"),
    ("fetch_part_two", "pickup", "second_slab", "cart"),
    ("pack_part_two", "put", "second_slab", "crate"),
)


def decision(state):
    get = state.maybe if hasattr(state, "maybe") else state.get
    return get("dispositions", "recheck") or state.get("dispositions", "decision")


def extend(spec, c):
    records = dict(spec.records)
    actions = list(spec.actions)
    def q(table, key, field, value):
        return Query(table=table, key=key, field=field, value=value)
    def add(id, operation, actor="ari", *, requires=(), **args):
        actions.append(Action(id=id, operation=operation, actor=actor, args=args, requires=requires))

    if c.kind == "load" and c.actual:
        records["entities"] = tuple(replace(e, name="the first stone slab", mass=10) if e.id == "clue" else e
                                    for e in records["entities"])
        records["entities"] += (Entity(id="second_slab", name="the second stone slab", kind="object", mass=10),)
        records["parents"] += (Parent(id="second_slab", parent="crate"),)
        declined = (q("requests", "help", "response", "declined"),)
        for id, operation, object, place in SPLIT_STEPS:
            add(id, operation, object=object, requires=declined,
                **({"source": place} if operation == "pickup" else {"destination": place}))

    if not c.readable and c.kind != "shortcut":
        source = "crate" if c.kind in {"load", "parcel"} else "workshop"
        records["parents"] = tuple(replace(p, parent=source) if p.id == "cover" else p for p in records["parents"])
        records["exposures"] += (Exposure(id="uncovered", fact="check"),)
        deferred = (q("dispositions", "decision", "mode", "defer"),)
        add("peel_take", "pickup", object="cover", source=source, requires=deferred)
        add("peel_place", "put", object="cover", destination="bench", requires=deferred)
        observer = "cy" if c.reported else "ari"
        add("reinspect", "observe", observer, fact="check", exposure="uncovered", attention=observer,
            channel="eyes", evidence="reseen", requires=deferred + (q("parents", "cover", "parent", "bench"),))
        add("reexplain", "speak", "cy", audience="ari", channel="voice", evidence="reseen", claim="reexplanation")
        add("rehear", "deliver", "ari", claim="reexplanation", receipt="reheard")
        add("reunderstand", "comprehend", "ari", receipt="reheard", comprehension="reunderstood")
        basis = dict(comprehension_ids=("reunderstood",)) if c.reported else dict(evidence_ids=("reseen",))
        for mode in ("adopt", "resolve"):
            add("re" + mode, "update_belief", disposition="recheck", head="ari_view", predecessor="prior",
                mode=mode, policy="trust_cy" if c.reported else "look", proposition="reseen:proposition", **basis)
        # Only downstream decisions use the second look. Preserve the first
        # evidence, its unknown proposition, its communication and its deferral.
        downstream = {"accept", "withdraw", "refuse", "self_take", "self_load", "cut", "untie", "take_opened", "place_opened", "undo_take", "say_decision"}
        adjusted = []
        for action in actions:
            if action.id in downstream:
                guards = tuple(replace(g, key="recheck") if g.table == "dispositions" and g.key == "decision" else
                               replace(g, key="reseen:proposition") if g.table == "propositions" and g.key == "seen:proposition" else g
                               for g in action.requires)
                action = replace(action, requires=guards)
                if action.id == "say_decision":
                    action = replace(action, args=dict(action.args, belief="recheck:belief"))
            adjusted.append(action)
        actions = adjusted
    return replace(spec, records=records, actions=tuple(actions), max_steps=90)


def second_look(c, state, step):
    if not c.recover or c.kind == "shortcut" or state.get("evidence", "seen").outcome == "exact":
        return state
    for action in ("peel_take", "peel_place", "reinspect"):
        state = step(action)
    if c.reported:
        for action in ("reexplain", "rehear", "reunderstand"):
            state = step(action)
    evidence = state.get("evidence", "reseen")
    result = state.get("propositions", evidence.proposition).result
    prior = state.get("propositions", "assumption").result.value
    return step("readopt" if result.value == prior else "reresolve")


def divide(step):
    for id, *_ in SPLIT_STEPS:
        step(id)


def require_divided_load(tx):
    tx.require(tx.get("parents", "crate").parent == "cart" and
               all(tx.get("parents", part).parent == "crate" for part in ("clue", "second_slab")),
               "The empty crate and both slabs must actually arrive and be repacked")
    for id, *_ in SPLIT_STEPS:
        tx.depend(id + ":1")


def add_second_look(add, state):
    evidence = state.get("evidence", "reseen")
    if evidence is None:
        return
    kind = state.get("harbor_jobs", "ari").kind
    value = state.get("propositions", evidence.proposition).result.value
    observer = "Cy" if evidence.observer == "cy" else "Ari"
    reveal = {
        ("load", True): "two stone slabs, each with a clear edge Ari could grip",
        ("load", False): "the bare wooden bottom, without a single stone",
        ("parcel", True): "paper cups nested together",
        ("parcel", False): "paint tins where Ari had expected cups",
        ("tool", True): "a sealed band with no loose end",
        ("tool", False): "the loose end of a bow",
    }[(kind, value)]
    text = 'Ari caught a free corner of the wrapping. "This part is not tied," Ari said, and lifted it away onto the bench. '
    text += f'With it out of the way, {observer} could see {reveal}.'
    add("reinspection", text, "What made a second inspection useful?",
        f"Ari physically removed the covering and put it on the bench. {observer} could then see {reveal}.",
        "peel_take", "peel_place", "reinspect")
    if evidence.observer == "cy":
        subject = "fastening" if kind == "tool" else "contents"
        add("rereport", 'Cy described what was underneath. Ari listened. "That is a different answer."\n"I can see more now," Cy said.',
            "How did Ari learn what the second inspection found?",
            f"Cy described the newly visible {subject}, and Ari heard and understood the report. Ari's changed plan followed that second report, not a guess about the hidden object.",
            "reexplain", "rehear", "reunderstand")


def divided_scene():
    return (
        'Ari looked at the two slabs. "You cannot carry them for me."\n"Not now," Cy said.\n'
        '"But I do not have to carry them together." Ari put one slab on the bench and the other on the cart. '
        'The empty crate came up easily. Once it was on the cart, Ari fetched the slabs and packed them back inside, one at a time. '
        'There were more lifts this way. At the last one, Ari let out a long breath.\n"Still the same stones," Cy said.\n"A smaller job each time," Ari answered.',
        "Ari moved the two slabs separately, loaded the emptied crate and repacked both slabs on the cart. Cy did not carry the refused load; Ari completed it through several smaller lifts.",
        "The cart held both stone slabs in their crate. The crate's old place on the workshop floor was empty.",
    )
