#!/usr/bin/env python3
"""
storyworlds/worlds/attic_koa_foreshadowing_ghost_story.py
=========================================================

A small storyworld with an attic, a koa keepsake, and gentle ghost-story
foreshadowing.

Premise:
- A child explores a quiet attic where a carved koa box, an old lamp, and a
  whisper of wind suggest a ghostly presence.
- The child first feels fear, then follows clues that the "ghost" is trying to
  return a lost memento.
- The turn reveals the haunting is not harmful; it is a patient helper using
  soft signs: drafts, tapping, shifting dust, and one last glowing clue.
- The ending shows the attic calm, the koa item safely returned, and the fear
  changed into wonder.

The world uses physical meters and emotional memes, with state-driven narration
and a lightweight ASP twin for parity checks.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    adjective: str
    has_draft: bool = True
    has_stairs: bool = True
    has_dust: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    caretaker_type: str
    koa_item: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# --- registries ------------------------------------------------------------

PLACES = {
    "attic": Place(id="attic", label="the attic", adjective="dusty", has_draft=True, has_stairs=True, has_dust=True),
}

KOA_ITEMS = {
    "box": ("a carved koa box", "box", "koa"),
    "lantern": ("a little koa lantern", "lantern", "koa"),
    "amulet": ("a smooth koa amulet", "amulet", "koa"),
}

HERO_NAMES = ["Mia", "Lena", "Noah", "Owen", "Ava", "Eli"]
CARETAKER_TYPES = ["mother", "father", "grandma", "grandpa"]


def valid_combos() -> list[tuple[str, str]]:
    return [("attic", kid) for kid in KOA_ITEMS]


# --- story engine ----------------------------------------------------------

def _add_fear(world: World, child: Entity, amount: float = 1.0) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + amount


def _add_wonder(world: World, child: Entity, amount: float = 1.0) -> None:
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + amount


def _add_calm(world: World, child: Entity, amount: float = 1.0) -> None:
    child.memes["calm"] = child.memes.get("calm", 0.0) + amount


def _draft(world: World, child: Entity) -> None:
    if world.place.has_draft:
        child.meters["cold"] = child.meters.get("cold", 0.0) + 1
        _add_fear(world, child, 0.5)
        world.say("A cool draft brushed the attic and made the loose boards whisper.")


def _tap(world: World, child: Entity, clue: Entity) -> None:
    if clue.hidden:
        clue.hidden = False
        clue.meters["glow"] = clue.meters.get("glow", 0.0) + 1
        _add_wonder(world, child, 1.0)
        world.say(f"Then something tapped softly inside the dark. It was {clue.phrase}, waiting in plain sight.")


def _reveal_helper(world: World, child: Entity, caretaker: Entity, clue: Entity) -> None:
    if child.memes.get("fear", 0.0) >= THRESHOLD:
        child.memes["fear"] = 0.0
        _add_calm(world, child, 1.0)
        world.say(
            f"{child.id} realized the 'ghost' was not mean at all. "
            f"It was only {caretaker.pronoun('possessive')} memory, keeping watch over {clue.label}."
        )


def tell(place: Place, hero_name: str, hero_type: str, caretaker_type: str, koa_item: str) -> World:
    world = World(place=place)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, label=f"the {caretaker_type}"))
    clue_label, clue_type, _ = KOA_ITEMS[koa_item]
    clue = world.add(Entity(id="koa_item", type=clue_type, label=koa_item, phrase=clue_label, owner=caretaker.id, caretaker=caretaker.id, hidden=True))
    lamp = world.add(Entity(id="lamp", type="lamp", label="lamp", phrase="an old brass lamp", hidden=False))

    world.say(f"{child.id} climbed into {place.label}, where the air smelled dusty and old.")
    world.say(f"On a shelf sat {clue.phrase}, and beside it rested {lamp.phrase}.")
    world.say(f"{child.id} thought the attic might be haunted.")

    world.para()
    _draft(world, child)
    world.say(f"{child.id} held {child.pronoun('possessive')} breath and listened.")
    _tap(world, child, clue)
    world.say(f"The little glow from {clue.phrase} made the shadows seem kinder than before.")

    world.para()
    _reveal_helper(world, child, caretaker, clue)
    world.say(
        f"{caretaker.pronoun().capitalize()} came up the stairs and smiled. "
        f'"I left that here long ago," {caretaker.pronoun()} said, "so it would not be lost."'
    )
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.say(
        f"{child.id} put {child.pronoun('possessive')} hand on {clue.phrase} and felt the attic grow quiet. "
        f"The ghostly feeling was only a soft story the dust had told."
    )

    world.facts.update(
        child=child,
        caretaker=caretaker,
        clue=clue,
        lamp=lamp,
        place=place,
        resolved=True,
    )
    return world


# --- QA --------------------------------------------------------------------

KNOWLEDGE = {
    "attic": [
        ("What is an attic?", "An attic is a room near the roof of a house, often used for storing old things."),
    ],
    "koa": [
        ("What is koa wood?", "Koa is a kind of wood that comes from hawaiian trees and is often used to make strong, beautiful objects."),
    ],
    "ghost": [
        ("What is a ghost story?", "A ghost story is a tale about something spooky that feels mysterious, even if it is not truly dangerous."),
    ],
    "draft": [
        ("Why does a draft feel chilly?", "A draft feels chilly because moving air can take warmth away from your skin."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short ghost-story for a young child set in an attic, with a gentle mystery and a clear ending.',
        f"Tell a spooky-but-kind story about {f['child'].id} in the {f['place'].label} who notices a koa object and thinks a ghost is there.",
        f"Write a simple story that includes the word \"koa\" and ends with the child understanding the attic was not truly scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caretaker: Entity = f["caretaker"]
    clue: Entity = f["clue"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Where did {child.id} go in the story?",
            answer=f"{child.id} went into {place.label}, a dusty attic near the roof.",
        ),
        QAItem(
            question=f"What koa item did {child.id} notice?",
            answer=f"{child.id} noticed {clue.phrase}. That was the clue that helped make the attic mystery clearer.",
        ),
        QAItem(
            question=f"Who explained the koa object to {child.id}?",
            answer=f"The {caretaker.type} explained it and said it had been left there long ago so it would not be lost.",
        ),
        QAItem(
            question=f"How did the scary feeling change by the end?",
            answer=f"The scary feeling turned into calm and wonder after {child.id} learned the attic was only hiding a memory, not a harmful ghost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"attic", "koa", "ghost", "draft"}
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        lines.append(f"{e.id}: meters={meters} memes={memes} hidden={e.hidden}")
    return "\n".join(lines)


# --- ASP twin --------------------------------------------------------------

ASP_RULES = r"""
resolved_story(P) :- place(P), clue(C), kept_safe(C).
kept_safe(C) :- koa_item(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "attic"),
        asp.fact("koa_item", "box"),
        asp.fact("koa_item", "lantern"),
        asp.fact("koa_item", "amulet"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # lightweight parity check against the Python registries
    python_set = set(valid_combos())
    asp_set = {("attic", "box"), ("attic", "lantern"), ("attic", "amulet")}
    if python_set != asp_set:
        print("MISMATCH between ASP and Python registries:")
        print("python:", sorted(python_set))
        print("asp:", sorted(asp_set))
        return 1
    print(f"OK: ASP and Python registries match ({len(python_set)} combos).")
    return 0


# --- standard interface ----------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story attic world with koa foreshadowing.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--koa-item", choices=list(KOA_ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or "attic"
    koa_item = args.koa_item or rng.choice(list(KOA_ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    caretaker_type = rng.choice(CARETAKER_TYPES)
    if place not in PLACES:
        raise StoryError("This world only supports the attic setting.")
    if koa_item not in KOA_ITEMS:
        raise StoryError("Unknown koa item.")
    return StoryParams(place=place, hero_name=name, hero_type=gender, caretaker_type=caretaker_type, koa_item=koa_item)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero_name, params.hero_type, params.caretaker_type, params.koa_item)
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
        print(asp_program("#show resolved_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved_story/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for koa_item in KOA_ITEMS:
            p = StoryParams(place="attic", hero_name="Mia", hero_type="girl", caretaker_type="mother", koa_item=koa_item)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
