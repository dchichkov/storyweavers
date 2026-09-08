#!/usr/bin/env python3
"""
A small adventure storyworld about persuading a friend to clear trail clutter,
discovering the moral value of care, and reaching a happy ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


OPENERS = [
    "At dawn, when the hills were pink and the trail smelled of pine,",
    "On a bright morning beside the Whispering Ridge,",
    "Beyond the last houses of the valley,",
    "When the mountain path glittered with dew,",
]

SCENES = [
    "A narrow trail curled between ferns, fallen branches, and smooth gray stones.",
    "Birds called from the trees while the old trail climbed toward a wooden bridge.",
    "The path crossed a meadow where yellow flowers nodded in the cool wind.",
    "Far above the village, a trail marker pointed toward the hidden waterfall.",
]

CLUTTER = {
    "branches": {
        "label": "fallen branches",
        "hazard": "hiding the stepping stones",
        "work": "dragged the branches to the edge of the trail",
        "result": "the stepping stones appeared again",
    },
    "litter": {
        "label": "bright wrappers and tin cans",
        "hazard": "slipping under careless feet and scaring the animals",
        "work": "gathered the wrappers and cans into a sturdy sack",
        "result": "the grass looked clean and the birds returned",
    },
    "stones": {
        "label": "a tumble of loose stones",
        "hazard": "rolling beneath a traveler's boots",
        "work": "stacked the loose stones beside the path",
        "result": "the trail became firm enough for everyone to pass",
    },
}

APPEALS = {
    "kindness": {
        "line": "A good path is a gift to the next traveler.",
        "action": "thought about the tired hikers who would come after them",
    },
    "safety": {
        "line": "If we clear it, nobody will trip here.",
        "action": "noticed how easily a hidden obstacle could hurt someone",
    },
    "nature": {
        "line": "The forest shares this trail with us, so we should leave it gentle.",
        "action": "listened to the small creatures moving near the mess",
    },
}

REWARDS = {
    "waterfall": "the secret waterfall",
    "lookout": "the eagle lookout",
    "orchard": "the mountain orchard",
}

ENDINGS = {
    "rainbow": "At sunset, a rainbow arched above the clean trail, and the two friends reached the waterfall laughing.",
    "lantern": "That evening, their lantern shone on the open path as they returned safely to the village.",
    "bell": "At the lookout, a little trail bell rang in the wind, celebrating the friends who had made the way safe.",
}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    affordances: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str = "ridge"
    clutter: str = "branches"
    appeal: str = "kindness"
    destination: str = "waterfall"
    ending: str = "rainbow"
    hero: str = "Luna"
    friend: str = "Pip"
    seed: Optional[int] = None


SETTINGS = {
    "ridge": Setting("Whispering Ridge", {"climb", "clear", "explore"}),
    "meadow": Setting("Sunrise Meadow", {"cross", "clear", "explore"}),
}

HERO_NAMES = ["Luna", "Mara", "Tavi", "Nia"]
FRIEND_NAMES = ["Pip", "Bram", "Kito", "Suri"]


def validate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.clutter not in CLUTTER:
        raise StoryError(f"Unknown clutter type: {params.clutter}")
    if params.appeal not in APPEALS:
        raise StoryError(f"Unknown appeal: {params.appeal}")
    if params.destination not in REWARDS:
        raise StoryError(f"Unknown destination: {params.destination}")
    if params.ending not in ENDINGS:
        raise StoryError(f"Unknown ending: {params.ending}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")


def build_world(params: StoryParams, rng: random.Random) -> World:
    validate(params)
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(params.hero, "girl", f"young explorer {params.hero}", location=setting.name))
    friend = world.add(Entity(params.friend, "boy", f"young explorer {params.friend}", location=setting.name))
    trail = world.add(Entity("trail", "place", "the mountain trail", location=setting.name))
    world.facts.update(hero=hero, friend=friend, trail=trail)
    world.facts["clutter"] = CLUTTER[params.clutter]
    world.facts["appeal"] = APPEALS[params.appeal]
    world.facts["destination"] = REWARDS[params.destination]
    world.facts["ending"] = ENDINGS[params.ending]
    world.facts["scene"] = rng.choice(SCENES)
    world.facts["opener"] = rng.choice(OPENERS)

    hero.memes["responsibility"] = 1.0
    friend.memes["impatience"] = 1.0
    trail.meters["clutter"] = 1.0
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mess = f["clutter"]
    appeal = f["appeal"]

    world.say(f"{f['opener']} {hero.id} and {friend.id} set out toward {f['destination']}.")
    world.say(f"{f['scene']} Soon they found {mess['label']} spread across the trail, {mess['hazard']}.")
    world.say(f'"We should clear this clutter before we go on," {hero.id} said.')
    world.say(f'"But the destination is waiting," {friend.id} replied. "Someone else can clean it."')
    world.say(
        f'{hero.id} pointed to the blocked path. "{appeal["line"]}" '
        f'{friend.id} {appeal["action"]}.'
    )
    friend.memes["impatience"] = 0.0
    friend.memes["care"] = 1.0
    hero.memes["persuasion"] = 1.0
    world.trace.append("Luna persuaded Pip by connecting the clutter to another traveler's safety and comfort.")
    world.say(
        f'"You are right," {friend.id} said. "I would want someone to help me if I found this mess ahead."'
    )
    world.say(f"Together they {mess['work']}. {mess['result'].capitalize()}, and a shy rabbit hopped into view.")
    world.para()
    trail = f["trail"]
    trail.meters["clutter"] = 0.0
    trail.meters["safe"] = 1.0
    world.trace.append("The trail clutter meter fell to zero, and the path became safe.")
    world.say(
        f"The cleared trail led them onward. They crossed the ridge carefully and reached {f['destination']} before the sun touched the far hills."
    )
    world.say(
        f'{friend.id} smiled at {hero.id}. "I thought the adventure was the place we would reach, but helping made the journey better."'
    )
    world.say(
        f'"That is the best kind of treasure," {hero.id} answered.'
    )
    world.say(f["ending"])


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
    tell_story(world)
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mess = f["clutter"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write an adventure about {hero.id} persuading {friend.id} to clear {mess['label']} from a mountain trail.",
            f"Show how the moral value of caring for other travelers changes {friend.id}'s decision.",
            f"End with a happy ending at {f['destination']}.",
        ],
        story_qa=[
            QAItem(
                "What did Luna persuade Pip to do?",
                f"Luna persuaded Pip to help clear {mess['label']} from the trail before they continued their adventure.",
            ),
            QAItem(
                "Why did Pip change his mind?",
                f"Pip changed his mind because Luna explained that clearing the clutter would make the path safer and kinder for the next traveler.",
            ),
            QAItem(
                "What moral value did the friends learn?",
                "They learned that caring for others and leaving a shared path safe can make an adventure more meaningful.",
            ),
            QAItem(
                "How did the story end?",
                f"The friends cleared the trail, reached {f['destination']}, and enjoyed a happy ending together.",
            ),
        ],
        world_qa=[
            QAItem("What is clutter?", "Clutter is a collection of unwanted or misplaced things that makes a place harder or less safe to use."),
            QAItem("What does persuade mean?", "To persuade someone means to help that person agree to an idea or choose an action."),
            QAItem("Why should trails be kept clear?", "Clear trails help people and animals move safely and protect the shared environment."),
            QAItem("What is a moral value?", "A moral value is a principle about how to act well, such as kindness, honesty, or responsibility."),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id}: " + " ".join(details))
    lines.extend(f"  event: {item}" for item in world.trace)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        clutter=args.clutter or rng.choice(list(CLUTTER)),
        appeal=args.appeal or rng.choice(list(APPEALS)),
        destination=args.destination or rng.choice(list(REWARDS)),
        ending=args.ending or rng.choice(list(ENDINGS)),
        hero=args.hero or rng.choice(HERO_NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
    )


ASP_RULES = r"""
place(ridge).
place(meadow).
clutter(branches).
clutter(litter).
clutter(stones).
appeal(kindness).
appeal(safety).
appeal(nature).
destination(waterfall).
destination(lookout).
destination(orchard).
safe_action(clear).
persuades(appeal, clear) :- appeal(appeal).
valid_story(P, C, A, D) :- place(P), clutter(C), appeal(A), destination(D), safe_action(clear), persuades(A, clear).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", p) for p in SETTINGS
    ] + [
        asp.fact("clutter", c) for c in CLUTTER
    ] + [
        asp.fact("appeal", a) for a in APPEALS
    ] + [
        asp.fact("destination", d) for d in REWARDS
    ] + [
        asp.fact("safe_action", "clear"),
    ])


def asp_valid_combos() -> set[tuple]:
    import asp
    model = asp.one_model(asp_facts() + "\n" + ASP_RULES)
    return set(asp.atoms(model, "valid_story"))


def python_valid_combos() -> set[tuple]:
    return {
        (place, clutter, appeal, destination)
        for place in SETTINGS
        for clutter in CLUTTER
        for appeal in APPEALS
        for destination in REWARDS
    }


def verify() -> int:
    try:
        clingo_set = asp_valid_combos()
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    python_set = python_valid_combos()
    if clingo_set != python_set:
        print("ASP/Python parity failure.")
        print("Only in ASP:", sorted(clingo_set - python_set))
        print("Only in Python:", sorted(python_set - clingo_set))
        return 1
    sample = generate(StoryParams(seed=17))
    if not sample.story or "persuad" not in sample.story.lower() or "happy" not in sample.story.lower():
        print("Generated story verification failed.")
        return 1
    print(f"OK: ASP/Python parity and generated story checks passed ({len(python_set)} combinations).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about persuasion and trail clutter.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--clutter", choices=CLUTTER)
    parser.add_argument("--appeal", choices=APPEALS)
    parser.add_argument("--destination", choices=REWARDS)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts())
        print(ASP_RULES)
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        try:
            import asp
            models = asp.solve(asp_facts() + "\n" + ASP_RULES, models=1)
            print(f"ASP produced {len(models)} model(s).")
        except ImportError:
            print("ASP mode unavailable: clingo is not installed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    count = max(1, args.n)
    for index in range(count):
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
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        print(sample.story)
        if args.trace:
            print(dump_trace(sample.world))
        if args.qa:
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
