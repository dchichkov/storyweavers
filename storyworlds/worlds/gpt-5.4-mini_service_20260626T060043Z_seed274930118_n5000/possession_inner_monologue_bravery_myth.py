#!/usr/bin/env python3
"""
storyworlds/worlds/possession_inner_monologue_bravery_myth.py
==============================================================

A small mythic story world about possession, inner monologue, and bravery.

Seed tale, imagined and then simulated:
A child finds a shining relic and feels the pull to keep it. On the road
home, the child hears an inner voice that speaks in quiet words and gathers
courage. The child chooses bravery, returns what was not theirs, and receives
a blessing that changes the ending.

The world model tracks:
- physical measures: holding, distance, darkness, travel, warmth
- emotional memes: desire, fear, courage, guilt, relief, pride, wonder

The prose is generated from those state changes, not from a frozen template.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    possessed_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["holding", "distance", "darkness", "travel", "warmth"]:
            self.meters.setdefault(k, 0.0)
        for k in ["desire", "fear", "courage", "guilt", "relief", "pride", "wonder", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Place:
    name: str
    mood: str
    path: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    spirit_name: str
    return_place: str
    glow: str
    blessing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_character()]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_dark_fear(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters["distance"] > 0.5 and hero.memes["fear"] >= THRESHOLD:
            sig = ("dark_fear", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.meters["darkness"] += 1
            out.append(f"The path grew darker around {hero.id}.")
    return out


def _r_inner_voice(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["fear"] < THRESHOLD or hero.meters["darkness"] < THRESHOLD:
            continue
        sig = ("inner_voice", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["wonder"] += 1
        out.append("A quiet inner voice answered, soft as a candle.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["courage"] < THRESHOLD or hero.memes["fear"] < THRESHOLD:
            continue
        sig = ("bravery", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["pride"] += 1
        out.append(f"{hero.id} stood steady instead of turning back.")
    return out


def _r_return_relic(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "relic" or not e.possessed_by:
            continue
        holder = world.get(e.possessed_by)
        if holder.memes["courage"] < THRESHOLD:
            continue
        sig = ("return", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.possessed_by = None
        holder.meters["holding"] = 0
        holder.memes["guilt"] += -1
        holder.memes["relief"] += 1
        out.append(f"{holder.id} lifted the relic with both hands and gave it back.")
    return out


def _r_blessing(world: World) -> list[str]:
    out: list[str] = []
    relic = next((e for e in world.entities.values() if e.kind == "relic"), None)
    hero = next((e for e in world.characters() if e.kind == "character" and e.memes["relief"] >= THRESHOLD), None)
    if not relic or not hero:
        return out
    sig = ("blessing", relic.id, hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["love"] += 1
    hero.meters["warmth"] += 1
    out.append(f"The relic answered with a blessing, and {hero.id} felt warm from the inside out.")
    return out


CAUSAL_RULES = [
    Rule("dark_fear", _r_dark_fear),
    Rule("inner_voice", _r_inner_voice),
    Rule("bravery", _r_bravery),
    Rule("return", _r_return_relic),
    Rule("blessing", _r_blessing),
]


PLACES = {
    "forest": Place(name="the deep forest", mood="green hush", path="a narrow root-road", affords={"walk", "hide", "listen"}),
    "hill": Place(name="the moonlit hill", mood="silver wind", path="a steep stony path", affords={"walk", "climb", "listen"}),
    "river": Place(name="the river shrine", mood="cold shining water", path="a wet stone path", affords={"walk", "listen", "kneel"}),
}

RELICS = {
    "sun_disk": Relic(
        id="sun_disk",
        label="sun disk",
        phrase="a small golden sun disk",
        spirit_name="Sun Keeper",
        return_place="the river shrine",
        glow="bright as dawn",
        blessing="the promise of morning",
        tags={"sun", "gold", "shrine"},
    ),
    "moon_shell": Relic(
        id="moon_shell",
        label="moon shell",
        phrase="a pale shell that shone like a moon",
        spirit_name="Moon Listener",
        return_place="the moonlit hill",
        glow="soft as milklight",
        blessing="quiet dreams for the road home",
        tags={"moon", "shell", "night"},
    ),
    "star_bell": Relic(
        id="star_bell",
        label="star bell",
        phrase="a tiny silver bell of stars",
        spirit_name="Star Shepherd",
        return_place="the deep forest",
        glow="clear as winter frost",
        blessing="a path that never lost its way",
        tags={"star", "bell", "forest"},
    ),
}

HERO_NAMES = ["Arin", "Mira", "Seth", "Liora", "Tavi", "Noa", "Kian", "Iri"]
PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]
HERO_TYPES = ["boy", "girl"]

MYTH_TONES = [
    "ancient and bright",
    "quiet and holy",
    "windy and old",
    "moonlit and careful",
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    relic = args.relic or rng.choice(list(RELICS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if relic not in RELICS:
        raise StoryError("Unknown relic.")
    return StoryParams(
        place=place,
        relic=relic,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
    )


def tell(place: Place, relic_cfg: Relic, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    relic = world.add(Entity(
        id=relic_cfg.id,
        kind="relic",
        type="relic",
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=relic_cfg.spirit_name,
        keeper=relic_cfg.spirit_name,
    ))
    spirit = world.add(Entity(
        id="spirit",
        kind="spirit",
        type="spirit",
        label=relic_cfg.spirit_name,
    ))

    hero.meters["holding"] = 1
    hero.memes["desire"] += 1
    hero.memes["fear"] += 1
    relic.possessed_by = hero.id

    world.say(f"In {place.name}, where the air was {place.mood}, {hero.id} found {relic_cfg.phrase}.")
    world.say(
        f"{hero.id} held it close and thought, 'It is mine now, and I can keep it if I am quick.'"
    )
    world.say(
        f"But {hero.pronoun('possessive')} {parent_type} saw the shine and said, "
        f'"That light does not belong to us."'
    )

    world.para()
    hero.meters["distance"] = 1
    world.say(
        f"Then {hero.id} walked {place.path}, and the road made the relic feel heavier in {hero.pronoun('possessive')} hands."
    )
    hero.memes["fear"] += 1
    hero.memes["guilt"] += 1
    world.say(
        f"{hero.id} thought, 'If I keep it, the night will remember me. If I return it, will I be brave enough?'"
    )
    propagate(world)

    world.para()
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} took a slow breath and thought, 'I can be afraid and still do the right thing.'"
    )
    if hero.memes["wonder"] >= THRESHOLD:
        world.say("The quiet voice in the dark seemed to nod.")
    propagate(world)

    world.para()
    if relic.possessed_by == hero.id:
        world.say(
            f"At last, {hero.id} knelt before {relic_cfg.spirit_name} and returned {relic_cfg.phrase} to its true home."
        )
    else:
        world.say(
            f"At last, {hero.id} knelt before {relic_cfg.spirit_name}, and the relic was already open in the hero's hands for returning."
        )
    world.say(
        f"The {relic_cfg.spirit_name} lifted the relic toward the sky, and its glow became {relic_cfg.glow}."
    )
    propagate(world)

    world.para()
    world.say(
        f"{hero.id} went home with empty hands but a warm chest, carrying {relic_cfg.blessing} instead of the lost thing."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        relic=relic,
        spirit=spirit,
        relic_cfg=relic_cfg,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic_cfg = f["relic_cfg"]
    place = f["place"]
    return [
        f"Write a mythic story for a small child about possession, a found treasure, and a brave choice at {place.name}.",
        f"Tell a short ancient-feeling tale where {hero.id} thinks, 'It is mine now,' but learns to return {relic_cfg.phrase}.",
        f"Write a gentle myth with inner monologue and bravery that ends with {relic_cfg.spirit_name} giving a blessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    relic_cfg = f["relic_cfg"]
    place = f["place"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {place.name}?",
            answer=f"{hero.id} found {relic_cfg.phrase}, a shining thing that felt precious in {hero.pronoun('possessive')} hands.",
        ),
        QAItem(
            question=f"What did {hero.id} think about the relic at first?",
            answer=f"{hero.id} thought, 'It is mine now, and I can keep it if I am quick.' That was the pull of possession.",
        ),
        QAItem(
            question=f"Why did {hero.id} hesitate on the road home?",
            answer=(
                f"{hero.id} felt fear and guilt because the relic did not truly belong to {hero.pronoun('object')}. "
                f"{hero.pronoun('possessive').capitalize()} {parent.type} had warned that the light should go back to its true keeper."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=(
                f"{hero.id} answered the quiet inner voice and chose to return {relic_cfg.phrase}, "
                f"even though keeping it would have been easier."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"The relic went back to {relic_cfg.spirit_name}, and {hero.id} went home with relief and pride instead of possession."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    relic_cfg = f["relic_cfg"]
    return [
        QAItem(
            question="What is possession?",
            answer="Possession means having or holding something as your own, or wanting to keep it for yourself.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing to do the right thing even when you feel afraid.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice of thoughts inside your own mind.",
        ),
        QAItem(
            question=f"What kind of glow did the {relic_cfg.label} have?",
            answer=f"It shone {relic_cfg.glow}.",
        ),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.possessed_by:
            bits.append(f"possessed_by={e.possessed_by}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
relic(R) :- thing(R), relic_id(R).

possesses(H, R) :- relic_id(R), held_by(R, H).
at_risk(H) :- possesses(H, R), wants_to_keep(H, R).
inner_voice(H) :- hero(H), afraid(H), dark_path(H).
brave(H) :- hero(H), afraid(H), chooses_right(H).
returns(R) :- relic_id(R), brave(H), possesses(H, R).
blessed(H) :- returns(R), relic_id(R), spirit_gives_blessing(R, H).

#show hero/1.
#show relic_id/1.
#show possesses/2.
#show at_risk/1.
#show inner_voice/1.
#show brave/1.
#show returns/1.
#show blessed/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_id", pid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic_id", rid))
        lines.append(asp.fact("spirit_gives_blessing", rid, relic.spirit_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show relic_id/1."))
    asp_ids = sorted(set(asp.atoms(model, "relic_id")))
    py_ids = sorted((rid,) for rid in RELICS)
    if asp_ids == py_ids:
        print(f"OK: ASP registry matches Python registry ({len(py_ids)} relics).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("  ASP:", asp_ids)
    print("  PY :", py_ids)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic possession storyworld with inner monologue and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], RELICS[params.relic], params.hero_name, params.hero_type, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="river", relic="sun_disk", hero_name="Arin", hero_type="boy", parent_type="mother"),
    StoryParams(place="hill", relic="moon_shell", hero_name="Mira", hero_type="girl", parent_type="grandmother"),
    StoryParams(place="forest", relic="star_bell", hero_name="Tavi", hero_type="boy", parent_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show relic_id/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
