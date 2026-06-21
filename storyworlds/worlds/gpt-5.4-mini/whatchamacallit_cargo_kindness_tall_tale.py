#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whatchamacallit_cargo_kindness_tall_tale.py
==========================================================================

A standalone story world for a tall-tale-style kindness story built from the
seed words "whatchamacallit" and "cargo".

Premise:
- A child or helper is moving cargo in a whimsical, oversized tall-tale setting.
- Something goes wrong because the cargo is awkward, missing a proper name, or
  tied up in a silly confusion about a "whatchamacallit".
- Kindness turns the story: a helper notices a need, shares a better plan, or
  gives up pride to help a neighbor.
- The ending image proves the change in state: cargo is safe, the helper is
  happier, and the kind act changes what the world looks like.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- has Python validity checks and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
METER_KINDNESS = "kindness"
METER_STRAIN = "strain"
METER_CARGO = "cargo_safe"

TALL_TALE_OPENINGS = [
    "On a wind-bright morning",
    "One sky-high afternoon",
    "Before the gulls had finished their first big circle",
    "When the river glowed like a silver ribbon",
]

HERO_NAMES = ["Mabel", "June", "Otis", "Nell", "Benny", "Clara", "Rufus", "Etta"]
HELPER_NAMES = ["Aunt Zora", "Uncle Pike", "Gran", "Mr. Finch", "Ms. Lottie", "Old Finn"]
CARGO_TYPES = ["barrels", "crates", "mail sacks", "apple boxes", "lantern crates"]
CARGO_WORDS = {
    "barrels": "barrels",
    "crates": "crates",
    "mail sacks": "mail sacks",
    "apple boxes": "apple boxes",
    "lantern crates": "lantern crates",
}
PLACES = {
    "dock": "the long dock by the river",
    "pier": "the wobbling pier at the edge of town",
    "wagon": "the creaky wagon road under the open sky",
    "barn": "the red barn with doors wide as gull wings",
}
MISHAPS = {
    "tilt": "tilted like a teapot in a storm",
    "bounce": "bounced high enough to tickle the moon",
    "swing": "swung side to side as if it had a mind of its own",
}
KIND_ACTS = {
    "share_rope": "shared a rope",
    "lift_together": "lifted it together",
    "make_room": "made room for it",
    "steady_hand": "gave it a steady hand",
}
SOLUTIONS = {
    "share_rope": ("shared a rope and tied the cargo down gentle as a lullaby",
                   "shared a rope and tied the cargo down"),
    "lift_together": ("lifted the cargo together and carried it safely",
                      "lifted the cargo together"),
    "make_room": ("made room on the wagon so the cargo could sit snug and safe",
                  "made room on the wagon"),
    "steady_hand": ("held it steady until it settled safe and square",
                    "held it steady"),
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "uncle", "father"}
        female = {"girl", "woman", "aunt", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def inc_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = mget(ent, key) + amt


def inc_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = mem(ent, key) + amt


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if mget(ent, "cargo_tilt") >= THRESHOLD and ("tilt", ent.id) not in world.fired:
                world.fired.add(("tilt", ent.id))
                if "cargo" in world.entities:
                    inc_meter(world.get("cargo"), METER_STRAIN, 1)
                if "hero" in world.entities:
                    inc_meme(world.get("hero"), "worry", 1)
                changed = True
            if mget(ent, "cargo_safe") >= THRESHOLD and ("safe", ent.id) not in world.fired:
                world.fired.add(("safe", ent.id))
                if "hero" in world.entities:
                    inc_meme(world.get("hero"), METER_KINDNESS, 1)
                changed = True


def cargo_risk(mishap: str) -> bool:
    return mishap in MISHAPS


def sensible_solutions() -> list[str]:
    return [k for k in SOLUTIONS if k in KIND_ACTS and k]


def best_solution() -> str:
    return "share_rope"


def solution_power(solution: str) -> int:
    return {"share_rope": 3, "lift_together": 2, "make_room": 2, "steady_hand": 2}[solution]


def difficulty(place: str, cargo_type: str, delay: int) -> int:
    base = {"dock": 2, "pier": 3, "wagon": 2, "barn": 1}[place]
    bulky = {"barrels": 2, "crates": 2, "mail sacks": 1, "apple boxes": 1, "lantern crates": 2}[cargo_type]
    return base + bulky + delay


def can_recover(solution: str, place: str, cargo_type: str, delay: int) -> bool:
    return solution_power(solution) >= difficulty(place, cargo_type, delay)


def predict(world: World, solution: str, place: str, cargo_type: str, delay: int) -> dict:
    sim = world.copy()
    if can_recover(solution, place, cargo_type, delay):
        inc_meter(sim.get("cargo"), METER_CARGO, 1)
    else:
        inc_meter(sim.get("cargo"), "lost", 1)
    return {"safe": mget(sim.get("cargo"), METER_CARGO) >= THRESHOLD, "lost": mget(sim.get("cargo"), "lost") >= THRESHOLD}


def tell_opening(world: World, hero: Entity, helper: Entity, setting: str, cargo_type: str) -> None:
    opening = random.choice(TALL_TALE_OPENINGS)
    world.say(
        f"{opening}, {hero.id} and {helper.id} were at {PLACES[setting]}. "
        f"They had a load of {CARGO_WORDS[cargo_type]}, and the whole job felt as big as a hill."
    )
    world.say(
        f"{hero.id} kept saying the name of the tricky thing was a "
        f"whatchamacallit, which made {helper.id} laugh, because the cargo was real enough to count."
    )


def problem(world: World, hero: Entity, helper: Entity, setting: str, cargo_type: str, mishap: str) -> None:
    inc_meter(world.get("cargo"), "cargo_tilt", 1)
    inc_meme(hero, "pride", 1)
    world.say(
        f"Then the {cargo_type} {mishap} on the {setting} side, and the last crate began to slide."
    )
    world.say(
        f"{hero.id} tried to look brave, but {helper.id} saw the wobble first and knew one quick kindness could save the day."
    )


def turn(world: World, hero: Entity, helper: Entity, solution: str, place: str, cargo_type: str, delay: int) -> bool:
    if can_recover(solution, place, cargo_type, delay):
        inc_meter(world.get("cargo"), METER_CARGO, 1)
        inc_meme(hero, METER_KINDNESS, 1)
        inc_meme(helper, METER_KINDNESS, 1)
        world.say(
            f"{helper.id} {SOLUTIONS[solution][0]}. {hero.id} stopped showing off, listened close, and helped right away."
        )
        world.say(
            f"Together they got the {cargo_type} settled, and the load quit shaking like a pair of loose teeth."
        )
        return True
    inc_meter(world.get("cargo"), "lost", 1)
    world.say(
        f"{helper.id} tried to help, but the day had grown too wild and the load kept slipping."
    )
    return False


def ending(world: World, hero: Entity, helper: Entity, cargo_type: str, place: str, success: bool) -> None:
    if success:
        world.say(
            f"By sunset the {cargo_type} sat safe and square at {PLACES[place]}, and {hero.id} kept the whatchamacallit joke only for laughing time."
        )
        world.say(
            f"{helper.id} wiped the dust from {hero.id}'s hands, and the two of them stood beside the cargo like proud tower-keepers."
        )
    else:
        world.say(
            f"By sunset the cargo was still in trouble, and the tall tale ended with a sigh and a hard lesson about asking for help sooner."
        )


def tell(params: "StoryParams") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity("helper", kind="character", type=params.helper_type, label=params.helper))
    cargo = world.add(Entity("cargo", kind="thing", type="cargo", label=params.cargo_type))
    cargo.meters[METER_CARGO] = 0.0
    world.facts.update(hero=hero, helper=helper, cargo=cargo, params=params)

    tell_opening(world, hero, helper, params.setting, params.cargo_type)
    world.para()
    problem(world, hero, helper, params.setting, params.cargo_type, params.mishap)
    success = turn(world, hero, helper, params.solution, params.setting, params.cargo_type, params.delay)
    world.para()
    ending(world, hero, helper, params.cargo_type, params.setting, success)

    world.facts["success"] = success
    world.facts["kindness"] = mem(hero, METER_KINDNESS) + mem(helper, METER_KINDNESS)
    world.facts["strain"] = mget(cargo, METER_STRAIN)
    return world


@dataclass
@dataclass
class StoryParams:
    setting: str
    cargo_type: str
    mishap: str
    solution: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    delay: int = 0
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


SETTINGS = ["dock", "pier", "wagon", "barn"]
MISHAP_OPTIONS = ["tilt", "bounce", "swing"]
SOLUTIONS = SOLUTIONS
STORY_VALID: list[tuple[str, str, str]] = [
    (s, c, m) for s in SETTINGS for c in CARGO_TYPES for m in MISHAP_OPTIONS if cargo_risk(m)
]


def valid_combos() -> list[tuple[str, str, str]]:
    return list(STORY_VALID)


def explain_rejection() -> str:
    return "(No story: that choice does not create a believable cargo mishap for this tall tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale kindness storyworld about cargo and a whatchamacallit.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGO_TYPES)
    ap.add_argument("--mishap", choices=MISHAP_OPTIONS)
    ap.add_argument("--solution", choices=list(SOLUTIONS))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    picks = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.cargo is None or c[1] == args.cargo)]
    if not picks:
        raise StoryError(explain_rejection())
    setting, cargo_type, mishap = rng.choice(sorted(picks))
    solution = args.solution or rng.choice(list(SOLUTIONS))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    hero_type = "girl" if hero in {"Mabel", "June", "Nell", "Clara", "Etta"} else "boy"
    helper_type = "woman" if "Aunt" in helper or "Ms." in helper or helper == "Gran" else "man"
    delay = 0 if args.delay is None else args.delay
    return StoryParams(setting, cargo_type, mishap, solution, hero, hero_type, helper, helper_type, delay)


def story_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a tall tale for a child that includes the words "whatchamacallit" and "cargo" and shows kindness fixing a problem.',
        f"Tell a whimsical story where {p.hero} and {p.helper} are moving {p.cargo_type}, the load starts to {MISHAP_OPTIONS[0] if p.mishap == 'tilt' else p.mishap}, and kindness saves the day.",
        f"Write a short, child-facing tall tale where someone calls a tricky object a whatchamacallit, then learns to help with cargo instead of boasting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p = f["params"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    cargo: Entity = f["cargo"]
    success = f["success"]
    if success:
        return [
            ("What was the problem in the story?",
             f"The cargo began to slip and wobble, so the load was in danger of spilling. That made it a good moment for kindness instead of bragging."),
            ("How did they fix it?",
             f"{helper.id} {SOLUTIONS[p.solution][1]}, and {hero.id} helped right away. They worked together, which kept the cargo safe."),
            ("How did the story end?",
             f"It ended with the cargo safe and square at the {p.setting}, and {hero.id} laughing about the whatchamacallit name only after the work was done. The ending image shows the load settled and the two helpers standing proud."),
        ]
    return [
        ("What was the problem in the story?",
         f"The cargo began to slip and wobble, and the day got too wild for the plan they had chosen. They needed more help than they expected."),
        ("How did the story end?",
         f"It ended with the cargo still in trouble, which taught them to ask for help sooner. Even so, they stayed together and tried to keep everyone safe."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is cargo?",
         "Cargo is a load of things being carried from one place to another. It can be crates, barrels, or other packed-up goods."),
        ("What does kindness mean?",
         "Kindness means helping someone, sharing work, or choosing a gentle action that makes things better. It often makes a hard job feel lighter."),
        ("What is a whatchamacallit?",
         "A whatchamacallit is a playful word people use when they forget or do not know an object's exact name. It can make a story feel silly and tall-tale big."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,M) :- setting(S), cargo(C), mishap(M), cargo_risk(M).
success(Sol) :- solution(Sol), sense(Sol, N), sense_min(M), N >= M.
kindness_up(H) :- hero(H), kindness(H, K), K > 0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CARGO_TYPES:
        lines.append(asp.fact("cargo", c))
    for m in MISHAP_OPTIONS:
        lines.append(asp.fact("mishap", m))
        lines.append(asp.fact("cargo_risk", m))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol))
        lines.append(asp.fact("sense", sol, 2 if sol != "share_rope" else 3))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        params = resolve_params(build_parser().parse_args([]), _random.Random(777))
        sample = generate(params)
        assert sample.story.strip()
        print("OK: smoke-test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show success/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("dock", "crates", "tilt", "share_rope", "Mabel", "girl", "Gran", "woman"),
            StoryParams("pier", "barrels", "bounce", "lift_together", "Otis", "boy", "Uncle Pike", "man"),
            StoryParams("wagon", "mail sacks", "swing", "make_room", "Nell", "girl", "Ms. Lottie", "woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
