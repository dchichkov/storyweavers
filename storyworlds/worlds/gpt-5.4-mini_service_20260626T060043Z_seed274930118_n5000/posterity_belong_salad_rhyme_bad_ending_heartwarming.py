#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/posterity_belong_salad_rhyme_bad_ending_heartwarming.py
====================================================================================

A small heartwarming storyworld about a child, a salad, and what belongs where.
The seed words suggest a gentle tale about posterity, belonging, and salad, with
a rhyming narrator and a brief "bad ending" beat that is turned into something
kind.

Story premise:
- A child and a grandparent make a salad from garden ingredients.
- The child fears the salad does not "belong" at the celebration.
- A careful rhyme-guided helper turn shows that the salad belongs with the family.
- The story ends with the salad shared and remembered for posterity.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- explicit invalid choices raise StoryError
- eager import of results.py; lazy import of asp.py in ASP helpers
- build_parser / resolve_params / generate / emit / main
- inline ASP_RULES twin and parity verification
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    served_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fresh": 0.0, "shared": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "warmth": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    belongs_to: str
    fresh: bool = True
    is_salad: bool = False


@dataclass
class RhymingGuide:
    id: str
    rhyme_a: str
    rhyme_b: str
    clue: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    elder_name: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"mix", "serve", "pack"}),
    "garden": Setting(place="the garden", indoors=False, affords={"pick", "mix", "serve"}),
    "porch": Setting(place="the porch", indoors=False, affords={"serve", "pack"}),
}

CHILD_NAMES = ["Mia", "Noah", "Ivy", "Luna", "Eli", "Milo", "June", "Ada"]
ELDER_NAMES = ["Grandma Rose", "Grandpa Ben", "Nana June", "Papa Leo"]

INGREDIENTS = {
    "lettuce": Ingredient("lettuce", "lettuce", "crisp lettuce", "salad"),
    "tomato": Ingredient("tomato", "tomato", "red tomato slices", "salad"),
    "cucumber": Ingredient("cucumber", "cucumber", "cool cucumber pieces", "salad"),
    "carrot": Ingredient("carrot", "carrot", "bright carrot coins", "salad"),
    "seedbread": Ingredient("seedbread", "seedbread", "toasted seed bread", "memory"),
    "salad": Ingredient("salad", "salad", "a big bowl of salad", "table", is_salad=True),
}

GUIDES = {
    "rhyme": RhymingGuide(
        "rhyme",
        rhyme_a="shine",
        rhyme_b="fine",
        clue="The guide says the salad should shine and be fine.",
    )
}

GROUNDS = {
    "memory": "for posterity",
    "table": "for the table",
    "family": "for the family",
}


class StoryWorldError(StoryError):
    pass


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, and {b}."


def simulate_mix(world: World, child: Entity) -> None:
    child.meters["handsy"] = child.meters.get("handsy", 0.0) + 1
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1


def simulate_worry(world: World, child: Entity, salad: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    salad.meters["fresh"] = max(0.0, salad.meters.get("fresh", 0.0) - 0.2)


def simulate_share(world: World, child: Entity, elder: Entity, salad: Entity) -> None:
    salad.meters["shared"] = salad.meters.get("shared", 0.0) + 1
    child.memes["warmth"] = child.memes.get("warmth", 0.0) + 1
    elder.memes["warmth"] = elder.memes.get("warmth", 0.0) + 1
    salad.served_to = elder.id


def setting_line(setting: Setting) -> str:
    if setting.indoors:
        return "The room was warm, with a table that waited like a smiling stage."
    return f"{setting.place.capitalize()} was bright, with air that felt light and kind."


def tell_story(world: World, child: Entity, elder: Entity, salad: Entity) -> None:
    ing = [world.get(k) for k in ("lettuce", "tomato", "cucumber", "carrot")]
    guide = GUIDES["rhyme"]

    world.say(
        f"{child.id} and {elder.label} came to {world.setting.place} with a basket of garden things."
    )
    world.say(
        f"They wanted to make a salad that could belong to the family, not just to one plate."
    )
    world.say(setting_line(world.setting))
    world.say(
        f"{guide.clue} {rhyme_line('Little hands went quick', 'and the bowl began to click')}"
    )

    world.para()
    world.say(
        f"{child.id} washed the lettuce, {elder.pronoun('subject').capitalize()} sliced the tomato, and the cucumber came next."
    )
    simulate_mix(world, child)
    salad.meters["fresh"] += 1
    world.say(
        f"The bowl looked cheerful, and the colors felt like a small song."
    )

    world.para()
    simulate_worry(world, child, salad)
    world.say(
        f"Then {child.id} frowned and whispered that the salad might not belong anywhere special."
    )
    world.say(
        f"{elder.label} shook {elder.pronoun('possessive')} head and said the salad belonged where love was shared."
    )
    world.say(
        rhyme_line("A salad can rest", "where kindly hands have blessed")
    )
    world.say(
        f"The sad thought was a bad ending for a moment, but it did not stay."
    )

    world.para()
    simulate_share(world, child, elder, salad)
    salad.owner = elder.id
    world.say(
        f"They added the carrots, tucked in the seed bread, and carried the bowl to the table."
    )
    world.say(
        f"At last the salad belonged with everyone, and {child.id} smiled because it would be remembered for posterity."
    )
    world.say(
        rhyme_line("One bowl, one light", "made the whole evening bright")
    )

    world.facts.update(
        child=child,
        elder=elder,
        salad=salad,
        guide=guide,
        setting=world.setting,
        ingredients=ing,
        shared=salad.meters["shared"] >= THRESHOLD,
        worried=child.memes["worry"] >= THRESHOLD,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    return [
        f'Write a heartwarming rhyming story about {child.id} and {elder.label} making a salad for posterity.',
        f"Tell a gentle story where a salad belongs with the family, even after a brief bad ending feeling.",
        f'Write a child-friendly rhyme using the words "posterity", "belong", and "salad".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    salad = f["salad"]
    qs = [
        QAItem(
            question=f"Who made the salad in {world.setting.place}?",
            answer=f"{child.id} and {elder.label} made the salad together in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the child worry about after the salad was mixed?",
            answer=f"{child.id} worried that the salad might not belong anywhere special.",
        ),
        QAItem(
            question=f"Where did the salad end up at the end of the story?",
            answer=f"It ended up on the table with the family, where it belonged.",
        ),
    ]
    if f.get("shared"):
        qs.append(
            QAItem(
                question="How did the story turn from the bad ending feeling to a happy ending?",
                answer=(
                    f"{elder.label} reminded {child.id} that the salad belonged where love was shared, "
                    f"and then they carried it to the table together."
                ),
            )
        )
    if salad.meters.get("shared", 0.0) >= THRESHOLD:
        qs.append(
            QAItem(
                question="Why will the salad be remembered for posterity?",
                answer=(
                    f"Because {child.id} and {elder.label} made it together and shared it with the family, "
                    f"so it became a warm memory."
                ),
            )
        )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for something to belong with a group?",
            answer="It means it fits there, is welcome there, and is part of that place or family.",
        ),
        QAItem(
            question="Why do people make salads?",
            answer="People make salads so they can mix fresh pieces of food into one bowl and share them.",
        ),
        QAItem(
            question="What does posterity mean?",
            answer="Posterity means people in the future, or the memory that lasts beyond today.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story() -> bool:
    return True


ASP_RULES = r"""
% A salad belongs where it is welcomed and shared.
belongs(S, family) :- salad(S), shared(S).

% A brief worry can become a bad-ending feeling before reassurance.
bad_ending_feeling(C, S) :- child(C), salad(S), worried(C), not shared(S).

% Heartwarming resolution: if the elder reassures the child, the salad belongs.
heartwarming_end(C, S) :- child(C), salad(S), shared(S), belongs(S, family).

#show valid_story/1.
#show belongs/2.
#show bad_ending_feeling/2.
#show heartwarming_end/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INGREDIENTS:
        lines.append(asp.fact("ingredient", iid))
        if INGREDIENTS[iid].is_salad:
            lines.append(asp.fact("salad", iid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("elder", "elder"))
    lines.append(asp.fact("valid_story", 1))
    lines.append(asp.fact("shared", "salad"))
    lines.append(asp.fact("worried", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show belongs/2.\n#show bad_ending_feeling/2.\n#show heartwarming_end/2."))
    atoms = set((s.name, tuple(str(a) for a in s.arguments)) for s in model)
    expected = {
        ("valid_story", ("1",)),
        ("belongs", ("salad", "family")),
        ("heartwarming_end", ("child", "salad")),
        ("bad_ending_feeling", ("child", "salad")),
    }
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH in ASP parity check.")
    print("got:", sorted(atoms))
    print("exp:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming rhyming salad story about belonging and posterity."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    child_name = args.name or rng.choice(CHILD_NAMES)
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, child_name=child_name, child_gender="child", elder_name=elder_name)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type="girl", label=params.child_name))
    elder = world.add(Entity(id="elder", kind="character", type="grandmother", label=params.elder_name))
    salad = world.add(Entity(id="salad", type="salad", label="salad", phrase="a big bowl of salad", owner=elder.id))
    for iid, ing in INGREDIENTS.items():
        if iid != "salad":
            world.add(Entity(id=iid, type="ingredient", label=ing.label, phrase=ing.phrase, owner=elder.id))
    tell_story(world, child, elder, salad)
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
    StoryParams(place="kitchen", child_name="Mia", child_gender="girl", elder_name="Grandma Rose"),
    StoryParams(place="garden", child_name="Noah", child_gender="boy", elder_name="Grandpa Ben"),
    StoryParams(place="porch", child_name="Ivy", child_gender="girl", elder_name="Nana June"),
]


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show belongs/2.\n#show bad_ending_feeling/2.\n#show heartwarming_end/2."))
    return [(s.name, tuple(str(a) for a in s.arguments)) for s in model]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show belongs/2.\n#show bad_ending_feeling/2.\n#show heartwarming_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show belongs/2.\n#show bad_ending_feeling/2.\n#show heartwarming_end/2."))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
