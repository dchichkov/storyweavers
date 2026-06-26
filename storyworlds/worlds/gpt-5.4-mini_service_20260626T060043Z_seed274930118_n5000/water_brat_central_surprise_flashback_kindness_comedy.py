#!/usr/bin/env python3
"""
water_brat_central_surprise_flashback_kindness_comedy.py
========================================================

A small story world about a bratty child, a central water place, a surprising
flashback, and a kindness-based comedy turn.

The premise:
- A child wants to play with water in the town's central fountain.
- A nearby grown-up worries about a favorite outfit and some slippery stones.
- The child acts bratty, the situation gets noisy and funny, and then a
  flashback reminds everyone why kindness matters.
- The ending resolves with a gentler plan and a comic final image.

This file is self-contained and follows the Storyweavers storyworld contract.
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
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "messy": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "bratty": 0.0, "surprise": 0.0, "kindness": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    central_feature: str
    affordance: str


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    comedy: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Comfort:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_done = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.flashback_done = self.flashback_done
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_wet_and_messy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["messy"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            sig = ("wet_item", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["messy"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got splashed and looked sillier by the second.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["bratty"] >= THRESHOLD and actor.memes["kindness"] < THRESHOLD:
            sig = ("conflict", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["conflict"] += 1
            out.append(f"{actor.id} crossed {actor.pronoun('possessive')} arms and made a face that could curdle lemonade.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("trigger_flashback") and not world.flashback_done:
        kid = world.get(world.facts["kid"])
        sig = ("flashback", kid.id)
        if sig not in world.fired:
            world.fired.add(sig)
            kid.memes["surprise"] += 1
            world.flashback_done = True
            out.append(
                f"Then a tiny flashback popped into {kid.id}'s head: last week, {kid.pronoun('possessive')} {world.facts['helper_label']} had shared a towel after a spill and laughed instead of scolding."
            )
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("resolved"):
        return out
    kid = world.get(world.facts["kid"])
    helper = world.get(world.facts["helper"])
    sig = ("kindness", kid.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["kindness"] += 1
    kid.memes["conflict"] = 0
    helper.memes["kindness"] += 1
    out.append(f"{kid.id} remembered to be kind first, and {helper.id} smiled as if the whole fountain had learned manners.")
    return out


RULES = [
    Rule("wet_and_messy", _r_wet_and_messy),
    Rule("conflict", _r_conflict),
    Rule("surprise", _r_surprise),
    Rule("kindness", _r_kindness),
]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "central_fountain": Setting(
        place="the central square",
        central_feature="a round fountain in the center",
        affordance="splashing water",
    ),
    "community_park": Setting(
        place="the community park",
        central_feature="a little water play pad near the middle",
        affordance="jumping in water",
    ),
}

ACTIVITIES = {
    "fountain_splash": Activity(
        id="fountain_splash",
        verb="splash in the fountain",
        gerund="splashing in the fountain",
        rush="run toward the fountain",
        mess="wet",
        zone={"feet", "legs", "torso"},
        keyword="water",
        comedy="the water bounced off every stone like it was telling jokes",
    ),
    "water_game": Activity(
        id="water_game",
        verb="play the water game",
        gerund="playing the water game",
        rush="dash to the spray",
        mess="wet",
        zone={"feet", "legs"},
        keyword="water",
        comedy="the spray tickled noses and made everyone snort-laugh",
    ),
}

PRIZES = {
    "red_shoes": Prize(
        label="shoes",
        phrase="bright red shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "blue_shirt": Prize(
        label="shirt",
        phrase="a neat blue shirt",
        type="shirt",
        region="torso",
    ),
}

COMFORTS = {
    "rainboots": Comfort(
        id="rainboots",
        label="rain boots",
        covers={"feet"},
        prep="put on the rain boots first",
        tail="walked back to the bench for the rain boots",
        plural=True,
    ),
    "old_towel": Comfort(
        id="old_towel",
        label="an old towel cape",
        covers={"torso"},
        prep="wrap on an old towel cape",
        tail="found the old towel cape",
    ),
}

NAMES = ["Milo", "Nina", "Ollie", "Pia", "Toby", "Lina"]
PARENTS = ["mother", "father", "aunt", "uncle"]


# ---------------------------------------------------------------------------
# World story
# ---------------------------------------------------------------------------

def make_world(setting: Setting, activity: Activity, prize: Prize, name: str, parent_type: str) -> World:
    world = World(setting)
    kid = world.add(Entity(id=name, kind="character", type="boy" if name in {"Milo", "Ollie", "Toby"} else "girl"))
    helper = world.add(Entity(id="Helper", kind="character", type=parent_type, label="the grown-up"))
    item = world.add(Entity(id="Prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=kid.id, caretaker=helper.id, plural=prize.plural))
    helper2 = world.add(Entity(id="Friend", kind="character", type="girl", label="the friend"))

    world.say(f"{kid.id} lived near {setting.place}, where {setting.central_feature} sat right in the middle like it owned the whole neighborhood.")
    world.say(f"{kid.id} was a bit of a brat about {activity.keyword}, because {activity.comedy}.")
    world.say(f"One morning, {helper.id} bought {kid.pronoun('object')} {prize.phrase}, and {kid.id} loved {prize.it()} immediately.")
    world.say(f"{kid.id} wore {prize.it()} everywhere and strutted around as if {prize.it()} were a royal treasure.")

    world.para()
    world.say(f"At the central square, {kid.id} stared at {setting.central_feature} and wanted to {activity.verb}.")
    world.say(f"{helper.id} pointed at the shirt-shiny stones and said, 'Easy there. Water and {prize.label} are not best friends.'")
    kid.memes["bratty"] += 1
    kid.meters["wet"] += 1
    world.say(f"{kid.id} huffed, {activity.rush}, and stomped so hard that even a pigeon looked offended.")
    propagate(world)

    world.para()
    world.facts.update(
        kid=kid.id,
        helper=helper.id,
        helper_label=helper.label,
        prize=item.id,
        activity=activity,
        setting=setting,
        trigger_flashback=True,
    )
    world.say(f"Then came the surprise: a tiny flashback to the day {helper.id} had helped clean up a spill without teasing anyone.")
    propagate(world)
    world.say(f"The memory softened {kid.id}'s face, because kindness can sneak up on a brat like a joke with a punchline.")
    world.facts["resolved"] = True
    propagate(world)
    world.say(f"{kid.id} apologized, and {helper.id} laughed so hard they nearly tipped into the fountain.")
    world.say(f"In the end, {kid.id} played the water game from the safe edge, {prize.label} stayed mostly dry, and the whole square looked like it had gotten away with being silly.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedy story for a child about water, a bratty mood, and a surprise memory that leads to kindness.',
        f"Tell a funny story where {f['kid']} wants to {f['activity'].verb} at {f['setting'].place} but worries about {f['helper_label']} and {f['prize']}.",
        "Make the ending gentle, with a flashback that changes the child from rude to kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = world.get(f["kid"])
    helper = world.get(f["helper"])
    prize = world.get(f["prize"])
    activity = f["activity"]
    return [
        QAItem(
            question=f"Where did {kid.id} want to {activity.verb}?",
            answer=f"{kid.id} wanted to {activity.verb} at {f['setting'].place}, right by {f['setting'].central_feature}.",
        ),
        QAItem(
            question=f"Why was {kid.id} acting like a brat?",
            answer=f"{kid.id} was acting bratty because {activity.keyword} was exciting and the water looked too tempting to ignore.",
        ),
        QAItem(
            question=f"What did the grown-up worry would happen to the {prize.label}?",
            answer=f"The grown-up worried the {prize.label} would get wet and messy if {kid.id} splashed too close to the fountain.",
        ),
        QAItem(
            question="What surprising memory changed the mood?",
            answer=f"{kid.id} remembered a flashback where {helper.id} had been kind after a spill, which made {kid.id} want to be gentler too.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {kid.id} choosing a safer way to play near the water and everyone laughing at the silly, splashy scene.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "water": (
        "What is water?",
        "Water is a clear liquid people drink, wash with, and splash in when it is time to play.",
    ),
    "brat": (
        "What does it mean to act like a brat?",
        "A bratty person is being rude or refusing to listen, often because they want their own way right away.",
    ),
    "central": (
        "What does central mean?",
        "Central means in the middle or most important place, like the center of a square or room.",
    ),
    "surprise": (
        "What is a surprise?",
        "A surprise is something you did not expect, so it pops up and makes you react fast.",
    ),
    "flashback": (
        "What is a flashback?",
        "A flashback is a quick memory that shows something from earlier, like a little scene in your mind.",
    ),
    "kindness": (
        "What is kindness?",
        "Kindness means being gentle, helpful, and caring toward someone else.",
    ),
    "comedy": (
        "What is comedy?",
        "Comedy is a kind of story or show that is meant to be funny and make people laugh.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["water", "brat", "central", "surprise", "flashback", "kindness", "comedy"]:
        q, a = WORLD_KNOWLEDGE[key]
        out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region := getattr(e, "region", ""):
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
kind_of_water(water).
kind_of_story(comedy).
kind_of_story(flashback).
kind_of_story(kindness).
kind_of_story(surprise).

central_place(P) :- place(P), central_feature(P,_).
at_risk(P, I) :- activity(A), setting(S), item(I), splashes(A,R), worn_on(I,R), affords(S,A), place(S,P).
compatible_fix(C, A, I) :- comfort(C), at_risk(_, I), covers(C, R), worn_on(I, R), activity(A), mess(A, wet).

valid_story(S, A, P) :- setting(S), activity(A), prize(P), affords(S,A), at_risk(S,P), has_fix(A,P).
has_fix(A,P) :- compatible_fix(_,A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("central_feature", sid, s.central_feature))
        lines.append(asp.fact("affords", sid, "fountain_splash" if sid == "central_fountain" else "water_game"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("item", pid))
        for r in [p.region]:
            lines.append(asp.fact("worn_on", pid, r))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", cid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Python gate is intentionally simple and mirrored by ASP through registry facts.
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP and Python agree on {len(python_set)} valid story combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(python_set - asp_set))
    print("asp:", sorted(asp_set - python_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for aid in ACTIVITIES:
            if sid == "central_fountain" or aid == "water_game":
                for pid in PRIZES:
                    combos.append((sid, aid, pid))
    return combos


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy storyworld about water, bratty behavior, surprise, flashback, and kindness.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = make_world(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_stories())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("central_fountain", "fountain_splash", "red_shoes", "Milo", "mother"),
            StoryParams("community_park", "water_game", "blue_shirt", "Nina", "father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
