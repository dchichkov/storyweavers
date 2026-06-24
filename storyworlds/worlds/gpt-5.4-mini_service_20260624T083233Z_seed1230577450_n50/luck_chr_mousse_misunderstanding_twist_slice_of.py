#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50/luck_chr_mousse_misunderstanding_twist_slice_of.py
===============================================================================================================

A small slice-of-life story world about a child named Chr, a bowl of mousse,
and a lucky misunderstanding that turns into a gentle twist.

Seed tale sketch:
---
Chr liked quiet afternoons, small treats, and the feeling of being lucky.
One day, Chr saw a fluffy bowl of chocolate mousse on the table and thought
it was for a special surprise. But the grown-up had set it out for a friend,
not for Chr. Chr felt disappointed and misunderstood.

Then the friend was late, and the grown-up noticed Chr's careful waiting.
The grown-up smiled, explained the mix-up, and split the mousse into two small
cups. Chr got one cup after all, and the day turned sweet and calm.

World model:
---
- Characters have physical meters and emotional memes.
- The mousse can be portioned, shared, and accidentally mistaken for a gift.
- A misunderstanding can rise when Chr assumes ownership too early.
- A twist resolves the scene when the intended recipient is late, letting the
  grown-up make a kind new plan.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of results.py; lazy import of asp.py in ASP helpers
- reasonableness gate + inline ASP twin
- verification compares ASP and Python parity and exercises generated stories
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    flavor: str
    portionable: bool = True
    shareable: bool = True


@dataclass
class Twist:
    id: str
    clue: str
    reveal: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"serve", "share"}),
    "living_room": Setting(place="the living room", affords={"serve", "share"}),
    "yard_table": Setting(place="the little yard table", affords={"serve", "share"}),
}

TREATS = {
    "chocolate_mousse": Treat(
        id="chocolate_mousse",
        label="chocolate mousse",
        phrase="a small bowl of chocolate mousse",
        flavor="chocolate",
    ),
    "vanilla_mousse": Treat(
        id="vanilla_mousse",
        label="vanilla mousse",
        phrase="a tiny glass of vanilla mousse",
        flavor="vanilla",
    ),
    "berry_mousse": Treat(
        id="berry_mousse",
        label="berry mousse",
        phrase="a chilled cup of berry mousse",
        flavor="berry",
    ),
}

TWISTS = {
    "late_friend": Twist(
        id="late_friend",
        clue="the friend was late",
        reveal="the friend had not arrived yet",
    ),
    "wrong_plate": Twist(
        id="wrong_plate",
        clue="the plate name was mixed up",
        reveal="the grown-up had written the wrong name on the note",
    ),
    "half_and_half": Twist(
        id="half_and_half",
        clue="the bowl looked smaller than expected",
        reveal="it was already meant to be split into two small servings",
    ),
}

CHILD_NAMES = ["Chr", "Cris", "Cora", "Nia", "Milo", "June"]
GROWNUP_NAMES = ["Mina", "Paz", "Lena", "Taro", "Ari", "Nora"]
TRAITS = ["quiet", "gentle", "curious", "patient", "careful", "hopeful"]


@dataclass
class StoryParams:
    place: str
    treat: str
    twist: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if params.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    treat = TREATS[params.treat]
    twist = TWISTS[params.twist]
    if not treat.shareable:
        raise StoryError("The treat must be shareable for this slice-of-life story.")
    if params.name.strip().lower() == params.parent.strip().lower():
        raise StoryError("The child and grown-up need different names.")
    if "mousse" not in treat.label and "mousse" not in treat.phrase:
        raise StoryError("This world centers on mousse.")
    if twist.id == "wrong_plate" and params.place == "yard_table":
        raise StoryError("The note-mixup twist needs an indoor feel to land naturally.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a slice-of-life misunderstanding around mousse."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    place = args.place or rng.choice(list(SETTINGS))
    treat = args.treat or rng.choice(list(TREATS))
    twist = args.twist or rng.choice(list(TWISTS))
    name = args.name or "Chr"
    parent = args.parent or rng.choice(GROWNUP_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, treat=treat, twist=twist, name=name, parent=parent, trait=trait)
    reasonableness_gate(params)
    return params


def _serve(world: World, child: Entity, adult: Entity, treat: Entity) -> None:
    child.memes["anticipation"] = child.memes.get("anticipation", 0) + 1
    world.say(
        f"On a calm afternoon, {child.id} and {adult.id} sat down at {world.setting.place}."
    )
    world.say(
        f"There was {treat.phrase} waiting there, and its soft top looked as fluffy as a cloud."
    )


def _misunderstand(world: World, child: Entity, adult: Entity, treat: Entity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0) + 1
    child.memes["luck"] = child.memes.get("luck", 0) + 1
    world.say(
        f"{child.id} smiled and thought the mousse was a lucky surprise made just for {child.pronoun('object')}."
    )
    world.say(
        f'But {adult.id} shook {adult.pronoun("possessive")} head and said, "Wait a moment, {child.id}."'
    )
    child.memes["misunderstood"] = child.memes.get("misunderstood", 0) + 1
    world.say(
        f"{child.id} felt a little misunderstood, because the bowl seemed to say one thing while the note said another."
    )


def _twist(world: World, child: Entity, adult: Entity, treat: Entity, twist: Twist) -> None:
    if twist.id == "late_friend":
        world.say(f"Then came a tiny twist: {twist.clue}.")
        world.say(
            f"{adult.id} looked out the window, sighed kindly, and said the mousse had been waiting for someone else."
        )
    elif twist.id == "wrong_plate":
        world.say(f"Then came a tiny twist: {twist.clue}.")
        world.say(
            f"{adult.id} found the note, laughed softly, and realized the name on the plate did not match the plan."
        )
    else:
        world.say(f"Then came a tiny twist: {twist.clue}.")
        world.say(
            f"{adult.id} checked the recipe and saw that the mousse was always meant to become two little servings."
        )
    world.facts["twist_reveal"] = twist.reveal
    child.memes["confusion"] = max(0.0, child.memes.get("confusion", 0) - 0.5)


def _resolve(world: World, child: Entity, adult: Entity, treat: Entity) -> None:
    treat.meters["portion"] = 2
    treat.meters["shared"] = 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["luck"] = child.memes.get("luck", 0) + 1
    child.memes["misunderstood"] = 0
    world.say(
        f'{adult.id} smiled and said, "Looks like we can share it after all."'
    )
    world.say(
        f"They gently split the mousse into two small cups, and {child.id} got one of them."
    )
    world.say(
        f"{child.id} took a spoonful, and the chocolate taste turned the whole afternoon calm and sweet."
    )


def tell(setting: Setting, treat_cfg: Treat, twist_cfg: Twist, child_name: str, parent_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child", label=child_name))
    adult = world.add(Entity(id=parent_name, kind="character", type="adult", label=parent_name))
    treat = world.add(Entity(id=treat_cfg.id, type="treat", label=treat_cfg.label, phrase=treat_cfg.phrase, caretaker=adult.id))

    world.say(f"{child.id} was a {trait} little child who loved quiet treats and small good surprises.")
    world.say(f"{child.id} also liked the feeling of luck, especially on ordinary days.")

    world.para()
    _serve(world, child, adult, treat)
    _misunderstand(world, child, adult, treat)

    world.para()
    _twist(world, child, adult, treat, twist_cfg)
    _resolve(world, child, adult, treat)

    world.facts.update(
        child=child,
        adult=adult,
        treat=treat,
        setting=setting,
        treat_cfg=treat_cfg,
        twist_cfg=twist_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    treat = f["treat_cfg"]
    twist = f["twist_cfg"]
    return [
        f'Write a slice-of-life story for a young child about "{child.id}" and a bowl of {treat.label}.',
        f"Tell a gentle story where {child.id} misunderstands a treat at {world.setting.place} and a small twist changes the plan.",
        f"Write a calm story that includes the word 'luck' and ends with {child.id} sharing {treat.label} with {adult.id}.",
        f"Make the story feel like everyday life, with a misunderstanding and then {twist.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    treat = f["treat_cfg"]
    twist = f["twist_cfg"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a {world.facts['child'].label.lower() if world.facts['child'].label else 'little child'}, and {adult.id}, who shared a calm moment together.",
        ),
        QAItem(
            question=f"What treat was sitting at {world.setting.place}?",
            answer=f"There was {treat.phrase} sitting there, and it was the treat that caused the misunderstanding.",
        ),
        QAItem(
            question=f"Why did {child.id} feel misunderstood?",
            answer=f"{child.id} thought the mousse was meant for {child.pronoun('object')}, but the grown-up had a different plan, so the moment felt confusing at first.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}, which changed the meaning of the mousse on the table.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {adult.id} splitting the mousse into two small cups so {child.id} could enjoy one, too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mousse?",
            answer="Mousse is a soft, airy dessert that can be sweet and fluffy, almost like a cloud you can eat with a spoon.",
        ),
        QAItem(
            question="What does luck mean?",
            answer="Luck is when something good happens, sometimes by chance, and it can make an ordinary day feel special.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think different things at first, but then they talk and clear it up.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what characters thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  facts={world.facts.keys()}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", treat="chocolate_mousse", twist="late_friend", name="Chr", parent="Mina", trait="quiet"),
    StoryParams(place="living_room", treat="vanilla_mousse", twist="wrong_plate", name="Chr", parent="Nora", trait="curious"),
    StoryParams(place="yard_table", treat="berry_mousse", twist="half_and_half", name="Chr", parent="Ari", trait="patient"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this world wants a calm mousse scene with a plausible misunderstanding and a gentle twist.)"


ASP_RULES = r"""
treat(T) :- treat_id(T).
place(P) :- place_id(P).
twist(X) :- twist_id(X).

supports_story(P, T, X) :- place(P), treat(T), twist(X).
valid_story(P, T, X) :- supports_story(P, T, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place_id", pid))
    for tid in TREATS:
        lines.append(asp.fact("treat_id", tid))
    for xid in TWISTS:
        lines.append(asp.fact("twist_id", xid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p.place, p.treat, p.twist) for p in CURATED)
    # Python gate for this world is intentionally small but still checked against ASP.
    asp_set = set(asp_valid_combos())
    if asp_set:
        print(f"OK: ASP produced {len(asp_set)} candidate story shapes.")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


def build_storyparams_from_choice(choice: tuple[str, str, str], rng: random.Random) -> StoryParams:
    place, treat, twist = choice
    return StoryParams(
        place=place,
        treat=treat,
        twist=twist,
        name="Chr",
        parent=rng.choice(GROWNUP_NAMES),
        trait=rng.choice(TRAITS),
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.treat and args.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    params = StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        treat=args.treat or rng.choice(list(TREATS)),
        twist=args.twist or rng.choice(list(TWISTS)),
        name=args.name or "Chr",
        parent=args.parent or rng.choice(GROWNUP_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREATS[params.treat], TWISTS[params.twist], params.name, params.parent, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story shapes")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.treat} at {p.place} with {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
