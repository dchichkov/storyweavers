#!/usr/bin/env python3
"""
storyworlds/worlds/animator_blur_restrict_skate_park_humor_folk.py
==================================================================

A small folk-tale style story world set in a skate park, built from the seed
words animator, blur, and restrict.

Premise:
- A cheerful animator visits the skate park with a mischievous blur of chalk
  and motion lines.
- The blur makes skating look magical and funny, but the park has a gate and a
  rule that restricts where the big tricks can happen.
- A child wants to zoom through the blur right away.
- A grown-up worries about a rough ramp and redirects the play toward a safe,
  funny compromise.

The world is modeled with physical meters and emotional memes so the story can
change from setup to tension to resolution in a state-driven way.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the skate park"
    affords: set[str] = field(default_factory=set)


@dataclass
class Trick:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    trick: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.id in {"helmet", "pads", "jacket"} and region in GEAR_BY_ID[g.id].covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(place="the skate park", affords={"blur", "restrict"})

TRICKS = {
    "blur": Trick(
        id="blur",
        verb="skate through the blur",
        gerund="skating through the blur",
        rush="race into the blur",
        mess="scuffed",
        soil="scuffed and dusty",
        zone={"feet", "legs"},
        keyword="blur",
        tags={"blur", "humor"},
    ),
    "restrict": Trick(
        id="restrict",
        verb="practice a restricted trick",
        gerund="practicing the restricted trick",
        rush="dash past the gate",
        mess="scuffed",
        soil="bumped and dusty",
        zone={"feet", "legs", "hands"},
        keyword="restrict",
        tags={"restrict", "humor"},
    ),
}

PRIZES = {
    "shoes": Entity(id="prize", type="shoes", label="shoes", phrase="bright skating shoes", plural=True),
    "helmet": Entity(id="prize", type="helmet", label="helmet", phrase="a shiny helmet"),
    "jacket": Entity(id="prize", type="jacket", label="jacket", phrase="a clean jacket"),
}

GEARS = [
    Gear(
        id="pads",
        label="knee pads",
        covers={"feet", "legs"},
        guards={"scuffed"},
        prep="put on knee pads first",
        tail="put on the knee pads and tried again",
        plural=True,
    ),
    Gear(
        id="helmet",
        label="a helmet",
        covers={"head"},
        guards={"scuffed"},
        prep="put on a helmet first",
        tail="put on the helmet and rolled on",
    ),
    Gear(
        id="jacket",
        label="a loose jacket",
        covers={"torso"},
        guards={"scuffed"},
        prep="button up a loose jacket first",
        tail="buttoned the jacket and laughed",
    ),
]

GEAR_BY_ID = {g.id: g for g in GEARS}

GIRL_NAMES = ["Mira", "Tess", "Nina", "Luna", "June"]
BOY_NAMES = ["Pip", "Otis", "Finn", "Theo", "Bram"]
TRAITS = ["cheerful", "curious", "spry", "merry", "bold"]


def prize_at_risk(trick: Trick, prize: Entity) -> bool:
    return prize.type in {"shoes", "helmet", "jacket"} and ("feet" in trick.zone or "legs" in trick.zone or "head" in trick.zone or "torso" in trick.zone)


def select_gear(trick: Trick, prize: Entity) -> Optional[Gear]:
    for gear in GEARS:
        if trick.mess in gear.guards:
            if prize.type == "shoes" and gear.id == "pads":
                return gear
            if prize.type == "helmet" and gear.id == "helmet":
                return gear
            if prize.type == "jacket" and gear.id == "jacket":
                return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for tid, trick in TRICKS.items():
        for pid, prize in PRIZE_CONFIGS.items():
            if prize_at_risk(trick, prize) and select_gear(trick, prize):
                combos.append((tid, pid))
    return combos


def story_setup(world: World, hero: Entity, parent: Entity, prize: Entity, trick: Trick) -> None:
    world.say(f"Long ago, in {world.setting.place}, there lived a little {hero.type} named {hero.id}.")
    world.say(f"{hero.pronoun('subject').capitalize()} was a {hero.memes.get('trait_word', 'cheerful')} animator who loved drawing funny motion lines, and everyone called the fastest lines a blur.")
    world.say(f"{hero.id} had a soft spot for {trick.gerund}, and {hero.pronoun('subject')} wore {prize.phrase} as if they had been made for the day.")

def apply_trick(world: World, hero: Entity, trick: Trick, narrate: bool = True) -> None:
    world.zone = set(trick.zone)
    hero.meters[trick.mess] = hero.meters.get(trick.mess, 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    if narrate:
        world.say(f"The blur twinkled like a ribbon in the air, and {hero.id} wanted to {trick.verb} at once.")

def warn(world: World, parent: Entity, hero: Entity, prize: Entity, trick: Trick) -> bool:
    if prize.type == "shoes":
        world.say(f'"If you {trick.verb}, your {prize.label} will get {trick.soil}," {parent.pronoun("possessive")} {parent.type} said.')
    else:
        world.say(f'"If you go past the gate, your {prize.label} will get {trick.soil}," {parent.pronoun("possessive")} {parent.type} said.')
    return True

def tension(world: World, hero: Entity, trick: Trick) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(f"{hero.id} frowned, because the blur looked too funny to leave alone.")
    world.say(f"{hero.pronoun('subject').capitalize()} tried to {trick.rush},")

def resolve(world: World, parent: Entity, hero: Entity, prize: Entity, trick: Trick) -> None:
    gear = select_gear(trick, prize)
    if not gear:
        raise StoryError("No reasonable compromise exists for this story.")
    item = world.add(Entity(id=gear.id, type=gear.id, label=gear.label, owner=hero.id, caretaker=parent.id, plural=gear.plural))
    item.worn_by = hero.id
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"Then {parent.id} smiled and said, '{gear.prep}.'")
    world.say(f"{hero.id} put on {gear.label}, and soon {gear.tail}.")
    world.say(f"At last {hero.id} was {trick.gerund}, {prize.label} stayed clean, and the skate park rang with laughter.")

def tell(params: StoryParams) -> World:
    setting = SETTING
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    prize = world.add(Entity(id="Prize", type=params.prize, label=params.prize, phrase=PRIZE_CONFIGS[params.prize].phrase, owner=hero.id, caretaker=parent.id))
    hero.memes["trait_word"] = params.trait

    trick = TRICKS[params.trick]

    story_setup(world, hero, parent, prize, trick)
    world.para()
    apply_trick(world, hero, trick)
    warn(world, parent, hero, prize, trick)
    tension(world, hero, trick)
    world.para()
    resolve(world, parent, hero, prize, trick)

    world.facts.update(hero=hero, parent=parent, prize=prize, trick=trick, gear=select_gear(trick, prize))
    return world


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale for a child about an animator, a blur, and a rule that must be respected at a skate park.',
        f"Tell a humorous story where {f['hero'].id} wants to {f['trick'].verb} but a grown-up worries about {f['prize'].label}, and they find a safe compromise.",
        'Write a gentle tale that includes the words animator, blur, and restrict, and ends with laughter at the skate park.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, trick = f["hero"], f["parent"], f["prize"], f["trick"]
    return [
        QAItem(
            question=f"Who was the animator in the skate park story?",
            answer=f"It was {hero.id}, a {hero.memes.get('trait_word', 'cheerful')} little {hero.type} who loved drawing funny blur lines.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} about the blur?",
            answer=f"{parent.id} warned {hero.id} because {hero.pronoun('possessive')} {prize.label} could get {trick.soil} if {hero.id} went too fast.",
        ),
        QAItem(
            question=f"What changed after {hero.id} listened to the parent and used the gear?",
            answer=f"{hero.id} kept playing, the {prize.label} stayed clean, and the joke-like blur became safe and fun instead of risky.",
        ),
    ]


KNOWLEDGE = {
    "blur": [("What is a blur?", "A blur is something that looks fuzzy or smeared when it moves very fast.")],
    "restrict": [("What does it mean to restrict something?", "To restrict something means to limit it or keep it in a smaller, safer place.")],
    "humor": [("What is humor?", "Humor is what makes people laugh or smile.")],
    "skate park": [("What do people do at a skate park?", "People ride skateboards, scooters, and bikes at a skate park.")],
    "animator": [("What does an animator do?", "An animator makes drawings or pictures seem to move, often by making many pictures in a row.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"blur", "restrict", "humor", "skate park", "animator"}
    out: list[QAItem] = []
    for tag in tags:
        q, a = KNOWLEDGE[tag][0]
        out.append(QAItem(question=q, answer=a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  zone={sorted(world.zone)}")
    return "\n".join(lines)


def explain_rejection(trick: Trick, prize: Entity) -> str:
    return f"(No story: this tale needs a prize that can honestly be put at risk by {trick.gerund}.)"


CURATED = [
    StoryParams(place="skate park", trick="blur", prize="shoes", name="Mira", gender="girl", parent="mother", trait="merry"),
    StoryParams(place="skate park", trick="restrict", prize="helmet", name="Pip", gender="boy", parent="father", trait="curious"),
]

GENDER_NAMES = {"girl": GIRL_NAMES, "boy": BOY_NAMES}
PRIZE_CONFIGS = {
    "shoes": Entity(id="Prize", type="shoes", label="shoes", phrase="bright skating shoes", plural=True),
    "helmet": Entity(id="Prize", type="helmet", label="helmet", phrase="a shiny helmet"),
    "jacket": Entity(id="Prize", type="jacket", label="jacket", phrase="a clean jacket"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale story world: animator, blur, restrict, and a skate park compromise.")
    ap.add_argument("--place", choices=["skate park"])
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--prize", choices=PRIZE_CONFIGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    trick = args.trick or rng.choice(list(TRICKS))
    prize = args.prize or ("shoes" if trick == "blur" else "helmet")
    if args.prize and not prize_at_risk(TRICKS[trick], PRIZE_CONFIGS[prize]):
        raise StoryError(explain_rejection(TRICKS[trick], PRIZE_CONFIGS[prize]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="skate park", trick=trick, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
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


ASP_RULES = r"""
% A prize is at risk when the trick reaches the region it is associated with.
at_risk(T, P) :- trick(T), prize(P), splashes(T, R), worn_on(P, R).

% Gear is a reasonable fix when it guards the mess and corresponds to the prize.
can_fix(T, P) :- at_risk(T, P), mess_of(T, M), guards(G, M), fit(G, P).

valid(T, P) :- at_risk(T, P), can_fix(T, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for tid, trick in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("mess_of", tid, trick.mess))
        for r in sorted(trick.zone):
            lines.append(asp.fact("splashes", tid, r))
    for pid in PRIZE_CONFIGS:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("fit", "pads", "shoes"))
    lines.append(asp.fact("fit", "helmet", "helmet"))
    lines.append(asp.fact("fit", "jacket", "jacket"))
    lines.append(asp.fact("guards", "pads", "scuffed"))
    lines.append(asp.fact("guards", "helmet", "scuffed"))
    lines.append(asp.fact("guards", "jacket", "scuffed"))
    lines.append(asp.fact("worn_on", "shoes", "feet"))
    lines.append(asp.fact("worn_on", "helmet", "head"))
    lines.append(asp.fact("worn_on", "jacket", "torso"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.trick} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
