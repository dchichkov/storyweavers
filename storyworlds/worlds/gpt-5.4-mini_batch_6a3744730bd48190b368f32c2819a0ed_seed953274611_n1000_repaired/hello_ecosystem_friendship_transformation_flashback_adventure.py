#!/usr/bin/env python3
"""
Storyworld: hello_ecosystem_friendship_transformation_flashback_adventure
=========================================================================

A tiny adventure storyworld about two friends exploring an ecosystem,
remembering an earlier encounter in a flashback, and transforming the
destination from lonely to lively.

The story is built from state changes:
- a quiet ecosystem starts out skipped over and unfinished,
- a greeting and an old memory open a friendship,
- a small transformation changes the place,
- the ending image proves the place is now shared and alive.

This file is standalone and uses only the stdlib plus the shared
``storyworlds/results.py`` and lazy ``storyworlds/asp.py`` helpers.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    memory_hint: str
    ecosystem_word: str = "ecosystem"
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Transformation:
    id: str
    label: str
    spark: str
    result: str
    method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Flashback:
    id: str
    label: str
    cue: str
    earlier: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child_a")
    b = world.get("child_b")
    if a.memes["greeting"] < THRESHOLD or b.memes["greeting"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    out.append("__friendship__")
    return out


def _r_transformation(world: World) -> list[str]:
    place = world.get("ecosystem")
    if place.meters["changed"] < THRESHOLD:
        return []
    sig = ("transformation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["alive"] += 1
    return ["__transformed__"]


CAUSAL_RULES = [Rule("friendship", _r_friendship), Rule("transformation", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def do_hello(world: World, child: Entity, other: Entity, place: Place) -> None:
    child.memes["greeting"] += 1
    other.memes["greeting"] += 1
    world.say(
        f'At the edge of the {place.ecosystem_word}, {child.id} waved and said, "Hello!" '
        f'{other.id} smiled back, and the old path felt less lonely at once.'
    )


def flashback(world: World, child: Entity, memory: Flashback, place: Place) -> None:
    child.memes["memory"] += 1
    world.say(
        f"{child.id} paused under the reeds. The sight of the {place.ecosystem_word} "
        f"brought back {memory.earlier}. In the flashback, {memory.cue}, and "
        f"{memory.lesson}."
    )


def transform(world: World, place: Place, method: Transformation) -> None:
    eco = world.get("ecosystem")
    eco.meters["changed"] += 1
    eco.meters["seeded"] += 1
    eco.attrs["state"] = method.result
    world.say(
        f"Together they tried {method.method}. Tiny seeds, careful hands, and water "
        f"from a shell bowl made the {place.ecosystem_word} begin to change."
    )
    propagate(world, narrate=False)


def ending(world: World, child: Entity, friend: Entity, place: Place) -> None:
    eco = world.get("ecosystem")
    if eco.meters["alive"] >= THRESHOLD:
        world.say(
            f"By sunset, the place was no longer quiet. New leaves leaned toward the light, "
            f"dragonflies circled above the stream, and {child.id} and {friend.id} walked "
            f"home side by side, proud of the little world they had helped grow."
        )
    else:
        world.say(
            f"By sunset, the place had only just begun to wake up, but {child.id} and "
            f"{friend.id} promised to return and keep the {place.ecosystem_word} growing."
        )


def tell(place: Place, transformation: Transformation, flash: Flashback, *,
         child_name: str = "Mina", child_type: str = "girl",
         friend_name: str = "Kai", friend_type: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id="child_a", kind="character", type=child_type, label=child_name, role="hero"))
    friend = world.add(Entity(id="child_b", kind="character", type=friend_type, label=friend_name, role="friend"))
    world.add(Entity(id="ecosystem", kind="thing", type="place", label=place.label, attrs={"state": "quiet"}, tags=set(place.tags)))

    world.say(
        f"{child_name} followed the winding trail into the {place.label}. "
        f"It was a small {place.ecosystem_word}, with a quiet stream, soft moss, and birds "
        f"hiding in the branches."
    )
    world.say(
        f"{friend_name} was already there, kneeling beside the water. {friend_name} looked up, "
        f"waved, and the two of them began the adventure together."
    )
    do_hello(world, child, friend, place)

    world.para()
    flashback(world, child, flash, place)
    world.say(
        f"That memory made {child_name} braver. If the old moment had taught anything, it was "
        f"that a lonely place could become friendly when someone showed up with care."
    )

    world.para()
    transform(world, place, transformation)

    world.para()
    ending(world, child, friend, place)

    world.facts.update(
        child=child,
        friend=friend,
        place=place,
        transformation=transformation,
        flashback=flash,
        ecosystem=world.get("ecosystem"),
        friendship=child.memes["friendship"] >= THRESHOLD,
        changed=world.get("ecosystem").meters["changed"] >= THRESHOLD,
    )
    return world


PLACES = {
    "pond": Place(
        id="pond",
        label="pond",
        scene="a shallow pond with a muddy bank",
        memory_hint="the ducks had once splashed away without stopping",
        ecosystem_word="ecosystem",
        tags={"water", "plants", "animals", "ecosystem"},
    ),
    "garden": Place(
        id="garden",
        label="garden",
        scene="a small garden of sleepy soil and bent stems",
        memory_hint="a seed had once fallen there and no one had noticed it",
        ecosystem_word="ecosystem",
        tags={"plants", "soil", "ecosystem"},
    ),
    "grove": Place(
        id="grove",
        label="grove",
        scene="a shady grove with a stream under the roots",
        memory_hint="the birds had once watched from far away",
        ecosystem_word="ecosystem",
        tags={"trees", "water", "animals", "ecosystem"},
    ),
}

TRANSFORMATIONS = {
    "planting": Transformation(
        id="planting",
        label="planting",
        spark="hello",
        result="alive",
        method="planting little reeds and bright flowers",
        tags={"plants", "growth"},
    ),
    "cleaning": Transformation(
        id="cleaning",
        label="cleaning",
        spark="hello",
        result="clear",
        method="clearing the fallen sticks and opening a path for water",
        tags={"water", "care"},
    ),
    "bridging": Transformation(
        id="bridging",
        label="bridging",
        spark="hello",
        result="connected",
        method="laying a narrow bridge of stones across the stream",
        tags={"path", "connection"},
    ),
}

FLASHBACKS = {
    "ducks": Flashback(
        id="ducks",
        label="ducks",
        cue="the ducks had once splashed away without looking back",
        earlier="the pond had felt too quiet for anyone to stay long",
        lesson="Mina remembered that a place can change when someone returns kindly",
        tags={"water", "memory"},
    ),
    "seed": Flashback(
        id="seed",
        label="seed",
        cue="she had tucked one seed into the dirt and promised to come back",
        earlier="the garden had looked empty at first",
        lesson="Mina remembered that small care can turn into a whole garden",
        tags={"plants", "memory"},
    ),
    "bridge": Flashback(
        id="bridge",
        label="bridge",
        cue="they had once crossed the stream by hopping on stones one by one",
        earlier="the grove had felt far away from the other side",
        lesson="Mina remembered that friendship can build a way across water",
        tags={"path", "memory"},
    ),
}

@dataclass
class StoryParams:
    place: str
    transformation: str
    flashback: str
    child_name: str = "Mina"
    child_type: str = "girl"
    friend_name: str = "Kai"
    friend_type: str = "boy"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(place="pond", transformation="planting", flashback="ducks", child_name="Mina", child_type="girl", friend_name="Kai", friend_type="boy"),
    StoryParams(place="garden", transformation="cleaning", flashback="seed", child_name="Lia", child_type="girl", friend_name="Owen", friend_type="boy"),
    StoryParams(place="grove", transformation="bridging", flashback="bridge", child_name="Nora", child_type="girl", friend_name="Tess", friend_type="girl"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, f) for p in PLACES for t in TRANSFORMATIONS for f in FLASHBACKS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    return [
        f'Write an adventure story that includes the words "hello" and "ecosystem".',
        f"Tell a friendship story where {f['child'].label_word} and {f['friend'].label_word} meet in the {place.label} ecosystem, remember something from before, and change the place together.",
        f"Write a gentle adventure with a flashback, a friendship, and a transformation in an ecosystem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend = f["child"], f["friend"]
    place = f["place"]
    flash = f["flashback"]
    trans = f["transformation"]
    eco = f["ecosystem"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label_word} and {friend.label_word}, two children who explore the {place.label} together. Their friendship is what carries the adventure forward.",
        ),
        QAItem(
            question="What did the flashback remind the main child of?",
            answer=f"The flashback reminded {child.label_word} of {flash.earlier}. That memory mattered because it showed why kindness and patience could change the place now.",
        ),
        QAItem(
            question="How did the ecosystem change?",
            answer=f"The ecosystem became more alive after {trans.method}. The world model marks it as changed, and the ending shows new leaves, birds, and moving water.",
        ),
    ]
    if eco.meters["alive"] >= THRESHOLD:
        answers.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the {place.label} feeling alive and shared. {child.label_word} and {friend.label_word} walked home proud because they had helped the ecosystem grow.",
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ecosystem?",
            answer="An ecosystem is a place where living things and the land or water around them all help each other. Plants, animals, water, and soil can belong to the same ecosystem.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier. It helps readers understand a character's memory or why the character feels a certain way now.",
        ),
        QAItem(
            question="Why is friendship important in an adventure?",
            answer="Friendship helps characters trust each other and keep going when the path is hard. A friend can make a scary or lonely place feel brave and hopeful.",
        ),
        QAItem(
            question="What can transformation mean in a story?",
            answer="Transformation means something changes into a new state. In a story, that change can be in a place, an object, or how a character feels.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs a place, a flashback, and a transformation to make the ecosystem change feel real.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("(Unknown place.)")
    if args.transformation and args.transformation not in TRANSFORMATIONS:
        raise StoryError("(Unknown transformation.)")
    if args.flashback and args.flashback not in FLASHBACKS:
        raise StoryError("(Unknown flashback.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.transformation is None or c[1] == args.transformation)
              and (args.flashback is None or c[2] == args.flashback)]
    if not combos:
        raise StoryError(explain_rejection())

    place, transformation, flashback = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        transformation=transformation,
        flashback=flashback,
        child_name=args.child_name or rng.choice(["Mina", "Lia", "Nora", "Ivy", "June"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        friend_name=args.friend_name or rng.choice(["Kai", "Owen", "Tess", "Pip", "Ezra"]),
        friend_type=args.friend_type or rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.transformation not in TRANSFORMATIONS or params.flashback not in FLASHBACKS:
        raise StoryError("(Invalid StoryParams for this world.)")
    world = tell(
        PLACES[params.place],
        TRANSFORMATIONS[params.transformation],
        FLASHBACKS[params.flashback],
        child_name=params.child_name,
        child_type=params.child_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
    )
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


ASP_RULES = r"""
friendship(A,B) :- greeting(A), greeting(B), child(A), child(B), A != B.
transformed(P) :- changed(P).
alive_ecosystem(P) :- transformed(P), ecosystem(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("ecosystem", pid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ERROR: clingo/asp helper unavailable: {exc}")
        return 1

    python_set = set(valid_combos())
    model = asp.one_model(asp_program("#show transformed/1.\n#show alive_ecosystem/1.\n"))
    asp_has = bool(model)
    ok_story = False
    try:
        sample = generate(CURATED[0])
        ok_story = bool(sample.story)
    except Exception as exc:
        print(f"ERROR: smoke test failed: {exc}")
        return 1

    if not ok_story:
        print("ERROR: smoke test produced no story.")
        return 1

    if not python_set:
        print("ERROR: no valid combos.")
        return 1

    print(f"OK: generate() smoke test passed, and {len(python_set)} valid combos exist.")
    print(f"OK: ASP helper returned a model: {asp_has}.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n"))
    return sorted(set(asp.atoms(model, "place")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: hello, ecosystem, friendship, transformation, flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show transformed/1.\n#show alive_ecosystem/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show place/1.\n#show ecosystem/1.\n#show transformation/1.\n#show flashback/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.friend_name}: {p.place}, {p.transformation}, {p.flashback}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
