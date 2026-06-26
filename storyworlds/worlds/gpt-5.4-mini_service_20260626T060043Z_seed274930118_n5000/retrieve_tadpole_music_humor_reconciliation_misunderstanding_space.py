#!/usr/bin/env python3
"""
Story world: a small space-adventure tale about a lost music thing, a tadpole,
a funny misunderstanding, and a gentle reconciliation.

The world is intentionally narrow: a child astronaut and a helper bot live on a
small orbital habitat with a moon-pool greenhouse. A tiny tadpole keeps ending
up near the music module, which creates a misunderstanding. In the end, the
tadpole helps retrieve the music while the characters reconcile.
"""

from __future__ import annotations

import argparse
import copy
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
    room: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "captain"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "pilot"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Habitat:
    name: str = "the Star Sprout Station"
    places: list[str] = field(default_factory=lambda: ["bridge", "greenhouse", "moon pool", "hallway"])
    music_rooms: set[str] = field(default_factory=lambda: {"bridge", "greenhouse", "hallway"})
    water_rooms: set[str] = field(default_factory=lambda: {"moon pool", "greenhouse"})


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Nova"
    helper: str = "Orb"
    place: str = "the Star Sprout Station"


class World:
    def __init__(self, habitat: Habitat) -> None:
        self.habitat = habitat
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        w = World(self.habitat)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _spills(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rush", 0) < THRESHOLD:
            continue
        if actor.meters.get("slip", 0) < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["embarrassment"] = actor.memes.get("embarrassment", 0) + 1
        out.append(f"{actor.id} made a tiny clumsy wobble and nearly bumped the console.")
    return out


def _soften(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("apology", 0) < THRESHOLD:
            continue
        if actor.memes.get("hurt", 0) < THRESHOLD:
            continue
        sig = ("soften", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hurt"] = 0
        actor.memes["warmth"] = actor.memes.get("warmth", 0) + 1
        out.append(f"{actor.id} felt a little better after hearing the kind words.")
    return out


CAUSAL_RULES = [
    _spills,
    _soften,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    habitat = Habitat(name=params.place)
    world = World(habitat)

    child = world.add(Entity(
        id=params.name, kind="character", type="girl", label=params.name,
        traits=["curious", "brave"],
        memes={"humor": 0.0, "frustration": 0.0, "joy": 0.0, "misunderstanding": 0.0, "reconciliation": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper, kind="character", type="robot", label=params.helper,
        traits=["careful", "literal"],
        memes={"humor": 0.0, "frustration": 0.0, "joy": 0.0, "misunderstanding": 0.0, "reconciliation": 0.0},
    ))
    tadpole = world.add(Entity(
        id="tadpole", kind="character", type="tadpole", label="tiny tadpole",
        traits=["wriggly", "tiny"],
        room="moon pool",
        memes={"humor": 0.0, "joy": 0.0, "misunderstanding": 0.0},
    ))
    music = world.add(Entity(
        id="music", kind="thing", type="music", label="music module",
        phrase="a little silver music module",
        room="bridge",
        owner=child.id,
        caretaker=helper.id,
    ))

    world.facts.update(child=child, helper=helper, tadpole=tadpole, music=music)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    tadpole: Entity = f["tadpole"]
    music: Entity = f["music"]

    world.say(
        f"On the Star Sprout Station, {child.id} loved listening to the little music module "
        f"while drifting past the bright windows."
    )
    world.say(
        f"{helper.id} kept the bridge neat, and {child.id} joked that even the blinking panels "
        f"looked like sleepy stars."
    )

    world.para()
    world.say(
        f"One day, the music module went missing from the bridge."
    )
    world.say(
        f"{child.id} and {helper.id} searched the hallway, the greenhouse, and the moon pool."
    )

    world.para()
    child.meters["rush"] = 1
    child.meters["slip"] = 1
    child.memes["misunderstanding"] = 1
    helper.memes["misunderstanding"] = 1
    helper.meters["rush"] = 1
    world.say(
        f"Then {helper.id} pointed at the moon pool and said, "
        f'"That tadpole must have taken the music!"'
    )
    world.say(
        f"{child.id} stared. The tiny tadpole only blinked, and its tail made a silly little loop in the water."
    )
    world.say(
        f"{child.id} nearly laughed, because the tadpole looked much too small for such a big-space crime."
    )
    propagate(world)

    world.para()
    tadpole.memes["humor"] = 1
    child.memes["humor"] = 1
    helper.memes["hurt"] = 1
    world.say(
        f"{child.id} followed the ripples and saw something shiny stuck near a floating fern."
    )
    world.say(
        f"It was the music module, bobbing on a leaf like a tiny silver boat."
    )
    world.say(
        f"The tadpole had not stolen it at all; it had only nudged the leaf with a splashy little wiggle."
    )
    world.say(
        f"{child.id} giggled, and even {helper.id} gave a quiet robot whirr that sounded like a chuckle."
    )

    world.para()
    child.memes["reconciliation"] = 1
    helper.memes["reconciliation"] = 1
    helper.memes["apology"] = 1
    world.say(
        f"{helper.id} lowered its voice and said sorry for jumping to the wrong idea."
    )
    world.say(
        f"{child.id} smiled and said the station was safer when everyone checked the facts before blaming a tiny tadpole."
    )
    world.say(
        f"Together they lifted the music module from the leaf, and the tadpole swished happily beside them."
    )
    world.say(
        f"That night the bridge filled with gentle music again, and the tadpole drifted in circles as if it were dancing in zero gravity."
    )

    world.facts.update(
        resolved=True,
        misunderstanding=True,
        reconciliation=True,
        humor=True,
        music_room="bridge",
        tadpole_room="moon pool",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        f"Write a short space adventure story about {child.id}, a tiny tadpole, and a missing music module.",
        "Tell a funny story where a small misunderstanding on a space station turns into a gentle reconciliation.",
        "Write a child-friendly adventure about retrieving music from a moon pool with a tadpole nearby.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question=f"What did {child.id} love on the station?",
            answer=f"{child.id} loved listening to the little music module while floating past the windows.",
        ),
        QAItem(
            question="What did the helper think had happened to the music module?",
            answer=f"{helper.id} thought the tiny tadpole had taken the music module, but that was a misunderstanding.",
        ),
        QAItem(
            question="Where was the music module found?",
            answer="It was found in the moon pool, stuck near a floating fern on a leaf.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The helper apologized, the child forgave the mistake, and everyone enjoyed the music again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tadpole?",
            answer="A tadpole is a young frog or toad with a round body and a tail that helps it swim.",
        ),
        QAItem(
            question="What is music?",
            answer="Music is organized sound that people can hear, sing, hum, or play on instruments.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace after a disagreement.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something happened, but the real story is different.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.room:
            bits.append(f"room={e.room}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("character", "child"))
    lines.append(asp.fact("character", "helper"))
    lines.append(asp.fact("character", "tadpole"))
    lines.append(asp.fact("thing", "music"))
    lines.append(asp.fact("room", "bridge"))
    lines.append(asp.fact("room", "greenhouse"))
    lines.append(asp.fact("room", "moon_pool"))
    lines.append(asp.fact("room", "hallway"))
    lines.append(asp.fact("belongs_to", "music", "child"))
    lines.append(asp.fact("kept_by", "music", "helper"))
    lines.append(asp.fact("in_room", "tadpole", "moon_pool"))
    lines.append(asp.fact("in_room", "music", "bridge"))
    lines.append(asp.fact("supports_music", "bridge"))
    lines.append(asp.fact("supports_music", "greenhouse"))
    lines.append(asp.fact("supports_music", "hallway"))
    lines.append(asp.fact("supports_water", "moon_pool"))
    lines.append(asp.fact("supports_water", "greenhouse"))
    lines.append(asp.fact("cute_small_creature", "tadpole"))
    lines.append(asp.fact("story_theme", "misunderstanding"))
    lines.append(asp.fact("story_theme", "humor"))
    lines.append(asp.fact("story_theme", "reconciliation"))
    return "\n".join(lines)


ASP_RULES = r"""
#show needs_retrieve/1.
#show misunderstanding/1.
#show reconciles/1.

needs_retrieve(M) :- thing(M), in_room(M, bridge).
misunderstanding(H) :- character(H), story_theme(misunderstanding).
reconciles(H) :- character(H), story_theme(reconciliation).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show needs_retrieve/1. #show misunderstanding/1. #show reconciles/1."))
    atoms = set((sym.name, tuple(a.string if a.type.name == "String" else a.number if a.type.name == "Number" else a.name for a in sym.arguments)) for sym in model)
    wanted = {("needs_retrieve", ("music",)), ("misunderstanding", ("child",)), ("misunderstanding", ("helper",)), ("reconciles", ("child",)), ("reconciles", ("helper",))}
    return 0 if wanted.issubset(atoms) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about retrieving music after a tadpole misunderstanding.")
    ap.add_argument("--name", default="Nova")
    ap.add_argument("--helper", default="Orb")
    ap.add_argument("--place", default="the Star Sprout Station")
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(["Nova", "Pip", "Luna", "Kite"]),
        helper=args.helper or rng.choice(["Orb", "Bix", "Dot", "Zed"]),
        place=args.place,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show needs_retrieve/1. #show misunderstanding/1. #show reconciles/1."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show needs_retrieve/1. #show misunderstanding/1. #show reconciles/1."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed)))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
