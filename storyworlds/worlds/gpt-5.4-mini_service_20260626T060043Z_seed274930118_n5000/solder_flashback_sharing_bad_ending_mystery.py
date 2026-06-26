#!/usr/bin/env python3
"""
storyworlds/worlds/solder_flashback_sharing_bad_ending_mystery.py
=================================================================

A small storyworld about a curious child, a broken metal keepsake, and a
mystery solved by sharing a clue and remembering a flashback.

Premise:
- A child finds a little metal object with a cracked seam.
- The object smells faintly like solder and old dust.
- A helper remembers a flashback about who last handled it.
- The truth is shared, and the mystery is solved.

Narrative instruments:
- Flashback: a remembered scene reveals the missing clue.
- Sharing: one character shares the clue, tool, or truth with another.
- Bad Ending: the ending is bittersweet; the mystery is solved, but the object
  cannot be restored all the way, so the final image is a careful loss.

This script follows the Storyweavers standalone world contract.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "mystery": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "share": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the attic"
    afford_mystery: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    material: str
    smell: str
    break_kind: str
    repairable: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    helps_with: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_seen = False
        self.shared = False
        self.solved = False
        self.bad_ending = False

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


SETTINGS = {
    "attic": Setting(place="the attic", afford_mystery=True),
    "workbench": Setting(place="the old workbench", afford_mystery=True),
    "shed": Setting(place="the shed", afford_mystery=True),
}

CLUES = {
    "music_box": Clue(
        id="music_box",
        label="music box",
        phrase="a tiny silver music box",
        material="metal",
        smell="like hot solder and dust",
        break_kind="cracked seam",
        repairable=True,
    ),
    "toy_robot": Clue(
        id="toy_robot",
        label="toy robot",
        phrase="a little tin robot",
        material="tin",
        smell="like oil and warm metal",
        break_kind="split joint",
        repairable=True,
    ),
    "lantern": Clue(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        material="brass",
        smell="like smoke and old cloth",
        break_kind="bent handle",
        repairable=True,
    ),
}

TOOLS = {
    "soldering_iron": Tool(
        id="soldering_iron",
        label="soldering iron",
        phrase="a warm soldering iron",
        action="solder the seam shut",
        helps_with={"cracked seam", "split joint"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        action="look closely at the crack",
        helps_with={"cracked seam", "split joint", "bent handle"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        action="shine into the corners",
        helps_with={"missing piece"},
    ),
    "gloves": Tool(
        id="gloves",
        label="work gloves",
        phrase="a pair of work gloves",
        action="hold the cold metal safely",
        helps_with={"cracked seam", "split joint", "bent handle"},
    ),
}

NAMES_GIRL = ["Maya", "Lena", "Iris", "Nina", "Tia", "Zoe", "June", "Nora"]
NAMES_BOY = ["Eli", "Finn", "Leo", "Max", "Owen", "Toby", "Sam", "Noah"]
TRAITS = ["curious", "quiet", "brave", "careful", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                if any(kind in TOOLS[t].helps_with for kind in {CLUES[c].break_kind, "missing piece"}) or t in {"magnifier", "flashlight"}:
                    combos.append((s, c, t))
    return combos


def prize_at_risk(clue: Clue, tool: Tool) -> bool:
    return clue.repairable and clue.break_kind in tool.helps_with


def select_tool(clue: Clue) -> Optional[Tool]:
    for tool in TOOLS.values():
        if prize_at_risk(clue, tool):
            return tool
    return None


def explain_rejection(clue: Clue) -> str:
    return (
        f"(No story: the {clue.label} has a {clue.break_kind}, but none of the tools can "
        f"honestly help with that problem.)"
    )


def introduce(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type} "
        f"who liked quiet places and puzzling out broken things."
    )
    world.say(
        f"One day, {hero.id} found {hero.pronoun('possessive')} {clue.label} in {world.setting.place}, "
        f"and the metal seam looked wrong."
    )
    clue.meters["damage"] += 1
    clue.memes["mystery"] += 1
    hero.memes["curiosity"] += 1
    helper.memes["worry"] += 1


def clue_detail(world: World, clue: Entity) -> None:
    world.say(
        f"It smelled {CLUES[clue.type].smell}, and a thin dark line ran across the broken part."
    )


def flashback(world: World, helper: Entity, clue: Entity) -> None:
    world.para()
    world.flashback_seen = True
    world.say(
        f"Then {helper.id} had a sudden flashback: yesterday, {helper.pronoun()} had heard a tiny snap "
        f"when {clue.id} was moved off a shelf."
    )
    world.say(
        f"In the flashback, {helper.id} saw {helper.pronoun('possessive')} own hand bump the box, and a tiny piece fall away."
    )


def share_clue(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    world.para()
    world.shared = True
    hero.memes["share"] += 1
    helper.memes["share"] += 1
    world.say(
        f"{helper.id} shared the flashback with {hero.id}, and {hero.id} shared the magnifying glass back without asking twice."
    )
    world.say(
        f"Together they held the {clue.label} under the light and looked for the missing piece."
    )


def solve_mystery(world: World, hero: Entity, helper: Entity, clue: Entity, tool: Entity) -> None:
    world.solved = True
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"The clue was simple at last: the {clue.label} had been cracked when it slipped from the shelf."
    )
    world.say(
        f"{hero.id} used the {tool.label} to repair what could be repaired, and the seam closed with a faint silver line."
    )


def bad_ending(world: World, clue: Entity) -> None:
    world.bad_ending = True
    clue.meters["damage"] += 1
    world.para()
    world.say(
        f"But the ending was still a little sad: the broken piece was too tiny to find, so the {clue.label} could never sing exactly the same way again."
    )
    world.say(
        f"{clue.id} sat on the table in the attic, quiet and whole enough to keep, but not whole enough to forget."
    )


def tell(setting: Setting, clue_cfg: Clue, tool_cfg: Tool, hero_name: str, hero_type: str,
         helper_type: str, hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious"])))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, traits=["gentle"]))
    clue = world.add(Entity(id=clue_cfg.id, type=clue_cfg.id, label=clue_cfg.label, phrase=clue_cfg.phrase, owner=hero.id))

    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=helper.id))
    world.facts.update(hero=hero, helper=helper, clue=clue, tool=tool, setting=setting, clue_cfg=clue_cfg, tool_cfg=tool_cfg)

    introduce(world, hero, helper, clue)
    clue_detail(world, clue)
    flashback(world, helper, clue)
    share_clue(world, hero, helper, clue)
    solve_mystery(world, hero, helper, clue, tool)
    bad_ending(world, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, clue = f["hero"], f["helper"], f["clue_cfg"]
    return [
        f'Write a short mystery story for a child where {hero.id} finds a broken {clue.label} and a flashback helps solve it.',
        f"Tell a gentle story about {hero.id} and {helper.id} sharing a clue in {world.setting.place}, with a sad but clear ending.",
        f'Write a simple story that includes the word "solder" and ends with a bittersweet repaired object in an attic-like place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, clue, tool = f["hero"], f["helper"], f["clue"], f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {hero.pronoun('possessive')} {clue.label}, and the broken seam made it look mysterious.",
        ),
        QAItem(
            question=f"Who remembered the flashback and shared it with {hero.id}?",
            answer=f"{helper.id} remembered the flashback, then shared the truth with {hero.id} so they could solve the mystery together.",
        ),
        QAItem(
            question=f"What tool helped repair the broken {clue.label}?",
            answer=f"The {tool.label} helped because it could work on the cracked seam and make the metal join again.",
        ),
        QAItem(
            question=f"Why was the ending sad?",
            answer=f"The ending was sad because the lost tiny piece could not be found, so the {clue.label} could be repaired only partway.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is solder?",
            answer="Solder is a metal material that melts when it is heated and helps join broken metal parts together.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a remembered scene from earlier that helps explain something happening now.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving someone else a clue, tool, or idea so you can work together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    lines.append(f"  shared={world.shared}")
    lines.append(f"  solved={world.solved}")
    lines.append(f"  bad_ending={world.bad_ending}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(attic).
setting(workbench).
setting(shed).

clue(music_box).
clue(toy_robot).
clue(lantern).

tool(soldering_iron).
tool(magnifier).
tool(flashlight).
tool(gloves).

break_kind(music_box, cracked_seam).
break_kind(toy_robot, split_joint).
break_kind(lantern, bent_handle).

helps(soldering_iron, cracked_seam).
helps(soldering_iron, split_joint).
helps(magnifier, cracked_seam).
helps(magnifier, split_joint).
helps(magnifier, bent_handle).
helps(flashlight, missing_piece).
helps(gloves, cracked_seam).
helps(gloves, split_joint).
helps(gloves, bent_handle).

valid_combo(S, C, T) :- setting(S), clue(C), tool(T),
    break_kind(C, K), helps(T, K).
#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("break_kind", cid, CLUES[cid].break_kind))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        for k in sorted(TOOLS[tid].helps_with):
            lines.append(asp.fact("helps", tid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with solder, flashbacks, sharing, and a bittersweet ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
    if args.clue and args.tool:
        clue, tool = CLUES[args.clue], TOOLS[args.tool]
        if not prize_at_risk(clue, tool):
            raise StoryError(explain_rejection(clue))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], TOOLS[params.tool], params.name,
                 "girl" if params.gender == "girl" else "boy", params.helper, [params.trait, "little"])
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(setting="attic", clue="music_box", tool="soldering_iron", name="Maya", gender="girl", helper="aunt", trait="curious"),
    StoryParams(setting="workbench", clue="toy_robot", tool="magnifier", name="Eli", gender="boy", helper="father", trait="thoughtful"),
    StoryParams(setting="shed", clue="lantern", tool="gloves", name="Nora", gender="girl", helper="mother", trait="careful"),
]


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, tool) combos:\n")
        for s, c, t in combos:
            print(f"  {s:10} {c:12} {t}")
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
