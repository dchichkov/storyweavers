#!/usr/bin/env python3
"""
A small pirate-tale storyworld: a timid deckhand learns brave jabbering and
rhyming with a tool that helps the crew solve a problem.

Premise:
- A young pirate wants to use a special tool.
- The captain worries the deckhand is too shy to speak up.
- A sea riddle can only be solved by brave jabber plus a fitting rhyme.

Turn:
- The deckhand blurts out a tangled jabber, then shapes it into a rhyme.
- That brave verse unlocks the tool's use.

Resolution:
- The crew repairs the ship, and the deckhand is praised for bravery and rhyme.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "deckhand", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the ship"
    affable: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    requires: str
    helps_with: str
    saves: str


@dataclass
class StoryParams:
    place: str
    tool: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": Setting(place="the ship"),
    "harbor": Setting(place="the harbor"),
    "island": Setting(place="the island"),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a sturdy rope",
        use="tie the loose sail",
        requires="bravery",
        helps_with="the mast",
        saves="the ship from drifting",
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        use="light the dark hold",
        requires="rhyme",
        helps_with="the map",
        saves="the crew from getting lost",
    ),
    "hook": Tool(
        id="hook",
        label="hook",
        phrase="a shiny hook",
        use="lift the trapped chest",
        requires="bravery",
        helps_with="the chest",
        saves="the crew from the storm",
    ),
}

HERO_NAMES = ["Finn", "Mara", "Pip", "Nell", "Jory", "Tess"]
TRAITS = ["bold", "curious", "small", "cheerful", "shy"]


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def reasonableness_gate(tool: Tool) -> None:
    if tool.requires not in {"bravery", "rhyme"}:
        raise StoryError("This pirate tale only supports tools that call for bravery or rhyme.")


def tell(setting: Setting, tool: Tool, hero_name: str, hero_type: str, captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        meters={"skill": 0.0, "tool_trust": 0.0},
        memes={"bravery": 0.0, "rhyme": 0.0, "fear": 1.0},
    ))
    captain = world.add(Entity(
        id="Captain", kind="character", type=captain_type, label="the captain",
        meters={"worry": 0.0}, memes={"trust": 0.0},
    ))
    tool_ent = world.add(Entity(
        id=tool.id, kind="thing", type="tool", label=tool.label,
        phrase=tool.phrase, owner=hero.id, caretaker=captain.id,
    ))

    # Act 1: setup
    world.say(
        f"On {setting.place}, {hero.id} was a little {hero_type} pirate who loved adventure."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept staring at {tool_ent.phrase}, wanting to "
        f"{tool.use}, but {captain.label} worried {hero.pronoun('possessive')} voice was too quiet."
    )

    # Act 2: tension
    world.para()
    world.say(
        f"One gray tide, the crew found a jammed chest and a torn sail, and the ship began to wobble."
    )
    world.say(
        f"{captain.label} said they needed {tool.label} used the right way, and that meant {tool.requires}."
    )
    if tool.requires == "bravery":
        hero.memes["fear"] += 1.0
        world.say(
            f"{hero.id} tried to speak, but the words came out in a nervous jabber, all tangled like seaweed."
        )
    else:
        hero.memes["fear"] += 0.5
        world.say(
            f"{hero.id} wanted to answer, but could only mutter a little jabber until a rhyme came to mind."
        )

    # Act 3: turn and resolution
    world.para()
    hero.memes["bravery"] += 1.0
    hero.meters["skill"] += 1.0
    hero.memes["rhyme"] += 1.0
    hero.meters["tool_trust"] += 1.0
    world.say(
        f"Then {hero.id} took a breath and turned the jabber into a brave rhyme: "
        f'"A rope to the mast, a lift that will last!"'
        if tool.id == "rope" else
        f"Then {hero.id} took a breath and turned the jabber into a brave rhyme: "
        f'"A lantern aglow will show what I know!"'
        if tool.id == "lantern" else
        f"Then {hero.id} took a breath and turned the jabber into a brave rhyme: "
        f'"A hook to the chest will do the rest!"'
    )
    world.say(
        f"The crew cheered, and {hero.id} used {tool.label} to {tool.use}, which {tool.saves}."
    )
    captain.memes["trust"] += 1.0
    world.say(
        f"At the end, {captain.label} smiled at {hero.id}: brave speech and a tidy rhyme had saved the day."
    )

    world.facts.update(hero=hero, captain=captain, tool=tool, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tool = f["tool"]
    return [
        f'Write a short pirate tale for a young child that includes "{tool.label}", "jabber", and "rhyme".',
        f"Tell a story where {hero.id} must be brave enough to speak up and use {tool.phrase} on a ship.",
        f"Create a gentle pirate adventure where a shy deckhand turns jabber into a rhyme to help the crew.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    tool = f["tool"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who is the pirate story about at {place}?",
            answer=f"It is about a little {hero.type} pirate named {hero.id} who learns to be brave."
        ),
        QAItem(
            question=f"What did {hero.id} first say before the brave rhyme?",
            answer="At first, the words came out as a nervous jabber, all tangled and shy."
        ),
        QAItem(
            question=f"What helped {hero.id} save the day?",
            answer=f"{tool.phrase} helped {hero.id} {tool.use}, and that {tool.saves}."
        ),
        QAItem(
            question=f"Why was {captain.label} worried?",
            answer=f"{captain.label} worried because the crew needed {tool.label} used the right way, and that called for bravery."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} grew braver, spoke in rhyme, and earned {captain.label}'s trust."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tool = world.facts["tool"]
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels afraid but still does the right thing."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like boat and coat."
        ),
        QAItem(
            question="What is a tool?",
            answer="A tool is something you use to help do a job, like tying, lifting, or lighting."
        ),
        QAItem(
            question=f"What is {tool.label} for?",
            answer=f"{tool.phrase} is used to help the crew with {tool.helps_with}."
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero_brave(H) :- brave(H), not shy(H).
can_use_tool(H, T) :- hero_brave(H), tool(T), requires(T, bravery).
can_use_tool(H, T) :- rhyme_ready(H), tool(T), requires(T, rhyme).
story_ok(P, T) :- place(P), tool(T), can_use_tool(hero, T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setname", pid, setting.place))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("requires", tid, tool.requires))
    lines.append(asp.fact("brave", "hero"))
    lines.append(asp.fact("rhyme_ready", "hero"))
    lines.append(asp.fact("shy", "captain"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    asp_set = set(asp.atoms(model, "story_ok"))

    py_set = set()
    for pid in SETTINGS:
        for tid, tool in TOOLS.items():
            if tool.requires in {"bravery", "rhyme"}:
                py_set.add((pid, tid))

    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_tools() -> list[str]:
    return [tid for tid, tool in TOOLS.items() if tool.requires in {"bravery", "rhyme"}]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about jabber, bravery, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captain-type", choices=["captain", "pirate"])
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
    tool_id = args.tool or rng.choice(valid_tools())
    if tool_id not in TOOLS:
        raise StoryError("Unknown tool.")
    tool = TOOLS[tool_id]
    if tool.requires not in {"bravery", "rhyme"}:
        raise StoryError("This storyworld only supports bravery- or rhyme-based tools.")
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    captain_type = args.captain_type or "captain"
    return StoryParams(place=place, tool=tool_id, hero_name=name, hero_type=hero_type, captain_type=captain_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_type,
        params.captain_type,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="ship", tool="rope", hero_name="Pip", hero_type="boy", captain_type="captain"),
    StoryParams(place="harbor", tool="lantern", hero_name="Mara", hero_type="girl", captain_type="pirate"),
    StoryParams(place="island", tool="hook", hero_name="Nell", hero_type="girl", captain_type="captain"),
]


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, tool in combos:
            print(f"  {place:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
