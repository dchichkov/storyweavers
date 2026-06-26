#!/usr/bin/env python3
"""
Story world: a bedtime cautionary quest in a parking lot, built from the seed
words "noodle" and "whimper".

A small child finds a dropped noodle box in a parking lot after dusk and wants
to carry it home. A gentle grown-up worries: parking lots are not for wandering,
and a slippery noodle can spill, attract trouble, or get stepped on. The child
starts to whimper, then the grown-up turns the moment into a quiet quest: find
the owner, keep to the curb, and use a lantern and a little cart so nothing gets
lost or squashed. The story ends with the noodle safely returned and the child
snug, ready for bedtime.
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the parking lot"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "child"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


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


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "parking_lot": Setting(place="the parking lot", affords={"noodle_quest"}),
}

QUESTS = {
    "noodle_quest": Quest(
        id="noodle_quest",
        verb="follow the noodle trail",
        gerund="following the noodle trail",
        rush="run toward the shiny noodle box",
        risk="the noodle might get spilled or stepped on",
        weather="twilight",
        keyword="noodle",
        tags={"noodle", "quest", "cautionary"},
    )
}

PRIZES = {
    "noodle": Prize(
        label="noodle",
        phrase="a warm noodle cup",
        type="noodle",
        owner_kind="child",
    )
}

GEAR = {
    "lantern": Gear(
        id="lantern",
        label="a little lantern",
        prep="take a little lantern and walk by the curb",
        tail="walked slowly by the curb with the lantern glowing",
        guards={"dark"},
    ),
    "cart": Gear(
        id="cart",
        label="a small cart",
        prep="put the noodle cup in a small cart",
        tail="rolled the cart carefully toward the office",
        guards={"spill"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Maya", "Ella"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Finn", "Noah"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime cautionary quest in a parking lot.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--quest", choices=list(QUESTS))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for q in setting.affords:
            for prize in PRIZES:
                out.append((place, q, prize))
    return out


def explain_rejection() -> str:
    return "(No story: this bedtime quest only works in a parking lot with a noodle.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("(No story: unknown place.)")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("(No story: unknown quest.)")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("(No story: unknown prize.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())

    place, quest, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    noodle = world.add(Entity(id="noodle", type="noodle", label="noodle", phrase="a noodle cup", owner=hero.id, caretaker=parent.id))

    hero.memes["love"] = 1
    world.say(f"{hero.id} was a little {params.trait} {hero.type} who loved bedtime stories and quiet quests.")
    world.say(f"{hero.id} loved {quest.gerund}, especially when a noodle was involved.")
    world.say(f"One evening, {params.parent if params.parent else 'a grown-up'} found {hero.id} near {world.setting.place} with {prize.phrase}.")

    world.para()
    world.say(f"The lights were small and gold over {world.setting.place}.")
    world.say(f"{hero.id} wanted to {quest.verb}, but {hero.pronoun('possessive')} {params.parent} gave a careful warning: \"The parking lot is not a place to race.\"")
    hero.memes["whimper"] = 1
    world.say(f"{hero.id} let out a tiny whimper, because the noodle cup was tempting and the way back looked long.")

    world.para()
    world.say(f"Then the day turned into a gentle quest.")
    world.say(f"{params.parent.capitalize()} said, \"We can still help the noodle safely.\"")
    world.say(f"They took {GEAR['lantern'].label} and {GEAR['cart'].label}; the lantern made a soft moon of light, and the cart kept the noodle steady.")
    world.say(f"{hero.id} stopped rushing and walked by the curb, while {params.parent} watched for puddles and cars.")
    world.say(f"At the office door, they found the noodle's owner waiting and worried.")

    world.para()
    noodle.owner = "Owner"
    world.add(Entity(id="Owner", kind="character", type="adult", label="the owner"))
    world.say(f"{hero.id} gave the noodle back.")
    world.say(f"The owner smiled, and the parking lot felt calm again.")
    world.say(f"{hero.id} yawned, snuggled close, and went home ready for bedtime.")
    world.say(f"The little whimper was gone, and the noodle had found its way home.")

    world.facts.update(hero=hero, parent=parent, quest=quest, prize=prize, noodle=noodle, setting=world.setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a bedtime story about {hero.id} and a noodle in {world.setting.place}.',
        f'Write a cautionary quest where a child wants to {quest.verb} but learns to stay safe in a parking lot.',
        f'Tell a gentle story that includes "noodle" and "whimper" and ends quietly at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {quest.verb}, but the grown-up said to be careful in the parking lot.",
        ),
        QAItem(
            question=f"Why did {hero.id} whimper?",
            answer=f"{hero.id} whimpers because the noodle cup looked tempting and the parking lot felt risky at twilight.",
        ),
        QAItem(
            question=f"How did {parent.id} help make the quest safe?",
            answer=f"{parent.id} used a little lantern and a small cart, then walked by the curb so the noodle could be carried safely.",
        ),
        QAItem(
            question=f"What happened to the noodle at the end?",
            answer="The noodle was returned to its owner, so nothing got spilled or stepped on.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parking lot for?",
            answer="A parking lot is a place where cars are parked so people can leave them safely for a while.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off a soft light so people can see in the dark.",
        ),
        QAItem(
            question="Why should people walk carefully near cars?",
            answer="People should walk carefully near cars because moving cars can be dangerous if someone runs out suddenly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place,quest,prize) :- setting(place), affords(place,quest), prize(prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
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
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="parking_lot", quest="noodle_quest", prize="noodle", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="parking_lot", quest="noodle_quest", prize="noodle", name="Theo", gender="boy", parent="father", trait="sleepy"),
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
