#!/usr/bin/env python3
"""
A small story world about a classic promenade mystery with rutabaga, teamwork,
friendship, and a happy ending.

A child and a friend notice a missing rutabaga at the promenade. They follow
little clues, ask careful questions, work together, and discover that the
rutabaga was not stolen at all — it was rolled away by a helpful cart and left
near a flower stand. The friends return it, calm the worried vendor, and end
the evening with a happy snack.

This world is intentionally tiny, state-driven, and constraint-checked.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "vendor"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the promenade"
    afford_mystery: bool = True


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    clue_word: str
    value_word: str


@dataclass
class Clue:
    id: str
    place: str
    text: str
    leads_to: str


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    friend_name: str
    vendor_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the promenade", afford_mystery=True)

OBJECTS = {
    "rutabaga": MysteryObject(
        id="rutabaga",
        label="rutabaga",
        phrase="a round purple rutabaga",
        clue_word="rutabaga",
        value_word="vegetable",
    ),
    "lantern": MysteryObject(
        id="lantern",
        label="lantern",
        phrase="a tiny brass lantern",
        clue_word="glow",
        value_word="light",
    ),
}

CLUES = [
    Clue(id="mud", place="near the bench", text="a muddy wheel mark", leads_to="flower_stall"),
    Clue(id="petal", place="by the flower stand", text="a purple petal stuck to a crate", leads_to="flower_stall"),
    Clue(id="coin", place="under a lamppost", text="a shiny coin beside a cart track", leads_to="cart"),
]

NAMES = ["Mia", "Nora", "Leo", "Finn", "Ava", "Eli", "Rose", "Maya"]
TRAITS = ["curious", "careful", "brave", "kind", "quiet", "clever"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def _add_meters(entity: Entity, key: str, value: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _add_memes(entity: Entity, key: str, value: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def investigate(world: World, hero: Entity, friend: Entity, vendor: Entity, obj: Entity) -> None:
    _add_memes(hero, "curiosity", 1)
    _add_memes(friend, "curiosity", 1)
    world.say(
        f"At the promenade, {hero.id} and {friend.id} noticed that {vendor.pronoun('possessive')} {obj.label} was missing."
    )
    world.say(
        f"'{obj.label.capitalize()} is gone,' {vendor.pronoun().capitalize()} whispered. "
        f"'{obj.phrase} was on the cart only a minute ago.'"
    )
    _add_memes(vendor, "worry", 1)
    world.facts["missing"] = True


def follow_clues(world: World, hero: Entity, friend: Entity) -> Clue:
    # Simple mystery progression: clues narrow the path.
    first = CLUES[0]
    second = CLUES[1]
    world.say(
        f"{hero.id} knelt by {first.place} and saw {first.text}."
    )
    world.say(
        f"{friend.id} pointed at a second clue: {second.text}."
    )
    _add_memes(hero, "focus", 1)
    _add_memes(friend, "focus", 1)
    world.facts["clue_path"] = [first.id, second.id]
    return second


def teamwork_solution(world: World, hero: Entity, friend: Entity, vendor: Entity, obj: Entity) -> None:
    _add_memes(hero, "teamwork", 1)
    _add_memes(friend, "teamwork", 1)
    _add_memes(hero, "friendship", 1)
    _add_memes(friend, "friendship", 1)
    world.say(
        f"The two friends followed the clues together and found the {obj.label} beside the flower stand."
    )
    world.say(
        f"It had rolled there when a little cart bumped the crate, so it was only lost, not stolen."
    )
    world.say(
        f"{hero.id} carried it back, and {friend.id} kept the path clear for the vendor."
    )
    _add_meters(obj, "returned", 1)
    world.facts["found"] = "flower_stall"
    world.facts["solved_by"] = "teamwork"


def happy_ending(world: World, hero: Entity, friend: Entity, vendor: Entity, obj: Entity) -> None:
    _add_memes(vendor, "relief", 1)
    _add_memes(hero, "joy", 1)
    _add_memes(friend, "joy", 1)
    world.say(
        f"{vendor.id} smiled with relief when {obj.it()} came back. "
        f"'{hero.id} and {friend.id}, you solved my little mystery,' {vendor.pronoun().capitalize()} said."
    )
    world.say(
        f"The three of them shared a snack at the promenade while the lamps glowed warm and gold."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, obj_cfg: MysteryObject, hero_name: str, friend_name: str, vendor_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mia", "Nora", "Ava", "Rose", "Maya"} else "boy"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl" if friend_name in {"Mia", "Nora", "Ava", "Rose", "Maya"} else "boy"))
    vendor = world.add(Entity(id=vendor_name, kind="character", type="vendor"))
    obj = world.add(Entity(id=obj_cfg.id, type=obj_cfg.id, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=vendor.id, caretaker=vendor.id))

    world.say(
        f"It was a classic evening at {setting.place}, where {hero.id} liked to walk with {friend.id}."
    )
    world.say(
        f"{vendor.id} kept a small stand there, and {vendor.pronoun()} cared about {obj.phrase} because it was part of the display."
    )

    world.para()
    investigate(world, hero, friend, vendor, obj)

    world.para()
    follow_clues(world, hero, friend)
    teamwork_solution(world, hero, friend, vendor, obj)

    world.para()
    happy_ending(world, hero, friend, vendor, obj)

    world.facts.update(hero=hero, friend=friend, vendor=vendor, obj=obj, setting=setting, object_cfg=obj_cfg)
    return world


# ---------------------------------------------------------------------------
# Narrative content
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child at {f["setting"].place} about a missing {f["object_cfg"].label}.',
        f"Tell a gentle friendship story where {f['hero'].id} and {f['friend'].id} solve a tiny mystery together.",
        f'Write a classic promenade tale that uses the word "{f["object_cfg"].label}" and ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, vendor, obj = f["hero"], f["friend"], f["vendor"], f["obj"]
    return [
        QAItem(
            question=f"What did {vendor.id} lose at the promenade?",
            answer=f"{vendor.id} lost {obj.phrase}, and {hero.id} and {friend.id} helped look for it."
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the mystery?",
            answer="They used teamwork, followed little clues, and found the missing item near the flower stand."
        ),
        QAItem(
            question=f"Why was the ending happy?",
            answer=f"The ending was happy because the rutabaga came back, {vendor.id} felt relieved, and the friends shared a snack."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a promenade?",
            answer="A promenade is a place for walking, looking around, and enjoying the view."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something."
        ),
        QAItem(
            question="What is a rutabaga?",
            answer="A rutabaga is a round vegetable that grows underground and can be cooked or eaten in soups."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and help one another."
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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [("the promenade", "rutabaga"), ("the promenade", "lantern")]


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: this world only makes sense for a classic mystery at the promenade, and '{obj}' does not fit.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(the_promenade).
object(rutabaga).
object(lantern).
clue(mud).
clue(petal).
clue(coin).

valid_story(P,O) :- place(P), object(O), P = the_promenade.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "the_promenade")]
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for c in CLUES:
        lines.append(asp.fact("clue", c.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
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
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Classic promenade mystery with rutabaga, teamwork, friendship, and a happy ending.")
    ap.add_argument("--place", choices=["the promenade"])
    ap.add_argument("--object", dest="object_", choices=list(OBJECTS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--vendor")
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
    if args.place and args.place != "the promenade":
        raise StoryError(explain_rejection(args.place, args.object_ or "unknown"))
    place = "the promenade"
    obj = args.object_ or rng.choice(list(OBJECTS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    vendor = args.vendor or "Penny"
    return StoryParams(place=place, object=obj, name=name, friend_name=friend, vendor_name=vendor)


def generate(params: StoryParams) -> StorySample:
    obj_cfg = OBJECTS[params.object]
    world = tell(SETTING, obj_cfg, params.name, params.friend_name, params.vendor_name)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = [
            StoryParams("the promenade", "rutabaga", "Mia", "Leo", "Penny"),
            StoryParams("the promenade", "lantern", "Nora", "Ava", "Penny"),
        ]
        samples = [generate(p) for p in params]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
