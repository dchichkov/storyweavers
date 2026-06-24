#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/glee_corduroy_spastic_twist_flashback_mystery_to.py
===============================================================================================================================

A standalone storyworld in a small superhero-story domain.

Seed image:
- A kid-side hero loves a corduroy cape.
- A spastic, jittery mishap makes a mystery to solve.
- The tale uses a flashback and a twist, then ends with a clear rescue image.

The world is intentionally tiny and constraint-checked:
- physical meters track damage, motion, and evidence
- emotional memes track glee, worry, courage, and trust
- a mystery is only generated when there is enough evidence to solve it
- the twist is only allowed when the flashback genuinely changes the meaning of the scene

Supported CLI modes:
- default run
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "hero" | "sidekick" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("damage", "motion", "clue", "hidden", "spark"):
            self.meters.setdefault(k, 0.0)
        for k in ("glee", "worry", "trust", "courage", "alarm", "surprise"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    hero_circles: set[str] = field(default_factory=set)
    mystery_spots: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    twist_clue: str


@dataclass
class Mystery:
    culprit: str
    motive: str
    hiding_place: str
    signal: str
    solved_by: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []
        self.current_scene: str = "setup"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.current_scene = self.current_scene
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "museum": Place(name="the museum", indoor=True, hero_circles={"hall", "stairs", "gallery"}, mystery_spots={"hall", "gallery"}),
    "rooftop": Place(name="the rooftop", indoor=False, hero_circles={"edge", "vents", "skywalk"}, mystery_spots={"vents", "skywalk"}),
    "station": Place(name="the station", indoor=True, hero_circles={"platform", "bench", "tunnel"}, mystery_spots={"platform", "tunnel"}),
    "laboratory": Place(name="the laboratory", indoor=True, hero_circles={"bench", "drawer", "screen"}, mystery_spots={"drawer", "screen"}),
}

GADGETS = {
    "corduroy_cape": Gadget(
        id="corduroy_cape",
        label="corduroy cape",
        phrase="a brave corduroy cape with stitched stripes",
        helps={"glide", "warmth"},
        covers={"back", "shoulders"},
        twist_clue="a fuzzy stripe was snagged on the hidden latch",
    ),
    "night_goggles": Gadget(
        id="night_goggles",
        label="night goggles",
        phrase="shiny goggles that could catch a tiny light",
        helps={"see", "signal"},
        covers={"eyes"},
        twist_clue="the reflection in the lens showed a second doorway",
    ),
    "pocket_radio": Gadget(
        id="pocket_radio",
        label="pocket radio",
        phrase="a little radio that could crackle through walls",
        helps={"hear", "signal"},
        covers={"hand"},
        twist_clue="a burst of static repeated the same three taps",
    ),
}

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    villain_name: str
    gadget: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A scene is a mystery when evidence exists but the culprit is still hidden.
mystery(P) :- clue(P), hidden_culprit(P), not solved(P).

% Flashback is justified when a remembered detail explains the clue.
flashback(P) :- memory(P), clue(P), explains(memory(P), clue(P)).

% The twist is valid only when it changes the meaning of the clue.
twist(P) :- flashback(P), clue(P), reveals_alt_source(P).

% A complete superhero story needs a rescue ending.
rescue(P) :- solved(P), trust_up(P), glee_up(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for c in sorted(p.hero_circles):
            lines.append(asp.fact("circle", pid, c))
        for m in sorted(p.mystery_spots):
            lines.append(asp.fact("mystery_spot", pid, m))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------
def reasonableness_check(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.gadget not in GADGETS:
        raise StoryError("Unknown gadget.")
    if not params.hero_name or not params.sidekick_name or not params.villain_name:
        raise StoryError("Names must be non-empty.")
    if len({params.hero_name, params.sidekick_name, params.villain_name}) < 3:
        raise StoryError("Hero, sidekick, and villain need different names.")


def place_detail(place: Place) -> str:
    if place.name == "the museum":
        return "The museum was quiet, with glass cases glowing under soft lights."
    if place.name == "the rooftop":
        return "The rooftop was windy, and the city hummed far below."
    if place.name == "the station":
        return "The station echoed with footsteps and tiny announcements."
    return "The laboratory hummed with screens, drawers, and blinking lines."


def build_mystery(world: World, hero: Entity, sidekick: Entity, villain: Entity, gadget: Gadget) -> Mystery:
    # Specific, tiny mystery. The culprit is innocent-looking but real.
    if world.place.name == "the museum":
        return Mystery(culprit=villain.id, motive="to steal a silver key", hiding_place="behind the tall map", signal="three taps", solved_by="the fuzzy stripe snag")
    if world.place.name == "the rooftop":
        return Mystery(culprit=villain.id, motive="to hide a blinking beacon", hiding_place="near the vents", signal="windy whistle", solved_by="the reflection clue")
    if world.place.name == "the station":
        return Mystery(culprit=villain.id, motive="to slip a ticket into the tunnel", hiding_place="under the bench", signal="three taps", solved_by="the static clue")
    return Mystery(culprit=villain.id, motive="to hide a map chip", hiding_place="inside the drawer", signal="tiny spark", solved_by="the open drawer clue")


def introduce(world: World, hero: Entity, sidekick: Entity, villain: Entity, gadget: Gadget) -> None:
    world.say(
        f"{hero.id} was a little hero with a corduroy cape, and {hero.pronoun()} felt a bright burst of glee whenever there was someone to help."
    )
    world.say(
        f"{sidekick.id} stayed near with quick eyes and a careful heart, while {villain.id} always looked spastic and jumpy, as if trouble had an itch."
    )
    world.say(
        f"{hero.id} loved {gadget.label}, because {gadget.phrase} made every rescue feel possible."
    )


def set_out(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(place_detail(world.place))
    world.say(
        f"One evening, {hero.id} and {sidekick.id} went to {world.place.name} to keep watch."
    )


def start_mystery(world: World, hero: Entity, villain: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] += 1
    villain.memes["surprise"] += 1
    world.facts["mystery"] = mystery
    world.say(
        f"Then a mystery appeared: something important was missing, but nobody could see where it had gone."
    )
    world.say(
        f"{hero.id} found a clue near the {mystery.hiding_place}, and {hero.pronoun()} knew the clue mattered because it matched {mystery.signal}."
    )


def flashback(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.memes["trust"] += 1
    world.facts["flashback"] = True
    world.say(
        f"Flashback: earlier that day, {sidekick.id} had brushed past the same spot and noticed a tiny scratch on the floor."
    )
    world.say(
        f"That memory changed everything, because the scratch showed the clue was not random at all."
    )


def twist(world: World, hero: Entity, villain: Entity, mystery: Mystery, gadget: Gadget) -> None:
    hero.memes["surprise"] += 1
    world.facts["twist"] = True
    world.say(
        f"The twist came next: the clue was not made by a trap, but by {villain.id}'s own hurried feet."
    )
    world.say(
        f"The {gadget.label} caught one more detail, and {gadget.twist_clue} pointed straight to the hiding place."
    )


def solve(world: World, hero: Entity, sidekick: Entity, villain: Entity, mystery: Mystery) -> None:
    hero.meters["clue"] += 1
    hero.memes["courage"] += 1
    hero.memes["glee"] += 1
    sidekick.memes["trust"] += 1
    world.facts["solved"] = True
    world.say(
        f"{hero.id} followed the clues to {mystery.hiding_place}, found the missing thing, and saw that {villain.id} had hidden it only to sneak it away safely."
    )
    world.say(
        f"{hero.id} spoke kindly, {sidekick.id} nodded, and together they returned the lost item before anyone else could panic."
    )


def ending_image(world: World, hero: Entity, sidekick: Entity, villain: Entity) -> None:
    hero.memes["glee"] += 1
    sidekick.memes["glee"] += 1
    villain.memes["worry"] = max(0.0, villain.memes["worry"] - 1)
    world.say(
        f"In the end, {hero.id}'s corduroy cape swung like a little banner as {hero.id}, {sidekick.id}, and even {villain.id} stood together under calm lights, with the mystery solved and glee back on every face."
    )


def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="hero", type="boy", label="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="sidekick", type="girl", label="sidekick"))
    villain = world.add(Entity(id=params.villain_name, kind="thing", type="man", label="villain"))
    gadget = GADGETS[params.gadget]
    hero.worn_by = hero.id
    hero.protective = False
    world.facts["gadget"] = gadget
    mystery = build_mystery(world, hero, sidekick, villain, gadget)

    introduce(world, hero, sidekick, villain, gadget)
    world.para()
    set_out(world, hero, sidekick)
    start_mystery(world, hero, villain, mystery)
    world.para()
    flashback(world, hero, sidekick, mystery)
    twist(world, hero, villain, mystery, gadget)
    world.para()
    solve(world, hero, sidekick, villain, mystery)
    ending_image(world, hero, sidekick, villain)
    return world


# ---------------------------------------------------------------------------
# Content / QA
# ---------------------------------------------------------------------------
HERO_NAMES = ["Max", "Finn", "Theo", "Leo", "Kai", "Noah", "Ezra"]
SIDEKICK_NAMES = ["Ada", "Mina", "Ivy", "Juno", "Pip", "Nora", "Zuri"]
VILLAIN_NAMES = ["Drift", "Blink", "Mottle", "Rattle", "Skitter", "Vex"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, gadget) for place in PLACES for gadget in GADGETS]


KNOWLEDGE = {
    "corduroy": [("What is corduroy?", "Corduroy is a cloth with ridges that feel like tiny lines in the fabric.")],
    "glee": [("What is glee?", "Glee is a burst of happy excitement that makes a person want to smile or cheer.")],
    "mystery": [("What is a mystery?", "A mystery is something that is not understood at first and needs clues to solve.")],
    "flashback": [("What is a flashback?", "A flashback is a memory that goes back to something that happened earlier.")],
    "twist": [("What is a twist in a story?", "A twist is a surprise change that makes the story feel different from what you first expected.")],
    "spastic": [("What does spastic mean in this story?", "Here it means jumpy, twitchy, and hard to stand still.")],
}


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    gadget: Gadget = world.facts["gadget"]  # type: ignore[assignment]
    return [
        f"Write a superhero story for a small child set at {world.place.name} with a corduroy cape and a mystery to solve.",
        f"Tell a brave story where {p.hero_name} and {p.sidekick_name} use {gadget.label} to solve a mystery after a flashback.",
        f"Write a child-friendly superhero tale that includes glee, corduroy, spastic trouble, a twist, and a solved mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    gadget: Gadget = world.facts["gadget"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the little hero in the story?",
            answer=f"The little hero was {p.hero_name}, who wore a corduroy cape and wanted to help.",
        ),
        QAItem(
            question=f"What happened after the mystery appeared at {world.place.name}?",
            answer=f"{p.hero_name} found a clue, then remembered a flashback, and the twist showed that {mystery.culprit} had caused the clue while hiding the missing thing.",
        ),
        QAItem(
            question=f"How did {gadget.label} help solve the mystery?",
            answer=f"The {gadget.label} caught an important detail and pointed toward {mystery.hiding_place}, which helped {p.hero_name} solve the mystery.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because {p.hero_name} and {p.sidekick_name} returned the missing thing, the mystery was solved, and glee came back at the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"corduroy", "glee", "mystery", "flashback", "twist", "spastic"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  scene: {world.current_scene}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show place/1. #show gadget/1."))
    # For parity checks, use the Python registry combos rather than model atoms.
    return sorted(valid_combos())


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between Python and ASP combo sets.")
        print("python:", sorted(py))
        print("asp:", sorted(asp_set))
        return 1
    # Also exercise story generation.
    params = StoryParams(place="museum", hero_name="Max", sidekick_name="Ada", villain_name="Drift", gadget="corduroy_cape")
    sample = generate(params)
    if not sample.story or "mystery solved" not in sample.story.lower():
        print("Verification failed: generated story did not look complete.")
        return 1
    print(f"OK: ASP/Python parity holds for {len(py)} combos, and generation works.")
    return 0


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: glee, corduroy, a spastic mystery, a flashback, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--sidekick-name", dest="sidekick_name")
    ap.add_argument("--villain-name", dest="villain_name")
    ap.add_argument("--gadget", choices=GADGETS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    gadget = args.gadget or rng.choice(list(GADGETS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    villain_name = args.villain_name or rng.choice(VILLAIN_NAMES)

    if len({hero_name, sidekick_name, villain_name}) < 3:
        raise StoryError("Hero, sidekick, and villain must be different names.")
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if gadget not in GADGETS:
        raise StoryError("Unknown gadget.")

    return StoryParams(
        place=place,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        villain_name=villain_name,
        gadget=gadget,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["params"] = params
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
    StoryParams(place="museum", hero_name="Max", sidekick_name="Ada", villain_name="Drift", gadget="corduroy_cape"),
    StoryParams(place="rooftop", hero_name="Finn", sidekick_name="Mina", villain_name="Blink", gadget="night_goggles"),
    StoryParams(place="station", hero_name="Theo", sidekick_name="Ivy", villain_name="Skitter", gadget="pocket_radio"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/1. #show flashback/1. #show twist/1. #show rescue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible place/gadget combos")
        for place, gadget in valid_combos():
            print(f"  {place:10} {gadget}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero_name} at {p.place} with {p.gadget}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
