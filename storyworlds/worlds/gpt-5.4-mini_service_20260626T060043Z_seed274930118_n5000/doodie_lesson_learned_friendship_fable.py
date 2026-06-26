#!/usr/bin/env python3
"""
A small fable-like storyworld about a doodie mess, friendship, and a lesson learned.

The seed idea:
- A small friend makes a messy choice and harms trust.
- A friend notices, speaks kindly, and helps fix the problem.
- The ending proves the lesson learned through a changed state.

This script follows the Storyweavers world contract:
- StoryParams + registries + build_parser + resolve_params + generate + emit + main
- eager import of results.py for QAItem/StoryError/StorySample
- lazy import of asp.py only in ASP helpers
- inline ASP_RULES twin and Python reasonableness gate
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "cat", "rabbit", "bird", "squirrel"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mess: str
    stain: str
    tag: str


@dataclass
class Lesson:
    id: str
    moral: str
    trigger: str


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"snack", "nap", "play"}),
    "barnyard": Setting(place="the barnyard", affords={"snack", "play"}),
    "brook": Setting(place="the brook", affords={"play"}),
}

ACTIONS = {
    "snack": Action(
        id="snack",
        verb="eat a berry snack",
        gerund="eating berry snacks",
        mess="doodie",
        stain="stained with doodie",
        tag="berry",
    ),
    "play": Action(
        id="play",
        verb="play in the grass",
        gerund="playing in the grass",
        mess="doodie",
        stain="smudged with doodie",
        tag="play",
    ),
    "nap": Action(
        id="nap",
        verb="nap in the straw",
        gerund="napping in the straw",
        mess="doodie",
        stain="dirtied with doodie",
        tag="rest",
    ),
}

LESSONS = {
    "share": Lesson(
        id="share",
        moral="a true friend shares, helps, and tells the truth",
        trigger="a friend speaks kindly before the hurt grows bigger",
    ),
}

# The at-risk item is a friendship token; if it is dirtied, trust is hurt.
PRIZES = {
    "ribbon": "a bright friendship ribbon",
    "stone": "a smooth promise stone",
    "basket": "a little shared berry basket",
}

FRIENDS = {
    "fox": ("fox", "brave"),
    "rabbit": ("rabbit", "gentle"),
    "cat": ("cat", "curious"),
    "squirrel": ("squirrel", "quick"),
    "bird": ("bird", "cheerful"),
}

NAMES = ["Pip", "Milo", "Tansy", "Junie", "Fenn", "Willow", "Nell", "Bram", "Ollie", "Toby"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    prize: str
    lesson: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(action: Action, prize: str) -> bool:
    return action.mess == "doodie" and prize in PRIZES


def select_fix(action: Action, prize: str) -> bool:
    return prize_at_risk(action, prize)


def explain_rejection(action: Action, prize: str) -> str:
    return (
        f"(No story: {action.gerund} would not reasonably affect {PRIZES.get(prize, prize)} "
        f"in this small fable world.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            act = ACTIONS[action_id]
            for prize in PRIZES:
                if prize_at_risk(act, prize) and select_fix(act, prize):
                    out.append((place, action_id, prize))
    return out


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------
def predict_dirt(world: World, hero: Entity, action: Action, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["doodie"] = 1
    return action.mess == "doodie" and prize.id in sim.entities and True


def do_action(world: World, hero: Entity, action: Action) -> None:
    hero.meters[action.mess] = hero.meters.get(action.mess, 0.0) + 1
    hero.memes["mischief"] = hero.memes.get("mischief", 0.0) + 1


def clean_up(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    hero.meters["doodie"] = 0
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    friend.memes["kindness"] = friend.memes.get("kindness", 0.0) + 1
    prize.meters["dirty"] = 0
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1


def tell_story(setting: Setting, action: Action, prize_label: str, hero_name: str, hero_type: str,
               friend_name: str, friend_type: str, lesson: Lesson) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name))
    prize = world.add(Entity(id="prize", type="thing", label=prize_label, owner=hero.id))

    world.say(
        f"Once in {setting.place}, {hero.id} the {hero.type} and {friend.id} the {friend.type} "
        f"were true friends."
    )
    world.say(
        f"They loved to be together, and {friend.id} kept a {prize.label} as a sign of their friendship."
    )

    world.para()
    world.say(
        f"One bright day, {hero.id} wanted to {action.verb}, because {action.gerund} felt funny and free."
    )
    world.say(
        f"But that choice could leave {hero.pronoun('possessive')} paws {action.stain}, and it might spoil the shared token."
    )

    if predict_dirt(world, hero, action, prize):
        world.say(
            f"{friend.id} saw the trouble and said, \"A good friend does not hide a doodie mess.\""
        )
        world.say(
            f"{hero.id} felt bad and stopped at once."
        )
        do_action(world, hero, action)

    world.para()
    clean_up(world, hero, friend, prize)
    world.say(
        f"Together they washed the little token clean, and {hero.id} thanked {friend.id} for being patient."
    )
    world.say(
        f"{hero.id} learned that friendship grows best when friends are honest, helpful, and kind."
    )
    world.say(
        f"From then on, the two friends played together, and the {prize.label} stayed bright and clean."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        action=action,
        setting=setting,
        lesson=lesson,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place affords an action, and the action can create
% the doodie lesson around a friendship token.
at_risk(A, P) :- action(A), prize(P), mess_of(A, doodie), token(P).

valid(Place, A, P) :- affords(Place, A), at_risk(A, P), has_fix(A, P).
has_fix(A, P) :- at_risk(A, P).

valid_story(Place, A, P) :- valid(Place, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("token", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    prize = f["prize"]
    return [
        f"Write a short fable for children about {hero.id} and {friend.id}, friendship, and a doodie lesson learned.",
        f"Tell a gentle story where {hero.id} wants to {action.verb}, but {friend.id} protects {prize.label} and teaches a lesson.",
        f"Write a fable that includes the word doodie, a kind friend, and an ending where the mistake is cleaned up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who learned the lesson in the story?",
            answer=f"{hero.id} learned the lesson after making a doodie mess and then helping clean it up with {friend.id}.",
        ),
        QAItem(
            question=f"What did {friend.id} do when {hero.id} was about to make the mess?",
            answer=f"{friend.id} spoke kindly, warned about the doodie mess, and helped keep the friendship token safe.",
        ),
        QAItem(
            question=f"What stayed clean at the end?",
            answer=f"The {prize.label} stayed bright and clean, which showed that the friends fixed the problem together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is doodie in this story world?",
            answer="Doodie is the messy kind of dirt that can stain paws, clothes, or shared things when a character makes a careless choice.",
        ),
        QAItem(
            question="What does friendship mean here?",
            answer="Friendship means the characters care for each other, tell the truth, and help fix mistakes instead of making them worse.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the good idea the character understands after the mistake, so they act more kindly next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world about doodie, friendship, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--action", choices=ACTIONS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=list(FRIENDS.keys()))
    ap.add_argument("--friend-type", choices=list(FRIENDS.keys()))
    ap.add_argument("--lesson", choices=LESSONS.keys())
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
    if args.action and args.prize:
        act = ACTIONS[args.action]
        if not prize_at_risk(act, args.prize):
            raise StoryError(explain_rejection(act, args.prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(list(FRIENDS.keys()))
    friend_type = args.friend_type or rng.choice([k for k in FRIENDS.keys() if k != hero_type])
    hero_name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != hero_name])
    lesson = args.lesson or "share"
    return StoryParams(
        place=place,
        action=action,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        prize=prize,
        lesson=lesson,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        SETTINGS[params.place],
        ACTIONS[params.action],
        PRIZES[params.prize],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
        LESSONS[params.lesson],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("meadow", "snack", "Pip", "fox", "Tansy", "rabbit", "ribbon", "share"),
            StoryParams("barnyard", "play", "Milo", "cat", "Willow", "bird", "stone", "share"),
            StoryParams("brook", "play", "Nell", "squirrel", "Bram", "fox", "basket", "share"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name} at {p.place} ({p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
