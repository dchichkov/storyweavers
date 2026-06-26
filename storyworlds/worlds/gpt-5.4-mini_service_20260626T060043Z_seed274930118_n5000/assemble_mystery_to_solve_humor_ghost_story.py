#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/assemble_mystery_to_solve_humor_ghost_story.py
==============================================================================================================

A small, self-contained story world for a Ghost Story style tale with
mystery-solving and gentle humor.

Premise:
- A child and a friendly ghost must assemble a simple device or object.
- The missing part or strange clue creates a mystery.
- The story resolves when they assemble the right pieces and discover the truth.

The world is built as a physical/emotional simulation:
- meters model tangible state like bits collected, assembled objects, noise, and light
- memes model feelings like worry, courage, surprise, and delight

The prose is intentionally child-facing, concrete, and state-driven.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    gloomy: bool
    supports: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    reveal: str
    noise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Build:
    id: str
    label: str
    phrase: str
    pieces: list[str]
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    build: str
    name: str
    ghost_name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "attic": Setting("the attic", gloomy=True, supports={"lantern", "mask", "mobile"}),
    "library": Setting("the old library", gloomy=True, supports={"lantern", "mobile"}),
    "garden": Setting("the moonlit garden", gloomy=True, supports={"kite", "lantern"}),
    "kitchen": Setting("the kitchen after dark", gloomy=True, supports={"lantern", "snack"}),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        clue="a tiny key-shaped shadow",
        culprit="a hook under the chair",
        reveal="the key had slipped onto a bent hook",
        noise="tick-tick",
        tags={"key", "metal"},
    ),
    "rattle_box": Mystery(
        id="rattle_box",
        clue="a rattling sound behind the curtains",
        culprit="marbles in a cookie tin",
        reveal="the noise came from marbles rolling in a cookie tin",
        noise="rattle-rattle",
        tags={"tin", "marble", "toy"},
    ),
    "lost_button": Mystery(
        id="lost_button",
        clue="a shiny button under a dusty book",
        culprit="a tiny costume sleeve",
        reveal="the button had bounced under a storybook",
        noise="plink",
        tags={"button", "cloth"},
    ),
    "cold_whisper": Mystery(
        id="cold_whisper",
        clue="a cold whisper by the window",
        culprit="a draft in a cracked frame",
        reveal="the whisper was only the wind sneaking through a crack",
        noise="whooo",
        tags={"wind", "window"},
    ),
}

BUILDS = {
    "lantern": Build(
        id="lantern",
        label="paper lantern",
        phrase="a little paper lantern with a smiling face",
        pieces=["paper", "string", "candlecup", "sticker"],
        finish="lit it with a soft glow",
        tags={"light", "paper"},
    ),
    "mobile": Build(
        id="mobile",
        label="hanging mobile",
        phrase="a tiny hanging mobile with stars and moons",
        pieces=["string", "stars", "moons", "hook"],
        finish="hung it where it could turn slowly",
        tags={"hanging", "star"},
    ),
    "mask": Build(
        id="mask",
        label="spooky mask",
        phrase="a funny spooky mask with a round nose",
        pieces=["cardboard", "rubberband", "paint", "nose"],
        finish="fit it over a grin",
        tags={"face", "cardboard"},
    ),
    "kite": Build(
        id="kite",
        label="paper kite",
        phrase="a bright paper kite with a long tail",
        pieces=["paper", "string", "tail", "frame"],
        finish="sent it floating up toward the moonlight",
        tags={"air", "paper"},
    ),
}

GENDERS = {"girl", "boy"}
TRAITS = ["curious", "brave", "gentle", "sly", "cheerful", "careful"]
GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Leo", "Theo", "Max", "Ben", "Noah", "Finn", "Eli", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            for bid, b in BUILDS.items():
                if m.tags & b.tags and b.id in setting.supports:
                    combos.append((place, mid, bid))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery, build: Build) -> str:
    return (
        f"(No story: {mystery.id} and {build.id} do not fit a believable ghost-story puzzle "
        f"in {setting.place}. The mystery clue and the assembled object need at least one shared "
        f"thread, and the setting has to support that kind of build.)"
    )


def explain_gender(build_id: str, gender: str) -> str:
    return f"(No story: this world can name either a girl or boy hero, but {build_id} needs a valid setup first.)"


def ghost_pronoun(name: str) -> str:
    return "it"


def setting_line(setting: Setting) -> str:
    if setting.place == "the attic":
        return "The attic was full of old trunks, soft dust, and moonlight slipping through a round window."
    if setting.place == "the old library":
        return "The old library was quiet except for the little creaks that old shelves like to make at night."
    if setting.place == "the moonlit garden":
        return "The moonlit garden shimmered with wet leaves, and every shadow looked like it might be listening."
    return "The kitchen after dark smelled like wood and warm bread, and the shadows under the table looked extra long."


def build_line(build: Build) -> str:
    return f"They wanted to assemble {build.phrase}."


def mystery_line(mystery: Mystery) -> str:
    return f"But something odd kept happening: {mystery.clue}."


def solve_line(mystery: Mystery) -> str:
    return mystery.reveal + "."


def kind_of_hero(hero: Entity) -> str:
    trait = next((t for t in hero.memes.get("traits", [])), "curious")
    return f"little {trait} {hero.type}"


def tell(setting: Setting, mystery: Mystery, build: Build, hero_name: str, ghost_name: str,
         hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        memories:=None if False else "",
    ))
    hero.memes["traits"] = [trait]
    hero.memes["wonder"] = 1
    ghost = world.add(Entity(
        id=ghost_name,
        kind="character",
        type="ghost",
        label=ghost_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
    ))
    hero.meters["tools"] = 0
    ghost.meters["courage"] = 0
    ghost.meters["assembly"] = 0

    world.say(f"{hero_name} was a little {trait} {hero_gender} who liked old places at night.")
    world.say(f"One evening, {hero_name} met a friendly ghost named {ghost_name}.")
    world.say(f"{ghost_name} was not a scary ghost at all; {ghost_name} was a helpful one with a squeaky laugh.")
    world.say(setting_line(setting))
    world.say(build_line(build))
    world.say(mystery_line(mystery))

    world.para()
    hero.memes["worry"] = 1
    ghost.memes["worry"] = 1
    world.say(f"{hero_name} and {ghost_name} listened carefully for the clue.")
    world.say(f"{ghost_name} pointed at the dark corner and said, \"I heard {mystery.noise}, and now I cannot find the thing that made it!\"")
    world.say(f"{hero_name} opened a small box and began to assemble the pieces one by one.")
    for piece in build.pieces:
        hero.meters["pieces_found"] = hero.meters.get("pieces_found", 0) + 1
        world.say(f"First came the {piece}.")
    hero.meters["assembled"] = 1
    ghost.meters["assembled"] = 1
    world.say(f"Together they assembled the {build.label}, and {ghost_name} gave a proud little nod.")

    world.para()
    hero.memes["hope"] = 1
    ghost.memes["hope"] = 1
    if mystery.id == "missing_key":
        world.say(f"They followed the little key-shaped shadow to a bent hook under a chair.")
    elif mystery.id == "rattle_box":
        world.say(f"They heard the rattle-rattle again and found marbles rolling in a cookie tin.")
    elif mystery.id == "lost_button":
        world.say(f"They peeked under a dusty book and found the shiny button waiting there.")
    else:
        world.say(f"They followed the cold whisper to the window and found a crack letting in the wind.")

    world.say(solve_line(mystery))
    world.say(f"{ghost_name} laughed. \"So that was the mystery!\" {ghost_name} said.")
    world.say(f"{hero_name} laughed too, because the ghost looked very serious while pointing at something so ordinary.")

    world.para()
    world.say(f"At the end, {build.finish}, and the spooky old room felt friendly instead of strange.")
    world.say(f"{ghost_name} drifted in a happy circle, and {hero_name} smiled at the solved mystery.")
    world.say(f"The night stayed quiet, but now it was the good kind of quiet.")

    world.facts.update(
        hero=hero,
        ghost=ghost,
        parent=parent,
        setting=setting,
        mystery=mystery,
        build=build,
        resolved=True,
        assembled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child where {f["hero"].id} and {f["ghost"].id} assemble {f["build"].phrase} to solve a mystery.',
        f"Tell a gentle spooky story set in {f['setting'].place} with a friendly ghost, a funny clue, and a happy reveal.",
        f'Write a story that includes the word "assemble" and ends with the mystery being solved in a silly, comforting way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    mystery: Mystery = f["mystery"]
    build: Build = f["build"]
    setting: Setting = f["setting"]
    trait = hero.memes["traits"][0]

    return [
        QAItem(
            question=f"Who did {hero.id} meet in {setting.place}?",
            answer=f"{hero.id} met a friendly ghost named {ghost.id} in {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {ghost.id} assemble?",
            answer=f"They assembled {build.phrase}.",
        ),
        QAItem(
            question=f"What mystery did they solve?",
            answer=f"They solved the mystery of {mystery.reveal}.",
        ),
        QAItem(
            question=f"Why was the story a little spooky but not too scary?",
            answer=(
                f"It was spooky because it took place in {setting.place} at night, but it was not too scary "
                f"because {ghost.id} was friendly, the clue was silly, and the mystery was solved safely."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} help?",
            answer=f"{hero.id} helped by staying brave, listening for clues, and helping assemble the pieces.",
        ),
        QAItem(
            question=f"What kind of child was {hero.id} in this story?",
            answer=f"{hero.id} was a little {trait} {hero.type} who liked old places at night.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to assemble something?",
            answer="To assemble something means to put its pieces together so it becomes one finished thing.",
        ),
        QAItem(
            question="What is a ghost?",
            answer="A ghost is a spooky figure in stories, and in this kind of tale it can be friendly or helpful.",
        ),
        QAItem(
            question="Why do people use clues in a mystery?",
            answer="People use clues to figure out what happened when something is hidden, lost, or strange.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", mystery="missing_key", build="mobile", name="Mia", ghost_name="Pip", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="library", mystery="rattle_box", build="lantern", name="Leo", ghost_name="Moth", gender="boy", parent="father", trait="brave"),
    StoryParams(place="garden", mystery="cold_whisper", build="kite", name="Nora", ghost_name="Glim", gender="girl", parent="mother", trait="careful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.gender not in GENDERS:
        raise StoryError("(No story: gender must be girl or boy.)")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.build is None or c[2] == args.build)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mid, bid = rng.choice(sorted(combos))
    setting = SETTINGS[place]
    mystery = MYSTERIES[mid]
    build = BUILDS[bid]
    if not (mystery.tags & build.tags and build.id in setting.supports):
        raise StoryError(explain_rejection(setting, mystery, build))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ghost_name = args.ghost_name or rng.choice(["Pip", "Moth", "Glim", "Wisp", "Boo", "Nim"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mid, build=bid, name=name, ghost_name=ghost_name,
                       gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        BUILDS[params.build],
        params.name,
        params.ghost_name,
        params.gender,
        params.parent,
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


ASP_RULES = r"""
place(attic). place(library). place(garden). place(kitchen).
setting_supports(attic,lantern). setting_supports(attic,mask). setting_supports(attic,mobile).
setting_supports(library,lantern). setting_supports(library,mobile).
setting_supports(garden,kite). setting_supports(garden,lantern).
setting_supports(kitchen,lantern). setting_supports(kitchen,snack).

mystery_tag(missing_key,key). mystery_tag(missing_key,metal).
mystery_tag(rattle_box,tin). mystery_tag(rattle_box,marble). mystery_tag(rattle_box,toy).
mystery_tag(lost_button,button). mystery_tag(lost_button,cloth).
mystery_tag(cold_whisper,wind). mystery_tag(cold_whisper,window).

build_tag(lantern,light). build_tag(lantern,paper).
build_tag(mobile,hanging). build_tag(mobile,star).
build_tag(mask,face). build_tag(mask,cardboard).
build_tag(kite,air). build_tag(kite,paper).

shared(A,B) :- mystery_tag(A,T), build_tag(B,T).
valid(P,A,B) :- setting_supports(P,B), shared(A,B).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for b in SETTINGS[p].supports:
            lines.append(asp.fact("setting_supports", p, b))
    for mid, m in MYSTERIES.items():
        for t in m.tags:
            lines.append(asp.fact("mystery_tag", mid, t))
    for bid, b in BUILDS.items():
        for t in b.tags:
            lines.append(asp.fact("build_tag", bid, t))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: assemble a mystery, solve it, and keep it gentle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--build", choices=BUILDS)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, a, b in combos:
            print(f"  {p:8} {a:14} {b}")
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
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
