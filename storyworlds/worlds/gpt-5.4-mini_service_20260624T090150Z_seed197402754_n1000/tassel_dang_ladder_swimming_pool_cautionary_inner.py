#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a swimming pool, a ladder, a magical tassel,
and a careful warning that keeps one small adventure safe.

Premise:
- A child loves a glittery tassel charm.
- The child wants to use the pool ladder and reach the water.
- Magic makes the tassel tempting and a little unpredictable.
- A cautionary voice and inner monologue guide the turn from danger to safety.

The world is state-driven: the hero's desire, the object's magical pull, and the
ladder's risk all shape the prose, then the resolution changes the final image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    kind_words: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=lambda: {"ladder", "magic"})


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    magic: bool = False
    dangerous: bool = False
    region: str = "hands"
    plural: bool = False
    owner_types: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    item: str
    child_name: str
    gender: str
    parent_title: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


ITEMS = {
    "tassel": Item(
        id="tassel",
        label="tassel",
        phrase="a bright tassel tied with silver thread",
        type="tassel",
        magic=True,
        dangerous=True,
        region="hands",
    ),
    "dang": Item(
        id="dang",
        label="dang",
        phrase="a dangling dang charm that rang like a tiny bell",
        type="dang",
        magic=True,
        dangerous=True,
        region="hands",
    ),
    "ladder": Item(
        id="ladder",
        label="ladder",
        phrase="the slippery pool ladder",
        type="ladder",
        dangerous=True,
        region="feet",
        plural=False,
    ),
}

GIRL_NAMES = ["Lily", "Mira", "Nora", "Elin", "Rosie", "Ivy", "Mina"]
BOY_NAMES = ["Finn", "Theo", "Eli", "Bram", "Noah", "Otto", "Jasper"]
MOODS = ["brave", "curious", "gentle", "dreamy", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale cautionary storyworld set at a swimming pool.")
    ap.add_argument("--place", choices=["swimming pool"], default=None)
    ap.add_argument("--item", choices=sorted(ITEMS), default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"], default=None)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("swimming pool", item) for item in ITEMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "swimming pool":
        raise StoryError("This storyworld only lives at the swimming pool.")
    item = args.item or rng.choice(sorted(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    mood = rng.choice(MOODS)
    return StoryParams(place="swimming pool", item=item, child_name=name, gender=gender, parent_title=parent, mood=mood)


def _cautionary_reason(item: Item) -> str:
    if item.id == "ladder":
        return "The ladder was slippery and led straight to deep water."
    if item.id in {"tassel", "dang"}:
        return "Magic things can pull a curious child closer to trouble."
    return "The pool was not a place for careless feet."


ASP_RULES = r"""
% A story is valid when the selected item matches the pool setting.
valid(swimming_pool, I) :- item(I).

% Dangerous things need a cautionary turn and a safe ending.
cautionary(I) :- item(I), dangerous(I).
magic(I) :- item(I), magical(I).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "swimming_pool"), asp.fact("setting", "swimming_pool")]
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.dangerous:
            lines.append(asp.fact("dangerous", iid))
        if item.magic:
            lines.append(asp.fact("magical", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def _build_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.child_name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_title, label=params.parent_title))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(id=item_cfg.id, kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase))
    world.facts.update(child=child, parent=parent, item=item, item_cfg=item_cfg, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    item: Entity = world.facts["item"]
    item_cfg: Item = world.facts["item_cfg"]

    world.say(f"Once in a small fairy tale by the swimming pool, {child.id} found {item_cfg.phrase}.")
    world.say(f"{child.id} loved {item_cfg.label} because it felt like a tiny treasure, and {child.pronoun().capitalize()} wondered if the day could turn into a spell.")

    world.say(f"Near the water, the old ladder waited with shining wet steps.")
    if item_cfg.magic:
        world.say(f"The {item_cfg.label} gave a soft little glimmer, as if it wanted to sing in {child.id}'s hand.")

    world.say(f"{child.id} wanted to climb the ladder and lean closer to the blue water.")
    world.say(f"In {child.pronoun('possessive')} inner monologue, {child.id} thought, 'I can go just a little farther. It will be fine.'")

    reason = _cautionary_reason(item_cfg)
    world.say(f"But {parent.label} spoke at once: 'Careful, dear one. {reason}'")

    if item_cfg.magic:
        world.say(f"The magic in the {item_cfg.label} made the warning feel warmer and truer, like a lantern lit inside the heart.")
    world.say(f"{child.id} paused on the pool deck and listened to the quiet thought inside {child.pronoun('possessive')} own chest: 'I can be brave and still be careful.'")

    if item_cfg.id == "ladder":
        world.say(f"{child.id} kept both feet on the dry stones, and the ladder stopped looking like an invitation to trouble.")
        world.say(f"Instead, {child.id} took {parent.pronoun('possessive')} hand and watched the water sparkle from a safe distance.")
    elif item_cfg.id == "tassel":
        world.say(f"{child.id} tucked the tassel into {child.pronoun('possessive')} pocket, where it could glow without leading {child.pronoun('object')} too close to the edge.")
        world.say(f"Then {child.id} sat beside {parent.pronoun('possessive')} chair and waved at the ripples like a little king or queen of patience.")
    else:
        world.say(f"{child.id} hung the dang charm on a nearby hook, so its tiny ringing could stay a merry sound and not a risky one.")
        world.say(f"After that, {child.id} chose a slower game beside {parent.pronoun('possessive')} side, where every step was steady.")

    world.say(f"By the end, the pool still shimmered, the {item_cfg.label} was safe, and {child.id} smiled at the brave choice that kept the day gentle.")
    world.facts.update(resolved=True, reason=reason)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    item_cfg: Item = world.facts["item_cfg"]
    return [
        f'Write a fairy tale about a child named {p.child_name} at the swimming pool with a magical {item_cfg.label}.',
        f"Tell a cautionary story where {p.child_name} wants to go by the pool ladder, but an inner monologue helps {p.child_name} choose safety.",
        f"Write a gentle magic story set at a swimming pool that includes the words tassel, dang, and ladder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    item_cfg: Item = world.facts["item_cfg"]
    child: Entity = world.facts["child"]
    return [
        QAItem(
            question=f"What did {p.child_name} find by the swimming pool?",
            answer=f"{p.child_name} found {item_cfg.phrase}. It felt like a little treasure from a fairy tale.",
        ),
        QAItem(
            question=f"Why did the grown-up warn {p.child_name} near the ladder?",
            answer=f"The warning was meant to keep {p.child_name} safe because {item_cfg.label} and the ladder could lead to trouble near the water.",
        ),
        QAItem(
            question=f"What did {child.pronoun('possessive')} inner monologue help {p.child_name} decide?",
            answer=f"It helped {p.child_name} decide to be brave and careful at the same time, so {p.child_name} stayed away from the risky edge.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.child_name} choosing the safe path, so the pool stayed sparkling and the magic stayed gentle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item_cfg: Item = world.facts["item_cfg"]
    qas = [
        QAItem(
            question="What is a ladder used for?",
            answer="A ladder helps someone climb up or down to a higher or lower place.",
        ),
        QAItem(
            question="Why is a swimming pool place to be careful?",
            answer="A swimming pool can be slippery, and people must watch their steps near the water.",
        ),
    ]
    if item_cfg.magic:
        qas.append(QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a story wonder that can make ordinary things glow, sing, move, or feel enchanted.",
        ))
    return qas


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.kind}/{e.type}) label={e.label!r} phrase={e.phrase!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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
    StoryParams(place="swimming pool", item="tassel", child_name="Lily", gender="girl", parent_title="mother", mood="curious"),
    StoryParams(place="swimming pool", item="dang", child_name="Finn", gender="boy", parent_title="father", mood="brave"),
    StoryParams(place="swimming pool", item="ladder", child_name="Mira", gender="girl", parent_title="aunt", mood="dreamy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
