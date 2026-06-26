#!/usr/bin/env python3
"""
A small storyworld about a community garden, a surprise, and a happy ending.

The seed premise:
- A shy helper comes to the community garden for a quiet audit of the planting beds.
- Something ghostly and surprising appears at dusk.
- The helper learns the "haunting" is just a kind old neighbor and a hidden garden arc
  of clues that leads to a shared lantern party.
- The ending is warm, not scary.

This world keeps the tone gently ghost-story-like while staying child-facing.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the community garden"
    dusk: bool = True
    season: str = "autumn"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    surprise: str
    explains: str
    meme_delta: float = 1.0


@dataclass
class StoryParams:
    clue: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


CLUES = {
    "lantern": Clue(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern with a little star cut in it",
        surprise="a soft glow blinked on near the bean poles",
        explains="the light came from a lantern the neighbor had hidden for the evening walk",
    ),
    "scarecrow": Clue(
        id="scarecrow",
        label="scarecrow",
        phrase="a tiny scarecrow with a crooked hat",
        surprise="a tall shadow waved from the compost corner",
        explains="the 'ghost' was only a scarecrow moved by the wind",
    ),
    "keys": Clue(
        id="keys",
        label="garden keys",
        phrase="a jangling ring of old garden keys",
        surprise="a jingling sound rang out by the shed",
        explains="the ghostly jingle came from keys in a pocket",
    ),
    "sprout": Clue(
        id="sprout",
        label="sprout map",
        phrase="a folded map full of sprout marks and arrows",
        surprise="a paper trail fluttered under the zinnias",
        explains="the marks showed where the shared seeds had been planted",
    ),
}

NAMES = ["Mina", "Toby", "June", "Pia", "Eli", "Noah", "Zara", "Ari"]
ROLES = ["helper", "volunteer", "gardener", "checker"]
HELPERS = ["neighbor", "grandma", "old gardener", "librarian"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue for this garden story.")
    if not params.name:
        raise StoryError("A child name is required.")
    if not params.role:
        raise StoryError("A role is required.")


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    clue = CLUES[params.clue]
    item = world.add(Entity(
        id="clue_item",
        kind="thing",
        type=clue.id,
        label=clue.label,
        phrase=clue.phrase,
        owner=helper.id,
    ))

    child.memes["curiosity"] = 2.0
    child.memes["worry"] = 1.0
    child.memes["hope"] = 0.0

    world.say(
        f"At the community garden, {child.id} came just after supper for an audit of the beds."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} carried a small notebook and looked at the rows of beans, mint, and roses."
    )
    world.say(
        f"'{child.pronoun('subject').capitalize()} will check what is growing,' {child.pronoun('subject')} whispered, "
        f"because the garden felt quiet in the dusk."
    )

    world.para()
    world.say(
        f"Then came the surprise: {clue.surprise}."
    )
    child.meters["startled"] = 1.0
    child.memes["worry"] += 1.5
    world.say(
        f"A pale shape seemed to float between the tomato cages, and {child.id} nearly shut {child.pronoun('possessive')} notebook."
    )
    world.say(
        f"'A ghost,' {child.id} breathed."
    )

    world.para()
    world.say(
        f"But the trail led on, one clue at a time, like a little arc through the garden."
    )
    world.say(
        f"First there was {item.phrase}, and then a tiny sound, and then a warm voice from behind the sunflowers."
    )
    world.say(
        f"It was only {helper.label_word if hasattr(helper, 'label_word') else helper.label}, who had been checking the beds before the night wind came up."
    )
    world.say(
        f"The mystery was not scary at all: {clue.explains}."
    )

    child.memes["worry"] = 0.0
    child.memes["hope"] += 2.0
    child.memes["delight"] = 2.0
    child.meters["steps"] = 3.0

    world.para()
    world.say(
        f"{child.id} laughed so hard {child.pronoun('subject')} had to lean on the watering can."
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} smiled and showed {child.pronoun('object')} the rest of the hidden path: seed packets, fresh mulch, and a little sign for the lantern walk."
    )
    world.say(
        f"Together they finished the audit, and the garden looked safe, neat, and ready."
    )
    world.say(
        f"By the end, the 'ghost' was just a friendly helper, the surprise had turned into a game, and the community garden glowed with a happy ending."
    )

    world.facts.update(
        child=child,
        helper=helper,
        clue=clue,
        item=item,
        setting=world.setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly ghost story set in a community garden that includes an audit, a surprise, and a happy ending.',
        f"Tell a gentle story where {f['child'].id} visits the community garden at dusk to audit the beds and finds a spooky surprise.",
        f"Write a short story about a garden clue that seems ghostly at first but ends with everyone feeling safe and happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question=f"Where did {child.id} go to do the audit?",
            answer=f"{child.id} went to the community garden to check the beds and make sure everything was in good shape.",
        ),
        QAItem(
            question=f"What was the surprising thing {child.id} saw first?",
            answer=f"{child.id} first saw {clue.surprise}, which made the garden seem ghostly for a moment.",
        ),
        QAItem(
            question=f"Who turned out to be behind the spooky surprise?",
            answer=f"It turned out to be {helper.label}, a friendly helper, not a real ghost.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because the scary-looking clue was explained, the audit was finished, and everyone in the community garden felt safe and cheerful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared place where neighbors grow flowers, vegetables, and herbs together.",
        ),
        QAItem(
            question="What is an audit?",
            answer="An audit is a careful check to see whether things are in order.",
        ),
        QAItem(
            question="Why can dusk feel spooky?",
            answer="Dusk can feel spooky because the light is fading and shadows can look strange.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light, so people can see better when it is dark.",
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class ASPItem:
    pass


ASP_RULES = r"""
#show valid/1.
valid(clue(C)) :- clue(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story garden world with an audit and a surprise.")
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice(sorted(CLUES))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    helper = args.helper or rng.choice(HELPERS)
    params = StoryParams(clue=clue, name=name, role=role, helper=helper)
    reasonableness_gate(params)
    return params


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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {("clue", cid) for cid in CLUES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry ({len(clingo_set)} clues).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(clue="lantern", name="Mina", role="checker", helper="neighbor"),
    StoryParams(clue="scarecrow", name="Toby", role="helper", helper="old gardener"),
    StoryParams(clue="keys", name="June", role="volunteer", helper="grandma"),
    StoryParams(clue="sprout", name="Ari", role="gardener", helper="librarian"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} ASP-valid clues:")
        for v in vals:
            print(" ", v[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
