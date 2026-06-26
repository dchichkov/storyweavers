#!/usr/bin/env python3
"""
storyworlds/worlds/myth_provoke_dear_surprise_adventure.py
===========================================================

A small adventure story world about a myth, a provocation, and a dear surprise.

Premise:
- A child explorer hears a local myth about a hidden path.
- They want to provoke the old place into showing its secret.
- A guide warns them that the surprise might be tricky, but not bad.
- The turn is a triggered reveal: a hidden bridge, stair, or passage appears.
- The ending proves the world changed: the path is open, the fear has fallen,
  and wonder is higher than before.

The script keeps the world tiny and constraint-driven:
- physical meters: dust, dark, open_path, sparkle, treasure
- emotional memes: curiosity, caution, bravery, fear, trust, wonder, relief

The child-facing prose is authored from simulated state, not from a frozen template.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Myth:
    id: str
    title: str
    rumor: str
    trigger: str
    surprise: str
    reveal: str
    wonder: str
    place_tags: set[str] = field(default_factory=set)
    trigger_tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    type: str
    label: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    active_myth: Optional[Myth] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c.active_myth = copy.deepcopy(self.active_myth)
        return c


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    myth: str
    trigger: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "old_temple": Setting(place="the old temple", kind="ruins", affords={"listen", "provoke", "reveal"}),
    "moon_bridge": Setting(place="the moon bridge", kind="bridge", affords={"listen", "provoke", "reveal"}),
    "forest_shrine": Setting(place="the forest shrine", kind="grove", affords={"listen", "provoke", "reveal"}),
    "cave_gate": Setting(place="the cave gate", kind="cave", affords={"listen", "provoke", "reveal"}),
}

MYTHS = {
    "hidden_bridge": Myth(
        id="hidden_bridge",
        title="the myth of the hidden bridge",
        rumor="a bridge that appears when someone tells the truth to the stones",
        trigger="tap the star-stone",
        surprise="a narrow bridge of glowing roots rose from the ground",
        reveal="the path to the opposite hill",
        wonder="the roots shimmered like little silver ropes",
        place_tags={"bridge", "grove", "ruins"},
        trigger_tags={"star-stone", "tap"},
    ),
    "sleeping_gate": Myth(
        id="sleeping_gate",
        title="the myth of the sleeping gate",
        rumor="an old gate that wakes when a brave voice calls it kindly",
        trigger="call the gate by its true name",
        surprise="the gate yawned open with a deep stone sigh",
        reveal="a secret stair under the hill",
        wonder="dust floated up like tiny gold fish",
        place_tags={"cave", "ruins"},
        trigger_tags={"name", "call"},
    ),
    "dear_lantern": Myth(
        id="dear_lantern",
        title="the myth of the dear lantern",
        rumor="a lantern that answers a careful knock with a friendly light",
        trigger="knock on the lantern door",
        surprise="a warm lantern light blinked awake",
        reveal="a hidden room with a map on the wall",
        wonder="the light made the room feel safe and bright",
        place_tags={"grove", "ruins", "cave"},
        trigger_tags={"knock", "lantern"},
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Maya", "Nora", "Lina", "Zoe", "Ava", "Elena", "Mira"]
BOY_NAMES = ["Theo", "Milo", "Eli", "Noah", "Finn", "Arlo", "Jasper"]
TRAITS = ["curious", "brave", "careful", "lively", "dreamy", "spirited"]
GUIDES = [
    Guide("grandpa", "man", "Grandpa"),
    Guide("aunt", "woman", "Aunt June"),
    Guide("ranger", "woman", "the ranger"),
    Guide("mentor", "man", "the old guide"),
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, myth_id: str, trigger: str) -> bool:
    myth = MYTHS[myth_id]
    setting = SETTINGS[place]
    return setting.kind in myth.place_tags and trigger in myth.trigger_tags


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for myth_id in MYTHS:
            for trigger in {MYTHS[myth_id].trigger}:
                if valid_combo(place, myth_id, trigger):
                    out.append((place, myth_id, trigger))
    return out


def explain_rejection(place: str, myth_id: str, trigger: str) -> str:
    myth = MYTHS[myth_id]
    setting = SETTINGS[place]
    return (
        f"(No story: {myth.title} does not fit {setting.place}, or the chosen action "
        f"would not really provoke a surprise there. Try a place whose kind matches "
        f"the myth, and use the myth's own trigger.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, guide: Entity, myth: Myth) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} "
        f"who loved old paths and brave stories."
    )
    world.say(
        f"One evening, {guide.label} told {hero.id} about {myth.title}: "
        f"{myth.rumor}."
    )


def arrive(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"{hero.id} and {guide.label} went to {world.setting.place}, where the stones "
        f"looked quiet and older than a hundred bedtime tales."
    )


def listen_to_myth(world: World, hero: Entity, myth: Myth) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} listened closely. The myth sounded {myth.title.split('the myth of ')[-1] if 'the myth of' in myth.title else 'mysterious'}, "
        f"and {hero.pronoun('possessive')} eyes kept drifting to the dark corner where the secret might hide."
    )


def warn(world: World, guide: Entity, hero: Entity, myth: Myth) -> None:
    hero.memes["caution"] += 1
    world.say(
        f'"If you provoke the place too hard," {guide.label} said, '
        f'"you may get a surprise, dear one. Let the stones answer gently."'
    )


def provoke(world: World, hero: Entity, myth: Myth) -> None:
    hero.memes["bravery"] += 1
    hero.memes["fear"] += 0.5
    world.say(
        f"But {hero.id} took a breath and chose to {myth.trigger}, just to see if the old myth was true."
    )


def reveal(world: World, hero: Entity, guide: Entity, myth: Myth) -> None:
    sig = ("reveal", myth.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["surprise"] += 1
    hero.memes["wonder"] += 2
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["relief"] += 1
    world.say(f"At once, {myth.surprise}.")
    world.say(
        f"It was not a scary surprise at all. It opened {myth.reveal}, and {myth.wonder}."
    )


def resolve(world: World, hero: Entity, guide: Entity) -> None:
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} smiled up at {guide.label}, and together they walked the new path as if it had been waiting for them."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def tell(setting: Setting, myth: Myth, trigger: str, name: str, gender: str,
         guide_name: str, trait: str) -> World:
    world = World(setting, active_myth=myth)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little", trait, "stubborn"],
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type="woman" if "June" in guide_name or guide_name == "Aunt June" or guide_name == "the ranger" else "man",
        label=guide_name,
    ))

    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["myth"] = myth
    world.facts["trigger"] = trigger
    world.facts["setting"] = setting

    intro(world, hero, guide, myth)
    world.para()
    arrive(world, hero, guide)
    listen_to_myth(world, hero, myth)
    warn(world, guide, hero, myth)
    provoke(world, hero, myth)
    world.para()
    reveal(world, hero, guide, myth)
    resolve(world, hero, guide)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, myth = f["hero"], f["myth"]
    return [
        f'Write a short adventure story for a young child that includes the words "myth", "provoke", and "dear".',
        f"Tell a gentle adventure about {hero.id} who hears {myth.title} and tries to provoke a surprise in a safe way.",
        f"Write a child-friendly quest story with an old place, a hidden reveal, and a warm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, myth = f["hero"], f["guide"], f["myth"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who heard {myth.title} and went to {place}?",
            answer=f"{hero.id} heard {myth.title} and went to {place} with {guide.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} do to provoke the surprise?",
            answer=f"{hero.id} chose to {f['trigger']}, which made the old place reveal its secret.",
        ),
        QAItem(
            question=f"Was the surprise bad or good?",
            answer="It was a good surprise. It opened a hidden path and made the child feel wonder instead of fear.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {guide.label} walking the new path together, with the secret safely revealed.",
        ),
    ]


KNOWLEDGE = {
    "myth": [
        ("What is a myth?", "A myth is an old story people tell to explain something or to share wonder about the world."),
    ],
    "surprise": [
        ("What is a surprise?", "A surprise is something unexpected that suddenly happens or is suddenly revealed."),
    ],
    "bridge": [
        ("What is a bridge for?", "A bridge helps people cross over water, a gap, or another hard-to-cross place."),
    ],
    "lantern": [
        ("What does a lantern do?", "A lantern gives light so people can see in dark places."),
    ],
    "stair": [
        ("What is a stair?", "A stair is one step in a set of steps that helps people move up or down."),
    ],
    "dear": [
        ("Why do people say dear?", "People sometimes say dear to sound warm, kind, or affectionate when they speak to someone."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"myth", "surprise", "dear"}
    myth = world.facts["myth"].id
    if myth == "hidden_bridge":
        tags.add("bridge")
    elif myth == "sleeping_gate":
        tags.add("stair")
    else:
        tags.add("lantern")
    out: list[QAItem] = []
    for tag in ["myth", "surprise", "dear", "bridge", "stair", "lantern"]:
        if tag in tags:
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_kind(old_temple, ruins).
place_kind(moon_bridge, bridge).
place_kind(forest_shrine, grove).
place_kind(cave_gate, cave).

myth_place(hidden_bridge, bridge).
myth_place(hidden_bridge, grove).
myth_place(hidden_bridge, ruins).
myth_place(sleeping_gate, cave).
myth_place(sleeping_gate, ruins).
myth_place(dear_lantern, grove).
myth_place(dear_lantern, ruins).
myth_place(dear_lantern, cave).

trigger_of(hidden_bridge, tap).
trigger_of(hidden_bridge, star_stone).
trigger_of(sleeping_gate, call).
trigger_of(sleeping_gate, name).
trigger_of(dear_lantern, knock).
trigger_of(dear_lantern, lantern).

valid(Place, Myth, Trigger) :- place_kind(Place, K), myth_place(Myth, K), trigger_of(Myth, Trigger).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("kind", pid, s.kind))
    for mid, myth in MYTHS.items():
        lines.append(asp.fact("myth", mid))
        for t in sorted(myth.place_tags):
            lines.append(asp.fact("myth_place", mid, t))
        for t in sorted(myth.trigger_tags):
            lines.append(asp.fact("trigger_of", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="forest_shrine", myth="hidden_bridge", trigger="tap", name="Maya", gender="girl", guide="Aunt June", trait="curious"),
    StoryParams(place="cave_gate", myth="sleeping_gate", trigger="name", name="Theo", gender="boy", guide="the old guide", trait="brave"),
    StoryParams(place="moon_bridge", myth="dear_lantern", trigger="knock", name="Lina", gender="girl", guide="the ranger", trait="spirited"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: myth, provoke, dear, and a surprising reveal.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--myth", choices=MYTHS)
    ap.add_argument("--trigger")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=[g.id for g in GUIDES])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.myth and args.trigger:
        if not valid_combo(args.place, args.myth, args.trigger):
            raise StoryError(explain_rejection(args.place, args.myth, args.trigger))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.myth is None or c[1] == args.myth)
              and (args.trigger is None or c[2] == args.trigger)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, myth_id, trigger = rng.choice(sorted(combos))
    myth = MYTHS[myth_id]
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice([g.id for g in GUIDES])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, myth=myth_id, trigger=trigger, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYTHS[params.myth],
        params.trigger,
        params.name,
        params.gender,
        next(g.label for g in GUIDES if g.id == params.guide),
        params.trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.myth} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
