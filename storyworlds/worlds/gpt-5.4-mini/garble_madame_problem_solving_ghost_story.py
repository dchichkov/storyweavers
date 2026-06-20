#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/garble_madame_problem_solving_ghost_story.py
=============================================================================

A tiny standalone storyworld about a child, a spooky old house, a garbled message,
and Madame who helps solve the mystery without turning the tale into a frozen
template.

Seed idea
---------
A ghost story in which a child hears a garbled whisper from a house, thinks it
means something scary, and then solves the problem with a calm adult. The
ending should feel ghostly but safe: the "ghost" is usually a trapped sound,
a draft, or a simple clue that gets decoded.

The world includes the seed words "garble" and "madame" and keeps a gentle,
child-facing ghost-story mood.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/garble_madame_problem_solving_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/garble_madame_problem_solving_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/garble_madame_problem_solving_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/garble_madame_problem_solving_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/garble_madame_problem_solving_ghost_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not isinstance(self.meters, dict):
            self.meters = {}
        if not isinstance(self.memes, dict):
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "madame"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "madame": "madame"}.get(self.type, self.type)



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
    haunted: bool
    echo_level: int
    clue_kind: str
    mood: str
    secret: str
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
class Problem:
    id: str
    source: str
    garble_style: str
    risk: str
    hidden_truth: str
    solved_by: str
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
class Tool:
    id: str
    label: str
    use: str
    gives_light: bool = False
    reveals: bool = False
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _get_meter(e: Entity, key: str) -> float:
    return float(e.meters.get(key, 0.0))


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _get_meme(e: Entity, key: str) -> float:
    return float(e.memes.get(key, 0.0))


def _set_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_whisper(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if _get_meter(child, "heard_garble") >= THRESHOLD and ("whisper",) not in world.fired:
        world.fired.add(("whisper",))
        _set_meme(child, "unease", _get_meme(child, "unease") + 1)
        out.append("__whisper__")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if _get_meme(child, "curiosity") >= THRESHOLD and _get_meter(child, "clue_found") >= THRESHOLD:
        sig = ("solve",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        _set_meme(child, "fear", max(0.0, _get_meme(child, "fear") - 1))
        _set_meme(child, "pride", _get_meme(child, "pride") + 1)
        out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("whisper", _r_whisper), Rule("solve", _r_solve)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def signal_risky(problem: Problem, place: Place) -> bool:
    return place.haunted and problem.source in {"voice", "bell", "door"}


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.reveals or t.gives_light]


def answerable(problem: Problem, tool: Tool, place: Place) -> bool:
    return tool.reveals and place.haunted


def predict(world: World, tool_id: str) -> dict:
    sim = world.copy()
    _use_tool(sim, sim.get(tool_id), narrate=False)
    return {
        "clue": _get_meter(sim.get("child"), "clue_found") >= THRESHOLD,
        "fear": _get_meme(sim.get("child"), "fear"),
    }


def _use_tool(world: World, tool: Entity, narrate: bool = True) -> None:
    child = world.get("child")
    if tool.id == "lantern":
        _set_meter(child, "clue_found", _get_meter(child, "clue_found") + 1)
    elif tool.id == "notebook":
        _set_meter(child, "clue_found", _get_meter(child, "clue_found") + 1)
        _set_meme(child, "curiosity", _get_meme(child, "curiosity") + 1)
    elif tool.id == "radio":
        _set_meter(child, "garble_listened", _get_meter(child, "garble_listened") + 1)
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, companion: Entity, place: Place) -> None:
    _set_meme(child, "curiosity", _get_meme(child, "curiosity") + 1)
    _set_meme(child, "joy", _get_meme(child, "joy") + 1)
    world.say(
        f"On a dim evening, {child.id} and {companion.id} came to {place.label}, "
        f"where the windows whispered to the dark."
    )
    world.say(
        f"The hall felt spooky, and every floorboard gave a tiny sigh."
    )


def garbled_message(world: World, child: Entity, problem: Problem) -> None:
    _set_meter(child, "heard_garble", _get_meter(child, "heard_garble") + 1)
    _set_meme(child, "fear", _get_meme(child, "fear") + 1)
    world.say(
        f"Then a garbled sound came from behind the old door -- a hush, a scrape, "
        f"and a half-swallowed word that sounded like a ghost trying to speak."
    )
    world.say(
        f"{child.id} froze. The message was so garbled that it could have meant a warning, "
        f"a secret, or just the wind."
    )


def warn(world: World, companion: Entity, child: Entity, problem: Problem, place: Place) -> None:
    child.memes["asked_help"] = child.memes.get("asked_help", 0.0) + 1
    world.say(
        f'{companion.id} took a breath and said, "Don\'t chase a mystery alone. '
        f'Let us listen again and solve it step by step."'
    )


def search(world: World, child: Entity, tool: Tool, place: Place) -> None:
    world.say(
        f"{child.id} held up {tool.label}, and the small light made the dust sparkle "
        f"like tiny stars."
    )
    if tool.reveals:
        world.say(
            f"Near the door, the light caught a loose note tucked into a crack."
        )
    else:
        world.say("The sound stayed confusing until they looked closer.")


def reveal(world: World, place: Place, problem: Problem, tool: Tool) -> None:
    child = world.get("child")
    child.memes["fear"] = max(0.0, _get_meme(child, "fear") - 1)
    world.say(
        f"The note was not a ghost at all. It was only a clue, and the garble had "
        f"come from rain tapping on a crooked radio hidden in the wall."
    )
    world.say(
        f"Madame had been right to stay calm: the spooky sound had a simple cause."
    )


def fix(world: World, child: Entity, companion: Entity, tool: Tool, place: Place) -> None:
    _set_meter(child, "clue_found", _get_meter(child, "clue_found") + 1)
    _set_meme(child, "bravery", _get_meme(child, "bravery") + 1)
    world.say(
        f'Together they used {tool.label} to follow the clue, and soon {child.id} '
        f'found the crooked radio and turned its knob until the static stopped.'
    )
    world.say(
        f"The house grew quiet in a friendly way, and the old dark place felt less like a ghost's room "
        f"and more like a house that had finally been understood."
    )


def ending(world: World, child: Entity, companion: Entity, place: Place) -> None:
    world.say(
        f"By the end, {child.id} was smiling, {companion.id} was smiling too, "
        f"and the only thing still eerie was the moonlight on the stairs."
    )


def tell(place: Place, problem: Problem, tool: Tool,
         child_name: str = "Nina", child_gender: str = "girl",
         companion_name: str = "Madame", companion_gender: str = "madame") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    world.add(Entity(id="hall", type="place", label=place.label))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["child"] = child
    world.facts["companion"] = companion

    opening(world, child, companion, place)
    world.para()
    garbled_message(world, child, problem)
    warn(world, companion, child, problem, place)
    search(world, child, tool, place)
    world.para()
    reveal(world, place, problem, tool)
    fix(world, child, companion, tool, place)
    ending(world, child, companion, place)
    world.facts["solved"] = _get_meter(child, "clue_found") >= THRESHOLD
    return world


PLACES = {
    "old_house": Place("old_house", "the old house on Lantern Lane", True, 2, "radio", "spooky", "a radio in the wall", {"ghost", "radio"}),
    "attic": Place("attic", "the attic above the stairs", True, 3, "window", "spooky", "a draft under the boards", {"ghost", "draft"}),
    "library": Place("library", "the quiet library basement", False, 1, "speaker", "still", "a speaker in the ceiling", {"echo"}),
}

PROBLEMS = {
    "radio": Problem("radio", "voice", "garbled", "a spooky sound", "a crooked radio", "listening carefully", {"ghost", "radio"}),
    "window": Problem("window", "wind", "garbled", "a spooky sound", "a drafty window", "looking for the breeze", {"ghost", "draft"}),
    "speaker": Problem("speaker", "voice", "garbled", "a strange echo", "a loose speaker", "checking the wires", {"echo"}),
}

TOOLS = {
    "lantern": Tool("lantern", "a little lantern", "shine light", gives_light=True, reveals=True, tags={"light"}),
    "notebook": Tool("notebook", "a small notebook", "write clues", reveals=True, tags={"clue"}),
    "radio": Tool("radio", "the radio dial", "listen for patterns", reveals=True, tags={"radio"}),
}

NAMES = ["Nina", "Lina", "Milo", "Ivy", "Theo", "June", "Eli", "Rose"]


@dataclass
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    child_name: str
    child_gender: str
    companion_name: str
    companion_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for pr_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if signal_risky(problem, place) and answerable(problem, tool, place):
                    out.append((pid, pr_id, tool_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story problem-solving tale for a young child that includes the words "garble" and "madame".',
        f"Tell a spooky but gentle story set in {f['place'].label} where a garbled sound turns out to have a simple explanation.",
        f"Write a child-friendly mystery story where {f['child'].id} and {f['companion'].id} solve a garbled message by staying calm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, comp, place, problem, tool = f["child"], f["companion"], f["place"], f["problem"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {comp.id}, who went into {place.label}. The story follows them as they listened to a strange clue and solved it together."),
        ("What made the child nervous?",
         f"{child.id} heard a garbled sound that seemed ghostly at first. It was confusing because it could have meant a warning or just the wind."),
        ("What did Madame tell the child to do?",
         f"Madame told {child.id} not to chase the mystery alone and to solve it step by step. That calm advice helped the child slow down and look for a real clue."),
    ]
    if f.get("solved"):
        qa.append((
            "What was the garbled sound really?",
            f"It was not a ghost at all. The sound came from a crooked radio and a loose clue hidden in the wall, so the mystery had a simple answer."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the mystery solved and the house feeling peaceful again. {child.id} and {comp.id} were still a little spooky-brave, but now they knew what the sound meant."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["problem"].tags) | set(f["tool"].tags)
    items = []
    for tag in ["ghost", "radio", "draft", "echo", "light", "clue"]:
        if tag in tags:
            if tag == "ghost":
                items.append(("What is a ghost story?", "A ghost story is a spooky story that may have a mystery, a surprise, or a pretend ghost in it. It is meant to feel eerie, but not too scary for a child."))
            elif tag == "radio":
                items.append(("What does a radio do?", "A radio can play voices, music, or static through a speaker. If something is wrong with it, the sound can get noisy or garbled."))
            elif tag == "draft":
                items.append(("What is a draft?", "A draft is moving air that can slip through a crack or window. It can make curtains flutter and can sound mysterious in a quiet room."))
            elif tag == "echo":
                items.append(("What is an echo?", "An echo is a sound that bounces and comes back to you. In a quiet place, it can make a voice sound strange or repeated."))
            elif tag == "light":
                items.append(("Why is a light useful in the dark?", "A light helps you see shapes, clues, and safe paths when a place is dim. It can make a spooky room easier to understand."))
            elif tag == "clue":
                items.append(("What is a clue?", "A clue is a small piece of information that helps solve a mystery. Clues can be sounds, notes, footprints, or anything that gives a hint."))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("old_house", "radio", "lantern", "Nina", "girl", "Madame", "madame"),
    StoryParams("attic", "window", "notebook", "Theo", "boy", "Madame", "madame"),
]


def explain_rejection(place: Place, problem: Problem, tool: Tool) -> str:
    if not signal_risky(problem, place):
        return "(No story: this place and problem do not make a spooky enough mystery.)"
    if not answerable(problem, tool, place):
        return "(No story: this tool would not help reveal the clue, so the mystery would stay unsolved.)"
    return "(No story: the combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "solved" if asp_outcome(params) == "solved" else "unsolved"


ASP_RULES = r"""
risky(P, X) :- haunted(P), source(X).
helpful(T, P) :- reveals(T), haunted(P).
solved :- risky(P, X), helpful(T, P), clue_found.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.haunted:
            lines.append(asp.fact("haunted", pid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("source", pr.source))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.reveals:
            lines.append(asp.fact("reveals", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
        asp.fact("clue_found", "yes"),
    ])
    model = asp.one_model(asp_program(extra, "#show solved/0."))
    return "solved" if asp.atoms(model, "solved") else "unsolved"


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        rc = 1
        print("MISMATCH in valid_combos:")
        print(" only in asp:", sorted(a - b))
        print(" only in python:", sorted(b - a))
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    try:
        p = CURATED[0]
        sample = generate(p)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world about garbled clues and Madame.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", default="Madame")
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
    if args.place and args.problem and args.tool:
        p, pr, t = PLACES[args.place], PROBLEMS[args.problem], TOOLS[args.tool]
        if not (signal_risky(pr, p) and answerable(pr, t, p)):
            raise StoryError(explain_rejection(p, pr, t))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    if name == args.companion:
        name = rng.choice([n for n in NAMES if n != args.companion])
    return StoryParams(place, problem, tool, name, gender, args.companion, "madame")


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.child_name, params.child_gender, params.companion_name, params.companion_gender)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
