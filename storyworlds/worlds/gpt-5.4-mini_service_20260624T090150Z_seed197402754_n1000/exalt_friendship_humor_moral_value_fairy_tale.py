#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a childlike kingdom where praise, friendship,
humor, and moral value can be weighed in the world state.

Premise:
- A young hero learns that boasting can make a friend feel small.
- The right turn is not a trick victory, but a kinder, funnier act: the hero
  uses humor to lift a friend up instead of trying to exalt only themself.

This script keeps the domain small and classical:
- typed entities with physical meters and emotional memes
- a forward-simulated world model that drives the prose
- a reasonableness gate for the compatible story shape
- an inline ASP twin of the same gate
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "prince", "king", "wizard", "knight"}
        female = {"girl", "princess", "queen", "witch"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit village green"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    turn: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    helps: str
    spark: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turn_state: str = "setup"

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


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

SETTINGS = {
    "village_green": Setting(place="the moonlit village green", outdoors := True, affords={"sing", "joke", "exalt"}),
    "castle_courtyard": Setting(place="the castle courtyard", indoors=False, affords={"sing", "joke", "exalt"}),
    "storybook_bridge": Setting(place="the storybook bridge", indoors=False, affords={"joke", "exalt"}),
}

ACTIONS = {
    "joke": Action(
        id="joke",
        verb="tell a joke",
        gerund="telling jokes",
        rush="blurt out a boast",
        risk="make a friend feel small",
        turn="turn the boast into a laughing matter",
        consequence="laughing together and feeling close again",
        keyword="laugh",
        tags={"humor", "friendship"},
    ),
    "sing": Action(
        id="sing",
        verb="sing a praise-song",
        gerund="singing praise-songs",
        rush="sing too loudly about oneself",
        risk="hide the value of a friend's help",
        turn="sing a duet that shares the praise",
        consequence="sharing the song like warm bread",
        keyword="song",
        tags={"friendship", "moral"},
    ),
    "exalt": Action(
        id="exalt",
        verb="exalt a friend",
        gerund="exalting a friend",
        rush="try to exalt oneself instead",
        risk="turn kindness into bragging",
        turn="exalt the friend in front of the whole square",
        consequence="a kinder heart and a brighter smile",
        keyword="exalt",
        tags={"friendship", "humor", "moral"},
    ),
}

CHARMS = {
    "garland": Charm(
        id="garland",
        label="a flower garland",
        phrase="a little flower garland",
        helps="makes the honor feel gentle",
        spark="fresh petals and a bright scent",
    ),
    "bell": Charm(
        id="bell",
        label="a silver bell",
        phrase="a tiny silver bell",
        helps="rings at the funny moment",
        spark="a merry tinkling sound",
    ),
}

GIRL_NAMES = ["Elia", "Mara", "Nina", "Sera", "Lina", "Tessa"]
BOY_NAMES = ["Oren", "Pip", "Tobin", "Rafi", "Milo", "Jasper"]
FRIEND_NAMES = ["Bram", "Penny", "Ludo", "Wren", "Holly", "Nell"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    action: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    charm: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Gate: only stories with real tension and real repair are allowed.
# ---------------------------------------------------------------------------

def action_needs_friendship(action: Action) -> bool:
    return "friendship" in action.tags


def select_charm(action: Action) -> Optional[Charm]:
    if action.id == "joke":
        return CHARMS["bell"]
    return CHARMS["garland"]


def explain_rejection(action: Action) -> str:
    return f"(No story: this world only tells fairy tales where {action.verb} can lead to a friendship turn.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for action_id, action in ACTIONS.items():
            if not action_needs_friendship(action):
                continue
            for charm_id in CHARMS:
                combos.append((setting_id, action_id, charm_id))
    return combos


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def _hero_intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Once, in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"who loved the sound of applause and the warmth of a true friend."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a dear friend named {friend.id}, and "
        f"they met every evening when the stars began to blink."
    )


def _friendship_setup(world: World, hero: Entity, friend: Entity, action: Action, charm: Charm) -> None:
    hero.memes["pride"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} wanted to {action.verb}, because {hero.pronoun('possessive')} heart "
        f"felt big that day."
    )
    world.say(
        f"{friend.id} brought {charm.phrase}, and {charm.spark} made the whole square feel like a storybook."
    )


def _boast_turn(world: World, hero: Entity, friend: Entity, action: Action) -> None:
    hero.memes["boast"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"But when the moment came, {hero.id} nearly forgot {action.verb} and tried to "
        f"{action.rush}."
    )
    world.say(
        f"{friend.id}'s smile grew small, for bragging can be a sharp thorn even in a lovely tale."
    )


def _repair(world: World, hero: Entity, friend: Entity, action: Action, charm: Charm) -> None:
    hero.memes["shame"] += 1
    hero.memes["humor"] += 1
    friend.memes["hurt"] = 0.0
    friend.memes["joy"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{hero.id} stopped at once, looked at {friend.id}, and remembered what was truly noble."
    )
    world.say(
        f"Then {hero.id} used {charm.label} to {action.turn}, and the little bell of shame turned into laughter."
        if charm.id == "bell"
        else f"Then {hero.id} used {charm.label} to {action.turn}, and the flower scent softened every word."
    )
    world.say(
        f"{hero.id} praised {friend.id} first, and the two of them shared the honor like a lantern shared on a dark road."
    )
    world.say(
        f"In the end, they were {action.consequence}, and the village remembered that true greatness is kind."
    )


def tell(world: World, hero: Entity, friend: Entity, action: Action, charm: Charm) -> None:
    _hero_intro(world, hero, friend)
    world.para()
    _friendship_setup(world, hero, friend, action, charm)
    _boast_turn(world, hero, friend, action)
    world.para()
    _repair(world, hero, friend, action, charm)
    world.facts.update(hero=hero, friend=friend, action=action, charm=charm)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, action, charm = f["hero"], f["friend"], f["action"], f["charm"]
    return [
        f'Write a short fairy tale for a child where {hero.id} tries to {action.verb}, stumbles into pride, and learns a kinder way.',
        f"Tell a story where {hero.id} and {friend.id} use humor to repair a wobble in friendship.",
        f'Write a gentle moral tale that includes the word "{action.keyword}" and ends with praise shared openly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, action, charm = f["hero"], f["friend"], f["action"], f["charm"]
    return [
        QAItem(
            question=f"Who wanted to {action.verb} in the fairy tale?",
            answer=f"{hero.id} wanted to {action.verb} in {world.setting.place}, but first {hero.id} had to learn how to do it kindly.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} first tried to {action.verb}?",
            answer=f"{hero.id} nearly turned the moment into bragging, and that made {friend.id} feel small and hurt for a little while.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} used {charm.label} and humor to {action.turn}, then praised {friend.id} first so the friendship could shine again.",
        ),
        QAItem(
            question=f"What did the ending show about the moral value of the story?",
            answer="It showed that true honor is not taking all the praise for yourself. Kind words, shared laughter, and loyal friendship make the best ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between people who care about each other, help each other, and enjoy each other's company.",
        ),
        QAItem(
            question="Why can humor help in a hard moment?",
            answer="Humor can help because a gentle laugh can soften hurt feelings and make it easier for people to talk kindly again.",
        ),
        QAItem(
            question="What does moral value mean in a fairy tale?",
            answer="Moral value means the story teaches a good lesson, like being kind, honest, fair, or brave in the right way.",
        ),
        QAItem(
            question="What does it mean to exalt someone?",
            answer="To exalt someone means to praise and lift them up, as if you are holding up their good name for everyone to see.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization and display
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id} ({ent.type}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
action_needs_friendship(A) :- action(A), tag(A, friendship).
valid_story(S, A, C) :- setting(S), action(A), charm(C), action_needs_friendship(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import in ASP helpers
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for tag in action.tags:
            lines.append(asp.fact("tag", aid, tag))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_story(setting_id: str, action_id: str, charm_id: str, name: str, gender: str, friend_name: str, friend_gender: str) -> StorySample:
    setting = SETTINGS[setting_id]
    action = ACTIONS[action_id]
    charm = CHARMS[charm_id]
    world = World(setting)

    hero = world.add(Entity(id=name, kind="character", type="girl" if gender == "girl" else "boy"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl" if friend_gender == "girl" else "boy"))
    tell(world, hero, friend, action, charm)

    return StorySample(
        params=StoryParams(
            setting=setting_id,
            action=action_id,
            hero_name=name,
            hero_gender=gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            charm=charm_id,
        ),
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.action not in ACTIONS:
        raise StoryError("(Unknown action.)")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(Unknown setting.)")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        if args.action:
            raise StoryError(explain_rejection(ACTIONS[args.action]))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, action_id, charm_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(
        setting=setting_id,
        action=action_id,
        hero_name=hero_name,
        hero_gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        charm=charm_id,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(
        params.setting,
        params.action,
        params.charm,
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("village_green", "exalt", "Elia", "girl", "Bram", "boy", "garland"),
    StoryParams("castle_courtyard", "joke", "Milo", "boy", "Nell", "girl", "bell"),
    StoryParams("storybook_bridge", "sing", "Tessa", "girl", "Rafi", "boy", "garland"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about friendship, humor, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, action, charm) combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
