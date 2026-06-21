#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/attach_prohibit_inner_monologue_repetition_heartwarming.py
==========================================================================================

A standalone storyworld for a tiny heartwarming domain: a child wants to attach
something precious to something special, an adult prohibits a risky step, the
child thinks it through in inner monologue, repeats the warning to themself, and
the story resolves with a safe, caring choice.

The world is intentionally small and classical:
- a child
- a grown-up
- a cherished item that can be attached
- a gentle rule that can be prohibited
- one safe alternative that preserves the heartwarming feeling

The prose is driven by world state, not a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MONOLOGUE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    attachable: bool = False
    prohibited: bool = False
    safe_alternative: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    feels: str
    place: str
    attach_kind: str
    can_attach: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    item: str
    object: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


CHILDREN = [
    ("Mia", "girl"),
    ("Lily", "girl"),
    ("Nora", "girl"),
    ("Owen", "boy"),
    ("Theo", "boy"),
    ("Ben", "boy"),
]

PARENTS = [("Mom", "mother"), ("Dad", "father")]

OBJECTS = {
    "gift": ObjectSpec("gift", "gift box", "a little gift box", "careful", "the table", "a ribbon"),
    "lantern": ObjectSpec("lantern", "lantern", "a paper lantern", "bright", "the shelf", "a string"),
    "photo": ObjectSpec("photo", "photo frame", "a family photo frame", "tender", "the mantel", "a gold clip"),
}

ATTACHMENTS = {
    "ribbon": "a soft red ribbon",
    "sticker": "a round star sticker",
    "tag": "a tiny name tag",
}

SAFE_ALTERNATIVES = {
    "bow": "tie a bow",
    "place": "place it beside the present",
    "draw": "draw a heart on the card",
}


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    obj = world.get("object")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("worry", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["thinking"] += 1
    if obj.attachable:
        out.append("__worry__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["thinking"] < THRESHOLD or parent.memes["kindness"] < THRESHOLD:
        return out
    sig = ("soften", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("soften", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(obj: ObjectSpec, attachment: str) -> bool:
    return obj.can_attach and attachment in ATTACHMENTS


def asp_facts() -> str:
    import asp
    lines = []
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.can_attach:
            lines.append(asp.fact("attachable", oid))
    for aid in ATTACHMENTS:
        lines.append(asp.fact("attachment", aid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(O, A) :- object(O), attachment(A), attachable(O).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for oid, obj in OBJECTS.items():
        for aid in ATTACHMENTS:
            if reasonableness_gate(obj, aid):
                combos.append((oid, aid))
    return combos


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, role="parent"))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=params.item, attachable=True))
    obj = world.add(Entity(id="object", kind="thing", type="thing", label=params.object))

    world.facts.update(child=child, parent=parent, item=item, obj=obj)

    child.memes["want"] += 1
    parent.memes["kindness"] += 1

    world.say(
        f"One bright morning, {child.id} found {OBJECTS[params.item].phrase} beside the window, "
        f"and {child.pronoun('possessive')} eyes sparkled."
    )
    world.say(
        f"{child.id} wanted to attach {ATTACHMENTS[params.object]} to it so it would feel extra special."
    )
    world.say(
        f"But {parent.label_word} smiled gently and said, \"I prohibit that part for now; "
        f"we have to be careful with something so dear.\""
    )

    world.para()
    child.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} paused and listened. In {child.pronoun('possessive')} head, the little thought circled: "
        f"attach, attach, attach -- or wait?"
    )
    world.say(
        f"{child.id} thought, \"If I listen, it will stay safe. If I hurry, I might make a mess.\""
    )
    world.say(
        f"The repeated word kept sounding gentle and small: prohibit, prohibit, prohibit."
    )

    world.para()
    child.memes["thinking"] += 1
    child.memes["calm"] += 1
    alt = SAFE_ALTERNATIVES["bow"] if params.object == "gift" else SAFE_ALTERNATIVES["place"]
    world.say(
        f"Then {child.id} had a kinder idea. {child.id} used {ATTACHMENTS[params.object]} to {alt} instead."
    )
    world.say(
        f"{parent.label_word} laughed softly, and the room felt warm and easy again."
    )
    world.say(
        f"At the end, {OBJECTS[params.item].phrase} stayed neat, and {child.id} had made it lovely without risking it."
    )

    world.facts.update(outcome="safe", attachment=params.object)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming story that uses the words "attach" and "prohibit" and includes a child thinking to themself.',
        "Tell a gentle story where a child wants to attach something to a cherished object, but a parent prohibits the risky idea and the child finds a safer way.",
        "Write a cozy story with repetition in the inner thoughts: the child repeats a warning, pauses, and makes a kind choice.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    item = world.facts["item"]
    obj = world.facts["obj"]
    return [
        (
            "What did the child want to do at first?",
            f"{child.id} wanted to attach {ATTACHMENTS[params.object if False else world.facts.get('attachment', 'a tiny name tag')]} to the {item.label}. "
            f"The idea felt exciting, but it was not the safest choice."
        ),
        (
            "Why did the parent say no?",
            f"{parent.label_word.capitalize()} prohibited the risky plan because the {item.label} was dear and should stay safe. "
            f"The grown-up wanted the child to protect it instead of rushing."
        ),
        (
            "How did the story end?",
            f"{child.id} chose a gentler way and kept the {item.label} tidy and unharmed. "
            f"That made the ending warm and happy for both {child.id} and {parent.label_word}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to attach something?", "To attach something means to fasten or join it to something else so it stays together."),
        ("What does prohibit mean?", "To prohibit something means to say it is not allowed."),
        ("Why do people think before changing something special?", "They think first so they do not damage something important by accident."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(item: ObjectSpec, attachment: str) -> str:
    return f"(No story: {item.label} is not a good match for {attachment}; try a different pair.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming attach/prohibit storyworld.")
    ap.add_argument("--child")
    ap.add_argument("--parent")
    ap.add_argument("--item", choices=OBJECTS)
    ap.add_argument("--object", choices=ATTACHMENTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.object and not reasonableness_gate(OBJECTS[args.item], args.object):
        raise StoryError(explain_rejection(OBJECTS[args.item], args.object))
    item = args.item or rng.choice(list(OBJECTS))
    obj = args.object or rng.choice(list(ATTACHMENTS))
    if not reasonableness_gate(OBJECTS[item], obj):
        raise StoryError(explain_rejection(OBJECTS[item], obj))
    child = args.child or rng.choice([c for c, _ in CHILDREN])
    child_gender = next(g for c, g in CHILDREN if c == child)
    parent = args.parent or rng.choice([p for p, _ in PARENTS])
    parent_gender = next(g for p, g in PARENTS if p == parent)
    return StoryParams(child, child_gender, parent, parent_gender, item, obj)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[
            QAItem("What did the child want to do at first?", f"{params.child} wanted to attach something special, but the parent said no."),
            QAItem("Why did the parent say no?", f"The parent prohibited the risky step because it might damage the special object."),
            QAItem("How did it end?", f"The child chose a safer way, and the special object stayed safe."),
        ],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def outcome_smoke() -> None:
    sample = generate(StoryParams("Mia", "girl", "Mom", "mother", "gift", "ribbon"))
    if not sample.story.strip():
        raise StoryError("smoke test failed: empty story")


def asp_verify() -> int:
    if set(valid_combos()) != set(asp_valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        return 1
    try:
        outcome_smoke()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


CURATED = [
    StoryParams("Mia", "girl", "Mom", "mother", "gift", "ribbon"),
    StoryParams("Owen", "boy", "Dad", "father", "lantern", "tag"),
    StoryParams("Nora", "girl", "Mom", "mother", "photo", "sticker"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
