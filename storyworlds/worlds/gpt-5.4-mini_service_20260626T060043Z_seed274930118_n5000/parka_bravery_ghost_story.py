#!/usr/bin/env python3
"""
storyworlds/worlds/parka_bravery_ghost_story.py
================================================

A small storyworld for a gentle ghost-story premise with bravery, a parka, and
a child who helps a shy ghost find its way home.

The seed image is a short tale in mind:
- A child goes out in a park wearing a warm parka on a chilly evening.
- They hear a spooky sound and first feel scared.
- Instead of running away, they gather bravery, investigate, and discover a
  lonely ghost that needs help.
- By being brave and kind, the child solves the problem and the spooky moment
  becomes a soft, friendly ending.

This script models:
- physical state in meters: cold, damp, lostness, glow, warmth, shelter
- emotional state in memes: fear, bravery, comfort, kindness, relief

The story is deterministic for a chosen parameter set, but the world can vary
in names, settings, and ghost details while keeping the core causal shape.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

BRAVERY_THRESHOLD = 1.0
FEAR_THRESHOLD = 1.0
HELP_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    friendly: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the park"
    evening: bool = True
    misty: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    lost_item: str
    home_place: str
    sound: str
    glow: str
    help_action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    if hero.meters["exposed"] < BRAVERY_THRESHOLD:
        return out
    if hero.meters["cold"] >= BRAVERY_THRESHOLD:
        sig = ("shiver", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 0.5
            out.append(f"A chilly breeze made {hero.id} shiver.")
    return out


def _r_parka_warmth(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    parka = next((e for e in world.entities.values() if e.id == "parka"), None)
    if not parka or parka.worn_by != hero.id:
        return out
    sig = ("warmth", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["warm"] += 1.5
    hero.meters["cold"] = max(0.0, hero.meters["cold"] - 1.0)
    hero.memes["comfort"] += 1.0
    out.append(f"The parka kept {hero.id} warm.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    if hero.memes["fear"] < FEAR_THRESHOLD:
        return out
    if hero.memes["bravery"] >= BRAVERY_THRESHOLD:
        sig = ("brave", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["bravery"] += 0.5
        out.append(f"{hero.id} took a deep breath and stayed put.")
    return out


def _r_help_ghost(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    ghost = next((e for e in world.characters() if e.type == "ghost"), None)
    if not hero or not ghost:
        return out
    if hero.memes["bravery"] < BRAVERY_THRESHOLD:
        return out
    if ghost.meters["lost"] < HELP_THRESHOLD:
        return out
    sig = ("help", hero.id, ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["lost"] = 0.0
    ghost.meters["homeward"] += 1.0
    hero.memes["kindness"] += 1.0
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["relief"] += 1.0
    out.append(f"{hero.id} followed the little glow and found a lost ghost.")
    out.append(f"With a brave smile, {hero.id} helped the ghost remember the way home.")
    return out


CAUSAL_RULES = [
    _r_cold,
    _r_parka_warmth,
    _r_bravery,
    _r_help_ghost,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
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
    return produced


def _do_walk(world: World, hero: Entity, ghost: Entity) -> None:
    hero.meters["exposed"] += 1.0
    hero.meters["cold"] += 0.5
    ghost.meters["lost"] += 1.0
    ghost.meters["glow"] += 1.0
    hero.memes["fear"] += 1.0
    propagate(world, narrate=True)


def _settle(world: World, hero: Entity, ghost: Entity) -> None:
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    if ghost.meters["lost"] < HELP_THRESHOLD:
        hero.memes["bravery"] += 1.0
        world.say(f"The park felt less spooky after that, and {hero.id} stood a little taller.")


def tell(setting: Setting, ghost_cfg: Ghost, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    parka = world.add(Entity(id="parka", type="parka", label="parka", phrase="a warm parka", owner=hero.id))
    parka.worn_by = hero.id
    ghost = world.add(Entity(
        id="Ghost", kind="character", type="ghost", label=ghost_cfg.label,
        phrase=ghost_cfg.label, friendly=True
    ))
    ghost.meters["lost"] = 1.0
    ghost.meters["glow"] = 1.0

    hero.memes["bravery"] += 0.5
    world.say(f"{hero.id} went to {setting.place} wearing a warm parka.")
    world.say(f"The air was misty, and somewhere ahead there came a soft {ghost_cfg.sound}.")

    world.para()
    world.say(f"{hero.id} wanted to keep walking, but the sound felt spooky.")
    _do_walk(world, hero, ghost)

    world.para()
    world.say(f"Then {hero.id} saw a tiny glow near the trees.")
    if hero.memes["fear"] >= FEAR_THRESHOLD:
        world.say(f"{hero.id} was scared, but {hero.pronoun('subject')} took a brave breath and looked closer.")
    hero.memes["bravery"] += 1.0
    propagate(world, narrate=True)
    _settle(world, hero, ghost)

    world.para()
    if ghost.meters["lost"] < HELP_THRESHOLD:
        world.say(f"It was only a lonely ghost looking for home.")
        world.say(f"{hero.id} pointed toward {ghost_cfg.home_place}, and the ghost drifted that way.")
        world.say(f"At the end, the ghost gave a happy little wave before fading into the mist.")
        hero.memes["relief"] += 1.0
    else:
        world.say(f"The glow blinked sadly, still waiting for a helper.")
    world.facts.update(hero=hero, parent=parent, parka=parka, ghost=ghost, ghost_cfg=ghost_cfg, setting=setting)
    return world


SETTINGS = {
    "park": Setting(place="the park", evening=True, misty=True, affords={"walk"}),
    "playground": Setting(place="the playground", evening=True, misty=True, affords={"walk"}),
    "lantern_path": Setting(place="the lantern path", evening=True, misty=True, affords={"walk"}),
}

GHOSTS = {
    "bench": Ghost(
        id="bench",
        label="bench-ghost",
        lost_item="a little silver key",
        home_place="the old gate",
        sound="whisper",
        glow="small blue glow",
        help_action="follow the glow",
        tags={"ghost", "lost", "glow"},
    ),
    "tree": Ghost(
        id="tree",
        label="tree-ghost",
        lost_item="a paper star",
        home_place="the tall tree",
        sound="rustle",
        glow="soft green glow",
        help_action="look by the roots",
        tags={"ghost", "lost", "glow"},
    ),
    "pond": Ghost(
        id="pond",
        label="pond-ghost",
        lost_item="a tiny lantern",
        home_place="the pond bridge",
        sound="sigh",
        glow="pale yellow glow",
        help_action="walk to the water",
        tags={"ghost", "lost", "glow"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Mila", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Eli", "Noah"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    ghost: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with a parka and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, ghost=ghost, name=name, gender=gender, parent=parent)


def _hero_type(gender: str) -> str:
    return gender


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost_cfg"]
    return [
        f"Write a gentle ghost story for a young child about {hero.id}, a parka, and bravery.",
        f"Tell a short story where {hero.id} hears a spooky sound in {world.setting.place} and helps {ghost.label} find home.",
        f"Write a child-friendly mystery with a misty park, a warm parka, and a brave helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Ghost = f["ghost_cfg"]
    parent: Entity = f["parent"]
    qa = [
        QAItem(
            question=f"What was {hero.id} wearing when {hero.id} went to {world.setting.place}?",
            answer=f"{hero.id} was wearing a warm parka, which helped {hero.pronoun('object')} feel brave in the chilly mist.",
        ),
        QAItem(
            question=f"What spooky sound did {hero.id} hear in the park?",
            answer=f"{hero.id} heard a soft {ghost.sound} coming from the misty path.",
        ),
        QAItem(
            question=f"Who helped the lonely ghost find the way home?",
            answer=f"{hero.id} helped the ghost by being brave and following the little glow.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the ghost turned out to be friendly?",
            answer=f"At first {hero.id} felt scared, but then {hero.id} felt relief and pride for being brave.",
        ),
        QAItem(
            question=f"Why did the parka matter in the story?",
            answer=f"The parka kept {hero.id} warm while {hero.id} stayed outside long enough to help the ghost.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parka for?",
            answer="A parka is a warm coat that helps keep a person cozy in cold weather.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means feeling scared or unsure and still choosing to do the helpful thing.",
        ),
        QAItem(
            question="Why can a ghost story feel spooky and friendly at the same time?",
            answer="A ghost story can feel spooky because of the dark and strange sounds, but friendly when the ghost needs help instead of causing trouble.",
        ),
    ]


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="park", ghost="bench", name="Lina", gender="girl", parent="mother"),
    StoryParams(place="playground", ghost="tree", name="Theo", gender="boy", parent="father"),
    StoryParams(place="lantern_path", ghost="pond", name="Maya", gender="girl", parent="mother"),
]


ASP_RULES = r"""
% A story is reasonable when the child has a parka and the ghost is lost.
has_parka(H) :- worn_by(parka,H).
spooky_scene(P,G) :- place(P), ghost(G), lost(G), has_parka(H), child(H).
resolved_scene(P,G) :- spooky_scene(P,G), brave(H), help(H,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.evening:
            lines.append(asp.fact("evening", pid))
        if s.misty:
            lines.append(asp.fact("misty", pid))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("lost", gid))
        lines.append(asp.fact("home", gid, g.home_place))
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("worn_by", "parka", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def tell_from_params(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    ghost_cfg = GHOSTS[params.ghost]
    return tell(setting, ghost_cfg, params.name, params.gender, params.parent)


def generate(params: StoryParams) -> StorySample:
    world = tell_from_params(params)
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
        print(asp_program("#show resolved_scene/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show spooky_scene/2.\n#show resolved_scene/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.place} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
