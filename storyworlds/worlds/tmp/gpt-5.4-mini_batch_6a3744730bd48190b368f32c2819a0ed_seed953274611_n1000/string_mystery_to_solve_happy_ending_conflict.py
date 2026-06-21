#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/string_mystery_to_solve_happy_ending_conflict.py
=================================================================================

A small slice-of-life storyworld about a missing string mystery, a gentle family
conflict, and a happy ending.

Seed words:
- string

Features:
- Mystery to solve
- Conflict
- Happy ending

Style:
- Slice of life

The world is built around a household object that matters to a child: a string
from a sewing basket. A small misunderstanding turns into a mystery, the family
looks for clues, and the ending proves what changed by showing the string put to
a kind use.

The script follows the shared Storyweavers contract:
- typed entities with meters and memes
- generate / emit / main
- prompts, story-grounded QA, and world-knowledge QA
- Python reasonableness gate plus inline ASP twin
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class MysterySetting:
    id: str
    place: str
    nook: str
    clue_place: str
    evening_detail: str


@dataclass
class StringItem:
    id: str
    label: str
    phrase: str
    use: str
    is_missing: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictPlan:
    id: str
    concern: str
    accusation: str
    calm_fix: str
    resolution_image: str
    sense: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    string_item: str
    conflict: str
    seeker_name: str
    seeker_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out = []
    seeker = world.get("seeker")
    if seeker.memes["frustration"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["tension"] += 1
    world.get("parent").memes["concern"] += 1
    out.append("__conflict__")
    return out


RULES = [Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_at_risk(setting: MysterySetting, string_item: StringItem) -> bool:
    return string_item.is_missing and bool(setting.nook)


def sensible_conflicts() -> list[ConflictPlan]:
    return [c for c in CONFLICTS.values() if c.sense >= SENSE_MIN]


def best_conflict() -> ConflictPlan:
    return max(CONFLICTS.values(), key=lambda c: c.sense)


def clues_solve(world: World) -> bool:
    return world.get("string").meters["found"] >= THRESHOLD


def play_setup(world: World, seeker: Entity, helper: Entity, setting: MysterySetting) -> None:
    seeker.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"After lunch, {seeker.id} and {helper.id} were in {setting.place}, "
        f"where the day felt ordinary and calm."
    )
    world.say(
        f"They were looking near {setting.nook}, because something small had gone missing."
    )


def reveal_loss(world: World, seeker: Entity, string_item: StringItem) -> None:
    seeker.memes["unease"] += 1
    world.say(
        f'{seeker.id} frowned. "My {string_item.label} is gone," {seeker.pronoun()} said. '
        f'The missing {string_item.label} had turned into a little mystery.'
    )


def conflict_beat(world: World, seeker: Entity, helper: Entity, plan: ConflictPlan) -> None:
    seeker.memes["frustration"] += 1
    world.say(
        f'{seeker.id} wanted to solve it right away, but {helper.id} worried about the clue that '
        f"was sitting near the basket. {seeker.id} thought {plan.concern}."
    )
    world.say(
        f'"{plan.accusation}" {seeker.id} muttered, and the room felt tense for a moment.'
    )
    propagate(world, narrate=False)


def search_clues(world: World, seeker: Entity, helper: Entity, setting: MysterySetting,
                 string_item: StringItem) -> None:
    seeker.memes["curiosity"] += 1
    helper.memes["patience"] += 1
    world.say(
        f'They checked {setting.clue_place}, under a chair, and by the little basket. '
        f'{helper.id} noticed a short thread stuck to the table edge.'
    )
    world.say(
        f'That thread looked just like {string_item.phrase}, only tucked away where someone could '
        f'have left it by accident.'
    )


def solve_mystery(world: World, seeker: Entity, helper: Entity, parent: Entity,
                  string_item: StringItem, setting: MysterySetting) -> None:
    string_ent = world.get("string")
    string_ent.meters["found"] += 1
    string_ent.meters["untangled"] += 1
    seeker.memes["relief"] += 1
    helper.memes["relief"] += 1
    parent.memes["warmth"] += 1
    world.say(
        f'{helper.id} smiled. "It was never lost for long," {helper.id} said. '
        f'The clue led them to {parent.label_word}, who had borrowed the {string_item.label} '
        f"from the sewing basket."
    )
    world.say(
        f'{parent.label_word.capitalize()} held up the {string_item.label} and explained that it was '
        f'{string_item.use}. The mystery was solved, and the room felt lighter at once.'
    )
    world.say(
        f'Nobody had to keep guessing anymore. The little string was safe, and now everyone knew '
        f"where it belonged."
    )


def happy_fix(world: World, seeker: Entity, helper: Entity, parent: Entity,
              string_item: StringItem, plan: ConflictPlan) -> None:
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} tied the {string_item.label} neatly and used it for '
        f'{plan.calm_fix}.'
    )
    world.say(
        f'Then {seeker.id} and {helper.id} watched {plan.resolution_image}. '
        f'It was a small, happy ending that fit an ordinary day.'
    )


def tell(setting: MysterySetting, string_item: StringItem, plan: ConflictPlan,
         seeker_name: str = "Mina", seeker_gender: str = "girl",
         helper_name: str = "Jun", helper_gender: str = "boy",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    s = world.add(Entity(id="string", type="thing", label=string_item.label))
    world.facts["string_item"] = string_item
    world.facts["plan"] = plan
    world.facts["setting"] = setting

    play_setup(world, seeker, helper, setting)
    world.para()
    reveal_loss(world, seeker, string_item)
    conflict_beat(world, seeker, helper, plan)
    world.para()
    search_clues(world, seeker, helper, setting, string_item)
    solve_mystery(world, seeker, helper, parent, string_item, setting)
    world.para()
    happy_fix(world, seeker, helper, parent, string_item, plan)

    world.facts.update(
        seeker=seeker, helper=helper, parent=parent, string=s,
        solved=clues_solve(world),
        conflict=True,
    )
    return world


SETTINGS = {
    "sewing_room": MysterySetting(
        id="sewing_room",
        place="the sewing room",
        nook="the basket of folded cloth",
        clue_place="the big worktable",
        evening_detail="the lamp made a soft yellow circle on the floor",
    ),
    "kitchen": MysterySetting(
        id="kitchen",
        place="the kitchen",
        nook="the counter by the fruit bowl",
        clue_place="the chair by the fridge",
        evening_detail="the kettle was quiet and the window held the last light",
    ),
    "living_room": MysterySetting(
        id="living_room",
        place="the living room",
        nook="the side table by the couch",
        clue_place="the rug under the window",
        evening_detail="the room was cozy with a blanket and a small lamp",
    ),
}

STRINGS = {
    "red_string": StringItem(
        id="red_string",
        label="red string",
        phrase="a bright red string",
        use="for tying a little gift bag closed",
        tags={"string", "red"},
    ),
    "blue_string": StringItem(
        id="blue_string",
        label="blue string",
        phrase="a soft blue string",
        use="for mending a torn bookmark",
        tags={"string", "blue"},
    ),
    "twine": StringItem(
        id="twine",
        label="twine",
        phrase="a coil of twine",
        use="for hanging a little paper note",
        tags={"string", "twine"},
    ),
}

CONFLICTS = {
    "accusation": ConflictPlan(
        id="accusation",
        concern="the clue might be important",
        accusation="Maybe someone lost it on purpose?",
        calm_fix="tying up a package for the neighbor",
        resolution_image="the string looped neatly around a small brown parcel",
        sense=3,
        tags={"conflict", "mystery"},
    ),
    "mixup": ConflictPlan(
        id="mixup",
        concern="the string could belong to the basket",
        accusation="I thought you took it!",
        calm_fix="wrapping a loose notebook",
        resolution_image="the string holding a stack of papers together",
        sense=2,
        tags={"conflict", "mystery"},
    ),
    "careful": ConflictPlan(
        id="careful",
        concern="the basket looked odd without its thread",
        accusation="Did somebody hide it?",
        calm_fix="securing a handmade bookmark",
        resolution_image="the string tying a bookmark to a favorite book",
        sense=4,
        tags={"conflict", "mystery"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Ava"]
BOY_NAMES = ["Jun", "Owen", "Kai", "Leo", "Milo"]
PARENT_NAMES = ["Mom", "Dad"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for stid in STRINGS:
            for cid in CONFLICTS:
                if mystery_at_risk(SETTINGS[sid], STRINGS[stid]):
                    combos.append((sid, stid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life string mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--string", choices=STRINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.string is None or c[1] == args.string)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, string_item, conflict = rng.choice(sorted(combos))
    seeker_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if seeker_gender == "girl" else "girl"
    seeker_name = args.name or rng.choice(GIRL_NAMES if seeker_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != seeker_name])
    parent_gender = args.parent or rng.choice(["mother", "father"])
    parent_name = "Mom" if parent_gender == "mother" else "Dad"
    return StoryParams(
        setting=setting,
        string_item=string_item,
        conflict=conflict,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: StringItem = f["string_item"]
    return [
        f'Write a gentle slice-of-life story that includes the word "{s.label}" and turns a small household worry into a mystery that gets solved.',
        f"Tell a story where {f['seeker'].id} and {f['helper'].id} disagree about a missing {s.label}, then find out what happened and end happily.",
        f'Write a child-friendly story about a missing "{s.label}" in an everyday room, with a calm family ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker: Entity = f["seeker"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    string_item: StringItem = f["string_item"]
    setting: MysterySetting = f["setting"]
    plan: ConflictPlan = f["plan"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=(
                f"The mystery was where the {string_item.label} had gone. "
                f"It looked missing at first, so the children had to follow clues and solve it."
            ),
        ),
        QAItem(
            question="Why did the children argue a little?",
            answer=(
                f"{seeker.id} wanted to solve the problem right away, but {helper.id} wanted to be careful. "
                f"That made the room feel tense for a moment before they worked together."
            ),
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=(
                f"They checked {setting.clue_place} and found a clue near the basket. "
                f"Then {parent.label_word} explained where the {string_item.label} belonged, and the mystery was solved."
            ),
        ),
        QAItem(
            question="What changed by the end?",
            answer=(
                f"The {string_item.label} was no longer missing, and everyone knew its place. "
                f"{parent.label_word.capitalize()} used it for {plan.calm_fix}, so the story ended with a neat, happy picture."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    string_item: StringItem = f["string_item"]
    setting: MysterySetting = f["setting"]
    return [
        QAItem(
            question="What is string usually used for?",
            answer=(
                "String is a thin cord that people can use for tying, bundling, or making small crafts. "
                "It is helpful because it can hold things together without much weight."
            ),
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer=(
                "Clues help people figure out what happened when something is missing or confusing. "
                "One little clue can point to the right answer."
            ),
        ),
        QAItem(
            question="What kind of place was the story setting?",
            answer=(
                f"It was {setting.place}, an ordinary family place with everyday objects and a quiet corner. "
                "That made the mystery feel small and close to home."
            ),
        ),
        QAItem(
            question="Is a string a hard or soft object?",
            answer=(
                "A string is soft and bendy. It can twist and curl, which makes it easy to tie and wrap."
            ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.string_item not in STRINGS or params.conflict not in CONFLICTS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        STRINGS[params.string_item],
        CONFLICTS[params.conflict],
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_name=params.parent_name,
        parent_gender=params.parent_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, C) :- setting(S), string(T), conflict(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in STRINGS:
        lines.append(asp.fact("string", t))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
    StoryParams(
        setting="sewing_room",
        string_item="red_string",
        conflict="careful",
        seeker_name="Mina",
        seeker_gender="girl",
        helper_name="Jun",
        helper_gender="boy",
        parent_name="Mom",
        parent_gender="mother",
    ),
    StoryParams(
        setting="kitchen",
        string_item="blue_string",
        conflict="mixup",
        seeker_name="Owen",
        seeker_gender="boy",
        helper_name="Ivy",
        helper_gender="girl",
        parent_name="Dad",
        parent_gender="father",
    ),
    StoryParams(
        setting="living_room",
        string_item="twine",
        conflict="accusation",
        seeker_name="Lila",
        seeker_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        parent_name="Mom",
        parent_gender="mother",
    ),
]


def explain_rejection() -> str:
    return "(No story: this combination does not make a good mystery.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
