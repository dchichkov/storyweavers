#!/usr/bin/env python3
"""
storyworlds/worlds/chump_queer_proper_inner_monologue_quest_adventure.py
=======================================================================

A standalone story world for a tiny adventure tale about a chump who feels
queer about a proper quest, thinks hard in an inner monologue, and finishes
with a clear, state-driven change.

Premise sketch:
- A small adventurer, called a chump by others at first, is sent on a proper
  quest to deliver a lantern key across a narrow bridge.
- The chump feels queer about the task: uneasy, curious, and a little out of
  place.
- Inner monologue matters. The character weighs the risk, remembers a helper's
  advice, and chooses a careful method.
- The quest succeeds when the chump uses the right tool, crosses the place, and
  proves that being proper can still mean being brave.

This world keeps to the Storyweavers contract:
- stdlib-only script
- imports results eagerly
- ASP twin with facts and inline rules
- story state drives prose and QA
- invalid choices raise StoryError with a clear reason
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
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass(frozen=True)
class Setting:
    place: str
    detail: str
    affords: set[str]


@dataclass(frozen=True)
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    region: str


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    glow: str
    tags: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters.get("worry", 0) < THRESHOLD:
        return out
    sig = ("wobble", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    out.append("The path felt even stranger now.")
    return out


def _r_tool_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    tool = world.entities.get("tool")
    goal = world.entities.get("goal")
    if not hero or not tool or not goal:
        return out
    if hero.meters.get("prepared", 0) < THRESHOLD:
        return out
    if tool.id in world.fired:
        return out
    if tool.attrs.get("used") != "yes":
        return out
    world.fired.add((tool.id, "help"))
    goal.meters["safe"] = 1
    out.append("The proper tool made the task feel steady.")
    return out


CAUSAL_RULES = [_r_wobble, _r_tool_help]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def quest_at_risk(quest: QuestItem) -> bool:
    return quest.region in {"rope", "bridge", "water"}


def fits_tool(tool: Tool, quest: QuestItem) -> bool:
    return quest.risk == tool.helps and quest.region == "bridge"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for quest_id, quest in QUESTS.items():
            for tool_id, tool in TOOLS.items():
                if quest_at_risk(quest) and fits_tool(tool, quest) and setting.place in {"the old bridge", "the city gate", "the hill path"}:
                    combos.append((setting_id, quest_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    tool: str
    hero_name: str
    hero_type: str
    guide_name: str
    guide_type: str
    mood: str
    seed: Optional[int] = None


SETTINGS = {
    "bridge": Setting(
        place="the old bridge",
        detail="The old bridge shivered over the water, with boards that creaked in the wind.",
        affords={"cross", "deliver"},
    ),
    "gate": Setting(
        place="the city gate",
        detail="The city gate stood tall and proper, with a brass latch and a watchful arch.",
        affords={"cross", "deliver"},
    ),
    "hill": Setting(
        place="the hill path",
        detail="The hill path bent through grass and stones, bright under a wide sky.",
        affords={"cross", "deliver"},
    ),
}

QUESTS = {
    "lantern_key": QuestItem(
        id="lantern_key",
        label="lantern key",
        phrase="a small lantern key",
        risk="slip",
        region="bridge",
    ),
    "map_scroll": QuestItem(
        id="map_scroll",
        label="map scroll",
        phrase="a rolled map scroll",
        risk="bend",
        region="bridge",
    ),
    "river_charm": QuestItem(
        id="river_charm",
        label="river charm",
        phrase="a silver river charm",
        risk="lose",
        region="bridge",
    ),
}

TOOLS = {
    "rope_loop": Tool(
        id="rope_loop",
        label="rope loop",
        phrase="a looped rope",
        helps="slip",
        glow="held tight in the hand",
        tags={"rope", "bridge"},
    ),
    "flat_case": Tool(
        id="flat_case",
        label="flat case",
        phrase="a flat case",
        helps="bend",
        glow="kept the scroll flat",
        tags={"case", "paper"},
    ),
    "pouch_clip": Tool(
        id="pouch_clip",
        label="pouch clip",
        phrase="a pouch clip",
        helps="lose",
        glow="fastened the charm in place",
        tags={"clip", "metal"},
    ),
}

HERO_NAMES = ["Nia", "Rin", "Milo", "Pip", "Tess", "Jory", "Lena", "Otto"]
GUIDE_NAMES = ["Ari", "Bee", "June", "Mara", "Sol", "Rowan"]
MOODS = ["queer", "nervous", "curious", "proper", "thoughtful"]


def explain_rejection(quest: QuestItem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not properly answer the risk of {quest.label}."
        f" The quest needs a tool that really fits the hazard and the bridge.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny adventure story world about a proper quest, inner monologue, and a queer feeling of worry."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--mood", choices=MOODS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.tool:
        if not fits_tool(TOOLS[args.tool], QUESTS[args.quest]):
            raise StoryError(explain_rejection(QUESTS[args.quest], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    mood = args.mood or rng.choice(MOODS)
    hero_type = rng.choice(["boy", "girl"])
    guide_type = rng.choice(["boy", "girl"])
    return StoryParams(setting, quest, tool, name, hero_type, guide, guide_type, mood)


def introduce(world: World, hero: Entity, guide: Entity, quest: QuestItem, tool: Tool) -> None:
    hero.memes["curiosity"] = 1
    world.say(
        f"{hero.name} was a small adventurer who had been called a chump once or twice, "
        f"but {hero.pronoun()} kept the label tucked away and listened to the road."
    )
    world.say(
        f"{guide.name} came with a proper quest: carry {quest.phrase} across {world.setting.place}."
    )


def monologue(world: World, hero: Entity, quest: QuestItem, tool: Tool) -> None:
    hero.meters["worry"] = hero.meters.get("worry", 0) + 1
    world.say(
        f"{hero.name} looked at {world.setting.place} and thought, "
        f'"This feels queer in my chest, like a door I have not opened yet."'
    )
    world.say(
        f'"If I rush, {quest.label} could {quest.risk}, but if I choose proper, '
        f'I can still finish the quest," {hero.pronoun()} told {hero.pronoun("object")}self.'
    )


def choose_tool(world: World, hero: Entity, guide: Entity, tool: Tool) -> None:
    hero.meters["prepared"] = 1
    tool.attrs["used"] = "yes"
    world.say(
        f"{guide.name} handed over {tool.phrase}. It {tool.glow}, and that made the task feel more proper."
    )
    world.say(
        f"{hero.name} breathed in, held the {tool.label}, and decided to cross slowly."
    )


def complete_quest(world: World, hero: Entity, quest: QuestItem) -> None:
    goal = world.get("goal")
    goal.meters["safe"] = 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"At last, {hero.name} crossed {world.setting.place} with steady steps and delivered {quest.phrase}."
    )
    world.say(
        f"The {quest.label} stayed safe, and the whole road seemed less strange than before."
    )


def tell(setting: Setting, quest: QuestItem, tool: Tool,
         hero_name: str = "Nia", hero_type: str = "girl",
         guide_name: str = "Ari", guide_type: str = "boy",
         mood: str = "queer") -> World:
    world = World(setting)
    hero = world.add(Entity("hero", kind="character", type=hero_type, label=hero_name))
    guide = world.add(Entity("guide", kind="character", type=guide_type, label=guide_name))
    world.add(Entity("goal", kind="thing", type="thing", label=quest.label))
    world.add(Entity("tool", kind="thing", type="thing", label=tool.label))
    world.facts["quest"] = quest
    world.facts["tool"] = tool
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["mood"] = mood

    introduce(world, hero, guide, quest, tool)
    world.para()
    monologue(world, hero, quest, tool)
    choose_tool(world, hero, guide, tool)
    propagate(world)
    world.para()
    complete_quest(world, hero, quest)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child about a proper quest using the word "{f["mood"]}".',
        f"Tell a story where {f['hero'].label} has an inner monologue before crossing {world.setting.place} to deliver {f['quest'].label}.",
        f"Write a quest story where a small chump proves steady and brave with {f['tool'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, quest, tool = f["hero"], f["guide"], f["quest"], f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=(
                f"It is about {hero.label}, a small adventurer on a proper quest, and {guide.label}, who helped with the plan."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} think about before crossing {world.setting.place}?",
            answer=(
                f"{hero.label} thought the place felt queer and a little strange, then reminded {hero.pronoun('object')}self that the proper way was still the brave way."
            ),
        ),
        QAItem(
            question=f"What helped {hero.label} finish the quest?",
            answer=(
                f"{guide.label} gave {hero.label} {tool.phrase}, and that let the journey stay proper while {quest.label} was carried safely across."
            ),
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=(
                f"At the start, the crossing felt uneasy. By the end, {hero.label} had delivered {quest.phrase} and felt proud and steady."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a job or journey with a goal to reach, often with a few hard steps along the way.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that helps you think, plan, and decide what to do next.",
        ),
        QAItem(
            question="What does proper mean in this story?",
            answer="Proper means careful, correct, and fitting the task. It helps the character choose the right way to act.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_at_risk(Q) :- quest(Q), risk(Q, R), region(Q, R).
tool_fits(T, Q) :- tool(T), quest(Q), risk(Q, R), helps(T, R), bridge_region(Q).
valid_story(S, Q, T) :- setting(S), quest(Q), tool(T), quest_at_risk(Q), tool_fits(T, Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk", qid, q.risk))
        lines.append(asp.fact("region", qid, q.region))
        lines.append(asp.fact("bridge_region", qid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, t.helps))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: chump, queer, proper, inner monologue, quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--mood", choices=MOODS)
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


def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, tool = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        quest=quest,
        tool=tool,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=rng.choice(["boy", "girl"]),
        guide_name=args.guide or rng.choice(GUIDE_NAMES),
        guide_type=rng.choice(["boy", "girl"]),
        mood=args.mood or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        mood=params.mood,
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
    StoryParams("bridge", "lantern_key", "rope_loop", "Nia", "girl", "Ari", "boy", "queer"),
    StoryParams("gate", "map_scroll", "flat_case", "Milo", "boy", "Bee", "girl", "proper"),
    StoryParams("hill", "river_charm", "pouch_clip", "Tess", "girl", "Sol", "boy", "thoughtful"),
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.hero_name}: {p.quest} at {p.setting} ({p.mood})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
