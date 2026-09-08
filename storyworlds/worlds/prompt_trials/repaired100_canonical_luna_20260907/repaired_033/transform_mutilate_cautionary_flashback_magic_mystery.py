#!/usr/bin/env python3
"""
A standalone mystery storyworld about a cautious transformation and a magical
flashback.

The world models a child who discovers that a cracked magic mirror can transform
a careless act into a warning from the past. A mutilated map, a missing bell,
and a hidden lesson lead to a safe repair.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


ENTITY_HUMAN = "human"
ENTITY_OBJECT = "object"
ENTITY_PLACE = "place"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    keeper: str
    relic: str
    mystery: str = "bell"
    opening_style: int = 0
    flashback_style: int = 0
    caution_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    object_name: str
    premise: str
    mutilation: str
    clue: str
    danger: str
    flashback: str
    past_mistake: str
    repair: str
    transformation: str
    final_image: str
    lesson: str


SETTINGS = {
    "clocktower": "the old clocktower",
    "museum": "the moonlit museum",
    "library": "the locked library",
    "greenhouse": "the glass greenhouse",
}

HERO_NAMES = ["Luna", "Mira", "Nell", "Tessa", "Robin", "Iris"]
KEEPER_NAMES = ["Mr. Vale", "Aunt Sable", "Mara", "Old Fen", "Professor Reed"]
RELIC_NAMES = ["the silver mirror", "the moon mirror", "the pocket mirror"]

CASES = {
    "bell": MysteryCase(
        object_name="the brass bell map",
        premise="had been drawn to find a bell that rang only when someone told the truth",
        mutilation="someone had torn the map into crooked strips and scratched away its final mark",
        clue="a blue thread caught on the map's torn edge",
        danger="the missing mark pointed toward a weak stair above the bell chamber",
        flashback="showed a boy following the same mark and falling through a rotten step",
        past_mistake="had erased the warning because he wanted the bell's treasure for himself",
        repair="laid the strips beneath the mirror and joined them with fine silver light",
        transformation="the damaged map transformed into a clear warning, not a treasure chart",
        final_image="the brass bell glowing above a bright red line that said STOP",
        lesson="A mystery should be solved with care, especially when an old warning has been damaged.",
    ),
    "garden": MysteryCase(
        object_name="the thorn-garden plan",
        premise="had been drawn to reveal a flower that bloomed only under moonlight",
        mutilation="had been cut into pieces, and the safest path was missing",
        clue="a smear of green wax marked the corner beside a tiny thorn",
        danger="the missing path led through sleeping vines that closed around careless feet",
        flashback="showed a gardener racing into the vines and losing the key to the garden gate",
        past_mistake="had hidden the safe route to keep strangers from stealing the moonflower",
        repair="pressed the pieces together and traced a safe path with chalk",
        transformation="the mutilated plan transformed into a living map whose vines curled away from danger",
        final_image="one moonflower opening beside the chalk path while the gate stayed safely shut",
        lesson="Protecting a secret must not destroy the warning that keeps people safe.",
    ),
    "portrait": MysteryCase(
        object_name="the painted portrait",
        premise="had been rumored to show a person's true choice before that person made it",
        mutilation="had been scraped across the eyes and covered with a strip of black cloth",
        clue="a flake of blue paint appeared under the cloth whenever the mirror warmed",
        danger="the portrait's magic could copy a frightened thought and make it seem like a command",
        flashback="showed the painter refusing to look away while a frightened friend asked for help",
        past_mistake="had mutilated the eyes after using the portrait to frighten someone",
        repair="washed the paint gently and replaced the cloth with a clear glass cover",
        transformation="the portrait transformed from a frightening command into a question",
        final_image="the painted eyes looking kindly toward a small painted door left open",
        lesson="Magic becomes safer when it invites a choice instead of forcing one.",
    ),
    "key": MysteryCase(
        object_name="the star-key diagram",
        premise="had been hidden to explain which key could open the town's sealed observatory",
        mutilation="had been stabbed with a pin until the stars became a blur",
        clue="one untouched star reflected the shape of the silver mirror",
        danger="the wrong key would awaken the observatory's storm machine",
        flashback="showed a former keeper turning the wrong key and covering the hill in thunder",
        past_mistake="had destroyed the diagram to stop anyone from repeating the mistake",
        repair="copied the surviving stars onto fresh paper before moving the old page",
        transformation="the battered diagram transformed into a careful set of three questions",
        final_image="the observatory dome opening under calm stars while the storm machine slept",
        lesson="Caution can preserve knowledge better than destroying the evidence.",
    ),
}

OPENINGS = [
    "{hero} liked mysteries, but only the kind that left everyone safe at the end.",
    "At dusk, {hero} carried a notebook into {setting} and promised not to touch anything without asking.",
    "{hero} had learned that magical places were full of clues and even fuller of traps.",
    "The old building whispered in its pipes when {hero} arrived with a lamp and a careful plan.",
    "Whenever a mystery seemed exciting, {hero} first looked for the warning nobody else had read.",
]

FLASHBACK_INTROS = [
    "The mirror clouded, then opened a window into yesterday.",
    "A silver shimmer crossed the glass, and the past stepped quietly into view.",
    "The relic did not speak in words. It showed a flashback in moving light.",
    "Dust rose from the mirror, forming a scene that had happened long ago.",
    "For one breath, the room became a memory someone had tried to bury.",
]

CAUTION_LINES = [
    "Luna held the relic by its wooden edge and kept her fingers away from the shining crack.",
    "She marked the safe floor with three pebbles before taking another step.",
    "The keeper tied a red ribbon around the dangerous stair so nobody could mistake it for a path.",
    "They copied every clue before touching the damaged object again.",
    "Luna asked whether the magic was warning them or inviting them, because those were not the same thing.",
]

ASP_RULES = r"""
% A mutilated relic is dangerous until its warning is recovered.
dangerous(R) :- relic(R), mutilated(R), warning_missing(R).

% A flashback reveals the reason for caution.
warning_recovered(R) :- relic(R), flashback_seen(R), careful_repair(R).

% Transformation is safe only when the repaired relic preserves a warning.
safe_transform(R) :- relic(R), warning_recovered(R), transformed(R).

valid_story(S) :- setting(S), relic(R), safe_transform(R).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines.extend(
        [
            asp.fact("relic", "mystery_relic"),
            asp.fact("mutilated", "mystery_relic"),
            asp.fact("warning_missing", "mystery_relic"),
            asp.fact("flashback_seen", "mystery_relic"),
            asp.fact("careful_repair", "mystery_relic"),
            asp.fact("transformed", "mystery_relic"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(SETTINGS)
    actual = {setting for (setting,) in asp_valid()}
    if expected == actual:
        print(f"OK: ASP model covers {len(expected)} story settings.")
        return 0
    print("MISMATCH between Python and ASP setting coverage.")
    print("only python:", sorted(expected - actual))
    print("only asp:", sorted(actual - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cautionary magical mystery with a flashback and a safe transformation."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--keeper")
    parser.add_argument("--relic")
    parser.add_argument("--mystery", choices=CASES)
    parser.add_argument("--opening-style", type=int)
    parser.add_argument("--flashback-style", type=int)
    parser.add_argument("--caution-style", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        keeper=args.keeper or rng.choice(KEEPER_NAMES),
        relic=args.relic or rng.choice(RELIC_NAMES),
        mystery=args.mystery or rng.choice(list(CASES)),
        opening_style=(
            args.opening_style
            if args.opening_style is not None
            else rng.randrange(len(OPENINGS))
        ),
        flashback_style=(
            args.flashback_style
            if args.flashback_style is not None
            else rng.randrange(len(FLASHBACK_INTROS))
        ),
        caution_style=(
            args.caution_style
            if args.caution_style is not None
            else rng.randrange(len(CAUTION_LINES))
        ),
    )


def validate_params(params: StoryParams) -> None:
    if params.hero.strip().lower() == params.keeper.strip().lower():
        raise StoryError("The hero and keeper need different names.")
    if not params.hero.strip():
        raise StoryError("The hero needs a readable name.")
    if not params.keeper.strip():
        raise StoryError("The keeper needs a readable name.")
    if not 0 <= params.opening_style < len(OPENINGS):
        raise StoryError("The opening style is outside the available registry.")
    if not 0 <= params.flashback_style < len(FLASHBACK_INTROS):
        raise StoryError("The flashback style is outside the available registry.")
    if not 0 <= params.caution_style < len(CAUTION_LINES):
        raise StoryError("The caution style is outside the available registry.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    case = CASES[params.mystery]
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="hero",
            kind=ENTITY_HUMAN,
            type="child",
            label=params.hero,
            phrase=params.hero,
            memes={"curiosity": 1.0, "caution": 0.5, "worry": 0.0, "relief": 0.0},
        )
    )
    keeper = world.add(
        Entity(
            id="keeper",
            kind=ENTITY_HUMAN,
            type="keeper",
            label=params.keeper,
            phrase=params.keeper,
            memes={"trust": 0.5, "worry": 0.5},
        )
    )
    relic = world.add(
        Entity(
            id="relic",
            kind=ENTITY_OBJECT,
            type="magical_relic",
            label=params.relic,
            phrase=params.relic,
            meters={"intact": 0.0, "warning": 0.0, "safe": 0.0, "transformed": 0.0},
            memes={"mystery": 1.0, "danger": 1.0},
            location=world.setting,
        )
    )
    map_piece = world.add(
        Entity(
            id="map_piece",
            kind=ENTITY_OBJECT,
            type="mutilated_clue",
            label=case.object_name,
            phrase=case.object_name,
            meters={"pieces": 0.4, "warning": 0.0},
            location=world.setting,
        )
    )

    world.facts.update(
        params=params,
        case=case,
        hero=hero,
        keeper=keeper,
        relic=relic,
        map_piece=map_piece,
        clue_found=False,
        flashback_seen=False,
        danger_understood=False,
        repaired=False,
        transformed=False,
        resolved=False,
    )
    return world


def act_opening(world: World) -> None:
    params = world.facts["params"]
    hero = world.get("hero")
    keeper = world.get("keeper")
    case = world.facts["case"]
    world.say(OPENINGS[params.opening_style].format(hero=hero.label, setting=world.setting))
    world.say(
        f"{hero.label} had come to investigate {case.object_name}, which {case.premise}."
    )
    world.say(
        f'"Stay beside me," {keeper.label} said. "A magical clue can be useful and still be dangerous."'
    )
    world.say(
        f'"I will look before I touch," {hero.label} promised.'
    )


def act_mutilation(world: World) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    relic = world.get("relic")
    case = world.facts["case"]
    relic.meters["intact"] = 0.0
    relic.meters["warning"] = 0.0
    relic.memes["danger"] = 1.0
    world.say(f"Behind a loose stone, they found {case.object_name}.")
    world.say(f"{case.mutilation.capitalize()}.")
    world.say(
        f"{hero.label} reached toward the torn pieces, but {keeper.label} caught the lamp."
    )
    world.say(
        f'"Do not mutilate the clue further," {keeper.label} warned. "The missing part may be the part that protects us."'
    )
    world.say(
        f'"Then the first mystery is not what it opens," {hero.label} said. "It is what it warns us about."'
    )
    world.facts["clue_found"] = True


def act_clue(world: World) -> None:
    hero = world.get("hero")
    case = world.facts["case"]
    relic = world.get("relic")
    relic.meters["warning"] = 0.3
    world.say(
        f"{hero.label} noticed {case.clue}. It led from the mutilated edge to a narrow door."
    )
    world.say(
        f"The door's keyhole was shaped like {world.facts['params'].relic}, but the floor beneath it had a fresh crack."
    )
    world.say(
        f"{hero.label} followed the clue only as far as the red ribbon, then stopped."
    )
    world.say(CAUTION_LINES[world.facts["params"].caution_style])
    world.facts["danger_understood"] = True


def act_flashback(world: World) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    relic = world.get("relic")
    case = world.facts["case"]
    world.say(FLASHBACK_INTROS[world.facts["params"].flashback_style])
    world.say(f"{case.flashback.capitalize()}.")
    world.say(f"The flashback explained that the former keeper {case.past_mistake}.")
    world.say(
        f'"The relic remembers the harm," {hero.label} whispered.'
    )
    world.say(
        f'"And it remembers the lesson," {keeper.label} replied. "That is why we repair it instead of hiding it."'
    )
    relic.meters["warning"] = 1.0
    relic.memes["danger"] = 0.5
    world.facts["flashback_seen"] = True


def act_repair(world: World) -> None:
    hero = world.get("hero")
    relic = world.get("relic")
    map_piece = world.get("map_piece")
    case = world.facts["case"]
    world.say(f"{hero.label} {case.repair}.")
    map_piece.meters["pieces"] = 1.0
    map_piece.meters["warning"] = 1.0
    relic.meters["intact"] = 1.0
    relic.meters["safe"] = 1.0
    relic.memes["danger"] = 0.0
    world.facts["repaired"] = True
    world.say(
        f"The pieces did not become new. They became honest about what had happened."
    )


def act_transform(world: World) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    relic = world.get("relic")
    case = world.facts["case"]
    relic.meters["transformed"] = 1.0
    relic.meters["safe"] = 1.0
    relic.memes["mystery"] = 0.4
    world.facts["transformed"] = True
    world.say(f"{case.transformation.capitalize()}.")
    world.say(
        f"The new magic did not pull {hero.label} toward the door. It showed {case.danger}."
    )
    world.say(
        f'"Now we know what not to do," {hero.label} said.'
    )
    world.say(
        f'"That is a powerful kind of answer," {keeper.label} said.'
    )
    world.say(f"Together they left the dangerous door closed.")


def act_resolution(world: World) -> None:
    hero = world.get("hero")
    case = world.facts["case"]
    world.say(
        f"At the end of the mystery, {hero.label} wrote the warning in the notebook before the magic faded."
    )
    world.say(f"{case.final_image.capitalize()}.")
    world.say(case.lesson)
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_mutilation(world)
    act_clue(world)
    act_flashback(world)
    world.para()
    act_repair(world)
    act_transform(world)
    act_resolution(world)
    return world


def reasonableness_gate(world: World) -> None:
    if not world.facts["clue_found"]:
        raise StoryError("The story needs a concrete clue.")
    if not world.facts["flashback_seen"]:
        raise StoryError("The mystery needs a flashback before its magical turn.")
    if not world.facts["repaired"]:
        raise StoryError("The mutilated object must be repaired.")
    if not world.facts["transformed"]:
        raise StoryError("The repaired relic must transform safely.")
    if not world.facts["resolved"]:
        raise StoryError("The mystery must end with a visible resolution.")


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a child-friendly mystery in {world.setting} about {params.hero}, {params.relic}, and a mutilated clue.",
        f"Include a cautionary flashback revealing why the magical object must be repaired rather than destroyed.",
        f"Show how the repaired relic can transform danger into a clear warning, ending with {case.final_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What mystery did {params.hero} investigate?",
            answer=f"{params.hero} investigated {case.object_name}, which was connected to {case.premise}.",
        ),
        QAItem(
            question=f"How had the clue been mutilated?",
            answer=f"{case.mutilation.capitalize()}.",
        ),
        QAItem(
            question="What clue did the hero discover?",
            answer=f"The hero discovered that {case.clue}.",
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"The flashback revealed that {case.past_mistake}.",
        ),
        QAItem(
            question="How did the magical object transform?",
            answer=f"After careful repair, {case.transformation}.",
        ),
        QAItem(
            question="Why did the characters leave the dangerous door closed?",
            answer=f"They left it closed because {case.danger}. The repaired magic made the warning clear.",
        ),
        QAItem(
            question="What image proved the mystery was resolved?",
            answer=f"The ending showed {case.final_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a scene that shows something that happened earlier, helping characters understand the present.",
        ),
        QAItem(
            question="What does it mean to mutilate an object?",
            answer="To mutilate an object means to damage it badly, often by cutting, tearing, or scraping it.",
        ),
        QAItem(
            question="What is a cautionary mystery?",
            answer="A cautionary mystery uses clues to reveal a danger and encourages careful choices instead of reckless ones.",
        ),
        QAItem(
            question="How does magic work in this storyworld?",
            answer="Magic reveals hidden connections and can transform a damaged clue into a useful warning, but it must be handled carefully.",
        ),
        QAItem(
            question="Why is repair better than destroying evidence?",
            answer="Repair can preserve both the truth about past harm and the warning that helps people avoid repeating it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.label} ({entity.type}); "
            f"meters={entity.meters}; memes={entity.memes}; location={entity.location}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    reasonableness_gate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        setting="clocktower",
        hero="Luna",
        keeper="Mr. Vale",
        relic="the silver mirror",
        mystery="bell",
        opening_style=0,
        flashback_style=0,
        caution_style=0,
    ),
    StoryParams(
        setting="greenhouse",
        hero="Mira",
        keeper="Aunt Sable",
        relic="the moon mirror",
        mystery="garden",
        opening_style=1,
        flashback_style=1,
        caution_style=1,
    ),
    StoryParams(
        setting="museum",
        hero="Nell",
        keeper="Mara",
        relic="the pocket mirror",
        mystery="portrait",
        opening_style=2,
        flashback_style=2,
        caution_style=2,
    ),
    StoryParams(
        setting="library",
        hero="Iris",
        keeper="Professor Reed",
        relic="the silver mirror",
        mystery="key",
        opening_style=3,
        flashback_style=3,
        caution_style=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("Generated-story verification failed.")
                sys.exit(1)
        print("OK: generated stories pass the Python reasonableness gate.")
        return

    if args.asp:
        print("Compatible ASP story settings:")
        for (setting,) in asp_valid():
            print(f"  {setting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempts < limit:
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as exc:
                print(exc, file=sys.stderr)
                sys.exit(2)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not produce the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.hero} / {params.relic} in {params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
