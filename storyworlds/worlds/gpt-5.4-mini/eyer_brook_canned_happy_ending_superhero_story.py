#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/eyer_brook_canned_happy_ending_superhero_story.py
==================================================================================

A small standalone storyworld for a superhero-style happy-ending tale built from
the seed words: eyer, brook, canned.

Premise
-------
Two kid superheroes, Eyer and Brook, are helping at a canned food drive when a
stolen bundle of cans rolls into a brook. The kids act fast, use a simple rescue
plan, and end the day with the cans saved, the helper safe, and the town cheering.

This world keeps the simulation tiny and classical:
- typed entities with physical meters and emotional memes
- a forward rule engine that mutates the world state
- a reasonableness gate and inline ASP twin
- generated stories, grounded QA, and world-knowledge QA from state, not from text

It supports the standard Storyweavers CLI:
    -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

# Import eagerly from the shared results module, robustly when run directly.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    base: str
    name: str
    team: str
    mission: str
    ending: str


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    risk: str
    can_fall: bool = True
    can_wet: bool = True


@dataclass
class RescueTool:
    id: str
    label: str
    phrase: str
    power: int
    method: str


@dataclass
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
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
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


def _r_worry(world: World) -> list[str]:
    out = []
    if world.get("brook").meters["wet"] >= THRESHOLD and world.get("cans").meters["scattered"] >= THRESHOLD:
        sig = ("worry",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("eyer").memes["alarm"] += 1
        world.get("brook").memes["alarm"] += 1
        out.append("The sight made both heroes spring into action.")
    return out


def _r_cheer(world: World) -> list[str]:
    out = []
    if world.get("cans").meters["saved"] >= THRESHOLD and world.get("helper").meters["safe"] >= THRESHOLD:
        sig = ("cheer",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("town").memes["joy"] += 1
        out.append("The crowd cheered as the last can was stacked safe.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("cheer", _r_cheer)]


THEMES = {
    "superhero": Theme(
        "superhero",
        "a bright little city square",
        "The town square had a folding table, red capes, and a sign that said canned food for neighbors.",
        "superheroes",
        "the rescue team",
        "save the falling cans",
        "a happy ending"),
}

HAZARDS = {
    "cans": Hazard("cans", "the cans", "a stack of canned soup and beans", "they can roll away"),
}

TOOLS = {
    "net": RescueTool("net", "catch net", "a strong catch net", 3, "scooped"),
    "rope": RescueTool("rope", "soft rope", "a soft rope", 2, "guided"),
    "board": RescueTool("board", "wide board", "a wide board", 4, "bridged"),
}

NAMES = ["Eyer", "Brook", "Milo", "Nina", "Pia", "Jude", "Ari", "Lena"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("superhero", "cans", tool_id) for tool_id in TOOLS]


@dataclass
class StoryParams:
    theme: str
    hazard: str
    tool: str
    eyer: str
    brook: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero-style happy-ending story world built from eyer, brook, and canned."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--eyer")
    ap.add_argument("--brook")
    ap.add_argument("--helper", choices=["girl", "boy", "adult"])
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


def reasonableness_gate(hazard: Hazard, tool: RescueTool) -> bool:
    return hazard.can_fall and tool.power >= 2


def explain_rejection(hazard: Hazard, tool: RescueTool) -> str:
    return f"(No story: {tool.label} is not a good enough rescue for {hazard.phrase}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.tool:
        if not reasonableness_gate(HAZARDS[args.hazard], TOOLS[args.tool]):
            raise StoryError(explain_rejection(HAZARDS[args.hazard], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, hazard, tool = rng.choice(combos)
    return StoryParams(
        theme=theme,
        hazard=hazard,
        tool=tool,
        eyer=args.eyer or "Eyer",
        brook=args.brook or "Brook",
        helper=args.helper or "adult",
    )


def tell(params: StoryParams) -> World:
    world = World()
    theme = THEMES[params.theme]
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]

    eyer = world.add(Entity(params.eyer, kind="character", type="girl", role="hero", traits=["brave"]))
    brook = world.add(Entity(params.brook, kind="character", type="boy", role="hero", traits=["quick"]))
    helper = world.add(Entity("helper", kind="character", type=params.helper, role="helper", label="Captain Bright"))
    town = world.add(Entity("town", kind="place", type="town", label="the town"))
    cans = world.add(Entity("cans", kind="thing", type="thing", label=hazard.label))
    brooklet = world.add(Entity("brook", kind="thing", type="water", label="the brook"))

    world.say(
        f"On a sunny afternoon, {eyer.id} and {brook.id} wore tiny capes in {theme.scene}. "
        f"{theme.base}"
    )
    world.say(
        f'They were the {theme.team} everyone called when a small problem needed a big brave heart. '
        f'That day, their mission was to {theme.mission}.'
    )

    world.para()
    world.say(
        f"Then a truck bumped the table, and {hazard.phrase} rolled toward {brooklet.label}."
    )
    cans.meters["scattered"] += 1
    brooklet.meters["wet"] += 1
    eyer.memes["alarm"] += 1
    brook.memes["alarm"] += 1
    world.say(
        f'"{eyer.id}, the cans!" {brook.id} shouted. "We can still catch them!"'
    )

    world.para()
    world.say(
        f"{eyer.id} grabbed {tool.phrase}, and {brook.id} helped guide the rolling stack back to dry ground. "
        f"Together they {tool.method} the cans before they slipped away."
    )
    cans.meters["saved"] += 1
    helper.meters["safe"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{helper.label_word.capitalize()} smiled and lifted the rescued cans onto the table again. "
        f"The crowd clapped, the sign stayed up, and the food drive kept going."
    )
    world.say(
        f"By evening, {eyer.id} and {brook.id} were still in their capes, standing beside a neat pile of canned soup. "
        f"The town had what it needed, and the heroes went home proud and happy."
    )

    world.facts.update(
        theme=theme,
        hazard=hazard,
        tool=tool,
        eyer=eyer,
        brook=brook,
        helper=helper,
        cans=cans,
        outcome="happy",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a superhero story for a young child that includes the words eyer, brook, and canned, and ends happily.",
        f"Tell a brave rescue story where {f['eyer'].id} and {f['brook'].id} save canned food from the brook and everyone cheers.",
        "Write a short happy-ending superhero adventure about helping with canned food before it gets lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Who are the story's heroes?",
            f"The heroes are {world.facts['eyer'].id} and {world.facts['brook'].id}. They worked together like a tiny superhero team."
        ),
        QAItem(
            "What happened to the canned food?",
            "It rolled toward the brook, but the heroes caught it before it was lost. That kept the food safe for the town."
        ),
        QAItem(
            "How did the story end?",
            "It ended happily. The cans were saved, the helper was safe, and everyone in town cheered."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a brook?",
            "A brook is a small stream of moving water. Water can make paper and food packages wet if they fall in."
        ),
        QAItem(
            "What does canned mean?",
            "Canned food comes in a metal can. The can helps keep food sealed and ready to store."
        ),
        QAItem(
            "What should heroes do when something small is in danger?",
            "They should act quickly, stay calm, and work together. A good plan can turn a scary moment into a safe ending."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("superhero", "cans", "net", "Eyer", "Brook", "adult"),
    StoryParams("superhero", "cans", "rope", "Eyer", "Brook", "adult"),
    StoryParams("superhero", "cans", "board", "Eyer", "Brook", "adult"),
]


ASP_RULES = r"""
valid(T, H, Tool) :- theme(T), hazard(H), rescue_tool(Tool).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for tool_id in TOOLS:
        lines.append(asp.fact("rescue_tool", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        print("MISMATCH: ASP gate differs from Python.")
        rc = 1
    # Smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible superhero combos:")
        for t in asp_valid_combos():
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.eyer} & {p.brook} save {p.hazard} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
