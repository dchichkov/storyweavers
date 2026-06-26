#!/usr/bin/env python3
"""
storyworlds/worlds/destruction_causative_architectural_teamwork_rhyming_story.py
===============================================================================

A small storyworld about an architectural project, a destructive mishap, and
a teamwork-based fix, told in a light rhyming-story style.

Seed premise:
- A little crew wants to build something architectural together.
- A causative chain leads to destruction: a strong push, a wrong bump, or a
  loose brace can topple the work.
- The crew then works together to repair or rebuild it.

This world is intentionally small and constraint-checked: the chosen structure
must be something that can be built, damaged, and repaired by a reasonable team
effort.
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
    plural: bool = False
    owner: Optional[str] = None
    builder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Structure:
    id: str
    label: str
    phrase: str
    kind: str
    material: str
    parts: list[str]
    can_be_ruined_by: set[str]
    repair_tool: str
    repair_verb: str
    ending_image: str


@dataclass
class TeamRole:
    name: str
    task: str
    helps_with: str


@dataclass
class StoryParams:
    setting: str
    structure: str
    mishap: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


SETTINGS = {
    "garden": Setting("the garden", "breezy", {"build"}),
    "backyard": Setting("the backyard", "windy", {"build"}),
    "yard": Setting("the yard", "windy", {"build"}),
    "park": Setting("the park", "bright", {"build"}),
}

STRUCTURES = {
    "treehouse": Structure(
        id="treehouse",
        label="treehouse",
        phrase="a tiny treehouse",
        kind="house",
        material="wood",
        parts=["boards", "rope ladder", "roof"],
        can_be_ruined_by={"wind", "bump", "rain"},
        repair_tool="hammer",
        repair_verb="nail back together",
        ending_image="the little treehouse stood straight and snug",
    ),
    "bridge": Structure(
        id="bridge",
        label="bridge",
        phrase="a little bridge",
        kind="bridge",
        material="planks",
        parts=["planks", "rails", "posts"],
        can_be_ruined_by={"wind", "bump", "roll"},
        repair_tool="rope",
        repair_verb="tie back together",
        ending_image="the little bridge stretched safe and strong",
    ),
    "tower": Structure(
        id="tower",
        label="tower",
        phrase="a tall block tower",
        kind="tower",
        material="blocks",
        parts=["blocks", "base", "top"],
        can_be_ruined_by={"bump", "shake", "roll"},
        repair_tool="glue",
        repair_verb="stick back together",
        ending_image="the block tower rose proud and bright",
    ),
}

MISHAPS = {
    "wind": ("a gusty wind", "blew", "knocked"),
    "bump": ("a clumsy bump", "bumped", "tipped"),
    "shake": ("a silly shake", "shook", "jiggled"),
    "roll": ("a rolling ball", "rolled", "bounced"),
    "rain": ("a sudden rain", "poured", "soaked"),
}

HELPERS = {
    "mother": TeamRole("mother", "plans the fixes", "keeps the crew calm"),
    "father": TeamRole("father", "holds the beams", "keeps the crew steady"),
    "friend": TeamRole("friend", "passes the tools", "keeps the crew ready"),
    "sibling": TeamRole("sibling", "brings the nails", "keeps the crew cheery"),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo", "Max", "Ben"]
TRAITS = ["brave", "bright", "cheery", "quick", "kind", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for stname, st in STRUCTURES.items():
            if "build" not in setting.affords:
                continue
            for mname in MISHAPS:
                if mname in st.can_be_ruined_by:
                    out.append((sname, stname, mname))
    return out


def reasonableness_gate(setting: Setting, structure: Structure, mishap: str) -> bool:
    return "build" in setting.affords and mishap in structure.can_be_ruined_by


def explain_rejection(setting: Setting, structure: Structure, mishap: str) -> str:
    return (
        f"(No story: a {mishap} mishap would not reasonably ruin {structure.phrase} "
        f"at {setting.place}, so the causative turn would be weak.)"
    )


def introduce(world: World, hero: Entity, helper: Entity, structure: Entity, role: TeamRole) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes['trait_word']} {hero.type} who loved to build and glow, "
        f"for teamwork made the good days grow."
    )
    world.say(
        f"With {helper.label}, the crew could share the load, "
        f"and {role.task} made the project road."
    )
    world.say(
        f"They dreamed of {structure.phrase}, neat and sweet, "
        f"a tiny architectural treat."
    )


def setup_work(world: World, hero: Entity, helper: Entity, structure: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    structure.meters["built"] += 1
    world.say(
        f"They gathered boards and set them in place, "
        f"with careful hands and smiling face."
    )
    world.say(
        f"One held the base, one fit each part, "
        f"and every snug fit warmed the heart."
    )


def trigger_destruction(world: World, hero: Entity, structure: Entity, mishap: str) -> None:
    kind, cause_verb, damage_verb = MISHAPS[mishap]
    structure.meters["stable"] = 1.0
    hero.memes["worry"] += 1
    world.say(
        f"But then came {kind}, with a tricky way, "
        f"and causative trouble joined the day."
    )
    world.say(
        f"It {cause_verb} the base and {damage_verb} the brace, "
        f"and down went pieces in a heap and haze."
    )
    structure.meters["damaged"] += 1
    structure.meters["destroyed"] += 1
    structure.meters["built"] = max(0.0, structure.meters["built"] - 1.0)
    world.facts["mishap_kind"] = kind
    world.facts["damage_word"] = damage_verb


def teamwork_repair(world: World, hero: Entity, helper: Entity, structure: Entity, role: TeamRole) -> None:
    hero.memes["resolve"] += 1
    helper.memes["resolve"] += 1
    world.say(
        f"{hero.id} did not pout or moan; {hero.pronoun()} called the team to the zone. "
        f"Together they could mend what was thrown."
    )
    world.say(
        f"{helper.label} {role.helps_with}, while {hero.id} worked near, "
        f"and soon the broken pieces did not look so queer."
    )
    world.say(
        f"They used a {structure.facts['tool']} to {structure.facts['repair_verb']}, "
        f"and little by little the cracks were no more."
    )
    structure.meters["destroyed"] = 0.0
    structure.meters["damaged"] = 0.0
    structure.meters["built"] = 2.0
    structure.meters["stable"] = 2.0


def ending(world: World, hero: Entity, helper: Entity, structure: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the soft last light, the {structure.facts['label']} stood tall and bright, "
        f"{structure.facts['ending_image']}."
    )
    world.say(
        f"{hero.id} and {helper.label} shared a happy cheer, "
        f"for teamwork turned the wreck to dear."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    structure_cfg = STRUCTURES[params.structure]
    mishap = params.mishap
    if not reasonableness_gate(setting, structure_cfg, mishap):
        raise StoryError(explain_rejection(setting, structure_cfg, mishap))

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait_word": TRAITS[0], "joy": 0.0, "worry": 0.0, "resolve": 0.0},
    ))
    hero.memes["trait_word"] = random.choice(TRAITS)

    helper_role = HELPERS[params.helper]
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        memes={"joy": 0.0, "resolve": 0.0},
    ))
    structure = world.add(Entity(
        id="structure",
        kind="thing",
        type=structure_cfg.kind,
        label=structure_cfg.label,
        phrase=structure_cfg.phrase,
        owner=hero.id,
        builder=hero.id,
        meters={"built": 0.0, "damaged": 0.0, "destroyed": 0.0, "stable": 0.0},
    ))
    structure.facts = {
        "label": structure_cfg.label,
        "tool": structure_cfg.repair_tool,
        "repair_verb": structure_cfg.repair_verb,
        "ending_image": structure_cfg.ending_image,
    }

    world.facts.update(
        hero=hero,
        helper=helper,
        structure=structure,
        structure_cfg=structure_cfg,
        helper_role=helper_role,
        setting=setting,
        mishap=mishap,
    )

    introduce(world, hero, helper, structure, helper_role)
    world.para()
    setup_work(world, hero, helper, structure)
    world.para()
    trigger_destruction(world, hero, structure, mishap)
    world.para()
    teamwork_repair(world, hero, helper, structure, helper_role)
    world.para()
    ending(world, hero, helper, structure)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cfg: Structure = f["structure_cfg"]
    setting: Setting = f["setting"]
    return [
        f"Write a short rhyming story about {hero.id} building {cfg.phrase} at {setting.place} with teamwork.",
        f"Tell a child-friendly story where a {f['mishap']} causes destruction, but the crew fixes it together.",
        f"Write a simple architectural teamwork story that ends with {cfg.ending_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    structure: Entity = f["structure"]
    cfg: Structure = f["structure_cfg"]
    role: TeamRole = f["helper_role"]
    mishap = f["mishap"]

    return [
        QAItem(
            question=f"What were {hero.id} and {helper.label} building together?",
            answer=f"They were building {cfg.phrase}, a little architectural project made with teamwork.",
        ),
        QAItem(
            question=f"What caused the destruction in the story?",
            answer=f"{MISHAPS[mishap][0].capitalize()} caused the trouble and knocked the project apart.",
        ),
        QAItem(
            question=f"How did they fix the broken {structure.label}?",
            answer=(
                f"They worked together, with {helper.label} helping to {role.helps_with} "
                f"and {hero.id} using a {cfg.repair_tool} to {cfg.repair_verb}."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {cfg.ending_image}, and the team felt happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    cfg: Structure = f["structure_cfg"]
    mishap = f["mishap"]
    helper_role: TeamRole = f["helper_role"]
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and share jobs to reach the same goal.",
        ),
        QAItem(
            question="What does destruction mean?",
            answer="Destruction means something is broken, ruined, or knocked apart.",
        ),
        QAItem(
            question="Why do builders use tools?",
            answer="Builders use tools to fit parts together, hold them in place, or repair what got damaged.",
        ),
        QAItem(
            question=f"Why was {helper_role.name} a good helper?",
            answer=f"{helper_role.name} was a good helper because {helper_role.helps_with}.",
        ),
        QAItem(
            question=f"Why can a {mishap} hurt a {cfg.kind}?",
            answer=f"A {mishap} can hurt a {cfg.kind} because it can knock loose parts out of place.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A structure is valid if the chosen mishap can reasonably destroy it.
valid_story(S, T, M) :- setting(S), structure(T), mishap(M), can_ruin(T, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in STRUCTURES.items():
        lines.append(asp.fact("structure", tid))
        lines.append(asp.fact("can_ruin", tid, *[])) if False else None
        for m in sorted(t.can_be_ruined_by):
            lines.append(asp.fact("can_ruin", tid, m))
    for mid in MISHAPS:
        lines.append(asp.fact("mishap", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about teamwork, architecture, and destruction.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--structure", choices=STRUCTURES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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
              and (args.structure is None or c[1] == args.structure)
              and (args.mishap is None or c[2] == args.mishap)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, structure, mishap = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, structure=structure, mishap=mishap, name=name, gender=gender, helper=helper)


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
    StoryParams(setting="backyard", structure="treehouse", mishap="wind", name="Mia", gender="girl", helper="father"),
    StoryParams(setting="garden", structure="bridge", mishap="roll", name="Leo", gender="boy", helper="mother"),
    StoryParams(setting="park", structure="tower", mishap="bump", name="Nora", gender="girl", helper="sibling"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.structure} with {p.helper} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
