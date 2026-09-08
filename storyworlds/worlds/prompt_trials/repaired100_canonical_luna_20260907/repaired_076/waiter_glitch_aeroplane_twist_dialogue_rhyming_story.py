#!/usr/bin/env python3
"""A rhyming StoryWorld about a waiter, an aeroplane, and a helpful glitch."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Sam"
    setting: str = "the little aeroplane"
    meal: str = "strawberry pie"
    glitch_kind: str = "mixed_up_order"
    rhyme_mode: str = "clap"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Glitch:
    key: str
    title: str
    problem: str
    clue: str
    tempting: str
    waiter_action: str
    dialogue: str
    turn: str
    ending: str
    lesson: str


NAMES = ("Luna", "Milo", "Nia", "Toby")
HELPERS = ("Sam", "Ari", "Pip", "Jo")
SETTINGS = ("the little aeroplane", "the cloud cruiser", "the sky-blue aeroplane")
MEALS = ("strawberry pie", "apple buns", "lemon cakes", "warm cocoa")
RHYME_MODES = ("clap", "bell", "whisper", "march")

GLITCHES = (
    Glitch(
        "mixed_up_order",
        "the muddled menu",
        "the tablet placed every passenger's meal on the wrong tray",
        "the seat cards did not match the names on the trays",
        "deliver the plates quickly and hope nobody would know",
        "checked the paper list, matched each tray to its passenger, and asked before serving",
        "A wrong tray is a clue, not a race. Shall we check each name and place?",
        "The glitch had hidden the labels, but the waiter discovered that the paper list still worked.",
        "The trays soon traveled in a neat parade, and the aeroplane hummed above the clouds.",
        "When a machine muddles things, careful checking can put them right.",
    ),
    Glitch(
        "frozen_screen",
        "the sleepy screen",
        "the serving screen froze just as the lunch bell rang",
        "the clock still moved while the screen stayed stuck",
        "tap the same button again and again",
        "paused the tapping, told the captain, and used the printed backup menu",
        "The screen may sleep, so do not make it guess. A paper plan can help us serve our best.",
        "The waiter learned that the old-fashioned menu was not old-fashioned at all; it was the safe backup.",
        "Paper menus fluttered like flags while every hungry traveler received a meal.",
        "A backup plan turns a puzzling pause into a manageable problem.",
    ),
    Glitch(
        "vanishing_trolley",
        "the runaway trolley",
        "a bump sent the snack trolley rolling toward the galley door",
        "the wheels spun even though the brake handle was down",
        "chase it between the seats",
        "called for help, blocked the aisle, and waited until the trolley was safely stopped",
        "The aeroplane gave a sudden sway, and the waiter chose a calm call instead of a wild chase.",
        "The twist was that the helper's quiet warning, not a fast foot, saved the snacks.",
        "The trolley rested by the galley, and warm buns reached every seat in time.",
        "Safety comes before speed when a machine or vehicle behaves oddly.",
    ),
    Glitch(
        "backward_beep",
        "the backward beep",
        "the meal bell beeped before the kitchen had finished the order",
        "the kitchen ticket still showed that the food was not ready",
        "announce that every meal was ready",
        "read the ticket aloud, told the passengers there would be a short wait, and confirmed the kitchen's signal",
        "A beep can sound bright, but words and tickets can tell us what is right.",
        "The false bell made the waiter slow down, and the real bell arrived with the real meal.",
        "The true bell chimed, and the whole cabin cheered in a gentle rhyme.",
        "Signals are useful clues, but checking the source prevents mistakes.",
    ),
)
GLITCH_BY_KEY = {item.key: item for item in GLITCHES}

OPENINGS = (
    "Luna climbed aboard with a spoon in her hand, while clouds curled softly above the bright land.",
    "Up in the sky where the silver wings gleamed, Luna served a lunch that had almost been dreamed.",
    "The little aeroplane lifted with cheer, and a rhyming meal-time began in the air.",
    "Round went the wheels, then up went the plane; Luna wore a smile like a sun after rain.",
)

REFRAINS = {
    "clap": "Check, check, cheer! Let careful hands steer.",
    "bell": "Ding, ding, ding! Wise checking makes the good news ring.",
    "whisper": "Softly we know, carefully go; that is the way safe answers grow.",
    "march": "Step by step and tray by tray, thoughtful helpers save the day.",
}


def validate(params: StoryParams) -> None:
    if params.glitch_kind not in GLITCH_BY_KEY:
        raise StoryError(f"Unknown glitch kind: {params.glitch_kind}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown passenger name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper name: {params.helper}")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.meal not in MEALS:
        raise StoryError(f"Unknown meal: {params.meal}")
    if params.rhyme_mode not in RHYME_MODES:
        raise StoryError(f"Unknown rhyme mode: {params.rhyme_mode}")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World(params)
    child = world.add(Entity(params.name, "passenger", params.name, {"calm": 0.7}, {"curiosity": 0.8}))
    waiter = world.add(Entity("waiter", "worker", "waiter", {"care": 1.0}, {"patience": 0.9}))
    helper = world.add(Entity("helper", "helper", params.helper, {"attention": 0.9}, {"trust": 0.8}))
    plane = world.add(Entity("aeroplane", "vehicle", "aeroplane", {"airborne": 1.0}, {"wonder": 0.9}))
    world.facts.update(child=child.label, waiter=waiter.label, helper=helper.label, vehicle=plane.label)
    return world


def pick(options: tuple[str, ...], params: StoryParams, salt: int) -> str:
    return random.Random((params.variant + 17) * 100003 ^ salt * 7919).choice(options)


def simulate(world: World) -> World:
    p = world.params
    glitch = GLITCH_BY_KEY[p.glitch_kind]
    world.say(pick(OPENINGS, p, 1))
    world.say(
        f"{p.name} was riding in {p.setting}, where the waiter carried {p.meal} "
        f"with a bright little rhyme: {REFRAINS[p.rhyme_mode]}"
    )
    world.say(f"{p.helper} helped count the trays while the aeroplane sailed through a cloud-white sky.")
    world.para()
    world.say(f"Then came {glitch.title}: {glitch.problem}.")
    world.say(f"The first important clue was this: {glitch.clue}.")
    world.say(f"It might have seemed easy to {glitch.tempting}, but that could have made the mix-up worse.")
    world.para()
    world.say(f"The waiter called, “{glitch.dialogue}”")
    world.say(f"{p.name} answered, “I will help you check, and {p.helper} can watch the aisle too.”")
    world.say(f"Together, the waiter and the helpers {glitch.waiter_action}.")
    world.say(f"{p.helper} said, “{glitch.turn}”")
    world.para()
    world.say(f"That was the twist: {glitch.turn}")
    world.say(f"Because they followed the clue, {glitch.ending}")
    world.say(f"{p.name} learned that {glitch.lesson}")
    world.say(REFRAINS[p.rhyme_mode])
    world.fired.update({"noticed_glitch", "spoke_up", "checked_backup", "resolved"})
    world.facts.update(
        glitch=p.glitch_kind,
        problem=glitch.problem,
        clue=glitch.clue,
        tempting_action=glitch.temping if hasattr(glitch, "temping") else glitch.tempting,
        waiter_action=glitch.waiter_action,
        turn=glitch.turn,
        resolved=True,
        ending=glitch.ending,
    )
    world.entities[p.name].memes.update(confidence=1.0, joy=1.0)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    glitch = GLITCH_BY_KEY[p.glitch_kind]
    return [
        f"Write a rhyming story about {p.name}, a waiter, and an aeroplane facing {glitch.title}.",
        f"Include child-friendly dialogue where the clue '{glitch.clue}' changes what the characters do.",
        f"Build to a twist and end with this image: {glitch.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    g = GLITCH_BY_KEY[p.glitch_kind]
    return [
        QAItem(f"What went wrong on the aeroplane?", f"The problem was that {g.problem}."),
        QAItem("What clue did the waiter notice?", f"The waiter noticed that {g.clue}."),
        QAItem("What did the waiter and helpers do?", f"They {g.waiter_action}."),
        QAItem("What was the twist in the story?", f"The twist was that {g.turn}"),
        QAItem("How did the story end?", f"{g.ending}"),
        QAItem("What lesson did Luna learn?", f"{g.lesson}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should a waiter check an order before serving it?",
            "Checking the order helps match the right food to the right person and prevents avoidable mistakes.",
        ),
        QAItem(
            "What should someone do when an aeroplane system glitches?",
            "They should stay calm, tell the responsible crew member, and follow the crew's safety instructions rather than improvising.",
        ),
        QAItem(
            "Why can a backup plan be useful?",
            "A backup plan provides a safe way to continue when a screen, signal, or machine stops working normally.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)), "", "== Story QA =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """passenger(X) :- named_passenger(X).
safe(X) :- passenger(X), noticed_glitch(X), spoke_up(X), checked_backup(X), resolved(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    atom = (params or StoryParams()).name.lower()
    return "\n".join(
        [
            asp.fact("named_passenger", atom),
            asp.fact("passenger", atom),
            asp.fact("noticed_glitch", atom),
            asp.fact("spoke_up", atom),
            asp.fact("checked_backup", atom),
            asp.fact("resolved", atom),
        ]
    )


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program("#show safe/1."))
    found = set(asp.atoms(symbols, "safe"))
    if not found:
        print("ASP verification failed.")
        return 1
    for key in GLITCH_BY_KEY:
        sample = generate(StoryParams(glitch_kind=key, variant=19))
        if "waiter" not in sample.story.lower() or "aeroplane" not in sample.story.lower():
            print(f"Story verification failed for {key}.")
            return 1
    print("OK: ASP twin confirms careful glitch handling, and generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming waiter and aeroplane StoryWorld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--meal", choices=MEALS)
    parser.add_argument("--glitch-kind", choices=tuple(GLITCH_BY_KEY))
    parser.add_argument("--rhyme-mode", choices=RHYME_MODES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        setting=args.setting or rng.choice(SETTINGS),
        meal=args.meal or rng.choice(MEALS),
        glitch_kind=args.glitch_kind or rng.choice(tuple(GLITCH_BY_KEY)),
        rhyme_mode=args.rhyme_mode or rng.choice(RHYME_MODES),
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}\nfired: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        symbols = asp.one_model(asp_program("#show safe/1."))
        print(json.dumps({"safe": asp.atoms(symbols, "safe")}, indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(
                StoryParams(
                    name="Luna",
                    helper="Sam",
                    setting="the little aeroplane",
                    meal="strawberry pie",
                    glitch_kind=key,
                    rhyme_mode=mode,
                    variant=index + 31,
                )
            )
            for index, (key, mode) in enumerate(
                (("mixed_up_order", "clap"), ("frozen_screen", "bell"), ("vanishing_trolley", "march"), ("backward_beep", "whisper"))
            )
        ]
    else:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)]

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        )
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
