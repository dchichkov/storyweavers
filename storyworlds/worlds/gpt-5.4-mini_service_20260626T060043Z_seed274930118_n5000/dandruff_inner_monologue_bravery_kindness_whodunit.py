#!/usr/bin/env python3
"""
dandruff_inner_monologue_bravery_kindness_whodunit.py

A tiny whodunit-style story world about a missing object, a few suspects,
and a trail of clues that includes dandruff, inner monologue, bravery, and
kindness.

The world models a small cast in one setting. One item goes missing, a child
thinks through the mystery, acts bravely, and solves it kindly.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def display(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    witnesses: list[str] = field(default_factory=list)
    ambiance: str = ""


@dataclass
class Suspect:
    id: str
    role: str
    alibi: str
    clue: str
    guilt: int
    kind: str = "person"


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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    protagonist_name: str
    protagonist_gender: str
    missing_item: str
    suspect_pack: str
    seed: Optional[int] = None


SETTINGS = {
    "classroom": Setting(place="the classroom", witnesses=["teacher", "cat poster"], ambiance="quiet and bright"),
    "library": Setting(place="the library corner", witnesses=["librarian", "book cart"], ambiance="soft and hushy"),
    "hallway": Setting(place="the hallway", witnesses=["janitor", "shoe rack"], ambiance="long and echoing"),
}

PROTAGONISTS = {
    "girl": ["Maya", "Lena", "Ivy", "Nora", "Zoe"],
    "boy": ["Noah", "Eli", "Owen", "Finn", "Theo"],
}

MISSING_ITEMS = {
    "red_ribbon": ("red ribbon", "a bright red ribbon for the reading basket"),
    "blue_marble": ("blue marble", "a glassy blue marble in a tiny velvet bag"),
    "gold_key": ("gold key", "a small gold key with a star-shaped head"),
}

SUSPECTS = {
    "teacher": Suspect(
        id="teacher",
        role="teacher",
        alibi="the teacher was writing on the board the whole time",
        clue="chalk dust on both hands",
        guilt=0,
    ),
    "librarian": Suspect(
        id="librarian",
        role="librarian",
        alibi="the librarian was stamping returns near the desk",
        clue="ink on a finger",
        guilt=0,
    ),
    "custodian": Suspect(
        id="custodian",
        role="custodian",
        alibi="the custodian was mopping by the far door",
        clue="a wet mop trail",
        guilt=0,
    ),
    "friend": Suspect(
        id="friend",
        role="friend",
        alibi="the friend was building a tower of books",
        clue="a jacket sleeve lined with dandruff flakes",
        guilt=2,
    ),
}

PACKS = {
    "school": ["teacher", "librarian", "friend"],
    "quiet": ["librarian", "custodian", "friend"],
    "busy": ["teacher", "custodian", "friend"],
}

INSIDE_THE_MIND = [
    "Maybe the clue was tiny, but tiny clues still mattered.",
    "If she stayed calm, she could line up the facts one by one.",
    "A brave question could be kinder than a loud accusation.",
    "The flakes on the sleeve looked odd, like pale little snow bits.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for gender in PROTAGONISTS:
            for item in MISSING_ITEMS:
                combos.append((place, gender, item))
    return combos


def _choose_missing_suspect(pack: str) -> str:
    return PACKS[pack][2]


def _normal_guess(world: World, protagonist: Entity, missing: Entity, suspect_ids: list[str]) -> str:
    clues = [world.get(s).phrase for s in suspect_ids if s in world.entities]
    return f"{protagonist.display} noticed the clues and thought about them carefully."


def _solve_mystery(world: World, protagonist: Entity, missing: Entity, suspect_ids: list[str]) -> Entity:
    for sid in suspect_ids:
        suspect = world.get(sid)
        if suspect.meters.get("guilt", 0) >= THRESHOLD:
            return suspect
    return world.get(suspect_ids[0])


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    protagonist = world.add(Entity(
        id=params.protagonist_name,
        kind="character",
        type=params.protagonist_gender,
        label=params.protagonist_name,
    ))
    missing_label, missing_phrase = MISSING_ITEMS[params.missing_item]
    missing = world.add(Entity(
        id="missing_item",
        kind="thing",
        type="thing",
        label=missing_label,
        phrase=missing_phrase,
        owner=protagonist.id,
    ))
    suspect_ids = PACKS[params.suspect_pack]
    suspects = []
    for sid in suspect_ids:
        base = SUSPECTS[sid]
        ent = world.add(Entity(
            id=base.id,
            kind="character",
            type="person",
            label=base.role,
            phrase=base.clue,
        ))
        ent.meters["guilt"] = float(base.guilt)
        suspects.append(ent)

    culprit_id = _choose_missing_suspect(params.suspect_pack)
    world.facts.update(
        protagonist=protagonist,
        missing=missing,
        suspects=suspects,
        culprit_id=culprit_id,
        setting=setting,
        pack=params.suspect_pack,
    )

    world.say(f"In {setting.place}, {protagonist.display} found that {missing.phrase} was gone.")
    world.say(f"The room was {setting.ambiance}, and {', '.join(setting.witnesses)} seemed to watch the scene.")
    world.say(f"{protagonist.display} took a slow breath and listened to the quiet in her head.")
    world.say(random.choice(INSIDE_THE_MIND))
    world.para()

    world.say(f"First, {protagonist.display} checked the places where {missing.label} had last been seen.")
    world.say(f"Then {protagonist.display} looked at the suspects: {', '.join(s.label for s in suspects)}.")
    world.say(f"One clue stood out: {world.get(culprit_id).phrase}.")
    world.say(f"The clue on the {world.get(culprit_id).label}'s sleeve looked like dandruff flakes.")
    world.say(f"{protagonist.display} felt her heartbeat speed up, but she stood up bravely and asked a kind question.")

    culprit = world.get(culprit_id)
    culprit.memes["nervous"] = 1.0
    protagonist.memes["bravery"] = 1.0
    protagonist.memes["kindness"] = 1.0

    world.para()
    world.say(f'"Did you take it by mistake?" {protagonist.display} asked softly.')
    world.say(f"{culprit.label} blinked, looked down, and admitted the truth.")
    world.say(f"{culprit.label} had borrowed {missing.label} to use as a bookmark and forgot to bring it back.")
    world.say(f"{culprit.label} also had dandruff on the sleeve from a windy walk home, which had helped make the clue noticeable.")
    world.say(f"{protagonist.display} did not shout. She simply held out a hand and said they could fix it together.")
    world.say(f"Together they found {missing.label}, brushed it clean, and put it back where it belonged.")
    world.say(f"The room felt peaceful again, and {protagonist.display} smiled because the mystery was solved kindly.")

    return world


def _story_text(params: StoryParams) -> str:
    world = _build_world(params)
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    protagonist = f["protagonist"]
    missing = f["missing"]
    return [
        f"Write a short whodunit for children set in {f['setting'].place} about {protagonist.display} and a missing {missing.label}.",
        f"Tell a gentle mystery story where dandruff becomes an important clue and the hero uses bravery and kindness.",
        f"Write a small detective story with inner monologue, a surprising clue, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    protagonist = f["protagonist"]
    missing = f["missing"]
    culprit = world.get(f["culprit_id"])
    return [
        QAItem(
            question=f"What went missing in {f['setting'].place}?",
            answer=f"{protagonist.display} noticed that {missing.label} was missing from {f['setting'].place}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was {culprit.phrase}, which included dandruff flakes and pointed to the right suspect.",
        ),
        QAItem(
            question=f"How did {protagonist.display} act when the mystery got scary?",
            answer=f"{protagonist.display} stayed brave, listened to her inner thoughts, and asked a kind question instead of accusing anyone.",
        ),
        QAItem(
            question=f"Who was behind the missing item?",
            answer=f"{culprit.label} had taken {missing.label} by mistake and later admitted it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dandruff?",
            answer="Dandruff is tiny dry flakes from the scalp that can fall onto hair or clothes.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous or afraid.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle and caring with other people.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(M) :- item(M), chosen(M).
guilty(S) :- suspect(S), clue(S, dandruff), not innocent(S).
solve(M, S) :- missing(M), suspect(S), guilty(S).
kindly_solved(M) :- solve(M, S), brave(hero), kind(hero).
#show solve/2.
#show kindly_solved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for gender in PROTAGONISTS:
        lines.append(asp.fact("gender", gender))
    for item in MISSING_ITEMS:
        lines.append(asp.fact("item", item))
    for pack, ids in PACKS.items():
        lines.append(asp.fact("pack", pack))
        for sid in ids:
            lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("clue", "friend", "dandruff"))
    lines.append(asp.fact("brave", "hero"))
    lines.append(asp.fact("kind", "hero"))
    for m in MISSING_ITEMS:
        lines.append(asp.fact("chosen", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solve/2. #show kindly_solved/1."))
    atoms = set(str(a) for a in model)
    if not atoms:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP program is runnable.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small dandruff whodunit story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=PROTAGONISTS)
    ap.add_argument("--name")
    ap.add_argument("--missing-item", choices=MISSING_ITEMS, dest="missing_item")
    ap.add_argument("--suspect-pack", choices=PACKS, dest="suspect_pack")
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
    gender = args.gender or rng.choice(list(PROTAGONISTS))
    if args.name:
        name = args.name
    else:
        name = rng.choice(PROTAGONISTS[gender])
    missing_item = args.missing_item or rng.choice(list(MISSING_ITEMS))
    suspect_pack = args.suspect_pack or rng.choice(list(PACKS))
    return StoryParams(
        place=place,
        protagonist_name=name,
        protagonist_gender=gender,
        missing_item=missing_item,
        suspect_pack=suspect_pack,
    )


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams(place="classroom", protagonist_name="Maya", protagonist_gender="girl", missing_item="red_ribbon", suspect_pack="school"),
    StoryParams(place="library", protagonist_name="Noah", protagonist_gender="boy", missing_item="blue_marble", suspect_pack="quiet"),
    StoryParams(place="hallway", protagonist_name="Ivy", protagonist_gender="girl", missing_item="gold_key", suspect_pack="busy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solve/2. #show kindly_solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solve/2. #show kindly_solved/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
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
