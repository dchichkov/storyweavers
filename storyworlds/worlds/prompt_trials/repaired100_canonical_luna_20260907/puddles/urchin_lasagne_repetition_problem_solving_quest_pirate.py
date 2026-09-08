#!/usr/bin/env python3
"""A tiny pirate quest about an urchin, lasagne, and solving the same problem again.

Captain Luna wants to carry a warm lasagne across a wobbly pirate ship. Each
attempt teaches her something: the dish slides, the crew notices, and a better
plan is tried. Repetition turns into problem solving, and the quest ends with
food shared under a bright moon.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def change(self, key: str, amount: float) -> None:
        self.meters[key] = self.meter(key) + amount


@dataclass(frozen=True)
class Setting:
    id: str
    name: str
    surface: str
    landmarks: tuple[str, ...]


@dataclass(frozen=True)
class Crew:
    id: str
    name: str
    role: str


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    attempt: int = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str,
        result: str,
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    filling: str
    hero: str
    companion: str
    seed: Optional[int] = None
    attempts: int = 3


SETTINGS = {
    "deck": Setting(
        "deck",
        "the moonlit deck",
        "the rolling deck",
        ("the brass bell", "the blue sail", "the captain's table"),
    ),
    "galley": Setting(
        "galley",
        "the little galley",
        "the warm galley floor",
        ("the copper pot", "the spice shelf", "the round porthole"),
    ),
    "cove": Setting(
        "cove",
        "the quiet cove",
        "the sandy shore",
        ("a leaning palm", "a tide pool", "a flat picnic rock"),
    ),
}

FILLINGS = {
    "lasagne": {
        "dish": "lasagne",
        "smell": "cheesy and warm",
        "meal": "the lasagne",
        "tag": "lasagne",
    }
}

HEROES = ["Luna", "Mara", "Pip", "Nico"]
COMPANIONS = ["Otto", "Tess", "Rafi", "Mina"]

CREW = {
    "navigator": Crew("navigator", "Navigator Nia", "navigator"),
    "cook": Crew("cook", "Cook Cori", "cook"),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, filling) for setting in SETTINGS for filling in FILLINGS]


def solve_step(world: World, method: str) -> None:
    hero = world.entities["hero"]
    dish = world.entities["dish"]
    helper = world.entities["helper"]
    world.attempt += 1
    dish.change("attempts", 1)

    if method == "hands":
        dish.change("slips", 1)
        hero.change("curiosity", 1)
        helper.change("knowledge", 1)
        cause = "The rolling ship made the dish slide when Luna carried it in both hands."
        result = "The crew learned that hands alone were too wobbly."
        world.record(
            "try_hands",
            f'Luna lifted the lasagne with both hands. "Steady as a sea star!" '
            f'she said, but the {world.setting.surface} tilted and the dish slid '
            f"one inch. {helper.label} caught it before it fell. {result}",
            actor="hero",
            target="dish",
            cause=cause,
            result=result,
        )
    elif method == "tray":
        dish.change("slips", 1)
        hero.change("patience", 1)
        helper.change("knowledge", 1)
        cause = "A tray spread the weight, but the ship still rolled beneath it."
        result = "They discovered that a tray needed a rope to stay still."
        world.record(
            "try_tray",
            f'Luna placed the lasagne on a wooden tray. "This should help," she said. '
            f'The tray made it farther, then skated toward {world.setting.landmarks[0]}. '
            f'{helper.label} grabbed the rim. {result}',
            actor="hero",
            target="tray",
            cause=cause,
            result=result,
        )
    elif method == "rope":
        dish.change("secure", 1)
        hero.change("patience", 1)
        hero.change("confidence", 1)
        cause = "A rope could hold the tray while the deck rolled."
        result = "The lasagne reached the captain's table without sliding."
        world.record(
            "tie_rope",
            f'Luna tied a soft rope around the tray and tested the knot twice. '
            f'"Pull gently," {helper.label} said. "I will pull gently," Luna answered. '
            f'Together they carried the lasagne past {world.setting.landmarks[1]}, '
            f'and the rope kept the tray snug. {result}',
            actor="hero",
            target="rope",
            cause=cause,
            result=result,
        )
    else:
        raise StoryError("Unknown quest method.")


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("The chosen setting is not in the pirate chart.")
    if params.filling not in FILLINGS:
        raise StoryError("The chosen meal is not in the galley.")
    if params.attempts != 3:
        raise StoryError("This quest needs three repeating attempts: hands, tray, and rope.")
    if params.hero == params.companion:
        raise StoryError("The hero and companion need different names.")

    world = World(SETTINGS[params.setting])
    world.add(Entity("hero", "character", params.hero, memes={"hope": 1}))
    world.add(Entity("helper", "character", params.companion, memes={"care": 1}))
    world.add(Entity("dish", "food", "the lasagne", owner="hero"))
    world.add(Entity("tray", "tool", "a wooden tray"))
    world.add(Entity("rope", "tool", "a soft rope"))
    world.add(Entity("table", "place", "the captain's table"))
    world.facts.update(
        hero=params.hero,
        companion=params.companion,
        filling=params.filling,
        setting=params.setting,
        solved=False,
    )

    hero = world.entities["hero"]
    helper = world.entities["helper"]
    dish = world.entities["dish"]

    world.record(
        "begin",
        f"Captain {hero.label} stood aboard {world.setting.name} with a warm dish of "
        f"lasagne. It smelled {FILLINGS[params.filling]['smell']}, and the crew had "
        f"promised to share it at {world.setting.landmarks[2]}. {helper.label} pointed "
        f"toward the rolling {world.setting.surface}. "
        f'"How will you carry it?" {helper.label} asked. "I will find a way," '
        f'{hero.label} replied.',
        actor="hero",
        target="dish",
        cause="The crew needed to carry the warm meal across a moving ship.",
        result="Luna began a quest to get the lasagne safely to the table.",
    )

    world.para()
    solve_step(world, "hands")
    world.para()
    solve_step(world, "tray")
    world.para()
    solve_step(world, "rope")

    dish.change("delivered", 1)
    hero.memes["joy"] = 1
    world.facts["solved"] = True
    world.record(
        "share",
        f'At last, {hero.label} set the lasagne on {world.setting.landmarks[2]}. '
        f'"We tried, noticed, and tried again," said {hero.label}. '
        f'"That is fine pirate problem solving," {helper.label} replied. '
        f'The crew shared warm lasagne while the moon shone on the sea, and the '
        f'lasagne stayed safely on the table.',
        actor="hero",
        target="table",
        cause="The rope held the tray after the first two attempts taught them what was missing.",
        result="The crew shared a safe meal and celebrated the solved quest.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a gentle Pirate Tale about {world.facts['hero']} carrying lasagne "
        f"across {world.setting.name}. Repeat three attempts so the child sees "
        f"problem solving.",
        f"Tell a quest story in which an urchin-like young pirate notices why a "
        f"meal slides, changes the plan, and reaches {world.setting.landmarks[2]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "begin": "What quest did Luna begin?",
        "try_hands": "Why did carrying the lasagne in both hands not work?",
        "try_tray": "What did the tray teach the crew?",
        "tie_rope": "How did Luna keep the tray from sliding?",
        "share": "How did the quest end?",
    }
    return [
        QAItem(question=questions[event.kind], answer=f"{event.cause} {event.result}")
        for event in world.history
        if event.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an urchin?",
            answer="An urchin is a small sea animal with a round body and many sharp spines.",
        ),
        QAItem(
            question="What is lasagne?",
            answer="Lasagne is a baked meal made with layers of pasta, sauce, and filling.",
        ),
        QAItem(
            question="Why can repetition help with problem solving?",
            answer="Repetition helps because each try gives you a chance to notice what happened and improve the next plan.",
        ),
        QAItem(
            question="What is a pirate quest?",
            answer="A pirate quest is an adventure with a goal, obstacles, and brave choices along the way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(dish) :- moving_surface(deck).
at_risk(dish) :- moving_surface(galley).
works(hands) :- at_risk(dish).
works(tray) :- at_risk(dish).
works(rope) :- at_risk(dish).
solved(rope) :- works(rope).
valid(S, F) :- setting(S), filling(F), solved(rope).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for filling in FILLINGS:
        lines.append(asp.fact("filling", filling))
    lines.append(asp.fact("moving_surface", "deck"))
    lines.append(asp.fact("moving_surface", "galley"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.facts["solved"]
    assert [e.kind for e in world.history] == [
        "begin",
        "try_hands",
        "try_tray",
        "tie_rope",
        "share",
    ]
    assert world.entities["dish"].meter("delivered") == 1
    assert world.entities["dish"].meter("slips") == 2
    assert len(sample.story_qa) == 5
    assert all(item.answer.endswith(".") for item in sample.story_qa)
    assert not any(x in sample.story for x in ("{", "}", "__", "meters=", "memes="))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    expected = {(s, f) for s, f in py}
    if clingo != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    sample = generate(
        StoryParams(
            setting="deck",
            filling="lasagne",
            hero="Luna",
            companion="Otto",
            seed=1,
        )
    )
    check_sample(sample)
    print(f"OK: {len(py)} ASP/Python combinations and story-state checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate Tale quest with repetition and problem solving.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--filling", choices=FILLINGS, default="lasagne")
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    filling = args.filling or "lasagne"
    hero = args.hero or rng.choice(HEROES)
    companion = args.companion or rng.choice([name for name in COMPANIONS if name != hero])
    if hero == companion:
        raise StoryError("The hero and companion need different names.")
    return StoryParams(
        setting=setting,
        filling=filling,
        hero=hero,
        companion=companion,
    )


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


CURATED = [
    StoryParams("deck", "lasagne", "Luna", "Otto"),
    StoryParams("galley", "lasagne", "Mara", "Tess"),
    StoryParams("cove", "lasagne", "Pip", "Rafi"),
]


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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible pirate quests:")
        for setting, filling in asp_valid_combos():
            print(f"  {setting}: {filling}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero}: {sample.params.setting} quest"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
