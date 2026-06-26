#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/push_pap_puller_humor_kindness_dialogue_detective.py
================================================================================

A small detective-story world with humor, kindness, and dialogue.

Seed tale:
---
A kid detective finds a mysterious pap note shoved behind a desk. A stubborn
drawer will not open, so the detective uses a puller tool, asks kind questions,
and learns the helper had only pushed the pap aside to keep it safe. The clue
ends with a laugh, a thank-you, and the pap returned to the case folder.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Shared typed world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden: bool = False
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    cue: str = ""


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        other = World(self.setting)
        other.entities = dataclasses.replace(self.entities) if False else __import__("copy").deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "office": Setting(place="the office", indoor=True, affords={"push", "pull"}),
    "hall": Setting(place="the hallway", indoor=True, affords={"push", "pull"}),
    "archive": Setting(place="the archive", indoor=True, affords={"push", "pull"}),
}

CLUES = {
    "pap": Clue(
        id="pap",
        label="pap note",
        phrase="a small pap note with tidy corners",
        type="note",
        risk="lost",
        zone="behind the desk",
        keyword="pap",
        tags={"pap", "note", "paper"},
    ),
    "badge": Clue(
        id="badge",
        label="badge",
        phrase="a shiny badge",
        type="badge",
        risk="scratched",
        zone="under a chair",
        keyword="badge",
        tags={"badge", "metal"},
    ),
    "receipt": Clue(
        id="receipt",
        label="receipt",
        phrase="a folded receipt",
        type="receipt",
        risk="creased",
        zone="inside a drawer",
        keyword="receipt",
        tags={"paper", "receipt"},
    ),
}

TOOLS = {
    "puller": Tool(
        id="puller",
        label="puller",
        phrase="a small puller tool",
        helps={"pull"},
        cue="used to pull stuck things loose",
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        helps={"look"},
        cue="used to study clues closely",
    ),
}

NAMES = ["Mia", "Noah", "Ivy", "Ben", "Lena", "Jude", "Ada", "Theo"]
TYPES = ["girl", "boy"]
HELPER_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")


def predict(world: World, clue: Clue, tool: Tool) -> dict:
    sim = world.copy()
    c = sim.get(clue.id)
    t = sim.get(tool.id)
    c.hidden = True
    if tool.id == "puller":
        c.hidden = False
        t.meters["success"] = 1
    return {"found": not c.hidden, "tool_used": tool.id == "puller"}


def push_clue(world: World, detective: Entity, clue: Clue) -> None:
    clue_ent = world.get(clue.id)
    clue_ent.hidden = True
    detective.meters["curiosity"] = detective.meters.get("curiosity", 0) + 1
    detective.memes["puzzled"] = detective.memes.get("puzzled", 0) + 1
    world.say(
        f"{detective.id} noticed that {clue.phrase} had been pushed behind {world.setting.place.split()[-1]}."
    )


def use_tool(world: World, detective: Entity, tool: Tool, clue: Clue) -> None:
    tool_ent = world.get(tool.id)
    clue_ent = world.get(clue.id)
    if tool.id != "puller":
        world.say(f"{detective.id} tried {tool.label}, but it did not help much.")
        return
    clue_ent.hidden = False
    tool_ent.meters["success"] = 1
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(f"{detective.id} used the puller to gently pull the clue back into view.")


def dialogue_question(world: World, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.memes["kind"] = detective.memes.get("kind", 0) + 1
    world.say(
        f'"Did you mean to hide the {clue.label}?" {detective.id} asked. '
        f'"I just pushed it aside so it would not get bent," {helper.id} said.'
    )


def humorous_turn(world: World, detective: Entity) -> None:
    world.say(
        f"{detective.id} blinked at the stubborn drawer and said, "
        f'"This drawer is acting like a sleepy turtle."'
    )


def resolve(world: World, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1
    helper.memes["kind"] = helper.memes.get("kind", 0) + 1
    world.say(
        f'{helper.id} smiled and said, "Thank you for asking kindly." '
        f"{detective.id} put the {clue.label} back in the case folder, safe and flat."
    )


def tell(setting: Setting, clue: Clue, tool: Tool,
         detective_name: str = "Mia", detective_type: str = "girl",
         helper_name: str = "Noah", helper_type: str = "boy") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    clue_ent = world.add(Entity(id=clue.id, type=clue.type, label=clue.label, phrase=clue.phrase))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase))

    world.say(
        f"{detective.id} was a small detective who liked neat clues and fair questions."
    )
    world.say(
        f"{detective.id} carried {tool.phrase} and looked for {clue.phrase} in {setting.place}."
    )

    world.para()
    push_clue(world, detective, clue)
    humorous_turn(world, detective)
    dialogue_question(world, detective, helper, clue)

    world.para()
    use_tool(world, detective, tool, clue)
    resolve(world, detective, helper, clue)

    world.facts.update(
        detective=detective,
        helper=helper,
        clue=clue,
        tool=tool,
        setting=setting,
        found=not clue_ent.hidden,
        kind_dialogue=True,
        humor=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries and generation logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for tool_id, tool in TOOLS.items():
                if clue.keyword == "pap" and tool_id == "puller" and "pull" in setting.affords:
                    combos.append((place, clue_id, tool_id))
    return combos


@dataclass
class _Registry:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=HELPER_TYPES)
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
    reasonableness_gate(StoryParams(
        place=args.place or "office",
        clue=args.clue or "pap",
        tool=args.tool or "puller",
        detective_name="Mia",
        detective_type="girl",
        helper_name="Noah",
        helper_type="boy",
    ))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid detective story matches the requested options.")
    place, clue, tool = rng.choice(sorted(combos))
    clue_obj = CLUES[clue]
    detective_type = rng.choice(TYPES)
    helper_type = args.gender or rng.choice(HELPER_TYPES)
    detective_name = args.name or rng.choice(NAMES)
    helper_name = args.helper or rng.choice([n for n in NAMES if n != detective_name])
    return StoryParams(place, clue, tool, detective_name, detective_type, helper_name, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"]
    return [
        f'Write a short detective story for children that uses the word "{clue.keyword}".',
        f"Tell a kind, funny mystery about {f['detective'].id} and a puller tool in {world.setting.place}.",
        f"Make a child-friendly detective tale with dialogue, humor, and a clue called {clue.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    hel: Entity = f["helper"]
    clue: Clue = f["clue"]
    tool: Tool = f["tool"]
    place = world.setting.place
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer=f"It is a detective story with humor, kindness, and dialogue in {place}.",
        ),
        QAItem(
            question=f"What did {det.id} use to bring the clue back?",
            answer=f"{det.id} used the puller to gently pull the {clue.label} back into view.",
        ),
        QAItem(
            question=f"Why had the {clue.label} been moved?",
            answer=f"{hel.id} said it was pushed aside so it would not get bent or hurt.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why is it nice to ask questions kindly?",
            answer="Kind questions help people explain what happened without feeling scared or blamed.",
        ),
        QAItem(
            question="What does a puller do?",
            answer="A puller helps tug something loose or open when it is stuck.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        TOOLS[params.tool],
        params.detective_name,
        params.detective_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}): {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show solved/3.

valid(Place, Clue, Tool) :- place(Place), clue(Clue), tool(Tool),
    clue_keyword(Clue,pap), tool_id(Tool,puller), affords(Place,pull).

solved(Place, Clue, Tool) :- valid(Place, Clue, Tool),
    clue_keyword(Clue,pap), tool_id(Tool,puller), place(Place).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_keyword", clue_id, clue.keyword))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_id", tool_id, tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("office", "pap", "puller", "Mia", "girl", "Noah", "boy"),
    StoryParams("hall", "pap", "puller", "Ben", "boy", "Ivy", "girl"),
]


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
        print(asp_program("#show valid/3.\n#show solved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
