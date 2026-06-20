#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/archeology_bramble_sweeper_magic_bravery_sound_effects.py
=========================================================================================

A small, standalone storyworld in a folk-tale style: a brave child and a guide
go on an archeology dig, a thorny bramble blocks the way, and a magical sweeper
with lively sound effects helps them clear the path and uncover a treasure.

This world is intentionally compact. It still follows the shared storyworld
contract: typed entities with physical meters and emotional memes, a reasoned
Python gate, an inline ASP twin, world-grounded Q&A, trace output, JSON output,
and a verify mode that exercises normal story generation.

Seed words:
- archeology
- bramble
- sweeper

Features:
- Magic
- Bravery
- Sound Effects

Style:
- Folk Tale
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    magic: bool = False
    makes_sound: bool = False
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
class Place:
    id: str
    name: str
    wild: str
    hidden: str
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
class Hazard:
    id: str
    label: str
    thickness: int
    thorny: bool = True
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
class Sweeper:
    id: str
    label: str
    phrase: str
    effect: str
    sound: str
    power: int
    magic: bool = False
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
class Treasure:
    id: str
    label: str
    phrase: str
    glow: str
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
        return clone

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


def _r_bramble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    bramble = world.entities.get("bramble")
    if not hero or not bramble:
        return out
    if hero.meters["determination"] < THRESHOLD:
        return out
    if bramble.meters["broken"] >= THRESHOLD:
        sig = ("bramble_done",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__bramble_clear__")
    return out


CAUSAL_RULES = [Rule("bramble", "physical", _r_bramble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_ok(place: Place, hazard: Hazard, sweeper: Sweeper, treasure: Treasure) -> bool:
    return hazard.thorny and sweeper.magic and "bramble" in place.tags and treasure.id == "relic"


def sweeper_can_work(sweeper: Sweeper, hazard: Hazard) -> bool:
    return sweeper.power >= hazard.thickness


def tell(place: Place, hazard: Hazard, sweeper: Sweeper, treasure: Treasure,
         hero_name: str = "Mira", hero_gender: str = "girl",
         guide_name: str = "Ned", guide_gender: str = "boy",
         guide_kind: str = "elder", seed_hint: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name,
                            role="hero", traits=["brave", "curious"], age=7))
    guide = world.add(Entity(id="guide", kind="character", type=guide_gender, label=guide_name,
                             role="guide", traits=["wise", "steady"], age=12))
    bramble = world.add(Entity(id="bramble", type="thing", label=hazard.label, attrs={"thickness": hazard.thickness}))
    relic = world.add(Entity(id="relic", type="thing", label=treasure.label))
    tool = world.add(Entity(id="sweeper", type="thing", label=sweeper.label, magic=sweeper.magic, makes_sound=True))
    world.facts["place"] = place
    world.facts["hazard"] = hazard
    world.facts["sweeper"] = sweeper
    world.facts["treasure"] = treasure
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["guide_kind"] = guide_kind
    world.facts["tool"] = tool
    world.facts["bramble"] = bramble
    world.facts["relic"] = relic

    hero.memes["joy"] += 1
    guide.memes["calm"] += 1
    world.say(
        f"Long ago, in {place.name}, there lived {hero_name}, a little {guide_kind} of a child who loved archeology."
    )
    world.say(
        f"{hero_name} followed {guide_name} to a forgotten hill, where {place.wild} and {place.hidden} waited under the trees."
    )
    world.say(
        f"Between the stones grew {hazard.label}, thick as a sleeping hedge, and it barred the way to the old dig."
    )

    world.para()
    hero.meters["determination"] += 1
    hero.memes["bravery"] += 1
    guide.memes["warning"] += 1
    world.say(
        f"{hero_name} lifted {sweeper.phrase} and took a brave breath. {guide_name} said, "
        f'"The path is tangled, but magic can help if we use it kindly."'
    )
    world.say(
        f'"Swish-whish!" went the sweeper. The leaves trembled, and a bright little {sweeper.sound} leaped through the air.'
    )
    if not sweeper_can_work(sweeper, hazard):
        world.say(
            f"But the bramble was too thick, and the little spell could not finish the job."
        )
        world.facts["outcome"] = "blocked"
        return world

    bramble.meters["broken"] += 1
    bramble.meters["cleared"] += 1
    if sweeper.magic:
        guide.memes["hope"] += 1
        hero.memes["bravery"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"With one more cry of '{sweeper.sound}!', the thorny wall parted at last."
    )
    world.say(
        f"Under the roots they found {treasure.phrase}, shining with {treasure.glow}."
    )
    world.say(
        f"{hero_name} smiled so wide that even {guide_name} laughed, and the old hill seemed to bow like a grateful king."
    )
    world.say(
        f"That night, the villagers told the tale of {hero_name} and the magic sweeper, and the bramble was only a memory."
    )
    world.facts["outcome"] = "found"
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hazard in HAZARDS:
            for sweeper in SWEEPERS:
                for treasure in TREASURES:
                    if reasonableness_ok(place, hazard, sweeper, treasure) and sweeper_can_work(sweeper, hazard):
                        combos.append((place.id, hazard.id, treasure.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    hazard: str
    sweeper: str
    treasure: str
    hero_name: str
    hero_gender: str
    guide_name: str
    guide_gender: str
    guide_kind: str
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


PLACES = [
    Place("greenhill", "the Green Hill", "wild bracken and old moss", "a buried stone door", {"bramble"}),
    Place("orchard", "the old orchard", "apple branches and nettles", "a low root cave", {"bramble"}),
]
HAZARDS = [
    Hazard("bramble", "the bramble", 2, True, {"bramble"}),
    Hazard("thornwall", "the thorn wall", 3, True, {"bramble"}),
]
SWEEPERS = [
    Sweeper("magic_sweeper", "the magic sweeper", "a magic sweeper", "clears brambles", "swish-whish", 3, True, {"magic", "sound"}),
    Sweeper("star_sweeper", "the star-sweeper", "a star-sweeper", "clears brambles", "shimmer-swish", 4, True, {"magic", "sound"}),
]
TREASURES = [
    Treasure("relic", "the lost relic", "a lost relic", "a warm gold glow", {"archeology"}),
    Treasure("cup", "the old cup", "an old cup", "a soft silver gleam", {"archeology"}),
]
NAMES = ["Mira", "Lena", "Tob", "Ned", "Pip", "Sia", "Arin", "Moss"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: archeology, bramble, sweeper, magic, bravery, and sound effects.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--hazard", choices=[h.id for h in HAZARDS])
    ap.add_argument("--sweeper", choices=[s.id for s in SWEEPERS])
    ap.add_argument("--treasure", choices=[t.id for t in TREASURES])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-kind", default="elder")
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
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.sweeper is None or c[2] == args.sweeper)
              and (args.treasure is None or c[2] == args.treasure or True)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, hazard_id, treasure_id = rng.choice(sorted(combos))
    place = next(p for p in PLACES if p.id == place_id)
    hazard = next(h for h in HAZARDS if h.id == hazard_id)
    sweeper = next(s for s in SWEEPERS if s.id == (args.sweeper or rng.choice([s.id for s in SWEEPERS])))
    treasure = next(t for t in TREASURES if t.id == (args.treasure or treasure_id))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(NAMES)
    guide_name = args.guide or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(place.id, hazard.id, sweeper.id, treasure.id, hero_name, hero_gender, guide_name, guide_gender, args.guide_kind)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a small child that includes the words "archeology", "bramble", and "sweeper".',
        f"Tell a brave little story where {f['hero'].label} and {f['guide'].label} use a magic sweeper to cross a bramble and uncover treasure.",
        f"Write a magical story with sound effects that begins with archeology and ends with a thorny path opening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    hazard = f["hazard"]
    sweeper = f["sweeper"]
    treasure = f["treasure"]
    return [
        QAItem(
            question="What was the child doing?",
            answer=f"{hero.label} was doing archeology, looking for something old and special in the hill."
        ),
        QAItem(
            question="What blocked the way?",
            answer=f"The bramble blocked the way. It was thick and thorny, so the path was hard to cross."
        ),
        QAItem(
            question="How did they get through?",
            answer=f"They used {sweeper.label}. Its magic sound effect helped clear the bramble, and their brave choice made the path open."
        ),
        QAItem(
            question="What did they find at the end?",
            answer=f"They found {treasure.phrase}, glowing with {treasure.glow}. That showed the old hill was hiding a real treasure."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is archeology?", "Archeology is the study of old things from long ago, like stones, pots, and hidden ruins."),
        QAItem("What is a bramble?", "A bramble is a prickly tangle of bushes and thorns that can scratch your skin."),
        QAItem("What does a sweeper do?", "A sweeper is a tool or magical helper that clears away leaves, dust, or tangled things."),
        QAItem("Why are sound effects fun in stories?", "Sound effects make a story feel lively, so children can almost hear the action as it happens."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.magic:
            bits.append("magic=True")
        if e.makes_sound:
            bits.append("makes_sound=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("greenhill", "bramble", "magic_sweeper", "relic", "Mira", "girl", "Ned", "boy", "elder"),
    StoryParams("orchard", "thornwall", "star_sweeper", "cup", "Pip", "boy", "Lena", "girl", "elder"),
]


def explain_rejection() -> str:
    return "(No story: this choice does not make a clear, magical bramble problem with a real solution.)"


ASP_RULES = r"""
valid(P,H,S,T) :- place(P), hazard(H), sweeper(S), treasure(T), thorny(H), magic(S), bramble_place(P), strong_enough(S,H), relic(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        if "bramble" in p.tags:
            lines.append(asp.fact("bramble_place", p.id))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h.id))
        if h.thorny:
            lines.append(asp.fact("thorny", h.id))
    for s in SWEEPERS:
        lines.append(asp.fact("sweeper", s.id))
        if s.magic:
            lines.append(asp.fact("magic", s.id))
        for t in TREASURES:
            if s.power >= next(h.thickness for h in HAZARDS if h.id == "bramble"):
                lines.append(asp.fact("strong_enough", s.id, "bramble"))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t.id))
        if "archeology" in t.tags:
            lines.append(asp.fact("relic", t.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python disagree.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, hazard=None, sweeper=None, treasure=None, name=None, gender=None, guide=None, guide_gender=None, guide_kind="elder"), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        next(p for p in PLACES if p.id == params.place),
        next(h for h in HAZARDS if h.id == params.hazard),
        next(s for s in SWEEPERS if s.id == params.sweeper),
        next(t for t in TREASURES if t.id == params.treasure),
        params.hero_name, params.hero_gender, params.guide_name, params.guide_gender, params.guide_kind
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
