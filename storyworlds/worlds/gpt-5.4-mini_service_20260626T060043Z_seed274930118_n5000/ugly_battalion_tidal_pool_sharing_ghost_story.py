#!/usr/bin/env python3
"""
storyworlds/worlds/ugly_battalion_tidal_pool_sharing_ghost_story.py
====================================================================

A small, standalone storyworld for a ghost story set at a tidal pool, where an
ugly battalion of little sea-ghosts learns to share one bright shell lantern.

Premise:
- The tidal pool is full of twilight water, stacked rocks, and shy foam.
- A "battalion" is a small marching group; here it means a cluster of ghostly
  helpers who try to act brave even when they feel sticky, awkward, or ugly.
- The turning point is a sharing problem: one treasured lantern is not enough
  for all the ghosts to crowd around.
- The ending proves a causal change in world state: the battalion shares, the
  sour tugging eases, and the tide makes the pool glow together.

The script follows the shared Storyweavers contract:
- StoryParams plus registries
- build_parser / resolve_params / generate / emit / main
- QA, JSON, trace, ASP twin, and --verify parity
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"ghost", "spirit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tidal pool"
    tide: str = "low"
    affords: set[str] = field(default_factory=set)


@dataclass
class SharingObject:
    id: str
    label: str
    phrase: str
    type: str
    mood: str
    can_share: bool = True


@dataclass
class StoryParams:
    place: str
    share_item: str
    name: str
    type: str
    helper: str
    trait: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _a_shimmer(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    if not lantern:
        return out
    if lantern.meters.get("light", 0.0) < THRESHOLD:
        return out
    for ghost in world.characters():
        if ghost.kind != "character" or ghost.type != "ghost":
            continue
        if ghost.memes.get("shared", 0.0) >= THRESHOLD:
            continue
        sig = ("shimmer", ghost.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ghost.memes["soften"] = ghost.memes.get("soften", 0.0) + 1.0
        out.append(f"The glow reached {ghost.id} and made the pool feel less lonely.")
    return out


def _a_make_space(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("sharing_done"):
        sig = ("space",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The ghosts drifted apart a little, so everyone could stand by the light.")
    return out


ASP_RULES = r"""
#show shared/2.

shared(G, Item) :- ghost(G), share_item(Item), light(Item), wants(G, Item).
shared_all(Item) :- share_item(Item), shared(_, Item), shared(_, Item2).

satisfied(G) :- ghost(G), shared(G, Item).
calm_pool :- share_item(Item), shared(G, Item), shared(H, Item), G != H.
"""


SETTINGS = {
    "tidal pool": Setting(place="the tidal pool", tide="low", affords={"sharing"}),
}

SHARE_ITEMS = {
    "lantern": SharingObject(
        id="lantern",
        label="shell lantern",
        phrase="a shell lantern with a warm gold flicker",
        type="lantern",
        mood="glowing",
        can_share=True,
    ),
    "bucket": SharingObject(
        id="bucket",
        label="little bucket",
        phrase="a little bucket of bright sea water",
        type="bucket",
        mood="splashy",
        can_share=True,
    ),
    "pebble-ring": SharingObject(
        id="pebble-ring",
        label="pebble ring",
        phrase="a ring of smooth pebbles",
        type="pebbles",
        mood="still",
        can_share=True,
    ),
}

GHOST_NAMES = ["Moss", "Pip", "Wren", "Dew", "Nim", "Lark", "Fenn", "Ivy"]
HERO_TRAITS = ["ugly", "brave", "quiet", "wobbly", "small", "determined"]
HELPERS = ["misty", "pale", "briny", "shy"]


def valid_combos() -> list[tuple[str, str]]:
    return [("tidal pool", sid) for sid, obj in SHARE_ITEMS.items() if obj.can_share]


def reasonableness_gate(place: str, share_item: str) -> None:
    if place not in SETTINGS:
        raise StoryError("This story only makes sense at the tidal pool.")
    if share_item not in SHARE_ITEMS:
        raise StoryError("Unknown sharing object.")
    if not SHARE_ITEMS[share_item].can_share:
        raise StoryError("That object cannot be shared in a reasonable way.")


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("affords", place, "sharing"))
    for item_id, item in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", item_id))
        lines.append(asp.fact("light", item_id))
    for name in GHOST_NAMES:
        lines.append(asp.fact("ghost", name))
        for item_id in SHARE_ITEMS:
            lines.append(asp.fact("wants", name, item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show shared/2."))
    return sorted(set(asp.atoms(model, "shared")))


def asp_verify() -> int:
    expected = set((name, item) for _, item in valid_combos() for name in GHOST_NAMES)
    got = set(asp_valid_combos())
    if got == expected:
        print(f"OK: clingo gate matches Python gate ({len(got)} shared facts).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if got - expected:
        print("  only in clingo:", sorted(got - expected))
    if expected - got:
        print("  only in python:", sorted(expected - got))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A ghost story world about a battalion sharing a light at the tidal pool."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
    ap.add_argument("--name", choices=GHOST_NAMES)
    ap.add_argument("--type", choices=["ghost"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    reasonableness_gate(args.place or "tidal pool", args.share_item or "lantern")
    place = args.place or "tidal pool"
    share_item = args.share_item or rng.choice(sorted(SHARE_ITEMS))
    name = args.name or rng.choice(GHOST_NAMES)
    ghost_type = args.type or "ghost"
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(HERO_TRAITS)
    if trait == "ugly":
        trait = "ugly"
    return StoryParams(place=place, share_item=share_item, name=name, type=ghost_type, helper=helper, trait=trait)


def _light_up(world: World, item: Entity) -> None:
    item.meters["light"] = item.meters.get("light", 0.0) + 1.0


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.type, traits=[params.trait, "small"]))
    helper = world.add(Entity(id="Helper", kind="character", type="ghost", label=params.helper, traits=["gentle"]))
    battalion = world.add(Entity(id="Battalion", kind="group", type="group", label="ugly battalion", plural=True))
    item_cfg = SHARE_ITEMS[params.share_item]
    item = world.add(Entity(id="lantern", kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase))
    item.meters["light"] = 1.0

    world.say(
        f"At the tidal pool, {hero.id} belonged to an ugly battalion of little ghosts who tried to march straight even when the rocks made them wobble."
    )
    world.say(
        f"{hero.id} was a {params.trait} ghost, and {helper.label or params.helper} stayed near because the dusk water made every shadow look like a secret."
    )
    world.say(
        f"One evening, the battalion found {item_cfg.phrase}. Its glow was so warm that the wet stones looked silver."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to keep the shell lantern close, but the other ghosts gathered around it too. Everyone wanted to feel the light."
    )
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    hero.memes["grip"] = hero.memes.get("grip", 0.0) + 1.0
    world.say(
        f"The ugly battalion huddled tighter and tighter, and the glow seemed smaller each time another ghost leaned in."
    )
    world.say(
        f"{helper.label or params.helper} lifted a careful hand and said, \"If we share the lantern, nobody will be left in the dark.\""
    )
    world.para()
    hero.memes["sting"] = hero.memes.get("sting", 0.0) + 1.0
    world.say(
        f"{hero.id} frowned at first, because sharing felt hard when the pool wind was cold and the night looked big."
    )
    world.say(
        f"Then {hero.id} remembered how the tide always reached the whole pool, not just one stone, and {hero.id} passed the lantern around."
    )
    _light_up(world, item)
    hero.memes["shared"] = hero.memes.get("shared", 0.0) + 1.0
    helper.memes["shared"] = helper.memes.get("shared", 0.0) + 1.0
    world.facts["sharing_done"] = True
    world.say(
        f"One by one, the ghosts took turns holding the shell lantern, and the ugly battalion stopped feeling ugly and lonely."
    )
    world.say(
        f"By the time the tide slipped back, the whole tidal pool glimmered softly, and {hero.id} stood with the others in one bright circle."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        battalion=battalion,
        item=item,
        item_cfg=item_cfg,
        setting=world.setting,
        sharing_done=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    return [
        f'Write a gentle ghost story for a young child about {hero.id} at the tidal pool and a glowing {item.label} that must be shared.',
        f'Tell a short story in which an ugly battalion of ghosts learns that sharing {item.phrase} makes the dark feel smaller.',
        f'Write a simple tidal-pool story where a ghost named {hero.id} and friends take turns with a bright light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item_cfg"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story happen?",
            answer=f"It happens at the tidal pool, where the rocks are wet and the tide keeps moving in and out.",
        ),
        QAItem(
            question=f"What did the ugly battalion find by the water?",
            answer=f"They found {item.phrase}, a little shell lantern that glowed warmly in the dark.",
        ),
        QAItem(
            question=f"What did {helper.label or helper.id} tell the ghosts to do?",
            answer="The helper told them to share the lantern so nobody would be left in the dark.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after sharing?",
            answer=f"{hero.id} felt calmer and less alone after passing the lantern around the battalion.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left behind among rocks when the tide goes out.",
        ),
        QAItem(
            question="Why do ghosts in a story often like lanterns?",
            answer="Lanterns give a soft light, which makes dark places feel less scary and easier to share.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something too.",
        ),
    ]


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, params)
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


CURATED = [
    StoryParams(place="tidal pool", share_item="lantern", name="Moss", type="ghost", helper="misty", trait="ugly"),
    StoryParams(place="tidal pool", share_item="bucket", name="Pip", type="ghost", helper="shy", trait="quiet"),
    StoryParams(place="tidal pool", share_item="pebble-ring", name="Wren", type="ghost", helper="briny", trait="determined"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        model = asp_valid_combos()
        print(f"{len(model)} shared facts found by clingo.")
        for atom in model:
            print(atom)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
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
            header = f"### {p.name}: sharing {p.share_item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
