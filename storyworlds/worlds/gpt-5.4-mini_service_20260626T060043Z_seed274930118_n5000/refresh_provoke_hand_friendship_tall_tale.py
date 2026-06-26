#!/usr/bin/env python3
"""
storyworlds/worlds/refresh_provoke_hand_friendship_tall_tale.py
===============================================================

A small tall-tale story world about Friendship, where a parched friend gets
refreshed, a boastful rival provokes trouble, and a helping hand turns the day
back toward laughter.

The world is intentionally small and state-driven:
- physical meters track thirst, dust, heat, and freshness
- emotional memes track friendship, pride, annoyance, courage, and delight
- narration is generated from the simulated state, not from a fixed template

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams + parser + resolve_params + generate + emit + main
- lazy ASP import inside ASP helpers only
- Python reasonableness gate plus inline ASP twin
- --verify checks Python/ASP parity and exercises generated stories
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
# Core story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle", "cowboy", "rancher"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryBeat:
    id: str
    verb: str
    gerund: str
    mess: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _n(v: float) -> float:
    return 1.0 if v >= THRESHOLD else 0.0


def add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "prairie": Setting(place="the wide prairie", weather="hot", affords={"refresh", "provoke", "hand"}),
    "riverbank": Setting(place="the riverbank", weather="windy", affords={"refresh", "provoke", "hand"}),
    "roundup": Setting(place="the cattle roundup", weather="dusty", affords={"refresh", "provoke", "hand"}),
}

BEATS = {
    "refresh": StoryBeat(
        id="refresh",
        verb="refresh a thirsty friend",
        gerund="refreshing a thirsty friend",
        mess="freshness",
        weather="hot",
        tags={"refresh", "water", "friendship"},
    ),
    "provoke": StoryBeat(
        id="provoke",
        verb="provoke a boastful troublemaker",
        gerund="provoke trouble",
        mess="dust",
        weather="dusty",
        tags={"provoke", "friendship", "dust"},
    ),
    "hand": StoryBeat(
        id="hand",
        verb="offer a helping hand",
        gerund="giving a helping hand",
        mess="calm",
        weather="windy",
        tags={"hand", "friendship"},
    ),
}

AIDS = {
    "canteen": Aid(
        id="canteen",
        label="a tin canteen",
        phrase="a tin canteen full of cool water",
        prep="raise the canteen and pour a cool drink",
        tail="poured cool water down the friend's dry throat",
        protects={"thirst"},
    ),
    "bandana": Aid(
        id="bandana",
        label="a wet bandana",
        phrase="a wet bandana that could cool a brow",
        prep="tie on the wet bandana",
        tail="wrapped cool cloth around the friend's brow",
        protects={"heat"},
    ),
    "shoulder": Aid(
        id="shoulder",
        label="a steady shoulder",
        phrase="a steady shoulder for a tired step",
        prep="brace one steady shoulder",
        tail="kept the friend from stumbling in the dust",
        protects={"wobble"},
    ),
    "hand": Aid(
        id="hand",
        label="a helping hand",
        phrase="a helping hand for a hard moment",
        prep="reach out a helping hand",
        tail="lifted the friend right back to their boots",
        protects={"fall"},
    ),
}

NAMES = ["Mabel", "Ruth", "June", "Nell", "Buck", "Hank", "Ivy", "Wes", "Jody", "Mae"]
TROUBLEMAKERS = ["Slim", "Rex", "Dusty", "Bo", "Milo", "Zeke"]


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    troublemaker: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for beat_id in setting.affords:
            beat = BEATS[beat_id]
            for aid_id, aid in AIDS.items():
                if beat_id == "refresh" and "thirst" in aid.protects:
                    combos.append((setting_id, beat_id))
                elif beat_id == "provoke" and "wobble" in aid.protects:
                    combos.append((setting_id, beat_id))
                elif beat_id == "hand" and "fall" in aid.protects:
                    combos.append((setting_id, beat_id))
    return sorted(set(combos))


def explain_rejection(setting_id: str, beat_id: str) -> str:
    beat = BEATS[beat_id]
    if beat_id == "refresh":
        return f"(No story: {settings_phrase(setting_id)} does not support a believable way to refresh a thirsty friend.)"
    if beat_id == "provoke":
        return f"(No story: {settings_phrase(setting_id)} does not give the troublemaker a reason to be provoked in a tall-tale way.)"
    return f"(No story: {settings_phrase(setting_id)} does not need a helping hand in a way that changes the friendship.)"


def settings_phrase(setting_id: str) -> str:
    return SETTINGS[setting_id].place


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.beat:
        if (args.setting, args.beat) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.beat))

    settings = [s for s in SETTINGS if args.setting is None or s == args.setting]
    if not settings:
        raise StoryError("(No valid setting matches the given options.)")
    setting = rng.choice(settings)

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    troublemaker = args.troublemaker or rng.choice(TROUBLEMAKERS)
    return StoryParams(setting=setting, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type, troublemaker=troublemaker)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    hero = world.add(Entity(
        id=params.hero, kind="character", type=params.hero_type,
        label=params.hero, traits=["bold", "friendly", "tall-tale"],
    ))
    friend = world.add(Entity(
        id=params.friend, kind="character", type=params.friend_type,
        label=params.friend, traits=["dusty", "kind"],
    ))
    trouble = world.add(Entity(
        id=params.troublemaker, kind="character", type="boy",
        label=params.troublemaker, traits=["boastful", "loud"],
    ))

    hero.memes.update(friendship=2.0, courage=1.0)
    friend.memes.update(friendship=2.0, tired=1.0, trust=1.0)
    trouble.memes.update(pride=1.0, provoke=1.0)

    world.facts.update(hero=hero, friend=friend, trouble=trouble, setting=world.setting)
    return world


def narrate_setup(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    place = world.setting.place
    world.say(f"{hero.id} and {friend.id} were the kind of friends folks remembered when the moon came up over {place}.")
    world.say(f"They had a friendship as wide as a wagon road and as steady as a fence post in a storm.")


def do_refresh(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    aid = AIDS["canteen"]
    add_meter(friend, "thirst", 1.0)
    add_meter(friend, "heat", 1.0)
    add_meme(friend, "weariness", 1.0)
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    world.say(f"The day ran hot, so {hero.id} lifted {aid.label} and {aid.prep} for {friend.id}.")
    world.say(f"{aid.tail}, and {friend.id} blinked like a cactus after rain.")


def do_provoke(world: World) -> None:
    trouble = world.facts["trouble"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    add_meme(trouble, "provocation", 1.0)
    add_meme(hero, "annoyance", 1.0)
    add_meme(friend, "startle", 1.0)
    world.say(f"Then {trouble.id} came swaggering by and tried to provoke a ruckus with a grin as crooked as a split rail.")
    world.say(f"{trouble.id} hollered that {hero.id} and {friend.id} could not cross the flat without looking silly.")


def do_hand(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(f"But {hero.id} only laughed, reached out a helping hand, and steadied {friend.id} before the dust could swallow the day.")
    add_meter(friend, "calm", 1.0)
    add_meme(hero, "delight", 1.0)
    add_meme(friend, "trust", 1.0)
    add_meme(friend, "friendship", 1.0)
    world.say(f"{friend.id} took the hand and stood straighter, as if courage itself had put on boots.")


def resolve_story(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    trouble = world.facts["trouble"]

    if friend.meters.get("thirst", 0.0) >= THRESHOLD:
        friend.meters["thirst"] = 0.0
        friend.meters["heat"] = max(0.0, friend.meters.get("heat", 0.0) - 1.0)
        friend.meters["freshness"] = friend.meters.get("freshness", 0.0) + 1.0

    trouble.memes["provocation"] = max(0.0, trouble.memes.get("provocation", 0.0) - 1.0)
    hero.memes["annoyance"] = max(0.0, hero.memes.get("annoyance", 0.0) - 1.0)
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0

    world.para()
    world.say(f"After that, {friend.id} felt fresh as creek water, and {trouble.id} had no one left to rattle.")
    world.say(f"{hero.id} and {friend.id} rode on laughing together, with the whole prairie looking smaller beside their friendship.")


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    world.para()
    do_refresh(world)
    do_provoke(world)
    do_hand(world)
    resolve_story(world)
    return world


# ---------------------------------------------------------------------------
# Verification and ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A friendship tall tale is valid when the setting supports a real refresh,
% a believable provocation, and a helpful hand that resolves the trouble.
valid(S, refresh) :- setting(S), affords(S, refresh), has_aid(refresh).
valid(S, provoke) :- setting(S), affords(S, provoke), has_aid(provoke).
valid(S, hand)    :- setting(S), affords(S, hand),    has_aid(hand).

has_aid(refresh) :- aid(canteen), protects(canteen, thirst).
has_aid(provoke) :- aid(shoulder), protects(shoulder, wobble).
has_aid(hand)    :- aid(hand), protects(hand, fall).

story_ok(S) :- valid(S, refresh), valid(S, provoke), valid(S, hand).
#show story_ok/1.
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for p in sorted(aid.protects):
            lines.append(asp.fact("protects", aid.id, p))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        sample = generate(resolve_params(argparse.Namespace(setting=None, beat=None, hero=None, hero_type=None, friend=None, friend_type=None, troublemaker=None), random.Random(7)))
        _ = sample.story
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos) and story generation runs.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A and formatting
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    trouble = f["trouble"]
    place = world.setting.place
    return [
        f'Write a tall-tale style story about friendship at {place} where {hero.id} uses a hand to help {friend.id}.',
        f"Tell a child-friendly story where {trouble.id} tries to provoke {hero.id} and {friend.id}, but friendship wins.",
        f'Create a short story using the words "refresh", "provoke", and "hand" in a frontier friendship adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    trouble = f["trouble"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who refreshed {friend.id} on the hot day at {place}?",
            answer=f"{hero.id} did. {hero.id} used a canteen to refresh {friend.id} when the day ran hot.",
        ),
        QAItem(
            question=f"Who tried to provoke trouble after the refreshing moment?",
            answer=f"{trouble.id} did. {trouble.id} came swaggering by and tried to provoke a ruckus.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help {friend.id} in the end?",
            answer=f"{hero.id} offered a helping hand, steadied {friend.id}, and kept the friendship strong.",
        ),
        QAItem(
            question=f"How did {friend.id} feel after taking the hand?",
            answer=f"{friend.id} felt fresh, calmer, and braver, like someone who had just found shade after a long ride.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to refresh someone?",
            answer="To refresh someone means to make them feel cooler, less tired, or more comfortable, like giving a thirsty friend cool water.",
        ),
        QAItem(
            question="What does provoke mean?",
            answer="To provoke means to stir up trouble or make someone feel challenged or annoyed on purpose.",
        ),
        QAItem(
            question="What is a helping hand?",
            answer="A helping hand is a kind way of offering support, like steadying a friend or lifting something together.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between friends who help, trust, and enjoy one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale friendship story world: refresh, provoke, and hand.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--troublemaker")
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


CURATED = [
    StoryParams(setting="prairie", hero="Mabel", hero_type="girl", friend="Buck", friend_type="boy", troublemaker="Slim"),
    StoryParams(setting="riverbank", hero="Hank", hero_type="boy", friend="Ivy", friend_type="girl", troublemaker="Rex"),
    StoryParams(setting="roundup", hero="June", hero_type="girl", friend="Wes", friend_type="boy", troublemaker="Dusty"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp_valid_combos())} valid setting/beat pairs:")
        for t in asp.atoms(model, "valid"):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.hero} and {p.friend} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
