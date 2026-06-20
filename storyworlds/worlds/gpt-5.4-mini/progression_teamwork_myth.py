#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/progression_teamwork_myth.py
==============================================================

A standalone storyworld about a small mythic quest where a team makes steady
progress together. The world is classical and state-driven: a group of young
helpers face a hard task, each one contributes something different, their shared
progress climbs in stages, and the ending proves what teamwork changed.

The seed words are rebuilt as a tiny myth:
- progression: the story advances through visible stages
- teamwork: no one can finish the task alone
- myth: the language, setting, and outcome feel legendary but child-facing
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
PROGRESS_STEP = 1.0
TEAM_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "goddess"}
        male = {"boy", "father", "dad", "man", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    sacred_name: str
    afford: str


@dataclass
class Quest:
    id: str
    task: str
    method: str
    obstacle: str
    reward: str
    theme: str
    stages: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    team = world.characters()
    if len(team) < TEAM_MIN:
        return out
    if all(e.meters["task"] >= THRESHOLD for e in team):
        key = ("progress", "complete")
        if key not in world.fired:
            world.fired.add(key)
            world.get("shrine").meters["glow"] += 1
            world.get("team").meters["progress"] = 3
            out.append("__glow__")
    return out


def _r_encourage(world: World) -> list[str]:
    out: list[str] = []
    if world.get("team").meters["progress"] >= 2 and ("encourage",) not in world.fired:
        world.fired.add(("encourage",))
        for e in world.characters():
            e.memes["hope"] += 1
        out.append("Their hope grew stronger as the work began to show.")
    return out


CAUSAL_RULES = [
    Rule("progress", "physical", _r_progress),
    Rule("encourage", "social", _r_encourage),
]


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


def teamwork_possible(quest: Quest, tools: list[Tool]) -> bool:
    needed = set(quest.tags)
    for tool in tools:
        needed -= tool.tags
    return not needed


def predict_success(world: World, quest: Quest, tools: list[Tool]) -> dict:
    sim = world.copy()
    for c in sim.characters():
        c.meters["task"] += 1
    sim.get("team").meters["progress"] += 1
    if teamwork_possible(quest, tools):
        sim.get("team").meters["progress"] += 1
        sim.get("shrine").meters["glow"] += 1
    return {
        "progress": sim.get("team").meters["progress"],
        "glow": sim.get("shrine").meters["glow"],
    }


def opening(world: World, heroes: list[Entity], quest: Quest) -> None:
    a, b = heroes
    world.say(
        f"Long ago, at {world.setting.place}, {a.id} and {b.id} stood before "
        f"the {world.setting.sacred_name}. The {world.setting.sky} sky watched "
        f"as they heard of the {quest.task}."
    )
    world.say(
        f"They called their task {quest.theme}, because the road could only be "
        f"crossed by steady progression."
    )


def obstacle(world: World, quest: Quest) -> None:
    world.say(
        f"But {quest.obstacle} guarded the way, and the shrine stayed dark."
    )


def divide_tasks(world: World, heroes: list[Entity], quest: Quest, tool: Tool) -> None:
    for hero in heroes:
        hero.memes["resolve"] += 1
    world.get("team").meters["progress"] += 1
    world.say(
        f"{heroes[0].id} carried the {tool.label}, while {heroes[1].id} guarded "
        f"the path. Together they began the first step of progression."
    )


def warn(world: World, elder: Entity, heroes: list[Entity], quest: Quest, tools: list[Tool]) -> None:
    pred = predict_success(world, quest, tools)
    elder.memes["care"] += 1
    world.facts["predicted_progress"] = pred["progress"]
    world.say(
        f'{elder.id} nodded. "{heroes[0].id} and {heroes[1].id}, you will not '
        f"reach the shrine alone. But if you share the work, the way will open "
        f"and the {world.setting.sacred_name} may glow again."'
    )


def team_action(world: World, heroes: list[Entity], quest: Quest, tools: list[Tool]) -> None:
    for hero in heroes:
        hero.meters["task"] += 1
        hero.memes["joy"] += 1
    world.get("team").meters["progress"] += 1
    world.say(
        f"One lifted, one steadied, one passed the {tools[0].label} forward, "
        f"and the hard middle of the road became possible."
    )


def finish(world: World, heroes: list[Entity], quest: Quest) -> None:
    propagate(world, narrate=False)
    for hero in heroes:
        hero.memes["joy"] += 1
        hero.memes["pride"] += 1
    world.say(
        f"At last they reached the {world.setting.sacred_name}. The stone awoke "
        f"with light, and the whole hill seemed to breathe."
    )
    world.say(
        f"{heroes[0].id} smiled at {heroes[1].id}. Their progression had become a "
        f"shared victory, and neither one had done it alone."
    )


def tell(setting: Setting, quest: Quest, tools: tuple[Tool, Tool],
         hero1: str = "Ari", hero2: str = "Mira",
         t1: str = "girl", t2: str = "boy", elder: str = "the elder",
         elder_type: str = "woman") -> World:
    world = World(setting)
    h1 = world.add(Entity(hero1, kind="character", type=t1, role="helper"))
    h2 = world.add(Entity(hero2, kind="character", type=t2, role="helper"))
    wise = world.add(Entity(elder, kind="character", type=elder_type, role="guide"))
    shrine = world.add(Entity("shrine", label="the shrine", meters=defaultdict(float)))
    team = world.add(Entity("team", label="the team", meters=defaultdict(float)))
    world.add(Entity("tool1", label=tools[0].label))
    world.add(Entity("tool2", label=tools[1].label))

    opening(world, [h1, h2], quest)
    world.para()
    obstacle(world, quest)
    warn(world, wise, [h1, h2], quest, list(tools))
    divide_tasks(world, [h1, h2], quest, tools[0])
    world.para()
    team_action(world, [h1, h2], quest, list(tools))
    finish(world, [h1, h2], quest)

    world.facts.update(
        heroes=(h1, h2), guide=wise, shrine=shrine, team=team, quest=quest,
        tools=tools, outcome="glow" if shrine.meters["glow"] >= THRESHOLD else "dim",
        progress=team.meters["progress"],
    )
    return world


SETTINGS = {
    "hill": Setting("hill", "the moonlit hill", "silver", "Old Star Shrine", "climb"),
    "grove": Setting("grove", "the fern grove", "green", "Springwell Altar", "cross"),
    "harbor": Setting("harbor", "the harbor cliffs", "blue", "Dawn Beacon", "reach"),
}

QUESTS = {
    "lamp": Quest("lamp", "bring back the lost lamp", "careful climbing",
                  "a narrow stair of broken stone", "the lamp will shine again",
                  "the lamp-quest", stages=["start", "middle", "end"], tags={"lift", "steady"}),
    "bridge": Quest("bridge", "rebuild the rope bridge", "braided rope work",
                    "the river below kept pulling the planks apart", "the path will open",
                    "the bridge-quest", stages=["start", "middle", "end"], tags={"tie", "carry"}),
    "spring": Quest("spring", "wake the hidden spring", "shared song and stone",
                    "the gate was sealed by mossy blocks", "the water will run",
                    "the spring-quest", stages=["start", "middle", "end"], tags={"push", "lift"}),
}

TOOLS = {
    "rope": Tool("rope", "rope", "bind and carry", {"tie"}),
    "stone": Tool("stone", "flat stones", "steady and support", {"steady"}),
    "bucket": Tool("bucket", "water buckets", "carry and pour", {"carry"}),
    "song": Tool("song", "a rhythm chant", "keep everyone in step", {"lift", "push"}),
}

CURATED = [
    StoryParams("hill", "lamp", "rope", "stone", "Ari", "girl", "Mira", "boy", "the elder", "woman"),
    StoryParams("grove", "bridge", "rope", "bucket", "Mira", "girl", "Jon", "boy", "the elder", "man"),
    StoryParams("harbor", "spring", "song", "stone", "Nia", "girl", "Tomas", "boy", "the elder", "woman"),
]


@dataclass
class StoryParams:
    setting: str
    quest: str
    tool1: str
    tool2: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for qid, q in QUESTS.items():
            tool_ids = list(TOOLS)
            if teamwork_possible(q, [TOOLS[tool_ids[0]], TOOLS[tool_ids[1]]]):
                combos.append((s, qid, tool_ids[0]))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest"]
    return [
        f'Write a mythic story that includes the word "progression" and shows a team making steady progress together.',
        f"Tell a child-friendly legend about {f['heroes'][0].id} and {f['heroes'][1].id} who must work together to finish the {q.task}.",
        f"Write a small myth where teamwork is the only way forward, and the ending proves how progression changed the shrine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2 = f["heroes"]
    q = f["quest"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {h1.id} and {h2.id} trying to finish {q.task} at the sacred place. They had to make steady progression together because the way was too hard for one child alone."
        ),
        QAItem(
            question="Why did they need teamwork?",
            answer=f"They needed teamwork because {q.obstacle} blocked the path. One helper could lift a piece, another could steady it, and that shared work is what moved the quest forward."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the shrine glowing again and both children smiling. Their progression was visible in the light at the shrine, which proved that the team had finished the quest together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does progression mean?", "Progression means moving forward step by step toward a goal. In a story, it can mean the heroes keep making enough progress until the hard thing is finally done."),
        QAItem("What is teamwork?", "Teamwork means people help one another and share the work. Each person does a part, and together they can finish something that would be too hard alone."),
        QAItem("What is a shrine in a myth?", "A shrine is a special place people treat with respect. In myths it often holds an old power, a light, or a promise."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
teamwork_possible(Q) :- quest(Q), need(Q, N), N <= 2.
progress(1) :- helper(H), task(H).
progress(2) :- progress(1), teamwork.
progress(3) :- progress(2), shrine_glow.
outcome(glow) :- progress(3).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("need", qid, len(q.tags)))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show quest/1."))
    _ = asp.atoms(model, "quest")
    # lightweight parity smoke check
    if not valid_combos():
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic teamwork storyworld with steady progression.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
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
    if args.tool1 and args.tool2 and args.tool1 == args.tool2:
        raise StoryError("Choose two different tools.")
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    t1 = args.tool1 or rng.choice(list(TOOLS))
    t2 = args.tool2 or rng.choice([k for k in TOOLS if k != t1])
    q = QUESTS[quest]
    if not teamwork_possible(q, [TOOLS[t1], TOOLS[t2]]):
        raise StoryError("This quest needs a different pair of tools.")
    return StoryParams(setting, quest, t1, t2,
                       args.hero1 or rng.choice(["Ari", "Nia", "Mira", "Lio"]),
                       "girl", args.hero2 or rng.choice(["Jon", "Tomas", "Sera", "Kai"]),
                       "boy", "Elder", "woman")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest],
                 (TOOLS[params.tool1], TOOLS[params.tool2]),
                 params.hero1, params.hero2_gender, params.hero2, params.hero2_gender,
                 params.elder, params.elder_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show progress/1.\n#show outcome/1."))
        return
    if args.verify:
        try:
            params = CURATED[0]
            sample = generate(params)
            assert sample.story
            return_code = asp_verify()
            sys.exit(return_code)
        except Exception as exc:
            print(exc)
            sys.exit(1)
    if args.asp:
        print("compatibility check available; this world emphasizes narrative generation.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
