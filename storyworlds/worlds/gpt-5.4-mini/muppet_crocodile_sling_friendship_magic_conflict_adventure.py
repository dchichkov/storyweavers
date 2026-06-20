#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/muppet_crocodile_sling_friendship_magic_conflict_adventure.py
==============================================================================================

A small adventure storyworld about a muppet, a crocodile, a sling, a little
bit of magic, and a friendship that has to survive a conflict before it can
shine again.

The world is built from a short causal simulation:
- a muppet and a crocodile explore a bright adventure trail,
- a sling is used to solve a practical problem,
- magic can help, but it can also tangle into conflict,
- the turn comes from choosing a calmer trick and a friendlier path,
- the ending proves what changed in the world state.

This script is standalone and uses only the Python standard library plus the
shared storyworld result containers.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"muppet", "girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    dark: bool = False
    adventurous: bool = True

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
    phrase: str
    helps: str
    can_magic: bool = False
    can_cast: bool = False

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
    label: str
    threatens: str
    heat: int = 1
    risky: bool = True

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
    def __init__(self, place: Place):
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

    def chars(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    f = world.get("friend")
    c = world.get("croc")
    if f.memes["hurt"] >= THRESHOLD and c.memes["stubborn"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            f.memes["conflict"] += 1
            c.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    f = world.get("friend")
    c = world.get("croc")
    if f.memes["trust"] >= THRESHOLD and c.memes["care"] >= THRESHOLD and ("soften",) not in world.fired:
        world.fired.add(("soften",))
        f.memes["peace"] += 1
        c.memes["peace"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("soften", "social", _r_soften)]


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


def sling_usable(tool: Tool, problem: Problem) -> bool:
    return tool.id == "sling" and problem.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def firepower(response: Response, problem: Problem, delay: int) -> bool:
    return response.power >= problem.heat + delay


def predict(world: World, problem: Problem, response: Response, delay: int) -> dict:
    sim = world.copy()
    problem_event(sim, sim.get("friend"), sim.get("croc"), problem, narrate=False)
    return {"conflict": sim.get("friend").memes["conflict"] >= THRESHOLD, "burn": not firepower(response, problem, delay)}


def setup(world: World, f: Entity, c: Entity, place: Place) -> None:
    world.say(
        f"On a bright adventure path, {f.id}, a little muppet, and {c.id}, a crocodile with a curious grin, set out together at {place.label}."
    )
    world.say(
        f"They were not just wandering; they were looking for a hidden stone bridge, a place where friendship and magic might matter."
    )


def needs_help(world: World, f: Entity, problem: Problem) -> None:
    world.say(
        f"Then they found the trouble: {problem.label} blocked the way, and the path beyond it looked too risky to cross."
    )
    world.say(
        f'{f.id} frowned. "We need a way across," {f.pronoun()} said, peering at the gap.'
    )


def tempt_magic(world: World, f: Entity, tool: Tool) -> None:
    f.memes["curiosity"] += 1
    world.say(
        f'{f.id} spotted {tool.phrase}. "I know!" {f.pronoun()} said. "We can use {tool.label} magic and swing over it!"'
    )
    world.say("For a moment, the idea felt bold and sparkling.")
    

def warn(world: World, c: Entity, f: Entity, problem: Problem) -> None:
    c.memes["care"] += 1
    pred = predict(world, problem, RESPONSES["guiding"], 0)
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'{c.id} lifted a webbed hand. "{f.id}, that gap is dangerous," {c.pronoun()} said. "If we rush, we will only make a bigger mess."'
    )


def problem_event(world: World, f: Entity, c: Entity, problem: Problem, narrate: bool = True) -> None:
    f.memes["hurt"] += 1
    c.memes["stubborn"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"The trouble jostled their friendship; for a breath, both of them felt cross and stuck."
        )


def use_magic(world: World, f: Entity, c: Entity, tool: Tool) -> None:
    f.memes["magic"] += 1
    c.memes["magic"] += 1
    world.say(
        f"{f.id} waved {tool.label}, and a tiny shimmer flashed across the path."
    )


def solve(world: World, f: Entity, c: Entity, tool: Tool, problem: Problem) -> None:
    f.memes["joy"] += 1
    c.memes["joy"] += 1
    world.say(
        f"Then {c.id} suggested a calmer trick: they could use the sling like a careful throw, not a wild swing."
    )
    world.say(
        f'{f.id} nodded, and together they aimed {tool.label} just so. The stone hopped cleanly past {problem.threatens}, marking a safe way forward.'
    )


def ending(world: World, f: Entity, c: Entity, tool: Tool, place: Place) -> None:
    f.memes["trust"] += 1
    c.memes["trust"] += 1
    world.say(
        f"In the end, the muppet and the crocodile crossed side by side, laughing as the sling settled back into {f.id}'s hands."
    )
    world.say(
        f"At {place.label}, their friendship felt stronger than the conflict, and the magic was gentle enough to keep the adventure bright."
    )


def tell(place: Place, tool: Tool, problem: Problem, response: Response,
         friend_name: str = "Milo", friend_type: str = "muppet",
         croc_name: str = "Cora", croc_type: str = "crocodile") -> World:
    w = World(place)
    f = w.add(Entity(friend_name, kind="character", type=friend_type, role="friend"))
    c = w.add(Entity(croc_name, kind="character", type=croc_type, role="helper"))
    sling = w.add(Entity("sling", kind="thing", type="tool", label=tool.label))
    w.add(Entity("bridge", kind="thing", type="place", label="the bridge"))
    f.memes["trust"] = 1
    c.memes["care"] = 0
    setup(w, f, c, place)
    w.para()
    needs_help(w, f, problem)
    tempt_magic(w, f, tool)
    warn(w, c, f, problem)
    w.para()
    if response.id == "guiding":
        problem_event(w, f, c, problem)
        use_magic(w, f, c, tool)
        solve(w, f, c, tool, problem)
        w.para()
        ending(w, f, c, tool, place)
        outcome = "healed"
    else:
        problem_event(w, f, c, problem)
        w.say(
            f"The magic flashed the wrong way, and the conflict grew sharper before they could fix it."
        )
        w.say(
            f"Even so, they kept hold of the sling and did not leave each other behind."
        )
        outcome = "strained"
    w.facts.update(friend=f, croc=c, tool=sling, place=place, problem=problem, response=response, outcome=outcome)
    return w


PLACES = {
    "riverbank": Place("riverbank", "the riverbank", dark=False, adventurous=True),
    "jungle": Place("jungle", "the jungle path", dark=True, adventurous=True),
    "cave": Place("cave", "the cave mouth", dark=True, adventurous=True),
}

TOOLS = {
    "sling": Tool("sling", "sling", "a sling", "to launch a little stone", can_magic=True, can_cast=True),
    "spark": Tool("spark", "magic spark", "a magic spark", "to light the way", can_magic=True, can_cast=True),
}

PROBLEMS = {
    "gap": Problem("gap", "a wide gap", "the far side of the trail", heat=1, risky=True),
    "mud": Problem("mud", "a sticky mud patch", "their boots", heat=1, risky=True),
}

RESPONSES = {
    "guiding": Response("guiding", 3, 2, "guided the sling stone across the gap", "could not guide the sling stone across the gap", "guided the sling stone across the gap"),
    "wild": Response("wild", 1, 0, "threw the sling wildly", "threw the sling wildly and missed everything", "threw the sling wildly"),
}

SENSE_MIN = 2

GIRL_NAMES = ["Milo", "Pip", "Nia", "Tia", "Rae"]
BOY_NAMES = ["Mik", "Tob", "Rio", "Sol", "Ben"]


@dataclass
@dataclass
class StoryParams:
    place: str
    tool: str
    problem: str
    response: str
    friend_name: str
    friend_type: str
    croc_name: str
    croc_type: str
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
    for p in PLACES:
        for t in TOOLS:
            for pr in PROBLEMS:
                if sling_usable(TOOLS[t], PROBLEMS[pr]):
                    out.append((p, t, pr))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "muppet", "crocodile", and "sling".',
        f"Tell a friendship story where {f['friend'].id} and {f['croc'].id} cross a risky place, but a sling and a little magic help them after a conflict.",
        f"Write a bright adventure with friendship, magic, and a calm resolution at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who is the story about?",
               f"It is about {f['friend'].id}, a muppet, and {f['croc'].id}, a crocodile, who travel together on an adventure."),
        QAItem("What problem did they face?",
               f"They found {f['problem'].label}, which blocked the trail and caused a conflict about what to do next. The path was risky, so they had to choose carefully."),
        QAItem("How did they fix it?",
               f"They used the sling carefully, with a little magic and calmer thinking. That choice turned the conflict into teamwork and let them cross safely."),
        QAItem("How did the story end?",
               f"It ended with friendship feeling stronger than the argument. The muppet and the crocodile crossed side by side and kept the adventure going."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a sling?",
               "A sling is a simple tool you can use to throw something carefully and farther away. In a story, it can be part of a clever adventure."),
        QAItem("What is magic in a story?",
               "Magic is a pretend force that can make surprising things happen. It is often used in adventures to solve problems in a special way."),
        QAItem("What is friendship?",
               "Friendship means people care about each other, listen, and try to help each other. Friends can disagree and still stay kind."),
        QAItem("What is a conflict?",
               "A conflict is a problem or disagreement that makes characters feel stuck. Stories often turn conflict into teamwork or understanding."),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("riverbank", "sling", "gap", "guiding", "Milo", "muppet", "Cora", "crocodile"),
    StoryParams("jungle", "sling", "mud", "guiding", "Pip", "muppet", "Mara", "crocodile"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a risky place, a sling, and a problem that a careful sling could actually help with.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: muppet, crocodile, sling, magic, friendship, conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing low-common-sense response.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError(explain_rejection())
    place, tool, problem = rng.choice(sorted(combos))
    response = args.response or "guiding"
    names = rng.sample(GIRL_NAMES + BOY_NAMES, 2)
    return StoryParams(place, tool, problem, response, names[0], "muppet", names[1], "crocodile")


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOOLS[params.tool], PROBLEMS[params.problem], RESPONSES[params.response], params.friend_name, params.friend_type, params.croc_name, params.croc_type)
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


ASP_RULES = r"""
risky_tool(T) :- tool(T), can_magic(T).
valid(P, T, Pr) :- place(P), tool(T), problem(Pr), risky(Pr), risky_tool(T).
conflict :- hurt(friend), stubborn(croc).
resolution :- care(croc), trust(friend).
outcome(healed) :- conflict, resolution.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t, obj in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if obj.can_magic:
            lines.append(asp.fact("can_magic", t))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
        lines.append(asp.fact("risky", pr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test story generation works.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        hdr = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
