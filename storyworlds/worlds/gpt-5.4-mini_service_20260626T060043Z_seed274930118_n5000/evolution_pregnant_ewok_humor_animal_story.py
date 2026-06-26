#!/usr/bin/env python3
"""
A small humorous animal-story world about an ewok family, a surprising
pregnancy, and an "evolution" mishap that changes how the creatures behave.

Premise:
- A young ewok wants to be brave, but the forest keeps turning ordinary plans
  into silly little problems.
- A pregnant mother needs comfort, rest, and help with a heavy chore.
- The child learns to help in a new way, which is the story's tiny "evolution":
  a change in behavior, not biology.

The world is state-driven:
- physical meters: hunger, tiredness, wobble, load, laughter, readiness
- emotional memes: worry, care, pride, mischief, relief

Humor comes from concrete, child-facing misunderstandings:
- acorns rolling underfoot
- a too-serious "evolution lesson"
- a stubborn ewok trying to invent a grand solution
- a small practical fix that ends up being funny and kind
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("hunger", "tiredness", "wobble", "load", "readiness", "warmth"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "care", "pride", "mischief", "relief", "humor", "love"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Kiri"
    parent_name: str = "Mara"
    companion_name: str = "Pip"
    place: str = "the mossy tree-home"
    activity: str = "carry the berry basket"
    concern: str = "the heavy basket"
    helper: str = "a vine sling"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] += amount


def _feel(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] += amount


def tell(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.hero_name, kind="character", type="ewok", label="ewok"))
    parent = w.add(Entity(id=params.parent_name, kind="character", type="ewok", label="mother ewok"))
    sibling = w.add(Entity(id=params.companion_name, kind="character", type="ewok", label="small ewok"))
    basket = w.add(Entity(
        id="basket",
        type="basket",
        label="berry basket",
        phrase="a berry basket full of bright red fruit",
        caretaker=parent.id,
    ))
    sling = w.add(Entity(
        id="sling",
        type="gear",
        label="vine sling",
        phrase="a soft vine sling for carrying things",
    ))

    # Setup
    hero.memes["mischief"] += 1
    parent.meters["load"] += 2
    _feel(parent, "care", 1)
    _feel(parent, "worry", 1)

    w.say(
        f"In {params.place}, {hero.id} was a little ewok with a big idea and even bigger ears."
    )
    w.say(
        f"{parent.id} was a pregnant ewok who walked slowly, one hand on her round belly, "
        f"because the baby inside made the day feel extra heavy."
    )
    w.say(
        f"{hero.id} loved to help, but mostly {hero.id} wanted to look heroic in front of {sibling.id}."
    )

    w.para()

    # Middle turn: the concern and the silly "evolution" lesson.
    _bump(hero, "hunger", 1)
    _bump(hero, "wobble", 1)
    _feel(hero, "mischief", 1)
    _feel(parent, "worry", 1)
    w.say(
        f"That morning, {parent.id} asked for help with {params.concern}, because carrying it "
        f"while pregnant made her steps slow and careful."
    )
    w.say(
        f"{hero.id} puffed out {hero.id}'s chest and said, 'I am ready for evolution!' "
        f"Then {hero.id} tried to use a stick like a fancy lifting machine."
    )
    w.say(
        f"The stick rolled away, the berries bounced, and {sibling.id} squeaked, "
        f"'That evolution has wobbly legs!'"
    )
    _feel(hero, "humor", 1)
    _feel(parent, "humor", 1)
    _bump(hero, "wobble", 1)

    w.para()

    # Turn: a practical helper appears.
    w.say(
        f"{parent.id} laughed so hard she had to sit on a stump. 'Not that kind of evolution,' "
        f"she said. 'A better way is the kind that helps.'"
    )
    w.say(
        f"She pointed to {params.helper}, and {sibling.id} tied it between two branches like a gentle swing."
    )
    sling.owner = hero.id
    sling.worn_by = hero.id
    _bump(hero, "readiness", 1)
    _feel(hero, "care", 1)
    _feel(hero, "pride", 1)

    w.para()

    # Resolution: the child grows into helpfulness.
    w.say(
        f"{hero.id} carefully slid {params.concern} into the sling and carried it without a single berry escape."
    )
    _bump(parent, "load", -1)
    _bump(parent, "warmth", 1)
    _feel(parent, "relief", 1)
    _feel(parent, "love", 1)
    _feel(hero, "relief", 1)
    _feel(hero, "love", 1)

    w.say(
        f"At the end, the baby still kicked happily inside {parent.id}, the basket stayed full, "
        f"and {hero.id} had evolved into the sort of ewok who made life lighter with two careful hands."
    )
    w.say(
        f"{sibling.id} grinned and said, 'Next time, let the giant think first and the stick rest.'"
    )

    w.facts.update(
        hero=hero,
        parent=parent,
        sibling=sibling,
        basket=basket,
        sling=sling,
        params=params,
        resolved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a humorous animal story about an ewok learning that evolution can mean improving a helpful skill.",
        f"Tell a short story where {p.hero_name} helps a pregnant mother ewok carry a berry basket.",
        "Write a gentle, funny story about a child, a berry basket, and a clever new way to help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.hero_name}, a little ewok who wanted to help in a smarter way."
        ),
        QAItem(
            question=f"Why did {parent.id} need help with the berry basket?",
            answer="Because she was pregnant, so carrying the basket was slow and heavy for her."
        ),
        QAItem(
            question=f"What did {p.hero_name} try at first?",
            answer=f"{p.hero_name} tried to use a stick like a big machine, but it only made the berries bounce."
        ),
        QAItem(
            question="How did the problem get solved?",
            answer="They used a vine sling, and the basket could be carried safely without dropping berries."
        ),
        QAItem(
            question=f"What kind of change was the 'evolution' in the story?",
            answer="It was a change in behavior: the ewok learned a better and kinder way to help."
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer="The ewok felt relieved and proud, because helping had become easier and gentler."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is an ewok in a story?",
        answer="An ewok is a small furry forest creature that can be brave, funny, and helpful."
    ),
    QAItem(
        question="What does pregnant mean?",
        answer="Pregnant means a parent is carrying a baby inside their body before the baby is born."
    ),
    QAItem(
        question="What does evolution mean in simple science words?",
        answer="Evolution means living things change slowly over a very long time, and helpful traits can spread."
    ),
    QAItem(
        question="Why might a vine sling be useful?",
        answer="A vine sling can help carry something heavy more easily, because the weight is supported."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_helped :- resolved.
funny_mistake :- mischief, not resolved.
pregnant_parent :- parent.
better_help :- resolved, hero_helped.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ewok", "hero"),
        asp.fact("ewok", "parent"),
        asp.fact("ewok", "sibling"),
        asp.fact("pregnant", "parent"),
        asp.fact("basket", "berry_basket"),
        asp.fact("tool", "vine_sling"),
        asp.fact("theme", "humor"),
        asp.fact("theme", "animal_story"),
        asp.fact("theme", "evolution"),
        asp.fact("resolved"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    ok = any(sym.name == "resolved" for sym in model)
    if ok:
        print("OK: ASP reasoner sees the story as resolved.")
        return 0
    print("MISMATCH: ASP reasoner did not see resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous ewok animal-story world.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--companion-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(["Kiri", "Tomo", "Luma", "Nebi"])
    parent = args.parent_name or rng.choice(["Mara", "Suri", "Tala", "Nima"])
    companion = args.companion_name or rng.choice(["Pip", "Boko", "Rin", "Moki"])
    return StoryParams(
        seed=args.seed,
        hero_name=hero,
        parent_name=parent,
        companion_name=companion,
    )


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
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(hero_name="Kiri", parent_name="Mara", companion_name="Pip"),
    StoryParams(hero_name="Tomo", parent_name="Suri", companion_name="Boko"),
    StoryParams(hero_name="Luma", parent_name="Tala", companion_name="Rin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print(model)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
