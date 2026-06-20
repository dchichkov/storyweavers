#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/factor_thirty_twist_problem_solving_mystery_to.py
==================================================================================

A small standalone storyworld for a child-friendly ghost-story mystery.

Premise
-------
A child hears a spooky problem in an old house: thirty soft taps, a fluttering
shadow, and a note with the word "factor" on it. The story begins as a ghost
mystery, turns on careful problem solving, and ends with a twist: the "ghost"
was making a message by moving puzzle pieces, and the house's mystery was a math
hint, not a haunting.

The world model keeps track of:
- physical meters: tapping, hidden, open, solved, surprising
- emotional memes: fear, courage, curiosity, relief, pride

Contract notes
--------------
- Uses the shared result containers from storyworlds/results.py.
- Provides StoryParams, build_parser, resolve_params, generate, emit, main.
- Supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp.
- Includes a Python reasonableness gate and an inline ASP twin.
- Generates QA from world state, not by parsing rendered prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

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


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    dark_spot: str


@dataclass
class Mystery:
    id: str
    clue_word: str
    spooky_sound: str
    count: int
    note_word: str
    hidden_message: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("mystery", 0.0) < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] = e.memes.get("fear", 0.0) + 1
        out.append("__fear__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("opened_box") and not world.facts.get("solved"):
        clue = world.get("clue")
        sig = ("clue", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["revealed"] = clue.meters.get("revealed", 0.0) + 1
            out.append("__clue__")
    return out


def _r_solve(world: World) -> list[str]:
    if world.facts.get("counted") and world.facts.get("matched") and not world.facts.get("solved"):
        world.facts["solved"] = True
        world.get("room").meters["solved"] = 1
        return ["__solve__"]
    return []


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("clue", _r_clue), Rule("solve", _r_solve)]


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


def mystery_risky(mystery: Mystery) -> bool:
    return mystery.count >= 30 and "ghost" in mystery.tags


def tool_reasonable(tool: Tool) -> bool:
    return tool.id in {"notebook", "flashlight", "magnifier", "ribbon"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            for tid, t in TOOLS.items():
                if mystery_risky(m) and tool_reasonable(t):
                    combos.append((sid, mid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting("attic", "the attic", "dusty and dim", "the back corner"),
    "library": Setting("library", "the old library", "quiet and moonlit", "the tall shelves"),
    "hall": Setting("hall", "the front hall", "echoey and pale", "the staircase landing"),
}

MYSTERIES = {
    "thirty_taps": Mystery(
        "thirty_taps",
        clue_word="factor",
        spooky_sound="thirty soft taps",
        count=30,
        note_word="factor",
        hidden_message="thirty is a factor of thirty",
        twist="the taps were a counting trick, not a ghost knock",
        tags={"ghost", "thirty", "factor", "mystery"},
    ),
    "thirty_rustles": Mystery(
        "thirty_rustles",
        clue_word="factor",
        spooky_sound="thirty tiny rustles",
        count=30,
        note_word="factor",
        hidden_message="thirty circles the lamp and the answer is a factor of thirty",
        twist="the rustles came from a ribbon tugging a toy",
        tags={"ghost", "thirty", "factor", "mystery"},
    ),
}

TOOLS = {
    "notebook": Tool("notebook", "notebook", "a little notebook", "count clues"),
    "flashlight": Tool("flashlight", "flashlight", "a flashlight", "look under shadows"),
    "magnifier": Tool("magnifier", "magnifier", "a magnifying glass", "read tiny marks"),
    "ribbon": Tool("ribbon", "ribbon", "a red ribbon", "tie pieces together"),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "Zoe", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Owen", "Milo", "Eli"]
HELPERS = ["Grandma", "Mom", "Dad", "Aunt June"]


def asp_facts() -> str:
    import asp
    parts = []
    for sid in SETTINGS:
        parts.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        parts.append(asp.fact("mystery", mid))
        parts.append(asp.fact("count", mid, m.count))
        parts.append(asp.fact("ghostish", mid))
    for tid, t in TOOLS.items():
        parts.append(asp.fact("tool", tid))
        if tool_reasonable(t):
            parts.append(asp.fact("reasonable_tool", tid))
    parts.append(asp.fact("min_count", 30))
    return "\n".join(parts)


ASP_RULES = r"""
risky(M) :- mystery(M), count(M, C), min_count(N), C >= N, ghostish(M).
reasonable(T) :- tool(T), reasonable_tool(T).
valid(S, M, T) :- setting(S), risky(M), reasonable(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a, b = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" only in clingo:", sorted(a - b))
        print(" only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, tool=None,
                                                            hero=None, hero_gender=None,
                                                            helper=None, helper_gender=None),
                                        random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print("MISMATCH: generate smoke test failed:", e)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=["mother", "father", "woman", "man"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting, mystery, tool, hero, hero_gender, helper, helper_gender)


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="solver"))
    helper = world.add(Entity(params.helper, "character", params.helper_gender, role="helper"))
    room = world.add(Entity("room", "thing", "room", label=SETTINGS[params.setting].place))
    clue = world.add(Entity("clue", "thing", "clue", label="the clue card"))
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]

    hero.meters["mystery"] = 1
    hero.memes["curiosity"] = 1
    room.meters["mystery"] = 1
    world.facts.update(hero=hero, helper=helper, room=room, clue=clue, mystery=mystery, tool=tool)

    world.say(
        f"On a pale night, {hero.id} and {helper.id} went into {world.setting.place}. "
        f"The room felt {world.setting.mood}, and {world.setting.dark_spot} looked like it could hide a secret."
    )
    world.say(
        f"Then they heard {mystery.spooky_sound} from the dark, and {hero.id} found a scrap of paper that said '{mystery.clue_word}'."
    )
    world.para()
    world.say(
        f"{hero.id} held up {tool.phrase} and said, 'We can solve this.' "
        f"{helper.id} nodded, because the mystery had a pattern to it."
    )

    hero.meters["mystery"] += 1
    clue.meters["hidden"] = 1
    world.facts["opened_box"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"They counted the clues one by one. There were {mystery.count} taps, and the note kept repeating the word factor."
    )
    world.facts["counted"] = True
    world.facts["matched"] = True
    propagate(world, narrate=False)

    if world.facts.get("solved"):
        world.say(
            f"At last, {helper.id} smiled and showed the twist: {mystery.twist}. "
            f"The note meant that {mystery.hidden_message}."
        )
        world.say(
            f"The 'ghost' was only moving things in the dark to make a puzzle trail. "
            f"{hero.id} laughed, and the spooky room felt bright and safe."
        )

    world.facts["resolved"] = bool(world.facts.get("solved"))
    return world


def _story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    h: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question="What made the story feel spooky at first?",
            answer=f"It felt spooky because {m.spooky_sound} came out of the dark, and {h.id} did not know what was making it. The old room and the mystery word made it feel like a ghost story."
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"{h.id} and {helper.id} slowed down and counted the clues instead of guessing. They used {f['tool'].label} to study the evidence, and that helped them see the pattern."
        ),
        QAItem(
            question="What was the twist at the end?",
            answer=f"The twist was that the 'ghost' was not a ghost at all. It was making a puzzle trail, and the note was pointing to a math clue about thirty being a factor of thirty."
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question="What is a factor?",
            answer="A factor is a number that can be multiplied by another number to make a whole answer."
        ),
        QAItem(
            question="What is thirty?",
            answer="Thirty is the number after twenty-nine and before thirty-one."
        ),
        QAItem(
            question="Why do people use a flashlight in a dark place?",
            answer="A flashlight helps people see in the dark without lighting a flame."
        ),
        QAItem(
            question="Why is a mystery fun to solve?",
            answer="A mystery is fun because you can look for clues, think carefully, and fit the pieces together."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    return [
        f"Write a ghost-story mystery for a young child that includes the words factor and thirty.",
        f"Tell a spooky story where {world.facts['hero'].id} hears {m.spooky_sound}, then solves the mystery with careful thinking.",
        f"Write a child-friendly story with a twist ending: the haunted sound turns out to be a clue about a factor of thirty.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams("attic", "thirty_taps", "notebook", "Maya", "girl", "Grandma", "woman"),
    StoryParams("library", "thirty_rustles", "flashlight", "Theo", "boy", "Dad", "man"),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
