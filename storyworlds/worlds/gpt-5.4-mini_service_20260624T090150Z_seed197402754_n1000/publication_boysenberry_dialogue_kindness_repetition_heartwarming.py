#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/publication_boysenberry_dialogue_kindness_repetition_heartwarming.py
================================================================================================

A small heartwarming storyworld about a child, a boysenberry, and a tiny
publication. The emotional engine is dialogue, kindness, and repetition:
someone feels stuck, a kind helper repeats a gentle plan, and the child ends up
braver by the end.

Seed tale used to build the world model:
---
A child named Ada helped her grandmother make a little publication about
boysenberries for the neighborhood table. Ada loved the bright berries, but she
felt shy about reading the publication out loud. Her grandmother smiled, made
room on the table, and said, "We can do it one small line at a time." Ada
practiced the first line, then the second, and then the whole page. When the
neighbors arrived, Ada read the publication with a wobbling voice that grew
steadier with every repeated line. The room felt warm, and Ada ended the day
feeling proud and loved.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class HelperMove:
    id: str
    label: str
    offer: str
    tail: str
    repeat_line: str
    requires: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters.get("boysenberry_sticky", 0.0) < THRESHOLD:
            continue
        pub = world.entities.get("publication")
        if not pub or pub.meters.get("clean", 0.0) < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        pub.meters["smudged"] = pub.meters.get("smudged", 0.0) + 1
        pub.meters["clean"] = 0.0
        out.append(f"The publication got a little smudged by berry fingers.")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    grand = world.entities.get("grand")
    if not child or not grand:
        return out
    if child.memes.get("shy", 0.0) < THRESHOLD:
        return out
    if grand.memes.get("kindly_repeat", 0.0) < THRESHOLD:
        return out
    sig = ("brave", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1
    child.memes["shy"] = 0.0
    out.append(f"The child's voice grew steadier.")
    return out


RULES = [_r_spill, _r_brave]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        world.say(s)


def reasonableness_gate(setting: Setting, activity: Activity, prize: Prize) -> bool:
    return activity.id in setting.affords and prize.label == "publication"


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"prepare"}),
    "table": Setting(place="the neighborhood table", indoor=True, affords={"share"}),
    "porch": Setting(place="the porch", indoor=True, affords={"practice"}),
}

ACTIVITIES = {
    "practice": Activity(
        id="practice",
        verb="read the publication aloud",
        gerund="reading the publication aloud",
        rush="rush through the lines",
        mess="voice_wobble",
        soil="less steady",
        keyword="publication",
        tags={"publication", "dialogue"},
    ),
    "share": Activity(
        id="share",
        verb="share the publication",
        gerund="sharing the publication",
        rush="run to the table",
        mess="nervousness",
        soil="more nervous",
        keyword="boysenberry",
        tags={"publication", "boysenberry"},
    ),
    "prepare": Activity(
        id="prepare",
        verb="make the boysenberry publication",
        gerund="making the boysenberry publication",
        rush="hurry the pages together",
        mess="ink_smear",
        soil="smudged",
        keyword="boysenberry",
        tags={"publication", "boysenberry"},
    ),
}

PRIZES = {
    "publication": Prize(
        label="publication",
        phrase="a small boysenberry publication",
        type="publication",
    ),
}

MOVES = {
    "kind_repeat": HelperMove(
        id="kind_repeat",
        label="kind repeated encouragement",
        offer='We can do it one small line at a time.',
        tail="They tried the first line, then the second, and then the whole page.",
        repeat_line="one small line at a time",
        requires={"publication"},
    ),
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


GIRL_NAMES = ["Ada", "Mina", "Ivy", "Luna", "Nora", "Etta"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ezra", "Finn", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("kitchen", "prepare", "publication"), ("table", "share", "publication"), ("porch", "practice", "publication")]


def select_move(activity: Activity, prize: Prize) -> HelperMove:
    if prize.label != "publication":
        raise StoryError("This world only tells stories about a publication.")
    return MOVES["kind_repeat"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming publication-and-boysenberry storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or ("grandmother" if gender == "girl" else "grandfather")
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="grand", kind="character", type=params.helper, label=f"the {params.helper}"))
    publication = world.add(Entity(
        id="publication", kind="thing", type="publication", label="publication",
        phrase="a small boysenberry publication", owner=child.id, caretaker=helper.id
    ))
    publication.meters["clean"] = 1.0
    child.memes["shy"] = 1.0
    child.memes["warm"] = 0.0
    helper.memes["kindly_repeat"] = 0.0
    child.meters["boysenberry_sticky"] = 0.0

    act = ACTIVITIES[params.activity]
    move = select_move(act, PRIZES[params.prize])

    world.say(f"{params.name} helped {params.helper} make a little boysenberry publication.")
    world.say(f"{params.name} loved the sweet boysenberry pages, but {child.pronoun()} felt shy about speaking.")
    world.para()
    world.say(f"At {world.setting.place}, {params.name} wanted to {act.verb}, but the words felt wobbly.")
    world.say(f'The {params.helper} smiled and said, "{move.offer}"')
    helper.memes["kindly_repeat"] += 1
    child.memes["shy"] += 0.5
    world.say(f'{params.name} whispered, "{move.repeat_line}."')
    world.say(f'The {params.helper} answered, "{move.repeat_line}."')
    world.say(f'{params.name} tried again: "{move.repeat_line}."')
    child.meters["boysenberry_sticky"] += 1
    propagate(world)
    world.para()
    child.memes["warm"] = 1.0
    child.meters["boysenberry_sticky"] = 0.0
    publication.meters["clean"] = 1.0
    world.say(f"Then {params.name} took a breath and {act.gerund}.")
    world.say(f'The {params.helper} nodded kindly, and {move.tail}')
    world.say(f"By the end, the publication stayed neat, the boysenberry words sounded bright, and {params.name} smiled all the way home.")
    world.facts.update(child=child, helper=helper, publication=publication, act=act, move=move, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a heartwarming story about {p.name} and a boysenberry publication.',
        f"Tell a gentle tale where {p.name} feels shy, {p.helper} uses kind repetition, and the publication helps them speak bravely.",
        f'Write a short story that includes the words "publication" and "boysenberry" and ends with a warm, proud smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    child = f["child"]
    helper = f["helper"]
    act = f["act"]
    return [
        QAItem(
            question=f"What was {p.name} helping make?",
            answer=f"{p.name} was helping make a small boysenberry publication.",
        ),
        QAItem(
            question=f"How did {p.helper} help {p.name} feel braver?",
            answer=f"{p.helper.capitalize()} helped by saying the same kind line again and again: one small line at a time.",
        ),
        QAItem(
            question=f"What did {p.name} do after practicing the repeated line?",
            answer=f"{p.name} took a breath and {act.gerund}, and the voice grew steadier.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt warm, proud, and loved when the boysenberry publication stayed neat and the reading went well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a publication?",
            answer="A publication is something printed or shared for people to read, like a small book, flyer, or newspaper.",
        ),
        QAItem(
            question="What is a boysenberry?",
            answer="A boysenberry is a dark, sweet berry that can be eaten fresh or used in jams, pies, and other treats.",
        ),
        QAItem(
            question="Why is repeating a kind sentence helpful?",
            answer="Repeating a kind sentence can help someone remember the plan and feel calmer and braver.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place,activity,prize) :- setting(place), affords(place,activity), prize(prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="kitchen", activity="prepare", prize="publication", name="Ada", gender="girl", helper="grandmother"),
    StoryParams(place="table", activity="share", prize="publication", name="Owen", gender="boy", helper="grandfather"),
    StoryParams(place="porch", activity="practice", prize="publication", name="Mina", gender="girl", helper="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
