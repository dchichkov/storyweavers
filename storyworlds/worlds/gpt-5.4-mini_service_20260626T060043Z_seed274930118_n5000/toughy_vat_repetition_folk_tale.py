#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about a toughy, a vat, and repetition.

The domain premise is simple:
- A small, stubborn creature named Toughy keeps visiting a vat.
- The vat begins as something helpful or tempting, but repeated visits reveal a problem.
- Repetition is the narrative instrument: each pass through the same action changes the state
  a little more until the final choice becomes wise.

The script follows the Storyweavers contract:
- standalone stdlib storyworld script
- eager import of shared result containers
- lazy import of asp helper inside ASP helpers
- StoryParams, registries, parser, resolve_params, generate, emit, main
- Python reasonableness gate plus inline ASP twin
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    is_outdoor: bool = True


@dataclass
class Ritual:
    id: str
    verb: str
    gerund: str
    effect: str
    repeated_effect: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    risk_if: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    helps_against: set[str]
    fix: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.counts: dict[str, int] = {"visits": 0, "warnings": 0}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.counts = dict(self.counts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orchard": Setting("the orchard"),
    "mill": Setting("the mill"),
    "lane": Setting("the windy lane"),
    "barn": Setting("the old barn"),
}

RITUALS = {
    "stir": Ritual(
        id="stir",
        verb="stir the vat",
        gerund="stirring the vat",
        effect="the surface went round and round",
        repeated_effect="the broth became thicker and thicker",
        risk="it might spill over the rim",
        keyword="vat",
        tags={"vat", "stir"},
    ),
    "taste": Ritual(
        id="taste",
        verb="taste from the vat",
        gerund="tasting from the vat",
        effect="the spoon came up sweet",
        repeated_effect="the sweetness grew stronger and stronger",
        risk="it might lose its gentle flavor",
        keyword="vat",
        tags={"vat", "taste"},
    ),
    "carry": Ritual(
        id="carry",
        verb="carry the vat",
        gerund="carrying the vat",
        effect="the little feet held it steady",
        repeated_effect="the arms grew more and more tired",
        risk="the heavy vat might slip",
        keyword="vat",
        tags={"vat", "carry"},
    ),
}

PRIZES = {
    "honey": Prize("honey", "honey", "a small wooden cup of honey", "it might spill", "hands"),
    "porridge": Prize("porridge", "porridge", "a warm bowl of porridge", "it might cool", "hands"),
    "jam": Prize("jam", "jam", "a bright jar of jam", "it might break", "hands"),
}

TOOLS = {
    "ladle": Tool("ladle", "a long ladle", {"spill"}, "hold the vat steady with a long ladle", "kept the vat from wobbling"),
    "lid": Tool("lid", "a snug lid", {"cool", "spill"}, "set on a snug lid after each stir", "kept the sweetness safe"),
    "tray": Tool("tray", "a broad tray", {"break", "spill"}, "put the vat on a broad tray", "made the carrying safer"),
}

NAMES = ["Toughy", "Marn", "Bela", "Jory", "Nina", "Pip"]
TITLE_WORDS = ["toughy", "vat"]
TRAITS = ["stubborn", "patient", "cheerful", "curious", "steady"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    ritual: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def ritual_risks_prize(ritual: Ritual, prize: Prize) -> bool:
    return True


def select_tool(ritual: Ritual, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if any(r in tool.helps_against for r in {prize.risk_if.replace("it might ", ""), "spill", "cool", "break"}):
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RITUALS:
            for p in PRIZES:
                if ritual_risks_prize(RITUALS[r], PRIZES[p]) and select_tool(RITUALS[r], PRIZES[p]):
                    combos.append((s, r, p))
    return combos


# ---------------------------------------------------------------------------
# World narration helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    ritual = RITUALS[params.ritual]
    prize = PRIZES[params.prize]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="toughy"))
    vat = world.add(Entity(id="vat", type="vat", label="vat", phrase="the big vat"))
    prize_ent = world.add(Entity(id="prize", type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id))
    tool = select_tool(ritual, prize)

    world.facts.update(hero=hero, vat=vat, prize=prize_ent, prize_cfg=prize, tool=tool, ritual=ritual, setting=setting)
    hero.memes["want"] = 1.0

    world.say(f"In {setting.place}, there lived a little toughy named {hero.id}.")
    world.say(f"{hero.id} liked {ritual.gerund} near the vat, because {ritual.effect}.")
    world.say(f"One day, {hero.id} found {prize.phrase} beside the vat and smiled at it.")

    world.para()
    for i in range(3):
        world.counts["visits"] += 1
        if i == 0:
            world.say(f"The first time, {hero.id} went to the vat and began {ritual.gerund}.")
        elif i == 1:
            world.say(f"The second time, {hero.id} went back and did it again, and {ritual.repeated_effect}.")
        else:
            world.say(f"The third time, {hero.id} returned once more, but now the vat looked a little less safe.")

    world.para()
    world.counts["warnings"] += 1
    world.say(f"Then someone said, \"Careful, little toughy. {prize.risk_if.capitalize()}\"")

    if tool is not None:
        world.say(f"{hero.id} thought about it and found {tool.label}.")
        world.say(f"With {tool.fix}, {tool.tail}.")
        hero.memes["relief"] = 1.0
        world.say(f"So {hero.id} could keep the nice little work at the vat without a mess.")
    else:
        hero.memes["worry"] = 1.0
        world.say(f"{hero.id} paused, listened, and chose to stop before anything could go wrong.")

    world.para()
    if tool is not None:
        world.say(f"In the end, {hero.id} stayed near the vat, and {prize.label} stayed safe.")
    else:
        world.say(f"In the end, {hero.id} left the vat alone, and the prize stayed safe and sound.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child that includes the word "{f["ritual"].keyword}" and the word "toughy".',
        f"Tell a repetitive little story about {f['hero'].id} and a vat, where doing the same thing three times changes the outcome.",
        f"Write a simple folk tale in which a stubborn small character learns what to do with a vat and a precious prize.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    ritual = f["ritual"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who was the little toughy in the story?",
            answer=f"The little toughy was {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing at the vat?",
            answer=f"{hero.id} kept {ritual.gerund} again and again.",
        ),
        QAItem(
            question=f"What was the prize near the vat?",
            answer=f"The prize was {prize.phrase}.",
        ),
    ]
    if tool is not None:
        qa.append(
            QAItem(
                question=f"How did {hero.id} keep the vat story safe?",
                answer=f"{hero.id} used {tool.label} so the repeated work at the vat could continue without ruining the prize.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"Why did {hero.id} stop in the end?",
                answer=f"{hero.id} stopped because the warning showed that repeating the same thing at the vat would have made trouble for the prize.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vat?",
            answer="A vat is a large container, often used to hold or mix things like soup, dye, or batter.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means doing, saying, or showing the same thing more than once so it feels important and easy to remember.",
        ),
        QAItem(
            question="What makes a folk tale feel like a folk tale?",
            answer="A folk tale often has a simple problem, a memorable character, a clear lesson, and a storytelling rhythm that can repeat phrases or events.",
        ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
ritual_risks(R,P) :- ritual(R), prize(P).
has_tool(R,P) :- ritual_risks(R,P), tool(T), helps(T,P).
valid(S,R,P) :- setting(S), ritual(R), prize(P), ritual_risks(R,P), has_tool(R,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RITUALS:
        lines.append(asp.fact("ritual", rid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("helps", "ladle", "spill"))
        lines.append(asp.fact("helps", "lid", "spill"))
        lines.append(asp.fact("helps", "lid", "cool"))
        lines.append(asp.fact("helps", "tray", "break"))
        lines.append(asp.fact("helps", "tray", "spill"))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generate / emit / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about Toughy and a vat.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.ritual is None or c[1] == args.ritual)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ritual, prize = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        ritual=ritual,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  counts={world.counts}")
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
    StoryParams(setting="orchard", ritual="stir", prize="honey", name="Toughy", trait="stubborn"),
    StoryParams(setting="mill", ritual="taste", prize="porridge", name="Marn", trait="curious"),
    StoryParams(setting="barn", ritual="carry", prize="jam", name="Bela", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
