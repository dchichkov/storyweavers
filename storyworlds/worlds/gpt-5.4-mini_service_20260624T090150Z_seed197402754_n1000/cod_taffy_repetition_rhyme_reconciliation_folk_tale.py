#!/usr/bin/env python3
"""
A small folk-tale story world about cod, taffy, repetition, rhyme, and
reconciliation.

Seed tale:
---
In a little seaside village, a child named Nia loved to carry a bright red basket
to the dock. The basket held two treats from the market: a silver cod wrapped in
paper, and a string of sticky taffy.

Nia's friend Bram wanted to trade the cod for the taffy. Nia said no, because the
cod was for supper and the taffy was for the festival. Bram kept asking again and
again, in the way of a stubborn child. The more he asked, the more the basket
wobbled near the water.

Then Nana came down the lane, singing a little rhyme about sharing fish and
sweetness: "Cod for the table, taffy for the tongue; one for the elders, one for
the young." She suggested they split the taffy, save the cod, and each bring a
little gift to the festival.

Bram apologized. Nia smiled. Together they carried the basket home, and the
evening ended with cod on the plate and taffy in two neat halves.

Causal shape:
- repetition raises insistence and tension
- rhyme lowers tension by offering a memorable shared rule
- reconciliation resolves the argument and proves the new arrangement
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
class Setting:
    place: str = "the harbor lane"
    feature: str = "seawall"


@dataclass
class World:
    setting: Setting
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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child: str
    friend: str
    elder: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor lane", feature="sea wall"),
    "cove": Setting(place="the little cove", feature="stone pier"),
    "village": Setting(place="the salt village", feature="wooden dock"),
}

CHILDREN = [
    ("Nia", "girl"),
    ("Milo", "boy"),
    ("Lena", "girl"),
    ("Tobin", "boy"),
]

FRIENDS = [
    ("Bram", "boy"),
    ("Iris", "girl"),
    ("Perrin", "boy"),
    ("Mara", "girl"),
]

ELDERS = [
    ("Nana", "woman"),
    ("Grandpa Otis", "man"),
    ("Aunt Nell", "woman"),
]

# "cod" and "taffy" are the core seed words.
COD = Entity(
    id="cod",
    kind="thing",
    type="fish",
    label="cod",
    phrase="a silver cod wrapped in paper",
    owner="child",
    caretaker="elder",
)

TAFFY = Entity(
    id="taffy",
    kind="thing",
    type="sweet",
    label="taffy",
    phrase="a string of sticky taffy",
    owner="child",
    caretaker="elder",
)

RHYME_LINES = [
    "Cod for the table, taffy for the tongue.",
    "One for the elders, one for the young.",
    "Share the sweet and save the fish,",
    "Then every heart gets half a wish.",
]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale story world about cod, taffy, repetition, rhyme, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--friend")
    ap.add_argument("--elder")
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
    child = args.child or rng.choice(CHILDREN)[0]
    friend = args.friend or rng.choice([x for x in FRIENDS if x[0] != child])[0]
    elder = args.elder or rng.choice(ELDERS)[0]
    place = args.place or rng.choice(list(SETTINGS))
    if child == friend:
        raise StoryError("The child and the friend must be different people.")
    return StoryParams(place=place, child=child, friend=friend, elder=elder)


def _gender_for_name(name: str) -> str:
    for n, g in CHILDREN + FRIENDS:
        if n == name:
            return g
    for n, g in ELDERS:
        if n == name:
            return g
    return "person"


def make_world(params: StoryParams) -> World:
    w = World(SETTINGS[params.place])
    child = w.add(Entity(id=params.child, kind="character", type=_gender_for_name(params.child)))
    friend = w.add(Entity(id=params.friend, kind="character", type=_gender_for_name(params.friend)))
    elder = w.add(Entity(id=params.elder, kind="character", type=_gender_for_name(params.elder)))
    cod = w.add(Entity(**{**COD.__dict__}))
    taffy = w.add(Entity(**{**TAFFY.__dict__}))

    # setup
    w.say(f"Long ago, in {w.setting.place}, there lived a child named {child.id}.")
    w.say(f"{child.id} loved the little market basket that held {cod.label} and {taffy.label}.")
    w.say(f"{friend.id} often came by to share stories at the {w.setting.feature}.")

    # tension with repetition
    w.para()
    w.say(f"One day, {friend.id} said, \"Let me have the {taffy.label}.\"")
    w.say(f"{child.id} said no, for the {cod.label} was for supper and the {taffy.label} was for the festival.")
    w.say(f"Again and again, {friend.id} asked for the {taffy.label}, and again and again {child.id} held the basket close.")
    child.memes["firm"] = 1
    friend.memes["wanting"] = 2
    child.memes["worry"] = 1
    friend.memes["tension"] = 1
    cod.meters["safe"] = 1
    taffy.meters["sticky"] = 1

    # consequence
    w.say(f"The basket wobbled near the water, and the air grew tight like a closed knot.")
    child.meters["risk"] = 1
    friend.meters["insistence"] = 1

    # rhyme and reconciliation
    w.para()
    w.say(f"Then {elder.id} came walking down the lane, smiling kindly.")
    w.say(f"{elder.id} sang a little rhyme:")
    for line in RHYME_LINES:
        w.say(f"“{line}”")
    w.say(f"The rhyme was easy to remember, and it made the hard choice seem fair.")
    w.say(f"{elder.id} said they could split the {taffy.label}, save the {cod.label} for supper, and bring a small gift to the festival.")
    friend.memes["apology"] = 1
    child.memes["relief"] = 1
    friend.memes["reconciled"] = 1
    child.memes["reconciled"] = 1
    taffy.meters["shared"] = 1
    cod.meters["saved"] = 1

    # ending image
    w.para()
    w.say(f"{friend.id} apologized, and {child.id} forgave {friend.pronoun('object')}.")
    w.say(f"Together they carried the basket home, where the {cod.label} waited for supper and the {taffy.label} became two neat halves.")
    w.say(f"By dusk, {w.setting.place} was quiet again, and no one was left with a hard heart.")
    w.facts.update(child=child, friend=friend, elder=elder, cod=cod, taffy=taffy)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for young children that uses the words "cod" and "taffy" and ends with reconciliation.',
        f"Tell a gentle story in {world.setting.place} where {f['child'].id} and {f['friend'].id} argue over cod and taffy, then make peace.",
        f"Write a short repeated-and-rhyming story about sharing cod and taffy near a harbor or dock.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, elder = f["child"], f["friend"], f["elder"]
    return [
        QAItem(
            question=f"Who was the child in the story?",
            answer=f"The child was {child.id}, who lived in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {friend.id} keep asking for?",
            answer=f"{friend.id} kept asking for the taffy again and again.",
        ),
        QAItem(
            question=f"Why did the hard feeling go away at the end?",
            answer=f"The hard feeling went away because {elder.id} sang a rhyme, the two friends shared the taffy, saved the cod, and made peace.",
        ),
        QAItem(
            question=f"What happened to the cod at the end?",
            answer=f"The cod was saved for supper.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cod?",
            answer="Cod is a kind of fish that people can cook and eat.",
        ),
        QAItem(
            question="What is taffy?",
            answer="Taffy is a sweet candy that is often sticky and chewy.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little bit of music in words, where sounds repeat in a pleasing way.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement.",
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% child(Name). friend(Name). elder(Name). place(Name). story(Child,Friend,Elder,Place).

% A story is valid when the names are distinct.
valid_story(C,F,E,P) :- story(C,F,E,P), C != F.

% The tale wants cod and taffy, repetition, rhyme, and reconciliation.
features(cod_taffy_repetition_rhyme_reconciliation) :- story(_,_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for name, _g in CHILDREN:
        lines.append(asp.fact("child", name))
    for name, _g in FRIENDS:
        lines.append(asp.fact("friend", name))
    for name, _g in ELDERS:
        lines.append(asp.fact("elder", name))
    for p in SETTINGS:
        for c, _ in CHILDREN:
            for f, _ in FRIENDS:
                for e, _ in ELDERS:
                    lines.append(asp.fact("story", c, f, e, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {
        (c, f, e, p)
        for p in SETTINGS
        for c, _ in CHILDREN
        for f, _ in FRIENDS
        for e, _ in ELDERS
        if c != f
    }
    if clingo_set != py_set:
        print("MISMATCH between clingo and python.")
        if clingo_set - py_set:
            print("Only in clingo:", sorted(clingo_set - py_set))
        if py_set - clingo_set:
            print("Only in python:", sorted(py_set - clingo_set))
        return 1
    print(f"OK: clingo gate matches python ({len(py_set)} stories).")
    sample = generate(StoryParams(place=next(iter(SETTINGS)), child=CHILDREN[0][0], friend=FRIENDS[0][0], elder=ELDERS[0][0]))
    if not sample.story or "cod" not in sample.story or "taffy" not in sample.story:
        print("Generated story check failed.")
        return 1
    print("OK: generated story contains cod and taffy.")
    return 0


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="harbor", child="Nia", friend="Bram", elder="Nana"),
            StoryParams(place="cove", child="Lena", friend="Iris", elder="Aunt Nell"),
            StoryParams(place="village", child="Milo", friend="Perrin", elder="Grandpa Otis"),
        ]
        return [generate(p) for p in curated]

    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        seed = base_seed + i
        i += 1
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError as err:
            print(err)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for c, f, e, p in stories:
            print(f"  {p:8} {c:8} {f:8} {e:12}")
        return

    samples = build_samples(args)
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
