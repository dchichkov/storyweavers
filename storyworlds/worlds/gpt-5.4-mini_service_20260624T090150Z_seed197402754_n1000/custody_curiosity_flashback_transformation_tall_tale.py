#!/usr/bin/env python3
"""
custody_curiosity_flashback_transformation_tall_tale.py
========================================================

A small, standalone story world for a tall-tale style custody story with
curiosity, flashback, and transformation.

Premise:
- A child is given temporary custody of a peculiar small creature or object.
- The child is curious, which triggers a flashback to how the creature/object
  was found.
- Care and patience cause a transformation that changes the ending image.

This world keeps the prose concrete and state-driven while staying close to the
breezy, exaggerated feel of a tall tale.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    kind: str
    size: str
    needs: set[str]
    transformation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CustodyItem:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "caretaker": v.caretaker, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


@dataclass
class StoryParams:
    place: str
    creature: str
    item: str
    child_name: str
    child_gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "porch": Setting(place="the porch", afford={"look", "care"}),
    "barn": Setting(place="the barn", afford={"look", "care"}),
    "kitchen": Setting(place="the kitchen", afford={"look", "care"}),
    "yard": Setting(place="the yard", afford={"look", "care"}),
}

CREATURES = {
    "gosling": Creature(
        id="gosling",
        label="gosling",
        phrase="a speckled gosling with a button-beak",
        kind="bird",
        size="small",
        needs={"grain", "water", "warmth"},
        transformation="a proud goose with a trumpet voice",
        tags={"bird", "feathers", "water"},
    ),
    "foal": Creature(
        id="foal",
        label="foal",
        phrase="a wobbling foal with long eyelashes",
        kind="horse",
        size="small",
        needs={"hay", "water", "brush"},
        transformation="a shining parade horse with a thunder-step",
        tags={"horse", "hooves", "hay"},
    ),
    "kitten": Creature(
        id="kitten",
        label="kitten",
        phrase="a whiskered kitten with a tiny tail",
        kind="cat",
        size="small",
        needs={"milk", "blanket", "gentle hands"},
        transformation="a grand barn cat with a captain's stare",
        tags={"cat", "fur", "milk"},
    ),
    "sapling": Creature(
        id="sapling",
        label="sapling",
        phrase="a skinny sapling in a clay pot",
        kind="tree",
        size="small",
        needs={"water", "sun", "soil"},
        transformation="a tall shade tree with a crown of leaves",
        tags={"tree", "leaves", "water"},
    ),
}

ITEMS = {
    "lantern": CustodyItem(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a smoky wick",
        kind="object",
        region="hands",
        fragile=True,
        tags={"light", "glass"},
    ),
    "egg": CustodyItem(
        id="egg",
        label="egg",
        phrase="a pale egg wrapped in straw",
        kind="object",
        region="hands",
        fragile=True,
        tags={"shell", "warmth"},
    ),
    "hat": CustodyItem(
        id="hat",
        label="hat",
        phrase="a feathered hat with a bent brim",
        kind="object",
        region="head",
        fragile=False,
        tags={"feather", "cloth"},
    ),
    "map": CustodyItem(
        id="map",
        label="map",
        phrase="a crinkly map with one missing corner",
        kind="object",
        region="hands",
        fragile=True,
        tags={"paper", "ink"},
    ),
}

GIRL_NAMES = ["Lena", "Mabel", "Rosie", "June", "Hazel", "Ivy", "Mina", "Daisy"]
BOY_NAMES = ["Otis", "Wes", "Cal", "Rudy", "Bennie", "Tate", "Jasper", "Eli"]
TRAITS = ["curious", "bold", "gentle", "lively", "stubborn", "bright"]


def custody_at_risk(creature: Creature, item: CustodyItem) -> bool:
    return bool(creature.tags & item.tags or item.fragile)


def resolve_pair(creature: Creature, item: CustodyItem) -> bool:
    return custody_at_risk(creature, item)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for c in CREATURES.values():
            for it in ITEMS.values():
                if resolve_pair(c, it):
                    combos.append((place, c.id, it.id))
    return combos


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.memes.get('traits', []) if t != 'little') if child.memes.get('traits') else child.type} "
        f"{child.type} who could spot a mystery from a mile away."
    )


def setup_story(world: World, child: Entity, guardian: Entity, creature: Creature, item: CustodyItem) -> None:
    world.say(
        f"One bright day at {world.setting.place}, {guardian.label} handed {child.id} "
        f"custody of {item.phrase} and {creature.phrase}."
    )
    world.say(
        f"{child.id} loved the job, because the little one looked like it had been made for a tale."
    )


def curiosity(world: World, child: Entity, creature: Creature, item: CustodyItem) -> None:
    child.memes["curiosity"] = meme(child, "curiosity") + 1
    world.say(
        f"{child.id} kept peeking at {item.label} and wondering how such a small thing could matter so much."
    )
    world.say(
        f"{child.id} asked, \"Where did this come from?\" and the question rang through the place like a dinner bell."
    )


def flashback(world: World, child: Entity, guardian: Entity, creature: Creature, item: CustodyItem) -> None:
    world.facts["flashback"] = True
    if creature.id == "gosling":
        text = (
            f"{guardian.label} smiled and told a flashback: yesterday, {creature.label} had wandered from the marsh "
            f"with a wet feather and a brave little honk."
        )
    elif creature.id == "foal":
        text = (
            f"{guardian.label} told a flashback: {creature.label} had tottered out of a stormy field, "
            f"shivering like a paper bag in the wind."
        )
    elif creature.id == "kitten":
        text = (
            f"{guardian.label} told a flashback: {creature.label} had climbed into the hayloft, "
            f"hungry enough to chase a crumb by smell alone."
        )
    else:
        text = (
            f"{guardian.label} told a flashback: {creature.label} had been found under the fence, "
            f"thirsty and leaning toward the sun like a sleepy cup."
        )
    world.say(text)


def transform(world: World, creature: Creature, item: CustodyItem, child: Entity) -> None:
    creature_ent = world.get(creature.id)
    creature_ent.meters["care"] = meter(creature_ent, "care") + 1
    creature_ent.memes["safe"] = meme(creature_ent, "safe") + 1
    if creature.id == "sapling":
        creature_ent.meters["tall"] = 1
    if creature.id == "kitten":
        creature_ent.memes["proud"] = 1
    world.facts["transformed"] = True
    world.say(
        f"Day by day, {child.id} gave {creature.label} {', '.join(sorted(creature.needs))}, and the little one began to change."
    )
    world.say(
        f"By supper time, {creature.label} stood as {creature.transformation}, while {item.label} gleamed like it had a fresh coat of luck."
    )


def ending(world: World, child: Entity, guardian: Entity, creature: Creature, item: CustodyItem) -> None:
    if creature.id == "gosling":
        world.say(
            f"Before the stars had finished twinkling, {creature.label} was marching in circles and honking like a trumpet."
        )
    elif creature.id == "foal":
        world.say(
            f"Before the lantern burned low, {creature.label} was stepping so high the boards seemed to clap back."
        )
    elif creature.id == "kitten":
        world.say(
            f"Before the moon rode up, {creature.label} was purring so hard it sounded like a tiny engine."
        )
    else:
        world.say(
            f"Before the morning bird had a chance to sing twice, {creature.label} had stretched tall and rustled the rafters."
        )
    world.say(
        f"{child.id} grinned at {guardian.label}, because custody had turned into care, and care had turned into something that felt a lot like family."
    )


def tell(setting: Setting, creature: Creature, item: CustodyItem,
         child_name: str = "Mabel", child_type: str = "girl",
         guardian_type: str = "grandmother", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, memes={"traits": ["little", trait, "curious"]},
    ))
    guardian = world.add(Entity(
        id="Guardian", kind="character", type=guardian_type, label="Grandma",
    ))
    creature_ent = world.add(Entity(
        id=creature.id, kind="creature", type=creature.kind, label=creature.label, phrase=creature.phrase,
        owner=guardian.id, caretaker=child.id,
    ))
    item_ent = world.add(Entity(
        id=item.id, kind="object", type=item.kind, label=item.label, phrase=item.phrase,
        owner=guardian.id, caretaker=child.id,
    ))

    setup_story(world, child, guardian, creature, item)
    world.para()
    curiosity(world, child, creature, item)
    flashback(world, child, guardian, creature, item)
    world.para()
    transform(world, creature, item, child)
    ending(world, child, guardian, creature, item)

    world.facts.update(
        child=child, guardian=guardian, creature=creature_ent, item=item_ent,
        creature_cfg=creature, item_cfg=item, setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    creature = f["creature_cfg"]
    item = f["item_cfg"]
    return [
        f'Write a tall tale for a young child about custody, curiosity, a flashback, and a transformation.',
        f"Tell a big-hearted story where {child.id} is given custody of {item.phrase} and learns where {creature.phrase} came from.",
        f"Write a simple story about a child who keeps asking questions and discovers that caring for {creature.label} changes everything.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    creature = f["creature_cfg"]
    item = f["item_cfg"]
    return [
        QAItem(
            question=f"Who was given custody of {item.label}?",
            answer=f"{child.id} was given custody of {item.phrase} by {guardian.label}.",
        ),
        QAItem(
            question=f"What did {child.id} keep wondering about?",
            answer=f"{child.id} kept wondering where {creature.label} came from and why it mattered so much.",
        ),
        QAItem(
            question=f"What did the flashback explain?",
            answer=f"The flashback explained how {creature.label} was first found and why it needed care.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{creature.label} changed into {creature.transformation}, and custody became loving care.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    creature = f["creature_cfg"]
    out = [
        QAItem(
            question="What is custody?",
            answer="Custody means having the responsibility to take care of someone or something for a while.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to ask questions and learn new things.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state or form into another.",
        ),
    ]
    if creature.id == "sapling":
        out.append(QAItem(
            question="What does a sapling need to grow?",
            answer="A sapling needs water, sun, and soil so it can grow into a bigger tree.",
        ))
    elif creature.id == "gosling":
        out.append(QAItem(
            question="What does a gosling become when it grows up?",
            answer="A gosling grows into a goose.",
        ))
    elif creature.id == "foal":
        out.append(QAItem(
            question="What does a foal become when it grows up?",
            answer="A foal grows into a horse.",
        ))
    else:
        out.append(QAItem(
            question="What does a kitten become when it grows up?",
            answer="A kitten grows into a cat.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
custody_risk(C, I) :- creature(C), item(I), tags(C, T), tags(I, T).
custody_risk(C, I) :- fragile(I), creature(C), item(I).

valid_story(P, C, I) :- place(P), creature(C), item(I), custody_risk(C, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tags", cid, t))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.fragile:
            lines.append(asp.fact("fragile", iid))
        for t in sorted(i.tags):
            lines.append(asp.fact("tags", iid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show custody_risk/2."))
    return sorted(set(asp.atoms(model, "custody_risk")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set((c, i) for _, c, i in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} pairs).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale custody story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.creature is None or c[1] == args.creature)
        and (args.item is None or c[2] == args.item)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, creature, item = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    guardian = args.guardian or rng.choice(["grandmother", "grandfather"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, creature=creature, item=item, child_name=name, child_gender=gender, guardian=guardian, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CREATURES[params.creature], ITEMS[params.item],
                 params.child_name, params.child_gender, params.guardian, params.trait)
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
    StoryParams(place="barn", creature="gosling", item="lantern", child_name="Mabel", child_gender="girl", guardian="grandmother", trait="curious"),
    StoryParams(place="yard", creature="foal", item="map", child_name="Otis", child_gender="boy", guardian="grandfather", trait="bold"),
    StoryParams(place="porch", creature="kitten", item="egg", child_name="June", child_gender="girl", guardian="grandmother", trait="gentle"),
    StoryParams(place="kitchen", creature="sapling", item="hat", child_name="Eli", child_gender="boy", guardian="grandfather", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show custody_risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show custody_risk/2."))
        print(sorted(set(asp.atoms(model, "custody_risk"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
