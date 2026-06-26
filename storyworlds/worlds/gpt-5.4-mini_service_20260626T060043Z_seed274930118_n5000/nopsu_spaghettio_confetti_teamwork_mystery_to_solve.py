#!/usr/bin/env python3
"""
A small adventure storyworld about teamwork, a mystery to solve, and the
mysterious seed-words nopsu, spaghettio, and confetti.

The domain:
- A pair of child adventurers investigate a strange clue.
- They must cooperate to solve the mystery.
- Confetti appears as a celebratory mess and a clue carrier.
- "nopsu" and "spaghettio" are playful nonsense tokens that can appear on
  labels, notes, or snack-packages inside the world.

This file is self-contained and follows the storyworld contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old plaza"
    clue_place: str = "the fountain steps"
    atmosphere: str = "breezy"


@dataclass
class Mystery:
    label: str
    clue_word: str
    hidden_in: str
    reveals: str
    solved_by: str
    risky_place: str


@dataclass
class Tool:
    id: str
    label: str
    helps_with: set[str] = field(default_factory=set)
    carries: set[str] = field(default_factory=set)
    note: str = ""


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "plaza": Setting(place="the old plaza", clue_place="the fountain steps", atmosphere="windy"),
    "harbor": Setting(place="the lantern harbor", clue_place="the dock boards", atmosphere="salt-sweet"),
    "garden": Setting(place="the moon garden", clue_place="the stone bench", atmosphere="soft"),
}

MYSTERIES = {
    "lantern_note": Mystery(
        label="the lantern note",
        clue_word="nopsu",
        hidden_in="a ribbon bundle",
        reveals="the map to the secret arch",
        solved_by="reading the tucked-away message",
        risky_place="the harbor",
    ),
    "crumb_trail": Mystery(
        label="the crumb trail",
        clue_word="spaghettio",
        hidden_in="a snack tin",
        reveals="the path to the lost picnic",
        solved_by="following the crumbs and counting turns",
        risky_place="the plaza",
    ),
    "confetti_signal": Mystery(
        label="the confetti signal",
        clue_word="confetti",
        hidden_in="a paper cannon",
        reveals="who was sending the help signal",
        solved_by="matching the colored paper pieces",
        risky_place="the garden",
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="a short rope", helps_with={"climb", "carry"}, carries={"confetti"}),
    "lantern": Tool(id="lantern", label="a small lantern", helps_with={"find", "read"}, carries={"nopsu"}),
    "bag": Tool(id="bag", label="a striped bag", helps_with={"carry"}, carries={"spaghettio", "confetti"}),
    "magnifier": Tool(id="magnifier", label="a round magnifier", helps_with={"read", "spot"}, carries={"nopsu", "spaghettio"}),
}

HERO_NAMES = ["Mira", "Tobi", "Lina", "Arlo", "Nia", "Jasper", "Koa", "Elia"]
PARTNER_NAMES = ["Juno", "Pip", "Oli", "Mina", "Rae", "Tess", "Suri", "Zed"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    partner_name: str
    partner_type: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is reasonable when its clue word can appear in the setting and
% the selected tool can help with the solving action.
can_use(T, M) :- tool(T), mystery(M), helps(T, A), solves(M, A).
reasonable(S, M, T) :- setting(S), mystery(M), can_use(T, M), risky(M, S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
        lines.append(asp.fact("hidden_in", mid, m.hidden_in))
        lines.append(asp.fact("solves", mid, m.solved_by))
        lines.append(asp.fact("risky", mid, m.risky_place))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
        for c in sorted(t.carries):
            lines.append(asp.fact("carries", tid, c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_reasonable() -> set[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return set(asp.atoms(model, "reasonable"))


# ---------------------------------------------------------------------------
# Causal story simulation
# ---------------------------------------------------------------------------

def _story_char(e: Entity) -> str:
    return e.id

def _solve_clue(world: World, hero: Entity, partner: Entity, mystery: Mystery, tool: Tool) -> None:
    clue = world.get("clue")
    if clue.location != mystery.hidden_in:
        raise StoryError("the clue is not hidden where the mystery says it should be")
    world.say(
        f"{hero.id} and {partner.id} followed the hint together, and {hero.pronoun('subject').capitalize()} "
        f"lifted the {clue.label} with {tool.label}."
    )
    if mystery.clue_word in clue.phrase:
        world.say(
            f"Inside, they found the word {mystery.clue_word} tucked beside the note. "
            f"That was the key to {mystery.solved_by}."
        )
    else:
        world.say(
            f"Inside, they found a clue that matched the strange trail. "
            f"That was enough for {mystery.solved_by}."
        )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    partner.memes["joy"] = partner.memes.get("joy", 0) + 1
    world.facts["solved"] = True

def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str,
         partner_name: str, partner_type: str, tool: Tool) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="note",
        label="mystery clue",
        phrase=f"a clue marked with the word {mystery.clue_word}",
        location=mystery.hidden_in,
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.label,
        carried_by=hero.id,
    ))

    world.say(
        f"At {setting.place}, {hero.id} and {partner.id} were on a small adventure. "
        f"They had one goal: solve {mystery.label}."
    )
    world.say(
        f"The air was {setting.atmosphere}, and a strange sign led them toward {setting.clue_place}."
    )

    world.para()
    world.say(
        f"{hero.id} spotted something odd: {mystery.clue_word} was written on a scrap near the path."
    )
    world.say(
        f"{partner.id} guessed it was a clue, but they needed to work together and use {tool.label}."
    )
    if tool.id == "lantern":
        world.say("The lantern let them read the tiny marks in the shadows.")
    elif tool.id == "magnifier":
        world.say("The magnifier made the faint letters look bold enough to follow.")
    elif tool.id == "bag":
        world.say("The striped bag held the loose pieces without letting them blow away.")
    else:
        world.say("The rope kept the loose clue pieces together while they searched.")

    world.para()
    _solve_clue(world, hero, partner, mystery, tool)
    world.say(
        f"In the end, they brought the clue back into the light, and {mystery.label} was no longer a mystery."
    )

    world.facts.update(
        setting=setting,
        mystery=mystery,
        hero=hero,
        partner=partner,
        tool=tool,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        f'Write a short adventure story for a child about {f["hero"].id} and {f["partner"].id} solving {m.label}.',
        f'Write a teamwork story that includes the word "{m.clue_word}" and ends with the mystery being solved.',
        f'Tell a child-friendly adventure where two friends use {f["tool"].label} to uncover a secret clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who worked together to solve {mystery.label}?",
            answer=f"{hero.id} and {partner.id} worked together to solve {mystery.label}.",
        ),
        QAItem(
            question=f"What strange word did they notice during the adventure?",
            answer=f"They noticed the word {mystery.clue_word}.",
        ),
        QAItem(
            question=f"What did {tool.label} help them do?",
            answer=f"{tool.label.capitalize()} helped them search for the clue and uncover the hidden message.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"They solved the mystery and found {mystery.reveals}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something hard.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand right away, so you investigate it.",
        ),
        QAItem(
            question="Why do people use a lantern?",
            answer="People use a lantern to make a dark place brighter so they can see better.",
        ),
        QAItem(
            question="What is confetti?",
            answer="Confetti is tiny bits of paper that flutter in the air during a celebration.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation and resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            for tid, t in TOOLS.items():
                if m.clue_word in t.carries or "read" in t.helps_with or "find" in t.helps_with or "spot" in t.helps_with:
                    combos.append((sid, mid, tid))
    return combos


def explain_rejection(setting: str, mystery: str, tool: str) -> str:
    m = MYSTERIES[mystery]
    t = TOOLS[tool]
    return (
        f"(No story: {t.label} does not fit the kind of clue-solving this mystery needs. "
        f"Try a tool that can help with reading, spotting, finding, or carrying the clue word {m.clue_word}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about teamwork and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--partner-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting or args.mystery or args.tool:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.mystery is None or c[1] == args.mystery)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    m = MYSTERIES[mystery]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    partner_name = args.partner_name or rng.choice([n for n in PARTNER_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_name=partner_name,
        partner_type=partner_type,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        params.hero_name,
        params.hero_type,
        params.partner_name,
        params.partner_type,
        TOOLS[params.tool],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP / verification
# ---------------------------------------------------------------------------

def asp_reasonable_python() -> set[tuple[str, str, str]]:
    out = set()
    for s, m, t in valid_combos():
        mystery = MYSTERIES[m]
        tool = TOOLS[t]
        if mystery.clue_word in tool.carries or any(h in tool.helps_with for h in {"read", "find", "spot"}):
            out.add((s, m, t))
    return out


def asp_reasonable_clingo() -> set[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return set(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    py = asp_reasonable_python()
    cl = asp_reasonable_clingo()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo gates:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


# ---------------------------------------------------------------------------
# Trace / emit / main
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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
    StoryParams(setting="plaza", mystery="crumb_trail", hero_name="Mira", hero_type="girl", partner_name="Pip", partner_type="boy", tool="magnifier"),
    StoryParams(setting="harbor", mystery="lantern_note", hero_name="Tobi", hero_type="boy", partner_name="Rae", partner_type="girl", tool="lantern"),
    StoryParams(setting="garden", mystery="confetti_signal", hero_name="Lina", hero_type="girl", partner_name="Zed", partner_type="boy", tool="bag"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible combos:\n")
        for s, m, t in combos:
            print(f"  {s:8} {m:16} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
