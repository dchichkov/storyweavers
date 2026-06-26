#!/usr/bin/env python3
"""
millimeter_rhyme_heartwarming.py

A small storyworld about careful measuring, a tiny rhyme, and a warm
heartwarming payoff.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> bool:
        return self.type in {"scissors", "beans", "stars"}

    def it(self) -> str:
        return "them" if self.is_plural() else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_role: str
    object_name: str
    task: str
    rhyme_word: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mina", "Owen", "Luna", "Noah", "Ivy", "Theo", "Rae", "Finn"]
HELPER_NAMES = ["Grandma", "Papa", "Auntie", "Grandpa", "Mom", "Dad"]
HELPER_ROLES = ["grandma", "grandpa", "aunt", "uncle", "mother", "father"]
OBJECTS = [
    ("ribbon", "a bright ribbon for a present"),
    ("string", "a soft string for tying a card"),
    ("paper chain", "a long paper chain for the window"),
    ("bookmark", "a handmade bookmark with a tassel"),
]
TASKS = [
    ("measure the ribbon", "measure", "measure"),
    ("cut the string", "cut", "cut"),
    ("sort the paper chain links", "sort", "sort"),
    ("line up the bookmark pieces", "line up", "line up"),
]
RHYME_WORDS = ["shine", "line", "tiny", "spry", "bright", "tight"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming millimeter rhyme storyworld.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--role", choices=HELPER_ROLES)
    ap.add_argument("--object", dest="object_name", choices=[o[0] for o in OBJECTS])
    ap.add_argument("--task", choices=[t[0] for t in TASKS])
    ap.add_argument("--rhyme", choices=RHYME_WORDS)
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
    if args.role and args.helper and args.role != args.helper.lower():
        raise StoryError("helper and role must match in this small storyworld.")
    obj_name, obj_phrase = rng.choice(OBJECTS)
    task_text, _, verb = rng.choice(TASKS)

    if args.object_name:
        for n, p in OBJECTS:
            if n == args.object_name:
                obj_name, obj_phrase = n, p
                break
    if args.task:
        for t, _, v in TASKS:
            if t == args.task:
                task_text, _, verb = t, _, v
                break

    if args.rhyme:
        rhyme = args.rhyme
    else:
        rhyme = rng.choice(RHYME_WORDS)

    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    role = args.role or rng.choice(HELPER_ROLES)
    return StoryParams(
        child_name=name,
        child_gender=gender,
        helper_name=helper,
        helper_role=role,
        object_name=obj_name,
        task=task_text,
        rhyme_word=rhyme,
    )


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper_role, label=params.helper_name))
    obj_phrase = dict(OBJECTS)[params.object_name]
    item = w.add(Entity(
        id="item",
        kind="thing",
        type=params.object_name,
        label=params.object_name,
        phrase=obj_phrase,
        owner=child.id,
        caretaker=helper.id,
    ))
    ruler = w.add(Entity(id="ruler", kind="thing", type="tool", label="ruler", phrase="a little ruler marked in millimeters"))

    # Setup
    w.say(f"{child.label} loved making little things with care.")
    w.say(f"{child.label} and {helper.label} were working on {obj_phrase}, and a tiny ruler helped them count every millimeter.")
    w.say(f"{child.label} smiled at the neat marks and whispered a rhyme: “{params.rhyme_word}, {params.rhyme_word}, nice and {params.rhyme_word}.”")
    w.para()

    # Tension
    w.say(f"Then {child.label} wanted to {params.task} all by {child.pronoun('subject').lower()}self, but the pieces were wiggly and the numbers were small.")
    w.say(f"{helper.label} said it was okay to go slowly, because even one careful millimeter could make the whole thing fit just right.")
    w.say(f"{child.label} tried again, holding the ruler steady with both hands.")
    item.meters["careful"] = 1
    item.memes["hope"] = 1
    w.para()

    # Turn / resolution
    w.say(f"The first try was a little off, so {child.label} did not give up.")
    w.say(f"{helper.label} showed where to start at zero, and together they checked each millimeter until the line was true.")
    w.say(f"At last {child.label} finished the {item.label}, and the tiny work looked lovely and strong.")
    w.say(f"{child.label} giggled and repeated the rhyme, “{params.rhyme_word}, {params.rhyme_word}, all is fine,” as {helper.label} gave a proud hug.")
    w.say(f"In the end, the small object was ready, and the warm room felt brighter because they had made it together.")

    w.facts.update(child=child, helper=helper, item=item, ruler=ruler, params=params)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a heartwarming story for a young child about using a ruler to measure in millimeters, and include the word "{p.rhyme_word}".',
        f"Tell a gentle story where {p.child_name} and {p.helper_name} work together on {p.object_name} and keep checking the millimeter marks.",
        f"Write a short story about a child who learns patience, careful measuring, and a happy rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    return [
        QAItem(
            question=f"What was {p.child_name} making with {p.helper_name}?",
            answer=f"{p.child_name} was making {item.phrase}, and they used a ruler to keep the measurements tiny and exact.",
        ),
        QAItem(
            question=f"What did {p.child_name} keep checking while working on the {item.label}?",
            answer=f"{p.child_name} kept checking the millimeter marks so the pieces would fit just right.",
        ),
        QAItem(
            question=f"How did {p.child_name} feel when the work was finished?",
            answer=f"{p.child_name} felt proud and happy, because the careful work with {helper.label} turned into something lovely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a millimeter?",
            answer="A millimeter is a very tiny unit for measuring length. It is much smaller than a centimeter.",
        ),
        QAItem(
            question="Why do people use a ruler when they measure?",
            answer="People use a ruler so they can check lengths carefully and make sure something is the right size.",
        ),
        QAItem(
            question="Why is being patient helpful when making something small?",
            answer="Being patient helps because tiny pieces are easier to fit when you go slowly and check your work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
item_ok(I) :- item(I).
careful_story :- item_ok(_), ruler(_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("item", "item"),
        asp.fact("ruler", "ruler"),
        asp.fact("millimeter", 1),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show careful_story/0."))
    ok = any(sym.name == "careful_story" for sym in model)
    if ok:
        print("OK: ASP gate can derive a careful story.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


CURATED = [
    StoryParams("Mina", "girl", "Grandma", "grandma", "ribbon", "measure the ribbon", "shine"),
    StoryParams("Owen", "boy", "Dad", "father", "bookmark", "line up the bookmark pieces", "bright"),
    StoryParams("Luna", "girl", "Auntie", "aunt", "paper chain", "sort the paper chain links", "tiny"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show careful_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
