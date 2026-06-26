#!/usr/bin/env python3
"""
storyworlds/worlds/vaseline_moral_value_bravery_bad_ending_bedtime.py
======================================================================

A small bedtime-story world about a child, a jar of vaseline, bravery,
moral value, and a gently bad ending.

Seed tale:
---
At bedtime, a child notices that their lips sting from the cold. Their parent
offers vaseline, but the child thinks it feels strange and does not want to
sit still. The child finally chooses to be brave and try the sticky balm.
It helps a little, but not enough to make everything perfect. The story ends
quietly with the child in bed, still a bit uncomfortable, but wiser about
doing the kind thing even when it is hard.

World model:
---
- The child has emotions like fear, bravery, trust, shame, and relief.
- The jar of vaseline can soothe chapped skin, but it can also smear on
  blankets or fingers if used carelessly.
- A bedtime mistake can leave a bad ending image: sticky sheets, a slow sleep,
  and a small leftover ache.
- Moral value is represented by choosing the helpful thing for someone else
  even when it is awkward or unpleasant.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
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
class Bed:
    name: str = "the bed"
    soft: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    skin_help: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, bed: Bed) -> None:
        self.bed = bed
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def pronoun_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_sticky(world: World) -> list[str]:
    out = []
    child = world.get("child")
    vas = world.get("vaseline")
    if child.meters.get("sticky", 0) < THRESHOLD:
        return out
    sig = ("sticky",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vas.meters["smudged"] = vas.meters.get("smudged", 0) + 1
    out.append("A little of the vaseline smeared onto the blanket.")
    return out


def _r_chapped(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters.get("cold", 0) < THRESHOLD:
        return out
    sig = ("chapped",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["chapped"] = child.meters.get("chapped", 0) + 1
    out.append("The cold made the child's lips sting even more.")
    return out


CAUSAL_RULES = [Rule("sticky", _r_sticky), Rule("chapped", _r_chapped)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CHILD_NAMES = ["Mina", "Nora", "Theo", "Lina", "Benny", "Pippa", "Otto", "Ivy"]
PARENTS = ["mother", "father"]
ITEMS = {
    "lipjar": Item(
        id="vaseline",
        label="vaseline",
        phrase="a tiny jar of vaseline",
        type="vaseline",
        region="lips",
        skin_help=True,
    ),
}


def valid_items() -> list[str]:
    return list(ITEMS)


def build_world(params: StoryParams) -> World:
    world = World(Bed())
    child = world.add(Entity(
        id="child",
        kind="character",
        type=pronoun_type(params.gender),
        label=params.name,
        meters={"cold": 1.0},
        memes={"fear": 1.0, "trust": 0.0, "bravery": 0.0, "moral_value": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        memes={"care": 1.0},
    ))
    item = ITEMS[params.item]
    vas = world.add(Entity(
        id="vaseline",
        type="thing",
        label=item.label,
        phrase=item.phrase,
        owner=parent.id,
        caretaker=parent.id,
        region=item.region,
        protective=False,
        meters={"help": 0.0, "smudged": 0.0},
    ))
    world.facts.update(child=child, parent=parent, vaseline=vas, item=item, params=params)
    return world


def tell(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    vas = world.get("vaseline")

    world.say(
        f"{child.label} was a little {child.type} who grew sleepy as the house turned quiet."
    )
    world.say(
        f"At bedtime, {child.label} noticed that {child.pronoun('possessive')} lips stung from the cold."
    )
    world.say(
        f"{parent.label_word if hasattr(parent, 'label_word') else parent.label} offered "
        f"{vas.phrase} and said it would help."
    )
    child.memes["fear"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.label} did not like the sticky feeling and wanted to say no."
    )

    world.para()
    world.say(
        f"{child.label} tried to be brave anyway. {child.pronoun().capitalize()} took a tiny dab,"
        f" and the cool cream touched {child.pronoun('possessive')} lips."
    )
    child.memes["bravery"] += 1
    child.memes["trust"] += 1
    child.meters["sticky"] = child.meters.get("sticky", 0) + 1
    vas.meters["help"] = vas.meters.get("help", 0) + 1
    propagate(world)

    world.para()
    child.meters["cold"] = 0.0
    child.meters["chapped"] = 1.0
    child.memes["moral_value"] += 1
    child.memes["relief"] += 0.5
    world.say(
        f"It helped a little, but not enough to make everything easy."
    )
    world.say(
        f"{child.label} lay under the blanket with a brave heart and a still-stingy smile."
    )
    world.say(
        f"The bed felt a bit sticky, the room stayed a bit cold, and the night ended quietly."
    )

    world.facts["ending_bad"] = True
    world.facts["moral"] = "being brave can mean doing the kind thing even when it feels awkward"
    world.facts["helped"] = True


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        "Write a bedtime story about a child, a jar of vaseline, and a small act of bravery.",
        f"Tell a gentle bedtime story where {child.label} is unsure about the sticky ointment "
        f"but {parent.label} helps anyway.",
        "Write a story that ends with a quiet, slightly disappointing bedtime image, but still teaches a moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    vas = f["vaseline"]
    return [
        QAItem(
            question=f"Why did {child.label} hesitate when {parent.label} offered the vaseline?",
            answer=f"{child.label} hesitated because the vaseline felt sticky and strange, and {child.pronoun('possessive')} lips already felt sore from the cold.",
        ),
        QAItem(
            question=f"What brave choice did {child.label} make before bed?",
            answer=f"{child.label} chose to try the vaseline anyway, even though {child.pronoun('subject')} did not like the feeling.",
        ),
        QAItem(
            question=f"How did the story end for {child.label} and the bed?",
            answer=f"The story ended with a slightly bad ending: the bed was a little sticky, the room still felt cold, and {child.label} did not get perfect comfort before sleep.",
        ),
        QAItem(
            question=f"What moral value did {child.label} show?",
            answer=f"{child.label} showed moral value by doing the helpful thing instead of only thinking about comfort, and that took bravery.",
        ),
        QAItem(
            question=f"Who offered the vaseline?",
            answer=f"{parent.label} offered {vas.phrase} at bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is vaseline used for?",
            answer="Vaseline is a greasy balm that can help dry or chapped skin feel softer and less sore.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how people should treat others, like being kind, honest, or helpful.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is a story ending where things are not completely fixed, so the characters do not get everything they wanted.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_hesitates :- fear(F), F >= 1.
brave_choice :- bravery(B), B >= 1.
bad_ending :- sticky(S), S >= 1, chapped(C), C >= 1.
moral_value :- moral(M), M >= 1.
#show child_hesitates/0.
#show brave_choice/0.
#show bad_ending/0.
#show moral_value/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item in ITEMS.values():
        lines.append(asp.fact("item", item.id))
        lines.append(asp.fact("helps_skin", item.id))
    lines.append(asp.fact("style", "bedtime"))
    lines.append(asp.fact("theme", "moral_value"))
    lines.append(asp.fact("theme", "bravery"))
    lines.append(asp.fact("theme", "bad_ending"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about vaseline, bravery, and a bad ending.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--item", choices=valid_items())
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    item = args.item or "lipjar"
    return StoryParams(name=name, gender=gender, parent=parent, item=item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=story_text(world),
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


def _asp_verify() -> int:
    import asp
    program = asp_program("#show brave_choice/0.\n#show bad_ending/0.\n#show moral_value/0.\n")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    expected = {"brave_choice", "bad_ending", "moral_value"}
    if expected.issubset(atoms):
        print("OK: ASP twin recognizes the core story features.")
        return 0
    print("MISMATCH: ASP twin did not recognize all core features.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_choice/0.\n#show bad_ending/0.\n#show moral_value/0.\n"))
        return
    if args.verify:
        sys.exit(_asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", parent="mother", item="lipjar"),
            StoryParams(name="Theo", gender="boy", parent="father", item="lipjar"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
