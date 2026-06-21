#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fuzz_dim_bus_seal_flashback_rhyme_humor.py
===========================================================================

A small, standalone storyworld for a nursery-rhyme style tale about a child on
a fuzz-dim bus ride, a friendly seal, a flashback, and a humorous rhyme.

The world is intentionally tiny:
- a child rides a bus at dusk
- the child remembers a funny earlier trip in a flashback
- the bus reaches a seal pool
- the child makes a safe choice, laughs, and the ending image proves a change

The story is state-driven: meter changes and memory changes decide which beats
appear. The tone stays child-facing, concrete, and lightly rhymed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/fuzz_dim_bus_seal_flashback_rhyme_humor.py
    python storyworlds/worlds/gpt-5.4-mini/fuzz_dim_bus_seal_flashback_rhyme_humor.py --all
    python storyworlds/worlds/gpt-5.4-mini/fuzz_dim_bus_seal_flashback_rhyme_humor.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/fuzz_dim_bus_seal_flashback_rhyme_humor.py --trace
    python storyworlds/worlds/gpt-5.4-mini/fuzz_dim_bus_seal_flashback_rhyme_humor.py --verify
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
RHYME_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    dim: str
    bus_sound: str
    route: str

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
class Seal:
    id: str
    label: str
    splash: str
    rhyme_tail: str
    funny: str

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
class Item:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = True

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
        self.flashback_done = False

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
        c.flashback_done = self.flashback_done
        return c


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            if s:
                world.say(s)
    return out


def _r_humor(world: World) -> list[str]:
    child = world.get("child")
    seal = world.get("seal")
    if child.memes.get("giggle", 0.0) >= THRESHOLD and seal.meters.get("splash", 0.0) >= THRESHOLD:
        sig = ("humor",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["humor"] = child.memes.get("humor", 0.0) + 1
        return [f'The seal did a wobble and a wiggle, and {child.id} laughed a little jiggle.']
    return []


def _r_settle(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("calm", 0.0) >= THRESHOLD:
        sig = ("settle",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["peace"] = child.memes.get("peace", 0.0) + 1
        return ['The fuzz-dim worry grew small, like a pea in a hall.']
    return []


CAUSAL_RULES = [Rule("humor", _r_humor), Rule("settle", _r_settle)]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(setting: Setting, seal: Seal, bus: Item, snack: Item,
         child_name: str = "Mia", child_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "mother",
         tone: str = "bright") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    bus_ent = world.add(Entity(id="bus", kind="thing", type="bus", label="the bus"))
    seal_ent = world.add(Entity(id="seal", kind="character", type="seal", label=seal.label))
    bus_ent.meters["fuzz_dim"] = 1.0
    bus_ent.memes["hush"] = 1.0
    child.memes["wonder"] = 1.0
    adult.memes["care"] = 1.0

    world.say(
        f'On a fuzz-dim day, {child.id} and {adult.id} rode the bus to the seal pool. '
        f"The bus went hum-hum; the windows went blur-blur."
    )
    world.say(
        f'{child.id} pressed a cheek to the glass and said, "The bus is slow and low, '
        f'but the seal will shine like snow."'
    )

    world.para()
    child.memes["flashback"] = 1.0
    world.say(
        f'And then {child.id} remembered a flashback: last time, the same bus had bounced '
        f'like a drum, and {snack.phrase} had rolled under the seat with a tum-tum thrum.'
    )
    world.say(
        f'{adult.id} had smiled and said, "No fuss, no rush; we find what is lost, '
        f'and keep the bus a hush."'
    )

    world.para()
    child.memes["giggle"] = 1.0
    world.say(
        f'At the pool, the seal lifted its nose and gave a bright, polite pose. '
        f'{seal.funny}'
    )
    world.say(
        f'{child.id} gasped, "A seal with a squeal! That is a real funny deal!"'
    )
    seal_ent.meters["alert"] = 1.0
    seal_ent.memes["play"] = 1.0
    child.memes["rhyme"] = 1.0
    propagate(world, narrate=True)

    world.para()
    if setting.dim and bus_ent.meters["fuzz_dim"] >= THRESHOLD:
        world.say(
            f'On the ride home, {adult.id} passed {child.id} the {bus.label} snack and '
            f'said, "The day was dim, but we kept it trim."'
        )
    child.memes["calm"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f'{child.id} held {snack.label_word if hasattr(snack, "label_word") else snack.label} close '
        f'on the bus seat and waved at the seal pool going by.'
    )
    world.say(
        f'The fuzz-dim bus hummed home, and {child.id} still had a smile with a rhyme on its own.'
    )

    world.facts.update(
        child=child, adult=adult, setting=setting, seal=seal, bus=bus, snack=snack,
        tone=tone, flashed_back=True, funny=True, calm=True
    )
    return world


SETTINGS = {
    "dusk": Setting("dusk", "the seal pool by the bay", "fuzz-dim", "hum-hum", "the bay"),
    "harbor": Setting("harbor", "the harbor museum stop", "fuzz-dim", "hum-hum", "the harbor"),
}

SEALS = {
    "gray": Seal("gray", "gray seal", "It slapped the splash with a happy crash.", "squeal/deal", "It slid, then it glid, and flipped like a lid."),
    "spot": Seal("spot", "spotty seal", "It gave a wave with a flipper and a grin.", "dot/spot", "It booped its nose and posed in rows."),
}

ITEMS = {
    "cracker": Item("cracker", "crackers", "a tin of crackers", "snack"),
    "cookie": Item("cookie", "cookies", "a little bag of cookies", "snack"),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Owen", "Theo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, z, i) for s in SETTINGS for z in SEALS for i in ITEMS]


@dataclass
@dataclass
class StoryParams:
    setting: str
    seal: str
    item: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme bus-and-seal storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seal", choices=SEALS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["Mom", "Dad"])
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
              and (args.seal is None or c[1] == args.seal)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, seal, item = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["Mom", "Dad"])
    return StoryParams(setting, seal, item, name, gender, adult, "mother" if adult == "Mom" else "father")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SEALS[params.seal], Item(**ITEMS[params.item].__dict__),
                 Item(**ITEMS[params.item].__dict__), params.child_name, params.child_gender,
                 params.adult_name, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story including the words "fuzz-dim", "bus", and "seal".',
        f"Tell a short funny story where {f['child'].id} rides a fuzz-dim bus to see a seal and remembers an earlier trip in a flashback.",
        f"Write a child-friendly rhyme about a bus ride, a seal, and a little laugh at the pool.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, seal = f["child"], f["adult"], f["seal"]
    return [
        ("Who went on the bus ride?",
         f"{child.id} went with {adult.id} on the fuzz-dim bus to the seal pool."),
        ("What did {0} remember in the flashback?".format(child.id),
         f"{child.id} remembered an earlier bus trip when a snack rolled under the seat. That memory made the later ride feel like a funny rhyme instead of a worry."),
        ("What happened when the seal appeared?",
         f"The seal did a silly, splashy bit of showtime and made {child.id} laugh. The story turns from remembering to giggling when the seal starts its little performance."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a seal?", "A seal is a sea animal that swims well, slides on land, and often splashes water when it plays."),
        QAItem("What does a bus do?", "A bus carries people from one place to another on roads. It is a good ride for family trips."),
        QAItem("What does fuzz-dim mean in this story?", "It means the light is soft and a little blurry, like dusk or a sleepy evening."),
        QAItem("What is a flashback?", "A flashback is when a story remembers something that happened earlier. It helps explain why a character thinks a certain thought now."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Z, I) :- setting(S), seal(Z), item(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for z in SEALS:
        lines.append(asp.fact("seal", z))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams("dusk", "gray", "cracker", "Mia", "girl", "Mom", "mother"),
    StoryParams("harbor", "spot", "cookie", "Leo", "boy", "Dad", "father"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
