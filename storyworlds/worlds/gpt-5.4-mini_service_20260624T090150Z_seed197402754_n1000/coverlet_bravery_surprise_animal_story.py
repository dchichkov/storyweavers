#!/usr/bin/env python3
"""
A small animal story world: a cozy coverlet, a brave little animal, and a
gentle surprise that turns into a warm ending.

Premise:
- An animal child loves a soft coverlet.
- Night or nap time brings a surprise that makes the child nervous.
- Bravery helps them face it, and the surprise becomes safe and kind.

World model:
- physical meters: comfort, cold, wet, noise, light, snug
- emotional memes: brave, surprised, worried, calm, love, trust

The story is generated from state changes, not from a frozen template.
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
    protective: bool = False
    plural: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ("comfort", "cold", "wet", "noise", "light", "snug"):
            self.meters.setdefault(k, 0.0)
        for k in ("brave", "surprised", "worried", "calm", "love", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mouse", "rabbit", "fox", "cat", "bear", "bird"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "foxboy", "dog", "cub", "puppy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the burrow"
    cozy: bool = True
    dark: bool = True


@dataclass
class Coverlet:
    id: str
    label: str
    phrase: str
    warmth: str
    covers: set[str]
    plural: bool = False


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    trigger: str
    safe: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_cold(world: World) -> list[str]:
    out = []
    child = world.facts.get("child")
    if not child:
        return out
    c = world.get(child.id)
    if c.meters["cold"] < THRESHOLD:
        return out
    if ("cold", c.id) in world.fired:
        return out
    world.fired.add(("cold", c.id))
    c.memes["worried"] += 1
    out.append(f"{c.id} shivered a little.")
    return out


def _r_coverlet(world: World) -> list[str]:
    out = []
    child = world.facts.get("child")
    coverlet = world.facts.get("coverlet")
    if not child or not coverlet:
        return out
    c = world.get(child.id)
    bl = world.get(coverlet.id)
    if bl.worn_by != c.id:
        return out
    sig = ("coverlet", c.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c.meters["comfort"] += 1
    c.meters["snug"] += 1
    c.meters["cold"] = max(0.0, c.meters["cold"] - 1)
    c.memes["calm"] += 1
    out.append(f"The coverlet wrapped {c.id} in a warm hug.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    child = world.facts.get("child")
    if not child:
        return out
    c = world.get(child.id)
    if c.memes["brave"] < THRESHOLD:
        return out
    sig = ("brave", c.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c.memes["worried"] = max(0.0, c.memes["worried"] - 1)
    c.memes["calm"] += 1
    out.append(f"{c.id} took a deep breath and stood still.")
    return out


CAUSAL_RULES = [_r_cold, _r_coverlet, _r_bravery]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def build_setting() -> Setting:
    return Setting(place="the little den", cozy=True, dark=True)


def child_names() -> list[tuple[str, str]]:
    return [("Milo", "mouse"), ("Pip", "rabbit"), ("Nora", "fox"), ("Toby", "bear")]


COVERLETS = {
    "blue": Coverlet(
        id="coverlet",
        label="coverlet",
        phrase="a soft blue coverlet",
        warmth="warm and soft",
        covers={"body"},
    ),
    "patchwork": Coverlet(
        id="coverlet",
        label="coverlet",
        phrase="a patchwork coverlet with tiny stars",
        warmth="soft and snug",
        covers={"body"},
    ),
}

SURPRISES = {
    "visitor": Surprise(
        id="surprise",
        label="surprise",
        reveal="a tiny lantern glowing at the door",
        trigger="a little tap at the den door",
        safe=True,
    ),
    "gift": Surprise(
        id="surprise",
        label="surprise",
        reveal="a basket of berries and a note",
        trigger="a soft rustle beside the pillow",
        safe=True,
    ),
}


@dataclass
class StoryParams:
    coverlet: str
    surprise: str
    name: str
    animal: str
    seed: Optional[int] = None


def validate_params(params: StoryParams) -> None:
    if params.coverlet not in COVERLETS:
        raise StoryError("Unknown coverlet choice.")
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise choice.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    world = World(build_setting())
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        traits=["little", "curious", "gentle"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type="mother" if params.animal != "bear" else "father",
        label="the parent",
    ))
    cover_def = COVERLETS[params.coverlet]
    surprise_def = SURPRISES[params.surprise]
    coverlet = world.add(Entity(
        id="coverlet",
        type="coverlet",
        label="coverlet",
        phrase=cover_def.phrase,
        owner=child.id,
        caretaker=parent.id,
        protective=True,
        covers=set(cover_def.covers),
    ))
    world.facts.update(child=child, parent=parent, coverlet=coverlet, surprise=surprise_def, setting=world.setting)

    # Act 1
    world.say(f"{child.id} was a little {child.type} who loved {coverlet.phrase}.")
    world.say(f"At {world.setting.place}, bedtime felt best when {child.id} could pull the coverlet up to {child.id}'s chin.")
    world.para()

    # Act 2
    child.meters["cold"] += 1
    child.memes["surprised"] += 1
    world.say(f"One night, {surprise_def.trigger} made {child.id} look up fast.")
    world.say(f"{child.id} had not expected it, and for a moment {child.pronoun()} felt startled and worried.")
    child.memes["worried"] += 1
    child.memes["brave"] += 1
    world.say(f"But {child.id} remembered how to be brave.")
    propagate(world)
    world.para()

    # Act 3
    world.say(f"{child.id} peeked out from the coverlet and saw {surprise_def.reveal}.")
    if surprise_def.safe:
        child.memes["trust"] += 1
        child.memes["surprised"] = max(0.0, child.memes["surprised"] - 1)
        world.say(f"It was not a scary surprise at all, just something kind waiting in the dark.")
    world.say(f"{child.id} smiled, tucked back under the coverlet, and felt snug and calm again.")

    world.facts["resolved"] = True
    world.facts["child"] = child
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sup = f["surprise"]
    return [
        f'Write a short animal story for a young child that includes the word "coverlet" and a gentle surprise.',
        f"Tell a bedtime story about {child.id} the {child.type}, a brave moment, and {sup.reveal}.",
        f"Write a cozy story where a little animal feels surprised, then uses a coverlet and bravery to feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    sup = world.facts["surprise"]
    coverlet = world.facts["coverlet"]
    return [
        QAItem(
            question=f"What did {c.id} love at bedtime?",
            answer=f"{c.id} loved {coverlet.phrase} and liked pulling the coverlet up close for warmth.",
        ),
        QAItem(
            question=f"What made {c.id} look up fast one night?",
            answer=f"{sup.trigger} made {c.id} look up fast and feel surprised.",
        ),
        QAItem(
            question=f"How did {c.id} feel after being brave?",
            answer=f"{c.id} felt calmer and snug again after being brave and staying under the coverlet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coverlet?",
            answer="A coverlet is a light blanket that you can pull over yourself to stay warm and cozy.",
        ),
        QAItem(
            question="What does brave mean?",
            answer="Brave means you keep going even when something feels a little scary or surprising.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect. It can make you look up fast or feel startled for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_worried(C) :- child(C), meme(C, worried), meme(C, surprised).
coverlet_soothes(C) :- child(C), wearing(C, coverlet), coverlet(coverlet).
brave_then_calm(C) :- child(C), meme(C, brave), coverlet_soothes(C).
resolved(C) :- brave_then_calm(C), child_worried(C).
#show resolved/1.
#show coverlet_soothes/1.
#show brave_then_calm/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "milo"))
    lines.append(asp.fact("child", "pip"))
    lines.append(asp.fact("child", "nora"))
    lines.append(asp.fact("coverlet", "coverlet"))
    lines.append(asp.fact("meme", "milo", "brave"))
    lines.append(asp.fact("meme", "milo", "surprised"))
    lines.append(asp.fact("wearing", "milo", "coverlet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show coverlet_soothes/1.\n#show brave_then_calm/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(getattr(a, "name", a) for a in sym.arguments)) for sym in model)
    expected = {("coverlet_soothes", ("milo",)), ("brave_then_calm", ("milo",)), ("resolved", ("milo",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH in ASP verification.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: coverlet, bravery, surprise.")
    ap.add_argument("--coverlet", choices=sorted(COVERLETS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=["mouse", "rabbit", "fox", "bear"])
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
    coverlet = args.coverlet or rng.choice(sorted(COVERLETS))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    animal = args.animal or rng.choice(["mouse", "rabbit", "fox", "bear"])
    name = args.name or rng.choice({"mouse": ["Milo", "Minnie"], "rabbit": ["Pip", "Poppy"], "fox": ["Nora", "Fenn"], "bear": ["Toby", "Bruno"]}[animal])
    return StoryParams(coverlet=coverlet, surprise=surprise, name=name, animal=animal)


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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show coverlet_soothes/1.\n#show brave_then_calm/1.\n#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for coverlet in sorted(COVERLETS):
            for surprise in sorted(SURPRISES):
                for animal, names in [("mouse", ["Milo"]), ("rabbit", ["Pip"]), ("fox", ["Nora"]), ("bear", ["Toby"])]:
                    params = StoryParams(coverlet=coverlet, surprise=surprise, name=names[0], animal=animal)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
