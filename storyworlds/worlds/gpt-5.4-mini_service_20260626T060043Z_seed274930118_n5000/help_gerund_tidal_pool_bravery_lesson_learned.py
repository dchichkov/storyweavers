#!/usr/bin/env python3
"""
storyworlds/worlds/help_gerund_tidal_pool_bravery_lesson_learned.py
===================================================================

A small superhero-style story world set at a tidal pool.

Premise:
- A child hero loves helping by doing a specific gerund action.
- They want to use their powers at the tidal pool.
- Their first choice is too reckless for the fragile pool life.
- A wiser helper offers a safer, braver way.
- The ending proves both bravery and the lesson learned.

This world keeps the prose child-facing and state-driven, with a small causal
model that turns a risky impulse into a better rescue plan.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def display(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the tidal pool"
    tide_state: str = "low tide"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    safe_for: set[str]
    prep: str
    ending: str


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _maybe_mark_rescue(world: World) -> None:
    hero = world.facts["hero"]
    target = world.facts["target"]
    if hero.memes.get("reckless", 0) >= THRESHOLD and target.meters.get("safe", 0) < THRESHOLD:
        if ("panic", target.id) not in world.fired:
            world.fired.add(("panic", target.id))
            target.memes["fear"] = target.memes.get("fear", 0) + 1


def _r_tide_pull(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    target = world.facts["target"]
    act = world.facts["activity"]
    if hero.meters.get(act.id, 0) < THRESHOLD:
        return out
    if target.location != world.setting.place:
        return out
    if target.meters.get("stuck", 0) >= THRESHOLD:
        return out
    sig = ("stuck", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["stuck"] = 1
    out.append(f"The tide tugged hard and left {target.display} stuck in a slick crack.")
    return out


def _r_brave_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    tool = world.facts.get("tool_entity")
    target = world.facts["target"]
    if not tool:
        return out
    if hero.memes.get("caring", 0) < THRESHOLD:
        return out
    if target.meters.get("stuck", 0) < THRESHOLD:
        return out
    sig = ("helped", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["safe"] = 1
    target.meters["stuck"] = 0
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    out.append(f"With {tool.display}, {hero.id} carefully helped {target.display} to safety.")
    return out


CAUSAL_RULES = [_r_tide_pull, _r_brave_help]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            sents = rule(world)
            if sents:
                for s in sents:
                    world.say(s)
                if len(world.fired) != before:
                    changed = True


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[params.trait, "heroic"],
        meters={"hope": 0},
        memes={"caring": 0, "bravery": 0, "reckless": 0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["wise", "steady"],
        meters={"hope": 0},
        memes={"calm": 1},
    ))
    target = world.add(Entity(
        id="starfish",
        kind="character",
        type="starfish",
        label="a little starfish",
        location=setting.place,
        meters={"safe": 0, "stuck": 0},
        memes={"fear": 0},
    ))
    tool_def = TOOLS[params.tool]
    tool = world.add(Entity(
        id=tool_def.id,
        kind="thing",
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        owner=hero.id,
        meters={},
        memes={},
    ))

    world.facts.update(hero=hero, helper=helper, target=target, tool_entity=tool, activity=ACTIVITIES[params.activity])

    hero.memes["caring"] += 1
    hero.memes["reckless"] += 1
    hero.meters[params.activity] = 1

    world.say(f"{hero.id} was a small superhero who loved {ACTIVITIES[params.activity].gerund}.")
    world.say(f"{hero.id}'s bright cape fluttered as {hero.pronoun()} watched over {setting.place}.")
    world.say(f"At the tidal pool, {hero.id} saw {target.display} near a sharp little crack in the rocks.")

    world.para()
    world.say(f"{hero.id} wanted to {ACTIVITIES[params.activity].verb} at once, but that could make the pool splash too wildly.")
    world.say(f"That might leave the tiny sea friend {ACTIVITIES[params.activity].risk}.")

    world.para()
    world.say(f"{helper.id} stepped beside {hero.id} and pointed to {tool_def.label}.")
    world.say(f'"{tool_def.prep}," {helper.id} said. "Being brave can still mean being careful."')
    world.say(f"{hero.id} listened, took a slower breath, and chose the gentler way.")

    propagate(world)

    if target.meters.get("safe", 0) >= THRESHOLD:
        world.para()
        hero.memes["bravery"] += 1
        hero.memes["reckless"] = 0
        hero.meters["lesson"] = 1
        world.say(f"{hero.id} smiled when {target.display} reached the clear water again.")
        world.say(f"That was {hero.id}'s lesson learned: true bravery protects others, too.")
        world.say(f"Together, they stood by the tidal pool while the waves shimmered like silver ribbons.")
    else:
        world.para()
        world.say(f"{hero.id} kept trying, but the rocks were still too slippery.")
        world.say(f"The lesson learned was to slow down and choose a safer rescue next time.")

    world.facts["resolved"] = target.meters.get("safe", 0) >= THRESHOLD
    return world


def prize_at_risk(activity: Activity) -> bool:
    return "tidal_pool" in activity.tags or "water" in activity.tags


def select_tool(activity: Activity) -> Optional[Tool]:
    for tool in TOOLS.values():
        if activity.id in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for tool_id, tool in TOOLS.items():
                if act_id in tool.helps:
                    combos.append((place, act_id, tool_id))
    return combos


def explain_rejection(activity: Activity, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit the danger in {activity.gerund}. "
        f"Try a tool that truly helps with {activity.keyword} at the tidal pool.)"
    )


SETTINGS = {
    "tidal_pool": Setting(place="the tidal pool", tide_state="low tide", affords={"rescue_sweep", "line_pull"}),
    "reef_edge": Setting(place="the reef edge", tide_state="falling tide", affords={"rescue_sweep"}),
    "harbor_wall": Setting(place="the harbor wall", tide_state="high tide", affords={"line_pull"}),
}

ACTIVITIES = {
    "rescue_sweep": Activity(
        id="rescue_sweep",
        verb="sweep the water aside",
        gerund="sweeping away foamy water",
        rush="dash in and splash around",
        risk="more trapped by the rushing water",
        consequence="the tide could shove the little creature deeper into trouble",
        keyword="help-gerund",
        tags={"tidal_pool", "water"},
    ),
    "line_pull": Activity(
        id="line_pull",
        verb="pull the rescue line",
        gerund="pulling a rescue line",
        rush="yank the line wildly",
        risk="tangled in the rope",
        consequence="the rope could snap back and scare everyone",
        keyword="help-gerund",
        tags={"tidal_pool", "water"},
    ),
}

TOOLS = {
    "grip_gloves": Tool(
        id="grip_gloves",
        label="grip gloves",
        phrase="a pair of grip gloves",
        helps={"rescue_sweep"},
        safe_for={"water"},
        prep="put on the grip gloves and use slow hands",
        ending="kept the rescue gentle and sure",
    ),
    "rescue_line": Tool(
        id="rescue_line",
        label="a rescue line",
        phrase="a bright rescue line",
        helps={"line_pull"},
        safe_for={"water"},
        prep="tie the rescue line to the rail and pull it steadily",
        ending="turned a risky tug into a careful rescue",
    ),
}

HERO_NAMES = ["Nova", "Spark", "Comet", "Mira", "Jet", "Echo"]
HELPER_NAMES = ["Captain Tide", "Aunt Beacon", "Professor Pearl", "Guardian Wave"]
TRAITS = ["brave", "kind", "quick", "shining", "steady"]


@dataclass
class StoryConfig:
    place: str
    activity: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world set at a tidal pool.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryConfig:
    if args.activity and args.tool:
        act = ACTIVITIES[args.activity]
        tool = TOOLS[args.tool]
        if args.activity not in tool.helps:
            raise StoryError(explain_rejection(act, tool))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryConfig(place, activity, tool, hero_name, hero_type, helper_name, helper_type, trait)


def generate(params: StoryConfig) -> StorySample:
    world = build_world(StoryParams(
        place=params.place,
        activity=params.activity,
        tool=params.tool,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
        seed=params.seed,
    ))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a superhero story for a child named {hero.id} at the tidal pool that includes "{act.keyword}".',
        f"Tell a brave rescue story where {hero.id} learns a lesson after choosing a safer way to help.",
        f"Write a small superhero tale about helping at {world.setting.place} with courage and care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    target = f["target"]
    act = f["activity"]
    tool = f["tool_entity"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, who loved {act.gerund} at the tidal pool.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice at the tidal pool?",
            answer=f"{hero.id} saw {target.display} stuck near a sharp crack in the rocks.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} solve the problem?",
            answer=f"{helper.id} suggested {tool.label} and a slower, safer rescue so {hero.id} could help without making things worse.",
        ),
        QAItem(
            question=f"What lesson learned did {hero.id} get at the end?",
            answer=f"{hero.id} learned that true bravery means helping carefully and protecting others.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a little pocket of seawater left behind among the rocks when the tide goes out.",
        ),
        QAItem(
            question="Why can tidal pools be tricky places?",
            answer="Tidal pools can be slippery and changing, so you have to move carefully near the rocks and water.",
        ),
        QAItem(
            question="What does bravery mean in this world?",
            answer="Bravery means choosing to help even when something is hard, while still being careful and kind.",
        ),
        QAItem(
            question="What does lesson learned mean here?",
            answer="A lesson learned is the important thing the hero understands after trying, thinking, and doing better the next time.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(tidal_pool).
affords(tidal_pool,rescue_sweep).
affords(tidal_pool,line_pull).

activity(rescue_sweep).
activity(line_pull).

tool(grip_gloves).
tool(rescue_line).

helps(grip_gloves,rescue_sweep).
helps(rescue_line,line_pull).

valid(Place,Act,Tool) :- place(Place), affords(Place,Act), tool(Tool), helps(Tool,Act).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", tid, a))
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
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryConfig("tidal_pool", "rescue_sweep", "grip_gloves", "Nova", "girl", "Captain Tide", "man", "brave"),
    StoryConfig("tidal_pool", "line_pull", "rescue_line", "Mira", "girl", "Aunt Beacon", "woman", "steady"),
    StoryConfig("reef_edge", "rescue_sweep", "grip_gloves", "Comet", "boy", "Professor Pearl", "woman", "kind"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
