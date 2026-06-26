#!/usr/bin/env python3
"""
A bedtime-story world about a tiny misunderstanding, a bad ending, and a sweet
reconciliation around an outlandish piece of toffee.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit kitchen"
    indoors: bool = True


@dataclass
class Sweet:
    label: str
    phrase: str
    mess: str
    sticky: bool = True


@dataclass
class CharacterSpec:
    name: str
    type: str
    trait: str


@dataclass
class StoryParams:
    sweet: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]


SWEETS = {
    "toffee": Sweet(
        label="toffee",
        phrase="an outlandish lump of toffee wrapped in silver paper",
        mess="sticky",
    ),
    "toffee-crown": Sweet(
        label="toffee-crown",
        phrase="a sparkling toffee crown",
        mess="sticky",
    ),
}

NAMES = {
    "girl": ["Mina", "Luna", "Tilly", "Mara", "Nora"],
    "boy": ["Owen", "Theo", "Milo", "Robin", "Finn"],
}
TRAITS = ["gentle", "curious", "sleepy", "brave", "small"]

SETTINGS = {
    "kitchen": Setting(place="the moonlit kitchen", indoors=True),
}

CURATED = [
    StoryParams(sweet="toffee", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(sweet="toffee", name="Owen", gender="boy", parent="father", trait="curious"),
]


def _touch_sticky(world: World, actor: Entity, sweet: Sweet) -> None:
    actor.meters[sweet.mess] = actor.meters.get(sweet.mess, 0.0) + 1.0


def _reconcile(world: World, child: Entity, parent: Entity, sweet: Entity) -> None:
    child.memes["sad"] = 0.0
    child.memes["warmth"] = child.memes.get("warmth", 0.0) + 1.0
    parent.memes["warmth"] = parent.memes.get("warmth", 0.0) + 1.0
    sweet.meters["shared"] = 1.0


def tell(setting: Setting, sweet: Sweet, hero_name: str, hero_type: str, trait: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    candy = world.add(Entity(
        id="toffee",
        kind="thing",
        type="toffee",
        label=sweet.label,
        phrase=sweet.phrase,
        owner=child.id,
    ))

    child.memes["love"] = 1.0
    child.memes["hope"] = 1.0

    world.say(f"{child.id} was a {trait} little {hero_type} who loved the quiet of {setting.place}.")
    world.say(f"One evening, {child.id} found {sweet.phrase} and held it like a treasure.")
    world.say(f"{child.id} thought it was a toy, because it looked so outlandish and shiny.")
    world.para()
    world.say(f"At bedtime, {child.id} wanted to keep the toffee close, but {parent.pronoun('possessive')} {parent.label or 'mom'} worried.")
    world.say(f'"Please do not bite it yet," {parent.pronoun()} said softly. "It is for tomorrow."')
    world.say(f"{child.id} did not understand. {child.pronoun().capitalize()} thought the warning meant the sweet was being taken away.")
    child.memes["misunderstanding"] = 1.0
    parent.memes["sad"] = 1.0
    world.para()
    world.say(f"So {child.id} tried to cope by hiding the toffee under a pillow, and that made a bad ending for the night.")
    world.say("The silver paper crinkled, the toffee warmed, and a sticky patch appeared on the sheets.")
    _touch_sticky(world, child, sweet)
    child.memes["bad_ending"] = 1.0
    parent.meters["work"] = parent.meters.get("work", 0.0) + 1.0
    world.say(f"The parent sighed, not angry, just tired from the extra cleaning and the sad mix-up.")
    world.para()
    world.say(f"Then the parent knelt beside the bed and spoke with a calm voice.")
    world.say(f'"I was not saying no forever," {parent.pronoun()} said. "I was trying to save the toffee for a sweet morning."')
    child.memes["misunderstanding"] = 0.0
    world.say(f"{child.id} blinked, then understood. The strange little mystery had been a promise all along.")
    world.say(f"{child.id} hugged {parent.pronoun('object')} and promised to help make it right.")
    _reconcile(world, child, parent, candy)
    world.say(f"Together they changed the sheets, wrapped the toffee neatly, and set it on the table for sunrise.")
    world.say(f"In the end, {child.id} fell asleep feeling warm, and the outlandish toffee waited politely for morning.")

    world.facts.update(
        child=child,
        parent=parent,
        sweet=candy,
        sweet_cfg=sweet,
        setting=setting,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sweet = f["sweet_cfg"]
    return [
        f'Write a bedtime story about a little {child.type} and an outlandish piece of {sweet.label}.',
        f"Tell a gentle story where {child.id} misunderstands a sweet treasure, has a bad ending, and then reconciles with {f['parent'].label or 'the parent'}.",
        f'Write a cozy story that uses the word "outlandish" and ends with peace after a toffee mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    sweet_cfg: Sweet = f["sweet_cfg"]
    sweet: Entity = f["sweet"]
    return [
        QAItem(
            question=f"What did {child.id} find in the moonlit kitchen?",
            answer=f"{child.id} found {sweet.phrase}, and it looked so outlandish that {child.pronoun()} thought it was a surprise toy.",
        ),
        QAItem(
            question=f"Why was the bedtime moment a bad ending at first?",
            answer=f"It became a bad ending because {child.id} tried to cope by hiding the toffee, and the sweet turned sticky on the bed.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label or 'the parent'} reconcile?",
            answer=f"They reconciled by talking gently, understanding the misunderstanding, and wrapping the toffee up for the morning together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the sheets were cleaned, the toffee was set aside safely, and {child.id} felt warm and sleepy instead of worried.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is toffee like?",
            answer="Toffee is a sweet candy that can be hard and sticky, so it can make a mess if it gets warm.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="Reconcile means to make peace again after a misunderstanding or a fight.",
        ),
        QAItem(
            question="What does cope mean?",
            answer="Cope means to manage a hard feeling or tricky moment as best you can.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, sweet in SWEETS.items():
        lines.append(asp.fact("sweet", sid))
        lines.append(asp.fact("mess", sid, sweet.mess))
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(S) :- sweet(S).
bad_ending(S) :- sweet(S).
reconciliation(S) :- sweet(S), misunderstanding(S), bad_ending(S).
#show misunderstanding/1.
#show bad_ending/1.
#show reconciliation/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciliation/1."))
    atoms = set(asp.atoms(model, "reconciliation"))
    py = {("toffee",), ("toffee-crown",)}
    if atoms == py:
        print("OK: ASP matches Python.")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about outlandish toffee and reconciliation.")
    ap.add_argument("--sweet", choices=SWEETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    sweet = args.sweet or rng.choice(list(SWEETS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(sweet=sweet, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["kitchen"], SWEETS[params.sweet], params.name, params.gender, params.trait, params.parent)
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


CURATED = CURATED


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reconciliation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reconciliation/1."))
        print(asp.atoms(model, "reconciliation"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
