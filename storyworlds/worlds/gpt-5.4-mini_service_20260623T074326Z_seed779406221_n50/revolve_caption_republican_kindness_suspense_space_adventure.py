#!/usr/bin/env python3
"""
A standalone storyworld: revolving space adventure, a lost caption, and a
republican-coded signal badge that must be used kindly under suspense.

The premise is a small moon-base expedition where one child wants to make a
drifting station panel revolve by hand, another notices a missing caption on the
mission display, and the crew must choose a calm, kind fix before the whole
module drifts into darkness.

The world is intentionally tiny: a few typed entities, physical meters, and
emotional memes drive a complete child-facing story with a beginning, middle
turn, and resolution image.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    id: str
    setting: str
    ship: str
    goal: str
    dark_place: str
    revolve_thing: str
    caption_item: str
    feel: str
    ending: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SCENES = {
    "orbit": Scene(
        id="orbit",
        setting="a bright moon station",
        ship="the docking ring",
        goal="the observatory",
        dark_place="the shadow side of the ring",
        revolve_thing="the outer hatch",
        caption_item="the mission caption",
        feel="a calm spin",
        ending="the station turning softly above the moon",
    ),
    "asteroid": Scene(
        id="asteroid",
        setting="a tiny asteroid base",
        ship="the shelter dome",
        goal="the sky window",
        dark_place="the tunnel corner",
        revolve_thing="the old solar dish",
        caption_item="the display caption",
        feel="a slow sway",
        ending="the base glowing under the stars",
    ),
}

TOOLS = {
    "spinhandle": Tool("spinhandle", "spin handle", "a spin handle", "by the lock"),
    "captioncard": Tool("captioncard", "caption card", "a caption card", "on the control shelf", safe=True),
    "signalbadge": Tool("signalbadge", "republican signal badge", "a republican signal badge", "in the kit", safe=True,
                        tags={"republican"}),
}

FIXES = {
    "steady": Fix(
        "steady", 3, 3,
        "steadied the panel with a gentle grip and lined the caption back up",
        "tried to steady it, but the panel was already slipping too fast",
        "fixed the panel and put the caption back in place",
        tags={"kindness"},
    ),
    "mark": Fix(
        "mark", 3, 2,
        "used the caption card to mark the words clearly and kept the panel from wobbling",
        "used the card, but the words still drifted out of sight",
        "used the caption card to make the words clear again",
        tags={"kindness"},
    ),
    "brace": Fix(
        "brace", 2, 2,
        "braced the wheel and slowed the spin long enough to read the caption",
        "braced the wheel, but the spin was too wild to hold",
        "braced the wheel and slowed the spin",
    ),
}

NAMES = ["Ava", "Milo", "Nora", "Theo", "Lina", "Zane", "Maya", "Owen"]
TRAITS = ["kind", "careful", "patient", "gentle"]


@dataclass
class StoryParams:
    scene: str
    tool: str
    fix: str
    captain: str
    helper: str
    captain_type: str
    helper_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def hazard(tool: Tool) -> bool:
    return tool.id == "spinhandle"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 3]


def story_outcome(params: StoryParams) -> str:
    sc = SCENES[params.scene]
    fx = FIXES[params.fix]
    return "contained" if fx.power >= 2 + params.delay else "spun"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not hazard(TOOLS[args.tool]):
        raise StoryError("This story needs the spin handle so the suspense can begin.")
    if args.fix and FIXES[args.fix].sense < 3:
        raise StoryError("Choose a kinder, wiser fix.")
    scene = args.scene or rng.choice(list(SCENES))
    tool = args.tool or "spinhandle"
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    captain = rng.choice(NAMES)
    helper = rng.choice([n for n in NAMES if n != captain])
    captain_type = rng.choice(["girl", "boy"])
    helper_type = "girl" if captain_type == "boy" else "boy"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(scene, tool, fix, captain, helper, captain_type, helper_type, trait, delay)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.safe:
            lines.append(asp.fact("safe", tid))
        if "republican" in tool.tags:
            lines.append(asp.fact("tagged", tid, "republican"))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
hazard(T) :- tool(T), not safe(T).
outcome(contained) :- fix(F), power(F,P), delay(D), P >= 2 + D.
outcome(spun) :- fix(F), power(F,P), delay(D), P < 2 + D.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1.\n#show outcome/1."))
    asp_sens = sorted(x[0] for x in asp.atoms(model, "sensible"))
    py_sens = sorted(f.id for f in sensible_fixes())
    ok = 0
    if asp_sens != py_sens:
        print("MISMATCH sensible:", asp_sens, py_sens)
        ok = 1
    return ok


def render_story(world: World, params: StoryParams) -> None:
    sc = SCENES[params.scene]
    captain = world.get("captain")
    helper = world.get("helper")
    tool = TOOLS[params.tool]
    fx = FIXES[params.fix]
    world.say(
        f"At {sc.setting}, {captain.id} and {helper.id} were on a small space adventure."
        f" They wanted to reach {sc.goal}, where {sc.caption_item} could guide them."
    )
    world.say(
        f"But the path near {sc.dark_place} was dim, and {sc.feel} made everything feel suspenseful."
    )
    captain.memes["curiosity"] = 1
    helper.memes["kindness"] = 1
    world.say(
        f"{captain.id} noticed {tool.phrase} and wanted to make {sc.revolve_thing} revolve faster."
        f" {helper.id} noticed that the words on the screen were drifting away."
    )
    world.say(
        f'"If we spin it too hard, we might lose the caption," {helper.id} said softly.'
        f" {captain.id} looked at {helper.id} and slowed down."
    )
    if params.delay > 0:
        captain.memes["worry"] = params.delay
    if fx.power >= 2 + params.delay:
        world.say(
            f"{helper.id} used {tool.label} kindly, then {fx.text}."
            f" The panel held steady, and the caption came back clear."
        )
        world.get("panel").meters["spin"] = 0
        world.get("panel").meters["safety"] = 1
        world.get("caption").meters["visible"] = 1
        world.say(
            f"Together they followed the bright caption to {sc.goal}, and the station settled into {sc.ending}."
        )
    else:
        world.say(
            f"{helper.id} tried to help, but {fx.fail}."
            f" The panel kept spinning and the caption slipped out of sight."
        )
        world.get("panel").meters["spin"] = 2
        world.get("caption").meters["visible"] = 0
        world.say(
            f"They called for a grown-up, held on tight, and waited until the ship stopped wobbling."
        )
        world.say(
            f"After that, the quiet crew wrote a new caption card and kept it safe for the next flight."
        )


def generate(params: StoryParams) -> StorySample:
    world = World()
    captain = world.add(Entity("captain", "character", params.captain_type, role="captain"))
    helper = world.add(Entity("helper", "character", params.helper_type, role="helper"))
    world.add(Entity("panel", "thing", "panel"))
    world.add(Entity("caption", "thing", "caption"))
    world.facts["scene"] = SCENES[params.scene]
    world.facts["tool"] = TOOLS[params.tool]
    world.facts["fix"] = FIXES[params.fix]
    world.facts["delay"] = params.delay
    render_story(world, params)
    outcome = story_outcome(params)
    prompts = [
        f"Write a space-adventure story where {params.captain} and {params.helper} try to make something revolve, but keep the ending kind.",
        f"Tell a suspenseful moon-base story that includes a caption, a republican signal badge, and a gentle fix.",
        f"Make a child-facing story about kindness under suspense on a space station.",
    ]
    story_qa = [
        QAItem(
            question="What did the children want the revolving part to do?",
            answer=f"They wanted {SCENES[params.scene].revolve_thing} to revolve so they could reach {SCENES[params.scene].goal}.",
        ),
        QAItem(
            question="What was missing or drifting on the screen?",
            answer=f"The caption was drifting, so the words were hard to read.",
        ),
        QAItem(
            question="How did the helper show kindness?",
            answer=f"{params.helper} spoke softly, warned about the caption, and helped in a careful way.",
        ),
        QAItem(
            question="What made the story suspenseful?",
            answer=f"The dark place near the station and the possibility of losing the caption made the moment suspenseful.",
        ),
    ]
    if outcome == "contained":
        story_qa.append(QAItem(
            question="How did the story end?",
            answer="They kept the panel steady, saved the caption, and reached the goal safely.",
        ))
    else:
        story_qa.append(QAItem(
            question="How did the story end?",
            answer="They had to stop, call for help, and make a new plan before they could continue.",
        ))
    world_qa = [
        QAItem(
            question="What does a caption do?",
            answer="A caption gives words that explain what you are seeing or guide you toward the next step.",
        ),
        QAItem(
            question="Why is kindness important in a space adventure?",
            answer="Kindness helps the crew share, warn each other, and stay calm when things feel scary.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for ent in sample.world.entities.values():
            print(ent.id, ent.kind, ent.type, ent.meters, ent.memes, ent.role)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(scene=s, tool="spinhandle", fix=f, captain="Ava", helper="Milo",
                        captain_type="girl", helper_type="boy", trait="kind", delay=0)
            for s in SCENES for f in sensible_fixes()
        ]
        samples = [generate(p) for p in combos]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
