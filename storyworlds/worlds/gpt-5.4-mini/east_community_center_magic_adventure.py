#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/east_community_center_magic_adventure.py
========================================================================

A standalone storyworld for a small community-center adventure with a little
magic, a problem, a careful turn, and a bright ending.

Seed premise:
- Setting: community center
- Style: adventure
- Feature: magic
- Seed word: east

The story world models a child exploring the east side of a community center,
discovering a little magic trick that goes wrong, then using a sensible fix with
help from a grown-up or guide. The world keeps state in meters and memes so the
story is driven by simulated events rather than a frozen template.
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
SENSE_MIN = 2
ADVENTURE_BEATS = ("map", "search", "key", "spark", "lantern")
EAST_WORD = "east"


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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    detail: str
    direction: str = "east"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class MagicItem:
    id: str
    label: str
    phrase: str
    use: str
    effect: str
    risky: bool = False
    harmless: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Problem:
    id: str
    label: str
    phrase: str
    danger: str
    fix_text: str
    fail_text: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Helper:
    id: str
    label: str
    role_line: str
    calmness: int
    power: int
    solution: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glimmer"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for child in list(world.entities.values()):
            if child.role == "adventurer":
                child.memes["startle"] += 1
        out.append("__spook__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glimmer"] < THRESHOLD or e.meters["steady"] >= THRESHOLD:
            continue
        sig = ("fix", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["steady"] += 1
        out.append("__fix__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook), Rule("fix", _r_fix)]


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


def safe_magic(item: MagicItem) -> bool:
    return item.harmless and not item.risky


def hazard(item: MagicItem, problem: Problem) -> bool:
    return item.risky and problem.power > 0


def can_fix(helper: Helper, problem: Problem) -> bool:
    return helper.power >= problem.power and helper.calmness >= SENSE_MIN


def choose_solution() -> Helper:
    return max(HELPERS.values(), key=lambda h: (h.calmness, h.power))


def _do_magic(world: World, item: MagicItem) -> None:
    world.get(item.id).meters["glimmer"] += 1
    if item.risky:
        world.get(item.id).meters["spark"] += 1
    propagate(world, narrate=False)


def setup(world: World, child: Entity, guide: Entity, place: Place, item: MagicItem) -> None:
    child.memes["joy"] += 1
    guide.memes["curiosity"] += 1
    world.say(
        f"On an afternoon at the community center, {child.id} slipped in through the {place.direction} door with {guide.id}. "
        f"{place.detail} The air felt like it was waiting for an adventure."
    )
    world.say(
        f"{child.id} found a {item.label} tucked near the bulletin board and whispered, "
        f'"It looks like magic."'
    )


def seek(world: World, child: Entity, place: Place) -> None:
    child.memes["quest"] += 1
    world.say(
        f"{child.id} wanted to explore the {place.direction} hall and see what the old room had hidden there."
    )


def tempt(world: World, child: Entity, item: MagicItem) -> None:
    child.memes["bold"] += 1
    world.say(
        f"{child.id}'s eyes lit up. \"I know! {item.phrase}. If I use it, maybe it will {item.use}.\""
    )


def warn(world: World, guide: Entity, child: Entity, item: MagicItem, problem: Problem) -> None:
    guide.memes["care"] += 1
    world.say(
        f"{guide.id} touched {child.id}'s shoulder gently. \"That might be clever, but it could leave {problem.label} behind. "
        f"{problem.danger} {guide.label_word if guide.label_word else 'A grown-up'} should help.\""
    )


def trigger(world: World, child: Entity, item: MagicItem, problem: Problem) -> None:
    child.memes["defiance"] += 1
    _do_magic(world, item)
    world.say(
        f"{child.id} tried it anyway. The {item.label} flashed with a little {item.effect}, and for a moment the whole east side of the center glowed."
    )
    world.say(
        f"Then the glow leaned toward {problem.label} and turned the game into real trouble."
    )


def alarm(world: World, child: Entity, guide: Entity, problem: Problem) -> None:
    world.say(f'"{guide.id}!" {child.id} yelled. "The {problem.label}!"')
    world.say(f"{guide.id} ran closer at once.")


def solve(world: World, guide: Entity, helper: Helper, problem: Problem) -> None:
    world.get(problem.id).meters["steady"] += 1
    world.say(
        f"{guide.id} reached for a calm fix and {helper.solution}."
    )
    world.say(
        f"The trouble settled down, and the {problem.label} stopped wobbling in the magic light."
    )


def lesson(world: World, guide: Entity, child: Entity, item: MagicItem) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"For a moment, nobody moved. Then {guide.id} smiled and knelt beside {child.id}. "
        f"\"Magic is wonderful,\" {guide.id} said, \"but you must use the safe kind when you are in a public place.\""
    )
    world.say(
        f"{child.id} nodded and held the {item.label} carefully, glad the adventure had ended without anyone getting hurt."
    )


def ending(world: World, child: Entity, guide: Entity, item: MagicItem) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After that, {child.id} and {guide.id} followed the {EAST_WORD} hallway to the activity room, "
        f"and the {item.label} shone only as a harmless little guide-light."
    )
    world.say(
        f"The east wing felt adventurous again, but now it was calm, bright, and safe."
    )


def tell(place: Place, item: MagicItem, problem: Problem, helper: Helper,
         child_name: str = "Maya", child_gender: str = "girl",
         guide_name: str = "Ms. Rivera", guide_gender: str = "woman") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="adventurer"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    item_ent = world.add(Entity(id="magic_item", type="thing", label=item.label))
    prob_ent = world.add(Entity(id="problem", type="thing", label=problem.label))
    world.facts["item"] = item
    world.facts["problem"] = problem
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["guide"] = guide
    world.facts["place"] = place

    setup(world, child, guide, place, item)
    world.para()
    seek(world, child, place)
    tempt(world, child, item)
    warn(world, guide, child, item, problem)

    world.para()
    trigger(world, child, item, problem)
    alarm(world, child, guide, problem)

    world.para()
    solve(world, guide, helper, problem)
    lesson(world, guide, child, item)
    world.para()
    ending(world, child, guide, item)

    item_ent.meters["glimmer"] = world.get("magic_item").meters["glimmer"]
    prob_ent.meters["steady"] = world.get("problem").meters["steady"]
    world.facts["resolved"] = True
    world.facts["scared"] = child.memes["startle"] >= THRESHOLD
    return world


PLACES = {
    "community_center": Place("community_center", "the community center", "The east wing held a craft table, a corkboard of flyers, and a long hallway lined with paper stars.", "east"),
}

MAGIC_ITEMS = {
    "wand": MagicItem("wand", "sparkly wand", "wave the wand", "make a trail of stars appear", "silver sparks", risky=True, tags={"magic", "spark"}),
    "card": MagicItem("card", "magic card", "flip the card", "reveal a secret path", "bright swirls", risky=True, tags={"magic", "map"}),
    "lantern": MagicItem("lantern", "glowing lantern", "lift the lantern", "light the way without fire", "soft gold light", harmless=True, tags={"magic", "lantern"}),
}

PROBLEMS = {
    "locked_door": Problem("locked_door", "locked door", "the locked door", "It needed a key, not just a trick.", "get the right key from the desk", "could not open it in time", 2, tags={"door", "key"}),
    "paper_snag": Problem("paper_snag", "paper snag", "the paper star display", "It might tear the decorations down.", "steady the string and tape the star back", "could not save the decorations", 1, tags={"paper"}),
    "fallen_box": Problem("fallen_box", "fallen box", "the tipped craft box", "Small pieces might spill everywhere.", "lift the box and gather the pieces carefully", "could not stop the mess", 2, tags={"box"}),
}

HELPERS = {
    "guide": Helper("guide", "guide", "kept a steady head and knew the room well", calmness=3, power=3, solution="found the right key in the desk drawer and opened the door"),
    "caretaker": Helper("caretaker", "caretaker", "knew how to calm busy rooms", calmness=3, power=2, solution="taped the paper star back into place"),
    "janitor": Helper("janitor", "janitor", "moved quickly with a careful plan", calmness=2, power=3, solution="lifted the craft box and gathered the pieces in a tray"),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    problem: str
    helper: str
    child: str
    child_gender: str
    guide: str
    guide_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in MAGIC_ITEMS.items():
            for problem_id, problem in PROBLEMS.items():
                if hazard(item, problem):
                    for helper_id, helper in HELPERS.items():
                        if can_fix(helper, problem):
                            combos.append((place_id, item_id, problem_id, helper_id))
    return combos


def explain_rejection(item: MagicItem, problem: Problem) -> str:
    return (
        f"(No story: {item.label} would create magic, but not enough of a dangerous turn for {problem.label}. "
        f"Pick a risky magic item and a problem with real stakes so the adventure has something to solve.)"
    )


def explain_helper(helper: Helper, problem: Problem) -> str:
    return f"(No story: {helper.label} is not steady enough to fix {problem.label} in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A community-center adventure with magic, caution, and a safe ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=MAGIC_ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["woman", "man"])
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
    if args.item and args.problem and not hazard(MAGIC_ITEMS[args.item], PROBLEMS[args.problem]):
        raise StoryError(explain_rejection(MAGIC_ITEMS[args.item], PROBLEMS[args.problem]))
    if args.helper and args.problem and not can_fix(HELPERS[args.helper], PROBLEMS[args.problem]):
        raise StoryError(explain_helper(HELPERS[args.helper], PROBLEMS[args.problem]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.problem is None or c[2] == args.problem)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, problem, helper = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or "woman"
    child = args.child or rng.choice(["Maya", "Ari", "Nina", "Leo", "Owen", "Tessa"])
    guide = args.guide or ("Ms. Rivera" if guide_gender == "woman" else "Mr. Hale")
    return StoryParams(place, item, problem, helper, child, child_gender, guide, guide_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story set in a community center that includes the word "{EAST_WORD}" and a little magic.',
        f"Tell a story about {f['child'].id} exploring the east side of the community center, where a magical object causes a problem and a guide helps fix it.",
        f"Write a safe adventure about magic in the community center with a problem, a warning, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    item = f["item"]
    problem = f["problem"]
    helper = f["helper"]
    return [
        QAItem(
            question="Where does the story take place?",
            answer="It takes place at the community center, especially on the east side where the adventure begins.",
        ),
        QAItem(
            question=f"What did {child.id} find?",
            answer=f"{child.id} found a {item.label}, and it looked like it could do a little magic.",
        ),
        QAItem(
            question=f"Why did {guide.id} warn {child.id}?",
            answer=f"{guide.id} warned {child.id} because the magic could leave {problem.label} behind and turn a fun game into trouble. A calm adult should help when that happens.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{guide.id} used {helper.solution}. That was the steady, sensible fix, so the east wing could feel adventurous again without danger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    qs = [
        QAItem("What is a community center?", "A community center is a public place where people gather for games, classes, crafts, and other activities."),
        QAItem("What does east mean?", "East is a direction. If you face the rising sun, east is the way it comes up."),
    ]
    if item.harmless:
        qs.append(QAItem("Can a lantern be magical and still safe?", "Yes. A lantern can look magical, but if it only makes soft light it can be safe to use."))
    else:
        qs.append(QAItem("Why can a sparkly magic item be risky?", "Because magic that flashes or changes things can make a mess, startle people, or lead to danger if nobody is careful."))
    return qs


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("community_center", "wand", "locked_door", "guide", "Maya", "girl", "Ms. Rivera", "woman"),
    StoryParams("community_center", "card", "paper_snag", "caretaker", "Leo", "boy", "Ms. Rivera", "woman"),
    StoryParams("community_center", "lantern", "fallen_box", "janitor", "Tessa", "girl", "Mr. Hale", "man"),
]


def outcome_of(params: StoryParams) -> str:
    return "resolved" if can_fix(HELPERS[params.helper], PROBLEMS[params.problem]) else "stuck"


ASP_RULES = r"""
hazard(I, P) :- risky(I), problem(P), power(P, N), N > 0.
fixable(H, P) :- helper(H), calmness(H, C), power(H, PWR), need(P, N), C >= 2, PWR >= N.
valid(P0, I, P, H) :- place(P0), hazard(I, P), fixable(H, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
    for iid, item in MAGIC_ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.risky:
            lines.append(asp.fact("risky", iid))
        if item.harmless:
            lines.append(asp.fact("harmless", iid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("power", pid, p.power))
        lines.append(asp.fact("need", pid, p.power))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("calmness", hid, h.calmness))
        lines.append(asp.fact("power", hid, h.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    # smoke test normal generation
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, problem=None, helper=None, child=None, child_gender=None, guide=None, guide_gender=None), random.Random(777)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MAGIC_ITEMS[params.item], PROBLEMS[params.problem], HELPERS[params.helper],
                 params.child, params.child_gender, params.guide, params.guide_gender)
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
