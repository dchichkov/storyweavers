#!/usr/bin/env python3
"""
A tiny Storyweavers world for an elementary-school rhyming tale of sharing,
surprise, and reconciliation.

Seed tale shape:
- A child wants to use something at elementary school.
- A small conflict grows when another child wants the same thing.
- A surprise reveals there is enough to share.
- The children reconcile and finish smiling together.

The prose is intentionally child-facing, concrete, and lightly rhyming.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def plural_word(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    adjective: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Want:
    id: str
    verb: str
    gerund: str
    surprise_reveal: str
    feature: str
    tag: str


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    plural: bool = False


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    help_line: str


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
        other = World(self.setting)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "classroom": Setting(place="the elementary classroom", adjective="bright", affords={"sharing"}),
    "library": Setting(place="the school library", adjective="quiet", affords={"sharing"}),
    "playground": Setting(place="the elementary playground", adjective="sunny", affords={"sharing"}),
}

WANTS = {
    "blocks": Want(
        id="blocks",
        verb="build a tall tower",
        gerund="building a tall tower",
        surprise_reveal="a second box of blocks under the bench",
        feature="sharing",
        tag="blocks",
    ),
    "crayons": Want(
        id="crayons",
        verb="color a big kite",
        gerund="coloring a big kite",
        surprise_reveal="a rainbow tin of crayons in the cubby",
        feature="sharing",
        tag="crayons",
    ),
    "stickers": Want(
        id="stickers",
        verb="make a shiny card",
        gerund="making a shiny card",
        surprise_reveal="a surprise packet of stickers from the teacher",
        feature="surprise",
        tag="stickers",
    ),
}

ITEMS = {
    "blocks": SharedItem(id="blocks", label="blocks", phrase="a pile of wooden blocks", plural=True),
    "crayons": SharedItem(id="crayons", label="crayons", phrase="a box of bright crayons", plural=True),
    "stickers": SharedItem(id="stickers", label="stickers", phrase="a page of shiny stickers", plural=True),
}

SURPRISES = {
    "blocks": Surprise(
        id="blocks",
        label="surprise blocks",
        reveal="another box of blocks was waiting nearby",
        help_line="There were enough blocks for both children to build",
    ),
    "crayons": Surprise(
        id="crayons",
        label="surprise crayons",
        reveal="there was a rainbow tin of crayons tucked in the cubby",
        help_line="There were enough crayons for both children to color",
    ),
    "stickers": Surprise(
        id="stickers",
        label="surprise stickers",
        reveal="the teacher smiled and found a packet of extra stickers",
        help_line="There were enough stickers for both children to share",
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Eli", "Ava", "Ben", "Zoe", "Milo"]
TRAITS = ["curious", "gentle", "cheery", "brave", "kind", "bouncy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    want: str
    child: str
    other: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def can_share(setting: Setting, want: Want, item: SharedItem, surprise: Surprise) -> bool:
    return want.feature in setting.affords and want.id == item.id == surprise.id


def evaluate_python(setting: Setting, want: Want, item: SharedItem, surprise: Surprise) -> bool:
    return can_share(setting, want, item, surprise)


def predict_resolution(world: World, child: Entity, other: Entity, want: Want, item: SharedItem) -> dict:
    sim = world.copy()
    _act_conflict(sim, sim.get(child.id), sim.get(other.id), want, narrate=False)
    _act_surprise(sim, want, item, narrate=False)
    return {
        "reconciled": sim.facts.get("resolved", False),
        "shared": sim.facts.get("shared", False),
    }


def _act_setup(world: World, child: Entity, other: Entity, want: Want, item: SharedItem) -> None:
    child.memes["want"] = 1
    child.memes["joy"] = 1
    other.memes["want"] = 1
    world.say(
        f"In the {world.setting.adjective} {world.setting.place}, little {child.id} "
        f"loved {want.gerund} with a grin so wide and bright."
    )
    world.say(
        f"{child.id} had {item.phrase}, and {other.id} liked it too, which made the morning feel all right."
    )


def _act_conflict(world: World, child: Entity, other: Entity, want: Want, narrate: bool = True) -> None:
    sig = ("conflict", child.id, other.id, want.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    other.memes["worry"] = other.memes.get("worry", 0) + 1
    world.facts["conflict"] = True
    if narrate:
        world.say(
            f"But soon both reached for the same thing, and the room grew tight and slight."
        )
        world.say(
            f"{child.id} said, \"I need it now.\" {other.id} said, \"I do too.\""
        )


def _act_surprise(world: World, want: Want, item: SharedItem, narrate: bool = True) -> None:
    sig = ("surprise", want.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.facts["surprised"] = True
    world.facts["shared"] = True
    world.facts["resolved"] = True
    if narrate:
        world.say(f"Then came a surprise, quick and light: {want.surprise_reveal}.")
        world.say(f"A gentle grown-up laughed and said, \"Let's share so everyone feels right.\"")
        world.say(
            f"That made the big worry shrink away, like a cloud let go of flight."
        )


def _act_reconcile(world: World, child: Entity, other: Entity, want: Want, item: SharedItem, narrate: bool = True) -> None:
    sig = ("reconcile", child.id, other.id, want.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    other.memes["joy"] = other.memes.get("joy", 0) + 1
    child.memes["worry"] = 0
    other.memes["worry"] = 0
    if narrate:
        world.say(
            f"{child.id} and {other.id} took turns, side by side, and shared in a merry glow."
        )
        world.say(
            f"They laughed and built together, and the day felt warm and slow."
        )


def simulate(world: World, child: Entity, other: Entity, want: Want, item: SharedItem, surprise: Surprise) -> None:
    _act_setup(world, child, other, want, item)
    world.para()
    _act_conflict(world, child, other, want, narrate=True)
    world.say(f"The room held its breath, then the surprise came just in time.")
    _act_surprise(world, want, item, narrate=True)
    _act_reconcile(world, child, other, want, item, narrate=True)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    want = f["want"]
    item = f["item"]
    return [
        f'Write a short rhyming story for an elementary child named {child.id} about sharing {item.label}.',
        f"Tell a gentle elementary-school tale where {child.id} wants to {want.verb}, then a surprise makes sharing possible.",
        f"Write a rhyming story with sharing, surprise, and reconciliation, using the word 'elementary'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    other: Entity = f["other"]
    want: Want = f["want"]
    item: SharedItem = f["item"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {setting.place}, where the day is bright and friendly.",
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {want.verb}, and {other.id} wanted to use the same thing too.",
        ),
        QAItem(
            question=f"What made the moment turn from tense to kind?",
            answer=(
                f"A surprise revealed extra {item.label}, so the children could share. "
                f"That helped them reconcile and finish happily together."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the children feel at the end?",
                answer=(
                    f"They felt glad and calm. After sharing, {child.id} and {other.id} "
                    f"smiled side by side instead of tugging apart."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means two or more people take turns or use something together so everyone gets a fair chance.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make people gasp, laugh, or smile.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and become friends again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(P) :- setting(P).
compatible(P,W,I,S) :- setting_ok(P), want(W), item(I), surprise(S),
                       setting_feature(P, sharing),
                       want_tag(W, T), item_tag(I, T), surprise_tag(S, T).

resolved(P,W,I,S) :- compatible(P,W,I,S).
#show compatible/4.
#show resolved/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("setting_feature", pid, "sharing"))
    for wid, w in WANTS.items():
        lines.append(asp.fact("want", wid))
        lines.append(asp.fact("want_tag", wid, w.tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_tag", iid, iid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_tag", sid, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for want_id, want in WANTS.items():
            for item_id, item in ITEMS.items():
                for surprise_id, surprise in SURPRISES.items():
                    if can_share(setting, want, item, surprise):
                        out.append((place, want_id, item_id))
    return out


def explain_rejection(setting: Setting, want: Want, item: SharedItem) -> str:
    return (
        f"(No story: {want.verb} with {item.label} does not fit the sharing-and-surprise "
        f"pattern in {setting.place}. Try matching want, item, and surprise with the same tag.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="An elementary rhyming story world about sharing, surprise, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--name")
    ap.add_argument("--other")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combos exist.")

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.want is None or c[1] == args.want)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, want_id, _ = rng.choice(sorted(filtered))
    child = args.name or rng.choice(NAMES)
    other = args.other or rng.choice([n for n in NAMES if n != child])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, want=want_id, child=child, other=other, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    want = WANTS[params.want]
    item = ITEMS[params.want]
    surprise = SURPRISES[params.want]

    if not evaluate_python(setting, want, item, surprise):
        raise StoryError(explain_rejection(setting, want, item))

    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type="child"))
    other = world.add(Entity(id=params.other, kind="character", type="child"))
    world.facts.update(
        child=child,
        other=other,
        want=want,
        item=item,
        surprise=surprise,
        setting=setting,
        params=params,
    )
    simulate(world, child, other, want, item, surprise)
    world.facts["resolved"] = True

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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4.\n#show resolved/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:")
        for place, want, item, surprise in combos:
            print(f"  {place:12} {want:10} {item:10} {surprise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, want, _ in valid_combos():
            p = StoryParams(place=place, want=want, child="Mia", other="Noah", trait="kind")
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
            header = f"### {p.child}: {p.want} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
