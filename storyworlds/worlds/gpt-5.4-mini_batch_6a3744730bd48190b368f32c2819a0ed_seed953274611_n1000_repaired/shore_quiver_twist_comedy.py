#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shore_quiver_twist_comedy.py
=============================================================

A standalone story world for a tiny comedic seaside mishap.

Premise
-------
A child brings a quiver full of paper "arrows" to the shore for pretend play.
A gust of wind turns the game into a ridiculous twist: the arrows fly off,
turn into beach chores, and a helpful grown-up suggests a funnier, safer way to
keep playing. The ending proves what changed by showing the same shore scene
now used for a better joke.

Seed words
----------
- shore
- quiver

Style
-----
Comedy, with a twist.

This file follows the shared Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- reasonableness gate
- inline ASP twin
- prompts, story QA, and world QA
- --verify smoke test
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
QUIVER_MIN = 3
WIND_MIN = 2


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    detail: str
    weather: str
    wind: int
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
class ToyPlan:
    id: str
    label: str
    phrase: str
    mischief: str
    result: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class TwistPlan:
    id: str
    reveal: str
    punchline: str
    fix: str
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
class HelperPlan:
    id: str
    label: str
    phrase: str
    fix_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    scene: str
    toy: str
    twist: str
    helper: str
    child_name: str
    child_gender: str
    grownup: str
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_quiver(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    quiver = world.entities.get("quiver")
    if not child or not quiver:
        return out
    if child.memes["embarrassment"] < THRESHOLD and child.meters["scattered"] < THRESHOLD:
        return out
    sig = ("quiver",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quiver.meters["empty"] += 1
    out.append("__quiver__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    grownup = world.entities.get("grownup")
    if not child or not grownup:
        return out
    if child.memes["relief"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    grownup.memes["amusement"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [
    Rule("quiver", "physical", _r_quiver),
    Rule("laugh", "social", _r_laugh),
]


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


def quiver_at_risk(scene: Scene, toy: ToyPlan) -> bool:
    return scene.wind >= WIND_MIN and "shore" in scene.tags and "paper" in toy.tags


def twist_is_funny(twist: TwistPlan, toy: ToyPlan) -> bool:
    return "comedy" in twist.tags and "paper" in toy.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for tid, toy in TOYS.items():
            for xid, twist in TWISTS.items():
                if quiver_at_risk(scene, toy) and twist_is_funny(twist, toy):
                    combos.append((sid, tid, xid))
    return combos


def _quiver_count(child: Entity) -> int:
    return int(child.meters["quiver"])


def predict(world: World, scene: Scene, toy: ToyPlan) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["quiver"] += 1
    child.meters["scattered"] += 1
    child.memes["embarrassment"] += 1
    propagate(sim, narrate=False)
    return {"empty": sim.get("quiver").meters["empty"] >= THRESHOLD}


def play_open(world: World, child: Entity, scene: Scene, toy: ToyPlan) -> None:
    world.say(
        f"At the {scene.place}, {child.id} set up a tiny game beside the shore. "
        f"{scene.detail}"
    )
    world.say(
        f'{child.id} proudly carried {toy.phrase} and announced, '
        f'"Tonight I shall be the most serious hero on the shore!"'
    )


def promise(world: World, child: Entity, toy: ToyPlan) -> None:
    child.memes["pride"] += 1
    world.say(
        f"{child.id} tapped {child.pronoun('possessive')} quiver and grinned. "
        f'The little paper arrows rattled like they were already applauding.'
    )


def warn(world: World, grownup: Entity, child: Entity, scene: Scene, toy: ToyPlan) -> None:
    pred = predict(world, SCENES[scene.id], toy)
    if pred["empty"]:
        world.facts["predicted_empty"] = True
    world.say(
        f'{grownup.id} squinted at the wind. "{child.id}, that quiver is a '
        f"trouble bucket on a day like this. One sneeze from the breeze and "
        f"your arrows will do cartwheels."'
    )


def toss(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    child.meters["quiver"] += 1
    child.meters["scattered"] += 1
    world.say(
        f'{child.id} tried anyway, because every comedy needs a confident mistake.'
    )


def twist_event(world: World, child: Entity, toy: ToyPlan, twist: TwistPlan) -> None:
    child.memes["embarrassment"] += 1
    world.say(
        f"Then the twist arrived: {twist.reveal} {twist.punchline}. "
        f"{toy.result}."
    )
    propagate(world, narrate=False)
    quiver = world.get("quiver")
    quiver.meters["full_of_news"] += 1


def help_arrives(world: World, grownup: Entity, helper: HelperPlan) -> None:
    grownup.memes["amusement"] += 1
    world.say(
        f"{grownup.id} laughed so hard {grownup.pronoun()} had to hold {grownup.pronoun('possessive')} sides. "
        f'Then {grownup.pronoun()} said, "{helper.fix_text}"'
    )


def recover(world: World, child: Entity, toy: ToyPlan, helper: HelperPlan) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.meters["quiver"] = 0
    world.say(
        f"{child.id} collected the last paper arrow, tucked it back into the quiver, "
        f"and nodded. The quiver had stopped being mighty and started being silly."
    )
    world.say(
        f"After that, {child.id} used {helper.phrase} instead, and the shore game became "
        f"a race to make the funniest splash-free hero pose."
    )


def tell(scene: Scene, toy: ToyPlan, twist: TwistPlan, helper: HelperPlan,
         child_name: str = "Milo", child_gender: str = "boy",
         grownup: str = "Aunt June") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    adult = world.add(Entity(id="grownup", kind="character", type="adult", label=grownup))
    quiver = world.add(Entity(id="quiver", type="thing", label="quiver", tags={"quiver"}))

    child.id = child_name
    adult.id = grownup

    play_open(world, child, scene, toy)
    promise(world, child, toy)
    world.para()
    warn(world, adult, child, scene, toy)
    toss(world, child)
    world.para()
    twist_event(world, child, toy, twist)
    help_arrives(world, adult, helper)
    recover(world, child, toy, helper)

    world.facts.update(
        child=child,
        grownup=adult,
        quiver=quiver,
        scene=scene,
        toy=toy,
        twist=twist,
        helper=helper,
        outcome="funny",
    )
    return world


SCENES = {
    "shore_evening": Scene(
        id="shore_evening",
        place="shore",
        detail="The gulls bobbed like little judges, and the waves kept making comic applause.",
        weather="windy",
        wind=3,
        tags={"shore", "wind"},
    ),
    "shore_morning": Scene(
        id="shore_morning",
        place="shore",
        detail="A bright shell line glittered on the sand, and the tide kept sneaking closer to listen.",
        weather="windy",
        wind=2,
        tags={"shore", "wind"},
    ),
}

TOYS = {
    "paper_arrows": ToyPlan(
        id="paper_arrows",
        label="paper arrows",
        phrase="a quiver full of paper arrows",
        mischief="the arrows lifted like tiny kites",
        result="The whole quiver was suddenly a bird feeder for the wind",
        tags={"paper", "quiver", "comedy"},
    ),
    "spoons": ToyPlan(
        id="spoons",
        label="spoons",
        phrase="a quiver full of wooden spoons",
        mischief="the spoons clattered like tiny drums",
        result="The whole quiver sounded like a marching band with one tooth missing",
        tags={"paper", "quiver", "comedy"},
    ),
}

TWISTS = {
    "seagull_swap": TwistPlan(
        id="seagull_swap",
        reveal="A seagull landed, sneezed, and swapped the arrows for fish crackers.",
        punchline="Now the most heroic thing in the quiver was lunch",
        fix="keep the crackers and call it a picnic",
        tags={"comedy", "twist"},
    ),
    "sandcastle_target": TwistPlan(
        id="sandcastle_target",
        reveal="The arrows all pointed at a sandcastle, which turned out to be a crab's fancy apartment.",
        punchline="The crab waved a claw like a tiny landlord asking for quiet",
        fix="aim the game at paper cups instead",
        tags={"comedy", "twist"},
    ),
}

HELPERS = {
    "kite_string": HelperPlan(
        id="kite_string",
        label="kite string",
        phrase="kite string",
        fix_text="Let's tie the paper arrows to kite string and make a wind-race instead.",
        tags={"shore", "twist", "comedy"},
    ),
    "bucket_drums": HelperPlan(
        id="bucket_drums",
        label="bucket drums",
        phrase="two little buckets",
        fix_text="Let's leave the arrows in the quiver and make bucket drums for the seagulls.",
        tags={"shore", "twist", "comedy"},
    ),
}


CURATED = [
    StoryParams(scene="shore_evening", toy="paper_arrows", twist="seagull_swap", helper="kite_string",
                child_name="Milo", child_gender="boy", grownup="Aunt June"),
    StoryParams(scene="shore_morning", toy="paper_arrows", twist="sandcastle_target", helper="bucket_drums",
                child_name="Nia", child_gender="girl", grownup="Uncle Pat"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about a shore, a quiver, and a twist.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--grownup")
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
    if args.scene and args.scene not in SCENES:
        raise StoryError("Unknown scene.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.toy is None or c[1] == args.toy)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, toy, twist = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    child_gender = args.gender or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(["Milo", "Nia", "Bea", "Owen", "Pip", "Luna"])
    grownup = args.grownup or rng.choice(["Aunt June", "Uncle Pat", "Grandma Sol"])
    return StoryParams(scene=scene, toy=toy, twist=twist, helper=helper,
                       child_name=child_name, child_gender=child_gender, grownup=grownup)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny seaside story that includes the words "{f["scene"].place}" and "quiver".',
        f"Tell a comedy story where {f['child'].id} brings a quiver to the shore, and the wind causes a silly twist.",
        "Write a child-friendly joke story about a beach game that turns into a helpful new plan.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    toy = f["toy"]
    twist = f["twist"]
    helper = f["helper"]
    scene = f["scene"]
    qa = [
        ("Where did the story happen?",
         f"It happened at the shore, where the wind kept teasing the game. The beach setting matters because it helps the twist feel playful instead of serious."),
        ("What did {0} bring?".format(child.id),
         f"{child.id} brought {toy.phrase}. The quiver made the game feel important until the wind made it ridiculous."),
        ("What was the twist?",
         f"{twist.reveal} {twist.punchline}. That surprise changed the game from heroic to silly."),
        ("How did the grown-up help?",
         f"{grownup.id} suggested, '{helper.fix_text}' The new idea kept the fun going and turned the mistake into a laugh."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a shore?",
         "A shore is the land right next to the sea or lake. It is a place where waves or water meet the sand or rocks."),
        ("What is a quiver?",
         "A quiver is a holder for arrows. In stories, it can be real or pretend, and it often hangs from the back or shoulder."),
        ("What is a twist in a story?",
         "A twist is a surprise that changes what you expected. It can make a story funny by turning the plan upside down."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.toy not in TOYS or params.twist not in TWISTS or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    world = tell(SCENES[params.scene], TOYS[params.toy], TWISTS[params.twist], HELPERS[params.helper],
                 child_name=params.child_name, child_gender=params.child_gender, grownup=params.grownup)
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


ASP_RULES = r"""
scene_ok(S) :- scene(S).
toy_ok(T) :- toy(T).
twist_ok(X) :- twist(X).
valid(S,T,X) :- scene_ok(S), toy_ok(T), twist_ok(X), shore(S), windy(S), paper(T), comedy_twist(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        if "shore" in s.tags:
            lines.append(asp.fact("shore", sid))
        if s.wind >= WIND_MIN:
            lines.append(asp.fact("windy", sid))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if "paper" in t.tags:
            lines.append(asp.fact("paper", tid))
    for xid, x in TWISTS.items():
        lines.append(asp.fact("twist", xid))
        if "comedy" in x.tags:
            lines.append(asp.fact("comedy_twist", xid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: clingo gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
        print("OK: generate()/serialization smoke test passed.")
    except Exception as err:
        rc = 1
        print("SMOKE TEST FAILED:", err)
        traceback.print_exc()
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return valid_combos_impl()


def valid_combos_impl() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for tid, toy in TOYS.items():
            for xid, twist in TWISTS.items():
                if quiver_at_risk(scene, toy) and twist_is_funny(twist, toy):
                    combos.append((sid, tid, xid))
    return combos


def build_parser_and_main() -> None:
    pass


def resolve_params_wrapper(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def build_parser2() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
