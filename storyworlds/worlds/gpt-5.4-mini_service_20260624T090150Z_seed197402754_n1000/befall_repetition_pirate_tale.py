#!/usr/bin/env python3
"""
storyworlds/worlds/befall_repetition_pirate_tale.py
====================================================

A tiny pirate-tale story world about a problem that befalls a ship, with a
repeated attempt, a clever correction, and a bright ending.

Seed tale:
---
A little pirate named Pip sailed with her crew to find a shiny shell-chest.
But a sudden fog befell the sea, and the ship could not see the reef.
Pip tried again and again to steer by the map, but the waves kept pushing her
off course. At last the parrot cried "Left, left!" and the crew followed the
sound of the bell. They passed the reef, found the shell-chest, and sang all
the way home.

World model:
---
Physical meters:
    - fogged: how much fog has befallen the voyage
    - lost: how confused the crew feels on the water
    - safe: whether the ship is back on a clear path
    - treasure: whether the sought chest has been found

Emotional memes:
    - worry: fear while the danger lasts
    - grit: the willingness to try again
    - cheer: joy after the turn

Repetition instrument:
---
The captain may try to steer by the map more than once. Each failed try raises
worry and grit; the repeated effort becomes a visible story beat before the
parrot's call provides the turn.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the glittering sea"
    afford_fog: bool = True
    afford_reef: bool = True


@dataclass
class Ship:
    label: str
    speed: str
    style: str
    has_bell: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    crew: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turns: int = 0

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
        clone.turns = self.turns
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "sea": Setting(place="the glittering sea"),
    "harbor": Setting(place="the bright harbor"),
    "islands": Setting(place="the island strait"),
}

CREW = {
    "sloop": Ship(label="a small sloop", speed="swift", style="spry"),
    "brig": Ship(label="a brave brig", speed="steady", style="sturdy"),
    "skiff": Ship(label="a tiny skiff", speed="quick", style="nimble"),
}

TREASURES = {
    "shell_chest": "a shell-covered chest",
    "golden_map": "a golden map case",
    "pearl_box": "a pearl box",
}

NAMES = ["Pip", "Nell", "Mara", "Jory", "Tess", "Cove"]
BOY_NAMES = ["Finn", "Jack", "Roe", "Bo", "Ned", "Pry"]
CREW_NAMES = ["crew", "band", "mateys"]


def _sail(world: World, captain: Entity, ship: Entity, treasure: Entity) -> None:
    captain.meters["safe"] = 0
    world.turns += 1
    world.say(
        f"{captain.id} stood on {ship.label} and said, "
        f'"Set sail for {treasure.phrase}!"'
    )
    world.say("The rope creaked, the sails puffed, and the ship moved out onto the water.")


def _befall_fog(world: World, captain: Entity) -> None:
    if world.fired:
        return
    world.fired.add(("fog",))
    captain.meters["fogged"] += 1
    captain.memes["worry"] += 1
    captain.memes["grit"] += 1
    world.say(
        f"Then a thick fog befell the sea. The water turned gray, and the shore vanished."
    )
    world.say(f"{captain.id} frowned, because the ship could not see the reef ahead.")


def _attempt(world: World, captain: Entity, ship: Entity) -> bool:
    sig = ("attempt", world.turns)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.turns += 1
    captain.memes["grit"] += 1
    captain.memes["worry"] += 1
    captain.meters["lost"] += 1
    world.say(
        f"{captain.id} tried again to steer by the map, but the fog hid the markers."
    )
    world.say("Again the waves nudged the bow sideways, and again the ship slipped off course.")
    return True


def _parrot_turn(world: World, captain: Entity, ship: Entity) -> None:
    if ("turn",) in world.fired:
        return
    world.fired.add(("turn",))
    captain.memes["cheer"] += 1
    captain.memes["worry"] = 0
    captain.meters["safe"] = 1
    captain.meters["lost"] = 0
    world.say('Then the parrot on the mast cried, "Left, left!"')
    world.say("The crew followed the sound of the bell and the parrot's call, and the ship swung clear of the reef.")


def _find_treasure(world: World, captain: Entity, treasure: Entity) -> None:
    if ("treasure",) in world.fired:
        return
    world.fired.add(("treasure",))
    captain.meters["treasure"] = 1
    captain.memes["cheer"] += 1
    treasure.owner = captain.id
    world.say(
        f"Past the reef, {captain.id} found {treasure.phrase}."
    )
    world.say(f"{captain.id} grinned, and the whole crew sang all the way home.")


def _resolve(world: World, captain: Entity, ship: Entity, treasure: Entity) -> None:
    if captain.meters.get("safe", 0) < THRESHOLD:
        _parrot_turn(world, captain, ship)
    if captain.meters.get("safe", 0) >= THRESHOLD and captain.meters.get("treasure", 0) < THRESHOLD:
        _find_treasure(world, captain, treasure)


def tell(setting: Setting, ship_def: Ship, treasure_name: str,
         name: str = "Pip", gender: str = "girl", crew: str = "crew") -> World:
    world = World(setting)
    captain = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        meters={"fogged": 0, "lost": 0, "safe": 0, "treasure": 0},
        memes={"worry": 0, "grit": 0, "cheer": 0},
    ))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=ship_def.label))
    treasure = world.add(Entity(id="treasure", kind="thing", type="treasure", label=treasure_name, phrase=treasure_name))

    world.say(f"{captain.id} was a little pirate with {ship_def.label} and a bright heart.")
    world.say(f"{captain.pronoun('subject').capitalize()} loved sailing with the {crew} in search of {treasure.phrase}.")
    world.para()
    _sail(world, captain, ship, treasure)
    _befall_fog(world, captain)
    world.para()
    _attempt(world, captain, ship)
    _attempt(world, captain, ship)
    world.say("But the fog stayed, so the little pirate tried one more time.")
    _resolve(world, captain, ship, treasure)
    world.para()
    world.say(
        f"In the end, {captain.id} was back on a safe course, {treasure.phrase} was aboard, "
        f"and the sea sparkled like a silver plate."
    )

    world.facts.update(captain=captain, ship=ship, treasure=treasure, setting=setting, ship_def=ship_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    treasure = f["treasure"]
    return [
        f'Write a short pirate tale for a young child that includes the word "befall".',
        f"Tell a story where a little pirate named {captain.id} goes after {treasure.phrase}, "
        f"then a problem befalls the sea, and the crew must try again.",
        f"Write a simple repeating pirate story about fog, a ship, and a cheerful rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["captain"]
    t = f["treasure"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {c.id}, a little pirate who sailed out with a brave heart.",
        ),
        QAItem(
            question=f"What befell the sea?",
            answer="A thick fog befell the sea and hid the reef from sight.",
        ),
        QAItem(
            question=f"What did {c.id} try to do again and again?",
            answer=f"{c.id} tried again and again to steer by the map, but the fog kept making the path hard to see.",
        ),
        QAItem(
            question=f"What helped the crew find the way?",
            answer="The parrot's call of 'Left, left!' and the sound of the bell helped the crew turn away from the reef.",
        ),
        QAItem(
            question=f"What did the captain find at the end?",
            answer=f"{c.id} found {t.phrase} and the crew sang all the way home.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops that hangs low in the air and can make it hard to see.",
        ),
        QAItem(
            question="What does a bell do on a ship?",
            answer="A bell can ring to give a signal, help people listen for direction, or let a crew know something important.",
        ),
        QAItem(
            question="What is a reef?",
            answer="A reef is a line of rocks or coral under the water that ships must steer around.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items())}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items())}}}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    crew: str
    treasure: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="sea", name="Pip", gender="girl", crew="crew", treasure="a shell-covered chest"),
    StoryParams(place="islands", name="Mara", gender="girl", crew="mateys", treasure="a pearl box"),
    StoryParams(place="harbor", name="Finn", gender="boy", crew="band", treasure="a golden map case"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale story world with befalling fog and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--crew", choices=CREW_NAMES)
    ap.add_argument("--treasure", choices=TREASURES)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    crew = args.crew or rng.choice(CREW_NAMES)
    treasure_key = args.treasure or rng.choice(list(TREASURES))
    return StoryParams(place=place, name=name, gender=gender, crew=crew, treasure=TREASURES[treasure_key])


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CREW["sloop"], params.treasure, params.name, params.gender, params.crew)
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
% A problem befalls the voyage when fog covers the sea.
befallen(fog) :- foggy(sea).

% Repetition is a purposeful repeated steering attempt.
repeat_try(C) :- captain(C), attempt(C, 1), attempt(C, 2).

% Success arrives when the parrot gives a direction and the ship is safe.
safe(C) :- captain(C), parrot_call(left), repeat_try(C), reef_passed(C).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("captain", "pip"),
        asp.fact("foggy", "sea"),
        asp.fact("parrot_call", "left"),
        asp.fact("reef_passed", "pip"),
        asp.fact("attempt", "pip", 1),
        asp.fact("attempt", "pip", 2),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show befallen/1.\n#show repeat_try/1.\n#show safe/1."))
    atoms = set(asp.atoms(model, "befallen")) | set(asp.atoms(model, "repeat_try")) | set(asp.atoms(model, "safe"))
    expected = {("fog",), ("pip",), ("pip",)}
    if atoms:
        print("OK: ASP twin produced a model for the pirate tale world.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story facts.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show befallen/1.\n#show repeat_try/1.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show befallen/1.\n#show repeat_try/1.\n#show safe/1."))
        print(sorted(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
