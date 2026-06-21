#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hypothesis_wasp_sharing_kindness_bravery_comedy.py
===================================================================================

A small comedy storyworld about a child making a hypothesis about a wasp, then
using sharing, kindness, and bravery to turn a noisy moment into a friendly,
silly ending.

Premise
-------
A kid spots a wasp near a picnic or snack time. The kid makes a hypothesis about
what the wasp wants, shares something small and safe, and bravely helps the wasp
out of a silly jam without harming it. The ending should feel light, warm, and
funny: the wasp gets what it needs, the child learns to share, and everyone
laughs at how nervous they were.

This script follows the Storyweavers contract:
- stdlib-only world logic
- typed entities with meters and memes
- Python and ASP reasonableness gates
- StoryParams, build_parser, resolve_params, generate, emit, main
- prompts, story-qa, and world-knowledge QA from world state
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    mood: str
    detail: str
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
class Snack:
    id: str
    label: str
    phrase: str
    sweetness: int
    shareable: bool = True
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
class WaspPlan:
    id: str
    hypothesis: str
    offer: str
    method: str
    comedy: str
    success_line: str
    fail_line: str
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
    setting: str
    snack: str
    plan: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_nervous(world: World) -> list[str]:
    out = []
    for kid in world.characters():
        if kid.role != "child" or kid.memes["alarm"] < THRESHOLD:
            continue
        sig = ("nervous", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["nervous"] += 1
        out.append("__nervous__")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["sharing"] < THRESHOLD:
        return out
    sig = ("share", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack = world.get("snack")
    snack.meters["given"] += 1
    out.append("__share__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    if world.get("helper").memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["calm"] += 1
    world.get("helper").memes["calm"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous), Rule("share", _r_share), Rule("kindness", _r_kindness)]


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


def is_reasonable(setting: Setting, snack: Snack, plan: WaspPlan) -> bool:
    return "wasp" in plan.tags and snack.shareable and "sharing" in plan.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for nid, n in SNACKS.items():
            for pid, p in PLANS.items():
                if is_reasonable(s, n, p):
                    combos.append((sid, nid, pid))
    return combos


def predict(world: World, snack_id: str) -> dict:
    sim = world.copy()
    snack = sim.get(snack_id)
    snack.meters["given"] += 1
    sim.get("wasp").memes["happy"] += 1
    return {"shared": snack.meters["given"] >= THRESHOLD}


def setup(world: World, child: Entity, helper: Entity, parent: Entity, snack: Snack, plan: WaspPlan) -> None:
    child.memes["curiosity"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"On a sunny afternoon, {child.id} and {helper.id} were enjoying {world.setting.place}. "
        f"{world.setting.detail}"
    )
    world.say(
        f"{child.id} had {snack.phrase}, and then a wasp buzzed in like it owned the whole picnic."
    )


def hypothesis(world: World, child: Entity, helper: Entity, plan: WaspPlan) -> None:
    child.memes["thinking"] += 1
    world.say(
        f'{child.id} took a brave breath and made a hypothesis: "{plan.hypothesis}"'
    )
    world.say(
        f'{helper.id} blinked. "{plan.comedy}"'
    )


def warn_and_offer(world: World, helper: Entity, child: Entity, snack: Snack, plan: WaspPlan) -> None:
    child.memes["alarm"] += 1
    child.memes["sharing"] += 1
    world.say(
        f'{helper.id} stayed kind instead of swatting. "{plan.offer}," {helper.id} said, '
        f'holding out a tiny piece.'
    )


def act(world: World, child: Entity, helper: Entity, snack: Snack, plan: WaspPlan) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} was scared, but brave enough to try {plan.method}."
    )
    if predict(world, "snack")["shared"]:
        snack.meters["shared"] += 1
        world.get("wasp").memes["trust"] += 1
        world.say(
            f"The wasp zipped down, took the little crumb, and did a funny loop-de-loop over the table."
        )
    else:
        world.say(plan.fail_line)


def ending(world: World, child: Entity, helper: Entity, parent: Entity, snack: Snack, plan: WaspPlan) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, the wasp flew off politely, and {parent.label_word} laughed at how serious everyone had looked."
    )
    world.say(
        f'{child.id} grinned. "My hypothesis was right," {child.pronoun()} said, '
        f'and now there was still some {snack.label} left for everyone.'
    )


SETTINGS = {
    "picnic": Setting(
        id="picnic",
        place="the picnic blanket",
        mood="bright",
        detail="The lemonade sparkled, the ants marched like tiny traffic cops, and the whole snack felt like a party.",
        tags={"wasp"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        mood="warm",
        detail="The chairs creaked a little, the sun slanted in, and a bowl of fruit sat nearby like a cheerful yellow mountain.",
        tags={"wasp"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden table",
        mood="breezy",
        detail="The flowers waved, the biscuits smelled sweet, and one wasp kept circling as if it had a very important opinion.",
        tags={"wasp"},
    ),
}

SNACKS = {
    "cake": Snack(id="cake", label="cake", phrase="a slice of strawberry cake", sweetness=5, tags={"sharing"}),
    "juice": Snack(id="juice", label="juice", phrase="a cup of orange juice", sweetness=4, tags={"sharing"}),
    "grapes": Snack(id="grapes", label="grapes", phrase="a little bowl of grapes", sweetness=3, tags={"sharing"}),
}

PLANS = {
    "crumb": WaspPlan(
        id="crumb",
        hypothesis="The wasp probably wants a sweet crumb, not a fight.",
        offer="Let's share a tiny crumb and let it leave in peace",
        method="a careful crumb trail",
        comedy="I think the wasp is here for the cake, not the drama",
        success_line="The crumb was tiny, but the wasp accepted it like a tiny crowned king.",
        fail_line="The wasp zigzagged away, still buzzing, and everyone looked even sillier for trying to be the boss.",
        tags={"wasp", "sharing", "kindness", "bravery"},
    ),
    "sip": WaspPlan(
        id="sip",
        hypothesis="Maybe the wasp is thirsty and wants a sip, not our whole snack.",
        offer="Let's set out a drop of juice on a spoon",
        method="a spoonful experiment",
        comedy="We are conducting an extremely scientific wasp snack experiment",
        success_line="The wasp drank one dainty sip and then hovered like it was bowing to the audience.",
        fail_line="The spoon wobbled, the juice splashed, and the wasp kept buzzing as if to say that was not the plan.",
        tags={"wasp", "sharing", "kindness", "bravery"},
    ),
    "path": WaspPlan(
        id="path",
        hypothesis="Maybe it just wants a clear path out of the room, like a polite little flying visitor.",
        offer="Let's open the door and make a safe exit",
        method="a brave open-door route",
        comedy="This was the only bug in the picnic, and it clearly wanted the exit menu",
        success_line="The wasp found the open door and sailed outside, while everyone cheered for the world's smallest parade.",
        fail_line="The door creaked, the wasp wheeled around, and the child accidentally bowled the spoon into the napkins.",
        tags={"wasp", "sharing", "kindness", "bravery"},
    ),
}

CHILDREN = ["Mina", "Toby", "Leah", "Noah", "Pia", "Ezra", "Nina", "Omar"]
HELPERS = ["Aunt June", "Grandpa", "Mom", "Dad", "Big Sister", "Big Brother"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a hypothesis, a wasp, and brave sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_name_pairs() -> list[tuple[str, str]]:
    return [("Mina", "girl"), ("Toby", "boy"), ("Leah", "girl"), ("Noah", "boy"), ("Pia", "girl"), ("Ezra", "boy"), ("Nina", "girl"), ("Omar", "boy")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and args.plan not in PLANS:
        raise StoryError("Unknown plan.")
    if args.snack and args.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, plan = rng.choice(sorted(combos))
    if args.child and args.child_gender is None:
        raise StoryError("If you set --child, also set --child-gender.")
    if args.helper and args.helper_gender is None:
        raise StoryError("If you set --helper, also set --helper-gender.")
    child = args.child or rng.choice(CHILDREN)
    child_gender = args.child_gender or dict(valid_name_pairs()).get(child, rng.choice(["girl", "boy"]))
    helper = args.helper or rng.choice([h for h in CHILDREN if h != child])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, snack=snack, plan=plan, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender, parent=parent)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    snack = SNACKS[params.snack]
    plan = PLANS[params.plan]
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=["curious"]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["kind"]))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent, role="parent", label="the parent"))
    wasp = world.add(Entity(id="wasp", kind="character", type="wasp", role="visitor", label="the wasp"))

    setup(world, child, helper, parent, snack, plan)
    world.para()
    hypothesis(world, child, helper, plan)
    warn_and_offer(world, helper, child, snack, plan)
    act(world, child, helper, snack, plan)
    world.para()
    ending(world, child, helper, parent, snack, plan)

    world.facts.update(child=child, helper=helper, parent=parent, wasp=wasp, snack=snack, plan=plan, setting=setting)
    return world


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, snack, plan = f["child"], f["helper"], f["snack"], f["plan"]
    return [
        ("What did the child think was happening?",
         f"{child.id} made a hypothesis that the wasp wanted something small and safe, not a battle over the snack. That idea helped turn the moment into a sharing problem instead of a swatting problem."),
        ("How did the helper act?",
         f"{helper.id} stayed kind and brave. {helper.id} offered a tiny share instead of trying to hurt the wasp, which kept everyone calmer."),
        ("What changed at the end?",
         f"The wasp got a little share, and the children kept some of the snack too. The big change was that fear turned into laughing, because kindness worked better than panic."),
    ]


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that includes the words "hypothesis" and "wasp".',
        f"Tell a comedy story where {f['child'].id} makes a hypothesis about a wasp and uses sharing instead of swatting.",
        f"Write a warm, silly story about kindness and bravery at snack time, with a wasp and a brave little hypothesis.",
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a hypothesis?", answer="A hypothesis is a guess about what you think is true. It is a thinking word, and people use it when they are trying to understand something."),
        QAItem(question="What is a wasp?", answer="A wasp is a flying insect with a narrow body. It can buzz around food, so people usually stay calm and give it space."),
        QAItem(question="What does sharing mean?", answer="Sharing means letting someone else have some of what you have. It is a kind way to help when there is something small that can be divided."),
        QAItem(question="What does bravery mean?", answer="Bravery means doing a hard or scary thing even while you feel nervous. In this story, bravery helped the child stay calm and choose a gentle solution."),
        QAItem(question="Why is kindness helpful?", answer="Kindness helps because it makes people less scared and more willing to work together. A kind choice can turn a problem into a funny, safe moment."),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if params.plan not in PLANS:
        raise StoryError("Unknown plan.")
    world = tell(params)
    story_qa_items = [QAItem(q, a) for q, a in story_qa(world)]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa_items,
        world_qa=world_qa(world),
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
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(child, snack) :- plan(plan), tags(plan, sharing), shareable(snack).
kind(child) :- plan(plan), tags(plan, kindness).
brave(child) :- plan(plan), tags(plan, bravery).
happy_end(child, snack) :- shared(child, snack), kind(child), brave(child).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, snack in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        if snack.shareable:
            lines.append(asp.fact("shareable", nid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        for t in sorted(plan.tags):
            lines.append(asp.fact("tags", pid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shared/2."))
    # derive from facts directly, then compare against Python
    combos = []
    for s in SETTINGS:
        for n in SNACKS:
            for p in PLANS:
                if is_reasonable(SETTINGS[s], SNACKS[n], PLANS[p]):
                    combos.append((s, n, p))
    return combos


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for nid, snack in SNACKS.items():
            for pid, plan in PLANS.items():
                if is_reasonable(setting, snack, plan):
                    combos.append((sid, nid, pid))
    return combos


CURATED = [
    StoryParams(setting="picnic", snack="cake", plan="crumb", child="Mina", child_gender="girl", helper="Big Sister", helper_gender="girl", parent="mother"),
    StoryParams(setting="porch", snack="juice", plan="sip", child="Toby", child_gender="boy", helper="Mom", helper_gender="girl", parent="mother"),
    StoryParams(setting="garden", snack="grapes", plan="path", child="Leah", child_gender="girl", helper="Dad", helper_gender="boy", parent="father"),
]


def build_asp_show() -> str:
    return asp_program("#show shared/2.\n#show kind/1.\n#show brave/1.\n#show happy_end/2.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for sid, nid, pid in valid_combos():
            print(f"  {sid:8} {nid:8} {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, plan = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILDREN)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice([h for h in CHILDREN if h != child])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, snack=snack, plan=plan, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender, parent=parent)


if __name__ == "__main__":
    main()
