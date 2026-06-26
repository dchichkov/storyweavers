#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/die_sound_effects_inner_monologue_space_adventure.py
================================================================================================

A standalone story world for a tiny space-adventure tale with sound effects
and inner monologue.

Premise:
- A young space explorer carries a lucky die on a small ship.
- The die helps decide what the ship should do next.
- A sudden problem makes the explorer hesitate.
- Inner monologue shows the explorer thinking through the choice.
- The ending proves the choice changed the ship's path and mood.

The world is small on purpose: one ship, one explorer, one helper robot,
one risky choice, and one resolution.

The script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of results.py containers
- lazy import of asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class ShipSetting:
    place: str = "the little starship"
    sky: str = "deep space"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    sound: str
    monologue: str
    risk: str
    turn: str
    tag: str


@dataclass
class Die:
    id: str
    label: str
    phrase: str
    faces: int
    lucky_face: int
    helps: dict[int, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class Assistant:
    id: str
    label: str
    phrase: str
    kind: str = "robot"


class World:
    def __init__(self, setting: ShipSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.last_roll: Optional[int] = None
        self.current_action: Optional[str] = None

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.last_roll = self.last_roll
        w.current_action = self.current_action
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_deck": ShipSetting(place="the orbital deck", sky="deep space", affords={"scan", "dock", "course"}),
    "moon_cabin": ShipSetting(place="the moon cabin", sky="the silver moon", affords={"scan", "course"}),
    "cargo_bay": ShipSetting(place="the cargo bay", sky="inside the ship", affords={"scan", "sort", "course"}),
}

ACTIONS = {
    "scan": Action(
        id="scan",
        verb="scan the stars",
        gerund="scanning the stars",
        sound="beep-beep",
        monologue="I hope the map is right.",
        risk="the ship might miss the safe route",
        turn="the scanner found a new path",
        tag="stars",
    ),
    "dock": Action(
        id="dock",
        verb="dock with the station",
        gerund="docking with the station",
        sound="clunk",
        monologue="Please line up neatly.",
        risk="the ship might bump the station",
        turn="the station lights blinked green",
        tag="station",
    ),
    "course": Action(
        id="course",
        verb="set a new course",
        gerund="setting a new course",
        sound="whirr",
        monologue="I can choose a better path.",
        risk="the ship could drift the wrong way",
        turn="the new course pointed toward home",
        tag="course",
    ),
    "sort": Action(
        id="sort",
        verb="sort the cargo",
        gerund="sorting the cargo",
        sound="clatter",
        monologue="If I tidy this now, the bay will feel calmer.",
        risk="the boxes might tumble and block the hatch",
        turn="the boxes stacked neatly again",
        tag="cargo",
    ),
}

DICE = {
    "silver_die": Die(
        id="silver_die",
        label="silver die",
        phrase="a silver die with bright edges",
        faces=6,
        lucky_face=4,
        helps={1: "scan", 2: "scan", 3: "course", 4: "course", 5: "dock", 6: "sort"},
        tags={"die", "space", "lucky"},
    ),
    "blue_die": Die(
        id="blue_die",
        label="blue die",
        phrase="a blue die with tiny comet marks",
        faces=6,
        lucky_face=6,
        helps={1: "scan", 2: "sort", 3: "scan", 4: "course", 5: "dock", 6: "course"},
        tags={"die", "space"},
    ),
    "gold_die": Die(
        id="gold_die",
        label="gold die",
        phrase="a gold die that gleamed like a tiny sun",
        faces=8,
        lucky_face=8,
        helps={1: "scan", 2: "scan", 3: "dock", 4: "course", 5: "course", 6: "sort", 7: "sort", 8: "dock"},
        tags={"die", "space", "sun"},
    ),
}

ASSISTANTS = {
    "helper_bot": Assistant(id="helper_bot", label="helper bot", phrase="a round helper robot with one blinking eye"),
    "map_drone": Assistant(id="map_drone", label="map drone", phrase="a tiny map drone that hummed above the console"),
}

HERO_NAMES = ["Mina", "Jori", "Tess", "Nova", "Pip", "Rin", "Lio", "Arin"]
ROLES = ["girl", "boy"]
TRAITS = ["brave", "curious", "careful", "bright", "nervous", "spirited"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
die_present(D) :- die(D).
action(A) :- action_kind(A).
available(A) :- action(A).

possible(A) :- die_face(D, F), die_helps(D, F, A), action(A).
valid_story(P, D, A) :- place(P), die(D), die_face(D, F), die_helps(D, F, A), affords(P, A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action_kind", aid))
    for did, d in DICE.items():
        lines.append(asp.fact("die", did))
        for face, act in sorted(d.helps.items()):
            lines.append(asp.fact("die_face", did, face))
            lines.append(asp.fact("die_helps", did, face, act))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    die: str
    name: str
    role: str
    trait: str
    assistant: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space-adventure story world with a lucky die.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--die", choices=DICE)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--assistant", choices=ASSISTANTS)
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

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, setting in SETTINGS.items():
        for action in setting.affords:
            for did, d in DICE.items():
                if action in d.helps.values():
                    combos.append((pid, action, did))
    return combos

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.die:
        combos = [c for c in combos if c[2] == args.die]
    if not combos:
        raise StoryError("(No valid space-adventure combination matches the given options.)")

    place, action, die = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    role = args.role or rng.choice(ROLES)
    trait = args.trait or rng.choice(TRAITS)
    assistant = args.assistant or rng.choice(list(ASSISTANTS))
    return StoryParams(place=place, action=action, die=die, name=name, role=role, trait=trait, assistant=assistant)

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _roll_die(world: World, hero: Entity, d: Die, rng: random.Random) -> int:
    roll = rng.randint(1, d.faces)
    world.last_roll = roll
    return roll

def _choose_action(d: Die, roll: int) -> str:
    return d.helps[roll]

def simulate(params: StoryParams) -> World:
    rng = random.Random(params.seed or 0)
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.role, label=params.name))
    assistant = world.add(Entity(id="assistant", kind="character", type="robot", label=ASSISTANTS[params.assistant].label))
    die = world.add(Entity(id="die", type="die", label=DICE[params.die].label, phrase=DICE[params.die].phrase))
    action = ACTIONS[params.action]

    world.facts.update(hero=hero, assistant=assistant, die=die, action=action, params=params)
    world.current_action = params.action

    # Setup
    world.say(f"{hero.label} floated through {world.setting.place} with {die.label} in {hero.pronoun('possessive')} pocket.")
    world.say(f"{assistant.label.capitalize()} hummed nearby, and the console lights glowed in {world.setting.sky}.")
    world.say(f"{hero.label} loved {action.gerund}, and the die felt lucky in {hero.pronoun('possessive')} hand.")

    # Problem
    world.para()
    world.say(f"Then the ship gave a soft {action.sound} and a warning blinked on the screen.")
    world.say(f"It meant {action.risk}.")
    world.say(f"{hero.label} looked at the die and thought, \"{action.monologue}\"")
    world.say(f"Inside {hero.pronoun('possessive')} head, another thought flickered: \"Should I trust the die or the warning?\"")

    # Turn
    roll = _roll_die(world, hero, DICE[params.die], rng)
    chosen = _choose_action(DICE[params.die], roll)
    world.facts["roll"] = roll
    world.facts["chosen"] = chosen

    world.para()
    world.say(f"{hero.label} rolled the die: {roll}.")
    world.say(f"{action.sound}! The die spun under the cabin light.")
    if chosen == params.action:
        world.say(f"{hero.label} smiled, because the lucky face pointed to {action.verb}.")
    else:
        world.say(f"The die pointed to {ACTIONS[chosen].verb} instead, and {hero.label} paused to listen.")
    world.say(f"{assistant.label.capitalize()} blinked and said, \"That choice could help.\"")

    # Resolution
    if chosen == params.action:
        world.say(f"{action.turn}.")
        world.say(f"{hero.label} followed the plan and {action.verb}.")
        world.say(f"At once the ship felt steady again, and {hero.label}'s chest warmed with relief.")
        world.say(f"\"We did it,\" {hero.label} whispered, and the stars looked less scary.")
        world.facts["resolved"] = True
    else:
        world.say(f"{ACTIONS[chosen].turn}.")
        world.say(f"{hero.label} trusted the new path instead and kept the ship safe.")
        world.say(f"The old worry drifted away, and the small ship slid on toward a calmer route.")
        world.say(f"\"Good call,\" {hero.label} thought, as the cabin lights settled into a soft blue.")
        world.facts["resolved"] = True

    return world


# ---------------------------------------------------------------------------
# Narration + QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child that includes the word "die" and a sound effect like "{f["action"].sound}".',
        f"Tell a gentle story about {f['hero'].label} using a lucky die to choose what to do on a tiny ship.",
        f"Write a child-friendly space story with inner monologue where a hero wonders whether to trust a die or a warning light.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    action: Action = f["action"]
    d: Entity = f["die"]
    roll = f["roll"]
    chosen = f["chosen"]
    return [
        QAItem(
            question=f"What did {hero.label} use to make a choice on the ship?",
            answer=f"{hero.label} used a {d.label} to make a choice.",
        ),
        QAItem(
            question=f"What sound did the ship make when the problem started?",
            answer=f"The ship made a {action.sound} sound when the warning started.",
        ),
        QAItem(
            question=f"What did {hero.label} think about inside {hero.pronoun('possessive')} head?",
            answer=f"{hero.label} wondered whether to trust the die or the warning light.",
        ),
        QAItem(
            question=f"What number did the die land on?",
            answer=f"The die landed on {roll}.",
        ),
        QAItem(
            question=f"What did the die point toward?",
            answer=f"It pointed toward {ACTIONS[chosen].verb}.",
        ),
        QAItem(
            question=f"How did the story end for the ship?",
            answer=f"The ship ended up safe and steady after {hero.label} made a careful choice.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a die?",
            answer="A die is a small object with numbers on its faces. People roll it to make a random choice.",
        ),
        QAItem(
            question="What is a robot helper?",
            answer="A robot helper is a machine that can blink, buzz, and assist with tasks.",
        ),
        QAItem(
            question="What is a starship?",
            answer="A starship is a ship made for traveling through space.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"last_roll={world.last_roll}")
    lines.append(f"chosen={world.facts.get('chosen')}")
    return "\n".join(lines)

def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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

# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="orbital_deck", action="scan", die="silver_die", name="Nova", role="girl", trait="curious", assistant="helper_bot"),
    StoryParams(place="moon_cabin", action="course", die="gold_die", name="Rin", role="boy", trait="careful", assistant="map_drone"),
    StoryParams(place="cargo_bay", action="sort", die="blue_die", name="Mina", role="girl", trait="brave", assistant="helper_bot"),
]

def valid_combo_set() -> set[tuple[str, str, str]]:
    return set(valid_combos())

def resolve_explicit(args: argparse.Namespace) -> None:
    if args.action and args.die:
        d = DICE[args.die]
        if args.action not in d.helps.values():
            raise StoryError("The chosen die does not reasonably point to that action.")

def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    resolve_explicit(args)
    return resolve_params(args, rng)

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = build_story_params_from_args(args, random.Random(seed))
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
            header = f"### {p.name}: {p.action} with {p.die} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
