#!/usr/bin/env python3
"""
storyworlds/worlds/whistle_balance_reconciliation_fable.py
==========================================================

A small fable world about a lost balance, a whistle, and reconciliation.

Seed tale:
---
Two little neighbors lived beside a narrow bridge. One liked to hurry across with
a heavy basket, and the other liked to rush after it to keep up. Each time they
met in the middle, the bridge tipped and the basket slid. A wise owl blew a
small whistle, asked them to stop, and showed them how to take turns and share
the load. The neighbors laughed, forgave each other, and walked home in peace.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "owl"}
        male = {"boy", "father", "man"}
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
    intro: str


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    zone: set[str]


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name_a: str
    name_b: str
    guide: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "bridge": Setting(place="the narrow bridge", intro="The narrow bridge crossed a quiet stream."),
    "orchard": Setting(place="the orchard path", intro="The orchard path ran between low trees and ripe fruit."),
    "meadow": Setting(place="the meadow lane", intro="The meadow lane bent through grass that swayed like a green wave."),
}

ACTIVITIES = {
    "cross": Activity(
        id="cross",
        verb="cross the bridge with a heavy basket",
        gerund="crossing with a heavy basket",
        rush="rush to the middle of the bridge",
        mess="tilt",
        soil="off balance",
        keyword="balance",
        zone={"middle"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry apples at once",
        gerund="carrying apples",
        rush="hurry forward together",
        mess="tilt",
        soil="tipping over",
        keyword="balance",
        zone={"middle"},
    ),
}

PRIZES = {
    "basket": Prize(label="basket", phrase="a woven basket of apples", region="middle", plural=False),
    "crate": Prize(label="crate", phrase="a small crate of pears", region="middle", plural=False),
}

GUIDES = {
    "owl": {
        "type": "owl",
        "label": "wise owl",
        "voice": "soft",
        "tool": "a little whistle",
    },
    "heron": {
        "type": "heron",
        "label": "tall heron",
        "voice": "clear",
        "tool": "a bright whistle",
    },
}

NAMES_A = ["Milo", "Tess", "Roo", "Pip", "Nina", "Bea"]
NAMES_B = ["Otto", "June", "Lena", "Koa", "Ivy", "Sol"]
TRAITS = ["restless", "proud", "quick", "steady", "fidgety", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for p in SETTINGS for a in ACTIVITIES for pr in PRIZES]


def _do_activity(world: World, a: Entity, b: Entity, act: Activity, prize: Entity) -> None:
    a.meters[act.mess] = a.m(act.mess) + 1
    b.meters[act.mess] = b.m(act.mess) + 1
    prize.meters["tilt"] = prize.m("tilt") + 1
    a.memes["strain"] = a.e("strain") + 1
    b.memes["strain"] = b.e("strain") + 1
    if prize.m("tilt") >= THRESHOLD:
        world.facts["tilting"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name_a: str, name_b: str,
         guide_key: str, trait_a: str, trait_b: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=name_a, kind="character", type="fox", traits=["little", trait_a]))
    b = world.add(Entity(id=name_b, kind="character", type="goat", traits=["little", trait_b]))
    guide_def = GUIDES[guide_key]
    guide = world.add(Entity(
        id="Guide", kind="character", type=guide_def["type"], label=guide_def["label"]
    ))
    whistle = world.add(Entity(
        id="Whistle", type="whistle", label="whistle", phrase=guide_def["tool"], owner=guide.id
    ))
    prize = world.add(Entity(
        id="Prize", type="basket", label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=a.id, caretaker=guide.id
    ))

    world.say(f"{a.id} and {b.id} were two little neighbors near {setting.place}.")
    world.say(f"{a.id} was a {trait_a} fox, and {b.id} was a {trait_b} goat.")
    world.say(f"They wanted to {activity.verb}, and they both cared about {prize.phrase}.")
    world.say(setting.intro)

    world.para()
    world.say(f"One day, they tried to {activity.verb} at the same time.")
    _do_activity(world, a, b, activity, prize)
    world.say(f"The bridge trembled, and the basket tipped so much that everyone felt it.")
    world.say(f"{a.id} frowned because {a.pronoun('possessive')} feet slipped out of {a.pronoun('possessive')} rhythm.")
    world.say(f"{b.id} frowned too, because {b.pronoun('possessive')} hurry made the load worse.")

    world.para()
    world.say(f"Then the {guide_def['label']} lifted {guide.pronoun('possessive')} {whistle.label} and blew a clear note.")
    world.say(f"The sound said, 'Stop, breathe, and find your balance.'")
    guide.memes["concern"] = guide.e("concern") + 1
    a.memes["surprise"] = a.e("surprise") + 1
    b.memes["surprise"] = b.e("surprise") + 1

    world.say(f"{a.id} and {b.id} listened.")
    a.memes["humble"] = a.e("humble") + 1
    b.memes["humble"] = b.e("humble") + 1
    a.memes["kindness"] = a.e("kindness") + 1
    b.memes["kindness"] = b.e("kindness") + 1

    world.say(f"They took turns, one step at a time, and held the basket between them.")
    prize.meters["tilt"] = 0.0
    a.meters["balance"] = a.m("balance") + 1
    b.meters["balance"] = b.m("balance") + 1

    world.para()
    a.memes["reconciliation"] = a.e("reconciliation") + 1
    b.memes["reconciliation"] = b.e("reconciliation") + 1
    world.say(f"{a.id} smiled at {b.id} and said sorry for rushing.")
    world.say(f"{b.id} smiled back and said sorry for hurrying along without thinking.")
    world.say(f"The two neighbors laughed, shared the basket, and crossed safely together.")
    world.say(f"After that, the bridge felt steady, and the whistle stayed quiet in the owl's feathers.")

    world.facts.update(
        a=a, b=b, guide=guide, whistle=whistle, prize=prize, activity=activity,
        setting=setting, reconciled=True, balanced=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, act, place = f["a"], f["b"], f["activity"], f["setting"].place
    return [
        f"Write a short fable about two neighbors at {place} who learn balance after a whistle sounds.",
        f"Tell a child-friendly story where {a.id} and {b.id} stop quarrelling and reconcile over {act.keyword}.",
        f"Make a gentle fable about a wise guide, a whistle, and two friends who find balance together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, guide, act, prize = f["a"], f["b"], f["guide"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"Who were the two neighbors in the story?",
            answer=f"The two neighbors were {a.id}, a little fox, and {b.id}, a little goat.",
        ),
        QAItem(
            question=f"What made the neighbors stop and listen?",
            answer=f"The wise {guide.type} blew a whistle, and the clear note told them to stop and find their balance.",
        ),
        QAItem(
            question=f"What went wrong when they tried to {act.verb} at the same time?",
            answer=f"The bridge tipped, the basket wobbled, and both neighbors felt off balance.",
        ),
        QAItem(
            question=f"How did the neighbors fix the problem?",
            answer=f"They took turns, held the load together, and crossed one step at a time so the basket stayed steady.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The neighbors reconciled, apologized, and walked across the bridge in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whistle for?",
            answer="A whistle makes a sharp sound that can help someone get attention, signal a stop, or call people together.",
        ),
        QAItem(
            question="What does balance mean?",
            answer="Balance means staying steady so you do not tip or fall over.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who argued make peace again and become friendly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(Place, Act, Prize) :- setting(Place), activity(Act), prize(Prize).
reconciled_story(Place, Act, Prize) :- valid(Place, Act, Prize).
#show valid/3.
#show reconciled_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about whistle, balance, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
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
    guide = args.guide or rng.choice(list(GUIDES))
    name_a = args.name_a or rng.choice(NAMES_A)
    name_b = args.name_b or rng.choice([n for n in NAMES_B if n != name_a])
    trait_a = args.trait_a or rng.choice(TRAITS)
    trait_b = args.trait_b or rng.choice([t for t in TRAITS if t != trait_a])
    return StoryParams(place, activity, prize, name_a, name_b, guide, trait_a, trait_b)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name_a, params.name_b, params.guide, params.trait_a, params.trait_b)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_valid = sorted(set(asp.atoms(model, "valid")))
    py_valid = sorted(valid_combos())
    if asp_valid == py_valid:
        print(f"OK: clingo gate matches valid_combos() ({len(py_valid)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in asp:", sorted(set(asp_valid) - set(py_valid)))
    print(" only in py:", sorted(set(py_valid) - set(asp_valid)))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show reconciled_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show reconciled_story/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, activity, prize) in enumerate(valid_combos()):
            params = StoryParams(
                place=place,
                activity=activity,
                prize=prize,
                name_a=NAMES_A[i % len(NAMES_A)],
                name_b=NAMES_B[i % len(NAMES_B)],
                guide="owl" if i % 2 == 0 else "heron",
                trait_a=TRAITS[i % len(TRAITS)],
                trait_b=TRAITS[(i + 2) % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
