#!/usr/bin/env python3
"""
family_tool_shed_friendship_kindness_dialogue_adventure.py
===========================================================

A standalone story world about a family in a tool shed, where a small
adventure grows out of friendship, kindness, and dialogue.

Premise:
- A child helps a family member look for a missing thing in a tool shed.
- The shed feels a little dark and cluttered, so the search becomes an
  adventure.
- A friend joins, offers kindness, and the group talks through the clues.
- The ending proves what changed: the missing item is found, the shed is
  tidied, and the family feels closer.

This world is deliberately small and constraint-driven: every generated story
must have a clear search, a turn, and a resolution.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tool shed"
    affordances: set[str] = field(default_factory=set)


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    location: str
    is_small: bool = True
    is_tool: bool = True


@dataclass
class FamilyRole:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    family_size: int
    hero_name: str
    hero_type: str
    parent_name: str
    parent_type: str
    friend_name: str
    friend_type: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _keyword_for_item(item_id: str) -> str:
    return {
        "hammer": "hammer",
        "gloves": "gloves",
        "lantern": "lantern",
        "nails": "nails",
        "pruner": "pruner",
    }[item_id]


ITEMS = {
    "hammer": MysteryItem(
        id="hammer",
        label="hammer",
        phrase="a little red hammer",
        location="behind the paint cans",
        is_small=True,
        is_tool=True,
    ),
    "gloves": MysteryItem(
        id="gloves",
        label="work gloves",
        phrase="a pair of soft work gloves",
        location="inside a bucket",
        is_small=True,
        is_tool=False,
    ),
    "lantern": MysteryItem(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        location="under a shelf",
        is_small=True,
        is_tool=False,
    ),
    "nails": MysteryItem(
        id="nails",
        label="nails",
        phrase="a tin of shiny nails",
        location="in a box of screws",
        is_small=True,
        is_tool=True,
    ),
    "pruner": MysteryItem(
        id="pruner",
        label="pruner",
        phrase="a green garden pruner",
        location="next to a rake",
        is_small=True,
        is_tool=True,
    ),
}

FAMILY_TYPES = ["mother", "father", "girl", "boy", "aunt", "uncle"]
NAMES = ["Maya", "Noah", "Lena", "Theo", "Iris", "Owen", "Mila", "Eli"]
TRAITS = ["brave", "kind", "curious", "helpful", "cheerful", "careful"]
FRIEND_TRAITS = ["friendly", "gentle", "loyal", "patient", "bright"]


def valid_items() -> list[str]:
    return list(ITEMS)


def item_at_risk(item: MysteryItem) -> bool:
    return item.is_small


def has_reasonable_search(item: MysteryItem) -> bool:
    return item_at_risk(item)


ASP_RULES = r"""
item(I) :- item_label(I,_).
searchable(I) :- item(I), small(I).
helpful(F) :- friend(F).
family_story(H,P,F,I) :- hero(H), parent(P), friend(F), searchable(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "tool_shed"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_label", iid, item.label))
        if item.is_small:
            lines.append(asp.fact("small", iid))
        if item.is_tool:
            lines.append(asp.fact("tool", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show item/1. #show searchable/1."))
    asp_items = {args[0] for args in asp.atoms(model, "item")}
    py_items = set(valid_items())
    if asp_items == py_items:
        print(f"OK: ASP matches Python item registry ({len(py_items)} items).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("ASP only:", sorted(asp_items - py_items))
    print("Python only:", sorted(py_items - asp_items))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a family adventure in a tool shed."
    )
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--family-size", type=int, choices=[3, 4, 5, 6], default=None)
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
    item = args.item or rng.choice(list(ITEMS))
    if not has_reasonable_search(ITEMS[item]):
        raise StoryError("No valid story for that item.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father", "aunt", "uncle"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    family_size = args.family_size or rng.choice([3, 4, 5])
    hero_name = args.hero_name or rng.choice(NAMES)
    parent_name = args.parent_name or rng.choice([n for n in NAMES if n != hero_name])
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n not in {hero_name, parent_name}])
    if hero_name == friend_name:
        raise StoryError("Hero and friend must be different names.")
    return StoryParams(
        family_size=family_size,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_name=parent_name,
        parent_type=parent_type,
        friend_name=friend_name,
        friend_type=friend_type,
        item=item,
    )


def intro(world: World, hero: Entity, parent: Entity, friend: Entity, item: MysteryItem) -> None:
    world.say(
        f"{hero.id} lived with {hero.pronoun('possessive')} family near the tool shed. "
        f"{hero.id} was a little {hero.type} who loved small adventures."
    )
    world.say(
        f"{parent.id} had asked for {item.phrase}, but nobody could find it in the shed. "
        f"{friend.id} came along with a smile and said they would help."
    )


def search_turn(world: World, hero: Entity, parent: Entity, friend: Entity, item: MysteryItem) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    parent.memes["worry"] = parent.memes.get("worry", 0) + 1
    friend.memes["kindness"] = friend.memes.get("kindness", 0) + 1
    world.para()
    world.say(
        f"The tool shed was dim and crowded with boxes, rope, and rakes. "
        f"{hero.id} peered under a shelf while {parent.id} checked the hooks."
    )
    world.say(
        f'"Maybe the clues are hidden in plain sight," {friend.id} said. '
        f"Together they looked carefully, one spot at a time."
    )
    world.say(
        f"{hero.id} found a dusty footprint, and {parent.id} noticed the print led "
        f"toward {item.location}."
    )


def resolve(world: World, hero: Entity, parent: Entity, friend: Entity, item: MysteryItem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    parent.memes["relief"] = parent.memes.get("relief", 0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0) + 1
    world.para()
    world.say(
        f"They followed the clue and found {item.phrase} right where the trail pointed."
    )
    world.say(
        f"{friend.id} handed it over kindly, and {hero.id} carried it to {parent.id} with care."
    )
    world.say(
        f"Then the family stacked the boxes neatly. The shed looked brighter, and the little adventure ended with smiles."
    )


def tell(params: StoryParams) -> World:
    setting = Setting(place="the tool shed", affordances={"search", "talk", "help"})
    world = World(setting)
    item = ITEMS[params.item]

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        traits=["little", "brave"]
    ))
    parent = world.add(Entity(
        id=params.parent_name, kind="character", type=params.parent_type,
        traits=["patient", "busy"]
    ))
    friend = world.add(Entity(
        id=params.friend_name, kind="character", type=params.friend_type,
        traits=["kind", "friendly"]
    ))
    object_ent = world.add(Entity(
        id=item.id, kind="thing", type=item.label, label=item.label,
        phrase=item.phrase, owner=parent.id, caretaker=parent.id
    ))

    world.facts.update(hero=hero, parent=parent, friend=friend, item=item, object=object_ent)
    intro(world, hero, parent, friend, item)
    search_turn(world, hero, parent, friend, item)
    resolve(world, hero, parent, friend, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    hero = f["hero"]
    parent = f["parent"]
    friend = f["friend"]
    return [
        f'Write a short adventure story for a young child set in a tool shed that includes "{item.label}".',
        f"Tell a gentle family story where {hero.id}, {parent.id}, and {friend.id} search the tool shed together.",
        f'Write a simple story about friendship and kindness where a missing {item.label} is found after careful talking.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    friend: Entity = f["friend"]
    item: MysteryItem = f["item"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id} and {hero.pronoun('possessive')} family in the tool shed, with {friend.id} helping too."
        ),
        QAItem(
            question=f"What were they looking for in the tool shed?",
            answer=f"They were looking for {item.phrase}."
        ),
        QAItem(
            question=f"How did {friend.id} help?",
            answer=f"{friend.id} helped by being kind, talking with the family, and searching carefully until they found {item.label}."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the missing {item.label} was found and the shed was tidied, so the family felt happy and close."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building where families keep tools, boxes, and things used for jobs around the home."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, help each other, and enjoy being together."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle and helpful for someone else."
        ),
        QAItem(
            question="Why is dialogue useful in a problem?",
            answer="Dialogue helps people share clues, ask questions, and work together to solve a problem."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for name, ent in world.entities.items():
        bits = []
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        lines.append(f"  {name}: {ent.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(3, "Mia", "girl", "Dad", "father", "Noah", "boy", "hammer"),
    StoryParams(4, "Eli", "boy", "Mom", "mother", "Lena", "girl", "lantern"),
    StoryParams(5, "Iris", "girl", "Aunt May", "aunt", "Theo", "boy", "gloves"),
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


def asp_valid_items() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show item/1."))
    return sorted(set(asp.atoms(model, "item")))


def asp_verify_items() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show item/1. #show small/1. #show tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show item/1. #show small/1. #show tool/1."))
        items = sorted(set(asp.atoms(model, "item")))
        print(f"{len(items)} items:")
        for item in items:
            print(" ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = []
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and family in the tool shed"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
