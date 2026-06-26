#!/usr/bin/env python3
"""
A standalone storyworld for a small cautionary space-adventure mystery.

Premise:
A curious child astronaut notices a strange rude-looking mark aboard a tiny
research ship. The crew wants to solve the mystery, but they must do it safely:
no opening sealed doors without checks, no poking unknown slime, and no chasing
shadows alone.

The story model tracks a few physical meters:
- battery charge
- hull integrity
- suit cleanliness
- clue visibility

And a few emotional memes:
- curiosity
- worry
- courage
- relief

The "obscene" seed word is used as a story-safe tag for a blatantly rude
message or symbol that the crew finds. The tale stays child-facing and
cautionary: the rude mark is the mystery, not the point of the story.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ("battery", "hull", "cleanliness", "clue_visibility"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "courage", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "it" if self.kind != "character" else "they"

    def possessive(self) -> str:
        return "its" if self.kind != "character" else "their"


@dataclass
class Setting:
    place: str = "the tiny research ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    danger: str
    solution: str
    risky_action: str
    safe_action: str
    prompt_word: str = "obscene"


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    safe_use: str
    effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the tiny research ship", affords={"scan", "map", "repair"}),
    "airlock": Setting(place="the airlock corridor", affords={"scan", "map"}),
    "moonbase": Setting(place="the moonbase lab", affords={"scan", "repair"}),
}

MYSTERIES = {
    "rude_message": Mystery(
        id="rude_message",
        label="a rude message scratched on a control panel",
        clue="a dark scratch shaped like a crooked grin",
        danger="it might hide a real warning or trick the crew into panic",
        solution="the mark was paint that could be cleaned off after a careful scan",
        risky_action="wipe it with a bare hand",
        safe_action="scan it with a light first",
        prompt_word="obscene",
    ),
    "alien_giggle": Mystery(
        id="alien_giggle",
        label="a strange giggling sound from the vents",
        clue="tiny footsteps of dust around a vent grate",
        danger="the crew could break the vent if they opened it too fast",
        solution="a loose toy drone was rattling inside",
        risky_action="kick the vent",
        safe_action="listen, then open the vent slowly",
        prompt_word="obscene",
    ),
    "glowing_dot": Mystery(
        id="glowing_dot",
        label="a glowing dot moving through the hallway",
        clue="a blinking light that left a silver trail",
        danger="chasing it could lead the child astronaut away from the others",
        solution="it was a rescue beacon stuck to a rolling maintenance bot",
        risky_action="run after it alone",
        safe_action="follow the beacon with a grown-up",
        prompt_word="obscene",
    ),
}

TOOLS = {
    "scanner": Tool(
        id="scanner",
        label="a little scanner",
        helps={"scan"},
        safe_use="hold the scanner steady and read the clues",
        effect="clue_visibility",
    ),
    "patch_kit": Tool(
        id="patch_kit",
        label="a patch kit",
        helps={"repair"},
        safe_use="seal the crack carefully",
        effect="hull",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        helps={"map"},
        safe_use="shine the lamp across the floor",
        effect="clue_visibility",
    ),
}

NAMES = ["Mira", "Tess", "Rio", "Nia", "Pip", "Juno", "Kai", "Luna"]
GROWNUPS = ["Captain Sol", "Engineer Vale", "Pilot Bram", "Dr. Ora"]
TRAITS = ["curious", "brave", "careful", "earnest", "bouncy"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    adult: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting: Setting, mystery: Mystery) -> bool:
    if setting.place == "the airlock corridor" and mystery.id == "glowing_dot":
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if valid_combo(setting, mystery):
                combos.append((sid, mid))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.label} does not fit well in {setting.place}; "
        f"the cautionary turn would be too thin there.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child astronaut",
        label=params.name,
        traits=["little", params.trait],
    ))
    adult = world.add(Entity(
        id=params.adult.replace(" ", "_"),
        kind="character",
        type="adult crew member",
        label=params.adult,
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=mystery.label,
        phrase=mystery.clue,
        caretaker=adult.id,
        meters={"battery": 0.0, "hull": 0.0, "cleanliness": 0.0, "clue_visibility": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    scanner = world.add(Entity(id="scanner", type="tool", label=TOOLS["scanner"].label))
    lamp = world.add(Entity(id="lamp", type="tool", label=TOOLS["lamp"].label))
    patch_kit = world.add(Entity(id="patch_kit", type="tool", label=TOOLS["patch_kit"].label))

    # Act 1: setup.
    world.say(
        f"{hero.label} was a little {params.trait} child astronaut who loved exploring {setting.place}."
    )
    world.say(
        f"One day, {hero.label} noticed {mystery.label}, and the odd mark made {hero.label} feel curious."
    )
    world.say(
        f"{params.adult} said it was best to {mystery.safe_action} because {mystery.danger}."
    )

    # World state.
    hero.memes["curiosity"] += 1.0
    adult.memes["worry"] += 1.0
    clue.meters["clue_visibility"] += 0.5

    # Act 2: mystery and tension.
    world.para()
    world.say(
        f"{hero.label} wanted to {mystery.risky_action}, but {params.adult} held up a hand."
    )
    world.say(
        f'"Let us {mystery.safe_action} first," {params.adult} said. "Space is for slow, safe steps."'
    )
    hero.memes["worry"] += 0.25
    hero.memes["courage"] += 0.5

    if mystery.id == "rude_message":
        world.say(
            f"The scratch looked a little obscene, but the crew did not laugh; they looked closer and more carefully."
        )
    elif mystery.id == "alien_giggle":
        world.say(
            "The vent gave a tiny giggle sound, and the hallway felt quiet and strange."
        )
    else:
        world.say(
            "The glowing dot slipped ahead like a tiny star, and nobody wanted to lose it."
        )

    # Safe investigation.
    world.para()
    world.say(f"{params.adult} used {scanner.label} to {TOOLS['scanner'].safe_use}.")
    clue.meters["clue_visibility"] += 1.0
    hero.memes["curiosity"] += 0.5

    if mystery.id == "rude_message":
        world.say("The scanner showed the mark was only old paint and dust.")
        world.say("There was no danger hiding inside it.")
    elif mystery.id == "alien_giggle":
        world.say("The lamp lit the vent, and the crew found a small toy drone wobbling inside.")
    else:
        world.say("The lamp caught the dot, and the crew saw a rescue beacon stuck to a tiny maintenance bot.")

    # Resolution.
    world.para()
    world.say(f"{params.adult} smiled and helped {hero.label} finish the job the safe way.")
    world.say("That careful choice kept the ship calm, and the mystery made sense at last.")

    if mystery.id == "rude_message":
        world.say("They cleaned the control panel, and the rude mark disappeared from the metal.")
    elif mystery.id == "alien_giggle":
        world.say("They opened the vent slowly and lifted out the wobbling drone without breaking anything.")
    else:
        world.say("They walked back together and guided the bot home instead of chasing it alone.")

    hero.memes["courage"] += 0.5
    hero.memes["relief"] += 1.0
    adult.memes["relief"] += 1.0
    clue.meters["clue_visibility"] = 1.0

    world.facts.update(
        hero=hero,
        adult=adult,
        clue=clue,
        mystery=mystery,
        setting=setting,
        tool=scanner,
        tool2=lamp,
        tool3=patch_kit,
        safe_action=mystery.safe_action,
        risky_action=mystery.risky_action,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short cautionary space adventure for a child who finds "{mystery.prompt_word}" as a clue and learns to stay safe.',
        f"Tell a mystery story where {hero.label} and {f['adult'].label} solve {mystery.label} by using a scanner before touching anything.",
        f"Write a child-friendly spaceship story about a strange clue, a careful adult, and a brave child astronaut.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    mystery = f["mystery"]

    return [
        QAItem(
            question=f"What did {hero.label} notice on the ship?",
            answer=f"{hero.label} noticed {mystery.label}, and it made the child astronaut curious.",
        ),
        QAItem(
            question=f"Why did {adult.label} tell {hero.label} to be careful?",
            answer=f"{adult.label} wanted {hero.label} to {mystery.safe_action} because {mystery.danger}.",
        ),
        QAItem(
            question=f"How did the crew solve the mystery?",
            answer=(
                f"They used a scanner first, learned what the clue really was, and solved the mystery "
                f"without doing anything risky."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should you check a strange thing before touching it in space?",
            answer="Because space gear and ship parts can be delicate, and careful checking helps keep people and equipment safe.",
        ),
        QAItem(
            question="What does a scanner do?",
            answer="A scanner helps you look closely at something without touching it right away.",
        ),
        QAItem(
            question="Why is it better to ask a grown-up when something seems strange?",
            answer="A grown-up can help you choose a safe plan and avoid a mistake that could cause trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.

valid(S,M) :- setting(S), mystery(M), not blocked(S,M).
blocked(airlock, glowing_dot).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("blocked", "airlock", "glowing_dot"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_story_combo(setting: str, mystery: str) -> bool:
    return valid_combo(SETTINGS[setting], MYSTERIES[mystery])


def explain_bad_combo(setting: str, mystery: str) -> str:
    return explain_rejection(SETTINGS[setting], MYSTERIES[mystery])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary space-adventure mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--adult", choices=GROWNUPS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.setting and args.mystery and not valid_story_combo(args.setting, args.mystery):
        raise StoryError(explain_bad_combo(args.setting, args.mystery))

    combos = [
        (s, m) for s, m in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.mystery is None or m == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    adult = args.adult or rng.choice(GROWNUPS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="ship", mystery="rude_message", name="Mira", adult="Captain Sol", trait="careful"),
    StoryParams(setting="moonbase", mystery="alien_giggle", name="Kai", adult="Engineer Vale", trait="curious"),
    StoryParams(setting="ship", mystery="glowing_dot", name="Luna", adult="Pilot Bram", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for s, m in vals:
            print(s, m)
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
