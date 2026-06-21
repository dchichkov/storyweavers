#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hollyhock_divert_sharing_rhyming_story.py
=========================================================================

A tiny storyworld for a rhyming sharing tale in a garden.

Premise
-------
Two children want the same little basket of seeds for a hollyhock patch.
One child feels possessive; the other suggests sharing and helps divert
attention to a second task so they can take turns, divide the work, and end
with a brighter garden.

This world keeps the model small and state-driven:
- physical meters: petals, seeds, water, bloom, tidiness
- emotional memes: want, worry, kindness, pride, calm, joy
- a simple causal engine that advances the simulated garden toward a turn
- an ASP twin that mirrors the reasonableness gate and outcome choice

The story is built to read like a gentle rhyming story, with child-facing
prose that includes the seed words hollyhock and divert naturally.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_divert_sharing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_divert_sharing_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_divert_sharing_rhyming_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_divert_sharing_rhyming_story.py --show-asp
"""

from __future__ import annotations

import argparse
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
    attrs: dict = field(default_factory=dict)
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
        return self.label or self.id
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
class GardenThing:
    id: str
    label: str
    kind: str
    petals: int
    shares_well: bool = False
    can_divert: bool = False
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
class StoryParams:
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
    flower: str
    object: str
    action: str
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


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    if world.get("basket").meters["shared"] >= THRESHOLD and ("shared",) not in world.fired:
        world.fired.add(("shared",))
        world.get("basket").meters["open"] = 1
        world.get("garden").memes["calm"] += 1
        out.append("__shared__")
    return out


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    if world.get("basket").meters["shared"] >= THRESHOLD and world.get("hollyhock").meters["water"] >= THRESHOLD:
        if ("bloom",) not in world.fired:
            world.fired.add(("bloom",))
            world.get("hollyhock").meters["bloom"] += 1
            out.append("__bloom__")
    return out


CAUSAL_RULES = [Rule("shared", _r_shared), Rule("bloom", _r_bloom)]


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


def make_reasonable(flower: GardenThing, obj: GardenThing, action: str) -> bool:
    return flower.shares_well and obj.can_divert and action in {"share", "divide"}


def outcome_of(params: StoryParams) -> str:
    flower = FLOWERS[params.flower]
    obj = OBJECTS[params.object]
    if not make_reasonable(flower, obj, params.action):
        return "invalid"
    return "shared"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for flower in FLOWERS:
        for obj in OBJECTS:
            for action in ACTIONS:
                if make_reasonable(FLOWERS[flower], OBJECTS[obj], action):
                    out.append((flower, obj, action))
    return out


def _setup(world: World, a: Entity, b: Entity, parent: Entity, flower: GardenThing, obj: GardenThing) -> None:
    garden = world.add(Entity(id="garden", kind="place", type="room", label="the garden"))
    basket = world.add(Entity(id="basket", kind="thing", type="thing", label="a little basket"))
    hollyhock = world.add(Entity(id="hollyhock", kind="thing", type="flower", label=flower.label))
    basket.meters["wanted"] += 1
    hollyhock.meters["seed"] += 1
    a.memes["want"] += 1
    b.memes["want"] += 1
    world.say(
        f"In the bright garden lane, {a.id} and {b.id} came out to play. "
        f"They found a {flower.label} patch that swayed and glowed, a pretty pink parade."
    )
    world.say(
        f"On the bench sat {obj.label}, neat and small, and both children wanted it all."
    )
    world.facts.update(garden=garden, basket=basket, hollyhock=hollyhock, obj=obj)


def _want(world: World, a: Entity, b: Entity, flower: GardenThing, obj: GardenThing) -> None:
    world.say(
        f'"Let me have it," {a.id} said with a sigh, "I want to work and never say bye."'
    )
    world.say(
        f'"Let us share," {b.id} replied, "so each can help and side by side."'
    )
    a.memes["worry"] += 1
    b.memes["kindness"] += 1


def _divert(world: World, a: Entity, b: Entity, obj: GardenThing) -> None:
    a.memes["calm"] += 1
    b.memes["calm"] += 1
    world.say(
        f"Then {b.id} helped divert the rush: they sorted pebbles, slow and hush."
    )
    world.say(
        f"While one child held the basket near, the other fetched a tin of clear water from nearby."
    )
    world.get("basket").meters["shared"] += 1
    world.get("hollyhock").meters["water"] += 1
    propagate(world, narrate=False)


def _share_finish(world: World, a: Entity, b: Entity, parent: Entity, flower: GardenThing, obj: GardenThing) -> None:
    world.say(
        f"{parent.id} smiled and clapped in time. " 
        f'"Good sharing makes a garden shine."'
    )
    world.say(
        f"{a.id} spread the seeds with care, and {b.id} watered the hollyhock there."
    )
    world.say(
        f"The petals rose like ribbons bright, and both children grinned in the light."
    )
    world.say(
        f"They shared the joy, they shared the day, and the little basket went right away."
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.child_a, kind="character", type=params.child_a_gender, role="child"))
    b = world.add(Entity(id=params.child_b, kind="character", type=params.child_b_gender, role="child"))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent", label="the parent"))
    flower = FLOWERS[params.flower]
    obj = OBJECTS[params.object]

    _setup(world, a, b, parent, flower, obj)
    world.para()
    _want(world, a, b, flower, obj)
    _divert(world, a, b, obj)
    world.para()
    _share_finish(world, a, b, parent, flower, obj)

    world.facts.update(a=a, b=b, parent=parent, flower=flower, action=params.action, outcome="shared")
    return world


FLOWERS = {
    "hollyhock": GardenThing(
        id="hollyhock",
        label="hollyhock",
        kind="flower",
        petals=5,
        shares_well=True,
        tags={"flower", "garden", "share"},
    ),
    "marigold": GardenThing(
        id="marigold",
        label="marigold",
        kind="flower",
        petals=6,
        shares_well=True,
        tags={"flower", "garden", "share"},
    ),
}

OBJECTS = {
    "basket": GardenThing(
        id="basket",
        label="little basket of seeds",
        kind="thing",
        petals=0,
        can_divert=True,
        tags={"basket", "share"},
    ),
    "watering_can": GardenThing(
        id="watering_can",
        label="small watering can",
        kind="thing",
        petals=0,
        can_divert=True,
        tags={"water", "share"},
    ),
}

ACTIONS = ["share", "divide"]


GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Noah", "Eli", "Ben"]
PARENT_NAMES = ["Mom", "Dad"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming sharing story for a young child that includes the word "{f["flower"].label}" and the word "divert".',
        f"Tell a gentle garden story where {f['a'].id} and {f['b'].id} learn to share a basket and divert their fuss into kind work.",
        f"Write a bright rhyming story about sharing in a garden with {f['flower'].label}, a basket, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, flower, obj = f["a"], f["b"], f["parent"], f["flower"], f["obj"]
    return [
        QAItem(
            question="What did the children learn to do?",
            answer=f"They learned to share. Instead of fighting over {obj.label}, they took turns and worked together in the garden.",
        ),
        QAItem(
            question=f"Why did {b.id} divert the fuss?",
            answer=f"{b.id} wanted to calm things down and keep the play kind. Diverting the fuss helped both children focus on the garden job instead of the argument.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the {flower.label} patch watered and smiling, and the children happy because they shared the basket and stayed kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hollyhock?",
            answer="A hollyhock is a tall garden flower with soft, pretty blossoms. It grows up happily when it gets water and care.",
        ),
        QAItem(
            question="What does divert mean?",
            answer="To divert means to turn something away or guide attention in a different direction. A person can divert a fuss into calmer, kinder work.",
        ),
        QAItem(
            question="Why is sharing good?",
            answer="Sharing helps people take turns and feel fair. It can turn a grumpy moment into a happier one for everyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(F,O,A) :- flower(F), object(O), action(A), shares_well(F), divertable(O), share_action(A).
outcome(shared) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for fid, f in FLOWERS.items():
        lines.append(asp.fact("flower", fid))
        if f.shares_well:
            lines.append(asp.fact("shares_well", fid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_divert:
            lines.append(asp.fact("divertable", oid))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
        if a == "share":
            lines.append(asp.fact("share_action", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            child_a=None, child_a_gender=None, child_b=None, child_b_gender=None,
            parent=None, flower=None, object=None, action=None
        ), random.Random(1)))
        _ = sample.story
    except Exception as e:
        print(f"smoke test failed: {e}")
        rc = 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as e:
        print(f"emit smoke test failed: {e}")
        rc = 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming sharing garden storyworld.")
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child-a")
    ap.add_argument("--child-a-gender", choices=["girl", "boy"])
    ap.add_argument("--child-b")
    ap.add_argument("--child-b-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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
    flower = args.flower or rng.choice(list(FLOWERS))
    obj = args.object or rng.choice(list(OBJECTS))
    action = args.action or rng.choice(ACTIONS)
    if not make_reasonable(FLOWERS[flower], OBJECTS[obj], action):
        raise StoryError("No valid sharing/divert combination matches the given options.")
    child_a_gender = args.child_a_gender or rng.choice(["girl", "boy"])
    child_b_gender = args.child_b_gender or ("boy" if child_a_gender == "girl" else "girl")
    child_a = args.child_a or rng.choice(GIRL_NAMES if child_a_gender == "girl" else BOY_NAMES)
    child_b = args.child_b or rng.choice([n for n in (GIRL_NAMES if child_b_gender == "girl" else BOY_NAMES) if n != child_a])
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(
        child_a=child_a,
        child_a_gender=child_a_gender,
        child_b=child_b,
        child_b_gender=child_b_gender,
        parent=parent,
        flower=flower,
        object=obj,
        action=action,
    )


def generate(params: StoryParams) -> StorySample:
    if params.flower not in FLOWERS or params.object not in OBJECTS or params.action not in ACTIONS:
        raise StoryError("Invalid parameters for this storyworld.")
    if not make_reasonable(FLOWERS[params.flower], OBJECTS[params.object], params.action):
        raise StoryError("That combination cannot make a sensible sharing story.")
    world = tell(params)
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
        print(asp_program("#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(child_a="Lily", child_a_gender="girl", child_b="Noah", child_b_gender="boy", parent="Mom", flower="hollyhock", object="basket", action="share")),
            generate(StoryParams(child_a="Mia", child_a_gender="girl", child_b="Eli", child_b_gender="boy", parent="Dad", flower="marigold", object="watering_can", action="divide")),
        ]
    else:
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
