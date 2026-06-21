#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/veggie_reconciliation_space_adventure.py
========================================================================

A standalone story world for a tiny Space Adventure about a lost veggie,
a misunderstanding, and reconciliation at the end.

Premise:
- Two small space explorers are on a tiny ship.
- One is upset because the other shared the last veggie at the wrong time.
- They drift into a little conflict while exploring a moon garden and cargo bay.
- A calm repair and an apology help them reconcile.
- The ending image proves the change: they share a new veggie harvest together.

The world is intentionally small, state-driven, and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {"moved": 0.0, "tended": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"sad": 0.0, "angry": 0.0, "hope": 0.0, "care": 0.0})
    attrs: dict[str, object] = field(default_factory=dict)

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    stars: str
    afford: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Veggie:
    id: str
    label: str
    phrase: str
    color: str
    ripe_sound: str
    kind: str
    edible: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Conflict:
    id: str
    cause: str
    hurt: str
    blame_word: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Repair:
    id: str
    action: str
    effect: str
    apology: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    veggie: str
    conflict: str
    repair: str
    explorer_a: str
    explorer_a_type: str
    explorer_b: str
    explorer_b_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("A")
    b = world.get("B")
    if a.memes["hope"] >= THRESHOLD and b.memes["hope"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["sad"] = 0.0
            b.memes["sad"] = 0.0
            a.memes["angry"] = 0.0
            b.memes["angry"] = 0.0
            a.memes["care"] += 1
            b.memes["care"] += 1
            out.append("__reconcile__")
    return out


RULES = [Rule("reconcile", _r_reconcile)]


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moon garden",
        stars="silver stars",
        afford={"walk", "pick", "share"},
        tags={"space", "garden"},
    ),
    "cargo_bay": Setting(
        id="cargo_bay",
        place="the cargo bay",
        stars="tiny dock lights",
        afford={"walk", "sort", "share"},
        tags={"space", "cargo"},
    ),
    "orbit_ring": Setting(
        id="orbit_ring",
        place="the orbit ring",
        stars="bright panel lights",
        afford={"float", "share", "fix"},
        tags={"space", "orbit"},
    ),
}

VEGGIES = {
    "pea_pod": Veggie(
        id="pea_pod",
        label="pea pod",
        phrase="a little pea pod",
        color="green",
        ripe_sound="pop",
        kind="pea pod",
        tags={"veggie", "green"},
    ),
    "carrot": Veggie(
        id="carrot",
        label="carrot",
        phrase="a crunchy carrot",
        color="orange",
        ripe_sound="crack",
        kind="carrot",
        tags={"veggie", "orange"},
    ),
    "tomato": Veggie(
        id="tomato",
        label="tomato",
        phrase="a round tomato",
        color="red",
        ripe_sound="plip",
        kind="tomato",
        tags={"veggie", "red"},
    ),
}

CONFLICTS = {
    "last_slice": Conflict(
        id="last_slice",
        cause="the last veggie slice was taken first",
        hurt="one explorer felt left out",
        blame_word="unfair",
        tags={"sharing", "hurt"},
    ),
    "late_snack": Conflict(
        id="late_snack",
        cause="the snack was promised for both, but one ate early",
        hurt="the other explorer got a sad surprise",
        blame_word="left out",
        tags={"sharing", "hurt"},
    ),
}

REPAIRS = {
    "apology": Repair(
        id="apology",
        action="said sorry and offered the other half",
        effect="the mood softened right away",
        apology="I'm sorry for taking it without asking",
        tags={"sorry", "sharing"},
    ),
    "repair_station": Repair(
        id="repair_station",
        action="fixed the snack tray together and split the new veggies fairly",
        effect="the ship felt fair again",
        apology="Let's make it right together",
        tags={"sharing", "fix"},
    ),
}

NAMES = ["Ava", "Milo", "Zoe", "Noah", "Luna", "Finn", "Maya", "Theo"]
GENDERS = {"girl": ["Ava", "Zoe", "Luna", "Maya"], "boy": ["Milo", "Noah", "Finn", "Theo"]}
HELPERS = [("captain", "mother"), ("pilot", "father")]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for v in VEGGIES:
            for c in CONFLICTS:
                combos.append((s, v, c))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this combination does not support a clear veggie conflict and reconciliation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space adventure about a veggie and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--veggie", choices=VEGGIES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GENDERS[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.veggie and args.conflict:
        if (args.setting, args.veggie, args.conflict) not in combos:
            raise StoryError(explain_rejection(StoryParams(
                setting=args.setting, veggie=args.veggie, conflict=args.conflict, repair=args.repair or "apology",
                explorer_a="", explorer_a_type="girl", explorer_b="", explorer_b_type="boy",
                helper="", helper_type="mother",
            )))
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("Unknown repair.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    veggie = args.veggie or rng.choice(sorted(VEGGIES))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    repair = args.repair or rng.choice(sorted(REPAIRS))
    a_type = rng.choice(["girl", "boy"])
    b_type = "boy" if a_type == "girl" else "girl"
    helper_type = rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        veggie=veggie,
        conflict=conflict,
        repair=repair,
        explorer_a=_pick_name(rng, a_type),
        explorer_a_type=a_type,
        explorer_b=_pick_name(rng, b_type),
        explorer_b_type=b_type,
        helper=rng.choice(NAMES),
        helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    veggie = VEGGIES[params.veggie]
    conflict = CONFLICTS[params.conflict]
    repair = REPAIRS[params.repair]

    a = world.add(Entity(id="A", kind="character", type=params.explorer_a_type, label=params.explorer_a, role="explorer"))
    b = world.add(Entity(id="B", kind="character", type=params.explorer_b_type, label=params.explorer_b, role="explorer"))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    snack = world.add(Entity(id="veggie", kind="thing", type=veggie.kind, label=veggie.label, role="snack", tags=veggie.tags))

    a.memes["hope"] = 1.0
    b.memes["hope"] = 1.0

    world.say(f"{a.label} and {b.label} were little space explorers on the {setting.place}.")
    world.say(f"Above them floated {setting.stars}, and in the snack bin sat {veggie.phrase}.")
    world.say(f"They had been out on a mission, and both of them wanted the {veggie.label} after the long ride.")

    world.para()
    world.say(f"But something went wrong: {conflict.cause}. {conflict.hurt.capitalize()}.")
    a.memes["sad"] += 1
    b.memes["sad"] += 1
    a.memes["angry"] += 1
    b.memes["angry"] += 1

    world.para()
    if params.repair == "apology":
        world.say(f"{a.label} looked down, then whispered, \"{repair.apology}.\"")
        world.say(f"{b.label} blinked, and the tension began to float away.")
    else:
        world.say(f"{helper.label} opened the tiny repair station and {repair.action}.")
        world.say(f"{a.label} and {b.label} watched carefully, and {repair.effect}.")

    a.memes["hope"] += 1
    b.memes["hope"] += 1
    propagate(world, narrate=False)

    world.para()
    if a.memes["hope"] >= THRESHOLD and b.memes["hope"] >= THRESHOLD:
        world.say(f"At last, they sat side by side under the silver lights and shared a fresh {veggie.label}.")
        world.say(f"This time the {veggie.label} was split fairly, and both explorers smiled.")
        world.say(f"Their little ship glowed warm again, as if the stars themselves approved.")
    else:
        world.say(f"They still felt a little stuck, but the helper stayed near until they could try again.")

    world.facts.update(setting=setting, veggie=veggie, conflict=conflict, repair=repair, helper=helper, a=a, b=b)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space adventure story that includes the word '{f['veggie'].label}' and ends with reconciliation.",
        f"Tell a child-friendly story about two explorers who argue over a veggie and then make up on a small ship.",
        f"Write a story where a helper helps two space kids reconcile after a misunderstanding about food.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    veggie = f["veggie"]
    return [
        QAItem(question="What were the children exploring?", answer=f"They were exploring a tiny space place with stars above them, and they were on a mission together."),
        QAItem(question="What caused the trouble?", answer=f"{f['conflict'].cause.capitalize()}. That made both explorers feel upset and a little left out."),
        QAItem(question="How did they reconcile?", answer=f"They reconciled by apologizing or fixing the snack problem together. After that, they shared {veggie.phrase} fairly and smiled again."),
        QAItem(question=f"What did {a.label} and {b.label} share at the end?", answer=f"They shared a fresh {veggie.label} at the end, and the split was fair this time."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a veggie?", answer="A veggie is a plant food that people can eat, like a carrot, tomato, or pea pod."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation means making up after a disagreement and becoming friendly again."),
        QAItem(question="What is a space adventure?", answer="A space adventure is a story about exploring stars, planets, ships, or moon places."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moon_garden", veggie="pea_pod", conflict="last_slice", repair="apology",
                explorer_a="Ava", explorer_a_type="girl", explorer_b="Milo", explorer_b_type="boy",
                helper="Captain", helper_type="mother"),
    StoryParams(setting="cargo_bay", veggie="carrot", conflict="late_snack", repair="repair_station",
                explorer_a="Theo", explorer_a_type="boy", explorer_b="Luna", explorer_b_type="girl",
                helper="Pilot", helper_type="father"),
    StoryParams(setting="orbit_ring", veggie="tomato", conflict="last_slice", repair="apology",
                explorer_a="Maya", explorer_a_type="girl", explorer_b="Noah", explorer_b_type="boy",
                helper="Star", helper_type="mother"),
]


ASP_RULES = r"""
veggie(V) :- veggie_id(V).
conflict(C) :- conflict_id(C).
repair(R) :- repair_id(R).
valid(S,V,C) :- setting_id(S), veggie_id(V), conflict_id(C).
reconcile :- hope(a), hope(b), not grudge.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_id", s))
    for v in VEGGIES:
        lines.append(asp.fact("veggie_id", v))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict_id", c))
    for r in REPAIRS:
        lines.append(asp.fact("repair_id", r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, veggie=None, conflict=None, repair=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        return 1 if not print(f"FAIL: generation smoke test failed: {exc}") else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.veggie not in VEGGIES or params.conflict not in CONFLICTS or params.repair not in REPAIRS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if args.veggie and args.veggie not in VEGGIES:
        raise StoryError("Invalid veggie.")
    if args.conflict and args.conflict not in CONFLICTS:
        raise StoryError("Invalid conflict.")
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("Invalid repair.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    veggie = args.veggie or rng.choice(sorted(VEGGIES))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    repair = args.repair or rng.choice(sorted(REPAIRS))
    a_type = rng.choice(["girl", "boy"])
    b_type = "boy" if a_type == "girl" else "girl"
    helper_type = rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        veggie=veggie,
        conflict=conflict,
        repair=repair,
        explorer_a=_pick_name(rng, a_type),
        explorer_a_type=a_type,
        explorer_b=_pick_name(rng, b_type),
        explorer_b_type=b_type,
        helper=rng.choice(NAMES),
        helper_type=helper_type,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for s, v, c in combos:
            print(f"  {s:12} {v:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
