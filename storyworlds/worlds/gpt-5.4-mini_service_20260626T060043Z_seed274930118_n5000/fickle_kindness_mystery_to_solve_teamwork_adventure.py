#!/usr/bin/env python3
"""
storyworlds/worlds/fickle_kindness_mystery_to_solve_teamwork_adventure.py
=========================================================================

A small adventure storyworld about a fickle mood, a puzzling mystery,
and a team that has to stay kind long enough to solve it.

The seed premise:
- A child or small team sets out on an adventure.
- Something important goes missing or behaves strangely.
- The group must work together, even when one helper's kindness is fickle.
- The ending should prove the mystery was solved by a concrete, world-driven turn.

This script keeps the world compact on purpose: fewer valid stories, but each one
should feel like a complete tiny adventure.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue_kind: str
    mystery_noun: str
    hiding_place: str
    truth: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    use_line: str
    final_line: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = dataclasses.deepcopy(self.entities)
        other.lines = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the harbor", kind="outdoor", affords={"shell", "lantern", "map"}),
    "forest": Setting(place="the forest path", kind="outdoor", affords={"footprints", "lantern", "map"}),
    "cove": Setting(place="the cove", kind="outdoor", affords={"shell", "lantern", "rope"}),
    "attic": Setting(place="the attic", kind="indoor", affords={"map", "lantern", "key"}),
}

MYSTERIES = {
    "shell_song": Mystery(
        id="shell_song",
        clue_kind="shell",
        mystery_noun="shell song",
        hiding_place="inside a tide pool",
        truth="a tiny crab was tapping the shell from underneath",
        reveal="The shell clicked because a little crab had been knocking on it all along.",
        tags={"shell", "sea", "crab"},
    ),
    "lost_map": Mystery(
        id="lost_map",
        clue_kind="map",
        mystery_noun="lost map",
        hiding_place="under a loose floorboard",
        truth="the map had slid under a board and waited there quietly",
        reveal="The map was tucked under a loose floorboard near the back wall.",
        tags={"map", "secret", "floorboard"},
    ),
    "lantern_glow": Mystery(
        id="lantern_glow",
        clue_kind="lantern",
        mystery_noun="lantern glow",
        hiding_place="behind a hollow tree",
        truth="a firefly swarm kept slipping past the glass",
        reveal="A cluster of fireflies was shining behind the lantern glass.",
        tags={"lantern", "light", "firefly"},
    ),
    "footprints": Mystery(
        id="footprints",
        clue_kind="footprints",
        mystery_noun="footprints",
        hiding_place="near a muddy bend",
        truth="a little fox kept circling back over its own tracks",
        reveal="The footprints belonged to a fox that doubled back again and again.",
        tags={"footprints", "fox", "mud"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a small lantern",
        helps={"lantern", "footprints"},
        use_line="held the lantern low so the team could see better",
        final_line="The lantern made the clue shine clear.",
    ),
    "rope": Tool(
        id="rope",
        label="a coil of rope",
        helps={"shell", "map"},
        use_line="used the rope to climb down carefully",
        final_line="The rope kept everyone steady on the adventure.",
    ),
    "notebook": Tool(
        id="notebook",
        label="a little notebook",
        helps={"map", "shell", "footprints"},
        use_line="jotted down every clue they found",
        final_line="The notebook kept the mystery clues in order.",
    ),
    "brush": Tool(
        id="brush",
        label="a soft brush",
        helps={"shell", "map", "lantern"},
        use_line="brushed dust away from the hidden place",
        final_line="The brush uncovered the last clue without hurting it.",
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Tess", "Nora", "June"],
    "boy": ["Eli", "Owen", "Milo", "Finn", "Theo"],
}
TRAITS = ["brave", "curious", "careful", "spirited", "gentle"]
HELPER_TRAITS = ["fickle", "kind", "quiet", "bright", "steady"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("harbor", "shell_song", "rope", "Mina", "girl", "Nora", "girl"),
    StoryParams("forest", "footprints", "lantern", "Eli", "boy", "Tess", "girl"),
    StoryParams("attic", "lost_map", "brush", "Theo", "boy", "June", "girl"),
    StoryParams("cove", "lantern_glow", "notebook", "Lila", "girl", "Owen", "boy"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
mystery_valid(S, M, T) :- setting(S), mystery(M), tool(T),
                          setting_affords(S, C), clue_kind(M, C),
                          tool_helps(T, C).

% A story is reasonable when the team can actually use the tool on the mystery.
solvable(S, M, T) :- mystery_valid(S, M, T).

#show mystery_valid/3.
#show solvable/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("tool_helps", tid, h))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "mystery_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asps:
        print("  only in Python:", sorted(py - asps))
    if asps - py:
        print("  only in ASP:", sorted(asps - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for s_id, setting in SETTINGS.items():
        for m_id, mystery in MYSTERIES.items():
            if mystery.clue_kind not in setting.affords:
                continue
            for t_id, tool in TOOLS.items():
                if mystery.clue_kind in tool.helps:
                    out.append((s_id, m_id, t_id))
    return out


def explain_rejection(setting: Setting, mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {setting.place} does not offer a clear way to solve the "
        f"{mystery.mystery_noun} with {tool.label}. The clue type and tool need to "
        f"match so the adventure can end in a real reveal.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[random.choice(TRAITS), "curious"],
        meters={"brave": 1.0, "tired": 0.0},
        memes={"hope": 1.0, "worry": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["fickle", random.choice(HELPER_TRAITS)],
        meters={"help": 0.0},
        memes={"kindness": 0.0, "fickle": 1.0, "teamwork": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type=mystery.clue_kind,
        label=mystery.mystery_noun,
        phrase=mystery.mystery_noun,
        owner=hero.id,
        caretaker=helper.id,
    ))
    gear = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.label,
        owner=hero.id,
        carried_by=hero.id,
        plural=tool.plural,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        gear=gear,
        mystery=mystery,
        tool=tool,
        setting=setting,
    )
    return world


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who loved adventure, "
        f"and {helper.id} came along with a fickle sort of kindness that changed "
        f"like the wind."
    )
    world.say(
        f"One day, they reached {setting.place} and found a {mystery.mystery_noun} "
        f"that nobody could explain."
    )


def build_turn(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    tool: Entity = f["gear"]
    tool_def: Tool = f["tool"]

    world.para()
    world.say(
        f"{hero.id} wanted to solve the mystery right away, so {hero.pronoun()} "
        f"carried {tool.label} deeper into {world.setting.place}."
    )
    world.say(
        f"{helper.id} tried to help, but their kindness was fickle; one moment "
        f"{helper.pronoun()} smiled, and the next moment {helper.pronoun()} stepped back."
    )
    helper.memes["kindness"] += 1
    helper.memes["fickle"] += 1
    hero.memes["worry"] += 1

    world.say(
        f"Then {hero.id} noticed a clue near {mystery.hiding_place}, but it was "
        f"too dim and tangled to read clearly."
    )
    world.say(
        f"{hero.id} used {tool.label} and {tool_def.use_line}, because the clue "
        f"needed a careful touch."
    )


def resolve(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    tool_def: Tool = f["tool"]

    hero.meters["brave"] += 1
    helper.memes["teamwork"] += 1
    helper.memes["kindness"] += 1

    world.para()
    world.say(
        f"{helper.id} saw how hard {hero.id} was trying, and the fickle mood "
        f"settled into real kindness."
    )
    world.say(
        f"Together they followed the clue until the truth came out: {mystery.reveal}"
    )
    world.say(
        f"{tool_def.final_line} {hero.id} and {helper.id} laughed, because the "
        f"mystery was solved as a team."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    build_turn(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short adventure story for a child where a {mystery.mystery_noun} is solved by teamwork.',
        f"Tell a gentle mystery adventure that includes the word 'fickle' and ends with a clear reveal.",
        f"Write a child-friendly story about kind helpers, a puzzling clue, and a team solving it together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]

    return [
        QAItem(
            question=f"Who went on the adventure to solve the {mystery.mystery_noun}?",
            answer=f"{hero.id} went on the adventure with {helper.id} to solve the mystery together.",
        ),
        QAItem(
            question=f"What made {helper.id}'s kindness a little hard to trust at first?",
            answer=f"{helper.id} was fickle at first, so their kindness changed from one moment to the next.",
        ),
        QAItem(
            question=f"What tool helped them find the clue?",
            answer=f"{tool.label} helped them look carefully and uncover the clue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved and the two teammates laughing together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and work together to do something hard.",
        ),
        QAItem(
            question="What does it mean when someone is fickle?",
            answer="If someone is fickle, their feelings or choices change quickly instead of staying steady.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to understand or solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Utility / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.kind == "character":
            parts.append("character")
        if e.label:
            parts.append(f"label={e.label!r}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: fickle kindness, a mystery to solve, and teamwork.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    if args.setting and args.mystery and args.tool:
        setting = SETTINGS[args.setting]
        mystery = MYSTERIES[args.mystery]
        tool = TOOLS[args.tool]
        if not (mystery.clue_kind in setting.affords and mystery.clue_kind in tool.helps):
            raise StoryError(explain_rejection(setting, mystery, tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    helper_name = args.helper_name or rng.choice(NAMES[helper_type])
    if helper_name == hero_name:
        helper_name = rng.choice([n for n in NAMES[helper_type] if n != hero_name])

    return StoryParams(
        setting=setting,
        mystery=mystery,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# CLI / ASP helpers
# ---------------------------------------------------------------------------

def asp_show_program() -> str:
    return asp_program()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/mystery/tool combos:\n")
        for s, m, t in combos:
            print(f"  {s:8} {m:12} {t}")
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
            header = f"### {p.hero_name}: {p.mystery} at {p.setting} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
