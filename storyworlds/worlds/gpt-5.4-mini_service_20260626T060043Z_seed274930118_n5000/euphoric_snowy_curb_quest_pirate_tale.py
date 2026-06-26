#!/usr/bin/env python3
"""
storyworlds/worlds/euphoric_snowy_curb_quest_pirate_tale.py
===========================================================

A small story world for a pirate-style quest on a snowy curb.

Premise:
- A cheerful pirate crew discovers a glittering quest object at the curb.
- Snow and slush threaten their gear and their prize.
- The crew must choose a careful route and a fitting tool to finish the quest.

The world is state-driven:
- physical meters track cold, wet, and heft
- emotional memes track eagerness, worry, and euphoric joy
- narration follows the simulated turn from problem to resolution
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["cold", "wet", "heft", "snow", "dirty"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "euphoria", "curiosity", "bond"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the snowy curb"
    snow_depth: str = "fresh"


@dataclass
class Quest:
    id: str
    noun: str
    phrase: str
    risk: str
    at_risk_region: str
    weather: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.curb: dict[str, bool] = {"icy": True, "snowy": True}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.curb = copy.deepcopy(self.curb)
        return clone


def _r_weather(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        sig = ("weather", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["cold"] += 1
        out.append(f"The cold bit {actor.id}'s cheeks a little harder.")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD or not world.curb["icy"]:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"The icy curb made the step feel tricky.")
    return out


CAUSAL_RULES = [
    ("weather", _r_weather),
    ("slip", _r_slip),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(quest: Quest, tool: Tool) -> bool:
    return quest.at_risk_region in tool.covers or quest.at_risk_region == "hands"


def select_tool(quest: Quest, tool_catalog: list[Tool]) -> Optional[Tool]:
    for tool in tool_catalog:
        if quest.risk in tool.guards and quest.at_risk_region in tool.covers:
            return tool
    return None


def predict(world: World, hero: Entity, quest: Quest) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["wet"] += 1
    propagate(sim, narrate=False)
    return {
        "cold": sim.get(hero.id).meters["cold"],
        "worry": sim.get(hero.id).memes["worry"],
    }


def introduce(world: World, hero: Entity, mate: Entity, quest: Quest) -> None:
    world.say(
        f"On the snowy curb, {hero.id} was a {hero.traits[0]} pirate with a bright grin "
        f"and a heart full of euphoria."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {mate.id} loved a good quest, especially one that sparkled "
        f"near the curb where the snow curled like white foam."
    )
    world.say(
        f"That day, they were after {quest.phrase}, a little prize that looked like it had been left "
        f"there just for bold sailors."
    )


def arrive(world: World, hero: Entity, mate: Entity) -> None:
    world.say(
        f"The two friends padded to {world.setting.place}, where the snow was soft on top but slippery underneath."
    )


def want(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1
    hero.memes["euphoria"] += 1
    world.say(f"{hero.id} wanted to start the quest at once and reach the shiny prize before the wind changed its mind.")


def warn(world: World, mate: Entity, hero: Entity, quest: Quest) -> bool:
    pred = predict(world, hero, quest)
    if pred["cold"] < THRESHOLD and pred["worry"] < THRESHOLD:
        return False
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"'{hero.id}, your boots will get wet on that icy curb,' {mate.id} said. "
        f"'Then your toes will feel cold, and the quest may turn grumpy.'"
    )
    return True


def defy(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["joy"] += 0.5
    world.say(f"{hero.id} still leaned forward, eager as a gull spotting a crumb.")


def choose_tool(world: World, hero: Entity, mate: Entity, quest: Quest) -> Optional[Tool]:
    tool = select_tool(quest, TOOLS)
    if tool is None:
        return None
    created = world.add(Entity(
        id=tool.id,
        type="gear",
        label=tool.label,
        owner=hero.id,
        caretaker=mate.id,
        protective=True,
        covers=set(tool.covers),
        plural=tool.plural,
    ))
    created.worn_by = hero.id
    world.say(
        f"Then {mate.id} lifted {tool.label} and said, '{tool.prep} and we can still finish the quest safely.'"
    )
    return tool


def accept(world: World, hero: Entity, mate: Entity, quest: Quest, tool: Tool) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["euphoria"] += 2
    mate.memes["bond"] += 1
    world.say(
        f"{hero.id} beamed and nodded. Soon they {tool.tail}, and the snowy curb quest felt easy as singing."
    )
    world.say(
        f"At the end, {hero.id} reached {quest.phrase}, and the prize stayed safe and dry while the two pirates laughed in the cold air."
    )


SETTING = Setting(place="the snowy curb", snow_depth="fresh")

QUESTS = {
    "shell": Quest(
        id="shell",
        noun="shell",
        phrase="a silver shell charm",
        risk="wet",
        at_risk_region="feet",
        weather="snowy",
        keyword="quest",
        tags={"shell", "wet"},
    ),
    "map": Quest(
        id="map",
        noun="map",
        phrase="a curled treasure map",
        risk="snow",
        at_risk_region="hands",
        weather="snowy",
        keyword="quest",
        tags={"map", "snow"},
    ),
    "key": Quest(
        id="key",
        noun="key",
        phrase="a small brass key",
        risk="dirty",
        at_risk_region="hands",
        weather="snowy",
        keyword="quest",
        tags={"key", "snow"},
    ),
}

TOOLS = [
    Tool(
        id="boots",
        label="warm sea boots",
        covers={"feet"},
        guards={"wet", "snow"},
        prep="put on warm sea boots first",
        tail="walked back to the curb in the warm sea boots",
    ),
    Tool(
        id="mittens",
        label="thick mittens",
        covers={"hands"},
        guards={"snow", "dirty"},
        prep="pull on thick mittens first",
        tail="went back with the thick mittens snug on",
        plural=True,
    ),
    Tool(
        id="cloak",
        label="a wool cloak",
        covers={"hands", "feet"},
        guards={"wet", "snow", "dirty"},
        prep="wrap in a wool cloak and keep the prize tucked close",
        tail="returned in the wool cloak, ready for the quest",
    ),
]

GIRL_NAMES = ["Mira", "Nina", "Tessa", "Lumi"]
BOY_NAMES = ["Finn", "Pip", "Jory", "Kai"]
TRAITS = ["euphoric", "brave", "spry", "cheery"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    mate: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for qid, q in QUESTS.items():
        if select_tool(q, TOOLS) is not None:
            combos.append((SETTING.place, qid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale quest on a snowy curb.")
    ap.add_argument("--place", choices=["curb"])
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--mate")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest:
        q = QUESTS[args.quest]
        if select_tool(q, TOOLS) is None:
            raise StoryError("No reasonable pirate tool can protect that quest on the snowy curb.")
    combos = [c for c in valid_combos() if (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid quest matches the given options.)")
    _, quest_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    mate = args.mate or rng.choice(["Matey", "Captain Tide", "Old Salt"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="curb", quest=quest_id, name=name, mate=mate, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="pirate", traits=[params.trait]))
    mate = world.add(Entity(id=params.mate, kind="character", type="pirate", traits=["helpful"]))
    quest = QUESTS[params.quest]
    world.facts.update(hero=hero, mate=mate, quest=quest)

    introduce(world, hero, mate, quest)
    world.para()
    arrive(world, hero, mate)
    want(world, hero, quest)
    warn(world, mate, hero, quest)
    defy(world, hero)
    world.para()
    tool = choose_tool(world, hero, mate, quest)
    if tool:
        accept(world, hero, mate, quest, tool)
    world.facts["tool"] = tool
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mate, quest = f["hero"], f["mate"], f["quest"]
    return [
        f'Write a short pirate tale for a child about a euphoric quest at a snowy curb.',
        f"Tell a gentle story where {hero.id} and {mate.id} chase {quest.phrase} without getting too cold.",
        f'Write a simple quest story that includes the word "euphoric" and ends with a safe, happy pirate choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, quest = f["hero"], f["mate"], f["quest"]
    tool = f.get("tool")
    out = [
        QAItem(
            question=f"Who was on the snowy curb quest?",
            answer=f"{hero.id} and {mate.id} were on the quest, and {hero.id} was the pirate who felt especially euphoric.",
        ),
        QAItem(
            question=f"What prize were they trying to reach?",
            answer=f"They were trying to reach {quest.phrase} at the snowy curb.",
        ),
        QAItem(
            question=f"Why did the matey pirate warn {hero.id}?",
            answer=f"{mate.id} warned {hero.id} because the snowy curb was icy and {quest.risk} could make the plan harder.",
        ),
    ]
    if tool is not None:
        out.append(
            QAItem(
                question=f"How did {tool.label} help the quest?",
                answer=f"{tool.label.capitalize()} helped by protecting the right part of the body so {hero.id} could finish the quest without trouble.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, where someone travels or tries hard to find or finish it.",
        ),
        QAItem(
            question="Why can snowy ground be slippery?",
            answer="Snowy ground can be slippery because snow can turn to ice or wet slush, and feet may slide on it.",
        ),
        QAItem(
            question="What does euphoric mean?",
            answer="Euphoric means extremely happy and excited, like a feeling that makes someone want to smile and cheer.",
        ),
        QAItem(
            question="What are mittens for?",
            answer="Mittens keep hands warm by covering the fingers together in one soft layer.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A quest is at risk when the tool or route does not protect the vulnerable region.
quest_at_risk(Q, R) :- quest(Q), risky_region(Q, R).

% A tool is compatible when it guards the risky material and covers the region.
compatible(T, Q) :- tool(T), quest(Q), guards(T, M), risk_of(Q, M), covers(T, R), risky_region(Q, R).

valid_story(Q) :- quest(Q), compatible(_, Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "curb"))
    lines.append(asp.fact("place", "snowy_curb"))
    lines.append(asp.fact("curb", "icy"))
    lines.append(asp.fact("curb", "snowy"))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk_of", qid, q.risk))
        lines.append(asp.fact("risky_region", qid, q.at_risk_region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {q for _, q in valid_combos()}
    clingo = {q for (q,) in asp_valid_stories()}
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} quests).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python only:", sorted(py - clingo))
    print("clingo only:", sorted(clingo - py))
    return 1


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
    StoryParams(place="curb", quest="shell", name="Mira", mate="Captain Tide", trait="euphoric"),
    StoryParams(place="curb", quest="map", name="Finn", mate="Old Salt", trait="brave"),
    StoryParams(place="curb", quest="key", name="Lumi", mate="Matey", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p}" for p in asp_valid_stories()))
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
            header = f"### {p.name}: {p.quest} on the snowy curb"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
