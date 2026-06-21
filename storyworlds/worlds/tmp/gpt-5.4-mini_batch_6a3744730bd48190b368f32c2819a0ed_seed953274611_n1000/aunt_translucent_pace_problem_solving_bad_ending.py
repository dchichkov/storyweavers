#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aunt_translucent_pace_problem_solving_bad_ending.py
====================================================================================

A tiny folk-tale storyworld about a brave child, a thoughtful aunt, and a
problem that asks for careful solving but ends badly anyway.

Seed words:
- aunt
- translucent
- pace

Features:
- Problem Solving
- Bad Ending
- Bravery

Style:
- Folk Tale

The world is intentionally small: a child and an aunt set out on a moonlit errand
for a folk-tale token. A translucent obstacle blocks the way. The child tries to
solve the problem bravely, but the chosen plan fails, leaving a bad ending image
that proves what changed.

This file is self-contained and follows the shared Storyweavers result/ASP
contract.
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
BRAVERY_START = 5.0
PACE_LIMIT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0, "damp": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "hope": 0.0, "worry": 0.0, "grief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "aunt", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


@dataclass
class Setting:
    id: str
    place: str
    season: str
    mood: str


@dataclass
class Obstacle:
    id: str
    label: str
    translucent: bool
    fragile: bool
    pace_sensitive: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    method: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "old_road"
    obstacle: str = "glass_ford"
    tool: str = "lantern_pole"
    child_name: str = "Mara"
    child_gender: str = "girl"
    aunt_name: str = "Aunt Wren"
    aunt_gender: str = "woman"
    seed: Optional[int] = None


SETTINGS = {
    "old_road": Setting(id="old_road", place="the old road by the reeds", season="autumn", mood="quiet"),
    "moon_lane": Setting(id="moon_lane", place="the moon lane under the hill", season="winter", mood="still"),
    "riverbank": Setting(id="riverbank", place="the riverbank near the willow tree", season="spring", mood="soft"),
}

OBSTACLES = {
    "glass_ford": Obstacle(
        id="glass_ford",
        label="translucent ford",
        translucent=True,
        fragile=True,
        pace_sensitive=True,
        tags={"translucent", "river", "glass"},
    ),
    "ice_gate": Obstacle(
        id="ice_gate",
        label="translucent ice gate",
        translucent=True,
        fragile=True,
        pace_sensitive=True,
        tags={"translucent", "ice"},
    ),
    "mist_wall": Obstacle(
        id="mist_wall",
        label="translucent mist wall",
        translucent=True,
        fragile=False,
        pace_sensitive=True,
        tags={"translucent", "mist"},
    ),
}

TOOLS = {
    "lantern_pole": Tool(
        id="lantern_pole",
        label="lantern on a pole",
        method="held the light high and marked the stones one by one",
        power=1,
        tags={"light", "pole"},
    ),
    "reed_bridge": Tool(
        id="reed_bridge",
        label="reed bundle",
        method="tied reeds together into a tiny bridge",
        power=1,
        tags={"reeds"},
    ),
    "stone_step": Tool(
        id="stone_step",
        label="stepping stones",
        method="placed flat stones across the water",
        power=0,
        tags={"stones"},
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Ivy", "Tess", "Nora"]
BOY_NAMES = ["Bram", "Otto", "Pelle", "Jon", "Rafe"]
AUNT_NAMES = ["Aunt Wren", "Aunt Sora", "Aunt Elspeth", "Aunt Mabel"]
TRAITS = ["brave", "steady", "curious", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid, obstacle in OBSTACLES.items():
            for tid, tool in TOOLS.items():
                if obstacle.translucent and obstacle.pace_sensitive and tool.power >= 0:
                    combos.append((sid, oid, tid))
    return combos


def _build_person(world: World, pid: str, name: str, gender: str, role: str, trait: str) -> Entity:
    ent = world.add(
        Entity(
            id=pid,
            kind="character",
            type=gender,
            label=name,
            role=role,
            traits=[trait],
        )
    )
    ent.memes["bravery"] = BRAVERY_START if role == "child" else 3.0
    return ent


def _setting_line(setting: Setting) -> str:
    return f"Along {setting.place}, the air was {setting.mood} in the {setting.season} dusk."


def _need_line(child: Entity, setting: Setting, obstacle: Obstacle) -> str:
    return f"{child.label_word} came to the {setting.place} and saw a {obstacle.label} shining ahead."


def _pace_warning(world: World, aunt: Entity, child: Entity, obstacle: Obstacle) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{aunt.label_word} lifted a hand. \"Go slow,\" she said. \"This place asks for a careful pace, "
        f"and that translucent way may break if you rush it.\""
    )


def _problem_solve(world: World, child: Entity, tool: Tool) -> None:
    child.memes["hope"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{child.label_word} drew a brave breath and chose a plan. With {tool.label}, "
        f"{tool.method}."
    )


def _bad_end(world: World, child: Entity, aunt: Entity, obstacle: Obstacle) -> None:
    child.meters["damage"] += 1
    child.meters["wear"] += 1
    child.memes["grief"] += 2
    aunt.memes["grief"] += 1
    world.say(
        f"But the {obstacle.label} shivered, cracked, and gave way all at once."
    )
    world.say(
        f"{child.label_word} splashed into the cold water below, and the brave little plan was lost."
    )
    world.say(
        f"{aunt.label_word} reached out too late, and they both stood on the bank with wet hems and heavy hearts."
    )


def tell(setting: Setting, obstacle: Obstacle, tool: Tool, child_name: str,
         child_gender: str, aunt_name: str, aunt_gender: str) -> World:
    world = World()
    child = _build_person(world, "child", child_name, child_gender, "child", "brave")
    aunt = _build_person(world, "aunt", aunt_name, aunt_gender, "aunt", "steady")
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="thing",
            label=obstacle.label,
            attrs={"translucent": obstacle.translucent, "fragile": obstacle.fragile},
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="thing",
            label=tool.label,
            attrs={"method": tool.method},
        )
    )

    world.say(_setting_line(setting))
    world.say(
        f"{child.label_word} walked at a quick pace beside {aunt.label_word}, both of them listening to the hush of the road."
    )
    world.say(_need_line(child, setting, obstacle))
    world.para()

    _pace_warning(world, aunt, child, obstacle)
    world.say(
        f"{child.label_word} nodded, but the wish to prove {child.pronoun('possessive')} bravery kept tugging at {child.pronoun('possessive')} sleeves."
    )
    _problem_solve(world, child, tool)
    world.para()
    _bad_end(world, child, aunt, obstacle)

    world.say(
        f"When the moon climbed higher, the road stayed empty, the lantern went dark, and the two of them went home with no treasure at all."
    )

    world.facts.update(
        setting=setting,
        obstacle=obstacle,
        tool=tool,
        child=child,
        aunt=aunt,
        outcome="bad",
        pace="quick",
        translucent=obstacle.translucent,
        brave=child.memes["bravery"] >= BRAVERY_START,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk-tale story for a young child about {f['child'].label_word} and {f['aunt'].label_word}, using the words aunt, translucent, and pace.",
        f"Tell a brave-but-sad story where {f['child'].label_word} tries to solve a problem near a translucent obstacle, but the plan fails and ends badly.",
        "Write a short folk tale about bravery and a problem-solving idea that does not work, so the ending feels heavy and quiet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    aunt: Entity = f["aunt"]
    obstacle: Obstacle = f["obstacle"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label_word} and {aunt.label_word}. They walk together through a folk-tale place and face a hard problem."
        ),
        QAItem(
            question="What did the aunt warn about?",
            answer=f"{aunt.label_word} warned that the {obstacle.label} needed a careful pace. She knew the translucent crossing could break if anyone rushed."
        ),
        QAItem(
            question="What happened when the child tried to solve the problem?",
            answer=f"{child.label_word} tried a brave plan, but it failed when the {obstacle.label} cracked. The problem was not solved, and the ending turned sad."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does translucent mean?",
            answer="Translucent means you can see light through something, but not clearly all the way. It looks bright and hazy at the same time."
        ),
        QAItem(
            question="What is a pace?",
            answer="A pace is the way someone steps or moves. A slow pace can be careful, while a quick pace can be risky."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means being willing to face something scary. A brave person may still need to choose wisely, though."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.label_word if e.label else e.id} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs a translucent obstacle and a problem-solving route that can still end badly.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about aunt, translucent, and pace."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--aunt-name")
    ap.add_argument("--aunt-gender", choices=["woman", "girl"])
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
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError(explain_rejection())
    setting, obstacle, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    aunt_gender = args.aunt_gender or "woman"
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    aunt_name = args.aunt_name or rng.choice(AUNT_NAMES)
    return StoryParams(
        setting=setting,
        obstacle=obstacle,
        tool=tool,
        child_name=child_name,
        child_gender=child_gender,
        aunt_name=aunt_name,
        aunt_gender=aunt_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.obstacle not in OBSTACLES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        OBSTACLES[params.obstacle],
        TOOLS[params.tool],
        params.child_name,
        params.child_gender,
        params.aunt_name,
        params.aunt_gender,
    )
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
setting(S) :- input_setting(S).
obstacle(O) :- input_obstacle(O).
tool(T) :- input_tool(T).
valid(S,O,T) :- setting(S), obstacle(O), tool(T), translucent(O), pace_sensitive(O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("input_setting", sid))
    for oid, ob in OBSTACLES.items():
        lines.append(asp.fact("input_obstacle", oid))
        if ob.translucent:
            lines.append(asp.fact("translucent", oid))
        if ob.pace_sensitive:
            lines.append(asp.fact("pace_sensitive", oid))
    for tid in TOOLS:
        lines.append(asp.fact("input_tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, obstacle=None, tool=None, child_name=None, child_gender=None, aunt_name=None, aunt_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(
        setting="old_road",
        obstacle="glass_ford",
        tool="lantern_pole",
        child_name="Mara",
        child_gender="girl",
        aunt_name="Aunt Wren",
        aunt_gender="woman",
    ),
    StoryParams(
        setting="moon_lane",
        obstacle="ice_gate",
        tool="reed_bridge",
        child_name="Bram",
        child_gender="boy",
        aunt_name="Aunt Sora",
        aunt_gender="woman",
    ),
    StoryParams(
        setting="riverbank",
        obstacle="mist_wall",
        tool="stone_step",
        child_name="Ivy",
        child_gender="girl",
        aunt_name="Aunt Mabel",
        aunt_gender="woman",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, o, t in combos:
            print(f"  {s:12} {o:14} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
