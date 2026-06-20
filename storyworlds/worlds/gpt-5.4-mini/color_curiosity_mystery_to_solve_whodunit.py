#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/color_curiosity_mystery_to_solve_whodunit.py
==============================================================================

A small standalone storyworld for a kid-friendly whodunit about color:
a curious child notices a mystery in a paint set, follows clues through a few
objects and rooms, and solves who made the color vanish or change. The story
is state-driven: curiosity rises, clues accumulate, suspicion narrows, the true
cause is revealed, and the ending image proves what changed.

Domain shape
------------
- A child wants to make a colorful picture.
- One color is missing, mixed, or smeared in a puzzling way.
- The child and a helper investigate a tiny set of likely suspects.
- A causal model tracks physical meters and emotional memes.
- The mystery resolves in a concrete ending: the color is found, restored,
  or explained.

This script is self-contained and uses only the Python standard library plus the
shared results containers from storyworlds/results.py.
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
class Scene:
    id: str
    place: str
    clue_place: str
    opening_image: str
    suspect_note: str
    ending_image: str
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
class ColorMystery:
    id: str
    label: str
    phrase: str
    missing_phrase: str
    reason: str
    revelation: str
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
class Suspect:
    id: str
    label: str
    phrase: str
    clue: str
    harmless: bool
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
class Solution:
    id: str
    action: str
    result: str
    power: int
    sense: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curiosity", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("__curious__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["clues"] < THRESHOLD:
        return out
    sig = ("clue_sure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confidence"] += 1
    out.append("__clue__")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    if world.get("mystery").meters["solved"] < THRESHOLD:
        return out
    sig = ("solved",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["relief"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule("curiosity", "social", _r_curiosity),
    Rule("clue", "mental", _r_clue),
    Rule("solution", "mental", _r_solution),
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


def valid_combo(scene: Scene, mystery: ColorMystery, suspect: Suspect, solution: Solution) -> bool:
    return solution.sense >= 2 and mystery.id in suspect.tags and scene.id in mystery.tags


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def mystery_to_solve(mystery: ColorMystery) -> bool:
    return True


def predict(world: World, mystery: ColorMystery, suspect: Suspect, solution: Solution) -> dict:
    sim = world.copy()
    sim.get("mystery").meters["solved"] += 1 if solution.power >= 1 else 0
    propagate(sim, narrate=False)
    return {"solved": sim.get("mystery").meters["solved"] >= THRESHOLD}


def setup(world: World, child: Entity, helper: Entity, scene: Scene, mystery: ColorMystery) -> None:
    child.memes["curiosity"] += 1
    child.memes["nervousness"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} were in {scene.place}. "
        f"{scene.opening_image}"
    )
    world.say(
        f'{child.id} leaned over the art table. "Where did the {mystery.label} color go?" '
        f"{child.pronoun()} asked."
    )


def notice(world: World, child: Entity, mystery: ColorMystery) -> None:
    world.say(
        f"It was a small whodunit. The {mystery.label} color was missing, and the page looked wrong "
        f"without it."
    )
    world.say(
        f'{child.id} looked closely and felt {child.pronoun("possessive")} curiosity wake up even more.'
    )


def inspect(world: World, child: Entity, suspect: Suspect) -> None:
    child.meters["clues"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f'They checked {suspect.phrase}. {suspect.clue}'
    )


def narrow(world: World, helper: Entity, suspect: Suspect) -> None:
    helper.memes["helpfulness"] += 1
    if suspect.harmless:
        world.say(
            f'{helper.id} smiled. "That one is not the culprit," {helper.pronoun()} said. '
            f"The clue only looked strange."
        )
    else:
        world.say(
            f'{helper.id} frowned. "This clue matters," {helper.pronoun()} said softly.'
        )


def reveal(world: World, child: Entity, mystery: ColorMystery, solution: Solution) -> None:
    world.get("mystery").meters["solved"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} found the answer: {solution.action}. '
        f"{mystery.revelation}"
    )


def restore(world: World, child: Entity, scene: Scene, mystery: ColorMystery, solution: Solution) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{solution.result}. Soon the {mystery.label} color was back where it belonged."
    )
    world.say(
        scene.ending_image
    )
    world.say(
        f'{child.id} grinned at the finished picture. The mystery was solved, and the color made the whole page glow.'
    )


def tell(scene: Scene, mystery: ColorMystery, suspect: Suspect, solution: Solution,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label="the helper"))
    world.add(Entity(id="mystery", type="mystery", label=mystery.label))
    world.add(Entity(id="scene", type="scene", label=scene.place))
    world.add(Entity(id="suspect", type="suspect", label=suspect.label))
    world.add(Entity(id="solution", type="solution", label=solution.id))

    setup(world, child, helper, scene, mystery)
    notice(world, child, mystery)
    world.para()
    inspect(world, child, suspect)
    narrow(world, helper, suspect)
    if mystery_to_solve(mystery):
        world.para()
        reveal(world, child, mystery, solution)
        restore(world, child, scene, mystery, solution)

    world.facts.update(
        child=child, helper=helper, scene=scene, mystery=mystery,
        suspect=suspect, solution=solution, solved=world.get("mystery").meters["solved"] >= THRESHOLD
    )
    return world


SCENES = {
    "artroom": Scene(
        "artroom", "the art room", "the color shelf",
        "The paint cups sat in a neat row, but one little space on the shelf was empty.",
        "A smear near the sink looked like a clue, but no one knew whose it was.",
        "The missing cup was back on the shelf, and the whole painting shone with red, blue, and gold.",
        tags={"artroom", "paint"},
    ),
    "kitchen": Scene(
        "kitchen", "the kitchen table", "the counter",
        "The cookie dough was cooling, and a rainbow dish of sprinkles waited nearby.",
        "A bright crumb trail pointed toward the sink.",
        "The color came from a bowl of sprinkles, and the cookies looked cheerful again.",
        tags={"kitchen", "color"},
    ),
    "classroom": Scene(
        "classroom", "the classroom", "the paint caddy",
        "The easels stood like little detectives waiting for a case.",
        "A blue handprint on a chair made everyone pause.",
        "The blue paint was found in the caddy, and the class picture went from plain to lively.",
        tags={"classroom", "color"},
    ),
}

MYSTERIES = {
    "missing_red": ColorMystery(
        "missing_red", "red", "red cup", "missing red",
        "someone had carried it to the sink and set it down", "The red cup was hiding beside the rinse water.",
        tags={"artroom", "classroom", "color"},
    ),
    "mixed_blue": ColorMystery(
        "mixed_blue", "blue", "blue paint", "mixed-up blue",
        "someone had stirred the blue with white until it turned pale", "The blue color had been lightened by a new mix.",
        tags={"classroom", "artroom", "color"},
    ),
    "lost_gold": ColorMystery(
        "lost_gold", "gold", "gold glitter", "lost gold",
        "someone had sprinkled it by the sink and the shine had rolled away", "The gold glitter was stuck in the paper towel roll.",
        tags={"artroom", "kitchen", "color"},
    ),
}

SUSPECTS = {
    "sink": Suspect("sink", "the sink", "the sink with wet drips", "There was a wet ring, so something had just been washed.", True, tags={"missing_red", "lost_gold"}),
    "brush": Suspect("brush", "the paintbrush", "the paintbrush cup", "The brush looked innocent, but it was stuck together with color.", True, tags={"mixed_blue", "missing_red"}),
    "cat": Suspect("cat", "the cat", "the sleepy cat under the table", "The cat had blue on one paw, but it was not the reason the color vanished.", True, tags={"mixed_blue", "lost_gold"}),
    "paper_towel": Suspect("paper_towel", "the paper towel roll", "the paper towel roll by the counter", "A shining speck was tucked inside the cardboard tube.", False, tags={"lost_gold"}),
}

SOLUTIONS = {
    "find_sink": Solution("find_sink", "looked beside the rinse water", "The helper lifted the cup out of the water and dried it", 2, 3, tags={"missing_red"}),
    "check_mix": Solution("check_mix", "made a new careful mix", "The helper added a little more blue and the pale color became bright again", 2, 3, tags={"mixed_blue"}),
    "find_roll": Solution("find_roll", "opened the paper towel roll", "The helper shook the glitter loose and caught every sparkling bit", 2, 3, tags={"lost_gold"}),
    "too_weak": Solution("too_weak", "tried to wish it back", "Wishing did not help at all", 0, 1, tags={"missing_red", "mixed_blue", "lost_gold"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Noa"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Noah", "Theo", "Max"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    mystery: str
    suspect: str
    solution: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for mid, mystery in MYSTERIES.items():
            if sid not in mystery.tags:
                continue
            for susid, suspect in SUSPECTS.items():
                if mid not in suspect.tags:
                    continue
                for sol in SOLUTIONS.values():
                    if mid in sol.tags and sol.sense >= 2:
                        combos.append((sid, mid, susid, sol.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny color whodunit storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.solution is None or c[3] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, mystery, suspect, solution = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("girl" if child_gender == "boy" else "boy")
    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    child = args.child or rng.choice(child_pool)
    helper_choices = [n for n in helper_pool if n != child]
    helper = args.helper or rng.choice(helper_choices or helper_pool)
    return StoryParams(scene, mystery, suspect, solution, child, child_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a kid-friendly whodunit about the color {f["mystery"].label} going missing in {f["scene"].place}.',
        f"Tell a curious mystery story where {f['child'].id} investigates a color problem and solves it with help from {f['helper'].id}.",
        f'Write a story that includes the word "color" and ends with the mystery being solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, mystery, suspect, solution = f["child"], f["helper"], f["mystery"], f["suspect"], f["solution"]
    items = [
        QAItem(
            question="What was the child trying to figure out?",
            answer=f"{child.id} was trying to figure out why the {mystery.label} color had gone missing. It was a little mystery about what happened to the paint.",
        ),
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{helper.id} helped by looking closely and finding the right clue. Together they followed the clue until the color problem made sense.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The mystery was solved, and the {mystery.label} color was found again. The picture looked bright and complete at the end.",
        ),
    ]
    if f["solved"]:
        items.append(QAItem(
            question="How did they solve it?",
            answer=f"They {solution.action} and found the answer hidden in a tiny place. That careful action fixed the color problem and made the page look right again.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["mystery"].tags) | set(f["suspect"].tags)
    out: list[QAItem] = []
    if "color" in tags:
        out.append(QAItem(
            question="What is color?",
            answer="Color is what makes things look red, blue, gold, and many other shades. It helps us notice differences in pictures and objects.",
        ))
    out.append(QAItem(
        question="What should a curious detective do first?",
        answer="A curious detective should look carefully and follow clues one by one. That helps the detective learn what really happened instead of guessing too fast.",
    ))
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], MYSTERIES[params.mystery], SUSPECTS[params.suspect], SOLUTIONS[params.solution],
                 params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(SC, MI, SU, SO) :- scene(SC), mystery(MI), suspect(SU), solution(SO),
                         scene_has_mystery(SC, MI), suspect_clue(SU, MI),
                         solution_for(SO, MI), sense(SO, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for suid in SUSPECTS:
        lines.append(asp.fact("suspect", suid))
    for soid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", soid))
        lines.append(asp.fact("sense", soid, sol.sense))
    for sid, sc in SCENES.items():
        for mid, ms in MYSTERIES.items():
            if sid in ms.tags:
                lines.append(asp.fact("scene_has_mystery", sid, mid))
    for suid, su in SUSPECTS.items():
        for mid in su.tags:
            lines.append(asp.fact("suspect_clue", suid, mid))
    for soid, sol in SOLUTIONS.items():
        for mid in sol.tags:
            lines.append(asp.fact("solution_for", soid, mid))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return rc


CURATED = [
    StoryParams("artroom", "missing_red", "sink", "find_sink", "Mia", "girl", "Mom", "girl"),
    StoryParams("classroom", "mixed_blue", "brush", "check_mix", "Ben", "boy", "Dad", "boy"),
    StoryParams("kitchen", "lost_gold", "paper_towel", "find_roll", "Lily", "girl", "Mom", "girl"),
]


def build_story(sample: StoryParams) -> StorySample:
    return generate(sample)


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
        print(f"{len(asp_valid_combos())} compatible stories")
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
            params = resolve_params(args, random.Random(seed))
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
