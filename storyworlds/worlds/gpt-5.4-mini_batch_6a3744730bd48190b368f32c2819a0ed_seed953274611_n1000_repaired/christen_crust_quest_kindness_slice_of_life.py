#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/christen_crust_quest_kindness_slice_of_life.py
==============================================================================

A small slice-of-life storyworld about a modest neighborhood quest: a child and
a kind helper bake something warm, name it, and bring a crusty treat to someone
who could use a cheerful surprise.

Seed words: christen, crust
Features: Quest, Kindness
Style: Slice of Life
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    quest_verb: str
    quest_goal: str
    cozy_image: str
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


@dataclass
class CrustThing:
    id: str
    label: str
    phrase: str
    has_crust: bool = True
    can_share: bool = True
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
class QuestPlan:
    id: str
    label: str
    errand: str
    finish: str
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
class KindnessMove:
    id: str
    label: str
    method: str
    effect: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bread").meters["warmth"] < THRESHOLD:
        return out
    sig = ("warm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["hope"] += 1
    out.append("The warm bread made the kitchen feel like a good place to start.")
    return out


def _r_kind(world: World) -> list[str]:
    out: list[str] = []
    if world.get("gift").meters["shared"] < THRESHOLD:
        return out
    sig = ("kind",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    neighbor = world.get("neighbor")
    child.memes["joy"] += 1
    neighbor.memes["joy"] += 1
    neighbor.meters["fed"] += 1
    out.append("Kindness filled the room with a softer kind of busy feeling.")
    return out


CAUSAL_RULES = [Rule("warm", "physical", _r_warm), Rule("kind", "social", _r_kind)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_kindness(world: World, plan: QuestPlan, move: KindnessMove) -> dict:
    sim = world.copy()
    sim.get("gift").meters["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get("gift").meters["shared"] >= THRESHOLD,
        "fed": sim.get("neighbor").meters["fed"],
    }


def start(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a slow afternoon, {child.id} and {helper.id} worked in {place.label}. "
        f"Their little quest was to {place.quest_verb} and make the house smell good."
    )
    world.say(
        f"{helper.id} showed {child.id} how to watch the dough, and the two of them "
        f"moved at an easy slice-of-life pace."
    )


def christen_loaf(world: World, child: Entity, loaf: CrustThing, place: Place) -> None:
    child.memes["pride"] += 1
    world.say(
        f'When the loaf came out, {child.id} smiled and said, "Let\'s christen it '
        f"{loaf.label}." The name stuck at once, and the crust looked proudly golden."
    )
    world.say(
        f"The {place.cozy_image} made the little kitchen feel like a tiny world of its own."
    )


def notice_neighbor(world: World, neighbor: Entity, helper: Entity, plan: QuestPlan) -> None:
    neighbor.memes["tired"] += 1
    world.say(
        f"Later, {helper.id} noticed that {neighbor.id} was looking quiet on the porch. "
        f"{neighbor.id} said the day had felt long, and even small chores felt heavy."
    )
    world.say(
        f"{helper.id} thought of a gentle {plan.label}: bring something warm, say hello, and "
        f"make the evening a little brighter."
    )


def gather_gift(world: World, child: Entity, loaf: CrustThing, move: KindnessMove) -> None:
    child.memes["care"] += 1
    world.say(
        f"{child.id} broke off a crust and wrapped it carefully for the walk. "
        f"It was only a small piece, but {move.method} made it feel like a real treasure."
    )


def deliver(world: World, child: Entity, helper: Entity, neighbor: Entity,
            loaf: CrustThing, move: KindnessMove) -> None:
    world.get("gift").meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the door, {child.id} held out the warm crust and {move.method}. "
        f"{neighbor.id} accepted it with a surprised smile, and {move.effect}."
    )
    world.say(
        f"By the time they headed back inside, the whole block felt a little kinder."
    )


def end_image(world: World, child: Entity, helper: Entity, neighbor: Entity, loaf: CrustThing) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    neighbor.memes["joy"] += 1
    world.say(
        f"Back home, {child.id} watched the rest of the {loaf.label} cool by the window. "
        f"The crust stayed crisp, the kitchen stayed warm, and the evening stayed kind."
    )


def tell(place: Place, crust: CrustThing, plan: QuestPlan, move: KindnessMove,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Aunt June", helper_gender: str = "woman",
         neighbor_name: str = "Mr. Bell", neighbor_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    neighbor = world.add(Entity(id=neighbor_name, kind="character", type=neighbor_gender, role="neighbor"))
    bread = world.add(Entity(id="bread", type="thing", label=crust.label))
    gift = world.add(Entity(id="gift", type="thing", label=crust.label))

    world.facts.update(place=place, crust=crust, plan=plan, move=move, child=child, helper=helper, neighbor=neighbor)

    start(world, child, helper, place)
    world.para()
    christen_loaf(world, child, crust, place)
    notice_neighbor(world, neighbor, helper, plan)
    gather_gift(world, child, crust, move)
    world.para()
    deliver(world, child, helper, neighbor, crust, move)
    end_image(world, child, helper, neighbor, crust)

    world.facts.update(
        bread=bread,
        gift=gift,
        shared=gift.meters["shared"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str = "kitchen"
    crust: str = "loaf"
    plan: str = "porch"
    move: str = "wrap"
    child_name: str = "Mina"
    child_gender: str = "girl"
    helper_name: str = "Aunt June"
    helper_gender: str = "woman"
    neighbor_name: str = "Mr. Bell"
    neighbor_gender: str = "man"
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


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        quest_verb="bake bread",
        quest_goal="a loaf with a crust worth sharing",
        cozy_image="sunlight on the counter",
    ),
    "bakery": Place(
        id="bakery",
        label="the little bakery",
        quest_verb="help with bread",
        quest_goal="a tray of warm loaves",
        cozy_image="the smell of flour and butter",
    ),
}

CRUSTS = {
    "loaf": CrustThing(
        id="loaf",
        label="Sun Loaf",
        phrase="a loaf with a crust",
        has_crust=True,
        can_share=True,
        tags={"crust", "christen"},
    ),
    "roll": CrustThing(
        id="roll",
        label="Moon Roll",
        phrase="a roll with a crisp crust",
        has_crust=True,
        can_share=True,
        tags={"crust", "christen"},
    ),
}

PLANS = {
    "porch": QuestPlan(
        id="porch",
        label="porch quest",
        errand="bring warm bread to the porch",
        finish="a friendly wave at the door",
        tags={"quest"},
    ),
    "doorstep": QuestPlan(
        id="doorstep",
        label="doorstep quest",
        errand="carry bread to the next door",
        finish="a thank-you from the neighbor",
        tags={"quest"},
    ),
}

MOVES = {
    "wrap": KindnessMove(
        id="wrap",
        label="wrap it in a napkin",
        method="wrapped the crust in a clean napkin",
        effect="the neighbor laughed and said the bread would be perfect with soup",
        tags={"kindness"},
    ),
    "share": KindnessMove(
        id="share",
        label="share it gently",
        method="shared the crust from a small plate",
        effect="the neighbor looked relieved, as if someone had remembered him at just the right time",
        tags={"kindness"},
    ),
}

CURATED = [
    StoryParams(place="kitchen", crust="loaf", plan="porch", move="wrap"),
    StoryParams(place="bakery", crust="roll", plan="doorstep", move="share", child_name="Leo", child_gender="boy"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, c, q, m) for p in PLACES for c in CRUSTS for q in PLANS for m in MOVES]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen pieces do not make a tidy kindness quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life quest storyworld with kindness and crust.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crust", choices=CRUSTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man", "aunt", "uncle"])
    ap.add_argument("--neighbor-name")
    ap.add_argument("--neighbor-gender", choices=["woman", "man"])
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
    crust = args.crust or rng.choice(list(CRUSTS))
    plan = args.plan or rng.choice(list(PLANS))
    move = args.move or rng.choice(list(MOVES))
    return StoryParams(
        place=place,
        crust=crust,
        plan=plan,
        move=move,
        child_name=args.child_name or rng.choice(["Mina", "Leo", "Ivy", "Noah"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(["Aunt June", "Dad", "Mom"]),
        helper_gender=args.helper_gender or rng.choice(["woman", "man", "aunt", "uncle"]),
        neighbor_name=args.neighbor_name or rng.choice(["Mr. Bell", "Ms. Green", "Mrs. Vale"]),
        neighbor_gender=args.neighbor_gender or rng.choice(["woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "{f["place"].label}" and "crust".',
        f"Tell a gentle quest story where {f['child'].id} and {f['helper'].id} make bread and bring a crusty piece to {f['neighbor'].id}.",
        f'Write a kindness story in which someone says "christen" while sharing warm bread.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, neighbor = f["child"], f["helper"], f["neighbor"]
    place, crust = f["place"], f["crust"]
    return [
        QAItem(question=f"Who is the story about?", answer=f"It is about {child.id}, who is helped by {helper.id} and shares bread with {neighbor.id}."),
        QAItem(question=f"What did {child.id} christen?", answer=f"{child.id} christened the loaf by giving it the name {crust.label}. That made the bread feel special before the kindness quest began."),
        QAItem(question=f"Why did they bring the crust to {neighbor.id}?", answer=f"They wanted to be kind and cheer up {neighbor.id} with something warm from the kitchen. The little quest turned an ordinary afternoon into a thoughtful visit."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is crust on bread?", answer="Crust is the outside part of bread. It can be crisp and golden after baking."),
        QAItem(question="What is a quest?", answer="A quest is a trip or errand with a purpose. In a story, it can be a small mission like bringing something helpful to someone."),
        QAItem(question="What is kindness?", answer="Kindness means being gentle, helpful, and thoughtful toward someone else. Small kind acts can make an ordinary day feel brighter."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions -- answerable from the story text =="]
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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("quest_verb", pid, p.quest_verb))
    for cid, c in CRUSTS.items():
        lines.append(asp.fact("crust", cid))
        if c.has_crust:
            lines.append(asp.fact("has_crust", cid))
    for qid in PLANS:
        lines.append(asp.fact("quest", qid))
    for mid in MOVES:
        lines.append(asp.fact("kindness", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,Q,M) :- place(P), crust(C), quest(Q), kindness(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, crust=None, plan=None, move=None,
            child_name=None, child_gender=None, helper_name=None, helper_gender=None,
            neighbor_name=None, neighbor_gender=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    else:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("place", PLACES), ("crust", CRUSTS), ("plan", PLANS), ("move", MOVES)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    world = tell(
        PLACES[params.place],
        CRUSTS[params.crust],
        PLANS[params.plan],
        MOVES[params.move],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        neighbor_name=params.neighbor_name,
        neighbor_gender=params.neighbor_gender,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
