#!/usr/bin/env python3
"""
Standalone storyworld for a gentle Bedtime Story domain about sharing at bedtime.

Premise:
- A child depends on a shared bedtime item or ritual to feel ready for sleep.
- A small conflict begins when one child does not want to share.
- A kind turn follows when they discover that sharing helps both of them begin
  bedtime happily.

This world keeps the state model small and concrete:
- typed entities with physical meters and emotional memes
- a short causal simulation that drives the prose
- grounded QA sets and an inline ASP twin for reasonableness checking
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
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("softness", "warmth", "glow", "tiredness"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "calm", "worry", "stinginess", "dependence", "kindness", "sleepiness"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    label: str
    cozy: str
    supports: set[str]


@dataclass(frozen=True)
class SharedItem:
    id: str
    label: str
    phrase: str
    comfort: str
    glow: str
    depends_on: str  # "together" or "quiet"


PLACES = {
    "bedroom": Place(
        id="bedroom",
        label="the bedroom",
        cozy="soft pillows waited on the bed",
        supports={"book", "lamp", "blanket"},
    ),
    "nursery": Place(
        id="nursery",
        label="the nursery",
        cozy="a tiny lamp made a warm dot of light",
        supports={"book", "lamp", "blanket", "stuffie"},
    ),
    "loft": Place(
        id="loft",
        label="the loft",
        cozy="the window was dark and sleepy",
        supports={"book", "lamp", "blanket"},
    ),
}

ITEMS = {
    "book": SharedItem(
        id="book",
        label="storybook",
        phrase="a bedtime storybook with shiny pictures",
        comfort="gentle",
        glow="soft",
        depends_on="together",
    ),
    "lamp": SharedItem(
        id="lamp",
        label="lamp",
        phrase="a small lamp with a warm yellow shade",
        comfort="bright",
        glow="warm",
        depends_on="quiet",
    ),
    "blanket": SharedItem(
        id="blanket",
        label="blanket",
        phrase="a big blanket with moon-and-star patches",
        comfort="cozy",
        glow="soft",
        depends_on="together",
    ),
    "stuffie": SharedItem(
        id="stuffie",
        label="stuffie",
        phrase="a round stuffed bear with sleepy ears",
        comfort="snuggly",
        glow="none",
        depends_on="quiet",
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Eli", "Ivy", "Owen", "Nora", "Theo"]
KINDS = [("girl", "mother"), ("girl", "father"), ("boy", "mother"), ("boy", "father")]
TRAITS = ["gentle", "curious", "sleepy", "small", "brave", "sweet"]


# ---------------------------------------------------------------------------
# Rules and simulation
# ---------------------------------------------------------------------------

def _share(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.kind != "thing":
            continue
        if len(item.shared_with) >= 2 and item.memes["kindness"] < 1:
            sig = ("share", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.memes["kindness"] += 1
            out.append(f"{item.label.capitalize()} felt better when it was shared.")
    return out


def _depend(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes["dependence"] >= 1 and char.memes["calm"] < 1:
            sig = ("depend", char.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            char.memes["worry"] += 1
            out.append(f"{char.id} waited, hoping the shared bedtime thing would begin soon.")
    return out


def _settle(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes["kindness"] >= 1 and char.memes["worry"] >= 1:
            sig = ("settle", char.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            char.memes["worry"] = 0.0
            char.memes["calm"] += 1
            char.memes["sleepiness"] += 1
            out.append(f"{char.id} grew calm again, just in time for bedtime.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_share, _depend, _settle):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def place_detail(place: Place) -> str:
    return place.cozy


def item_can_be_shared(place: Place, item: SharedItem) -> bool:
    return item.id in place.supports


def pick_shared_item(place: Place, rng: random.Random) -> SharedItem:
    options = [i for i in ITEMS.values() if item_can_be_shared(place, i)]
    if not options:
        raise StoryError("No shared bedtime item fits this setting.")
    return rng.choice(options)


def build_world(params: "StoryParams") -> World:
    place = PLACES[params.place]
    item = ITEMS[params.item]
    if not item_can_be_shared(place, item):
        raise StoryError("That item does not fit this bedtime setting.")
    world = World(place=place.label)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"softness": 0.0, "warmth": 0.0, "glow": 0.0, "tiredness": 0.0},
        memes={"joy": 0.0, "calm": 0.0, "worry": 0.0, "stinginess": 0.0, "dependence": 0.0,
               "kindness": 0.0, "sleepiness": 0.0},
    ))
    sibling = world.add(Entity(
        id="Sibling",
        kind="character",
        type="boy" if params.gender == "girl" else "girl",
        label="the other child",
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
    ))
    shared = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        shared_with={child.id},
        plural=False,
        meters={"softness": 1.0 if item.id in {"blanket", "stuffie"} else 0.0,
                "warmth": 1.0 if item.id in {"lamp", "blanket"} else 0.0,
                "glow": 1.0 if item.id == "lamp" else 0.0,
                "tiredness": 0.0},
        memes={"joy": 0.0, "calm": 0.0, "worry": 0.0, "stinginess": 0.0,
               "dependence": 0.0, "kindness": 0.0, "sleepiness": 0.0},
    ))

    # Act 1
    world.say(f"It was bedtime in {place.label}, where {place_detail(place)}.")
    world.say(f"{child.id} was a {params.trait} little {child.type} who liked quiet nights.")
    world.say(f"{child.id} loved {item.phrase}, because it helped the room feel safe and snug.")
    world.say(f"The other child liked it too, and that made sharing matter.")

    # Act 2
    world.para()
    child.memes["dependence"] += 1
    sibling.memes["stinginess"] += 1
    shared.memes["worry"] += 1
    world.say(f"Then the bedtime routine was ready to begin, but the {shared.label} was needed by both children.")
    world.say(f"{child.id} wanted to begin right away, yet the other child did not want to share.")
    world.say(f"The little room grew still, and even the {shared.label} seemed to wait.")
    if item.depends_on == "together":
        world.say(f"Without sharing, the cozy part of bedtime could not truly begin.")
    else:
        world.say(f"Without a quiet turn, the shared {shared.label} could not begin its calm glow.")
    propagate(world, narrate=True)

    # Parent intervenes gently.
    parent.memes["kindness"] += 1
    child.memes["worry"] += 1
    sibling.memes["worry"] += 1
    world.say(f"The parent knelt beside them and said, \"Bedtime begins best when everyone has a turn.\"")
    world.say(f"That sounded fair, and it helped the room feel softer.")

    # Act 3
    world.para()
    shared.shared_with.add(sibling.id)
    child.memes["kindness"] += 1
    sibling.memes["kindness"] += 1
    child.memes["joy"] += 1
    sibling.memes["joy"] += 1
    child.memes["calm"] += 1
    sibling.memes["calm"] += 1
    shared.memes["calm"] += 1
    propagate(world, narrate=True)

    if item.id == "book":
        world.say(f"At last, the storybook opened, and the two children listened together until their eyes grew heavy.")
    elif item.id == "blanket":
        world.say(f"At last, the blanket spread over both small shoulders, and the room turned into a warm nest.")
    elif item.id == "lamp":
        world.say(f"At last, the lamp glowed softly while the children shared a quiet minute, then the light went low.")
    else:
        world.say(f"At last, the stuffie was hugged by both children in turn, and the room settled into a sleepy hush.")

    world.say(f"{child.id} felt safe, the other child felt included, and bedtime could finally begin.")
    world.say(f"Before long, everyone in {place.label} was quiet and cozy.")

    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        shared=shared,
        place=place,
        item=item,
    )
    return world


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
share_ready(P, I) :- place(P), item(I), supports(P, I).
valid_story(P, I) :- share_ready(P, I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for pid, p in PLACES.items():
        for iid in ITEMS:
            if item_can_be_shared(p, ITEMS[iid]):
                out.append((pid, iid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    b = set(valid_pairs())
    if a == b:
        print(f"OK: clingo gate matches valid_pairs() ({len(a)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        f'Write a gentle bedtime story for young children about sharing a {item.label}.',
        f"Tell a bedtime story where {child.id} depends on sharing {item.label} before sleep can begin.",
        f"Write a cozy story in which a small disagreement begins, then becomes a happy sharing moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    parent = f["parent"]
    item = f["shared"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who wanted to use the {item.label} at bedtime?",
            answer=f"{child.id} wanted to use the {item.label} first, and the other child wanted it too.",
        ),
        QAItem(
            question=f"Why did the bedtime routine begin slowly in {place.label}?",
            answer=f"It began slowly because both children needed the same {item.label}, and they had to share it kindly before bedtime could begin.",
        ),
        QAItem(
            question="What did the parent say to help them?",
            answer="The parent said that bedtime begins best when everyone has a turn.",
        ),
        QAItem(
            question=f"How did the children feel when they shared the {item.label}?",
            answer=f"They felt calm, included, and ready for sleep once they shared the {item.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    if item.id == "book":
        return [QAItem(
            question="What is a storybook for?",
            answer="A storybook is for reading stories, often before sleep or at quiet times.",
        )]
    if item.id == "blanket":
        return [QAItem(
            question="What does a blanket do?",
            answer="A blanket helps keep you warm and cozy when you are resting or sleeping.",
        )]
    if item.id == "lamp":
        return [QAItem(
            question="What does a lamp do?",
            answer="A lamp gives light so a room is not dark.",
        )]
    return [QAItem(
        question="What is a stuffed toy for?",
        answer="A stuffed toy is for hugging and cuddling, especially when someone wants comfort.",
    )]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="bedroom", item="book", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="nursery", item="blanket", name="Noah", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="loft", item="lamp", name="Luna", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", item="stuffie", name="Theo", gender="boy", parent="father", trait="sweet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime Story world about sharing, patience, and beginning bedtime kindly."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.item:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        if not item_can_be_shared(place, item):
            raise StoryError("That shared item does not fit this bedtime place.")
    pairs = [p for p in valid_pairs()
             if args.place is None or p[0] == args.place
             if args.item is None or p[1] == args.item]
    if not pairs:
        raise StoryError("(No valid bedtime combination matches the given options.)")
    place, item = rng.choice(pairs)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} valid bedtime sharing pairs:")
        for place, item in pairs:
            print(f"  {place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
