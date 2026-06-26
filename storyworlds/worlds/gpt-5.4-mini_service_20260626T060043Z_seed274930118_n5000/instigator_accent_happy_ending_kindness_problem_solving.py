#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/instigator_accent_happy_ending_kindness_problem_solving.py
==============================================================================================================

A small adventure story world about a kind-hearted explorer, an instigator with
a distinctive accent, a problem that grows from a misunderstanding, and a happy
ending earned through kindness and problem solving.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    accent: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the mountain trail"
    detail: str = "The path wound between rocks and wild flowers."


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    obstacle: str
    success_image: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    used_for: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

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


THRESHOLD = 1.0


@dataclass
class StoryParams:
    setting: str
    quest: str
    tool: str
    hero_name: str
    hero_type: str
    instigator_name: str
    instigator_type: str
    accent: str
    seed: Optional[int] = None


SETTINGS = {
    "trail": Setting(
        place="the mountain trail",
        detail="The trail climbed past pine trees and a bright little bridge.",
    ),
    "cave": Setting(
        place="the lantern cave",
        detail="The cave walls glittered where old lantern light touched the stone.",
    ),
    "harbor": Setting(
        place="the harbor path",
        detail="Waves tapped the docks, and gulls called above the water.",
    ),
}

QUESTS = {
    "bridge": Quest(
        id="bridge",
        goal="cross the old bridge",
        verb="cross the old bridge",
        obstacle="the bridge was blocked by a fallen crate",
        success_image="they crossed safely together",
        keyword="bridge",
        tags={"water", "wood", "teamwork"},
    ),
    "lantern": Quest(
        id="lantern",
        goal="find the lost lantern",
        verb="search for the lost lantern",
        obstacle="the lantern had rolled behind a narrow stone shelf",
        success_image="the lantern glowed warmly in their hands",
        keyword="lantern",
        tags={"light", "stone", "search"},
    ),
    "map": Quest(
        id="map",
        goal="deliver the map",
        verb="deliver the map to the lookout",
        obstacle="the map sleeve had torn in the wind",
        success_image="the lookout held the repaired map high with a smile",
        keyword="map",
        tags={"paper", "wind", "repair"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a coil of rope",
        phrase="a sturdy coil of rope",
        helps={"bridge"},
        used_for={"pull", "tie", "carry"},
    ),
    "lamp": Tool(
        id="lamp",
        label="a brass lamp",
        phrase="a small brass lamp with a bright flame",
        helps={"lantern"},
        used_for={"light", "search"},
    ),
    "patchkit": Tool(
        id="patchkit",
        label="a patch kit",
        phrase="a neat little patch kit",
        helps={"map"},
        used_for={"repair", "fix"},
    ),
}

HERO_NAMES = ["Mina", "Taro", "Elin", "Jonah", "Sora", "Iris", "Noah", "Pia"]
INSTIGATOR_NAMES = ["Rook", "Nera", "Vik", "Luma", "Pell", "Zed"]
ACCENTS = [
    "a sing-song accent",
    "a rough mountain accent",
    "a soft seaside accent",
    "a clipped court accent",
    "a warm traveling accent",
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for quest_id in setting_to_quests(setting_id):
            for tool_id, tool in TOOLS.items():
                if quest_id in tool.helps:
                    out.append((setting_id, quest_id, tool_id))
    return out


def setting_to_quests(setting_id: str) -> list[str]:
    if setting_id == "trail":
        return ["bridge", "map"]
    if setting_id == "cave":
        return ["lantern", "map"]
    return ["bridge", "lantern"]


def choose_instigator_accent() -> str:
    return random.choice(ACCENTS)


def _do_quest(world: World, hero: Entity, quest: Quest, tool: Tool, narrate: bool = True) -> None:
    hero.meters["resolve"] = hero.meters.get("resolve", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.facts["success"] = quest.id in tool.helps
    if narrate:
        world.say(f"{hero.id} used {tool.label} to face the {quest.goal}.")


def predict_outcome(world: World, hero: Entity, quest: Quest, tool: Tool) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, tool, narrate=False)
    return {
        "solved": quest.id in tool.helps,
        "calm": sim.get(hero.id).meters.get("resolve", 0.0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, instigator: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a brave little {hero.type} who loved adventure, quiet paths, "
        f"and solving hard problems."
    )
    world.say(
        f"One morning, {hero.id} set out toward {world.setting.place} to {quest.verb}."
    )


def problem(world: World, hero: Entity, instigator: Entity, quest: Quest) -> None:
    instigator.memes["mischief"] = instigator.memes.get("mischief", 0.0) + 1.0
    world.say(
        f"Near the trail, {instigator.id} called out with {instigator.accent}, "
        f"and the words sounded stranger than they meant to."
    )
    world.say(
        f"{hero.id} heard the voice, paused, and thought there might be trouble."
    )
    world.say(f"Then {quest.obstacle}.")


def kindness(world: World, hero: Entity, instigator: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    instigator.memes["worry"] = instigator.memes.get("worry", 0.0) + 1.0
    world.say(
        f"Instead of snapping back, {hero.id} took a slow breath and answered kindly."
    )
    world.say(
        f"{hero.id} asked {instigator.id} to explain again, and the two of them listened carefully."
    )


def solve(world: World, hero: Entity, instigator: Entity, quest: Quest, tool: Tool) -> None:
    outcome = predict_outcome(world, hero, quest, tool)
    if not outcome["solved"]:
        raise StoryError("The chosen tool does not fit this quest.")

    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    instigator.memes["kindness"] = instigator.memes.get("kindness", 0.0) + 1.0

    world.say(
        f"Together, they used {tool.phrase} and worked out a careful plan."
    )
    world.say(
        f"With patience and problem solving, {quest.success_image}."
    )
    world.say(
        f"{hero.id} smiled at {instigator.id}, and the strange voice now sounded friendly."
    )


def tell(setting: Setting, quest: Quest, tool: Tool, hero_name: str, hero_type: str,
         instigator_name: str, instigator_type: str, accent: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["kind", "bold"],
    ))
    instigator = world.add(Entity(
        id=instigator_name,
        kind="character",
        type=instigator_type,
        accent=accent,
        traits=["mysterious", "shy"],
    ))
    world.facts.update(hero=hero, instigator=instigator, quest=quest, tool=tool, setting=setting)

    introduce(world, hero, instigator, quest)
    world.say(setting.detail)
    world.para()
    problem(world, hero, instigator, quest)
    kindness(world, hero, instigator)
    world.para()
    solve(world, hero, instigator, quest, tool)
    world.say("By sunset, the path felt safe again, and everyone went home with a happy ending.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Registries and generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle adventure story for a young child that includes an instigator with {f["instigator"].accent}.',
        f"Tell a story where {f['hero'].id} meets {f['instigator'].id} at {f['setting'].place} and solves a problem with kindness.",
        f'Create a short adventure about "{f["quest"].keyword}" that ends in a happy ending after problem solving.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    instigator = f["instigator"]
    quest = f["quest"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who went on the adventure in the story?",
            answer=f"{hero.id} went on the adventure and tried to {quest.verb}.",
        ),
        QAItem(
            question=f"What made the voice sound unusual near {world.setting.place}?",
            answer=f"The voice sounded unusual because {instigator.id} spoke with {instigator.accent}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help solve the problem?",
            answer=f"{hero.id} used {tool.phrase} to solve the problem together with {instigator.id}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the problem solved and everyone feeling safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about other people.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully, trying ideas, and working out a good answer.",
        ),
        QAItem(
            question="What is an accent?",
            answer="An accent is a special way people speak words, often because of where they come from.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.accent:
            bits.append(f"accent={ent.accent!r}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Setting,Quest,Tool) :- setting(Setting), quest(Quest), tool(Tool), helps(Tool, Quest).
"""


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
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with kindness, problem solving, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--type", dest="hero_type", choices=["girl", "boy"])
    ap.add_argument("--instigator-name")
    ap.add_argument("--instigator-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--accent", choices=ACCENTS)
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
    if args.setting or args.quest or args.tool:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.quest is None or c[1] == args.quest)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, quest, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    instigator_type = args.instigator_type or rng.choice(["girl", "boy", "woman", "man"])
    instigator_name = args.instigator_name or rng.choice(INSTIGATOR_NAMES)
    accent = args.accent or rng.choice(ACCENTS)
    return StoryParams(
        setting=setting,
        quest=quest,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        instigator_name=instigator_name,
        instigator_type=instigator_type,
        accent=accent,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_type,
        params.instigator_name,
        params.instigator_type,
        params.accent,
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


CURATED = [
    StoryParams(
        setting="trail",
        quest="bridge",
        tool="rope",
        hero_name="Mina",
        hero_type="girl",
        instigator_name="Rook",
        instigator_type="man",
        accent="a rough mountain accent",
    ),
    StoryParams(
        setting="cave",
        quest="lantern",
        tool="lamp",
        hero_name="Taro",
        hero_type="boy",
        instigator_name="Nera",
        instigator_type="woman",
        accent="a soft seaside accent",
    ),
    StoryParams(
        setting="harbor",
        quest="map",
        tool="patchkit",
        hero_name="Iris",
        hero_type="girl",
        instigator_name="Vik",
        instigator_type="boy",
        accent="a sing-song accent",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for qid in setting_to_quests(sid):
            for tid, tool in TOOLS.items():
                if qid in tool.helps:
                    out.append((sid, qid, tid))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, quest, tool) combos:\n")
        for s, q, t in triples:
            print(f"  {s:8} {q:8} {t:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
