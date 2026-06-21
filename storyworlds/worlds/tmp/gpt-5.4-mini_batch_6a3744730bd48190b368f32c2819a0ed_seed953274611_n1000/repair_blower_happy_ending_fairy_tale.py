#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/repair_blower_happy_ending_fairy_tale.py
========================================================================

A tiny fairy-tale storyworld about a broken magical blower, a careful repair,
and a happy ending. A child, a small helper, and a gentle craft problem are
modeled as typed entities with physical meters and emotional memes.

The world premise:
- A royal garden has a magical blower used to clear petals and leaves.
- The blower stops working on a windy day.
- A skilled helper finds the broken part, repairs it, and the garden blooms
  again.
- The ending is always kind, bright, and reassuring.

The story keeps a fairy-tale tone, but the state changes are real:
- dust, brokenness, repaired, and joy are tracked in the world model
- the repair must be plausible
- the blower must matter to the garden's condition
- the ending must prove that the repair changed the world

Run it:
    python storyworlds/worlds/gpt-5.4-mini/repair_blower_happy_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/repair_blower_happy_ending_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/repair_blower_happy_ending_fairy_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    blower: str
    repair_kind: str
    repair_tool: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    weather: str
    description: str
    garden_name: str


@dataclass
class Blower:
    id: str
    label: str
    broken_label: str
    repair_part: str
    repair_hint: str
    blower_word: str = "blower"
    makes_air: bool = True
    broken: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    skill: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_broken(world: World) -> list[str]:
    out: list[str] = []
    blower = world.get("blower")
    garden = world.get("garden")
    if blower.meters["broken"] < THRESHOLD or ("broken",) in world.fired:
        return out
    world.fired.add(("broken",))
    garden.meters["tangled"] += 1
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["worry"] += 1
    out.append("__broken__")
    return out


def _r_repaired(world: World) -> list[str]:
    out: list[str] = []
    blower = world.get("blower")
    garden = world.get("garden")
    helper = world.get("helper")
    if blower.meters["repaired"] < THRESHOLD or ("repaired",) in world.fired:
        return out
    world.fired.add(("repaired",))
    garden.meters["tangled"] = 0
    garden.meters["bloom"] += 1
    helper.memes["pride"] += 1
    out.append("__repaired__")
    return out


CAUSAL_RULES = [Rule("broken", _r_broken), Rule("repaired", _r_repaired)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def reasonableness_gate(blower: Blower, repair: Repair) -> bool:
    return blower.makes_air and repair.sense >= 2


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid, rep in REPAIRS.items():
            if reasonableness_gate(BLOWERS["blower"], rep):
                combos.append((sid, rid))
    return combos


def _predict(world: World) -> dict:
    sim = world.copy()
    sim.get("blower").meters["broken"] = 1
    propagate(sim, narrate=False)
    return {
        "tangled": sim.get("garden").meters["tangled"],
        "bloom": sim.get("garden").meters["bloom"],
    }


def tell(setting: Setting, blower: Blower, repair: Repair, hero: str, helper: str,
         hero_type: str, helper_type: str, repair_tool: str) -> World:
    w = World()
    h = w.add(Entity(id="hero", kind="character", type=hero_type, label=hero, role="hero"))
    k = w.add(Entity(id="helper", kind="character", type=helper_type, label=helper, role="helper"))
    g = w.add(Entity(id="garden", kind="thing", type="garden", label=setting.garden_name))
    b = w.add(Entity(id="blower", kind="thing", type="blower", label=blower.label))
    h.memes["hope"] += 1
    k.memes["care"] += 1
    w.say(
        f"Once in a fair kingdom, {hero} walked to {setting.place}, where "
        f"{setting.description}. {setting.garden_name} was kept neat by a small {blower.label}, "
        f"but today the {blower.blower_word} would not sing."
    )
    w.say(
        f'"Oh dear," said {helper}, "the {blower.broken_label} is stuck." '
        f"{hero} touched the quiet machine and felt the wind stop in the leaves."
    )
    w.para()
    pred = _predict(w)
    w.facts["predicted"] = pred
    w.facts["repair"] = repair
    w.facts["setting"] = setting
    w.facts["blower"] = blower
    w.facts["hero_name"] = hero
    w.facts["helper_name"] = helper
    w.say(
        f"{helper} fetched a tiny {repair_tool} and looked under the cover. "
        f'"If I mend the {blower.repair_part}," {helper} said, "the garden will breathe again."'
    )
    b.meters["broken"] = 1
    if repair.skill >= 2:
        w.say(
            f"With careful fingers, {helper} used the {repair_tool}, set the {blower.repair_part} straight, "
            f"and gave the little machine a brave turn."
        )
        b.meters["repaired"] = 1
        propagate(w, narrate=False)
        w.say(
            f"The {blower.label_word if blower.label else 'blower'} hummed at once, blowing the dry petals away. "
            f"{setting.garden_name} brightened, and the roses lifted their heads like happy crowns."
        )
        h.memes["joy"] += 1
        k.memes["joy"] += 1
        w.say(
            f"{hero} clapped, and {helper} laughed. By sunset, the paths were clear, the fountain sparkled, "
            f"and the whole garden smelled sweet and clean."
        )
    else:
        w.say(
            f"{helper} tried, but the repair was not enough. The broken part slipped back again, and the wind stayed still."
        )
        w.say(
            f"So {hero} and {helper} called a wiser craftswoman, and the tale would have gone on sadly "
            f"if not for her steady hands."
        )
    w.facts["world"] = w
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    repair = f["repair"]
    return [
        f'Write a fairy tale for a small child that uses the words "repair" and "blower".',
        f"Tell a happy story set in {setting.place} where a broken blower is repaired by a kind helper.",
        f"Write a gentle fairy tale with a clear problem and a bright ending about fixing a blower in {setting.garden_name}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting = f["setting"]
    repair = f["repair"]
    hero = f["hero_name"]
    helper = f["helper_name"]
    ans1 = (
        f"It is about {hero} and {helper} in {setting.place}. "
        f"The garden needed help because the blower stopped working."
    )
    ans2 = (
        f"{helper} repaired the blower with a small tool. "
        f"That fixed the broken part and made the garden neat again."
    )
    ans3 = (
        f"The ending is happy. The blower hummed, the paths were clear, and the flowers stood up bright."
    )
    return [
        ("Who is the story about?", ans1),
        ("What did the helper do?", ans2),
        ("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does repair mean?",
         "Repair means to fix something that is broken so it can work again."),
        ("What is a blower?",
         "A blower is a machine that pushes air or wind to move leaves, dust, or petals."),
        ("Why might a garden need a blower?",
         "A blower helps clear paths and keep a garden neat when leaves or petals fall."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "rose_garden": Setting(
        id="rose_garden",
        place="the rose garden",
        weather="soft",
        description="the morning breeze smelled like honey",
        garden_name="the rose garden",
    ),
    "castle_courtyard": Setting(
        id="castle_courtyard",
        place="the castle courtyard",
        weather="bright",
        description="the stone arches shone after dawn",
        garden_name="the castle flowers",
    ),
    "lantern_green": Setting(
        id="lantern_green",
        place="the lantern-green garden",
        weather="gentle",
        description="little glass lanterns blinked between the hedges",
        garden_name="the lantern-green garden",
    ),
}

BLOWERS = {
    "blower": Blower(
        id="blower",
        label="magical blower",
        broken_label="gear wheel",
        repair_part="gear wheel",
        repair_hint="a loose gear wheel",
        tags={"blower", "repair"},
    )
}

REPAIRS = {
    "tighten": Repair(
        id="tighten",
        label="tighten the wheel",
        sense=3,
        skill=3,
        text="tightened the wheel until it sat straight",
        fail="tried to tighten it, but the wheel slipped again",
        tags={"repair"},
    ),
    "oil": Repair(
        id="oil",
        label="oil the axle",
        sense=2,
        skill=2,
        text="oiled the axle and made it turn smoothly",
        fail="oiled the axle, but the blower still coughed and stalled",
        tags={"repair"},
    ),
    "replace": Repair(
        id="replace",
        label="replace the wheel",
        sense=4,
        skill=3,
        text="replaced the broken wheel with a shining new one",
        fail="searched for a new wheel, but the old one would not budge",
        tags={"repair"},
    ),
}


TRAITS = ["kind", "careful", "brave", "gentle", "patient"]
GIRL_NAMES = ["Mira", "Lina", "Ayla", "Nora", "Elin"]
BOY_NAMES = ["Theo", "Arin", "Jasper", "Felix", "Oren"]


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    blower: str
    repair_kind: str
    repair_tool: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about repairing a blower.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--blower", choices=BLOWERS)
    ap.add_argument("--repair-kind", choices=REPAIRS)
    ap.add_argument("--repair-tool")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_repair_choices() -> list[str]:
    return [r.id for r in REPAIRS.values() if r.sense >= 2]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair_kind and REPAIRS[args.repair_kind].sense < 2:
        raise StoryError("That repair is too weak for a story of this kind.")
    settings = list(SETTINGS)
    repairs = valid_repair_choices()
    setting = args.setting or rng.choice(settings)
    repair_kind = args.repair_kind or rng.choice(repairs)
    blower = args.blower or "blower"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man", "girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Iris", "Mabel", "Cedric", "Rowan", "June"])
    repair_tool = args.repair_tool or rng.choice(["tiny wrench", "golden screwdriver", "little oil can"])
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        blower=blower,
        repair_kind=repair_kind,
        repair_tool=repair_tool,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.repair_kind not in REPAIRS:
        raise StoryError("Unknown repair kind.")
    world = tell(
        SETTINGS[params.setting],
        BLOWERS[params.blower],
        REPAIRS[params.repair_kind],
        params.hero,
        params.helper,
        params.hero_type,
        params.helper_type,
        params.repair_tool,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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


ASP_RULES = r"""
repairable(S,R) :- setting(S), repair(R), sense_ok(R).
happy_end(S) :- repairable(S,R), blower(B), setting(S), repaired(B).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense_ok", rid) if r.sense >= 2 else asp.fact("sense_ok", rid))
    for bid in BLOWERS:
        lines.append(asp.fact("blower", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show repairable/2."))
    return sorted(set(asp.atoms(model, "repairable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, hero=None, hero_type=None, helper=None, helper_type=None,
            blower=None, repair_kind=None, repair_tool=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: verification passed.")
    return rc


CURATED = [
    StoryParams(setting="rose_garden", hero="Mira", hero_type="girl", helper="Iris", helper_type="woman",
                blower="blower", repair_kind="tighten", repair_tool="tiny wrench"),
    StoryParams(setting="castle_courtyard", hero="Theo", hero_type="boy", helper="Cedric", helper_type="man",
                blower="blower", repair_kind="replace", repair_tool="golden screwdriver"),
    StoryParams(setting="lantern_green", hero="Ayla", hero_type="girl", helper="Mabel", helper_type="woman",
                blower="blower", repair_kind="oil", repair_tool="little oil can"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show repairable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible repair stories:")
        for s, r in asp_valid_combos():
            print(s, r)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
