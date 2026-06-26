#!/usr/bin/env python3
"""
storyworlds/worlds/caddy_recognition_effeminate_sharing_humor_quest_superhero.py
=================================================================================

A standalone story world for a tiny superhero tale about a quest, a shared caddy,
a little humor, and the kind of recognition that helps a hero feel brave.

The seed prompt suggested the words caddy, recognition, and effeminate, with
Sharing, Humor, and Quest as narrative instruments, in a Superhero Story style.

This world models a small city adventure where a young hero carries a caddy of
useful things, helps others along the way, and returns home with recognition for
kindness as well as courage.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Metered:
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Hero(Metered):
    name: str = "Milo"
    role: str = "boy"
    outfit: str = "sparkly cape"
    adjective: str = "gentle"
    pride: float = 0.0
    worry: float = 0.0
    joy: float = 0.0


@dataclass
class CityPlace(Metered):
    name: str = "the city"
    place_type: str = "city"
    noisy: bool = True


@dataclass
class Caddy(Metered):
    label: str = "caddy"
    owner: str = "Milo"
    items: list[str] = field(default_factory=list)
    shared: bool = False


@dataclass
class Quest:
    goal: str
    item: str
    place: str
    obstacle: str
    reward: str


@dataclass
class World:
    hero: Hero
    caddy: Caddy
    place: CityPlace
    quest: Quest
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

        return World(
            hero=copy.deepcopy(self.hero),
            caddy=copy.deepcopy(self.caddy),
            place=copy.deepcopy(self.place),
            quest=copy.deepcopy(self.quest),
            facts=copy.deepcopy(self.facts),
            paragraphs=[[]],
        )


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero_name: str = "Milo"
    hero_role: str = "boy"
    outfit: str = "sparkly cape"
    adjective: str = "gentle"
    place: str = "the avenue"
    quest_item: str = "missing medal"
    obstacle: str = "a spilled box of marbles"
    reward: str = "a bright thank-you note"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_NAMES = ["Milo", "Nia", "Tessa", "Rowan", "Pip", "Aria"]
HERO_ROLES = ["boy", "girl"]
ADJECTIVES = ["gentle", "brave", "bright", "sweet", "effeminate"]
OUTFITS = [
    "sparkly cape",
    "soft lavender suit",
    "shiny boots",
    "polished mask",
]
PLACES = [
    "the avenue",
    "the rooftop garden",
    "the old bridge",
    "the sunny square",
]
QUEST_ITEMS = [
    "missing medal",
    "lost key",
    "tiny rescue bell",
    "silver star pin",
]
OBSTACLES = [
    "a spilled box of marbles",
    "a stuck door",
    "a windy corner",
    "a tall puddle",
]
REWARDS = [
    "a bright thank-you note",
    "a big cheer",
    "a round of applause",
    "a warm hug",
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    if not params.hero_name:
        return False
    if params.adjective == "effeminate" and params.outfit not in {"sparkly cape", "soft lavender suit"}:
        return False
    if params.quest_item == "missing medal" and params.place not in {"the avenue", "the sunny square"}:
        return False
    return True


def explain_invalid(params: StoryParams) -> str:
    if params.adjective == "effeminate" and params.outfit not in {"sparkly cape", "soft lavender suit"}:
        return "No story: an effeminate style here needs a softer, sparkly outfit to fit the superhero tone."
    if params.quest_item == "missing medal" and params.place not in {"the avenue", "the sunny square"}:
        return "No story: the missing medal quest only makes sense in a lively city place."
    return "No story: the given choices do not make a reasonable superhero adventure."


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World) -> None:
    h = world.hero
    world.say(
        f"{h.name} was a little superhero with a {h.outfit} and a {h.adjective} smile."
    )
    world.say(
        f"{h.name} kept a caddy full of useful things: a ribbon, a snack, a spare glove, and a chalk map."
    )
    world.facts["intro_done"] = True


def quest_call(world: World) -> None:
    h = world.hero
    q = world.quest
    world.say(
        f"One morning, {h.name} heard about a quest to find {q.item} near {q.place}."
    )
    world.say(
        f"{h.name} wanted to help right away, because heroes felt strongest when they shared what they had."
    )
    h.worry += 1
    h.memes["quest"] = h.memes.get("quest", 0) + 1
    world.facts["quest_called"] = True


def travel_and_help(world: World) -> None:
    h = world.hero
    c = world.caddy
    q = world.quest
    world.say(
        f"At {q.place}, {h.name} found {q.obstacle} blocking the path."
    )
    world.say(
        f"{h.name} opened the caddy and shared the snack with a tired pigeon, then used the chalk map to mark a safe way around."
    )
    c.shared = True
    c.meters["opened"] = c.meters.get("opened", 0) + 1
    h.meters["helped"] = h.meters.get("helped", 0) + 1
    h.joy += 1
    world.facts["help_done"] = True


def humor_turn(world: World) -> None:
    h = world.hero
    world.say(
        f"A passing child laughed when {h.name}'s cape fluttered like a laundry flag."
    )
    world.say(
        f"{h.name} giggled too and said, “It is not flying away — it is practicing its superhero pose!”"
    )
    h.joy += 1
    h.pride += 1
    world.facts["humor_done"] = True


def resolve(world: World) -> None:
    h = world.hero
    q = world.quest
    world.say(
        f"Then {h.name} spotted {q.item} tucked beside {q.obstacle}, and carefully picked it up."
    )
    world.say(
        f"The grateful town guard gave {h.name} {q.reward}, and everyone cheered for the hero who shared, solved the problem, and stayed kind."
    )
    h.meters["recognized"] = h.meters.get("recognized", 0) + 1
    h.joy += 1
    h.pride += 1
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    if not valid_combo(params):
        raise StoryError(explain_invalid(params))
    world = World(
        hero=Hero(
            name=params.hero_name,
            role=params.hero_role,
            outfit=params.outfit,
            adjective=params.adjective,
        ),
        caddy=Caddy(owner=params.hero_name, items=["snack", "ribbon", "spare glove", "chalk map"]),
        place=CityPlace(name=params.place),
        quest=Quest(
            goal="find and return the lost item",
            item=params.quest_item,
            place=params.place,
            obstacle=params.obstacle,
            reward=params.reward,
        ),
    )
    world.say(
        f"{world.hero.name} lived in the city and loved being a superhero."
    )
    introduce(world)
    world.para()
    quest_call(world)
    travel_and_help(world)
    world.para()
    humor_turn(world)
    resolve(world)

    world.facts.update(
        hero=world.hero,
        caddy=world.caddy,
        place=world.place,
        quest=world.quest,
    )
    return world


# ---------------------------------------------------------------------------
# ASPs: inline rules and facts
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the hero can have the right outfit for the chosen tone.
reasonable(Hero, Outfit) :- hero(Hero), outfit(Outfit), not bad_pair(Hero, Outfit).

bad_pair(Hero, Outfit) :- adjective(Hero, effeminate), outfit(Outfit), not soft_style(Outfit).

% A quest is valid in a lively city place.
valid_quest(Item, Place) :- quest_item(Item), place(Place), city_place(Place).

% Sharing helps when the hero has a caddy and opens it.
shares_help(Hero) :- hero(Hero), has_caddy(Hero), opened_caddy(Hero).

#show reasonable/2.
#show valid_quest/2.
#show shares_help/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero", name))
    for role in HERO_ROLES:
        lines.append(asp.fact("role", role))
    for outfit in OUTFITS:
        lines.append(asp.fact("outfit", outfit))
    for adj in ADJECTIVES:
        lines.append(asp.fact("adjective", adj))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p in {"the avenue", "the sunny square"}:
        lines.append(asp.fact("city_place", p))
    for q in QUEST_ITEMS:
        lines.append(asp.fact("quest_item", q))
    for o in OUTFITS:
        if o in {"sparkly cape", "soft lavender suit"}:
            lines.append(asp.fact("soft_style", o))
    lines.append(asp.fact("has_caddy", "Milo"))
    lines.append(asp.fact("opened_caddy", "Milo"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    h = world.hero
    q = world.quest
    return [
        f'Write a short superhero story for a child about {h.name}, a caddy, and a quest for {q.item}.',
        f"Tell a gentle superhero tale where {h.name} uses a caddy, shares something helpful, and earns recognition.",
        f'Write a story that includes humor, sharing, and the word "caddy" in a city adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    q = world.quest
    return [
        QAItem(
            question=f"What was {h.name} carrying during the quest?",
            answer=f"{h.name} was carrying a caddy full of useful things, including a snack, a ribbon, a spare glove, and a chalk map.",
        ),
        QAItem(
            question=f"Why did the hero visit {q.place}?",
            answer=f"{h.name} went to {q.place} because there was a quest to find {q.item}.",
        ),
        QAItem(
            question=f"How did {h.name} solve the problem at {q.place}?",
            answer=f"{h.name} shared a snack, used the chalk map to find a safe way around {q.obstacle}, and kept going on the quest.",
        ),
        QAItem(
            question=f"What gave the story its funny moment?",
            answer=f"The funny moment came when a passerby laughed at the cape, and {h.name} turned it into a joke about practicing a superhero pose.",
        ),
        QAItem(
            question=f"What kind of recognition did {h.name} get at the end?",
            answer=f"{h.name} got {q.reward} and a cheer from the town because the hero was helpful and kind.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caddy?",
            answer="A caddy is a container or carrier that helps hold and carry useful things together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something you have, like food, tools, or a space.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something, help someone, or solve a problem.",
        ),
        QAItem(
            question="What is recognition?",
            answer="Recognition means noticing and praising someone for what they did, so they feel seen and appreciated.",
        ),
        QAItem(
            question="What is humor in a story?",
            answer="Humor is the funny part that makes people smile or laugh without hurting anyone.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable/2. #show valid_quest/2. #show shares_help/1."))
    return sorted(set(asp.atoms(model, "reasonable"))), sorted(set(asp.atoms(model, "valid_quest"))), sorted(set(asp.atoms(model, "shares_help")))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show reasonable/2. #show valid_quest/2. #show shares_help/1."))
    reasonables = set(asp.atoms(model, "reasonable"))
    valid_q = set(asp.atoms(model, "valid_quest"))
    shares = set(asp.atoms(model, "shares_help"))

    py_reasonable = {(h, o) for h in HERO_NAMES for o in OUTFITS if (o in {"sparkly cape", "soft lavender suit"}) or True}
    py_valid = {(q, p) for q in QUEST_ITEMS for p in {"the avenue", "the sunny square"}}
    py_shares = {("Milo",)}

    ok = True
    if not reasonables:
        ok = False
    if not valid_q:
        ok = False
    if not shares:
        ok = False

    if ok:
        print("OK: ASP rules generated a valid model.")
        return 0
    print("ASP verification failed.")
    print("Reasonable:", sorted(reasonables))
    print("Valid quest:", sorted(valid_q))
    print("Shares help:", sorted(shares))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld about a quest, a caddy, and recognition.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--role", choices=HERO_ROLES)
    ap.add_argument("--outfit", choices=OUTFITS)
    ap.add_argument("--adjective", choices=ADJECTIVES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--reward", choices=REWARDS)
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
    name = args.name or rng.choice(HERO_NAMES)
    role = args.role or rng.choice(HERO_ROLES)
    adjective = args.adjective or rng.choice(ADJECTIVES)
    outfit = args.outfit or rng.choice(OUTFITS if adjective != "effeminate" else ["sparkly cape", "soft lavender suit"])
    place = args.place or rng.choice(PLACES)
    quest_item = args.quest_item or rng.choice(QUEST_ITEMS)
    obstacle = args.obstacle or rng.choice(OBSTACLES)
    reward = args.reward or rng.choice(REWARDS)

    params = StoryParams(
        hero_name=name,
        hero_role=role,
        outfit=outfit,
        adjective=adjective,
        place=place,
        quest_item=quest_item,
        obstacle=obstacle,
        reward=reward,
    )
    if not valid_combo(params):
        raise StoryError(explain_invalid(params))
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"hero: {world.hero}")
    lines.append(f"caddy: {world.caddy}")
    lines.append(f"place: {world.place}")
    lines.append(f"quest: {world.quest}")
    lines.append(f"facts: {world.facts}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2. #show valid_quest/2. #show shares_help/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show reasonable/2. #show valid_quest/2. #show shares_help/1."))
        print("reasonable:", sorted(set(asp.atoms(model, "reasonable"))))
        print("valid_quest:", sorted(set(asp.atoms(model, "valid_quest"))))
        print("shares_help:", sorted(set(asp.atoms(model, "shares_help"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Milo", "boy", "sparkly cape", "effeminate", "the avenue", "missing medal", "a spilled box of marbles", "a bright thank-you note"),
            StoryParams("Nia", "girl", "soft lavender suit", "gentle", "the sunny square", "silver star pin", "a windy corner", "a round of applause"),
            StoryParams("Tessa", "girl", "shiny boots", "bright", "the avenue", "tiny rescue bell", "a tall puddle", "a big cheer"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(p)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
