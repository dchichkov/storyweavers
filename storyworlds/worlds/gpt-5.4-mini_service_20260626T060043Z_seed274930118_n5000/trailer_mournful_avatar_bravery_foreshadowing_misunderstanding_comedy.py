#!/usr/bin/env python3
"""
A small story world about a brave kid, a mistaken idea, and a cheerful fix in a
trailer park.

Premise:
- A child in a trailer loves a little avatar figure in a game.
- A harmless, well-meaning warning is misunderstood.
- The child gathers bravery, clarifies the mistake, and makes a funny, happy ending.

The world is intentionally small and constraint-driven:
- typed entities with meters and memes
- a simulated state that changes over time
- a Python reasonableness gate
- an inline ASP twin for parity checks
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
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    place: str
    inside: bool = True
    supports: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ObjectConfig:
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass(frozen=True)
class SceneConfig:
    id: str
    verb: str
    gerund: str
    fear: str
    misunderstanding: str
    resolution: str
    risk: str
    emote: str
    topic: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "trailer": Setting(place="the trailer", inside=True, supports={"game", "snack", "talk"}),
    "porch": Setting(place="the porch", inside=False, supports={"talk", "game"}),
    "yard": Setting(place="the yard", inside=False, supports={"game", "talk"}),
}

SCENES = {
    "avatar": SceneConfig(
        id="avatar",
        verb="play with the avatar",
        gerund="playing with the little avatar",
        fear="the avatar might be lost in the game",
        misunderstanding="the warning was about the avatar's helmet, not the child",
        resolution="the avatar should just wear the helmet",
        risk="the helmet could be dropped",
        emote="mournful",
        topic="avatar",
        tags={"avatar", "game", "helmet"},
    ),
    "trailer": SceneConfig(
        id="trailer",
        verb="decorate the trailer",
        gerund="decorating the trailer",
        fear="the trailer might look silly before guests arrive",
        misunderstanding="the note was about tape, not trouble",
        resolution="the streamer should be hung higher",
        risk="the streamer could slip",
        emote="mournful",
        topic="trailer",
        tags={"trailer"},
    ),
}

OBJECTS = {
    "helmet": ObjectConfig(label="helmet", phrase="a tiny shiny helmet", region="head", fragile=True),
    "streamer": ObjectConfig(label="streamer", phrase="a long paper streamer", region="hands", fragile=True),
}

CHAR_NAMES = ["Milo", "Nina", "Toby", "Rae", "Pip", "Lena", "Jude", "Zara"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    scene: str
    name: str
    parent: str = "mother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _inc(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


def _text_place(place: str) -> str:
    return SETTINGS[place].place


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def predict_problem(world: World, hero: Entity, obj: Entity, scene: SceneConfig) -> dict:
    sim = world.copy()
    _do_scene(sim, hero.id, scene, obj.id, narrate=False)
    thing = sim.get(obj.id)
    return {
        "broken": thing.meters.get("broken", 0.0) >= THRESHOLD,
        "conflict": sim.facts.get("conflict", False),
    }


def _do_scene(world: World, hero_id: str, scene: SceneConfig, obj_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    obj = world.get(obj_id)
    _inc(hero.memes, "curiosity")
    _inc(hero.memes, "joy")
    _inc(obj.meters, "risk")
    if scene.id == "avatar":
        _inc(obj.meters, "wobble")
        if obj.meters.get("wobble", 0.0) >= THRESHOLD:
            _inc(obj.meters, "broken")
    else:
        _inc(obj.meters, "stuck")
        if obj.meters.get("stuck", 0.0) >= THRESHOLD:
            _inc(obj.meters, "broken")
    if narrate:
        world.say(f"{hero.id} tried to {scene.verb}, and the room got a little noisier.")


def introduce(world: World, hero: Entity, parent: Entity, obj: Entity, scene: SceneConfig) -> None:
    world.say(
        f"{hero.id} was a little {scene.emote} {hero.type} who lived in {_text_place(world.place)} with {parent.pronoun('possessive')} careful grown-up."
    )
    world.say(
        f"{hero.id} loved {scene.gerund} with {obj.phrase}, because it felt like a tiny adventure."
    )


def foreshadow(world: World, parent: Entity, hero: Entity, obj: Entity, scene: SceneConfig) -> None:
    _inc(parent.memes, "foresight")
    world.say(
        f"Before the fun began, {parent.pronoun().capitalize()} gave a gentle warning: "
        f'"If {hero.id} is too fast, {obj.label} could get {scene.risk}."'
    )
    world.say(
        f"{hero.id} heard the words, but only caught the shiny part and not the caution."
    )


def misunderstanding(world: World, hero: Entity, parent: Entity, obj: Entity, scene: SceneConfig) -> None:
    _inc(hero.memes, "misunderstanding")
    _inc(hero.memes, "mournful")
    world.say(
        f"{hero.id} made a mournful face and said, 'Oh no, {obj.label}! Did I do something wrong?'"
    )
    world.say(
        f"{parent.pronoun().capitalize()} blinked and laughed a little. "
        f'"No, no," {parent.pronoun("subject")} said. "I meant the {obj.label}, not you."'
    )


def bravery(world: World, hero: Entity, parent: Entity, obj: Entity, scene: SceneConfig) -> None:
    _inc(hero.memes, "bravery")
    _inc(hero.memes, "relief")
    world.say(
        f"That took bravery, so {hero.id} took a deep breath and asked a better question."
    )
    world.say(
        f"Then {hero.id} and {parent.pronoun('subject')} fixed the plan together, because the {scene.topic} idea was never bad."
    )


def resolution(world: World, hero: Entity, parent: Entity, obj: Entity, scene: SceneConfig) -> None:
    if scene.id == "avatar":
        _inc(obj.meters, "safe")
        world.say(
            f"They put the tiny helmet on the avatar, and the little figure stayed safe while {hero.id} cheered."
        )
        world.say(
            f"{hero.id} laughed so hard that even the mournful face turned into a grin."
        )
    else:
        _inc(obj.meters, "safe")
        world.say(
            f"They moved the streamer higher, and the trailer looked fancy instead of fussy."
        )
        world.say(
            f"{hero.id} smiled, because the big worry had been only a misunderstanding with a funny wiggle to it."
        )


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    world = World(place=params.place)
    hero = world.add(Entity(id=params.name, kind="character", type="boy", meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, meters={}, memes={}))
    obj_cfg = OBJECTS["helmet"] if params.scene == "avatar" else OBJECTS["streamer"]
    obj = world.add(Entity(
        id=obj_cfg.label,
        kind="thing",
        type=obj_cfg.label,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        meters={},
        memes={},
    ))
    scene = SCENES[params.scene]

    introduce(world, hero, parent, obj, scene)
    world.para()
    foreshadow(world, parent, hero, obj, scene)
    _do_scene(world, hero.id, scene, obj.id)
    world.para()
    misunderstanding(world, hero, parent, obj, scene)
    bravery(world, hero, parent, obj, scene)
    resolution(world, hero, parent, obj, scene)

    world.facts.update(
        hero=hero,
        parent=parent,
        obj=obj,
        scene=scene,
        conflict=True,
        resolved=True,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for scene in SCENES.values():
            if scene.id == "avatar" and place in {"trailer", "porch", "yard"}:
                out.append((place, scene.id))
            if scene.id == "trailer" and place in {"trailer"}:
                out.append((place, scene.id))
    return out


def explain_rejection(place: str, scene: str) -> str:
    if (place, scene) not in valid_combos():
        return "(No story: that scene does not fit this setting in a believable way.)"
    return "(No story: invalid combination.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        f'Write a short comedic story for a child in {world.place} about {hero.id} and a {scene.topic}.',
        f'Tell a gentle story where a {hero.id} feels mournful for a moment, then shows bravery after a misunderstanding.',
        f'Write a story with foreshadowing in which a warning turns out to be about the object, not the child.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    scene = f["scene"]
    obj = f["obj"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where does {hero.id} live in the story?",
            answer=f"{hero.id} lives in {_text_place(place)} with {parent.pronoun('possessive')} careful grown-up.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {obj.label}?",
            answer=f"{hero.id} wanted to {scene.verb}, because it felt like a tiny adventure.",
        ),
        QAItem(
            question=f"Why did {hero.id} first look mournful?",
            answer=f"{hero.id} looked mournful because the warning sounded scary before it was understood correctly.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding?",
            answer=f"{hero.id} asked a better question, and then {parent.pronoun('subject')} explained that the warning was about the {obj.label}, not about {hero.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    if scene.id == "avatar":
        return [
            QAItem(
                question="What is an avatar in a game?",
                answer="An avatar is a character or picture that stands in for a player in a game.",
            ),
            QAItem(
                question="What does bravery mean?",
                answer="Bravery means doing something even when you feel nervous, worried, or shy.",
            ),
            QAItem(
                question="What is foreshadowing?",
                answer="Foreshadowing is a little clue that hints something important may happen later.",
            ),
            QAItem(
                question="What is a misunderstanding?",
                answer="A misunderstanding happens when people think something means one thing, but it really means something else.",
            ),
        ]
    return [
        QAItem(
            question="What is a trailer?",
            answer="A trailer is a small home or room on wheels, or a movable home that can be parked in one place.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints at a later event.",
        ),
        QAItem(
            question="What does mournful mean?",
            answer="Mournful means sad and downhearted, like when someone looks like they might cry.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Scene) :- place(Place), scene(Scene), compatible(Place, Scene).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for scene in SCENES:
        lines.append(asp.fact("scene", scene))
    for place, scene in valid_combos():
        lines.append(asp.fact("compatible", place, scene))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python for {len(python_set)} combos.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Python only:", sorted(python_set - asp_set))
    print("ASP only:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedic trailer world with bravery and misunderstanding.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--scene", choices=sorted(SCENES))
    ap.add_argument("--name", choices=CHAR_NAMES)
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
    combos = valid_combos()
    if args.place and args.scene and (args.place, args.scene) not in combos:
        raise StoryError(explain_rejection(args.place, args.scene))
    filtered = [
        (p, s) for p, s in combos
        if (args.place is None or p == args.place)
        and (args.scene is None or s == args.scene)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, scene = rng.choice(sorted(filtered))
    name = args.name or rng.choice(CHAR_NAMES)
    return StoryParams(place=place, scene=scene, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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
    StoryParams(place="trailer", scene="avatar", name="Milo"),
    StoryParams(place="porch", scene="avatar", name="Nina"),
    StoryParams(place="yard", scene="avatar", name="Toby"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"compatible combos: {len(valid_combos())}")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
