#!/usr/bin/env python3
"""
storyworlds/worlds/honey_dusty_moss_misty_path_shopping_mall.py
================================================================

A standalone storyworld for a seed prompt:

    Words: honey, dusty moss, misty path
    Setting: shopping mall
    Features: Inner Monologue, Bad Ending, Dialogue
    Style: Pirate Tale

Source tale, kept small on purpose:
In a shopping mall dressed up like a pirate harbor, a child carries honey
through a misty path attraction edged with dusty moss. A friend gives a clear
warning, but the child chooses a showy pirate shortcut instead. Honey spills,
the attraction is damaged, and the ending turns bad in a concrete way that
proves what changed in the mall.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class MallDeck:
    id: str
    mall_name: str
    pirate_area: str
    path_label: str
    mist_line: str
    moss_line: str
    feature: str
    feature_label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HoneyCargo:
    id: str
    label: str
    carry_line: str
    spill_line: str
    warning: str
    feature: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    action: str
    thought: str
    boast: str
    feature: str
    lure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class BadEnding:
    id: str
    feature: str
    crash_line: str
    closure_line: str
    image_line: str
    outcome: str
    outcome_label: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mall: str
    honey: str
    shortcut: str
    ending: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, mall: MallDeck) -> None:
        self.mall = mall
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
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
        clone = World(self.mall)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_honey_spills(world: World) -> list[str]:
    hero = world.get("hero")
    honey = world.get("honey")
    path = world.get("path")
    moss = world.get("moss")
    cargo: HoneyCargo = world.facts["honey_cfg"]
    if hero.memes["shortcut"] < THRESHOLD or honey.meters["spilled"] >= THRESHOLD:
        return []
    sig = ("spill", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    honey.meters["spilled"] += 1
    path.meters["sticky"] += 1
    moss.meters["sticky"] += 1
    return [cargo.spill_line]


def _r_warning_breaks(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["shortcut"] < THRESHOLD or friend.memes["warned"] < THRESHOLD:
        return []
    sig = ("warning_broken", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["shame"] += 1
    friend.memes["alarm"] += 1
    return []


def _r_bad_ending(world: World) -> list[str]:
    hero = world.get("hero")
    captain = world.get("captain")
    path = world.get("path")
    ending: BadEnding = world.facts["ending_cfg"]
    if path.meters["sticky"] < THRESHOLD or path.meters["closed"] >= THRESHOLD:
        return []
    sig = ("bad_ending", ending.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    path.meters["closed"] += 1
    hero.memes["regret"] += 2
    captain.memes["disappointed"] += 1
    return [
        ending.crash_line.format(hero=hero.id),
        f'"Belay that," said Captain {captain.id}. "{ending.closure_line}"',
    ]


CAUSAL_RULES = [
    Rule("honey_spills", "physical", _r_honey_spills),
    Rule("warning_breaks", "social", _r_warning_breaks),
    Rule("bad_ending", "closure", _r_bad_ending),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def python_reasonable(mall: MallDeck, honey: HoneyCargo, shortcut: Shortcut,
                      ending: BadEnding) -> tuple[bool, str]:
    if honey.feature != mall.feature:
        return (
            False,
            f"(No story: {mall.pirate_area} is built around {mall.feature_label}, "
            f"but {honey.id} spills on a different part of the display.)",
        )
    if shortcut.feature != mall.feature:
        return (
            False,
            f"(No story: {shortcut.id} needs {shortcut.feature}, but the chosen "
            f"misty path uses {mall.feature_label}.)",
        )
    if ending.feature != mall.feature:
        return (
            False,
            f"(No story: {ending.id} does not grow from the real hazard on this "
            f"misty path.)",
        )
    if shortcut.lure < 2:
        return (
            False,
            f"(No story: {shortcut.id} is not tempting enough to drive a bad ending.)",
        )
    return True, ""


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mall_id, mall in MALLS.items():
        for honey_id, honey in HONEY_CARGO.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                for ending_id, ending in BAD_ENDINGS.items():
                    ok, _ = python_reasonable(mall, honey, shortcut, ending)
                    if ok:
                        combos.append((mall_id, honey_id, shortcut_id, ending_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    return BAD_ENDINGS[params.ending].outcome


def introduce(world: World, hero: Entity, friend: Entity, captain: Entity,
              honey: HoneyCargo) -> None:
    mall = world.facts["mall_cfg"]
    world.say(
        f"In the {mall.mall_name} shopping mall, {hero.id} and {friend.id} liked "
        f"to call {mall.pirate_area} their indoor ship."
    )
    world.say(
        f"Their favorite stretch was {mall.path_label}. {mall.mist_line} {mall.moss_line}"
    )
    world.say(
        f'Captain {captain.id} handed {hero.id} {honey.carry_line} and said, "{honey.warning}"'
    )


def warning_scene(world: World, hero: Entity, friend: Entity, shortcut: Shortcut) -> None:
    friend.memes["warned"] += 1
    world.say(
        f'"Take the dry way," said {friend.id}. "That pirate trick with the '
        f'{world.facts["mall_cfg"].feature_label} is not for sticky hands."'
    )
    world.say(f"{shortcut.thought} {hero.id} thought.")
    world.say(f"{hero.id} whispered, {shortcut.boast}")


def mistake_scene(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["shortcut"] += 1
    hero.memes["pride"] += shortcut.lure
    world.say(f"Then {hero.id} {shortcut.action}.")
    propagate(world, narrate=True)


def ending_scene(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    ending: BadEnding = world.facts["ending_cfg"]
    if world.get("path").meters["closed"] < THRESHOLD:
        return
    world.say(
        f"{friend.id} reached for {hero.id}, but the game was already spoiled. "
        f"{hero.id} felt {hero.pronoun('possessive')} brave pirate grin sink away."
    )
    world.say(ending.image_line)


def tell(mall: MallDeck, honey: HoneyCargo, shortcut: Shortcut, ending: BadEnding,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         captain_name: str, trait: str) -> World:
    ok, why_not = python_reasonable(mall, honey, shortcut, ending)
    if not ok:
        raise StoryError(why_not)

    world = World(mall)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(friend_name, kind="character", type=friend_gender, role="friend"))
    captain = world.add(Entity(captain_name, kind="character", type="woman", role="captain"))
    path = world.add(Entity("path", type="path", label=mall.path_label))
    moss = world.add(Entity("moss", type="moss", label="dusty moss"))
    honey_ent = world.add(Entity("honey", type="honey", label=honey.label, owner=hero.id))
    hero.attrs["trait"] = trait
    friend.attrs["trait"] = "careful"
    world.facts.update({
        "mall_cfg": mall,
        "honey_cfg": honey,
        "shortcut_cfg": shortcut,
        "ending_cfg": ending,
        "trait": trait,
    })

    introduce(world, hero, friend, captain, honey)
    world.para()
    warning_scene(world, hero, friend, shortcut)
    mistake_scene(world, hero, shortcut)
    world.para()
    ending_scene(world)
    return world


MALLS = {
    "anchor_atrium": MallDeck(
        "anchor_atrium",
        "Seabell",
        "Captain Crate's Harbor Walk",
        "the misty path curling past fake rocks and blue lamps",
        "A little fog machine breathed soft white mist across the floor.",
        "A strip of dusty moss sat under the rocks like old seaweed left by a tiny tide.",
        "rail",
        "rope side rail",
        tags={"mall", "pirate", "mist", "moss"},
    ),
    "shell_square": MallDeck(
        "shell_square",
        "Moonbay",
        "The Honey Harbor Treasure Course",
        "the misty path painted with barrel stones and gull arrows",
        "Silver mist drifted from a fountain shaped like a whale tail.",
        "Dusty moss softened the edge of the path where the fake cliff met the tiles.",
        "barrel",
        "painted barrel stones",
        tags={"mall", "pirate", "mist", "moss"},
    ),
    "lantern_level": MallDeck(
        "lantern_level",
        "Harborlight",
        "Captain Lantern's Indoor Wharf",
        "the misty path leading to a toy bridge under paper sails",
        "Thin mall mist curled up from vents under the bridge and made the lights look moony.",
        "Dusty moss clung around the base of the bridge posts like sleepy green foam.",
        "wheel",
        "lookout wheel",
        tags={"mall", "pirate", "mist", "moss"},
    ),
}

HONEY_CARGO = {
    "glaze_cup": HoneyCargo(
        "glaze_cup",
        "a wobbling cup of honey glaze from the bun kiosk",
        "a wobbling cup of honey for the treasure stamp game",
        "The honey splashed over the rope side rail and slid into the dusty moss below.",
        "Carry this straight across the misty path and keep it off the rail.",
        "rail",
        tags={"honey", "spill", "rail"},
    ),
    "tea_tin": HoneyCargo(
        "tea_tin",
        "a warm tin of honey tea from the upper stall",
        "a warm tin of honey tea for the captain's stamp table",
        "The lid jumped, and honey tea washed across the painted barrel stones and into the dusty moss.",
        "Mind the barrel stones. Honey on that path turns fun into a mess.",
        "barrel",
        tags={"honey", "spill", "barrel"},
    ),
    "sample_jar": HoneyCargo(
        "sample_jar",
        "a squat jar of thick honey from the sample counter",
        "a squat jar of honey for the bridge prize shelf",
        "The jar slapped the lookout wheel, and a golden sheet of honey ran down to the dusty moss.",
        "Hold the jar low and never tug the wheel with a sticky hand.",
        "wheel",
        tags={"honey", "spill", "wheel"},
    ),
}

SHORTCUTS = {
    "swing_rail": Shortcut(
        "swing_rail",
        "swinging on the side rail",
        "hooked one arm around the rope rail and tried to swing past the safe tiles",
        '"If I swing once, I will look like the fastest pirate in the whole mall."',
        '"Stand back. A fast pirate never waits."',
        "rail",
        4,
        tags={"inner", "bad", "pirate"},
    ),
    "dash_barrels": Shortcut(
        "dash_barrels",
        "dashing over the barrel stones",
        "ran over the painted barrel stones instead of the dry stepping marks",
        '"If I dash over the barrels, I can win the stamp before anyone blinks."',
        '"I know a quicker deck than this one."',
        "barrel",
        4,
        tags={"inner", "bad", "pirate"},
    ),
    "spin_wheel": Shortcut(
        "spin_wheel",
        "spinning the lookout wheel",
        "grabbed the lookout wheel and spun it hard to hurry the bridge gate",
        '"If I spin the wheel myself, the bridge will obey me like a captain\'s ship."',
        '"A real captain does not shuffle. A real captain commands."',
        "wheel",
        3,
        tags={"inner", "bad", "pirate"},
    ),
}

BAD_ENDINGS = {
    "torn_banner": BadEnding(
        "torn_banner",
        "rail",
        "The rail turned slick at once, and {hero} skidded into the pirate banner until its corner tore free.",
        "The misty path is closed now. No child crosses it again until every sticky strand is scrubbed clean.",
        "At the end, the misty path stood empty behind a red cord, and honey-dark dusty moss clung to the fallen banner.",
        "closed_banner",
        "the banner tore and the path had to close",
        "Speed and showing off spoiled the whole game for everyone behind them.",
        tags={"bad_ending", "closure", "banner"},
    ),
    "lost_tokens": BadEnding(
        "lost_tokens",
        "barrel",
        "The barrel stones went slick, and {hero} slipped just enough to fling the treasure tokens into a gray cleaning bucket.",
        "The stamp game is over for today. We will not play pirate on a sticky deck.",
        "At the end, gold paper tokens floated in bucket water beside the misty path, and the dusty moss looked dark and gummy.",
        "lost_tokens",
        "the treasure tokens were lost and the game ended early",
        "A rushed victory can turn into a real loss when a child ignores the safe route.",
        tags={"bad_ending", "closure", "tokens"},
    ),
    "red_alarm": BadEnding(
        "red_alarm",
        "wheel",
        "The wheel flung honey into the little fog machine, and a red alarm light blinked over the toy bridge.",
        "Bridge game over. Sticky gears and mist do not mix.",
        "At the end, the wheel was still, the fake sea mist was gone, and a shiny patch of dusty moss glimmered under the mall lights.",
        "alarm_shutdown",
        "the bridge alarm shut the pirate game down",
        "Pretending to command everything made the whole pirate world stop working.",
        tags={"bad_ending", "closure", "alarm"},
    ),
}

GIRL_NAMES = ["Mara", "Nia", "Lily", "Poppy", "Tess", "Rina", "Mina", "Zoe"]
BOY_NAMES = ["Pip", "Finn", "Theo", "Sam", "Leo", "Noah", "Jory", "Ben"]
CAPTAINS = ["Mira", "Reed", "Sable", "Bram"]
TRAITS = ["eager", "proud", "bright", "restless", "curious", "bold"]

CURATED = [
    StoryParams("anchor_atrium", "glaze_cup", "swing_rail", "torn_banner",
                "Mara", "girl", "Finn", "boy", "Mira", "proud"),
    StoryParams("shell_square", "tea_tin", "dash_barrels", "lost_tokens",
                "Theo", "boy", "Nia", "girl", "Reed", "eager"),
    StoryParams("lantern_level", "sample_jar", "spin_wheel", "red_alarm",
                "Lily", "girl", "Sam", "boy", "Sable", "bold"),
]


KNOWLEDGE = {
    "honey": [(
        "Why can honey make a walking path dangerous?",
        "Honey is thick and sticky, but it can still make a smooth surface slippery. On a path, that means feet and hands can slide when a child expects grip."
    )],
    "moss": [(
        "What is moss?",
        "Moss is a small soft plant that grows low and close together. In stories and displays, it can hold dust, water, or sticky spills."
    )],
    "mist": [(
        "Why does mist make it harder to see a problem quickly?",
        "Mist softens edges and hides small changes on the floor or a rail. That can make a fresh spill look less obvious for a moment."
    )],
    "mall": [(
        "What is a shopping mall?",
        "A shopping mall is a large building with many stores and indoor walkways. It can also hold themed play areas or displays for children."
    )],
    "pirate": [(
        "What makes this story feel like a pirate tale?",
        "The children talk about captains, decks, rails, and treasure as if the mall were a ship. Pirate words turn an everyday place into an adventure world."
    )],
    "bad_ending": [(
        "What is a bad ending in a story?",
        "A bad ending is when a poor choice leads to a real loss instead of a happy fix. It should show a clear consequence, not just say someone felt sad."
    )],
}
KNOWLEDGE_ORDER = ["honey", "moss", "mist", "mall", "pirate", "bad_ending"]


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    mall: MallDeck = world.facts["mall_cfg"]
    honey: HoneyCargo = world.facts["honey_cfg"]
    shortcut: Shortcut = world.facts["shortcut_cfg"]
    ending: BadEnding = world.facts["ending_cfg"]
    return [
        'Write a TinyStories-style pirate tale in a shopping mall that includes the words "honey", "dusty moss", and "misty path", plus dialogue, inner monologue, and a bad ending.',
        f"Tell a child-facing story about {hero.id} in {mall.pirate_area}, where {honey.label} is carried through a misty path, {shortcut.label} looks tempting, and the ending goes badly in a concrete way.",
        f"Write a pirate-flavored mall story with a clear warning, a private thought, a sticky mistake, and a closing image that proves {ending.outcome_label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get("hero")
    friend = world.get("friend")
    captain = world.get("captain")
    mall: MallDeck = world.facts["mall_cfg"]
    honey: HoneyCargo = world.facts["honey_cfg"]
    shortcut: Shortcut = world.facts["shortcut_cfg"]
    ending: BadEnding = world.facts["ending_cfg"]
    return [
        (
            "Where does the story happen?",
            f"It happens in the {mall.mall_name} shopping mall, inside {mall.pirate_area}. The children treat the mall display like a little pirate harbor."
        ),
        (
            f"What was {hero.id} carrying?",
            f"{hero.id} was carrying {honey.carry_line}. That honey mattered because a sticky spill could ruin the misty path."
        ),
        (
            f"What warning did {friend.id} give?",
            f"{friend.id} told {hero.id} to take the dry way and leave the shortcut alone. The warning was about sticky hands and an unsafe pirate trick."
        ),
        (
            f"What was the inner monologue?",
            f"{hero.id} privately thought that the shortcut would make {hero.pronoun('object')} look like the fastest pirate in the mall. That boastful thought pushed the story toward its bad ending."
        ),
        (
            "Why did the accident happen?",
            f"The accident happened because {hero.id} chose {shortcut.label} while carrying honey. Once the honey hit the display and the dusty moss, the path turned too slick for play."
        ),
        (
            "What was the bad ending?",
            f"The bad ending was that {ending.outcome_label}. Captain {captain.id} shut the attraction because the sticky mess had made the pirate game unsafe."
        ),
        (
            "How did the story end?",
            f"It ended with a concrete picture of the damaged play area, not a quick apology that fixed everything. The final image showed the misty path closed and marked by honey-dark dusty moss."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mall", "pirate", "bad_ending"}
    for key in ("mall_cfg", "honey_cfg", "shortcut_cfg", "ending_cfg"):
        tags |= set(world.facts[key].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    seen: set[int] = set()
    for ent in world.entities.values():
        if id(ent) in seen:
            continue
        seen.add(id(ent))
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Mall, Honey, Shortcut, Ending) :-
    mall(Mall),
    mall_feature(Mall, Feature),
    honey_feature(Honey, Feature),
    shortcut_feature(Shortcut, Feature),
    ending_feature(Ending, Feature),
    shortcut_lure(Shortcut, L), L >= 2.

outcome(Outcome) :- chosen_ending(Ending), ending_outcome(Ending, Outcome).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mall_id, mall in MALLS.items():
        lines.append(asp.fact("mall", mall_id))
        lines.append(asp.fact("mall_feature", mall_id, mall.feature))
    for honey_id, honey in HONEY_CARGO.items():
        lines.append(asp.fact("honey", honey_id))
        lines.append(asp.fact("honey_feature", honey_id, honey.feature))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("shortcut_feature", shortcut_id, shortcut.feature))
        lines.append(asp.fact("shortcut_lure", shortcut_id, shortcut.lure))
    for ending_id, ending in BAD_ENDINGS.items():
        lines.append(asp.fact("ending", ending_id))
        lines.append(asp.fact("ending_feature", ending_id, ending.feature))
        lines.append(asp.fact("ending_outcome", ending_id, ending.outcome))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_ending", params.ending)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    empty = build_parser().parse_args([])
    for seed in range(80):
        try:
            cases.append(resolve_params(empty, random.Random(seed)))
        except StoryError:
            continue
    bad = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for params in bad[:5]:
            print(" ", params, asp_outcome(params), outcome_of(params))

    for params in CURATED:
        sample = generate(params)
        story = sample.story.lower()
        if "shopping mall" not in story:
            rc = 1
            print(f"MISMATCH: story for {params} does not name the shopping mall.")
        for needle in ("honey", "dusty moss", "misty path"):
            if needle not in story:
                rc = 1
                print(f"MISMATCH: story for {params} is missing '{needle}'.")
        if sample.world is None or sample.world.get("path").meters["closed"] < THRESHOLD:
            rc = 1
            print(f"MISMATCH: story for {params} did not reach its bad ending state.")
    if rc == 0:
        print("OK: curated stories keep the seed words, mall setting, and bad ending state.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a pirate-flavored shopping mall mistake with honey, dusty moss, and a misty path."
    )
    ap.add_argument("--mall", choices=MALLS)
    ap.add_argument("--honey", choices=HONEY_CARGO)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--ending", choices=BAD_ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mall and args.honey and args.shortcut and args.ending:
        ok, why_not = python_reasonable(
            MALLS[args.mall], HONEY_CARGO[args.honey], SHORTCUTS[args.shortcut], BAD_ENDINGS[args.ending]
        )
        if not ok:
            raise StoryError(why_not)

    combos = [
        combo for combo in valid_combos()
        if (args.mall is None or combo[0] == args.mall)
        and (args.honey is None or combo[1] == args.honey)
        and (args.shortcut is None or combo[2] == args.shortcut)
        and (args.ending is None or combo[3] == args.ending)
    ]
    if not combos:
        raise StoryError("(No valid mall, honey, shortcut, and ending combination matches the given options.)")

    mall_id, honey_id, shortcut_id, ending_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or _pick_name(rng, gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    captain = args.captain or rng.choice(CAPTAINS)
    return StoryParams(
        mall_id, honey_id, shortcut_id, ending_id, hero, gender,
        friend, friend_gender, captain, rng.choice(TRAITS)
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        MALLS[params.mall], HONEY_CARGO[params.honey], SHORTCUTS[params.shortcut],
        BAD_ENDINGS[params.ending], params.hero, params.hero_gender,
        params.friend, params.friend_gender, params.captain, params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mall, honey, shortcut, ending) combos:\n")
        for mall, honey, shortcut, ending in combos:
            print(f"  {mall:14} {honey:12} {shortcut:13} {ending}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 80, 80):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero}: {p.mall} / {p.honey} / {p.shortcut} / "
                f"{p.ending} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
