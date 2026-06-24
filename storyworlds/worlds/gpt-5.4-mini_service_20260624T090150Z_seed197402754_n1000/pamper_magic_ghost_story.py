#!/usr/bin/env python3
"""
Story world: a child, a shy ghost, and a little magic pampering.

Seed image:
- A child finds a ghost that is cold, dusty, and lonely.
- The child wants to pamper the ghost with magic: a warm bath, a blanket, a snack, or a lantern.
- The ghost is frightened at first, but the gentle magic turns the night bright and kind.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "dusty": 0.0, "sweet": 0.0, "bright": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "joy": 0.0, "trust": 0.0, "tenderness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    shadowy: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    help_word: str
    effect: str
    warmth: float = 0.0
    brightness: float = 0.0
    sweetness: float = 0.0
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    magic: str
    gift: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "attic": Setting(place="the attic", shadowy=True, affords={"lantern", "blanket", "soup"}),
    "bedroom": Setting(place="the bedroom", shadowy=False, affords={"blanket", "soup", "song"}),
    "kitchen": Setting(place="the kitchen", shadowy=False, affords={"soup", "cake", "song"}),
    "hallway": Setting(place="the hallway", shadowy=True, affords={"lantern", "song"}),
}

MAGIC = {
    "lantern": MagicItem(
        id="lantern",
        label="a magic lantern",
        phrase="a little magic lantern with a gold star",
        help_word="light",
        effect="made the dark corners glow",
        brightness=1.0,
        covers={"dark"},
    ),
    "blanket": MagicItem(
        id="blanket",
        label="a magic blanket",
        phrase="a soft magic blanket stitched with moons",
        help_word="warmth",
        effect="made chilly air feel gentle",
        warmth=1.0,
        covers={"cold"},
    ),
    "soup": MagicItem(
        id="soup",
        label="a magic soup bowl",
        phrase="a steaming bowl of magic soup",
        help_word="comfort",
        effect="made the ghost feel fed and calm",
        warmth=0.5,
        sweetness=0.5,
        covers={"cold", "fear"},
    ),
    "song": MagicItem(
        id="song",
        label="a magic lullaby",
        phrase="a soft magic lullaby",
        help_word="bravery",
        effect="helped a scared heart feel brave",
        brightness=0.4,
        sweetness=0.4,
        covers={"fear"},
    ),
    "cake": MagicItem(
        id="cake",
        label="a magic cake",
        phrase="a tiny magic cake with blueberry glaze",
        help_word="kindness",
        effect="made the room smell sweet and cozy",
        sweetness=1.0,
        covers={"fear", "cold"},
    ),
}

GIFTS = {
    "old_towel": ("old towel", "a clean old towel", {"cold"}),
    "pajamas": ("pajamas", "cozy pajamas", {"cold"}),
    "teacup": ("teacup", "a tiny teacup", {"fear"}),
}

GIRL_NAMES = ["Luna", "Mina", "Iris", "Nora", "Elsie", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Eli", "Noah", "Ben"]
TRAITS = ["gentle", "curious", "brave", "softhearted", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for magic_id in setting.affords:
            for gift_id, (_, _, helps) in GIFTS.items():
                m = MAGIC[magic_id]
                if helps & m.covers:
                    combos.append((place, magic_id, gift_id))
    return combos


@dataclass
class RoleStory:
    child: Entity
    ghost: Entity
    parent: Entity
    gift: Entity
    magic: Entity


def magic_at_risk(magic: MagicItem, gift_id: str) -> bool:
    _, _, helps = GIFTS[gift_id]
    return bool(helps & magic.covers)


def select_magic(magic_id: str, gift_id: str) -> Optional[MagicItem]:
    magic = MAGIC[magic_id]
    return magic if magic_at_risk(magic, gift_id) else None


def build_world(params: StoryParams) -> tuple[World, RoleStory]:
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    gift_name, gift_phrase, helps = GIFTS[params.gift]
    gift = world.add(Entity(
        id="gift", type=gift_name, label=gift_name, phrase=gift_phrase,
        owner=child.id, caretaker=parent.id, protective=True, covers=set(helps)
    ))
    magic_def = MAGIC[params.magic]
    magic = world.add(Entity(
        id=magic_def.id, type="magic", label=magic_def.label, phrase=magic_def.phrase,
        protective=True, covers=set(magic_def.covers)
    ))
    return world, RoleStory(child=child, ghost=ghost, parent=parent, gift=gift, magic=magic)


def tell(world: World, rs: RoleStory, params: StoryParams) -> None:
    child, ghost, parent, gift, magic = rs.child, rs.ghost, rs.parent, rs.gift, rs.magic

    child.memes["tenderness"] += 1
    ghost.meters["cold"] += 1
    ghost.meters["dusty"] += 1
    ghost.memes["fear"] += 1

    world.say(
        f"On a quiet night in {world.setting.place}, {child.id} was a {params.trait} child "
        f"who noticed a small ghost hiding near the wall."
    )
    world.say(
        f"{child.id} did not shout. {child.pronoun().capitalize()} only held up {gift.phrase} and whispered "
        f"that {ghost.pronoun()} looked cold and lonely."
    )

    world.para()
    world.say(
        f"{child.id} wanted to pamper {ghost.it()} with {magic.phrase}, because {magic.effect}."
    )
    world.say(
        f"But {ghost.pronoun()} trembled at first, and the dark room seemed even bigger."
    )

    if params.magic == "lantern":
        ghost.memes["fear"] += 1
        world.say(
            f"{child.id} set down the lantern slowly and let its gold light reach the dusty corners."
        )
    elif params.magic == "blanket":
        ghost.meters["cold"] += 1
        world.say(
            f"{child.id} wrapped the blanket around {ghost.pronoun('object')} like a moon-soft hug."
        )
    elif params.magic == "soup":
        ghost.memes["fear"] += 0.5
        world.say(
            f"{child.id} carried the soup carefully, and the warm smell made the ghost peek out from behind the shelf."
        )
    elif params.magic == "song":
        ghost.memes["fear"] += 0.5
        world.say(
            f"{child.id} hummed a tiny lullaby, and the notes floated gently through the dark."
        )
    else:
        ghost.memes["fear"] += 0.5
        world.say(
            f"{child.id} opened the little cake tin, and the sweet smell made the ghost stop shaking."
        )

    world.say(
        f"{child.id} kept going softly, not rushing {ghost.pronoun('object')}, just helping one gentle piece at a time."
    )

    ghost.memes["trust"] += 1
    ghost.memes["joy"] += 1
    ghost.meters["cold"] = max(0.0, ghost.meters["cold"] - (magic.warmth + 0.5))
    ghost.meters["dusty"] = max(0.0, ghost.meters["dusty"] - (magic.brightness + magic.sweetness))
    world.facts["help_word"] = magic.help_word

    world.para()
    world.say(
        f"At last, the ghost stood straighter. {ghost.pronoun().capitalize()} looked less like a frightened shadow "
        f"and more like a friend."
    )
    world.say(
        f"{child.id} smiled, and {parent.label if parent.label else 'the parent'} smiled too, because the room felt warm and bright."
    )
    world.say(
        f"By the end, {child.id} was still holding {gift.phrase}, and the ghost was no longer hiding."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child that includes the word "pamper" and a little magic.',
        f"Tell a gentle story where {f['child_name']} tries to pamper a shy ghost with {f['magic_label']}.",
        f"Write a cozy nighttime story about a child, a ghost, and a kind magic gift.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who did {f['child_name']} want to help in the story?",
            answer=f"{f['child_name']} wanted to help the shy ghost hiding in {f['place']}."
        ),
        QAItem(
            question=f"What did {f['child_name']} use to pamper the ghost?",
            answer=f"{f['child_name']} used {f['magic_phrase']} to pamper the ghost gently."
        ),
        QAItem(
            question=f"How did the ghost feel at the end?",
            answer="At the end, the ghost felt safer, warmer, and happier, so it stopped hiding."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is often a spooky-looking spirit in a story, but in a gentle story it can also be shy, lonely, and kind."
        ),
        QAItem(
            question="What does pamper mean?",
            answer="To pamper someone means to care for them in a very gentle and comforting way."
        ),
        QAItem(
            question="What does magic do in a fairy tale?",
            answer="Magic can change how things feel, like making a dark room bright or making a scared heart feel calm."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
helpful(M) :- magic(M), covers(M, X), helps(X).
valid(Place, Magic, Gift) :- affords(Place, Magic), helpful(Magic), gift(Gift), helps(Gift, X), covers(Magic, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for m in sorted(setting.affords):
            lines.append(asp.fact("affords", place, m))
    for magic_id, magic_def in MAGIC.items():
        lines.append(asp.fact("magic", magic_id))
        for c in sorted(magic_def.covers):
            lines.append(asp.fact("covers", magic_id, c))
    for gift_id, (_, _, helps) in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for h in sorted(helps):
            lines.append(asp.fact("helps", gift_id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(python_set - clingo_set))
    print("only clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with pampering magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def explain_rejection(magic_id: str, gift_id: str) -> str:
    return f"(No story: {magic_id} does not reasonably pamper {gift_id} in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.gift and not magic_at_risk(MAGIC[args.magic], args.gift):
        raise StoryError(explain_rejection(args.magic, args.gift))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, magic_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic_id, gift=gift_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world, rs = build_world(params)
    world.facts.update(
        child_name=params.name,
        place=params.place,
        magic_label=MAGIC[params.magic].label,
        magic_phrase=MAGIC[params.magic].phrase,
    )
    tell(world, rs, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(place="attic", magic="lantern", gift="old_towel", name="Luna", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bedroom", magic="blanket", gift="pajamas", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="kitchen", magic="soup", gift="teacup", name="Mina", gender="girl", parent="mother", trait="softhearted"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, magic, gift) combos:")
        for t in vals:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
