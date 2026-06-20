#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/colony_hose_tire_mystery_to_solve_kindness.py
==============================================================================

A small space-adventure storyworld about a colony, a hose, and a tire mystery.

Premise:
- A child in a moon colony notices a big tire rolling loose near a storage bay.
- A hose is needed for a practical job, but the hose goes missing.
- Kindness turns the mystery into a cooperative search, and the lost item is found.

The world keeps the action physically grounded with meters and emotionally
grounded with memes. The story is not a frozen paragraph with swapped nouns: it
simulates a small problem, a clue trail, a choice to help, and a resolution.

The script supports:
- default random generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

It is self-contained and stdlib-only.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    dark_spot: str
    affordance: str


@dataclass
class Clue:
    id: str
    text: str
    kind: str


@dataclass
class MysteryItem:
    id: str
    label: str
    where: str
    clue: str
    heavy: bool = False
    broken: bool = False


@dataclass
class Tool:
    id: str
    label: str
    use_text: str
    safe: bool = True


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["missing"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__tension__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension), Rule("kindness", "social", _r_kindness)]


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


SETTINGS = {
    "colony": Setting(
        "colony",
        "a bright moon colony",
        "The colony dome glowed silver, and little tunnels linked the garden bay, the storage bay, and the repair nook.",
        "the storage bay",
        "the repair bay",
    ),
    "outpost": Setting(
        "outpost",
        "a tiny asteroid outpost",
        "The outpost hummed softly, and narrow corridors led from the sleeping pods to the tool room and the airlock.",
        "the tool room",
        "the airlock",
    ),
    "station": Setting(
        "station",
        "a busy space station",
        "The station drifted above a blue planet, with long halls, a garden tube, and a machine room full of blinking lights.",
        "the machine room",
        "the garden tube",
    ),
}

CLUES = [
    Clue("dust", "a trail of dusty tracks", "trail"),
    Clue("drip", "a line of wet drops", "water"),
    Clue("scratch", "a scratch mark near the wall", "mark"),
    Clue("echo", "a soft clank echoing from the hall", "sound"),
]

MYSTERY_ITEMS = {
    "hose": MysteryItem("hose", "hose", "the repair nook", "a wet trail and a bendy loop of rubber"),
    "tire": MysteryItem("tire", "tire", "the cargo shelf", "a heavy rolling mark and a round black ring", heavy=True),
    "panel": MysteryItem("panel", "panel", "the wall rack", "a loose edge and a tiny buzzing light", broken=True),
}

TOOLS = {
    "spare_hose": Tool("spare_hose", "spare hose", "used a spare hose to finish the job"),
    "patch_kit": Tool("patch_kit", "patch kit", "patched the problem with careful hands"),
    "tug_line": Tool("tug_line", "tug line", "pulled it back with a steady tug line"),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lina", "Zoe", "Aria", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Kai", "Leo", "Eli", "Taj", "Noah", "Finn", "Omar"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, item in MYSTERY_ITEMS.items():
            for tid, tool in TOOLS.items():
                if sid == "colony" and mid in {"hose", "tire"} and tool.safe:
                    combos.append((sid, mid, tid))
    return combos


def setting_for(story_id: str) -> Setting:
    return SETTINGS[story_id]


def mystery_for(mid: str) -> MysteryItem:
    return MYSTERY_ITEMS[mid]


def tool_for(tid: str) -> Tool:
    return TOOLS[tid]


def tell(setting: Setting, mystery: MysteryItem, tool: Tool, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    colony = world.add(Entity(id="colony", kind="thing", type="place", label="the colony"))
    item = world.add(Entity(id=mystery.id, kind="thing", type="thing", label=mystery.label))
    kind = world.add(Entity(id="kindness", kind="thing", type="idea", label="kindness"))

    child.memes["curiosity"] = 2
    helper.memes["kindness"] = 2
    world.facts.update(setting=setting, mystery=mystery, tool=tool, child=child, helper=helper, colony=colony, item=item)

    world.say(
        f"In {setting.scene}, {setting.place_line} {setting.dark_spot} waited for a small mystery to be solved."
    )
    world.say(
        f"{child_name} and {helper_name} drifted through the dome, their boots tapping softly on the metal floor."
    )
    world.say(
        f'"We need the {mystery.label}," {child_name} said, "but it is not where it should be."'
    )

    world.para()
    child.meters["missing"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"They followed {mystery.clue}. It led past the garden lights, then toward {mystery.where}, where the air smelled faintly of grease and rainwater."
    )
    world.say(
        f"{helper_name} did not laugh at the mistake. Instead, {helper.pronoun()} said, "
        f'"Let us look together. Kind hands find answers faster."'
    )
    propagate(world, narrate=False)
    world.say(
        f"Their careful search found the {mystery.label}, tucked beside a crate, with {mystery.clue} still clinging to it."
    )

    world.para()
    if mystery.id == "hose":
        world.say(
            f"The hose had been curled too tightly, and nobody had noticed it roll away from the repair bay."
        )
        world.say(
            f"{helper_name} used the {tool.label} to finish the job, and the colony's water line began to hum again."
        )
    elif mystery.id == "tire":
        world.say(
            f"The tire had slipped from the cargo shelf when the shuttle shook the hallway."
        )
        world.say(
            f"{helper_name} used the {tool.label} to steady it, and the round tire stopped bumping along the floor."
        )
    else:
        world.say(
            f"The broken panel had hidden a tiny wire gap behind it, and the clue trail made sense at last."
        )
        world.say(
            f"{helper_name} used the {tool.label} to fix it, and the blinking lights on the wall turned calm and blue."
        )

    world.para()
    child.memes["joy"] += 1
    child.memes["kindness"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{child_name} grinned and thanked {helper_name} for being so kind."
    )
    world.say(
        f"By the end, the colony was tidy again, the mystery was solved, and {mystery.label} was back where it belonged."
    )

    world.facts.update(outcome="solved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        f'Write a short space-adventure mystery for a 3-to-5-year-old in {setting.id} that includes the words "colony", "{mystery.label}", and "kindness".',
        f"Tell a gentle story where {child.id} and {helper.id} solve a missing-{mystery.label} mystery in a space colony by being kind and looking together.",
        f'Write a child-friendly story in a moon colony where a lost {mystery.label} is found through clues, teamwork, and kindness.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who solved a small mystery in the colony together. Their kindness helped them stay calm and work as a team."),
        ("What was missing?",
         f"The {mystery.label} was missing. They found it by following a clue trail and looking carefully in the colony."),
        ("How did kindness help?",
         f"{helper.id} was kind instead of teasing, so the search stayed calm and helpful. Because they worked together, they found the missing {mystery.label} faster."),
        ("Where did the story happen?",
         f"It happened in {setting.id}, a space colony with quiet halls, a garden, and places to fix things. That setting made the mystery feel like a little space adventure."),
        ("How did the story end?",
         f"The mystery was solved, the missing {mystery.label} was back where it belonged, and the colony felt peaceful again. The final scene shows them smiling after the job was done."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    items = [
        QAItem("What is a colony?", "A colony is a place where people live together in a new area, like on the Moon or in space. It has homes, work places, and shared spaces."),
        QAItem("What is kindness?", "Kindness means being gentle, helpful, and caring to others. It can mean sharing, listening, and helping solve problems."),
        QAItem("What is a hose?", "A hose is a long tube that carries water or air from one place to another. People use hoses for watering, cleaning, and repairs."),
        QAItem("What is a tire?", "A tire is a round rubber ring that helps a wheel roll smoothly. Cars, carts, and space gear can use tires or tire-like wheels."),
    ]
    if mystery.id == "hose":
        items.append(QAItem("Why can a hose matter in a colony?", "A hose can carry water for cleaning or repairs. In a colony, that helps keep systems working and people safe."))
    elif mystery.id == "tire":
        items.append(QAItem("Why can a tire be heavy?", "A tire is made of thick rubber and sometimes metal inside. That makes it strong enough to roll, but also heavy to lift."))
    return items


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.tool and args.mystery and (args.tool not in TOOLS or args.mystery not in MYSTERY_ITEMS):
        raise StoryError("(No valid combination matches the given options.)")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting = args.setting or rng.choice([c[0] for c in combos])
    mystery = args.mystery or rng.choice([c[1] for c in combos if c[0] == setting])
    tool = args.tool or rng.choice([c[2] for c in combos if c[0] == setting and c[1] == mystery])
    if args.setting and args.mystery and args.tool and (args.setting, args.mystery, args.tool) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("girl" if child_gender == "boy" and rng.random() < 0.5 else "boy")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child]
    helper = args.helper or rng.choice(helper_pool)
    return StoryParams(setting, mystery, tool, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(setting_for(params.setting), mystery_for(params.mystery), tool_for(params.tool),
                 params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
missing(H) :- child(H), needs_help(H).
kindness(H) :- helper(H), kind(H).
solved :- kindness(_), found(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERY_ITEMS:
        lines.append(asp.fact("mystery", mid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("needs_help", "child"))
    lines.append(asp.fact("kind", "helper"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    rc = 0
    import asp
    if not valid_combos():
        print("MISMATCH: no Python combos generated.")
        return 1
    model = asp.one_model(asp_program("#show setting/1.\n"))
    if model is None:
        print("MISMATCH: ASP produced no model.")
        rc = 1
    try:
        sample = generate(StoryParams("colony", "hose", "spare_hose", "Mina", "girl", "Kai", "boy"))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery storyworld about colony, hose, tire, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERY_ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    return valid_story_params(args, rng)


def CURATED = [
    StoryParams("colony", "hose", "spare_hose", "Mina", "girl", "Kai", "boy"),
    StoryParams("colony", "tire", "tug_line", "Leo", "boy", "Nora", "girl"),
    StoryParams("station", "hose", "patch_kit", "Ivy", "girl", "Omar", "boy"),
]


def _curated() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show setting/1.\n#show mystery/1.\n#show tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos:")
        for s, m, t in valid_combos():
            print(f"  {s:8} {m:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in _curated()]
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
