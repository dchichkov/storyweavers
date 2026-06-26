#!/usr/bin/env python3
"""
storyworlds/worlds/kneel_problem_solving_adventure.py
======================================================

A small adventure storyworld about a young explorer who faces a tricky obstacle,
kneels to look closely, and solves the problem with careful thinking.

The world is intentionally compact:
- one hero and one helper
- one place
- one problem
- one useful tool or clue
- one resolution that changes the world state

The story engine keeps the tale state-driven instead of swapping nouns in a
frozen paragraph. The hero's physical actions (meters) and emotions (memes)
drive the narration.

Features:
- kneel as an important physical action
- problem solving as the central turn
- adventure-style setting and tone
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "explorer-girl"}
        male = {"boy", "father", "dad", "man", "explorer-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    atmosphere: str
    allows: set[str] = field(default_factory=set)
    low_spot: bool = False


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    clue: str
    obstacle: str
    solved_by: str
    requires_kneel: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "forest": Place(
        id="forest",
        label="the forest path",
        atmosphere="The trees made a green roof overhead, and the path curved between mossy stones.",
        allows={"bridge", "gate", "trail"},
        low_spot=True,
    ),
    "cave": Place(
        id="cave",
        label="the cave tunnel",
        atmosphere="The cave was cool and echoey, with a low tunnel and shiny walls.",
        allows={"gate", "dripstone", "tunnel"},
        low_spot=True,
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor dock",
        atmosphere="The harbor smelled like salt and tar, and ropes clicked softly against wood.",
        allows={"rope", "crate", "gate"},
        low_spot=False,
    ),
    "ruins": Place(
        id="ruins",
        label="the old ruins",
        atmosphere="Broken stone arches stood in the sun, and a narrow way slipped between them.",
        allows={"gate", "arch", "trail"},
        low_spot=True,
    ),
}

PROBLEMS = {
    "stuck_gate": Problem(
        id="stuck_gate",
        label="a stuck gate",
        verb="open the gate",
        clue="a bent latch",
        obstacle="the latch would not lift",
        solved_by="straightening the latch",
        requires_kneel=True,
        tags={"metal", "careful", "puzzle"},
    ),
    "broken_bridge": Problem(
        id="broken_bridge",
        label="a broken bridge",
        verb="cross the bridge",
        clue="a loose plank",
        obstacle="one plank had slipped down",
        solved_by="sliding the plank back into place",
        requires_kneel=True,
        tags={"wood", "balance", "puzzle"},
    ),
    "lost_map": Problem(
        id="lost_map",
        label="a lost map",
        verb="find the map",
        clue="a scrap of paper",
        obstacle="the map had fallen under a crate",
        solved_by="reaching under the crate and pulling it out",
        requires_kneel=True,
        tags={"paper", "search", "puzzle"},
    ),
    "jammed_rope": Problem(
        id="jammed_rope",
        label="a jammed rope",
        verb="loosen the rope",
        clue="a twisted knot",
        obstacle="the knot was tight and hard to see",
        solved_by="working the knot apart",
        requires_kneel=False,
        tags={"rope", "hands", "puzzle"},
    ),
}

TOOLS = {
    "stick": Tool(
        id="stick",
        label="a long stick",
        phrase="a long stick with a smooth tip",
        use="reach things",
        tags={"wood", "reach"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern that glowed warm and gold",
        use="see in the dark",
        tags={"light", "search"},
    ),
    "string": Tool(
        id="string",
        label="a coil of string",
        phrase="a coil of string wound neatly in a pocket",
        use="tie things together",
        tags={"rope", "repair"},
    ),
    "gloves": Tool(
        id="gloves",
        label="soft gloves",
        phrase="soft gloves with grippy palms",
        use="hold rough things",
        tags={"hands", "careful"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ruby", "Ivy", "Tia"]
BOY_NAMES = ["Owen", "Finn", "Jasper", "Milo", "Theo", "Arlo"]
TRAITS = ["brave", "curious", "patient", "clever", "gentle", "lively"]


def compatible(place: Place, problem: Problem, tool: Tool) -> bool:
    if problem.id == "broken_bridge" and place.id not in {"forest", "ruins"}:
        return False
    if problem.id == "lost_map" and place.id not in {"cave", "harbor"}:
        return False
    if problem.id == "stuck_gate" and place.id not in {"ruins", "forest", "harbor"}:
        return False
    if problem.id == "jammed_rope" and place.id not in {"harbor", "cave"}:
        return False
    if problem.id == "broken_bridge" and "wood" not in tool.tags:
        return False
    if problem.id == "stuck_gate" and "careful" not in tool.tags and "repair" not in tool.tags:
        return False
    if problem.id == "lost_map" and "search" not in tool.tags and "light" not in tool.tags:
        return False
    if problem.id == "jammed_rope" and "rope" not in tool.tags and "repair" not in tool.tags:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for pr in PROBLEMS.values():
            for t in TOOLS.values():
                if compatible(p, pr, t):
                    out.append((p.id, pr.id, t.id))
    return out


def reason_invalid(place: Place, problem: Problem, tool: Tool) -> str:
    if not compatible(place, problem, tool):
        return (
            f"(No story: {tool.label} does not fit this kind of problem at {place.label}. "
            f"The adventure needs a tool that can honestly help with {problem.label}.)"
        )
    return "(No story: the requested options do not form a valid adventure.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.id))
        for tg in sorted(pr.tags):
            lines.append(asp.fact("problem_tag", pr.id, tg))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tool_tag", t.id, tg))
    for pid, place in PLACES.items():
        for pr in PROBLEMS:
            if compatible(place, PROBLEMS[pr], next(iter(TOOLS.values()))):
                pass
    for pid, place in PLACES.items():
        for pr in PROBLEMS.values():
            if pr.id in {"broken_bridge", "stuck_gate", "lost_map", "jammed_rope"}:
                lines.append(asp.fact("fits_place", pid, pr.id))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,PR,T) :- place(P), problem(PR), tool(T), fit(P,PR), help(T,PR).
fit(P,"broken_bridge") :- P="forest"; P="ruins".
fit(P,"lost_map") :- P="cave"; P="harbor".
fit(P,"stuck_gate") :- P="forest"; P="harbor"; P="ruins".
fit(P,"jammed_rope") :- P="cave"; P="harbor".
help("stick","broken_bridge").
help("lantern","lost_map").
help("string","stuck_gate").
help("gloves","stuck_gate").
help("string","jammed_rope").
help("gloves","jammed_rope").
help("stick","stuck_gate").
help("lantern","stuck_gate").
help("lantern","broken_bridge").
help("gloves","broken_bridge").
help("stick","lost_map").
help("gloves","lost_map").
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure about kneeling to solve a problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["sister", "brother", "friend", "parent"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place and args.problem and args.tool:
        if not compatible(PLACES[args.place], PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError(reason_invalid(PLACES[args.place], PROBLEMS[args.problem], TOOLS[args.tool]))
    choices = [c for c in combos
               if (args.place is None or c[0] == args.place)
               and (args.problem is None or c[1] == args.problem)
               and (args.tool is None or c[2] == args.tool)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["sister", "brother", "friend", "parent"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def kneel_action(world: World, hero: Entity) -> None:
    hero.meters["kneel"] = hero.meters.get("kneel", 0) + 1
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    world.say(f"{hero.id} knelt down to look closely.")


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type="parent" if params.helper == "parent" else "friend"))
    problem = PROBLEMS[params.problem]
    tool = world.add(Entity(id=tool_id := params.tool, kind="thing", type="tool", label=TOOLS[tool_id].label, phrase=TOOLS[tool_id].phrase, owner=hero.id))
    hero.memes["curiosity"] = 1
    hero.memes["resolve"] = 0
    hero.meters["walk"] = 1
    hero.meters["kneel"] = 0
    world.say(f"{hero.id} was a {params.trait} young explorer on {world.place.label}.")
    world.say(world.place.atmosphere)
    world.say(f"{hero.id} carried {tool.phrase} and went with {params.helper} along the way.")
    world.para()
    world.say(f"Then they found {problem.label}. {problem.obstacle.capitalize()}.")
    world.say(f"{hero.id} wanted to {problem.verb}, but the problem would not budge.")
    world.say(f"{params.helper.capitalize()} pointed at {problem.clue} and said, 'Let's look closer.'")
    kneel_action(world, hero)
    hero.memes["fear"] = 1 if problem.requires_kneel else 0
    world.say(f"{hero.id} used {tool.label} to solve it by {problem.solved_by}.")
    hero.memes["resolve"] = 1
    hero.memes["joy"] = 1
    world.para()
    world.say(f"At last, the way opened.")
    if problem.id == "broken_bridge":
        world.say(f"They crossed safely, and the bridge stayed steady behind them.")
    elif problem.id == "lost_map":
        world.say(f"The map showed the hidden path, and the two explorers followed it forward.")
    elif problem.id == "stuck_gate":
        world.say(f"The gate swung open with a soft creak, and fresh air rushed through.")
    else:
        world.say(f"The rope loosened, and the little crew could pull the boat free.")
    world.facts.update(hero=hero, helper=helper, problem=problem, tool=tool, place=world.place)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    tool: Entity = f["tool"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the adventure story about?",
            answer=f"It was about {hero.id}, a {('girl' if hero.type == 'girl' else 'boy')} explorer who traveled through {place.label}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} find?",
            answer=f"{hero.id} found {problem.label}, and the obstacle was that {problem.obstacle}.",
        ),
        QAItem(
            question=f"What did {hero.id} do before solving the problem?",
            answer=f"{hero.id} knelt down to look closely and then used {tool.label} to help solve it.",
        ),
        QAItem(
            question=f"Who went along with {hero.id}?",
            answer=f"{helper.id} went along too and helped by pointing out the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do explorers kneel down sometimes?",
            answer="Explorers kneel down so they can look closely at small clues, reach under low places, or work carefully on a problem.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps you solve a puzzle or figure out what to do next.",
        ),
        QAItem(
            question="Why is careful thinking useful on an adventure?",
            answer="Careful thinking helps you notice details, choose the right tool, and find a safe way forward.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    place: Place = f["place"]
    return [
        f"Write a short adventure story for a young child about {hero.id} at {place.label} who has to kneel to solve {problem.label}.",
        f"Tell a gentle adventure where a brave child notices a clue, kneels down, and fixes {problem.label} with help.",
        f"Write a problem-solving story that includes the word 'kneel' and ends with the path opening again.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    generate_story(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="forest", problem="broken_bridge", tool="stick", name="Mina", gender="girl", helper="friend", trait="brave"),
    StoryParams(place="cave", problem="lost_map", tool="lantern", name="Owen", gender="boy", helper="sister", trait="curious"),
    StoryParams(place="ruins", problem="stuck_gate", tool="gloves", name="Lena", gender="girl", helper="parent", trait="patient"),
    StoryParams(place="harbor", problem="jammed_rope", tool="string", name="Finn", gender="boy", helper="friend", trait="clever"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.problem} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
