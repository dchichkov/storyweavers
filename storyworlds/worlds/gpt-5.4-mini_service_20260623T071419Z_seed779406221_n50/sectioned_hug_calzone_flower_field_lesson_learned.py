#!/usr/bin/env python3
"""
storyworlds/worlds/sectioned_hug_calzone_flower_field_lesson_learned.py
======================================================================

A small Adventure-style storyworld set in a flower field, built from the seed
words sectioned, hug, and calzone, with a clear Lesson Learned ending.

Premise:
- Two children explore a flower field.
- They find a sectioned calzone in a picnic basket.
- A tempting plan goes a little wrong when the food is split the wrong way.
- They solve it by sharing carefully, learning that a kind plan works better
  than grabbing first.

The world uses typed entities with meters and memes, a tiny forward-chaining
simulation, a reasonableness gate, and an inline ASP twin.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the flower field"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    sectioned: bool = False
    edible: bool = False
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_hunger(world: World) -> list[str]:
    out = []
    basket = world.entities.get("basket")
    if not basket:
        return out
    if basket.meters.get("opened", 0) < THRESHOLD:
        return out
    if basket.meters.get("touched", 0) < THRESHOLD:
        return out
    if basket.meters.get("crumbs", 0) >= THRESHOLD and ("hunger", "felt") not in world.fired:
        world.fired.add(("hunger", "felt"))
        for kid in world.children():
            kid.memes["hunger"] = kid.memes.get("hunger", 0) + 1
        out.append("The smell made the children even hungrier.")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    snack = world.entities.get("item")
    if not snack or snack.meters.get("divided", 0) < THRESHOLD:
        return out
    if snack.meters.get("dropped", 0) < THRESHOLD:
        return out
    if ("spill", snack.id) in world.fired:
        return out
    world.fired.add(("spill", snack.id))
    snack.meters["messy"] = snack.meters.get("messy", 0) + 1
    out.append("Some filling fell into the grass.")
    return out


def _r_lesson(world: World) -> list[str]:
    out = []
    if world.facts.get("resolved") and ("lesson", "learned") not in world.fired:
        world.fired.add(("lesson", "learned"))
        for kid in world.children():
            kid.memes["lesson"] = kid.memes.get("lesson", 0) + 1
            kid.memes["joy"] = kid.memes.get("joy", 0) + 1
        out.append("The lesson settled in warmly.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_hunger, _r_spill, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    return [("flower_field", "calzone")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a flower field.")
    ap.add_argument("--place", choices=["flower_field"])
    ap.add_argument("--item", choices=["calzone"])
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    place = args.place or "flower_field"
    item = args.item or "calzone"
    if (place, item) not in valid_combos():
        raise StoryError("No valid combination matches the given options.")
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or ("boy" if gender1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(["Mia", "Lily", "Ava", "Nora", "Leo", "Max"])
    name2 = args.name2 or rng.choice([n for n in ["Mia", "Lily", "Ava", "Nora", "Leo", "Max"] if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        item=item,
        child1=name1,
        child1_gender=gender1,
        child2=name2,
        child2_gender=gender2,
        parent=parent,
    )


def tell(params: StoryParams) -> World:
    setting = Setting(place="the flower field", affordances={"picnic", "share"})
    world = World(setting)
    a = world.add(Entity(id="child1", kind="character", type=params.child1_gender, label=params.child1))
    b = world.add(Entity(id="child2", kind="character", type=params.child2_gender, label=params.child2))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    basket = world.add(Entity(id="basket", label="picnic basket", meters={"opened": 0, "touched": 0, "crumbs": 0}))
    snack = world.add(Entity(id="item", label="calzone", phrase="a sectioned calzone", tags={"sectioned", "calzone"}))
    a.meters["want"] = 1
    b.meters["want"] = 1
    a.memes["curious"] = 1
    b.memes["curious"] = 1

    world.say(
        f"On a bright afternoon, {a.label} and {b.label} ran into the flower field, where the blossoms bobbed like tiny flags."
    )
    world.say(
        f"They found a picnic basket beside the path, and inside it was {snack.phrase}, neatly sectioned for sharing."
    )
    world.para()
    world.say(
        f"{a.label} wanted a hug for luck, so {a.pronoun().capitalize()} gave {b.label} a quick hug before the first bite."
    )
    basket.meters["opened"] = 1
    basket.meters["touched"] = 1
    basket.meters["crumbs"] = 1
    snack.meters["divided"] = 1
    propagate(world, narrate=True)
    world.say(
        f"But when both children reached for the biggest section at once, the calzone tipped and a little filling dropped into the grass."
    )
    snack.meters["dropped"] = 1
    propagate(world, narrate=True)

    world.para()
    parent.say = world.say
    world.say(
        f"{parent.label_word.capitalize() if hasattr(parent, 'label_word') else params.parent.capitalize()} knelt by the flowers and smiled. "
        f'\"A sectioned snack works best when everyone shares the pieces,\" {params.parent} said.'
    )
    snack.meters["shared"] = 1
    snack.meters["messy"] = 0
    world.facts["resolved"] = True
    propagate(world, narrate=True)
    world.say(
        f"{a.label} and {b.label} took smaller bites, laughed, and watched the bees drift from bloom to bloom while the flower field stayed tidy."
    )
    world.facts.update(child1=a, child2=b, parent=parent, snack=snack, basket=basket)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, snack = f["child1"], f["child2"], f["snack"]
    return [
        'Write a short Adventure story set in a flower field that includes the words "sectioned", "hug", and "calzone".',
        f"Tell a gentle adventure where {a.label} and {b.label} find {snack.phrase} in a flower field and learn to share it kindly.",
        "Write a child-friendly lesson-learned story in a flower field with a picnic snack and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, snack = f["child1"], f["child2"], f["snack"]
    return [
        QAItem(
            question=f"Where did {a.label} and {b.label} find the snack?",
            answer="They found it in the flower field beside the path, inside a picnic basket.",
        ),
        QAItem(
            question=f"What kind of snack was sectioned for sharing?",
            answer=f"It was a calzone, and it had been sectioned into pieces so it could be shared.",
        ),
        QAItem(
            question=f"Why did the children give each other a hug?",
            answer=f"They gave a hug because they felt excited and wanted to be kind before sharing the calzone.",
        ),
        QAItem(
            question="What did the children learn at the end?",
            answer="They learned that sharing small pieces works better than grabbing the biggest one first.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a flower field?", answer="A flower field is a wide outdoor place full of blossoms and buzzing bees."),
        QAItem(question="What does sectioned mean?", answer="Sectioned means split into pieces or parts."),
        QAItem(question="What is a calzone?", answer="A calzone is a folded baked snack with filling tucked inside."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs} tags={sorted(e.tags)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sectioned(calzone).
valid(flower_field, calzone).
learned :- resolved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "flower_field"), asp.fact("item", "calzone"), asp.fact("sectioned", "calzone")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("ASP mismatch.")
        print("python:", sorted(py))
        print("asp:", sorted(asp_set))
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("Story generation failed.")
        return 1
    print("OK")
    return 0


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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="flower_field", item="calzone", child1="Mia", child1_gender="girl", child2="Leo", child2_gender="boy", parent="mother"))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
