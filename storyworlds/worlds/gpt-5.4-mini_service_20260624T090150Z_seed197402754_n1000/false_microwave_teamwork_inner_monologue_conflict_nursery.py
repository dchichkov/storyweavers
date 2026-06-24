#!/usr/bin/env python3
"""
A tiny story world about a small false alarm around a microwave, where teamwork
and inner monologue help a child and a helper solve a conflict in a nursery-rhyme
style tale.
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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Milo"
    helper: str = "Mama"
    place: str = "kitchen"
    snack: str = "porridge"
    object_name: str = "cup"
    false_alarm: str = "the microwave was empty and still"
    rhyme_word: str = "glow"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


CHILD_NAMES = ["Milo", "Nina", "Toby", "Lily", "Pip", "Ruby", "Owen", "Ivy"]
HELPERS = ["Mama", "Papa", "Grandma", "Grandpa"]
PLACES = ["kitchen", "little kitchen", "warm kitchen"]
SNACKS = ["porridge", "peas", "oat cake", "soup", "apple slices"]
OBJECTS = ["cup", "bowl", "spoon", "plate"]
RHYME_ENDINGS = ["glow", "show", "slow", "snow", "row", "go"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a false microwave conflict and teamwork.")
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--object-name", choices=OBJECTS)
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
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(CHILD_NAMES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        snack=args.snack or rng.choice(SNACKS),
        object_name=args.object_name or rng.choice(OBJECTS),
        false_alarm="the microwave was empty and still",
        rhyme_word=rng.choice(RHYME_ENDINGS),
    )


def _child_type(name: str) -> str:
    return "girl" if name in {"Nina", "Lily", "Ruby", "Ivy"} else "boy"


def _build_world(params: StoryParams) -> World:
    world = World(place=params.place)
    child = world.add(Entity(id=params.child, kind="character", type=_child_type(params.child), label=params.child))
    helper = world.add(Entity(id=params.helper, kind="character", type="parent", label=params.helper))
    microwave = world.add(Entity(id="microwave", kind="thing", type="appliance", label="microwave", phrase="a small microwave"))
    snack = world.add(Entity(id="snack", kind="thing", type="food", label=params.snack, phrase=f"a bowl of {params.snack}"))
    obj = world.add(Entity(id=params.object_name, kind="thing", type="thing", label=params.object_name, phrase=f"a little {params.object_name}"))

    child.memes["worry"] = 0.0
    child.memes["conflict"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["joy"] = 0.0
    helper.memes["care"] = 1.0
    microwave.meters["still"] = 1.0
    snack.meters["warm"] = 0.0
    obj.meters["safe"] = 1.0

    world.say(
        f"In the {world.place} so neat, with a tap-tap tune and tidy beat, "
        f"{params.child} saw {params.helper} and a {params.snack} so sweet."
    )
    world.say(
        f"{params.child} wished to warm it fast, by the microwave in the corner cast, "
        f"and hummed a plan to make it last."
    )

    world.para()
    world.say(
        f"{params.child} thought, 'Oh dear, oh me, what if {params.false_alarm}? "
        f"That would not be right for tea.'"
    )
    child.memes["worry"] += 1.0
    child.memes["inner_monologue"] = 1.0
    world.say(
        f"{params.child} stood still and frowned a bit, while {params.helper} heard the worry fit."
    )

    child.memes["conflict"] += 1.0
    world.para()
    world.say(
        f"'I want the snack made warm,' {params.child} said, 'but I feel a storm inside my head.'"
    )
    world.say(
        f"{params.helper} smiled and knelt right down: 'Let's check it first, you thoughtful noun.'"
    )
    world.say(
        f"They looked together, two by two, and found the microwave was false in view: "
        f"it was empty, quiet, safe, and true."
    )

    snack.meters["warm"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["conflict"] = 0.0
    child.memes["joy"] += 1.0
    child.memes["hope"] += 1.0
    world.facts.update(
        child=child,
        helper=helper,
        microwave=microwave,
        snack=snack,
        object=obj,
        false_alarm=params.false_alarm,
        rhyme_word=params.rhyme_word,
        resolved=True,
    )

    world.para()
    world.say(
        f"Then teamwork made the moment bright: {params.helper} held the bowl just right, "
        f"and {params.child} watched the steam take flight."
    )
    world.say(
        f"{params.child} took a spoon and gave a cheer; the little {params.object_name} stayed near, "
        f"and the warm {params.snack} smelled cozy and dear."
    )
    world.say(
        f"So down went doubt, and up went song, and {params.child} and {params.helper} hummed along; "
        f"the kitchen glowed and the day felt long and strong."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story about a child named {f['child'].id} who has a false worry about a microwave.",
        f"Tell a gentle story in a kitchen where {f['child'].id} and {f['helper'].id} use teamwork to fix a conflict.",
        f"Write a short rhyme with the words false and microwave, ending in a warm and happy scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    snack = f["snack"]
    microwave = f["microwave"]
    return [
        QAItem(
            question=f"What was {child.id} worried about in the kitchen?",
            answer=f"{child.id} had a false worry that the microwave was empty and still, so {child.pronoun('subject')} felt confused at first.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} solve the problem?",
            answer=f"They used teamwork. {helper.id} helped {child.id} check the microwave, and that calmed the conflict.",
        ),
        QAItem(
            question=f"What happened to the {snack.label} at the end?",
            answer=f"The {snack.label} was warmed safely, and everyone enjoyed it together.",
        ),
        QAItem(
            question=f"Why did the story stop being tense?",
            answer=f"The conflict ended when the child saw that the microwave was safe, so worry changed into joy.",
        ),
        QAItem(
            question=f"What did they learn about the microwave?",
            answer=f"They learned that a microwave should be checked carefully before guessing, because a false thought can cause worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a microwave?",
            answer="A microwave is a kitchen machine that heats food quickly by using energy inside a closed box.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together so it becomes easier and kinder.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a person does inside their own mind while they think.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem where feelings or wishes do not match and people need to work it out.",
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_worries(C) :- child(C), false_alarm(C).
teamwork(C,H) :- child(C), helper(H), resolve_together(C,H).
conflict(C) :- child(C), child_worries(C).
resolved(C) :- conflict(C), teamwork(C,_).
#show child_worries/1.
#show conflict/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "milo"),
        asp.fact("helper", "mama"),
        asp.fact("false_alarm", "milo"),
        asp.fact("resolve_together", "milo", "mama"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((s.name, tuple(a.string if a.type.name == "String" else a.number if a.type.name == "Number" else a.name for a in s.arguments)) for s in model)
    expected = {
        ("child_worries", ("milo",)),
        ("conflict", ("milo",)),
        ("resolved", ("milo",)),
    }
    if atoms == expected:
        print("OK: ASP and Python reasoning agree.")
        return 0
    print("MISMATCH:")
    print("actual:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams(child="Milo", helper="Mama", place="kitchen", snack="porridge", object_name="cup", false_alarm="the microwave was empty and still", rhyme_word="glow"),
    StoryParams(child="Nina", helper="Grandma", place="warm kitchen", snack="soup", object_name="bowl", false_alarm="the microwave was too loud and wild", rhyme_word="slow"),
    StoryParams(child="Toby", helper="Papa", place="little kitchen", snack="oat cake", object_name="plate", false_alarm="the microwave might bite the cake", rhyme_word="show"),
]


def resolve_combo_constraints(args: argparse.Namespace) -> None:
    pass


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "child_worries"))
        print(asp.atoms(model, "conflict"))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = StoryParams(
                seed=seed,
                child=args.child or rng.choice(CHILD_NAMES),
                helper=args.helper or rng.choice(HELPERS),
                place=args.place or rng.choice(PLACES),
                snack=args.snack or rng.choice(SNACKS),
                object_name=args.object_name or rng.choice(OBJECTS),
                false_alarm="the microwave was empty and still",
                rhyme_word=rng.choice(RHYME_ENDINGS),
            )
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
