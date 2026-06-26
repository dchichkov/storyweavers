#!/usr/bin/env python3
"""
A small pirate-tale storyworld with a compact simulation of push-dim/apply
dynamics and three narrative instruments: Twist, Repetition, and Transformation.

Premise:
- A young pirate wants a shining prize.
- A dim lantern or clouded signal makes the prize hard to find.
- The crew must apply a clever change, then repeat the right action, until the
  world transforms and the treasure is safely reached.

The story is state-driven: light, location, ownership, and confidence all shift
as the crew tries, fails, adjusts, and finally succeeds.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "captainess"}
        male = {"boy", "man", "father", "captain", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the harbor"
    afford_push: bool = True
    afford_apply: bool = True


@dataclass
class Puzzle:
    id: str
    verb: str
    gerund: str
    twist: str
    repetition: str
    transformation: str
    dim_target: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    role: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    outcome: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class StoryParams:
    setting: str
    puzzle: str
    prize: str
    tool: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor"),
    "island": Setting(place="the island shore"),
    "cove": Setting(place="the hidden cove"),
    "deck": Setting(place="the ship deck"),
}

PUZZLES = {
    "lantern": Puzzle(
        id="lantern",
        verb="push the dim lantern brighter",
        gerund="pushing the dim lantern",
        twist="the lantern was too dim to light the map mark",
        repetition="push it again and again",
        transformation="the dark patch on the map became a bright gold point",
        dim_target="lantern",
        keyword="push-dim",
        tags={"light", "ship"},
    ),
    "clouds": Puzzle(
        id="clouds",
        verb="apply the signal flag carefully",
        gerund="applying the signal flag",
        twist="the cloudy sky hid the far rock",
        repetition="wave the flag twice more",
        transformation="the lookout could finally spot the rock",
        dim_target="sky",
        keyword="apply",
        tags={"sky", "signal"},
    ),
    "glass": Puzzle(
        id="glass",
        verb="push the blue glass into place",
        gerund="pushing the blue glass",
        twist="the glass stayed dim until the sun hit it just right",
        repetition="turn it a little more",
        transformation="the glass flashed like a small star",
        dim_target="glass",
        keyword="push-dim",
        tags={"shine", "light"},
    ),
    "lantern_flag": Puzzle(
        id="lantern_flag",
        verb="apply the lantern cover and push the light through",
        gerund="applying the lantern cover",
        twist="the cover made the lantern even dimmer at first",
        repetition="try the same careful push again",
        transformation="the cover glowed softly and showed the path",
        dim_target="cover",
        keyword="apply",
        tags={"light", "twist"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a curled treasure map", type="map", role="thing"),
    "key": Prize(label="key", phrase="a tiny brass key", type="key", role="thing"),
    "coin": Prize(label="coin", phrase="a bright captain's coin", type="coin", role="thing", plural=False),
    "shell": Prize(label="shell", phrase="a pearl shell", type="shell", role="thing"),
}

TOOLS = {
    "lens": Tool(id="lens", label="a polished lens", prep="set a polished lens over the light", outcome="the light grew clearer", helps={"lantern", "glass"}),
    "flag": Tool(id="flag", label="a red signal flag", prep="apply the red signal flag to the mast", outcome="the signal showed through the fog", helps={"clouds"}),
    "cloth": Tool(id="cloth", label="a dry cloth", prep="apply a dry cloth over the wet glass", outcome="the glass stopped shining muddy gray", helps={"glass", "lantern_flag"}),
    "mirror": Tool(id="mirror", label="a small mirror", prep="place a small mirror by the lantern", outcome="the beam bounced toward the mark", helps={"lantern"}),
}

NAMES = ["Mina", "Kip", "Rory", "Nell", "Bo", "Tia", "Jax", "Pia"]
TRAITS = ["brave", "cheeky", "curious", "bold", "quick", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PUZZLES:
            for pr in PRIZES:
                if p in {"lantern", "glass", "lantern_flag"} and pr in {"map", "key", "shell"}:
                    out.append((s, p, pr))
                elif p == "clouds" and pr in {"map", "coin"}:
                    out.append((s, p, pr))
    return out


def reason_reject(puzzle: Puzzle, prize: Prize) -> str:
    return f"(No story: {puzzle.verb} does not reasonably threaten {prize.phrase} in this pirate tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with twist, repetition, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["captain", "first mate", "older pirate", "deckhand"])
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.puzzle:
        combos = [c for c in combos if c[1] == args.puzzle]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid pirate story combination matches the given options.)")
    setting, puzzle, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(["captain", "first mate", "older pirate", "deckhand"])
    trait = args.trait or rng.choice(TRAITS)
    tool = args.tool or rng.choice(sorted([t for t, td in TOOLS.items() if puzzle in td.helps]))
    return StoryParams(setting=setting, puzzle=puzzle, prize=prize, tool=tool, name=name, gender=gender, companion=companion, trait=trait)


def can_help(tool: Tool, puzzle: Puzzle) -> bool:
    return puzzle.id in tool.helps


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"curiosity": 1.0, "hope": 1.0}))
    mate = world.add(Entity(id="Mate", kind="character", type="pirate", label=f"the {params.companion}", memes={"patience": 1.0}))
    prize = world.add(Entity(id="Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    tool_def = TOOLS[params.tool]
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, owner=mate.id))
    puzzle = PUZZLES[params.puzzle]

    # Act 1
    world.say(f"{hero.id} was a {params.trait} little pirate who loved bright adventures on {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} wanted {prize.phrase} because every treasure felt like a tiny song to {hero.pronoun('object')}.")
    world.say(f"But {puzzle.twist}.")

    # Act 2
    world.para()
    world.say(f"{hero.id} tried to {puzzle.verb}, yet the way stayed tricky.")
    world.say(f"{mate.label.capitalize()} said, \"Let's {puzzle.repetition}.\"")
    world.say(f"{hero.id} did, but the first try still did not work.")

    # Act 3
    world.para()
    if can_help(tool_def, puzzle):
        world.say(f"Then {mate.label} said, \"We should {tool_def.prep}.\"")
        world.say(f"{hero.id} listened and applied the plan with care.")
        world.say(f"At last, {puzzle.transformation}.")
        world.say(f"{hero.id} smiled wide and held {prize.it()} high while the sea winked nearby.")
    else:
        raise StoryError("(Chosen tool cannot help this puzzle; no honest pirate resolution.)")

    world.facts.update(hero=hero, mate=mate, prize=prize, tool=tool, tool_def=tool_def, puzzle=puzzle, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a young child that uses the words "{f["puzzle"].keyword}", "Twist", "Repetition", and "Transformation".',
        f"Tell a gentle story where {f['hero'].id} wants {f['prize'].phrase} and {f['mate'].label} helps with {f['tool_def'].label}.",
        f"Write a tiny story about a pirate who must {f['puzzle'].verb} before the treasure can be found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    prize = f["prize"]
    puzzle = f["puzzle"]
    tool = f["tool_def"]
    return [
        QAItem(
            question=f"Who wanted {prize.phrase} in the story?",
            answer=f"{hero.id} wanted {prize.phrase}, because {hero.pronoun()} was a {hero.type} pirate with a brave heart.",
        ),
        QAItem(
            question=f"What made the treasure hunt hard at first?",
            answer=f"{puzzle.twist.capitalize()}. That meant {hero.id} could not find the prize right away.",
        ),
        QAItem(
            question=f"How did the crew fix the problem?",
            answer=f"They used {tool.label} and kept trying. The plan worked because they knew when to apply the right change.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"{puzzle.transformation.capitalize()} and {hero.id} ended the tale happy with {prize.it()} in hand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a seafaring adventurer in stories, often sailing from place to place in search of treasure.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light so people can see in dark places.",
        ),
        QAItem(
            question="What does it mean to apply something?",
            answer="To apply something means to put it on or use it carefully in the right place.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the problem harder or more interesting for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S,P,R) :- setting(S), puzzle(P), prize(R), valid_combo(S,P,R).

valid_combo(S,P,R) :- setting(S), puzzle(P), prize(R), relevant(P,R).

relevant(lantern,map).
relevant(lantern,key).
relevant(lantern,shell).
relevant(glass,map).
relevant(glass,key).
relevant(glass,shell).
relevant(lantern_flag,map).
relevant(lantern_flag,key).
relevant(lantern_flag,shell).
relevant(clouds,map).
relevant(clouds,coin).

#show valid_combo/3.
#show good_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PUZZLES:
        lines.append(asp.fact("puzzle", p))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for p, puzzle in PUZZLES.items():
        for r in PRIZES:
            if (p, r) in {("clouds", "coin"), ("clouds", "map")}:
                lines.append(asp.fact("relevant", p, r))
            if p in {"lantern", "glass", "lantern_flag"} and r in {"map", "key", "shell"}:
                lines.append(asp.fact("relevant", p, r))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    clingo_set = set(asp.atoms(model, "valid_combo"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    print("only clingo:", sorted(clingo_set - py_set))
    print("only python:", sorted(py_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_combo")))


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


CURATED = [
    StoryParams(setting="harbor", puzzle="lantern", prize="map", tool="lens", name="Mina", gender="girl", companion="first mate", trait="curious"),
    StoryParams(setting="deck", puzzle="clouds", prize="coin", tool="flag", name="Kip", gender="boy", companion="captain", trait="brave"),
    StoryParams(setting="cove", puzzle="glass", prize="shell", tool="cloth", name="Nell", gender="girl", companion="older pirate", trait="spry"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
