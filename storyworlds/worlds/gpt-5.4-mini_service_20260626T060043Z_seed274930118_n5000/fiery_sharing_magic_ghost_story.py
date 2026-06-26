#!/usr/bin/env python3
"""
storyworlds/worlds/fiery_sharing_magic_ghost_story.py
======================================================

A small ghost-story world about a child ghost, a fiery magical thing, and a
kind choice to share it safely.

Seed tale sketch:
---
On a chilly moonlit evening, a little ghost found a fiery magic candle that
could make a dark room glow like a tiny sunrise. The ghost wanted to keep it
all for itself, because the warm light felt wonderful in the cold hall.

But when the ghost's friends shivered in the dark, the ghost felt torn.
Sharing the candle could help everyone, but the flame was too fiery to pass
around carelessly. So the ghost's helper suggested a softer spell: cool the
flame a little, make the glow gentle, and share the light in a circle.

The ghost agreed, and soon everyone sat together under the warm magic glow,
feeling brave, cozy, and close.
---

This script turns that premise into a tiny simulated story world with:
* physical meters: heat, brightness, coldness, soot
* emotional memes: joy, fear, possessiveness, generosity, bravery, comfort

It includes a Python reasonableness gate plus an inline ASP twin for parity
checks and inspection.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    dark: bool = True
    cozy: bool = False
    helps: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    heat: float
    shines: float
    shareable: bool = True
    cooled_by: set[str] = field(default_factory=set)


@dataclass
class HelperSpell:
    id: str
    label: str
    verb: str
    result: str
    reduces_heat: float
    increases_share: float


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    for ghost in world.characters():
        if ghost.meters.get("heat", 0.0) < THRESHOLD:
            sig = ("cold", ghost.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ghost.memes["comfort"] = ghost.memes.get("comfort", 0.0) + 1
            out.append(f"The night felt chilly around {ghost.id}.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for ghost in world.characters():
        if ghost.memes.get("sharing", 0.0) < THRESHOLD:
            continue
        for treasure in world.entities.values():
            if treasure.kind != "thing" or treasure.owner != ghost.id:
                continue
            sig = ("share", ghost.id, treasure.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{ghost.id} made a careful choice to share.")
    return out


CAUSAL_RULES = [
    ("cold", _r_cold),
    ("share", _r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "attic": Place(id="attic", label="the attic", dark=True, cozy=False, helps={"glow", "share"}),
    "hall": Place(id="hall", label="the moonlit hall", dark=True, cozy=False, helps={"glow", "share"}),
    "graveyard": Place(id="graveyard", label="the quiet graveyard path", dark=True, cozy=False, helps={"glow"}),
    "porch": Place(id="porch", label="the porch steps", dark=True, cozy=True, helps={"share", "glow"}),
}

TREASURES = {
    "candle": Treasure(
        id="candle",
        label="magic candle",
        phrase="a fiery magic candle",
        type="candle",
        heat=2.0,
        shines=2.0,
        shareable=True,
        cooled_by={"cool_spell", "gentle_spell"},
    ),
    "lantern": Treasure(
        id="lantern",
        label="magic lantern",
        phrase="a fiery magic lantern",
        type="lantern",
        heat=1.5,
        shines=2.5,
        shareable=True,
        cooled_by={"cool_spell"},
    ),
    "orb": Treasure(
        id="orb",
        label="glowing orb",
        phrase="a fiery glowing orb",
        type="orb",
        heat=1.2,
        shines=2.2,
        shareable=True,
        cooled_by={"cool_spell", "soft_spell"},
    ),
}

SPELLS = [
    HelperSpell(
        id="cool_spell",
        label="cooling spell",
        verb="cool the flame",
        result="the glow became gentle",
        reduces_heat=1.3,
        increases_share=1.0,
    ),
    HelperSpell(
        id="soft_spell",
        label="softening spell",
        verb="soften the glow",
        result="the light turned mild and safe",
        reduces_heat=1.0,
        increases_share=0.8,
    ),
    HelperSpell(
        id="gentle_spell",
        label="gentle spell",
        verb="make the light gentle",
        result="the candle stopped feeling too fierce",
        reduces_heat=0.9,
        increases_share=1.2,
    ),
]

NAMES = ["Mira", "Nico", "Luna", "Toby", "Ivy", "Pip", "Wren", "Ada"]
GHOST_NAMES = ["Mira", "Nico", "Luna", "Pip"]
HELPER_NAMES = ["Aunt Ebb", "Uncle Moss", "Grandma Vale", "Old Hush"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    helper: str
    seed: Optional[int] = None


def treasure_at_risk(treasure: Treasure, place: Place) -> bool:
    return place.dark and treasure.heat >= 1.0


def select_spell(treasure: Treasure) -> Optional[HelperSpell]:
    for spell in SPELLS:
        if spell.id in treasure.cooled_by:
            return spell
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for tid, treasure in TREASURES.items():
            if treasure_at_risk(treasure, place) and select_spell(treasure):
                out.append((pid, tid))
    return out


def introduce(world: World, ghost: Entity) -> None:
    world.say(f"{ghost.id} was a little ghost who loved soft whispers and bright secrets.")


def find_treasure(world: World, ghost: Entity, treasure: Entity) -> None:
    ghost.memes["joy"] = ghost.memes.get("joy", 0.0) + 1
    treasure.carried_by = ghost.id
    world.say(
        f"One chilly night, {ghost.id} found {treasure.phrase} tucked in {world.place.label}."
    )
    world.say(f"The little glow felt warm and wonderful in {ghost.pronoun('possessive')} floating hands.")


def wants_to_keep(world: World, ghost: Entity, treasure: Entity) -> None:
    ghost.memes["possessive"] = ghost.memes.get("possessive", 0.0) + 1
    world.say(
        f"{ghost.id} wanted to keep the {treasure.label} close, because the fiery light felt like a tiny sun."
    )


def friends_arrive(world: World, ghost: Entity) -> None:
    ghost.meters["cold"] = ghost.meters.get("cold", 0.0) + 1
    world.say(
        f"Then friends drifted in from the dark, and the room felt colder and bigger than before."
    )


def warn(world: World, helper: Entity, ghost: Entity, treasure: Entity) -> bool:
    pred = treasure_at_risk(world.get(treasure.id).metadata["treasure"], world.place) if False else None
    if not treasure_at_risk(TREASURES[world.facts["treasure"]], world.place):
        return False
    world.say(
        f'"If you pass that fiery {treasure.label} around too fast, it could feel too hot," '
        f"{helper.id} whispered. \"Let's share it the safe way.\""
    )
    ghost.memes["worry"] = ghost.memes.get("worry", 0.0) + 1
    return True


def decide_to_share(world: World, ghost: Entity) -> None:
    ghost.memes["sharing"] = ghost.memes.get("sharing", 0.0) + 1
    world.say(f"{ghost.id} looked at the shivering friends and decided to share instead of hoard.")


def apply_spell(world: World, ghost: Entity, treasure: Entity, spell: HelperSpell) -> None:
    treasure.meters["heat"] = max(0.0, treasure.meters.get("heat", 0.0) - spell.reduces_heat)
    treasure.meters["glow"] = treasure.meters.get("glow", 0.0) + spell.increases_share
    ghost.memes["bravery"] = ghost.memes.get("bravery", 0.0) + 1
    world.say(
        f"{ghost.id} and {world.facts['helper_name']} used a {spell.label} to {spell.verb}. "
        f"After that, {spell.result}."
    )
    propagate(world, narrate=True)


def final_sharing(world: World, ghost: Entity, treasure: Entity) -> None:
    ghost.memes["joy"] = ghost.memes.get("joy", 0.0) + 1
    ghost.memes["comfort"] = ghost.memes.get("comfort", 0.0) + 1
    world.say(
        f"At last, {ghost.id} held the {treasure.label} in the center of the room, and everyone gathered in a cozy circle."
    )
    world.say(
        f"The fiery glow stayed bright, but it was gentle now, and the whole dark place felt warm and brave."
    )


def tell(place: Place, treasure_cfg: Treasure, name: str, helper_name: str) -> World:
    world = World(place)
    ghost = world.add(Entity(id=name, kind="character", type="ghost"))
    helper = world.add(Entity(id=helper_name, kind="character", type="ghost"))
    treasure = world.add(Entity(id="treasure", kind="thing", type=treasure_cfg.type, label=treasure_cfg.label))
    treasure.meters["heat"] = treasure_cfg.heat
    treasure.meters["glow"] = treasure_cfg.shines
    world.facts.update(place=place.id, treasure=treasure_cfg.id, helper_name=helper_name)

    introduce(world, ghost)
    find_treasure(world, ghost, treasure)
    wants_to_keep(world, ghost, treasure)
    world.para()
    friends_arrive(world, ghost)
    world.say(
        f"{helper.id} floated in beside them and noticed the way the treasure's fiery glow made everyone squint."
    )
    warn(world, helper, ghost, treasure)
    decide_to_share(world, ghost)
    world.para()
    spell = select_spell(treasure_cfg)
    if spell is None:
        raise StoryError("No safe spell exists for this treasure.")
    apply_spell(world, ghost, treasure, spell)
    final_sharing(world, ghost, treasure)

    world.facts.update(ghost=ghost, helper=helper, treasure_ent=treasure, spell=spell)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about a {f["treasure"]} and a kind act of sharing.',
        f"Tell a spooky-but-cozy story where {f['ghost'].id} learns to share a fiery magical treasure in {world.place.label}.",
        f'Write a gentle ghost story that includes the word "fiery" and ends with everyone feeling safe and warm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost: Entity = f["ghost"]
    helper: Entity = f["helper"]
    treasure: Entity = f["treasure_ent"]
    spell: HelperSpell = f["spell"]
    qa = [
        QAItem(
            question=f"What did {ghost.id} find in {world.place.label}?",
            answer=f"{ghost.id} found {treasure.phrase} tucked in {world.place.label}, and it glowed like a tiny sunrise.",
        ),
        QAItem(
            question=f"Why did {ghost.id} want to keep the {treasure.label} close?",
            answer=(
                f"{ghost.id} wanted to keep it close because the fiery light felt warm and wonderful. "
                f"At first, {ghost.pronoun('possessive')} heart was a little selfish, but the light was very inviting."
            ),
        ),
        QAItem(
            question=f"What did {helper.id} worry about when the friends arrived?",
            answer=(
                f"{helper.id} worried that the fiery {treasure.label} might feel too hot if it was passed around carelessly. "
                f"That was why {helper.pronoun('subject')} suggested a safer way to share."
            ),
        ),
        QAItem(
            question=f"How did {ghost.id} and {helper.id} make the {treasure.label} safe to share?",
            answer=(
                f"They used a {spell.label} to {spell.verb}. After that, {spell.result}, so the light could be shared in a cozy circle."
            ),
        ),
        QAItem(
            question=f"How did the story end for {ghost.id} and the friends?",
            answer=(
                f"The story ended with {ghost.id} sharing the {treasure.label} in the middle of the room. "
                f"Everyone felt warm, brave, and close together."
            ),
        ),
    ]
    return qa


KNOWLEDGE = {
    "fiery": [
        QAItem(
            question="What does fiery mean?",
            answer="Fiery means hot, bright, or strong, like a flame that looks lively and warm.",
        )
    ],
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that can float through places and often appears at night in ghost stories.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, enjoy, or have a turn with something instead of keeping it all to yourself.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special that can do surprising things, like change light, make a spell work, or help a problem feel easier.",
        )
    ],
    "light": [
        QAItem(
            question="Why is light helpful in the dark?",
            answer="Light helps people see shapes, feel calmer, and move around more safely when it is dark.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fiery", "ghost", "sharing", "magic", "light"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(KNOWLEDGE.get(tag, []))
    return out


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A treasure is at risk when it is fiery and the place is dark.
at_risk(T, P) :- treasure(T), place(P), fiery(T), dark(P).

% A spell is suitable if it reduces the heat enough for the treasure.
suitable(S, T) :- spell(S), treasure(T), cooled_by(T, S).

valid_story(P, T, S) :- at_risk(T, P), suitable(S, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
        if place.cozy:
            lines.append(asp.fact("cozy", pid))
    for tid, tre in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("fiery", tid))
        for s in sorted(tre.cooled_by):
            lines.append(asp.fact("cooled_by", tid, s))
    for sp in SPELLS:
        lines.append(asp.fact("spell", sp.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for tid, tre in TREASURES.items():
            for sp in SPELLS:
                if treasure_at_risk(tre, place) and sp.id in tre.cooled_by:
                    out.append((pid, tid, sp.id))
    return out


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_story_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world about fiery magic and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = valid_story_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.treasure:
        combos = [c for c in combos if c[1] == args.treasure]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treasure, _spell = rng.choice(sorted(combos))
    name = args.name or rng.choice(GHOST_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, treasure=treasure, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREASURES[params.treasure], params.name, params.helper)
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
    StoryParams(place="attic", treasure="candle", name="Mira", helper="Aunt Ebb"),
    StoryParams(place="hall", treasure="lantern", name="Luna", helper="Grandma Vale"),
    StoryParams(place="porch", treasure="orb", name="Pip", helper="Old Hush"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (place, treasure, spell) combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.treasure} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
