#!/usr/bin/env python3
"""
A standalone storyworld for a small Animal Story domain centered on a seam,
a remote, and rust.

Premise:
- A small animal family lives near a shed full of old things.
- The child animal loves a shiny remote that helps the toys sing and dance.
- A torn seam in a soft blanket, plus a rusty remote battery door, creates a
  small problem.
- A helper explains the trouble in dialogue, then the animals fix it together.

The storyworld simulates the physical state of the remote, blanket seam, and
repair tools, plus the emotional state of the characters.  The prose is driven
by those state changes, not by a frozen template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"rust": 0.0, "broken": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "squirrel"}
        male = {"boy", "father", "dad", "man", "rabbit", "fox", "bear"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the shed"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    region: str = ""
    plural: bool = False
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    hero_type: str
    friend_type: str
    name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shed": Setting(place="the shed", indoor=True, affords={"fix_remote"}),
    "barn": Setting(place="the barn", indoor=True, affords={"fix_remote"}),
    "porch": Setting(place="the porch", indoor=False, affords={"fix_remote"}),
}

HERO_TYPES = ["rabbit", "fox", "bear", "squirrel"]
FRIEND_TYPES = ["rabbit", "fox", "bear", "squirrel"]

ITEMS = {
    "blanket": ItemSpec(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        fragile=True,
    ),
    "remote": ItemSpec(
        id="remote",
        label="remote",
        phrase="a small toy remote with a springy button",
        fragile=True,
    ),
    "patch": ItemSpec(
        id="patch",
        label="patch",
        phrase="a square cloth patch",
    ),
    "oil": ItemSpec(
        id="oil",
        label="oil",
        phrase="a tiny bottle of oil",
    ),
}

CHARACTER_NAMES = {
    "rabbit": ["Pip", "Nina", "Milo"],
    "fox": ["Tara", "Finn", "Roo"],
    "bear": ["Benny", "Mara", "Tess"],
    "squirrel": ["Suki", "Jax", "Luna"],
}


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------

def seam_is_torn(blanket: Entity) -> bool:
    return blanket.meters.get("broken", 0.0) >= THRESHOLD


def remote_is_rusty(remote: Entity) -> bool:
    return remote.meters.get("rust", 0.0) >= THRESHOLD


def can_fix_remote(world: World) -> bool:
    return "patch" in world.entities and "oil" in world.entities


def apply_rust(world: World, remote: Entity) -> None:
    remote.meters["rust"] += 1.0


def repair_seam(world: World, blanket: Entity, patch: Entity) -> None:
    if ("repair_seam", blanket.id) in world.fired:
        return
    world.fired.add(("repair_seam", blanket.id))
    blanket.meters["broken"] = 0.0
    blanket.meters["clean"] += 1.0
    patch.meters["clean"] += 1.0


def oil_remote(world: World, remote: Entity, oil: Entity) -> None:
    if ("oil_remote", remote.id) in world.fired:
        return
    world.fired.add(("oil_remote", remote.id))
    remote.meters["rust"] = max(0.0, remote.meters["rust"] - 1.0)
    oil.meters["clean"] += 1.0


def predict_fix(world: World) -> dict[str, bool]:
    sim = world.copy()
    blanket = sim.get("blanket")
    remote = sim.get("remote")
    patch = sim.get("patch")
    oil = sim.get("oil")
    repair_seam(sim, blanket, patch)
    oil_remote(sim, remote, oil)
    return {
        "seam_fixed": not seam_is_torn(blanket),
        "rust_fixed": not remote_is_rusty(remote),
    }


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, friend: Entity, blanket: Entity, remote: Entity) -> str:
    return (
        f"{hero.id} was a little {hero.type} who loved {remote.phrase}. "
        f"{friend.id}, a cheerful {friend.type}, liked to curl up on {blanket.phrase} and listen."
    )


def conflict_line(hero: Entity, blanket: Entity, remote: Entity) -> str:
    return (
        f"One day {hero.id} tugged the blanket too hard, and the seam split with a soft rip. "
        f'\"Oh no,\" {hero.id} said, \"the blanket is torn!\" '
        f'Then the button on the remote stuck, because a little rust had crept inside.'
    )


def dialogue_warning(hero: Entity, friend: Entity, blanket: Entity, remote: Entity) -> str:
    return (
        f'\"If the seam stays open, the blanket will get worse,\" {friend.id} said. '
        f'\"And if the remote stays rusty, it will not sing,\" {hero.id} said. '
        f'\"We can fix both,\" {friend.id} replied.'
    )


def resolution_line(hero: Entity, friend: Entity, blanket: Entity, remote: Entity) -> str:
    return (
        f"{hero.id} held the patch in place while {friend.id} dripped a tiny bit of oil into the remote. "
        f"The seam closed neatly, the rust loosened, and the button clicked again."
    )


def ending_line(hero: Entity, friend: Entity, blanket: Entity, remote: Entity) -> str:
    return (
        f"By sunset, {hero.id} and {friend.id} were sitting together on the blanket, "
        f"pressing the remote and laughing as the toys danced."
    )


# ---------------------------------------------------------------------------
# World screenplay
# ---------------------------------------------------------------------------

def tell(setting: Setting, hero_type: str, friend_type: str, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))

    blanket = world.add(Entity(id="blanket", type="blanket", label="blanket", phrase="a soft blue blanket"))
    remote = world.add(Entity(id="remote", type="remote", label="remote", phrase="a small toy remote with a springy button"))
    patch = world.add(Entity(id="patch", type="patch", label="patch", phrase="a square cloth patch"))
    oil = world.add(Entity(id="oil", type="oil", label="oil", phrase="a tiny bottle of oil"))

    hero.memes["love"] += 1.0
    hero.memes["curiosity"] += 1.0
    friend.memes["joy"] += 1.0

    world.say(intro_line(hero, friend, blanket, remote))
    world.para()

    blanket.meters["broken"] += 1.0
    apply_rust(world, remote)
    hero.memes["worry"] += 1.0
    friend.memes["worry"] += 1.0

    world.say(conflict_line(hero, blanket, remote))
    world.say(dialogue_warning(hero, friend, blanket, remote))
    world.para()

    if not can_fix_remote(world):
        raise StoryError("This story needs both a patch and oil so the animals can fix the seam and the rust.")

    repair_seam(world, blanket, patch)
    oil_remote(world, remote, oil)
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0

    world.say(resolution_line(hero, friend, blanket, remote))
    world.say(ending_line(hero, friend, blanket, remote))

    world.facts = {
        "hero": hero,
        "friend": friend,
        "blanket": blanket,
        "remote": remote,
        "patch": patch,
        "oil": oil,
        "setting": setting,
        "seam_fixed": not seam_is_torn(blanket),
        "rust_fixed": not remote_is_rusty(remote),
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        "Write a short Animal Story about a child animal, a torn seam, a rusty remote, and a kind repair.",
        f"Tell a gentle story where {hero.id} and {friend.id} talk about a seam and a remote that needs help.",
        "Write a child-friendly dialogue story that ends with the animals fixing both the seam and the rust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    blanket: Entity = f["blanket"]  # type: ignore[assignment]
    remote: Entity = f["remote"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What did {hero.id} love in the story?",
            answer=f"{hero.id} loved the little remote because it could make the toys sing and dance.",
        ),
        QAItem(
            question=f"What happened to the blanket at {setting.place}?",
            answer=f"The seam in the blanket tore open when {hero.id} tugged too hard.",
        ),
        QAItem(
            question=f"Why did the remote stop working well?",
            answer="A little rust had crept inside the remote, so the button stuck.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=f"They used a patch to close the seam and a tiny bit of oil to loosen the rust in the remote.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} sitting on the repaired blanket and laughing as the remote worked again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seam?",
            answer="A seam is the line where two pieces of cloth are stitched together.",
        ),
        QAItem(
            question="What is rust?",
            answer="Rust is a reddish, flaky coating that can form on metal when it gets wet for a long time.",
        ),
        QAItem(
            question="What does a remote do?",
            answer="A remote lets you control a toy or machine from a little distance away.",
        ),
        QAItem(
            question="Why can oil help a stuck part?",
            answer="Oil can help moving parts slide more easily, so something stuck can begin to move again.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A seam is torn when a blanket is broken.
torn_seam(B) :- blanket(B), broken(B).

% A remote is rusty when it has rust.
rusty_remote(R) :- remote(R), rust(R).

% A fix is reasonable when the world contains both a patch and oil.
has_fix :- patch(P), oil(O), blanket(B), remote(R), torn_seam(B), rusty_remote(R).

valid_story(Place, HeroType, FriendType) :-
    setting(Place),
    animal(HeroType),
    animal(FriendType),
    has_fix.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for t in HERO_TYPES:
        lines.append(asp.fact("animal", t))
    for t in FRIEND_TYPES:
        lines.append(asp.fact("animal", t))
    lines.append(asp.fact("blanket", "blanket"))
    lines.append(asp.fact("remote", "remote"))
    lines.append(asp.fact("patch", "patch"))
    lines.append(asp.fact("oil", "oil"))
    lines.append(asp.fact("broken", "blanket"))
    lines.append(asp.fact("rust", "remote"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(place, h, f) for place in SETTINGS for h in HERO_TYPES for f in FRIEND_TYPES}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches Python expectations ({len(got)} combos).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(got - expected))
    print("only in Python:", sorted(expected - got))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="shed", hero_type="rabbit", friend_type="fox", name="Pip", friend_name="Tara"),
    StoryParams(place="barn", hero_type="squirrel", friend_type="bear", name="Suki", friend_name="Benny"),
    StoryParams(place="porch", hero_type="fox", friend_type="rabbit", name="Finn", friend_name="Nina"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with a seam, a remote, and rust.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    name = args.name or rng.choice(CHARACTER_NAMES[hero_type])
    friend_name = args.friend_name or rng.choice(CHARACTER_NAMES[friend_type])

    if name == friend_name:
        friend_name = random.choice([n for n in CHARACTER_NAMES[friend_type] if n != friend_name])

    return StoryParams(
        place=place,
        hero_type=hero_type,
        friend_type=friend_type,
        name=name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_type, params.friend_type, params.name, params.friend_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible story triples:")
        for row in asp_valid_stories():
            print(" ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} ({p.hero_type} + {p.friend_type})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
