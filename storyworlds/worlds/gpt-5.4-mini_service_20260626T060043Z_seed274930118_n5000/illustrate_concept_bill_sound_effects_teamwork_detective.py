#!/usr/bin/env python3
"""
A small detective-story world about an illustrator, a concept board, and a bill
that can be solved only with teamwork and clue-like sound effects.

The seed words are woven into the premise:
- illustrate
- concept
- bill

The domain is a child-friendly detective tale: someone hears a strange sound,
the team investigates, and the ending reveals how cooperation helps pay or
deliver the bill without losing the important concept sketch.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str = "office"  # office | studio | street | library | kitchen
    has_echo: bool = False
    has_light: bool = False
    has_clock: bool = True


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    meaning: str
    leads_to: str
    intensity: int = 1


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        w = World(self.place)
        w.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "studio": Place("the little studio", kind="studio", has_echo=True, has_light=True),
    "office": Place("the downtown office", kind="office", has_echo=False, has_light=True),
    "library": Place("the library corner", kind="library", has_echo=False, has_light=True),
    "street": Place("the quiet street", kind="street", has_echo=False, has_light=False),
}

CLUES = {
    "drip": Clue(
        id="drip",
        label="drip, drip",
        sound="drip drip",
        meaning="a leaky pipe is making the floor slippery",
        leads_to="the back sink",
        intensity=1,
    ),
    "tap": Clue(
        id="tap",
        label="tap-tap",
        sound="tap tap",
        meaning="someone is knocking from the next room",
        leads_to="the hallway door",
        intensity=1,
    ),
    "rustle": Clue(
        id="rustle",
        label="rustle-rustle",
        sound="rustle rustle",
        meaning="papers are sliding across the desk",
        leads_to="the concept board",
        intensity=1,
    ),
    "clang": Clue(
        id="clang",
        label="clang!",
        sound="clang",
        meaning="a heavy sign has fallen near the front desk",
        leads_to="the front table",
        intensity=2,
    ),
}

TOOLS = {
    "notebook": Tool(id="notebook", label="a notebook", use="write clues in", helps_with={"clue", "plan"}),
    "flashlight": Tool(id="flashlight", label="a flashlight", use="shine under desks with", helps_with={"dark", "clue"}),
    "tape": Tool(id="tape", label="tape", use="pin the pages with", helps_with={"paper", "bill", "plan"}),
    "markers": Tool(id="markers", label="bright markers", use="draw the final picture with", helps_with={"illustrate", "concept"}),
}

HEROES = ["Mina", "Leo", "Iris", "Noah", "Zuri", "Theo"]
SIDEKICKS = ["Pip", "Momo", "Rae", "Finn", "Bea", "Jo"]

THEMES = [
    "illustrate a concept",
    "illustrate the clue map",
    "illustrate a bill plan",
    "illustrate the team board",
]


# ---------------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world about sound clues, teamwork, and a bill.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    clue = args.clue or rng.choice(list(CLUES))
    tool = args.tool or rng.choice(list(TOOLS))
    hero = args.hero or rng.choice(HEROES)
    sidekick = args.sidekick or rng.choice([x for x in SIDEKICKS if x != hero])
    if clue == "clang" and place == "street" and tool == "markers":
        pass
    return StoryParams(place=place, clue=clue, tool=tool, hero=hero, sidekick=sidekick)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def can_use_tool(tool: Tool, clue: Clue) -> bool:
    return "clue" in tool.helps_with or clue.id in tool.helps_with or clue.meaning.startswith("a ")


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="detective", label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="detective", label=params.sidekick))
    clue = world.add(Entity(id="clue", type="clue", label=CLUES[params.clue].label, phrase=CLUES[params.clue].meaning))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].use))

    world.facts.update(hero=hero, sidekick=sidekick, clue=clue, tool=tool, clue_def=CLUES[params.clue], tool_def=TOOLS[params.tool])
    world.facts["mystery"] = f"{hero.id} and {sidekick.id} must follow {clue.label} to protect the bill and the concept."
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    clue_def: Clue = f["clue_def"]
    tool_def: Tool = f["tool_def"]
    place = world.place.name

    world.say(
        f"{hero.id} was a small detective who loved to illustrate a concept board before every case."
    )
    world.say(
        f"{sidekick.id} liked teamwork and always carried {tool_def.label}."
    )
    world.say(
        f"One afternoon at {place}, a bill sat on the desk beside a half-finished concept sketch."
    )
    world.para()
    world.say(
        f"Then the team heard {clue_def.sound}, {clue_def.sound} from somewhere in the room."
    )
    world.say(
        f"{hero.id} wrote it down, because {clue_def.meaning}."
    )
    world.say(
        f"{sidekick.id} shone {tool_def.label} under the desk and pointed to {clue_def.leads_to}."
    )
    world.say(
        f"Together they followed the sound and found the missing envelope with the bill inside."
    )
    world.para()
    if can_use_tool(tool_def, clue_def):
        world.say(
            f"{hero.id} used {tool_def.label} to illustrate the clue map while {sidekick.id} taped the pages together."
        )
        world.say(
            f"Their teamwork made the answer clear, and the bill was paid before the office clock chimed twice."
        )
    else:
        world.say(
            f"{hero.id} still tried to illustrate the clue map, but the tool was not the best fit."
        )
        world.say(
            f"Luckily, {sidekick.id} helped anyway, and the team found a simple way to keep the bill safe until morning."
        )
    world.say(
        f"At the end, the concept board showed the whole case, and the little detectives smiled beside the solved bill."
    )

    world.facts["solved"] = True
    world.facts["sound"] = clue_def.sound
    world.facts["place_name"] = place


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    clue_def: Clue = f["clue_def"]
    tool_def: Tool = f["tool_def"]
    return [
        f'Write a detective story where {hero.id} and {sidekick.id} hear "{clue_def.sound}" and use {tool_def.label} to solve a bill problem.',
        f"Tell a child-friendly mystery that includes the words illustrate, concept, and bill, with teamwork and a sound clue.",
        f"Write a short story set in {world.place.name} where a team follows a sound effect and illustrates the final concept board.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    clue_def: Clue = f["clue_def"]
    tool_def: Tool = f["tool_def"]
    return [
        QAItem(
            question=f"What did {hero.id} and {sidekick.id} hear at the start of the mystery?",
            answer=f"They heard {clue_def.sound}, which sounded like a clue in the room.",
        ),
        QAItem(
            question=f"What did the team use to help solve the case?",
            answer=f"They used {tool_def.label} and teamwork to follow the clue.",
        ),
        QAItem(
            question=f"What important thing did the detectives keep safe?",
            answer="They kept the bill safe and finished the case without losing the concept sketch.",
        ),
        QAItem(
            question=f"What did {hero.id} illustrate at the end?",
            answer="They illustrated the clue map and the finished concept board so everyone could see how the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that imitate a noise, like tap-tap or clang!",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_def(C).
tool(T) :- tool_def(T).

teamwork(P,H,S) :- protagonist(H), sidekick(S), place(P).
solved_case(P,C,T) :- clue(C), tool(T), helpful(T), teamwork(P,_,_).

#show solved_case/3.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue_def", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_def", tid))
        if "clue" in tool.helps_with or "plan" in tool.helps_with or "illustrate" in tool.helps_with:
            lines.append(asp.fact("helpful", tid))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    from itertools import product
    program = asp_program()
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "solved_case"))
    python_set = set()
    for p, c, t in product(PLACES, CLUES, TOOLS):
        if "clue" in TOOLS[t].helps_with or "plan" in TOOLS[t].helps_with or "illustrate" in TOOLS[t].helps_with:
            python_set.add((p, c, t))
    if atoms == python_set:
        print(f"OK: ASP parity holds for {len(atoms)} solved_case facts.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only ASP:", sorted(atoms - python_set))
    print("only Python:", sorted(python_set - atoms))
    return 1


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print()
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if isinstance(v, Entity):
                continue
            print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


def dump_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="studio", clue="rustle", tool="markers", hero="Mina", sidekick="Pip"),
            StoryParams(place="office", clue="tap", tool="notebook", hero="Leo", sidekick="Rae"),
            StoryParams(place="library", clue="drip", tool="flashlight", hero="Iris", sidekick="Bea"),
            StoryParams(place="street", clue="clang", tool="tape", hero="Noah", sidekick="Finn"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            prng = random.Random(seed)
            try:
                params = resolve_params(args, prng)
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
        print(dump_json(samples))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.sidekick} at {p.place} ({p.clue}/{p.tool})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
