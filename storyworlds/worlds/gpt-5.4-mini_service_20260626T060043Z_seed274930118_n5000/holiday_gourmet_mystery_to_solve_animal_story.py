#!/usr/bin/env python3
"""
A small Storyweavers world for a holiday gourmet mystery, in a gentle Animal
Story style.

Premise:
- A festive animal host prepares a gourmet holiday treat.
- Something goes missing or gets swapped, creating a mystery to solve.
- The animals use clues in the setting, kindness, and careful noticing to solve
  the problem and restore the holiday meal.

The world is intentionally compact and constraint-checked. It simulates typed
entities with physical meters and emotional memes, and it can render a complete
child-facing story with grounded Q&A.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    missing: str
    found_in: str
    fix: str
    reason: str


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    region: str
    gourmet: bool = True
    holiday: bool = True


@dataclass
class Tool:
    id: str
    label: str
    clue_kind: str
    use: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"bake", "search", "serve"}),
    "hall": Setting(place="the hall", indoor=True, affords={"search", "serve"}),
    "garden": Setting(place="the garden", indoor=False, affords={"search"}),
}

ANIMALS = {
    "bunny": {"type": "bunny", "label": "bunny", "traits": ["small", "bright-eyed"]},
    "fox": {"type": "fox", "label": "fox", "traits": ["quick", "curious"]},
    "bear": {"type": "bear", "label": "bear", "traits": ["warm", "careful"]},
    "cat": {"type": "cat", "label": "cat", "traits": ["neat", "gentle"]},
    "mouse": {"type": "mouse", "label": "mouse", "traits": ["tiny", "clever"]},
    "deer": {"type": "deer", "label": "deer", "traits": ["graceful", "soft-footed"]},
}

TREATS = {
    "pie": Treat(id="pie", label="holiday pie", phrase="a glossy holiday pie with spiced apples", region="table"),
    "cake": Treat(id="cake", label="gourmet cake", phrase="a gourmet cake with berry cream", region="table"),
    "tarts": Treat(id="tarts", label="berry tarts", phrase="a tray of berry tarts with sugar stars", region="table",),
    "soup": Treat(id="soup", label="golden soup", phrase="a bowl of golden soup with herb swirls", region="table",),
}

TOOLS = {
    "trail": Tool(id="trail", label="crumb trail", clue_kind="crumbs", use="follow"),
    "sparkle": Tool(id="sparkle", label="sparkly spoon", clue_kind="shine", use="notice"),
    "ribbon": Tool(id="ribbon", label="red ribbon", clue_kind="thread", use="trace"),
    "note": Tool(id="note", label="little note", clue_kind="writing", use="read"),
}

MYSTERIES = {
    "missing_slice": Mystery(
        id="missing_slice",
        clue="crumbs on the windowsill",
        culprit="the mouse",
        missing="one slice of gourmet cake",
        found_in="the pantry",
        fix="share a smaller slice with everyone",
        reason="the mouse was carrying it to a baby mouse who was too shy to come to the table",
    ),
    "swapped_tarts": Mystery(
        id="swapped_tarts",
        clue="a red ribbon tied around the tray",
        culprit="the fox",
        missing="the berry tarts",
        found_in="the garden bench",
        fix="bring the tarts back and set them in the center of the table",
        reason="the fox moved them to make room for a snowflake centerpiece",
    ),
    "hidden_spoon": Mystery(
        id="hidden_spoon",
        clue="a shiny spoon under a napkin",
        culprit="the bear",
        missing="the serving spoon",
        found_in="beside the soup pot",
        fix="put the spoon back and serve the soup",
        reason="the bear had hidden it so the tiny guests could play a guessing game",
    ),
}

HERO_NAMES = ["Pip", "Mina", "Toby", "Luna", "Hugo", "Nia", "Coco", "Bram"]
TRAITS = ["cheerful", "curious", "gentle", "brave", "spry", "friendly"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    animal: str
    host: str
    treat: str
    mystery: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, host: Entity, treat: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with {hero.traits[0]} eyes and a nose for good smells."
    )
    world.say(
        f"On a bright holiday morning, {hero.pronoun('possessive')} friend {host.id} had made "
        f"{treat.phrase} for the feast."
    )


def setup_mystery(world: World, hero: Entity, host: Entity, mystery: Mystery, treat: Entity) -> None:
    world.para()
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"But then {treat.label} was not where it should have been."
    )
    world.say(
        f"'{mystery.missing.capitalize()} is missing,' said {host.id}, looking worried."
    )
    world.say(
        f"{hero.id} sniffed the air and saw {mystery.clue}."
    )


def search_world(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} and {helper.id} went to {world.setting.place} to search carefully."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1


def solve_mystery(world: World, hero: Entity, host: Entity, mystery: Mystery, treat: Entity) -> None:
    world.para()
    world.say(
        f"At last, {hero.id} found {mystery.missing} in {mystery.found_in}."
    )
    world.say(
        f"The clue showed that {mystery.culprit} had taken it because {mystery.reason}."
    )
    world.say(
        f"So {hero.id} helped {mystery.culprit} bring it back and told everyone the kind truth."
    )
    world.say(
        f"Then {host.id} smiled and asked {mystery.culprit} to stay for the feast."
    )
    world.say(
        f"They {mystery.fix}, and the holiday table looked warm and complete again."
    )
    world.say(
        f"Before long, {treat.label} was served, and everyone ate with happy faces."
    )


def tell(world: World, hero: Entity, host: Entity, helper: Entity, treat: Entity, mystery: Mystery) -> None:
    intro(world, hero, host, treat)
    setup_mystery(world, hero, host, mystery, treat)
    search_world(world, hero, helper, mystery)
    solve_mystery(world, hero, host, mystery, treat)


# ---------------------------------------------------------------------------
# World QA and story QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story for children about a holiday gourmet mystery in {f["place"]}.',
        f"Tell a short story where {f['hero_name']} the {f['hero_type']} helps solve a missing {f['treat_label']} problem.",
        f"Write a cozy holiday tale in which animals search for a clue and bring the feast back together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer="It is a holiday animal mystery story about finding a missing gourmet treat and solving the problem kindly.",
        ),
        QAItem(
            question=f"Who solved the mystery?",
            answer=f"{f['hero_name']} the {f['hero_type']} helped solve it by following the clue and finding the missing treat.",
        ),
        QAItem(
            question=f"What was missing from the feast?",
            answer=f"{f['mystery'].missing.capitalize()} was missing.",
        ),
        QAItem(
            question=f"Where was the missing item found?",
            answer=f"It was found in {f['mystery'].found_in}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The missing item came back, the feast was served, and everyone shared the holiday meal happily.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "holiday": [
        QAItem(
            question="What is a holiday?",
            answer="A holiday is a special day that people and families often celebrate with food, decorations, and time together.",
        )
    ],
    "gourmet": [
        QAItem(
            question="What does gourmet mean?",
            answer="Gourmet means fancy or especially tasty, often made with extra care.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known at first, so people look for clues to figure it out.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small hint or sign that helps someone solve a mystery.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["holiday"])
    out.extend(WORLD_KNOWLEDGE["gourmet"])
    out.extend(WORLD_KNOWLEDGE["mystery"])
    out.extend(WORLD_KNOWLEDGE["clue"])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place can host the mystery, a treat is present,
% and there is at least one helper animal.
valid_story(Place, Treat, Mystery, Animal, Host, Helper) :-
    setting(Place), affords(Place, search), treat(Treat), mystery(Mystery),
    animal(Animal), animal(Host), animal(Helper), Animal != Host, Helper != Host.

% The mystery is solvable when the clue type matches the mystery and the
% solution returns the missing treat to the feast.
solvable(Mystery) :- mystery(Mystery), clue(Mystery, _), found_in(Mystery, _), fix(Mystery, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("found_in", mid, m.found_in))
        lines.append(asp.fact("fix", mid, m.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Minimal parity gate: ensure every mystery has a fix and can be read by ASP.
    model = asp.one_model(asp_program("#show solvable/1."))
    solvable = sorted(set(asp.atoms(model, "solvable")))
    python = [(mid,) for mid in sorted(MYSTERIES)]
    if solvable and len(solvable) == len(python):
        print(f"OK: ASP sees {len(solvable)} solvable mysteries.")
        return 0
    print("MISMATCH or empty ASP result.")
    print("ASP:", solvable)
    print("PY :", python)
    return 1


# ---------------------------------------------------------------------------
# Parser, resolve, generate, emit, main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Holiday gourmet animal mystery story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--host", choices=ANIMALS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=ANIMALS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    host = args.host or rng.choice([a for a in ANIMALS if a != animal])
    helper = args.helper or rng.choice([a for a in ANIMALS if a not in {animal, host}])
    treat = args.treat or rng.choice(list(TREATS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, animal=animal, host=host, treat=treat, mystery=mystery, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    hero_info = ANIMALS[params.animal]
    host_info = ANIMALS[params.host]
    helper_info = ANIMALS[params.helper]
    treat = TREATS[params.treat]
    mystery = MYSTERIES[params.mystery]

    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_info["type"], label=hero_info["label"],
        traits=hero_info["traits"],
        meters={"tired": 0.0},
        memes={"curiosity": 1.0, "hope": 0.0},
    ))
    host = world.add(Entity(
        id="host", kind="character", type=host_info["type"], label=host_info["label"],
        traits=host_info["traits"], memes={"worry": 1.0},
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=helper_info["type"], label=helper_info["label"],
        traits=helper_info["traits"], memes={"helpful": 1.0},
    ))
    treat_ent = world.add(Entity(
        id="treat", type="thing", label=treat.label, phrase=treat.phrase,
        owner=host.id, caretaker=host.id
    ))
    world.facts.update(
        place=setting.place,
        hero_name=params.animal.capitalize(),
        hero_type=hero.type,
        host_name=params.host.capitalize(),
        helper_name=params.helper.capitalize(),
        treat_label=treat.label,
        mystery=mystery,
    )
    tell(world, hero, host, helper, treat_ent, mystery)

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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print("== (1) Generation prompts -- asks that would produce this story ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions -- answerable from the story text ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions -- child level, no story needed ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="kitchen", animal="bunny", host="cat", treat="cake", mystery="missing_slice", helper="mouse"),
    StoryParams(place="hall", animal="fox", host="bear", treat="tarts", mystery="swapped_tarts", helper="deer"),
    StoryParams(place="kitchen", animal="mouse", host="deer", treat="soup", mystery="hidden_spoon", helper="bunny"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        print(sorted(set(asp.atoms(model, "solvable"))))
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = rng_base + i
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
            header = f"### {p.animal} / {p.treat} / {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
