#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/doctor_bravery_quest_mystery.py
==============================================================================================================

A standalone storyworld for a small mystery tale about a doctor on a brave quest.
The story stays child-facing and grounded in a tiny simulated world: a clinic,
a puzzling problem, a careful search, and a resolution that proves what changed.

Seed premise:
- doctor
- Bravery
- Quest
- style: Mystery
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"doctor", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "doctor"}:
            # doctor is neutral in story text; choose they/them style
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the clinic"
    affordances: set[str] = field(default_factory=lambda: {"quest", "mystery"})


@dataclass
class Quest:
    id: str
    thing: str
    clue: str
    search_place: str
    danger: str
    outcome: str
    keyword: str = "quest"


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "clinic": Setting("the clinic", {"quest", "mystery"}),
    "ward": Setting("the ward", {"mystery"}),
    "night_clinic": Setting("the night clinic", {"quest", "mystery"}),
}

QUESTS = {
    "lost_stethoscope": Quest(
        id="lost_stethoscope",
        thing="stethoscope",
        clue="a tiny silver trail",
        search_place="the supply closet",
        danger="the dark hall",
        outcome="found it tucked inside a basket",
        keyword="quest",
    ),
    "missing_chart": Quest(
        id="missing_chart",
        thing="chart",
        clue="a paper corner under the desk",
        search_place="behind the water jug",
        danger="the quiet records room",
        outcome="found it under a stack of books",
        keyword="mystery",
    ),
    "lost_lantern": Quest(
        id="lost_lantern",
        thing="lantern",
        clue="a warm glow near the window",
        search_place="the windowsill",
        danger="the shadowy stair",
        outcome="found it hanging on a hook",
        keyword="bravery",
    ),
}

HERO_NAMES = ["Mira", "Noah", "Lina", "Theo", "Nora", "Eli"]
HELPERS = ["nurse", "helper", "friend", "assistant"]
ROLES = ["doctor"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            combos.append((s, q))
    return combos


def explain_rejection(setting: str, quest: str) -> str:
    return f"(No story: {setting} does not fit the {quest} mystery quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about a doctor on a brave quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.setting and args.quest:
        if (args.setting, args.quest) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.quest))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    setting, quest = rng.choice(combos)
    name = args.name or rng.choice(HERO_NAMES)
    role = args.role or "doctor"
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, quest=quest, name=name, role=role, helper=helper)


def _do_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(f"{hero.id} noticed something odd at {world.setting.place}.")
    world.say(f"There was a mystery: {quest.clue}.")
    world.say(f"{hero.pronoun('subject').capitalize()} followed the clue on a quiet quest toward {quest.search_place}.")
    hero.memes["quest"] = hero.memes.get("quest", 0.0) + 1.0


def tell(setting: Setting, quest: Quest, name: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="doctor"))
    side = world.add(Entity(id=helper, kind="character", type="helper"))
    item = world.add(Entity(id=quest.id, type="thing", label=quest.thing, phrase=f"the missing {quest.thing}"))
    world.facts.update(hero=hero, helper=side, item=item, quest=quest, setting=setting)

    world.say(f"{hero.id} was a doctor who liked to keep every room calm and tidy.")
    world.say(f"{hero.pronoun('subject').capitalize()} knew that a small mystery could make people worried, so {hero.pronoun('subject')} promised to help.")
    world.say(f"{helper.capitalize()} stayed near {hero.pronoun('possessive')} side, ready for a brave quest.")
    world.para()

    world.say(f"One evening, someone noticed that {quest.thing} had gone missing.")
    world.say(f"The only clue was {quest.clue}.")
    world.say(f"{hero.id} looked at the clue and took a slow breath.")
    world.say(f"{hero.pronoun('subject').capitalize()} was brave enough to search {quest.danger} even though it felt spooky.")
    world.para()

    _do_quest(world, hero, quest)
    world.say(f"At last, {hero.id} found {quest.outcome}.")
    world.say(f"The missing {quest.thing} was back where it belonged, and the worry in the clinic melted away.")
    world.say(f"{helper.capitalize()} smiled, and {hero.id} felt proud of a brave mystery solved well.")

    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], params.name, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child about a {f["hero"].type} named {f["hero"].id} on a brave quest.',
        f"Tell a gentle clinic mystery where {f['hero'].id} searches for a missing {f['item'].label} with help from {f['helper'].id}.",
        f"Write a simple story with clues, courage, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a doctor who takes on a brave mystery quest.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was a {quest.thing}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} start the search?",
            answer=f"The clue was {quest.clue}. That clue led {hero.id} toward the place where the {quest.thing} was found.",
        ),
        QAItem(
            question=f"Who helped {hero.id} during the quest?",
            answer=f"{helper.id} stayed close and helped {hero.id} stay calm while the search went on.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery was solved when the missing {quest.thing} was found, and the worry disappeared.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a doctor do?",
            answer="A doctor helps people feel better, checks what is wrong, and tries to keep everyone safe.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or hard even when you feel nervous.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something important or solve a problem.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you have to investigate to understand.",
        ),
    ]


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S,Q) :- setting(S), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asv = set(asp_valid_combos())
    if py == asv:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asv:
        print("  only in python:", sorted(py - asv))
    if asv - py:
        print("  only in clingo:", sorted(asv - py))
    return 1


CURATED = [
    StoryParams(setting="clinic", quest="lost_stethoscope", name="Mira", role="doctor", helper="nurse"),
    StoryParams(setting="night_clinic", quest="missing_chart", name="Theo", role="doctor", helper="assistant"),
    StoryParams(setting="ward", quest="lost_lantern", name="Lina", role="doctor", helper="friend"),
]


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, q in combos:
            print(f"  {s:12} {q}")
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
