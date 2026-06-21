#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wrap_gerund_problem_solving_curiosity_bravery_tall.py
=====================================================================================

A small standalone storyworld with a tall-tale flavor: a curious child, a tricky
problem, a brave attempt, and a wrap-gerund solution that turns a dangerous
mess into a clever triumph.

The seed phrase "wrap-gerund" is represented in-world by a rope-wrap action
that helps solve the problem. Stories are generated from simulated world state,
not by swapping nouns into a frozen paragraph.
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
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    scene: str
    tall_sound: str
    dark_spot: str
    heighty_end: str
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
class Problem:
    id: str
    label: str
    clue: str
    risk: str
    makes_tangle: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tangled"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "lane" in world.entities:
            world.get("lane").meters["blocked"] += 1
        for c in world.characters():
            c.memes["alarm"] += 1
        out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def rope_valid(problem: Problem) -> bool:
    return problem.makes_tangle


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def fire_like_risk(problem: Problem) -> bool:
    return problem.makes_tangle


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= (2 + delay)


def predict_tangle(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(problem_id), narrate=False)
    return {
        "tangled": sim.get(problem_id).meters["tangled"] >= THRESHOLD,
        "blocked": sim.get("lane").meters["blocked"],
    }


def _do_problem(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["tangled"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Down in {place.scene}, where the air rang with {place.tall_sound}, "
        f"{hero.id} and {helper.id} made a grand little day of it."
    )
    world.say(
        f"Far off stood {place.dark_spot}, and every breeze there seemed to ask "
        f"for a question."
    )


def spark_curiosity(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id} squinted at the knot of trouble and said, "Well now, that '
        f'looks like a puzzle."'
    )
    world.say(f"{hero.pronoun().capitalize()} followed the clue of {problem.clue}.")


def warn(world: World, helper: Entity, hero: Entity, problem: Problem) -> None:
    pred = predict_tangle(world, "problem")
    helper.memes["bravery"] += 1
    world.facts["predicted_blocked"] = pred["blocked"]
    world.say(
        f'{helper.id} lifted a hand and warned, "{problem.risk}, and if it '
        f'keeps going, the lane will be blocked."'
    )


def brave_try(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'{hero.id} drew a long breath, squared {hero.pronoun("possessive")} '
        f'shoulders, and stepped right up to the mess.'
    )


def do_wrap(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    _do_problem(world, world.get("problem"))
    world.say(
        f"{tool.phrase} {tool.use}, and {hero.id} went {tool.id}-around the "
        f"trouble until it stood as neat as a bundle of fence posts."
    )
    world.say(
        f"The rope-wraping trick held the knot fast, and the danger had nowhere "
        f"else to go."
    )


def rescue(world: World, helper: Entity, response: Response) -> None:
    body = response.text
    world.get("problem").meters["tangled"] = 0.0
    world.get("lane").meters["blocked"] = 0.0
    world.say(f"{helper.id} came running and {body}.")
    world.say("The blocked lane opened up, and the whole place breathed easy again.")


def lesson(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.id} grinned like a wagon wheel in the sun and said, "
        f'"That is what I call brave thinking."'
    )
    world.say(
        f"{hero.id} puffed up with pride and nodded at the saved lane. The same "
        f"twisted trouble was now bound tight and tamed."
    )


def tell(place: Place, problem: Problem, tool: Tool, response: Response,
         hero_name: str = "Mara", hero_type: str = "girl",
         helper_name: str = "Uncle Hank", helper_type: str = "man",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="lane", type="path", label="the lane"))
    world.add(Entity(id="problem", type="problem", label=problem.label))
    set_scene(world, hero, helper, place)
    world.para()
    spark_curiosity(world, hero, problem)
    warn(world, helper, hero, problem)
    brave_try(world, hero, problem)
    world.para()
    do_wrap(world, hero, tool, problem)
    if is_contained(response, delay):
        rescue(world, helper, response)
        lesson(world, hero, helper, problem)
    else:
        world.say(
            f"{helper.id} tried to help, but the knot had already snatched the lane "
            f"too hard, and the whole contraption stayed jammed."
        )
        world.say(
            f"So the pair had to back up, unpick the mess by hand, and start over "
            f"with calmer minds."
        )
    world.facts.update(
        hero=hero, helper=helper, place=place, problem=problem, tool=tool,
        response=response, delay=delay, outcome="contained" if is_contained(response, delay) else "stuck"
    )
    return world


PLACES = {
    "prairie": Place(
        id="prairie",
        scene="the prairie road",
        tall_sound="wind and whistling grass",
        dark_spot="the bend beyond the cottonwood",
        heighty_end="far as a kite-string could reach",
        tags={"outdoors"},
    ),
    "harbor": Place(
        id="harbor",
        scene="the harbor walk",
        tall_sound="masts and gull-crying",
        dark_spot="the dock under the fog lamp",
        heighty_end="as long as a dockhand's yarn",
        tags={"outdoors"},
    ),
    "barn": Place(
        id="barn",
        scene="the big red barnyard",
        tall_sound="loose boards and sleepy cows",
        dark_spot="the hay loft stairs",
        heighty_end="up where rafters could tickle clouds",
        tags={"outdoors"},
    ),
}

PROBLEMS = {
    "net": Problem(
        id="net",
        label="a fisherman’s net",
        clue="the tangled rope and snarled loops",
        risk="That net can snare a wheel or a boot",
        makes_tangle=True,
        tags={"tangle"},
    ),
    "banner": Problem(
        id="banner",
        label="a parade banner",
        clue="the banner rope flapping in the wind",
        risk="That banner rope can twist around a post",
        makes_tangle=True,
        tags={"tangle"},
    ),
    "vine": Problem(
        id="vine",
        label="a wild vine",
        clue="the green coils climbing the rail",
        risk="That vine can latch onto the path",
        makes_tangle=True,
        tags={"tangle"},
    ),
}

TOOLS = {
    "wrap": Tool(
        id="wrap",
        label="a length of rope",
        phrase="the length of rope",
        use="could be wrapped around the trouble",
        tags={"wrap", "rope"},
    ),
    "lasso": Tool(
        id="lasso",
        label="a lasso",
        phrase="the lasso",
        use="could loop the knot tight",
        tags={"wrap", "rope"},
    ),
    "cloth": Tool(
        id="cloth",
        label="a strip of cloth",
        phrase="the strip of cloth",
        use="could wrap the snag from end to end",
        tags={"wrap", "cloth"},
    ),
}

RESPONSES = {
    "tighten": Response(
        id="tighten", sense=3, power=3,
        text="tightened the wrap until the snag held still",
        fail="tightened the wrap, but the knot was too wild to calm",
        qa_text="tightened the wrap until the snag held still",
    ),
    "pin": Response(
        id="pin", sense=3, power=2,
        text="pinned the trouble down with a quick, steady shove",
        fail="pinned at the trouble, but it sprang loose again",
        qa_text="pinned the trouble down with a quick, steady shove",
    ),
    "guess": Response(
        id="guess", sense=1, power=1,
        text="guessed at a fix and hoped for the best",
        fail="guessed at a fix, but hope was too small for that mess",
        qa_text="guessed at a fix and hoped for the best",
    ),
}


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    response: str
    hero_name: str = "Mara"
    hero_type: str = "girl"
    helper_name: str = "Uncle Hank"
    helper_type: str = "man"
    delay: int = 0
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


CURATED = [
    StoryParams(place="prairie", problem="net", tool="wrap", response="tighten", hero_name="Mara", helper_name="Uncle Hank"),
    StoryParams(place="harbor", problem="banner", tool="lasso", response="pin", hero_name="June", helper_name="Aunt Belle", helper_type="woman"),
    StoryParams(place="barn", problem="vine", tool="cloth", response="tighten", hero_name="Nell", helper_name="Uncle Hank", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for prob in PROBLEMS:
            for tool in TOOLS:
                if PROBLEMS[prob].makes_tangle and TOOL_OK(tool, prob):
                    out.append((p, prob, tool))
    return out


def TOOL_OK(tool_id: str, problem_id: str) -> bool:
    return "wrap" in TOOLS[tool_id].tags and PROBLEMS[problem_id].makes_tangle


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale wrap-gerund storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("Refusing a low-common-sense response.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    place_obj = PLACES[place]
    hero_name = args.name or rng.choice(["Mara", "June", "Nell", "Ivy", "Dot"])
    helper_name = args.helper_name or rng.choice(["Uncle Hank", "Aunt Belle", "Pa Sal", "Ma Dee"])
    return StoryParams(place=place, problem=problem, tool=tool, response=response,
                       hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("Refusing a low-common-sense response.")
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], RESPONSES[params.response],
                 hero_name=params.hero_name, hero_type=params.hero_type,
                 helper_name=params.helper_name, helper_type=params.helper_type,
                 delay=params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story with "{f["problem"].label}" and the word "wrap-gerund".',
        f"Tell a curious, brave problem-solving story where {f['hero'].id} uses a wrap action to save the lane.",
        f"Write a child-friendly tall tale about a tricky problem, a brave helper, and a wrap-around solution.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, place, problem, response = f["hero"], f["helper"], f["place"], f["problem"], f["response"]
    return [
        ("What was the problem?", f"It was {problem.label}, and it was snarling up the way in {place.scene}."),
        ("What did the hero do?", f"{hero.id} used a wrap-around fix and stayed brave enough to try."),
        ("How was the problem solved?", f"The helper {response.qa_text}, and the lane opened again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does wrapping do?", "Wrapping can hold things together, keep things neat, or stop a tangled mess from spreading."),
        ("Why is curiosity useful?", "Curiosity helps you notice clues and ask questions, which can lead to a clever fix."),
        ("Why is bravery useful?", "Bravery helps you try a hard thing when the answer is not obvious."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, T) :- place(P), problem(Pr), tool(T), makes_tangle(Pr), wrap_tool(T).
outcome(contained) :- response_ok(R), power(R, P), delay(D), P >= 2 + D.
outcome(stuck) :- not outcome(contained).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if pr.makes_tangle:
            lines.append(asp.fact("makes_tangle", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if "wrap" in TOOLS[tid].tags:
            lines.append(asp.fact("wrap_tool", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response_ok", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program(extra=asp.fact("delay", params.delay), show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between clingo and python valid_combos().")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        print(sample.story[:80])
    except Exception as e:
        rc = 1
        print(f"Smoke test failed: {e}")
    if asp_outcome(CURATED[0]) != ("contained" if is_contained(RESPONSES[CURATED[0].response], CURATED[0].delay) else "stuck"):
        rc = 1
        print("MISMATCH in outcome logic.")
    else:
        print("OK: outcome model matches.")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
