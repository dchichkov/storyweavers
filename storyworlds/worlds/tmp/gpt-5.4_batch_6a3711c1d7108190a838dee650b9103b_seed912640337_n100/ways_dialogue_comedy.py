#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py
==================================================

A tiny storyworld about a child trying to reach a snack on a shelf by thinking
of many funny ways. The world prefers sensible reaching methods and refuses
circus-level nonsense. Dialogue carries the comedy, but simulated state drives
the warning, the turn, and the ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py
    python storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py --shelf high --container jar
    python storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py --method books
    python storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py --all
    python storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ways_dialogue_comedy.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Shelf:
    id: str
    phrase: str
    height: int
    room: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    snack: str
    fragile: bool
    weight: int
    sound: str
    open_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    reach: int
    stability: int
    sense: int
    adult_help: bool
    text: str
    success: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def stability_need(container: Container) -> int:
    return 3 if container.fragile or container.weight >= 2 else 2


def method_can_reach(method: Method, shelf: Shelf) -> bool:
    return method.adult_help or method.reach >= shelf.height


def method_is_reasonable(method: Method, shelf: Shelf, container: Container) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if not method_can_reach(method, shelf):
        return False
    if method.stability < stability_need(container):
        return False
    if method.id == "grabber" and container.weight >= 3:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, shelf in SHELVES.items():
        for cid, container in CONTAINERS.items():
            for mid, method in METHODS.items():
                if method_is_reasonable(method, shelf, container):
                    combos.append((sid, cid, mid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    shelf = SHELVES[params.shelf]
    container = CONTAINERS[params.container]
    if method.id == "ask_parent":
        return "helped"
    margin = method.stability - stability_need(container)
    reach_margin = 99 if method.adult_help else method.reach - shelf.height
    if margin == 0 or reach_margin == 0:
        return "wobble"
    return "easy"


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    container = world.get("container")
    if child.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["alarm"] += 1
    world.get("helper").memes["alarm"] += 1
    if container.attrs.get("fragile"):
        container.meters["clink"] += 1
        out.append("__clink__")
    return out


CAUSAL_RULES = [
    Rule("wobble", "physical", _r_wobble),
]


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


def predict_attempt(world: World, shelf: Shelf, container: Container, method: Method) -> dict:
    sim = world.copy()
    child = sim.get("child")
    cont = sim.get("container")
    if method.id != "ask_parent":
        if method.stability == stability_need(container) or (
            not method.adult_help and method.reach == shelf.height
        ):
            child.meters["wobble"] += 1
            propagate(sim, narrate=False)
    success = method_is_reasonable(method, shelf, container)
    return {
        "success": success,
        "wobble": child.meters["wobble"],
        "clink": cont.meters["clink"],
    }


def introduce(world: World, child: Entity, helper: Entity, shelf: Shelf, container: Container) -> None:
    child.memes["hunger"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"After school, {child.id} padded into the {shelf.room} and stopped under {shelf.phrase}."
    )
    world.say(
        f"Up there sat {container.phrase}, full of {container.snack}. When the jar gave {container.sound}, "
        f"{child.id}'s eyes grew round."
    )
    world.say(
        f'"There are at least nine ways to get that down," {child.id} whispered. '
        f'"Maybe ten if one of the ways is growing taller."'
    )
    world.say(
        f'"If growing taller is your plan," said {helper.id}, "it is taking too long."'
    )


def brainstorm(world: World, child: Entity, helper: Entity, shelf: Shelf, container: Container) -> None:
    child.memes["impatience"] += 1
    world.say(
        f'{child.id} looked from the floor to {shelf.phrase} and back again. '
        f'"I could jump," {child.pronoun()} said.'
    )
    world.say(
        f'"You jump like a very hopeful potato," said {helper.id}.'
    )
    world.say(
        f'"Fine," said {child.id}. "Then I need more ways."'
    )
    world.say(
        f'{helper.id} put both hands on {helper.pronoun("possessive")} hips. '
        f'"Ways are easy. Good ways are the tricky part."'
    )


def warn(world: World, child: Entity, helper: Entity, shelf: Shelf, container: Container, method: Method) -> None:
    pred = predict_attempt(world, shelf, container, method)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_clink"] = pred["clink"]
    if method.id == "ask_parent":
        world.say(
            f'"One very good way," said {helper.id}, "is to use your voice and call a grown-up with longer arms."'
        )
        return
    if pred["wobble"] >= THRESHOLD:
        world.say(
            f'"That way would make you wobble," said {helper.id}. '
            f'"And {container.label} sounds like it wants to stay in one piece."'
        )
    else:
        world.say(
            f'{helper.id} squinted up at {shelf.phrase}. '
            f'"That might work," {helper.pronoun()} said, "if nobody turns this into a circus."'
        )


def do_method(world: World, child: Entity, helper: Entity, parent: Entity,
              shelf: Shelf, container: Container, method: Method) -> None:
    child.memes["resolve"] += 1
    cont = world.get("container")
    if method.id == "ask_parent":
        parent.memes["helpfulness"] += 1
        world.say(
            f'{child.id} took a deep breath and called, "{parent.label_word.capitalize()}, can you help us reach the {container.label}?"'
        )
        world.say(
            f'{parent.label_word.capitalize()} came in smiling. "That is my favorite kind of emergency," {parent.pronoun()} said. '
            f'"It is quiet, and nobody is standing on anything wiggly."'
        )
        cont.meters["lowered"] += 1
        return

    world.say(method.text.format(child=child.id, helper=helper.id, parent=parent.label_word, container=container.label))
    wobble = outcome_of(world.facts["params"]) == "wobble"
    if wobble:
        world.get("child").meters["wobble"] += 1
        propagate(world, narrate=False)
        world.say(
            f'The whole business gave one tiny wobble. "{container.label.capitalize()} first, knees second," yelped {helper.id}.'
        )
        child.memes["embarrassment"] += 1
    cont.meters["lowered"] += 1
    world.say(method.success.format(child=child.id, container=container.label))


def share(world: World, child: Entity, helper: Entity, parent: Entity, container: Container, method: Method) -> None:
    cont = world.get("container")
    cont.meters["open"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'Soon {container.open_phrase}. "{container.snack.capitalize()} for the thinkers," said {parent.label_word}, passing some around.'
    )
    if method.id == "ask_parent":
        world.say(
            f'"So the best way was asking?" said {child.id}.'
        )
        world.say(
            f'"One of the best ways," said {helper.id}. "Also the least likely to end with your feet in the air."'
        )
    elif outcome_of(world.facts["params"]) == "wobble":
        world.say(
            f'"We did it," said {child.id}.'
        )
        world.say(
            f'"Yes," said {helper.id}, "but next time let us use a way with fewer dramatic eyebrows."'
        )
    else:
        world.say(
            f'"That was almost too easy," said {child.id}.'
        )
        world.say(
            f'"Good," said {helper.id}. "Snacks should be crunchy, not the plan."'
        )


def closing_image(world: World, child: Entity, helper: Entity, shelf: Shelf) -> None:
    world.say(
        f"After that, the two of them sat under {shelf.phrase}, munching and laughing, while the empty air above their heads looked much less bossy."
    )


def tell(shelf: Shelf, container: Container, method: Method,
         child_name: str = "Nora", child_type: str = "girl",
         helper_name: str = "Max", helper_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="shelf", type="shelf", label=shelf.phrase, attrs={"height": shelf.height}))
    world.add(Entity(
        id="container", type="container", label=container.label,
        attrs={"fragile": container.fragile, "weight": container.weight, "snack": container.snack}
    ))

    introduce(world, child, helper, shelf, container)
    world.para()
    brainstorm(world, child, helper, shelf, container)
    warn(world, child, helper, shelf, container, method)
    world.para()
    do_method(world, child, helper, parent, shelf, container, method)
    share(world, child, helper, parent, container, method)
    closing_image(world, child, helper, shelf)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        shelf=shelf,
        container_cfg=container,
        method=method,
        reached=world.get("container").meters["lowered"] >= THRESHOLD,
        opened=world.get("container").meters["open"] >= THRESHOLD,
        outcome=outcome_of(world.facts["params"]),
    )
    return world


SHELVES = {
    "low": Shelf("low", "the lowest pantry shelf", 1, "kitchen", tags={"shelf"}),
    "middle": Shelf("middle", "the middle pantry shelf", 2, "kitchen", tags={"shelf"}),
    "high": Shelf("high", "the top pantry shelf", 3, "kitchen", tags={"shelf"}),
}

CONTAINERS = {
    "jar": Container(
        "jar", "cookie jar", "a round cookie jar with blue dots", "butter cookies",
        fragile=True, weight=2, sound="a hopeful clink", open_phrase="the lid came off with a cheerful pop",
        tags={"jar", "cookies", "fragile"},
    ),
    "tin": Container(
        "tin", "cracker tin", "a bright cracker tin with a red lid", "cheese crackers",
        fragile=False, weight=1, sound="a papery rattle", open_phrase="the lid flipped up with a click",
        tags={"tin", "crackers"},
    ),
    "bowl": Container(
        "bowl", "popcorn bowl", "a wide popcorn bowl covered with a towel", "sweet popcorn",
        fragile=False, weight=1, sound="a soft rustle", open_phrase="the towel was lifted, and the popcorn smell rushed out",
        tags={"bowl", "popcorn"},
    ),
}

METHODS = {
    "ask_parent": Method(
        "ask_parent", "ask a grown-up", "ask a grown-up", 4, 4, 4, True,
        adult_help=True,
        text="",
        success='In one smooth move, the {container} was safely on the counter.',
        tags={"ask_adult"},
    ),
    "stool": Method(
        "stool", "step stool", "a step stool", 2, 3, 4, False,
        text='"Bring the step stool," said {helper}. "{container.capitalize()} is not worth acrobatics." {child} climbed up carefully and reached with both hands.',
        success='A second later, {child} had the {container} tucked safely against {child}\'s chest.',
        tags={"stool"},
    ),
    "chair": Method(
        "chair", "kitchen chair", "a kitchen chair", 3, 3, 3, False,
        text='They dragged over the kitchen chair. "This is the respectable kind of climbing," said {child}, trying to sound grand.',
        success='Stretching as tall as possible, {child} got hold of the {container} and brought it down.',
        tags={"chair"},
    ),
    "grabber": Method(
        "grabber", "grabber claw", "a grabber claw", 4, 3, 3, False,
        text='From beside the broom closet, {helper} fetched the grabber claw. "Behold," {helper} said, "the metal pinchy bird."',
        success='After one careful pinch and one tiny shuffle, the {container} slid close enough for {child} to take it.',
        tags={"grabber"},
    ),
    "books": Method(
        "books", "stack of books", "a stack of books", 3, 1, 1, False,
        text='They stacked books into a wobbly tower that looked like a bad idea wearing hard covers.',
        success='Somehow the {container} came down.',
        tags={"books"},
    ),
    "skateboard": Method(
        "skateboard", "skateboard", "a skateboard", 3, 0, 0, False,
        text='"What if I roll and reach at the same time?" asked {child}.',
        success='The {container} came down in a blur.',
        tags={"skateboard"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Max", "Leo", "Ben", "Sam", "Finn", "Theo", "Jack", "Eli"]


@dataclass
class StoryParams:
    shelf: str
    container: str
    method: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ask_adult": [(
        "Why is asking a grown-up a good way to reach something high?",
        "A grown-up may be taller or stronger and can help without wobbling on unsafe things. Asking for help can be the smartest way, not the baby way."
    )],
    "stool": [(
        "What is a step stool for?",
        "A step stool is a short, steady step that helps you reach something a little higher. It is made to stand on much better than a pile of books."
    )],
    "chair": [(
        "Why should you be careful on a chair?",
        "A chair can tip or slide if you climb on it the wrong way. That is why children should use it only with care and grown-up judgment."
    )],
    "grabber": [(
        "What is a grabber claw?",
        "A grabber claw is a long tool that helps you pinch and pull something closer. It is useful for light things that are a bit out of reach."
    )],
    "fragile": [(
        "What does fragile mean?",
        "Fragile means something can break easily if it is dropped or bumped. Glass jars are often fragile."
    )],
    "cookies": [(
        "What is a cookie jar?",
        "A cookie jar is a container that holds cookies and keeps them together in one place. Some jars are heavy or made of breakable glass."
    )],
    "crackers": [(
        "What is a cracker tin?",
        "A cracker tin is a metal container with a lid for crackers. A tin is often lighter and less breakable than a glass jar."
    )],
    "popcorn": [(
        "Why does popcorn smell strong?",
        "Popcorn has a warm, toasty smell that spreads through the air quickly. That is why people can notice it from across a room."
    )],
}
KNOWLEDGE_ORDER = ["ask_adult", "stool", "chair", "grabber", "fragile", "cookies", "crackers", "popcorn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    container = f["container_cfg"]
    shelf = f["shelf"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "ways" and lots of dialogue. A child wants {container.snack} from {container.phrase} on {shelf.phrase}.',
        f"Tell a comedy where {child.id} and {helper.id} think of many ways to reach a snack, but only one way is sensible enough to use.",
        f'Write a light family story with back-and-forth dialogue, a high snack, a safer plan, and an ending where everyone laughs in the kitchen.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    shelf = f["shelf"]
    container = f["container_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id}, who were trying to reach {container.phrase} in the kitchen. {parent.label_word.capitalize()} also helped at the end."
        ),
        (
            f"Why did {child.id} keep looking up at the shelf?",
            f"{child.id} wanted the {container.snack} inside {container.label}. The snack was sitting on {shelf.phrase}, so reaching it became the whole problem."
        ),
        (
            "Why did they talk about so many ways?",
            f"They were trying to solve the same problem in different ways and make each other laugh while they thought. The dialogue turns the reaching problem into a funny little debate."
        ),
    ]
    if method.id == "ask_parent":
        qa.append((
            f"What was the best way in this story?",
            f"The best way was asking {parent.label_word} for help. That worked because a grown-up could reach the shelf safely without wobbling."
        ))
    elif outcome == "wobble":
        qa.append((
            f"What happened when they used {method.phrase}?",
            f"They did get the {container.label} down, but the attempt gave a tiny wobble first. That mattered because the container needed careful handling, especially on a high shelf."
        ))
    else:
        qa.append((
            f"How did they finally get the {container.label} down?",
            f"They used {method.phrase} and moved carefully instead of trying something silly. The plan worked because it gave enough reach and enough steadiness."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the snack open, everyone sharing, and the shelf no longer feeling so bossy. The change is clear because the problem moved from 'too high to reach' to 'safe and funny to remember.'"
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["method"].tags)
    tags |= set(f["container_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("high", "jar", "ask_parent", "Nora", "girl", "Max", "boy", "mother"),
    StoryParams("middle", "tin", "stool", "Leo", "boy", "Mia", "girl", "father"),
    StoryParams("high", "bowl", "grabber", "Ava", "girl", "Ben", "boy", "mother"),
    StoryParams("high", "tin", "chair", "Sam", "boy", "Zoe", "girl", "father"),
]


def explain_rejection(shelf: Shelf, container: Container, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: {method.phrase} is too silly to be the chosen plan here. "
            f"A storyworld should prefer steady, everyday ways like a stool, a chair, a grabber, or asking a grown-up.)"
        )
    if not method_can_reach(method, shelf):
        return (
            f"(No story: {method.phrase} cannot honestly reach {shelf.phrase}. "
            f"Pick a taller help method or a lower shelf.)"
        )
    if method.stability < stability_need(container):
        return (
            f"(No story: {container.label} needs a steadier plan than {method.phrase}. "
            f"It would wobble too much, especially with something that breakable or heavy.)"
        )
    if method.id == "grabber" and container.weight >= 3:
        return (
            f"(No story: the grabber claw is too weak for a heavy {container.label}. "
            f"Choose a method that supports the weight.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
reachable(M, S) :- adult_help(M), shelf(S).
reachable(M, S) :- reach(M, R), shelf_height(S, H), R >= H.

need(C, 3) :- container(C), fragile(C).
need(C, 3) :- container(C), weight(C, W), W >= 2.
need(C, 2) :- container(C), not fragile(C), weight(C, W), W < 2.

steady(M, C) :- stability(M, S), need(C, N), S >= N.
light_enough(M, C) :- method(M), container(C), not special_heavy_rule(M, C).
special_heavy_rule(grabber, C) :- weight(C, W), W >= 3.

reasonable(M, S, C) :- method(M), shelf(S), container(C),
                       sense(M, X), sense_min(MN), X >= MN,
                       reachable(M, S), steady(M, C), light_enough(M, C).

outcome(helped) :- chosen_method(ask_parent).
outcome(wobble) :- chosen_method(M), M != ask_parent, chosen_shelf(S), chosen_container(C),
                   reasonable(M, S, C), need(C, N), stability(M, N).
outcome(wobble) :- chosen_method(M), M != ask_parent, chosen_shelf(S), chosen_container(C),
                   reasonable(M, S, C), not adult_help(M),
                   reach(M, R), shelf_height(S, R).
outcome(easy) :- chosen_method(M), chosen_shelf(S), chosen_container(C),
                 reasonable(M, S, C), not outcome(wobble), M != ask_parent.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for sid, shelf in SHELVES.items():
        lines.append(asp.fact("shelf", sid))
        lines.append(asp.fact("shelf_height", sid, shelf.height))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("weight", cid, container.weight))
        if container.fragile:
            lines.append(asp.fact("fragile", cid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("reach", mid, method.reach))
        lines.append(asp.fact("stability", mid, method.stability))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.adult_help:
            lines.append(asp.fact("adult_help", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_shelf", params.shelf),
        asp.fact("chosen_container", params.container),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: many funny ways to reach a snack, with dialogue and a sensible ending."
    )
    ap.add_argument("--shelf", choices=SHELVES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shelf and args.container and args.method:
        shelf = SHELVES[args.shelf]
        container = CONTAINERS[args.container]
        method = METHODS[args.method]
        if not method_is_reasonable(method, shelf, container):
            raise StoryError(explain_rejection(shelf, container, method))

    combos = [
        c for c in valid_combos()
        if (args.shelf is None or c[0] == args.shelf)
        and (args.container is None or c[1] == args.container)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shelf, container, method = rng.choice(sorted(combos))
    child, cg = _pick_name(rng)
    helper, hg = _pick_name(rng, avoid=child)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(shelf, container, method, child, cg, helper, hg, parent)


def generate(params: StoryParams) -> StorySample:
    world = World()
    world.facts["params"] = params
    world = tell(
        SHELVES[params.shelf],
        CONTAINERS[params.container],
        METHODS[params.method],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
    world.facts["params"] = params
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
        print(asp_program("", "#show reasonable/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shelf, container, method) combos:\n")
        for shelf, container, method in combos:
            print(f"  {shelf:7} {container:8} {method}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} & {p.helper}: {p.container} on {p.shelf} shelf ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
