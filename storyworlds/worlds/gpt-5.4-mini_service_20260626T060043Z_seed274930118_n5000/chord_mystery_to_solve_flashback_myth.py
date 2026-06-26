#!/usr/bin/env python3
"""
storyworlds/worlds/chord_mystery_to_solve_flashback_myth.py
============================================================

A myth-style storyworld about a child, a vanished chord, a mystery to solve,
and a flashback that reveals the answer.

The world is built from a small simulated domain:
- a legendary place
- a hidden chord mystery
- a clue trail
- a memory turn that causes the answer to surface

The prose is driven by state changes, not a frozen template.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    epithet: str
    clue_kind: str
    mystery_kind: str
    opening_image: str


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    missing: str
    solved_by: str
    memory_trigger: str
    answer_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    guide_name: str
    hero_type: str
    guide_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def myth_title(setting: Setting, mystery: Mystery) -> str:
    return f"The {mystery.label} of {setting.place}"


def introduce(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"In {world.setting.place}, where {world.setting.epithet}, "
        f"there lived a young {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} walked with {guide.id}, a wise {guide.type}, "
        f"who knew the old songs and the safe paths."
    )


def awaken_mystery(world: World, hero: Entity) -> None:
    mystery = world.mystery
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.meters["attention"] = hero.meters.get("attention", 0) + 1
    world.say(
        f"One dusk, {hero.id} heard a single chord rising from the stones, "
        f"soft as a breath and bright as moonlight."
    )
    world.say(
        f"That chord left behind a mystery: the {mystery.label} had vanished, "
        f"and the gate would not answer without it."
    )


def search(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.meters["searching"] = hero.meters.get("searching", 0) + 1
    world.say(
        f"{hero.id} searched beneath roots, beside jars, and along the old wall, "
        f"trying to learn where the missing sound had gone."
    )


def clue_found(world: World, hero: Entity) -> None:
    hero.meters["clue"] = hero.meters.get("clue", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"At last, {hero.id} found a small sign of the lost chord: "
        f"{world.mystery.phrase} hidden where the wind had settled."
    )


def flashback(world: World, hero: Entity, guide: Entity) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    guide.memes["memory"] = guide.memes.get("memory", 0) + 1
    world.say(
        f"Then a flashback came to {hero.id}, and the old day returned."
    )
    world.say(
        f"{guide.id} had once shown {hero.id} how the chord was not lost at all; "
        f"it had been tucked away as a promise, waiting for the right song."
    )


def solve(world: World, hero: Entity) -> None:
    hero.meters["solved"] = hero.meters.get("solved", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} listened again, matched the old memory to the clue, and solved the mystery."
    )
    world.say(
        f"The chord returned, the gate opened, and the air felt full of gold."
    )


def restore(world: World, hero: Entity) -> None:
    world.say(
        f"By the end, {hero.id} stood in the glow of the opening gate, "
        f"while the chord rang clean through {world.setting.place}."
    )
    world.say(world.mystery.answer_image)


def tell(setting: Setting, mystery: Mystery, hero_name: str, guide_name: str,
         hero_type: str, guide_type: str) -> World:
    world = World(setting, mystery)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type))
    world.facts.update(hero=hero, guide=guide, setting=setting, mystery=mystery)

    introduce(world, hero, guide)
    world.para()
    awaken_mystery(world, hero)
    search(world, hero)
    clue_found(world, hero)
    world.para()
    flashback(world, hero, guide)
    solve(world, hero)
    restore(world, hero)
    world.facts["solved"] = True
    return world


SETTINGS = {
    "stone_hall": Setting(
        place="the stone hall",
        epithet="echoes slept in the pillars",
        clue_kind="rune",
        mystery_kind="lost sound",
        opening_image="The hall held its breath under a roof of carved stone.",
    ),
    "moon_grove": Setting(
        place="the moon grove",
        epithet="silver leaves whispered at night",
        clue_kind="leaf",
        mystery_kind="hidden harmony",
        opening_image="The grove shimmered with pale leaves and quiet branches.",
    ),
    "river_shrine": Setting(
        place="the river shrine",
        epithet="water sang over smooth steps",
        clue_kind="shell",
        mystery_kind="river tune",
        opening_image="The shrine listened to the river as if it were a prayer.",
    ),
    "sun_tower": Setting(
        place="the sun tower",
        epithet="warm light climbed every wall",
        clue_kind="rope",
        mystery_kind="sealed echo",
        opening_image="The tower glowed like a bright pillar at the edge of dawn.",
    ),
}

MYSTERIES = {
    "rune": Mystery(
        id="rune",
        label="rune chord",
        phrase="a rune traced in old dust",
        missing="the rune chord",
        solved_by="a remembered song",
        memory_trigger="a lesson from long ago",
        answer_image="The dust-mark shone once the forgotten notes were spoken again.",
        tags={"rune", "stone"},
    ),
    "leaf": Mystery(
        id="leaf",
        label="leaf chord",
        phrase="a green leaf tied with thread",
        missing="the leaf chord",
        solved_by="the evening breeze",
        memory_trigger="a shared walk under the trees",
        answer_image="The leaves trembled, and the grove answered with a gentle hum.",
        tags={"leaf", "moon"},
    ),
    "shell": Mystery(
        id="shell",
        label="shell chord",
        phrase="a shell bright with river salt",
        missing="the shell chord",
        solved_by="the river's refrain",
        memory_trigger="a story told beside the water",
        answer_image="The water ran laughing, as if it had been waiting to join the song.",
        tags={"shell", "river"},
    ),
    "rope": Mystery(
        id="rope",
        label="rope chord",
        phrase="a rope knot on a sun-warmed beam",
        missing="the rope chord",
        solved_by="the climbing wind",
        memory_trigger="a lesson from the tower steps",
        answer_image="The knot loosened, and sunlight poured through the opening like honey.",
        tags={"rope", "sun"},
    ),
}

HERO_TYPES = ["girl", "boy"]
GUIDE_TYPES = ["woman", "man", "priestess", "priest"]
HERO_NAMES = ["Ari", "Mina", "Tala", "Niko", "Lea", "Soren", "Iris", "Bram"]
GUIDE_NAMES = ["Edda", "Orin", "Lyra", "Hale", "Mara", "Ivo", "Nera", "Timon"]


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, myst.id) for place in SETTINGS for myst in MYSTERIES)


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the place '{place}' or mystery '{mystery}' is not part of this mythic world.)"


def build_story_params(place: str, mystery: str, rng: random.Random) -> StoryParams:
    setting = SETTINGS[place]
    myst = MYSTERIES[mystery]
    hero_type = rng.choice(HERO_TYPES)
    guide_type = rng.choice(GUIDE_TYPES)
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=rng.choice(HERO_NAMES),
        guide_name=rng.choice(GUIDE_NAMES),
        hero_type=hero_type,
        guide_type=guide_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    mystery = f["mystery"]
    return [
        f"Write a short myth for children about a {hero.type} who hears a chord in {setting.place}.",
        f"Tell a story where a mystery to solve leads to a flashback and the lost {mystery.label} returns.",
        f"Make a gentle mythic tale set in {setting.place} with a chord, an old memory, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    guide: Entity = f["guide"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.id} hear the chord?",
            answer=f"{hero.id} heard the chord in {setting.place}, where the old place was waiting for a story to wake it up.",
        ),
        QAItem(
            question=f"What was the mystery to solve in the story?",
            answer=f"The mystery was finding the lost {mystery.label}, the missing sound that kept the gate from opening.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember {guide.id}'s old lesson, which showed that the chord had been kept safe as a promise.",
        ),
        QAItem(
            question=f"How was the mystery solved at the end?",
            answer=f"{hero.id} matched the clue to the memory, spoke the old song, and the chord returned so the gate could open.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chord in music?",
            answer="A chord is several notes sounded together so they make one rich musical sound.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened earlier.",
        ),
        QAItem(
            question="What does a mystery to solve mean?",
            answer="It means there is something unknown, and the characters need clues to figure it out.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id} ({e.type}): meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_kind(M).

compatible(P, M) :- place(P), mystery(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("clue_kind", pid, setting.clue_kind))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery_kind", mid))
        lines.append(asp.fact("solved_by", mid, mystery.solved_by))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic chord mystery storyworld.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--guide-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guide-type", choices=GUIDE_TYPES)
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
    if args.place and args.mystery and (args.place not in SETTINGS or args.mystery not in MYSTERIES):
        raise StoryError(explain_rejection(args.place, args.mystery))
    combos = valid_combos()
    filtered = [
        (p, m) for (p, m) in combos
        if (args.place is None or p == args.place)
        and (args.mystery is None or m == args.mystery)
    ]
    if not filtered:
        raise StoryError("(No valid mythic combination matches the given options.)")
    place, mystery = rng.choice(filtered)
    params = build_story_params(place, mystery, rng)
    if args.name:
        params.hero_name = args.name
    if args.guide_name:
        params.guide_name = args.guide_name
    if args.hero_type:
        params.hero_type = args.hero_type
    if args.guide_type:
        params.guide_type = args.guide_type
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        params.hero_name,
        params.guide_name,
        params.hero_type,
        params.guide_type,
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


CURATED = [
    StoryParams(place="stone_hall", mystery="rune", hero_name="Ari", guide_name="Edda", hero_type="girl", guide_type="woman"),
    StoryParams(place="moon_grove", mystery="leaf", hero_name="Tala", guide_name="Lyra", hero_type="boy", guide_type="priestess"),
    StoryParams(place="river_shrine", mystery="shell", hero_name="Mina", guide_name="Mara", hero_type="girl", guide_type="man"),
    StoryParams(place="sun_tower", mystery="rope", hero_name="Niko", guide_name="Orin", hero_type="boy", guide_type="priest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mythic combos:\n")
        for place, mystery in combos:
            print(f"  {place:12} {mystery}")
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
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
