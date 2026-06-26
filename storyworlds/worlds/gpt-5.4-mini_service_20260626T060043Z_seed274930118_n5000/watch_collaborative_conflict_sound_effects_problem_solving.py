#!/usr/bin/env python3
"""
storyworlds/worlds/watch_collaborative_conflict_sound_effects_problem_solving.py
================================================================================

A small ghost-story-style simulation about a watch, collaborative problem solving,
conflict, and sound effects.

Seed tale sketch:
---
At dusk, a child found an old watch that ticked in an empty hallway. Every time
the watch chimed, the house answered with strange little sounds: tap, hush, creak.
A shy ghost appeared and wanted the watch back. The child wanted to keep it and
solve the mystery. At first they argued, but then they listened together, followed
the sounds, and discovered the watch was not haunting the house by itself. It was
warning them about a stuck window and a cold draft. By working together, they fixed
the problem, and the ghost finally smiled.

Design notes:
- The world tracks physical meters and emotional memes.
- Sound effects are stateful clues that reveal hidden problems.
- Conflict rises when the child and ghost want different outcomes.
- Collaborative problem solving lowers conflict and resolves the haunting.
- Story prose is authored from simulation state, not swapped templates.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def init_meters(self) -> None:
        for key in ("ticking", "haunting", "draft", "sound"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "fear", "conflict", "trust", "joy", "resolve", "care"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str = "the old house"
    room: str = "the hallway"
    mood: str = "quiet and dim"


@dataclass
class Watch:
    label: str
    phrase: str
    sound: str
    clue: str
    problem: str
    fix: str


@dataclass
class StoryParams:
    place: str
    name: str
    ghost_name: str
    watch: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        ent.init_meters()
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


WATCHES = {
    "gold_watch": Watch(
        label="gold watch",
        phrase="an old gold watch with a cracked face",
        sound="tick-tick",
        clue="the window was stuck open",
        problem="a cold draft kept slipping into the hallway",
        fix="close the window and lock it tight",
    ),
    "silver_watch": Watch(
        label="silver watch",
        phrase="a silver pocket watch with a soft blue shine",
        sound="tik-tak",
        clue="the cellar door was bumping in the wind",
        problem="the draft from below was making the house shiver",
        fix="push the cellar door shut and tie the latch",
    ),
    "brass_watch": Watch(
        label="brass watch",
        phrase="a brass watch with tiny dents on the rim",
        sound="click-clack",
        clue="the attic hinge was loose",
        problem="each gust made the attic flap tap like a nervous finger",
        fix="hold the hatch closed and wedge it with a board",
    ),
}

PLACES = {
    "house": Setting(place="the old house", room="the hallway", mood="quiet and dim"),
    "manor": Setting(place="the crooked manor", room="the front hall", mood="blue-gray and still"),
    "cottage": Setting(place="the candlelit cottage", room="the stair landing", mood="soft and hushy"),
}

NAMES = ["Mina", "Eli", "Nora", "Iris", "Jun", "Tessa", "Ari", "Milo"]
GHOST_NAMES = ["Pale Pip", "Murmur", "Bell", "Wisp", "Moth"]
WATCH_ORDER = ["gold_watch", "silver_watch", "brass_watch"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about a watch, conflict, and collaborative problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--watch", choices=WATCHES)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
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
    place = args.place or rng.choice(list(PLACES))
    watch = args.watch or rng.choice(list(WATCHES))
    name = args.name or rng.choice(NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, name=name, ghost_name=ghost_name, watch=watch)


def make_world(params: StoryParams) -> World:
    setting = PLACES[params.place]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", label=params.ghost_name))
    watch = world.add(Entity(id="watch", kind="thing", type="watch", label=WATCHES[params.watch].label, phrase=WATCHES[params.watch].phrase))

    world.facts.update(child=child, ghost=ghost, watch=watch, watch_cfg=WATCHES[params.watch], setting=setting)
    return world


def nudge(world: World, actor: Entity, key: str, amount: float = 1.0) -> None:
    actor.meters[key] = actor.meters.get(key, 0.0) + amount


def nudge_meme(world: World, actor: Entity, key: str, amount: float = 1.0) -> None:
    actor.memes[key] = actor.memes.get(key, 0.0) + amount


def predictive_signal(world: World, watch: Entity, watch_cfg: Watch) -> bool:
    return True


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    watch: Entity = f["watch"]
    cfg: Watch = f["watch_cfg"]
    setting: Setting = f["setting"]

    # Act 1
    world.say(f"{setting.place.capitalize()} was quiet and dim, and {child.id} found {watch.phrase} in {setting.room}.")
    world.say(f"It went {cfg.sound}, a tiny sound that made the hallway feel awake.")
    nudge_meme(world, child, "curiosity", 1)
    nudge(world, watch, "ticking", 1)

    # Act 2
    world.para()
    world.say(f"Then a shy ghost drifted out of the shadow and said, \"That watch belongs with me.\"")
    nudge_meme(world, ghost, "fear", 1)
    nudge_meme(world, child, "fear", 1)
    nudge_meme(world, child, "conflict", 1)
    nudge_meme(world, ghost, "conflict", 1)
    world.say(f"{child.id} clutched the watch and said they wanted to keep listening.")
    world.say(f"The ghost frowned, and the little room filled with a worried hush.")

    # Sound clue escalates
    world.say(f"Again the watch went {cfg.sound}, and the walls answered with a faint creak.")
    nudge(world, watch, "sound", 1)
    nudge(world, watch, "haunting", 1)
    nudge(world, watch, "draft", 1)

    # Act 3 collaborative problem solving
    world.para()
    world.say(f"{child.id} and the ghost stopped arguing and listened together.")
    nudge_meme(world, child, "trust", 1)
    nudge_meme(world, ghost, "trust", 1)
    nudge_meme(world, child, "resolve", 1)
    nudge_meme(world, ghost, "resolve", 1)

    world.say(f"They followed the sound and found {cfg.clue}.")
    world.say(f"That was the real problem: {cfg.problem}.")
    world.say(f"Together they chose to {cfg.fix}, and the hallway grew still.")

    world.say(f"The watch gave one last soft {cfg.sound}, then rested in {ghost.id}'s hand without a shiver.")
    child.memes["conflict"] = 0.0
    ghost.memes["conflict"] = 0.0
    nudge_meme(world, child, "joy", 1)
    nudge_meme(world, ghost, "joy", 1)

    world.facts["resolved"] = True


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cfg: Watch = f["watch_cfg"]
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    return [
        'Write a short ghost story for a young child about a watch that makes strange sound effects and leads to collaborative problem solving.',
        f"Tell a gentle spooky story where {child.id} and {ghost.id} disagree about {cfg.label}, then solve the mystery together.",
        f"Write a child-friendly ghost story that includes the sound {cfg.sound} and ends with a solved hallway problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    cfg: Watch = f["watch_cfg"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.id} find in {setting.room}?",
            answer=f"{child.id} found {cfg.phrase} in {setting.room}.",
        ),
        QAItem(
            question=f"What sound did the watch make before the conflict grew?",
            answer=f"The watch went {cfg.sound}.",
        ),
        QAItem(
            question=f"Why did {child.id} and {ghost.id} stop arguing?",
            answer=f"They stopped arguing so they could solve the mystery together and listen to the clue in the sound.",
        ),
        QAItem(
            question=f"What was the real problem behind the spooky sounds?",
            answer=f"The real problem was that {cfg.problem}.",
        ),
        QAItem(
            question=f"How did the story end for the watch?",
            answer=f"The watch rested quietly after they worked together to {cfg.fix}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a watch for?",
            answer="A watch is a small timepiece that helps people tell time by ticking or chiming.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are little words that suggest noises, like creak, tap, or tick-tick.",
        ),
        QAItem(
            question="What does collaborative mean?",
            answer="Collaborative means working together with someone else to do a job or solve a problem.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong and finding a good way to fix it.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
child_wants_keep(C) :- child(C).
ghost_wants_return(G) :- ghost(G).

conflict(C,G) :- child_wants_keep(C), ghost_wants_return(G).
heard_sound(W) :- watch(W), soundy(W).
clue_found(W) :- heard_sound(W), problem_clue(W).

solved(C,G,W) :- conflict(C,G), clue_found(W), collaborative(C,G), fixable(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("room", pid, setting.room))
    for wid, w in WATCHES.items():
        lines.append(asp.fact("watch", wid))
        lines.append(asp.fact("soundy", wid))
        lines.append(asp.fact("problem_clue", wid))
        lines.append(asp.fact("fixable", wid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("collaborative", "child", "ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/3."))
    return sorted(set(asp.atoms(model, "solved")))


def python_valid() -> list[tuple]:
    return [("child", "ghost", wid) for wid in WATCHES]


def asp_verify() -> int:
    a, b = set(asp_valid()), set(python_valid())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} solved templates).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in asp:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        name=args.name or rng.choice(NAMES),
        ghost_name=args.ghost_name or rng.choice(GHOST_NAMES),
        watch=args.watch or rng.choice(list(WATCHES)),
    )


def curried_all() -> list[StoryParams]:
    return [
        StoryParams(place="house", name="Mina", ghost_name="Pale Pip", watch="gold_watch"),
        StoryParams(place="manor", name="Eli", ghost_name="Wisp", watch="silver_watch"),
        StoryParams(place="cottage", name="Nora", ghost_name="Bell", watch="brass_watch"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/3."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curried_all()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name} / {p.ghost_name} / {p.watch}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
