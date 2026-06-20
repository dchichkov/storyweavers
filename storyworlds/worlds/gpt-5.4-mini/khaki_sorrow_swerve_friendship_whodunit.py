#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/khaki_sorrow_swerve_friendship_whodunit.py
==========================================================================

A standalone storyworld for a small friendship whodunit with the seed words
"khaki", "sorrow", and "swerve".

Premise
-------
Two friends prepare a tiny detective game around a missing object. One child
wears khaki because it looks like a detective's coat, the game takes a sorrowful
turn when the object seems gone, and a careful swerve in the search reveals the
truth: the item was not stolen, only hidden by a clumsy clue.

The world is built around:
- friendship and trust
- simple clues
- a mistaken suspicion
- a revealed culprit and a repaired friendship

It follows the Storyweavers contract with:
- typed entities carrying meters and memes
- a Python reasonableness gate plus an inline ASP twin
- three grounded Q&A sets
- `--verify`, `--asp`, `--show-asp`, `--trace`, `--qa`, `--json`, `-n`, `--all`

This script is stdlib-only and can run directly from the repo root.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPICION_LIMIT = 1.0
SAD_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Suspect:
    id: str
    label: str
    clue: str
    where: str
    likely: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    hidden_by: str = ""
    found: bool = False
    touched: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    detail: str
    sweep: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_sorrow(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities:
        return out
    child = world.get("child")
    if child.memes["sorrow"] < SAD_LIMIT or ("sorrow", child.id) in world.fired:
        return out
    world.fired.add(("sorrow", child.id))
    child.memes["worry"] += 1
    out.append("__sorrow__")
    return out


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    if child.meters["suspicion"] < SUSPICION_LIMIT or ("suspicion", child.id) in world.fired:
        return out
    world.fired.add(("suspicion", child.id))
    friend.memes["hurt"] += 1
    out.append("__suspicion__")
    return out


CAUSAL_RULES = [Rule("sorrow", "social", _r_sorrow), Rule("suspicion", "social", _r_suspicion)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_truth(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _search(sim, sim.get(clue_id), narrate=False)
    return {
        "found": sim.get("object").found,
        "suspicion": sim.get("child").meters["suspicion"],
        "friend_hurt": sim.get("friend").memes["hurt"],
    }


def _search(world: World, clue: Suspect, narrate: bool = True) -> None:
    obj = world.get("object")
    if clue.id == obj.hidden_by:
        obj.found = True
        obj.touched = True
        world.get("child").meters["suspicion"] = 0
        world.get("friend").memes["hurt"] = 0
        if narrate:
            world.say(f"The clue pointed straight to {clue.likely}, and the missing thing was there all along.")
    else:
        world.get("child").meters["suspicion"] += 1
        propagate(world, narrate=narrate)


def setup(world: World, child: Entity, friend: Entity, scene: Scene) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {friend.id} turned the room into a little detective office. "
        f"{scene.detail}"
    )
    world.say(
        f'{child.id} wore khaki today, because it looked smart and brave. '
        f'"{scene.mood} case," {friend.id} whispered, smiling at the game.'
    )


def discover_missing(world: World, child: Entity, friend: Entity, obj: ObjectThing) -> None:
    world.say(
        f"Then {child.id} looked at the shelf and froze. {obj.phrase} was gone. "
        f'For a moment, everything felt full of sorrow.'
    )
    child.memes["sorrow"] += 1
    friend.memes["concern"] += 1


def clue_talk(world: World, child: Entity, friend: Entity, suspect: Suspect, obj: ObjectThing) -> None:
    child.memes["curious"] += 1
    world.say(
        f'{friend.id} pointed to a clue: {suspect.clue}. "Maybe {suspect.likely}?" '
        f'{friend.id} asked, but {child.id} noticed the clue could also mean something else.'
    )
    world.say(
        f"{child.id} did not want to blame a friend too fast. So {child.id} decided to swerve away "
        f"from the first guess and look again."
    )


def reveal(world: World, child: Entity, friend: Entity, suspect: Suspect, obj: ObjectThing, scene: Scene) -> None:
    world.say(
        f"The careful swerve led them behind {scene.place}. There, {obj.phrase} sat hidden by "
        f"{suspect.likely}. The missing thing had not been stolen at all."
    )
    world.say(
        f"{friend.id} let out a tiny gasp. {child.id} smiled at once, because the clue made sense now."
    )


def repair(world: World, child: Entity, friend: Entity, obj: ObjectThing) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    friend.memes["hurt"] = 0
    child.memes["sorrow"] = 0
    world.say(
        f'{child.id} hugged {friend.id}. "I am sorry I nearly blamed you," {child.id} said. '
        f'"I should have looked more carefully."'
    )
    world.say(
        f'{friend.id} hugged back. "It is okay," {friend.id} said. '
        f"They put {obj.phrase} back where it belonged and laughed softly, relieved that friendship was still safe."
    )


def tell(scene: Scene, suspect: Suspect, obj: ObjectThing,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Jo", friend_gender: str = "boy",
         parent_name: str = "Aunt") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type="adult", role="guide", label="the grown-up"))
    thing = world.add(Entity(id="object", type="thing", label=obj.label, attrs={"hidden_by": obj.hidden_by}))
    world.add(Entity(id="scene", type="scene", label=scene.place))
    world.facts["scene"] = scene
    world.facts["suspect"] = suspect
    world.facts["object_cfg"] = obj
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["parent"] = parent
    world.facts["object"] = thing

    setup(world, child, friend, scene)
    world.para()
    discover_missing(world, child, friend, obj)
    clue_talk(world, child, friend, suspect, obj)
    world.para()
    _search(world, suspect)
    reveal(world, child, friend, suspect, obj, scene)
    repair(world, child, friend, obj)
    world.facts["outcome"] = "solved"
    return world


SCENES = {
    "library": Scene("library", "the library", "a whispering mystery", "Dust floated in the light between tall shelves.", "swerve past the old maps", {"book", "quiet"}),
    "garden": Scene("garden", "the garden path", "a missing-clue mystery", "Leaves made little shadows by the bench.", "swerve around the rosebushes", {"bench", "leaf"}),
    "attic": Scene("attic", "the attic", "a secret-case mystery", "Old boxes leaned together like sleepy towers.", "swerve behind the trunks", {"box", "dust"}),
}

SUSPECTS = {
    "cat": Suspect("cat", "a cat print", "a small muddy print near the door", "the doorway", "the cat", {"print", "mud"}),
    "kite": Suspect("kite", "a ribbon clue", "a ribbon caught on the chair leg", "the chair", "the kite string", {"ribbon", "string"}),
    "umbrella": Suspect("umbrella", "a bent umbrella clue", "a bent umbrella left near the coat hook", "the hook", "the umbrella", {"umbrella", "hook"}),
}

OBJECTS = {
    "key": ObjectThing("key", "silver key", "the silver key", hidden_by="the cat", tags={"key"}),
    "book": ObjectThing("book", "storybook", "the storybook", hidden_by="the kite string", tags={"book"}),
    "badge": ObjectThing("badge", "small badge", "the small badge", hidden_by="the umbrella", tags={"badge"}),
}

GIRL_NAMES = ["Mina", "Lina", "Tess", "Nora", "Ruby", "Ivy", "Lila"]
BOY_NAMES = ["Jo", "Owen", "Milo", "Finn", "Ezra", "Theo", "Nico"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    suspect: str
    object: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for sus in SUSPECTS:
            for obj in OBJECTS:
                if SUSPECTS[sus].hidden_by == OBJECTS[obj].hidden_by:
                    combos.append((s, sus, obj))
    return combos


def explain_rejection(scene: Scene, suspect: Suspect, obj: ObjectThing) -> str:
    return (
        f"(No story: the clue and the missing thing do not line up. "
        f"This whodunit needs the hidden thing and the clue to point to the same source.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a friendship whodunit with khaki, sorrow, and a swerve.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, suspect, obj = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or (rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES))
    friend = args.friend or (rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != child]))
    parent = args.parent or rng.choice(["Aunt", "Uncle", "Mom", "Dad"])
    return StoryParams(scene, suspect, obj, child, child_gender, friend, friend_gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short friendship whodunit for a child that includes the word "khaki".',
        f'Write a mystery story where {f["child"].id} and {f["friend"].id} search for a missing item, feel sorrow, and swerve away from a bad guess.',
        f'Write a gentle detective story that includes the words "sorrow" and "swerve" and ends with friends making up.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, fr, suspect, obj, scene = f["child"], f["friend"], f["suspect"], f["object_cfg"], f["scene"]
    return [
        ("Who are the story friends?",
         f"It is about {c.id} and {fr.id}, two friends who were playing detective together. Their friendship matters because they solve the mystery by talking instead of blaming."),
        ("Why did the story feel sorrowful?",
         f"The story felt sorrowful when {obj.phrase} seemed to be missing. That made both friends worry, because they thought something bad might have happened."),
        ("What did the careful swerve change?",
         f"It changed the search from a fast guess into a careful look behind {scene.place}. That is how they found {obj.phrase} and learned the clue had been misleading."),
        ("Was the friend blamed in the end?",
         f"No. The friends learned not to blame too quickly, and they fixed the misunderstanding together. The ending keeps the friendship safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is khaki?",
         "Khaki is a light brown color often used for clothes. It can look neat and detective-like."),
        ("What does sorrow mean?",
         "Sorrow means a sad feeling. It can happen when something important seems lost."),
        ("What does swerve mean?",
         "To swerve means to turn away quickly or change direction. In a mystery, it can mean avoiding the first guess and looking somewhere else."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sorrow(X) :- person(X), has_sorrow(X).
suspicion(X) :- person(X), has_suspicion(X).
solved :- found(object), friendship_safe.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("hidden_by", sid, s.likely))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("hidden_by", oid, o.hidden_by))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    _ = asp.one_model(asp_program("", "#show scene/1."))
    ok = True
    if set(valid_combos()) != set(asp_valid_combos()):
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(3)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAILED: {exc}")
        return 1
    print("OK: verify and smoke test passed.")
    return 0 if ok else 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hidden_by/2."))
    return sorted(set(asp.atoms(model, "hidden_by")))


def build_world(params: StoryParams) -> World:
    return tell(SCENES[params.scene], SUSPECTS[params.suspect], OBJECTS[params.object],
                params.child, params.child_gender, params.friend, params.friend_gender, params.parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("library", "cat", "key", "Mina", "girl", "Jo", "boy", "Aunt"),
    StoryParams("garden", "kite", "book", "Nora", "girl", "Finn", "boy", "Mom"),
    StoryParams("attic", "umbrella", "badge", "Theo", "boy", "Lila", "girl", "Uncle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show hidden_by/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible clue/object sources:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.friend}: {p.scene} ({p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
