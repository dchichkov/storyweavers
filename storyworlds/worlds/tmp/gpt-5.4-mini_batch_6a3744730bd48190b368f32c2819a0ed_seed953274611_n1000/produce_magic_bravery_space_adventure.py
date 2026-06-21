#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/produce_magic_bravery_space_adventure.py
========================================================================

A small, self-contained story world for a space adventure about a child who
needs to produce a little magic, summon bravery, and help a stranded friend
get home safely.

The domain is tiny on purpose: one ship, one moon path, one tricky drifting
gate, and one brave choice. The story model tracks physical meters and emotional
memes so the prose follows the simulation rather than acting like a frozen
template.

Run:
    python storyworlds/worlds/gpt-5.4-mini/produce_magic_bravery_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/produce_magic_bravery_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/produce_magic_bravery_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/produce_magic_bravery_space_adventure.py --verify
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
BRAVERY_MIN = 4.0
MAGIC_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class MoonGate:
    id: str
    label: str
    sparkle: str
    unstable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    produce_text: str
    effort: int
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    setting: str
    launch_text: str
    problem_text: str
    helper_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    ship: Optional[Ship] = None
    gate: Optional[MoonGate] = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone.ship = copy.deepcopy(self.ship)
        clone.gate = copy.deepcopy(self.gate)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_magic_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters.get("magic", 0.0) >= THRESHOLD and "glow" not in world.fired:
        world.fired.add(("glow",))
        world.get("ship").meters["light"] = world.get("ship").meters.get("light", 0.0) + 1
        out.append("__glow__")
    return out


def _r_brave_ready(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("bravery", 0.0) >= BRAVERY_MIN and "steady" not in world.fired:
        world.fired.add(("steady",))
        world.get("ship").memes["hope"] = world.get("ship").memes.get("hope", 0.0) + 1
        out.append("__steady__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_magic_spill, _r_brave_ready):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, tool: MagicTool) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["magic"] = hero.meters.get("magic", 0.0) + tool.power
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + tool.effort
    propagate(sim, narrate=False)
    return {
        "lit": sim.ship.meters.get("light", 0.0) >= THRESHOLD if sim.ship else False,
        "steady": sim.ship.memes.get("hope", 0.0) >= THRESHOLD if sim.ship else False,
    }


def launch(world: World, hero: Entity, adventure: Adventure, gate: MoonGate) -> None:
    world.say(
        f"On a quiet day among the stars, {hero.id} rode the ship through {adventure.setting}. "
        f"{adventure.launch_text}"
    )
    world.say(
        f"Then the path bent toward {gate.label}, and the moon-gate shimmered with {gate.sparkle}."
    )


def problem(world: World, hero: Entity, gate: MoonGate) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} peered ahead and frowned. The gate looked tricky, and the ship needed a little light."
    )
    world.say(
        f'"If we do not find a way through," {hero.id} whispered, "we will drift and never reach the far moon."'
    )
    world.say(gate.label.capitalize() + " waited in the dark.")
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1


def offer_magic(world: World, hero: Entity, tool: MagicTool, gate: MoonGate) -> None:
    hero.meters["magic"] = hero.meters.get("magic", 0.0) + tool.power
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + tool.effort
    world.say(
        f'{hero.id} lifted {tool.phrase}. "{tool.produce_text}," {hero.id} said, and took a slow breath.'
    )
    world.say(
        f"That choice was not loud, but it was brave: the little {tool.label} could help the ship face {gate.label}."
    )
    propagate(world, narrate=False)
    if world.ship:
        if world.ship.meters.get("light", 0.0) >= THRESHOLD:
            world.say("A soft light bloomed across the control panel.")
        if world.ship.memes.get("hope", 0.0) >= THRESHOLD:
            world.say("The cabin felt steadier at once.")


def cross_gate(world: World, hero: Entity, adventure: Adventure, gate: MoonGate) -> None:
    world.say(
        f"With the glow ready, the ship slipped past {gate.label}. The sparkles turned into a clear path."
    )
    world.say(
        f"{adventure.helper_text}"
    )
    world.say(
        f"At the end, {hero.id} smiled at the little trail of light left behind them."
    )


def finish(world: World, hero: Entity, adventure: Adventure) -> None:
    world.say(
        f"{adventure.ending_text} {hero.id} returned home with brave hands, and the ship still shining."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1


def tell(adventure: Adventure, tool: MagicTool, gate: MoonGate, name: str = "Nova",
         gender: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=gender, role="hero"))
    world.ship = Ship(id="ship", label="little starship", meters={"light": 0.0}, memes={"hope": 0.0})
    world.gate = gate
    world.add(Entity(id="ship_entity", kind="thing", type="ship", label="little starship"))
    launch(world, hero, adventure, gate)
    world.para()
    problem(world, hero, gate)
    world.para()
    offer_magic(world, hero, tool, gate)
    world.para()
    cross_gate(world, hero, adventure, gate)
    finish(world, hero, adventure)
    world.facts.update(hero=hero, tool=tool, gate=gate, adventure=adventure)
    return world


ADVENTURES = {
    "moonpath": Adventure(
        id="moonpath",
        setting="the silver moonpath",
        launch_text="The engines hummed while the stars blinked like tiny lanterns.",
        problem_text="",
        helper_text="The captain charted a calm line between the drifting stones, and the ship answered with a happy hum.",
        ending_text="By dawn, the far moon was not far at all.",
        tags={"space", "adventure"},
    ),
    "comettrail": Adventure(
        id="comettrail",
        setting="the comet trail",
        launch_text="The ship zipped behind a comet, where the dust twinkled like sugar.",
        problem_text="",
        helper_text="The bright trail showed the safest way through, and the ship followed it carefully.",
        ending_text="Soon the crew could see the home station ahead.",
        tags={"space", "adventure"},
    ),
}

MAGIC_TOOLS = {
    "starlight": MagicTool(
        id="starlight",
        label="star charm",
        phrase="a tiny star charm",
        produce_text="I can produce a little star light",
        effort=2,
        power=1,
        tags={"magic", "light"},
    ),
    "sparkle": MagicTool(
        id="sparkle",
        label="sparkle wand",
        phrase="a small sparkle wand",
        produce_text="I can produce a soft sparkle",
        effort=1,
        power=1,
        tags={"magic", "sparkle"},
    ),
    "courage": MagicTool(
        id="courage",
        label="courage coin",
        phrase="a warm courage coin",
        produce_text="I can produce enough bravery to try",
        effort=3,
        power=1,
        tags={"magic", "bravery"},
    ),
}

CURATED = [
    StoryParams(adventure="moonpath", tool="starlight", gate="moon", name="Nova", gender="girl", seed=1),
    StoryParams(adventure="comettrail", tool="courage", gate="comet", name="Pax", gender="boy", seed=2),
]

@dataclass
class StoryParams:
    adventure: str
    tool: str
    gate: str
    name: str = "Nova"
    gender: str = "girl"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in ADVENTURES:
        for t in MAGIC_TOOLS:
            for g in ("moon", "comet"):
                combos.append((a, t, g))
    return combos


KNOWLEDGE = {
    "magic": [("What is magic in a story?",
               "Magic in a story is a special, pretend power that can make unusual things happen.")],
    "bravery": [("What is bravery?",
                 "Bravery is trying to do a hard thing even when you feel a little scared.")],
    "star": [("What is a star?",
              "A star is a giant ball of hot light in the sky.")],
    "moon": [("What is the moon?",
              "The moon is a round space rock that goes around Earth.")],
    "space": [("What is space?",
               "Space is the huge area beyond Earth where the stars, planets, and moons are.")],
    "light": [("Why is light helpful in the dark?",
               "Light helps you see where you are going and makes scary dark places feel safer.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the word "produce" and a little magic.',
        f"Tell a story where {f['hero'].id} must produce magic to help a ship cross a tricky gate.",
        f"Write a brave moon-story where a child uses a magic tool and learns that bravery can light the way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, tool, gate, adv = f["hero"], f["tool"], f["gate"], f["adventure"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a young space traveler who wanted to help the ship. {hero.id} had to stay calm and brave when the gate looked tricky."),
        ("What did {name} do with the magic tool?".format(name=hero.id),
         f"{hero.id} lifted {tool.phrase} and said they could produce a little magic. That brave choice helped the ship face {gate.label}."),
        ("How did the problem get solved?",
         f"The ship grew brighter and steadier, then slipped past {gate.label} safely. Bravery and magic worked together, so the crew could keep going."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool"].tags) | set(world.facts["adventure"].tags)
    out: list[tuple[str, str]] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_ready(H) :- hero(H), magic(H, M), M >= 1.
brave_ready(H) :- hero(H), bravery(H, B), B >= 4.
solve(H) :- magic_ready(H), brave_ready(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for tid, tool in MAGIC_TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_power", tid, tool.power))
        lines.append(asp.fact("tool_effort", tid, tool.effort))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    lines.append(asp.fact("bravery_min", int(BRAVERY_MIN)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solve/1.", ""))
    _ = model
    try:
        sample = generate(resolve_params(argparse.Namespace(adventure=None, tool=None, gate=None, name=None, gender=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"FAILED: smoke test crashed: {exc}")
        return 1
    print("OK: smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with magic and bravery.")
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--tool", choices=MAGIC_TOOLS)
    ap.add_argument("--gate", choices=["moon", "comet"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if not combos:
        raise StoryError("No valid space stories are available.")
    adv = args.adventure or rng.choice(sorted(ADVENTURES))
    tool = args.tool or rng.choice(sorted(MAGIC_TOOLS))
    gate = args.gate or rng.choice(["moon", "comet"])
    if (adv, tool, gate) not in combos:
        raise StoryError("That combination does not make a reasonable adventure.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Nova", "Pax", "Luna", "Orin", "Mira", "Zed"])
    return StoryParams(adventure=adv, tool=tool, gate=gate, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    if params.adventure not in ADVENTURES:
        raise StoryError("Unknown adventure.")
    if params.tool not in MAGIC_TOOLS:
        raise StoryError("Unknown magic tool.")
    if params.gate not in {"moon", "comet"}:
        raise StoryError("Unknown gate.")
    world = tell(ADVENTURES[params.adventure], MAGIC_TOOLS[params.tool],
                 MoonGate(id=params.gate, label="the moon-gate" if params.gate == "moon" else "the comet-gate",
                          sparkle="silver sparks" if params.gate == "moon" else "bright comet dust"),
                 name=params.name, gender=params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show solve/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(adventure="moonpath", tool="starlight", gate="moon", name="Nova", gender="girl")),
            generate(StoryParams(adventure="comettrail", tool="courage", gate="comet", name="Pax", gender="boy")),
        ]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
