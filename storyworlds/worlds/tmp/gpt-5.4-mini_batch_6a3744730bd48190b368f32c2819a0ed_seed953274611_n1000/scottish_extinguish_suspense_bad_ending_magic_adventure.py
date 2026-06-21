#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scottish_extinguish_suspense_bad_ending_magic_adventure.py
===========================================================================================

A small adventure storyworld about a windy Scottish night, a bit of magic, a
suspenseful search for a lost lantern, and a bad ending when the magic goes
wrong and the light cannot be saved.

The world is deliberately tiny:
- typed entities with physical meters and emotional memes
- a state-driven story, not a fixed paragraph swap
- one forward-chained causal rule engine
- a Python reasonableness gate with an ASP twin
- three QA sets grounded in simulated state

This world always includes the words "scottish" and "extinguish" in its
storyspace and keeps the style close to an adventure tale.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    cue: str


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    glow: str
    fragile: bool = True
    magical: bool = False
    dims: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    sense: int
    power: int
    safe: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_storm(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    if lantern and lantern.meters["lit"] >= THRESHOLD:
        sig = ("storm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("sky").meters["storm"] += 1
            for e in world.entities.values():
                if e.kind == "character":
                    e.memes["fear"] += 1
            out.append("__storm__")
    return out


def _r_fade(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    if lantern and world.get("sky").meters["storm"] >= THRESHOLD and lantern.meters["lit"] >= THRESHOLD:
        sig = ("fade",)
        if sig not in world.fired:
            world.fired.add(sig)
            lantern.meters["flicker"] += 1
            out.append("__flicker__")
    return out


CAUSAL_RULES = [Rule("storm", "physical", _r_storm), Rule("fade", "physical", _r_fade)]


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


def magic_ok(tool: MagicTool) -> bool:
    return tool.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for relic in RELICS:
            for tool in TOOLS:
                if tool.sense >= SENSE_MIN and RELICS[relic].fragile and TOOLS[tool].power >= 1:
                    combos.append((setting, relic, tool))
    return combos


def predict(world: World) -> dict:
    sim = world.copy()
    _attempt_extinguish(sim, narrate=False)
    return {
        "flicker": sim.get("lantern").meters["flicker"],
        "dark": sim.get("hall").meters["darkness"],
    }


def _attempt_magic(world: World, tool: MagicTool, target: Entity, narrate: bool = True) -> None:
    target.meters["lit"] += 1
    world.get("lantern").meters["lit"] += 1
    world.get("lantern").meters["magic"] += 1
    world.say(
        f"The {tool.label} hummed, and the {target.label} shone at once. "
        f"It was a bright little spell, proud and quick."
    )
    propagate(world, narrate=narrate)


def _attempt_extinguish(world: World, narrate: bool = True) -> None:
    lantern = world.get("lantern")
    lantern.meters["lit"] = 0
    lantern.meters["flicker"] += 1
    world.get("hall").meters["darkness"] += 1
    world.get("hero").memes["hope"] -= 1
    if narrate:
        world.say(
            "But the storm wind thumped the window and the flame shrank to a wobble, "
            "then to a tiny pin of gold."
        )


def tell(setting: Setting, relic: Relic, tool: MagicTool,
         hero_name: str = "Mairi", sidekick_name: str = "Ewan",
         parent_name: str = "Gran") -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=hero_name, role="hero"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="boy", label=sidekick_name, role="sidekick"))
    parent = world.add(Entity(id="parent", kind="character", type="woman", label=parent_name, role="parent"))
    hall = world.add(Entity(id="hall", type="room", label="the hall"))
    sky = world.add(Entity(id="sky", type="weather", label="the sky"))
    lantern = world.add(Entity(id="lantern", type="relic", label=relic.label))
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["parent"] = parent
    world.facts["relic"] = relic
    world.facts["tool"] = tool

    hero.memes["hope"] = 2
    sidekick.memes["curiosity"] = 2

    world.say(
        f"On a wild scottish evening, {hero.label} and {sidekick.label} went into "
        f"{setting.place}. {setting.cue}"
    )
    world.say(
        f"They were hunting for {relic.phrase}, a magical treasure that could "
        f"{relic.glow} in the dark."
    )
    world.say(
        f"Then {hero.label} found the {tool.label}. \"If we try a little spell, "
        f"we might guide the way,\" {hero.pronoun()} whispered."
    )
    world.say(
        f"{sidekick.label} swallowed hard. The air felt suspenseful, as if the old stones "
        f"were listening."
    )
    world.para()
    _attempt_magic(world, tool, lantern, narrate=True)
    world.para()
    world.say(
        f"{hero.label} lifted the lantern toward the stairs. For one shining moment, "
        f"the hall looked safe."
    )
    world.say(
        f"Then the wind rushed in like a sneaky beast. The magic began to shake, and "
        f"everyone held their breath."
    )
    _attempt_extinguish(world, narrate=True)
    world.para()
    world.say(
        f"{parent.label} hurried in with a blanket, but the spell had already slipped away. "
        f"The lantern went out, and the treasure stayed hidden."
    )
    world.say(
        f"The adventure ended badly: {hero.label} stood in the dark, staring at the cold, "
        f"empty lantern while the scottish storm boomed outside."
    )
    hero.memes["hope"] = 0
    sidekick.memes["fear"] += 2
    world.facts["outcome"] = "bad"
    return world


SETTINGS = {
    "castle": Setting(
        id="castle",
        place="the old castle on the hill",
        atmosphere="stone walls and long shadows",
        cue="A narrow stair curled upward, and every torch had gone out years ago.",
    ),
    "harbor": Setting(
        id="harbor",
        place="the windy harbor road",
        atmosphere="salt spray and creaking ropes",
        cue="The boats bobbed like black shapes, and the dock lamps were all dim.",
    ),
    "croft": Setting(
        id="croft",
        place="the moor croft",
        atmosphere="heather, peat smoke, and owl calls",
        cue="A little path led to a broken shed where something might still be waiting.",
    ),
}

RELICS = {
    "lantern": Relic(id="lantern", label="old lantern", phrase="an old lantern", glow="glow like a small moon"),
    "brooch": Relic(id="brooch", label="silver brooch", phrase="a silver brooch", glow="sparkle with blue fire"),
    "key": Relic(id="key", label="rune key", phrase="a rune key", glow="open secret doors"),
}

TOOLS = {
    "spark": MagicTool(id="spark", label="spark charm", phrase="a spark charm", effect="spark", sense=3, power=1, safe=False),
    "mist": MagicTool(id="mist", label="mist spell", phrase="a mist spell", effect="mist", sense=2, power=1, safe=False),
    "murmur": MagicTool(id="murmur", label="murmur rune", phrase="a murmur rune", effect="murmur", sense=1, power=0, safe=False),
}

GIRL_NAMES = ["Mairi", "Isla", "Fiona", "Catrin", "Ailsa"]
BOY_NAMES = ["Ewan", "Hamish", "Finlay", "Callum", "Nairn"]


@dataclass
class StoryParams:
    setting: str
    relic: str
    tool: str
    hero: str = "Mairi"
    sidekick: str = "Ewan"
    parent: str = "Gran"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story that includes the words "scottish" and "extinguish" and has a magical danger at {f["relic"].phrase}.',
        f"Tell a suspenseful Scottish tale where {f['hero'].label} tries a magic {f['tool'].label}, but the light goes out in the storm.",
        f"Write a child-facing adventure with a bad ending: magic helps for a moment, then the storm extinguish-es the light and the treasure is lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    parent = world.facts["parent"]
    relic = world.facts["relic"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.label} and {sidekick.label} went into the dark place together. {parent.label} came in at the end, but the search belonged to the two children."
        ),
        QAItem(
            question=f"Why did {hero.label} feel brave enough to try the magic?",
            answer=f"{hero.label} wanted to guide the way to {relic.phrase}. The little spell looked helpful at first, so the adventure felt possible even though the hall was spooky."
        ),
        QAItem(
            question="What went wrong at the end?",
            answer=f"The storm wind made the magic flicker, and the lantern went out. The search ended badly because the light could not be kept alive long enough."
        ),
        QAItem(
            question=f"What did the {tool.label} do?",
            answer=f"It made a brief magical glow and then failed when the wind and darkness pushed back. The spell gave hope, but it could not save the lantern."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does extinguish mean?",
            answer="To extinguish something is to make it stop burning or shining. A flame or light can be extinguished when it goes out."
        ),
        QAItem(
            question="What makes a story suspenseful?",
            answer="Suspense happens when something important might go wrong and everyone is waiting to see what happens next. It makes the reader hold their breath."
        ),
        QAItem(
            question="What is a magical adventure?",
            answer="A magical adventure is a journey where strange powers, hidden places, or enchanted objects change what the characters can do. It usually feels exciting and a little mysterious."
        ),
        QAItem(
            question="What is a Scottish setting like?",
            answer="A Scottish setting often has castles, hills, windy air, and old stone places. It can feel wild, ancient, and full of stories."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="castle", relic="lantern", tool="spark", hero="Mairi", sidekick="Ewan", parent="Gran"),
    StoryParams(setting="harbor", relic="brooch", tool="mist", hero="Fiona", sidekick="Callum", parent="Mum"),
    StoryParams(setting="croft", relic="key", tool="spark", hero="Ailsa", sidekick="Hamish", parent="Gran"),
]


def explain_rejection(tool: MagicTool) -> str:
    return f"(No story: the {tool.label} is too weak or too shaky for this adventure.)"


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not magic_ok(TOOLS[args.tool]):
        raise StoryError(explain_rejection(TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.relic is None or c[1] == args.relic)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, relic, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES)
    sidekick = args.sidekick or rng.choice(BOY_NAMES)
    parent = args.parent or rng.choice(["Gran", "Mum"])
    return StoryParams(setting=setting, relic=relic, tool=tool, hero=hero, sidekick=sidekick, parent=parent)


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("setting", SETTINGS), ("relic", RELICS), ("tool", TOOLS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"invalid {field_name}: {getattr(params, field_name)!r}")
    world = tell(SETTINGS[params.setting], RELICS[params.relic], TOOLS[params.tool], params.hero, params.sidekick, params.parent)
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
valid(S,R,T) :- setting(S), relic(R), tool(T), sense(T,SN), sense_min(M), SN >= M.
"""
def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("sense", t, tool.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False)
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Scottish, extinguish, suspense, bad-ending magic adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--parent")
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
    return valid_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
