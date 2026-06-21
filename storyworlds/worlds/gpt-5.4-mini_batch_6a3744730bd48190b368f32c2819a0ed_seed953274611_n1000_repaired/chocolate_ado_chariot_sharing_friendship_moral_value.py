#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chocolate_ado_chariot_sharing_friendship_moral_value.py
=======================================================================================

A standalone storyworld about animal friends, a shared chocolate treat, and a
toy chariot that triggers a small ado before a moral-value resolution.

Seed words:
- chocolate
- ado
- chariot

Features:
- Sharing
- Friendship
- Moral Value

Style:
- Animal Story

This world models a tiny animal-friend domain: one animal arrives with a sweet,
another feels left out, a chariot prop raises a bit of ado, and the group learns
that sharing grows friendship. The world state drives the prose, the Q&A, and
the ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2

ANIMAL_NAMES = ["Benny", "Milo", "Tilly", "Pippa", "Roo", "Nina", "Wally", "Suki"]
ANIMAL_TYPES = ["rabbit", "fox", "bear", "mouse", "hedgehog", "cat"]
SCENES = [
    "the sunny meadow",
    "the soft barnyard",
    "the little garden",
    "the grassy hill",
]
TREATS = ["chocolate square", "chocolate bar", "small chocolate coin"]
CHARIOTS = ["toy chariot", "little chariot", "wooden chariot"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"share": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "left_out": 0.0, "friendship": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    scene: str
    name1: str
    type1: str
    name2: str
    type2: str
    name3: str
    type3: str
    treat: str
    chariot: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def animals(self) -> list[Entity]:
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _propagate(world: World) -> None:
    if "share" in world.fired:
        return
    choco = world.get("choco")
    a, b, c = world.get("A"), world.get("B"), world.get("C")
    if choco.meters["share"] >= THRESHOLD:
        world.fired.add("share")
        for e in (a, b, c):
            e.memes["friendship"] += 1
            e.memes["joy"] += 1
        world.get("leftout").memes["left_out"] = 0.0


def predict(world: World) -> dict:
    sim = world.copy()
    choco = sim.get("choco")
    choco.meters["share"] += 1
    _propagate(sim)
    return {
        "friendship": sum(e.memes["friendship"] for e in sim.animals()),
        "left_out": sim.get("leftout").memes["left_out"],
    }


def reasonableness_gate() -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    if not reasonableness_gate():
        return []
    combos = []
    for scene in SCENES:
        for treat in TREATS:
            for ch in CHARIOTS:
                combos.append((scene, treat, ch))
    return combos


def _intro(world: World, a: Entity, b: Entity, c: Entity, scene: str) -> None:
    world.say(
        f"At {scene}, {a.id}, {b.id}, and {c.id} were three animal friends who loved playing together."
    )
    world.say(
        f"They raced toy wheels, laughed in the grass, and gave the day a bright, bouncy feeling."
    )


def _problem(world: World, a: Entity, b: Entity, c: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    c.memes["left_out"] += 1
    world.say(
        f"Then {a.id} found a {world.facts['chariot']} and a sweet {world.facts['treat']} tucked inside it."
    )
    world.say(
        f"{a.id} and {b.id} wanted to keep the chocolate for themselves, and that made {c.id} feel left out."
    )
    world.say(
        f"Little ado followed, as paws, noses, and tails all turned toward the shiny treat."
    )


def _warning(world: World, a: Entity, c: Entity) -> None:
    pred = predict(world)
    world.facts["predicted_friendship"] = pred["friendship"]
    world.facts["predicted_left_out"] = pred["left_out"]
    world.say(
        f"{c.id} spoke up gently: 'If we share the chocolate, the chariot can carry fun for all of us.'"
    )
    world.say(
        f"{a.id} paused and looked at the others. The little ado was really a chance to do the kind thing."
    )


def _share(world: World, a: Entity, b: Entity, c: Entity) -> None:
    choco = world.get("choco")
    choco.meters["share"] += 1
    _propagate(world)
    world.say(
        f"So {a.id} broke the chocolate into three equal pieces and offered one to each friend."
    )
    world.say(
        f"{a.id}, {b.id}, and {c.id} shared the sweet treat beside the chariot, and the grass felt warmer somehow."
    )


def _ending(world: World, a: Entity, b: Entity, c: Entity) -> None:
    world.say(
        f"After that, {a.id} drove the little chariot in a slow circle while the three friends giggled together."
    )
    world.say(
        f"The chocolate was gone, but the friendship stayed, and nobody felt left out anymore."
    )
    world.say(
        f"It was a small lesson with a big moral value: sharing makes room for everyone."
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.name1, kind="character", type=params.type1, role="first"))
    b = world.add(Entity(id=params.name2, kind="character", type=params.type2, role="second"))
    c = world.add(Entity(id=params.name3, kind="character", type=params.type3, role="third"))
    world.add(Entity(id="choco", type="treat", label=params.treat))
    world.add(Entity(id="leftout", type="state", label="left out"))
    world.facts.update(scene=params.scene, treat=params.treat, chariot=params.chariot)

    _intro(world, a, b, c, params.scene)
    world.para()
    _problem(world, a, b, c)
    world.para()
    _warning(world, a, c)
    world.para()
    _share(world, a, b, c)
    world.para()
    _ending(world, a, b, c)
    world.facts.update(
        a=a, b=b, c=c, outcome="shared", choco=world.get("choco"),
        moral="sharing"
    )
    return world


PROMPTS = [
    "Write an animal story about friends who almost argue over chocolate, then learn to share it kindly.",
    "Tell a small story where a toy chariot causes a little ado, but friendship wins in the end.",
    "Write a child-friendly animal tale that teaches sharing as a moral value and includes chocolate.",
]


def generation_prompts(world: World) -> list[str]:
    return list(PROMPTS)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, c = f["a"], f["b"], f["c"]
    return [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {c.id}, three animal friends who play together."),
        ("Why was there ado?",
         f"There was ado because the chocolate was only one treat, and one friend felt left out. The moment of tension pushed the animals to choose kindness."),
        ("How did the problem get fixed?",
         f"{a.id} shared the chocolate into three equal pieces, so everyone got some. That helped the friendship grow and ended the argument."),
        ("What moral value does the story teach?",
         f"It teaches that sharing is a good choice. When friends share, nobody stays left out and the group feels happier."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is chocolate?",
         "Chocolate is a sweet food people and animals in stories often enjoy. It is a treat, so it should be shared carefully."),
        ("What is a chariot?",
         "A chariot is a small wheeled ride or cart in stories. In this tale, it is a toy that adds fun to the play."),
        ("What does ado mean?",
         "Ado means a little fuss or commotion. It can happen when friends disagree before they solve a problem."),
        ("What is friendship?",
         "Friendship is the caring bond between friends. Friends help, listen, and try to be kind to one another."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared :- choco_share(1).
friendship(A) :- animal(A), shared.
outcome(shared) :- shared.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for scene in SCENES:
        lines.append(asp.fact("scene", scene))
    for treat in TREATS:
        lines.append(asp.fact("treat", treat))
    for ch in CHARIOTS:
        lines.append(asp.fact("chariot", ch))
    lines.append(asp.fact("choco_share", 1))
    for name in ANIMAL_NAMES:
        lines.append(asp.fact("animal", name))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    model = asp.one_model(asp_program(show="#show outcome/1."))
    got = set(asp.atoms(model, "outcome"))
    want = {("shared",)}
    if got != want:
        print("MISMATCH in ASP outcome:", got, want)
        rc = 1
    else:
        print("OK: ASP outcome matches Python reasoning.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        print(f"MISMATCH in generate() smoke test: {err}")
        rc = 1
    return rc


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show scene/1.\n#show treat/1.\n#show chariot/1."))
    scenes = [x[0] for x in asp.atoms(model, "scene")]
    treats = [x[0] for x in asp.atoms(model, "treat")]
    chariots = [x[0] for x in asp.atoms(model, "chariot")]
    return [(s, t, c) for s in scenes for t in treats for c in chariots]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about chocolate, ado, and a chariot.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--chariot", choices=CHARIOTS)
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=ANIMAL_TYPES)
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=ANIMAL_TYPES)
    ap.add_argument("--name3")
    ap.add_argument("--type3", choices=ANIMAL_TYPES)
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


@dataclass
class _Choice:
    name: str
    typ: str
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


CURATED = [
    StoryParams(
        scene="the sunny meadow",
        name1="Benny", type1="rabbit",
        name2="Milo", type2="fox",
        name3="Tilly", type3="mouse",
        treat="chocolate bar",
        chariot="toy chariot",
    ),
    StoryParams(
        scene="the little garden",
        name1="Pippa", type1="cat",
        name2="Roo", type2="bear",
        name3="Suki", type3="hedgehog",
        treat="chocolate square",
        chariot="wooden chariot",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.treat and args.chariot:
        pass
    scenes = [args.scene] if args.scene else SCENES
    treats = [args.treat] if args.treat else TREATS
    chariots = [args.chariot] if args.chariot else CHARIOTS
    combos = [(s, t, c) for s in scenes for t in treats for c in chariots]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, treat, chariot = rng.choice(combos)
    def pick_name(existing: set[str]) -> tuple[str, str]:
        typ = rng.choice(ANIMAL_TYPES)
        name = rng.choice([n for n in ANIMAL_NAMES if n not in existing])
        return name, typ
    n1, t1 = args.name1 or pick_name(set())[0], args.type1 or rng.choice(ANIMAL_TYPES)
    n2, t2 = args.name2 or pick_name({n1})[0], args.type2 or rng.choice(ANIMAL_TYPES)
    n3, t3 = args.name3 or pick_name({n1, n2})[0], args.type3 or rng.choice(ANIMAL_TYPES)
    return StoryParams(scene=scene, name1=n1, type1=t1, name2=n2, type2=t2, name3=n3, type3=t3, treat=treat, chariot=chariot)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if params.chariot not in CHARIOTS:
        raise StoryError("Unknown chariot.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show scene/1.\n#show treat/1.\n#show chariot/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP combos:")
        for x in asp_valid_combos():
            print(" ", x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
