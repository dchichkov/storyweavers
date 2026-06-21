#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cumin_transformation_lesson_learned_comedy.py
=============================================================================

A tiny comedy storyworld about a child, a kitchen, a suspicious spice, and a
surprising transformation. The premise is built from a fresh seed: a child tries
to improve a snack with cumin, the result goes oddly wrong, and a calm grown-up
turns the moment into a funny lesson learned.

The world is simulated, not frozen: state changes drive the prose, the ending
image proves what changed, and the Q&A sets are grounded in the simulated world.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/cumin_transformation_lesson_learned_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/cumin_transformation_lesson_learned_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/cumin_transformation_lesson_learned_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/cumin_transformation_lesson_learned_comedy.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    transform_to: str
    flavor: str
    smells: str
    funny_result: str
    safe_result: str
    danger: int = 1
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
class Spice:
    id: str
    label: str
    phrase: str
    clue: str
    strong: bool = True
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
class Remedy:
    id: str
    label: str
    action: str
    result: str
    lesson: str
    sense: int
    power: int
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
            raise StoryError(f"Missing world entity: {eid}")
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    if pan.meters["toasted"] >= THRESHOLD and ("transform", "pan") not in world.fired:
        world.fired.add(("transform", "pan"))
        pan.meters["new_shape"] = 1.0
        out.append("__transform__")
    return out


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["spiced"] >= THRESHOLD and snack.meters["odd"] < THRESHOLD:
        key = ("odd", "snack")
        if key not in world.fired:
            world.fired.add(key)
            snack.meters["odd"] = 1.0
            out.append("The kitchen smelled like a joke that had gone slightly too far.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    if kid.memes["embarrassed"] >= THRESHOLD and kid.memes["lesson"] < THRESHOLD:
        key = ("lesson", "kid")
        if key not in world.fired:
            world.fired.add(key)
            kid.memes["lesson"] = 1.0
            out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("transform", _r_transform),
    Rule("smell", _r_smell),
    Rule("lesson", _r_lesson),
]


@dataclass
class StoryParams:
    kid_name: str
    kid_gender: str
    parent_name: str
    parent_gender: str
    dish: str
    spice: str
    remedy: str
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


KID_NAMES = ["Mia", "Leo", "Zoe", "Ava", "Noah", "Ben", "Lily", "Finn"]
PARENT_NAMES = ["Mom", "Dad"]
DISHES = {
    "toast": Dish(
        id="toast",
        label="toast",
        phrase="a plain piece of toast",
        transform_to="fancy toast",
        flavor="buttery",
        smells="like a breakfast grin",
        funny_result="a brown puffed-up toast hat",
        safe_result="a golden snack",
        danger=1,
        tags={"toast", "food"},
    ),
    "eggs": Dish(
        id="eggs",
        label="scrambled eggs",
        phrase="a bowl of scrambled eggs",
        transform_to="sunny eggs",
        flavor="soft",
        smells="like morning sunshine",
        funny_result="tiny fluffy clouds in a pan",
        safe_result="a warm breakfast",
        danger=2,
        tags={"eggs", "food"},
    ),
    "rice": Dish(
        id="rice",
        label="rice",
        phrase="a little bowl of rice",
        transform_to="golden rice",
        flavor="plain",
        smells="like a picnic in a pantry",
        funny_result="a very serious bowl of confused grains",
        safe_result="a tasty side dish",
        danger=1,
        tags={"rice", "food"},
    ),
}
SPICES = {
    "cumin": Spice(
        id="cumin",
        label="cumin",
        phrase="a tiny shaker of cumin",
        clue="a warm, dusty smell that sounded like a trumpet in socks",
        strong=True,
        tags={"cumin", "spice"},
    ),
    "cinnamon": Spice(
        id="cinnamon",
        label="cinnamon",
        phrase="a little jar of cinnamon",
        clue="a sweet smell that felt like a hug from a bun",
        strong=False,
        tags={"cinnamon", "spice"},
    ),
    "paprika": Spice(
        id="paprika",
        label="paprika",
        phrase="a red jar of paprika",
        clue="a bright smell that tickled noses",
        strong=True,
        tags={"paprika", "spice"},
    ),
}
REMEDIES = {
    "yogurt": Remedy(
        id="yogurt",
        label="plain yogurt",
        action="stir in a spoon of plain yogurt",
        result="the snack calmed down and became friendly again",
        lesson="a little of the right thing can fix a big-sounding mistake",
        sense=3,
        power=3,
        tags={"cool", "food"},
    ),
    "sugar": Remedy(
        id="sugar",
        label="sugar",
        action="sprinkle sugar on top",
        result="the snack got sweeter, but also a little confused",
        lesson="not every fix matches the problem",
        sense=1,
        power=1,
        tags={"sweet", "food"},
    ),
    "lemon": Remedy(
        id="lemon",
        label="lemon juice",
        action="add a tiny squeeze of lemon juice",
        result="the flavor brightened up and stopped acting so bossy",
        lesson="small careful changes can rescue a snack",
        sense=2,
        power=2,
        tags={"bright", "food"},
    ),
}
CAUTIOUS = {"careful", "cautious", "thoughtful"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for d in DISHES:
        for s in SPICES:
            for r in REMEDIES:
                if SPICES[s].strong and REMEDIES[r].sense >= SENSE_MIN:
                    combos.append((d, s, r))
    return combos


def best_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def oddity_level(spice: Spice, dish: Dish) -> int:
    return 2 if spice.strong else 1


def transformation_success(spice: Spice, dish: Dish) -> bool:
    return spice.id == "cumin" and dish.id in {"toast", "rice", "eggs"}


def remedy_works(remedy: Remedy, dish: Dish) -> bool:
    return remedy.power >= dish.danger


def reasonability_gate(spice: Spice, dish: Dish) -> Optional[str]:
    if spice.id != "cumin":
        return None
    if not transformation_success(spice, dish):
        return None
    return None


def _do_spice(world: World, kid: Entity, dish: Entity, spice: Spice) -> None:
    kid.meters["hope"] += 1
    dish.meters["spiced"] += 1
    dish.meters["toasted"] += 1 if spice.id == "cumin" and dish.id == "toast" else 0
    if dish.id == "eggs":
        dish.meters["wiggle"] += 1
    propagate(world, narrate=False)


def make_story(world: World, kid: Entity, parent: Entity, dish: Dish, spice: Spice, remedy: Remedy) -> None:
    world.say(
        f"{kid.id} tiptoed into the kitchen, where {dish.phrase} waited on the counter."
    )
    world.say(
        f'“I can improve it,” {kid.id} said, and opened {spice.phrase}. '
        f'{spice.clue.capitalize()}.'
    )
    world.say(
        f"{parent.label_word.capitalize()} peeked over the counter and said, "
        f'“That smells like a trumpet wearing socks.”'
    )

    world.para()
    world.say(
        f"{kid.id} sprinkled in {spice.label}, and the whole kitchen blinked."
    )
    if transformation_success(spice, dish):
        world.get("pan").meters["toasted"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The {dish.label} changed at once: it became {dish.transform_to}, "
            f"and for a second it looked very proud of itself."
        )
        world.say(
            f"Then everyone laughed, because the smell was strong but the joke was stronger."
        )
    else:
        world.say(
            f"Instead of becoming better, the {dish.label} acted as if it had forgotten its manners."
        )

    world.para()
    if remedy_works(remedy, dish):
        world.say(
            f'{parent.label_word.capitalize()} came to the rescue and {remedy.action}. '
            f'That made the problem manageable.'
        )
        world.say(
            f"After that, {remedy.result}, and {kid.id} grinned through the last crumb."
        )
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
        world.say(
            f'{kid.id} learned that {remedy.lesson}, and that not every kitchen mystery needs more spice.'
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} tried {remedy.action}, but it was too small for the flavor fight."
        )
        world.say(
            f"Still, the day ended with a funny face, a sticky spoon, and a very important lesson: "
            f"{remedy.lesson}."
        )
        kid.memes["lesson"] += 1

    world.para()
    world.say(
        f"In the end, the {dish.label} was not the same as before: it was now {dish.safe_result}, "
        f"and the cumin jar was put back on the shelf like it had done its tiny dramatic part."
    )


def tell(dish: Dish, spice: Spice, remedy: Remedy,
         kid_name: str = "Mia", kid_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "woman") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="child", traits=["curious"]))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="pan", type="pan"))
    snack = world.add(Entity(id="snack", type="snack", label=dish.label))
    world.facts["dish"] = dish
    world.facts["spice"] = spice
    world.facts["remedy"] = remedy
    world.facts["kid"] = kid
    world.facts["parent"] = parent

    make_story(world, kid, parent, dish, spice, remedy)
    snack.meters["odd"] = 1 if spice.id == "cumin" else 0
    world.facts.update(outcome="lesson learned", transformed=transformation_success(spice, dish))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dish, spice, remedy = f["dish"], f["spice"], f["remedy"]
    return [
        f'Write a funny story for a child about {spice.label} and a kitchen surprise.',
        f"Tell a comedy story where a child tries to improve {dish.phrase} with {spice.label}, "
        f"but the result changes in a silly way and a grown-up helps fix it.",
        f"Write a short story that includes the word '{spice.label}' and ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, parent = f["kid"], f["parent"]
    dish, spice, remedy = f["dish"], f["spice"], f["remedy"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {parent.id} in the kitchen. {kid.id} is the one who tries the funny idea first."),
        ("What did {kid} want to do?".replace("{kid}", kid.id),
         f"{kid.id} wanted to improve {dish.phrase} with {spice.label}. {kid.id} thought the spice would make the snack better."),
        ("What did the grown-up do?",
         f"{parent.id} helped by choosing {remedy.label}. That turned the mistake into something workable."),
        ("What did the child learn?",
         f"{kid.id} learned that {remedy.lesson}. The story ends with a lesson learned instead of a disaster."),
    ]
    if f.get("transformed"):
        qa.append((
            "What changed in the snack?",
            f"It transformed into {dish.transform_to}. The cumin made it act extra dramatic, which was funny instead of bad."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    spice = world.facts["spice"]
    dish = world.facts["dish"]
    remedy = world.facts["remedy"]
    out = []
    if spice.id == "cumin":
        out.append(("What is cumin?",
                     "Cumin is a spice with a warm, earthy smell. People use it to flavor food, but a little can go a long way."))
    out.append(("What is a transformation?",
                 "A transformation is when something changes into a new form or becomes very different. In stories, that change can be funny, surprising, or magical."))
    out.append(("Why do people taste food carefully when adding spices?",
                 "Because spices can be strong, and too much at once can change the flavor a lot. Small careful changes are easier to fix."))
    out.append(("What is a lesson learned?",
                 "A lesson learned is a useful thing someone remembers after making a mistake or trying something new. It helps them do better next time."))
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this tiny comedy world only supports cumin plus a sensible fix.)"


ASP_RULES = r"""
strong_spice(cumin).
sensible_remedy(yogurt).
sensible_remedy(lemon).
valid_combo(Dish, cumin, Remedy) :- dish(Dish), strong_spice(cumin), sensible_remedy(Remedy).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for d in DISHES:
        lines.append(asp.fact("dish", d))
    lines.append(asp.fact("spice", "cumin"))
    lines.append(asp.fact("spice", "cinnamon"))
    lines.append(asp.fact("spice", "paprika"))
    for r, rem in REMEDIES.items():
        if rem.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible_remedy", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about cumin, transformation, and a lesson learned.")
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--spice", choices=SPICES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.spice and args.spice != "cumin":
        raise StoryError("This comedy seed world is built around cumin.")
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError("Pick a sensible remedy for the story.")
    dish = args.dish or rng.choice(sorted(DISHES))
    spice = "cumin"
    remedy = args.remedy or rng.choice(sorted(r.id for r in best_remedies()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(KID_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(kid_name=name, kid_gender=gender, parent_name=parent, parent_gender=("woman" if parent == "Mom" else "man"), dish=dish, spice=spice, remedy=remedy)


def generate(params: StoryParams) -> StorySample:
    if params.spice != "cumin":
        raise StoryError("This storyworld only supports cumin.")
    world = tell(DISHES[params.dish], SPICES[params.spice], REMEDIES[params.remedy], params.kid_name, params.kid_gender, params.parent_name, params.parent_gender)
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


CURATED = [
    StoryParams(kid_name="Mia", kid_gender="girl", parent_name="Mom", parent_gender="woman", dish="toast", spice="cumin", remedy="yogurt"),
    StoryParams(kid_name="Leo", kid_gender="boy", parent_name="Dad", parent_gender="man", dish="eggs", spice="cumin", remedy="lemon"),
    StoryParams(kid_name="Zoe", kid_gender="girl", parent_name="Mom", parent_gender="woman", dish="rice", spice="cumin", remedy="yogurt"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
