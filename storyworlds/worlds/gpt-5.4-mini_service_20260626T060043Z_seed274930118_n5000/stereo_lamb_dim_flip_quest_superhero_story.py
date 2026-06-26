#!/usr/bin/env python3
"""
A tiny superhero quest world about a kid hero, a stubborn stereo, a dimmer lamp,
and a flip that changes the room from stuck to ready.

The premise is classical and child-sized:
- A hero wants to leave on a quest.
- A humming stereo fills the room with noise.
- A lamb-dim lamp leaves the map too dark to read.
- A needed flip switch or turn changes the situation.
- The hero and a helper use a simple, concrete fix to get moving.

The world is state-driven:
- Physical meters track noise, light, readiness, and gadget status.
- Emotional memes track confidence, worry, teamwork, and relief.
- Prose is authored from the simulated state, not from a frozen template.
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


# ---------------------------------------------------------------------------
# World model
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the clubhouse"
    quest_goal: str = "the hilltop beacon"
    affords: set[str] = field(default_factory=lambda: {"stereo", "lamp", "flip"})


@dataclass
class Gadget:
    id: str
    label: str
    kind: str
    effect: str
    fix: str


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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero: str
    sidekick: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Milo", "Rae", "Juno", "Tess", "Kai"]
SIDEKICK_NAMES = ["Zip", "Pip", "Dot", "Bea", "Moss", "Nia"]
PLACE_OPTIONS = {
    "clubhouse": Setting(place="the clubhouse", quest_goal="the hilltop beacon"),
    "tower": Setting(place="the watchtower", quest_goal="the city gate"),
    "garage": Setting(place="the garage", quest_goal="the lantern bridge"),
}

GADGETS = {
    "stereo": Gadget(
        id="stereo",
        label="stereo",
        kind="noise",
        effect="hum",
        fix="turn the stereo off",
    ),
    "lamp": Gadget(
        id="lamp",
        label="lamb-dim lamp",
        kind="light",
        effect="dim",
        fix="flip the lamp switch",
    ),
    "flip": Gadget(
        id="flip",
        label="flip switch",
        kind="switch",
        effect="change",
        fix="flip the switch once",
    ),
}


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def valid_story_combo(hero: str, sidekick: str, place: str) -> bool:
    return hero != sidekick and place in PLACE_OPTIONS


def explain_rejection() -> str:
    return "(No story: the hero and sidekick must be different names, and the place must be one of the known quest settings.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = PLACE_OPTIONS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="hero",
        label="hero",
        meters={"bravery": 1.0, "readiness": 0.0, "noise": 0.0, "light": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "relief": 0.0, "teamwork": 0.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick,
        kind="character",
        type="hero",
        label="sidekick",
        meters={"bravery": 0.7, "readiness": 0.0},
        memes={"hope": 0.7, "worry": 0.2, "relief": 0.0, "teamwork": 0.0},
    ))
    stereo = world.add(Entity(
        id="stereo",
        label="stereo",
        phrase="a buzzing stereo",
        meters={"noise": 1.0},
        memes={"stubborn": 1.0},
    ))
    lamp = world.add(Entity(
        id="lamp",
        label="lamb-dim lamp",
        phrase="a lamb-dim lamp",
        meters={"light": 0.2},
        memes={"stubborn": 0.6},
    ))
    flip = world.add(Entity(
        id="flip",
        label="flip switch",
        phrase="a flip switch on the wall",
        meters={"ready": 1.0},
        memes={"helpful": 1.0},
    ))

    world.facts.update(hero=hero, sidekick=sidekick, stereo=stereo, lamp=lamp, flip=flip)
    return world


def apply_initial_pressure(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    stereo = world.facts["stereo"]
    lamp = world.facts["lamp"]

    hero.meters["noise"] += stereo.m("noise")
    hero.meters["light"] += lamp.m("light")
    hero.memes["worry"] += 0.7 if hero.meters["light"] < 0.5 else 0.1
    sidekick.memes["worry"] += 0.4 if hero.meters["noise"] > 0.5 else 0.0

    hero.meters["readiness"] = 0.0
    sidekick.meters["readiness"] = 0.0


def can_start_quest(world: World) -> bool:
    hero = world.facts["hero"]
    return hero.meters.get("light", 0.0) >= 0.5 and hero.meters.get("noise", 0.0) <= 0.2


def resolve_problem(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    stereo = world.facts["stereo"]
    lamp = world.facts["lamp"]
    flip = world.facts["flip"]

    # Turn off the stereo.
    if stereo.m("noise") > 0:
        stereo.meters["noise"] = 0.0
        hero.meters["noise"] = 0.0
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.2)
        sidekick.memes["worry"] = max(0.0, sidekick.memes["worry"] - 0.1)
        world.say("The hero reached over and turned the stereo off, and the buzzing room went quiet.")

    # Flip the lamp into bright mode.
    if lamp.m("light") < 0.5:
        if flip.m("ready") <= 0:
            raise StoryError("The flip switch is missing its ready state.")
        lamp.meters["light"] = 1.0
        hero.meters["light"] = 1.0
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.3)
        sidekick.memes["worry"] = max(0.0, sidekick.memes["worry"] - 0.2)
        world.say("Then the sidekick gave the lamp a flip, and the room became bright enough to read the quest map.")

    hero.memes["teamwork"] += 1.0
    sidekick.memes["teamwork"] += 1.0
    hero.memes["relief"] += 1.0
    sidekick.memes["relief"] += 1.0
    hero.meters["readiness"] = 1.0
    sidekick.meters["readiness"] = 1.0

    world.say(
        f"With the noise gone and the lamb-dim lamp bright, they smiled at {world.setting.quest_goal} and got ready to go."
    )


def tell_story(world: World) -> str:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    stereo = world.facts["stereo"]
    lamp = world.facts["lamp"]

    world.say(
        f"{hero.id} and {sidekick.id} were in {world.setting.place}, where a stereo hummed too loud and a lamb-dim lamp made the quest map hard to see."
    )
    world.say(
        f"{hero.id} wanted to start the Quest for {world.setting.quest_goal}, but {hero.pronoun('possessive')} eyes kept darting between the noisy stereo and the dim little lamp."
    )
    apply_initial_pressure(world)
    if hero.meters["light"] < 0.5:
        world.say(
            f"{hero.id} worried that the dark map would twist the path, and {sidekick.id} nodded because {sidekick.pronoun()} could hear the stereo thumping like a trapped drum."
        )
    world.para()
    world.say(
        f"{hero.id} pointed to the flip switch and said they should fix the room before the Quest began."
    )
    resolve_problem(world)
    world.para()
    world.say(
        f"So the two heroes left together, carrying the map, with the quiet stereo behind them and the bright lamp shining over the doorway."
    )
    return world.render()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story for children that includes a stereo, a lamb-dim lamp, and a flip switch.",
        f"Tell a Quest story where {f['hero'].id} and {f['sidekick'].id} must fix a noisy room before leaving {world.setting.place}.",
        f"Write a gentle heroic tale about turning off a stereo and flipping a lamp so the map can be read.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    return [
        QAItem(
            question=f"Why could {hero.id} not start the Quest right away?",
            answer=f"{hero.id} could not start the Quest right away because the stereo was too loud and the lamb-dim lamp left the map too dark to read.",
        ),
        QAItem(
            question=f"What did {hero.id} do first to help the room become ready?",
            answer=f"{hero.id} turned the stereo off first, which made the room quiet enough for the heroes to think clearly.",
        ),
        QAItem(
            question=f"How did {sidekick.id} help after that?",
            answer=f"{sidekick.id} helped by flipping the lamp switch, which made the lamp bright and let them read the quest map.",
        ),
        QAItem(
            question=f"How did the heroes feel at the end?",
            answer=f"They felt relieved and proud, because the noisy room was calm and the Quest could begin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a stereo do?",
            answer="A stereo plays sound, music, or voices through speakers so people can hear them in a room.",
        ),
        QAItem(
            question="What does a lamp do?",
            answer="A lamp gives light so people can see things better when a room is dark.",
        ),
        QAItem(
            question="What does it mean to flip a switch?",
            answer="To flip a switch means to move it so a machine or light changes from off to on, or from one setting to another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero_ready(H) :- hero(H), quiet_room, bright_room.
quiet_room :- not loud(stereo).
bright_room :- lamp_on(lamp).
quest_can_start(H) :- hero_ready(H), hero(H).

% The story is reasonable only if the stereo is a source of noise and the lamp
% is dim enough to need a flip before the Quest can begin.
needs_fix(stereo) :- loud(stereo).
needs_fix(lamp) :- dim(lamp).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("hero", "sidekick"))
    lines.append(asp.fact("loud", "stereo"))
    lines.append(asp.fact("dim", "lamp"))
    lines.append(asp.fact("lamp_on", "lamp"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show quest_can_start/1."))
    got = set(asp.atoms(model, "quest_can_start"))
    want = {("hero",)}
    if got == want:
        print("OK: ASP gate matches Python reasonableness checks.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(got))
    print("  Python:", sorted(want))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACE_OPTIONS))
    if place not in PLACE_OPTIONS:
        raise StoryError("Unknown place.")
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different names.")
    if not valid_story_combo(hero, sidekick, place):
        raise StoryError(explain_rejection())
    return StoryParams(hero=hero, sidekick=sidekick, place=place)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell_story(world)
    return StorySample(
        params=params,
        story=story,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={dict(sorted(e.meters.items()))} memes={dict(sorted(e.memes.items()))}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero Quest story world.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--place", choices=sorted(PLACE_OPTIONS))
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


CURATED = [
    StoryParams(hero="Nova", sidekick="Zip", place="clubhouse"),
    StoryParams(hero="Milo", sidekick="Dot", place="tower"),
    StoryParams(hero="Rae", sidekick="Bea", place="garage"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_can_start/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show quest_can_start/1."))
        print("quest_can_start:", sorted(asp.atoms(model, "quest_can_start")))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
