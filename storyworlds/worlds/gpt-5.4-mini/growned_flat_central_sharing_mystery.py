#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/growned_flat_central_sharing_mystery.py
=======================================================================

A tiny standalone storyworld for a mystery-flavored sharing tale.

Premise
-------
Two children share a strange, flat clue at the central table in a quiet room.
They try to solve a small mystery, discover who the clue belongs to, and end by
sharing the answer and the discovered object with a nearby helper.

This world keeps the action small and state-driven:
- a puzzle token is flat
- a central place draws attention
- sharing can be refused, offered, accepted, or resolved
- the mystery is solved by observing state, not by swapping nouns in a template

Seed words included in the world and prose:
- growned
- flat
- central

The script supports:
- default run
- -n, --all, --seed
- --trace, --qa, --json
- --asp, --verify, --show-asp
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    owner: str = ""
    flat: bool = False
    central: bool = False
    hidden: bool = False
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
class Setting:
    id: str
    place: str
    central_place: str
    mood: str

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
class Clue:
    id: str
    label: str
    flat: bool = True
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
class SharingItem:
    id: str
    label: str
    phrase: str
    shared_use: str
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
class Hint:
    id: str
    label: str
    answer: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_ask_for_share(world: World) -> list[str]:
    out: list[str] = []
    owner = world.facts.get("owner")
    seeker = world.facts.get("seeker")
    if not owner or not seeker:
        return out
    if owner.memes["guarded"] < THRESHOLD:
        return out
    sig = ("ask", owner.id, seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__ask__")
    return out


def _r_sharing_thaw(world: World) -> list[str]:
    out: list[str] = []
    offered = world.facts.get("offered")
    if not offered:
        return out
    sig = ("thaw", offered.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.facts.get("kids", []):
        kid.memes["curiosity"] += 1
    out.append("__thaw__")
    return out


CAUSAL_RULES = [
    Rule("ask_for_share", "social", _r_ask_for_share),
    Rule("sharing_thaw", "social", _r_sharing_thaw),
]


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


def make_state_flat(world: World, clue: Entity, item: Entity) -> bool:
    return clue.flat and item.flat


def shared_result(world: World) -> str:
    return world.facts.get("outcome", "solved")


def introduce(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} sat at the central table in "
        f"{world.setting.place}. The room felt {world.setting.mood}, like it was "
        f"waiting to tell a secret."
    )
    world.say(
        f"{a.id} found a flat little clue on the table, and {b.id} leaned close "
        f"to look at it."
    )


def clue_detail(world: World, clue: Entity, item: Entity) -> None:
    world.say(
        f"The clue was {clue.label}, and it had a {item.label} shape stamped "
        f"into the middle. It looked almost growned, as if someone had pressed "
        f"it there on purpose."
    )


def suspicion(world: World, a: Entity, b: Entity, clue: Entity) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f'"This is strange," {a.id} said. "{clue.label.capitalize()} is flat, '
        f"but it feels important."
    )
    world.say(
        f'{b.id} touched the edge and whispered, "Maybe it belongs to someone '
        f"central to the room."
    )


def search(world: World, a: Entity, b: Entity, hint: Hint) -> None:
    world.say(
        f"They looked around the {world.setting.central_place}, near the lamp, "
        f'and under a cushion. At last they noticed {hint.label}.'
    )


def offer(world: World, owner: Entity, seeker: Entity, item: Entity) -> None:
    owner.memes["guarded"] += 1
    world.say(
        f'{owner.id} held the {item.label} a little tighter, then asked, '
        f'"Will you share it if we solve the puzzle together?"'
    )


def accept(world: World, owner: Entity, seeker: Entity, item: Entity) -> None:
    owner.memes["trust"] += 1
    seeker.memes["joy"] += 1
    world.say(
        f'{seeker.id} smiled. "Yes," {seeker.id} said. "We can share it."'
    )
    world.say(
        f"{owner.id} let {seeker.pronoun('object')} hold the {item.label} too, "
        f"and the mystery felt smaller right away."
    )


def solve(world: World, owner: Entity, seeker: Entity, clue: Entity, item: Entity, hint: Hint) -> None:
    clue.hidden = False
    item.hidden = False
    owner.memes["relief"] += 1
    seeker.memes["relief"] += 1
    world.say(
        f"They followed the clue, and the answer made sense at once: "
        f"{hint.answer}"
    )
    world.say(
        f"The flat clue belonged with the {item.label}. That was why it had been "
        f"waiting at the central table all along."
    )


def ending(world: World, owner: Entity, seeker: Entity, item: Entity) -> None:
    owner.memes["joy"] += 1
    seeker.memes["joy"] += 1
    world.say(
        f"In the end, {owner.id} and {seeker.id} shared the {item.label} and "
        f"the answer. The room was still quiet, but now it felt warm and sure."
    )


def tell(setting: Setting, clue_cfg: Clue, item_cfg: SharingItem, hint: Hint,
         owner_name: str = "Mina", owner_gender: str = "girl",
         seeker_name: str = "Theo", seeker_gender: str = "boy",
         helper_name: str = "Granded", helper_gender: str = "man") -> World:
    world = World(setting)
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    clue = world.add(Entity(id="clue", label=clue_cfg.label, flat=clue_cfg.flat, central=True))
    item = world.add(Entity(id="item", label=item_cfg.label, flat=True, central=True, owner=owner.id))
    owner.memes["guarded"] = 1.0
    seeker.memes["curiosity"] = 1.0
    world.facts["kids"] = [owner, seeker]
    world.facts["owner"] = owner
    world.facts["seeker"] = seeker
    world.facts["helper"] = helper
    world.facts["item_cfg"] = item_cfg
    world.facts["clue_cfg"] = clue_cfg
    world.facts["hint"] = hint

    introduce(world, owner, seeker)
    world.para()
    clue_detail(world, clue, item)
    suspicion(world, owner, seeker, clue)
    propagate(world, narrate=False)
    search(world, owner, seeker, hint)
    offer(world, owner, seeker, item)
    accept(world, owner, seeker, item)
    world.para()
    solve(world, owner, seeker, clue, item, hint)
    world.say(
        f"{helper.id} came over, and they shared the answer with {helper.pronoun('object')}. "
        f"It turned out the clue was for everyone at the table."
    )
    ending(world, owner, seeker, item)
    world.facts["outcome"] = "solved"
    world.facts["clue"] = clue
    world.facts["item"] = item
    return world


SETTINGS = {
    "house": Setting("house", "the house", "central table", "mysterious"),
    "library": Setting("library", "the library", "central desk", "hushed"),
    "attic": Setting("attic", "the attic", "central chest", "dusty"),
}

CLUES = {
    "note": Clue("note", "a folded note", tags={"paper", "note"}),
    "tile": Clue("tile", "a flat tile", tags={"tile", "flat"}),
    "coin": Clue("coin", "a shiny flat coin", tags={"coin", "flat"}),
}

ITEMS = {
    "map": SharingItem("map", "a tiny map", "a tiny map", "share the route", tags={"map"}),
    "key": SharingItem("key", "a brass key", "a brass key", "share the secret", tags={"key"}),
    "badge": SharingItem("badge", "a round badge", "a round badge", "share the sign", tags={"badge"}),
}

HINTS = {
    "lamp": Hint("lamp", "the lamp stand", "the lamp stand was under the cloth", tags={"lamp"}),
    "book": Hint("book", "the center shelf", "the center shelf held the missing book", tags={"book"}),
    "box": Hint("box", "the central box", "the central box had the same mark", tags={"box"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    item: str
    hint: str
    owner_name: str
    owner_gender: str
    seeker_name: str
    seeker_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for i in ITEMS:
                for h in HINTS:
                    if CLUES[c].flat and ITEMS[i].flat:
                        combos.append((s, c, i, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery-sharing storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hint", choices=HINTS)
    ap.add_argument("--owner-name")
    ap.add_argument("--seeker-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--seeker-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.item is None or c[2] == args.item)
              and (args.hint is None or c[3] == args.hint)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, item, hint = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting, clue=clue, item=item, hint=hint,
        owner_name=args.owner_name or rng.choice(["Mina", "Lila", "Nora", "Ada"]),
        owner_gender=args.owner_gender or rng.choice(["girl", "woman"]),
        seeker_name=args.seeker_name or rng.choice(["Theo", "Ben", "Eli", "Max"]),
        seeker_gender=args.seeker_gender or rng.choice(["boy", "man"]),
        helper_name=args.helper_name or rng.choice(["Granded", "Auntie", "Papa"]),
        helper_gender=args.helper_gender or rng.choice(["man", "woman"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "growned", "flat", and "central".',
        f"Tell a sharing story where {f['owner'].id} and {f['seeker'].id} find a flat clue at a central place and solve a little mystery together.",
        f"Write a calm mystery about sharing an important object after a clue leads two children to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    owner = world.facts["owner"]
    seeker = world.facts["seeker"]
    item_cfg = world.facts["item_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    hint = world.facts["hint"]
    return [
        QAItem(
            question="What made the story feel like a mystery?",
            answer=f"The children found a flat clue and had to figure out what it meant. The answer was hidden near the central place, so they had to look carefully."
        ),
        QAItem(
            question="How did the children share?",
            answer=f"{owner.id} let {seeker.id} hold the {item_cfg.label} too, and they talked about the answer together. Sharing the object helped them solve the mystery as a team."
        ),
        QAItem(
            question="What did the clue belong to?",
            answer=f"The flat clue belonged with the {item_cfg.label}. The hint showed that it had been waiting in the central place for someone to notice it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flat mean?",
            answer="Flat means smooth and not bumpy or round. A flat thing can lie down on a table without rolling away."
        ),
        QAItem(
            question="What does central mean?",
            answer="Central means in the middle or most important place. A central table or desk is the place that draws everyone's attention."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, hold, or enjoy something too. It helps people work together and feel close."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== (3) World questions ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.flat:
            bits.append("flat")
        if e.central:
            bits.append("central")
        if e.hidden:
            bits.append("hidden")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("house", "note", "map", "lamp", "Mina", "girl", "Theo", "boy", "Granded", "man"),
    StoryParams("library", "tile", "key", "book", "Lila", "girl", "Ben", "boy", "Auntie", "woman"),
    StoryParams("attic", "coin", "badge", "box", "Nora", "girl", "Max", "boy", "Papa", "man"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not give a flat clue, a central place, and a shareable mystery at once.)"


ASP_RULES = r"""
flat_clue(C) :- clue(C), flat(C).
central_place(S) :- setting(S), central(S).
shareable(I) :- item(I), flat_item(I).

valid(S,C,I,H) :- setting(S), clue(C), item(I), hint(H),
                  flat_clue(C), shareable(I), central_place(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "central" in s.central_place:
            lines.append(asp.fact("central", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.flat:
            lines.append(asp.fact("flat", cid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.flat:
            lines.append(asp.fact("flat_item", iid))
    for hid in HINTS:
        lines.append(asp.fact("hint", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue=None, item=None, hint=None,
            owner_name=None, owner_gender=None, seeker_name=None,
            seeker_gender=None, helper_name=None, helper_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], CLUES[params.clue], ITEMS[params.item], HINTS[params.hint],
        params.owner_name, params.owner_gender, params.seeker_name, params.seeker_gender,
        params.helper_name, params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
