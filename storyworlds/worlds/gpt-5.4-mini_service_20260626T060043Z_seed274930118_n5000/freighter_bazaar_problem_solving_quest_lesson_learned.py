#!/usr/bin/env python3
"""
A small bedtime-story world about a freighter, a bazaar, a quest, and a gentle
problem solved with patience and help.

Premise:
- A child rides on a freighter that stops near a bazaar.
- A small problem appears: a needed package is missing before nightfall.
- The child and a caring adult go on a quest through the bazaar.
- They solve the problem by asking, checking, and matching clues.
- The lesson learned is that calm thinking and kind help can fix a worry.

The prose is state-driven: characters, places, items, and feelings all move
through the story model. The result is a complete bedtime-story style tale.
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
    location: str = ""
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    missing_item: str
    clue: str
    worry: str
    fixable_by: str


@dataclass
class QuestStep:
    id: str
    action: str
    result: str
    takes_time: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_lines: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    adult_type: str
    problem: str
    quest: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", indoors=False, affords={"freighter", "bazaar"}),
    "dockside": Setting(place="the dockside market", indoors=False, affords={"freighter", "bazaar"}),
}

PROBLEMS = {
    "missing_lantern": Problem(
        id="missing_lantern",
        label="missing lantern",
        phrase="a little lantern for the night watch",
        missing_item="lantern",
        clue="a bright brass reflection in a stall mirror",
        worry="the deck would be too dark after sunset",
        fixable_by="lamp oil",
    ),
    "missing_tea": Problem(
        id="missing_tea",
        label="missing tea",
        phrase="a warm packet of tea for bedtime",
        missing_item="tea",
        clue="a paper packet tied with blue string",
        worry="the cabin would feel empty without a sleepy cup",
        fixable_by="tea leaves",
    ),
    "missing_berries": Problem(
        id="missing_berries",
        label="missing berries",
        phrase="a small basket of berries for supper",
        missing_item="berries",
        clue="a berry stain on a cloth napkin",
        worry="the supper basket would not be ready for the crew",
        fixable_by="berries",
    ),
}

QUESTS = {
    "find_market_stall": QuestStep(
        id="find_market_stall",
        action="walk carefully through the bazaar and ask the stallkeepers",
        result="they found the right stall by following clues",
        takes_time=True,
    ),
    "compare_clues": QuestStep(
        id="compare_clues",
        action="look at the clue again and match it to the goods",
        result="the clue pointed to the correct shelf",
        takes_time=True,
    ),
    "choose_kind_offer": QuestStep(
        id="choose_kind_offer",
        action="choose the honest stallkeeper who offered the right item",
        result="a helpful seller wrapped up the needed thing",
        takes_time=False,
    ),
}

TOOLS = {
    "map": Tool(
        id="map",
        label="a tiny map",
        phrase="a folded little map",
        helps_with={"find_market_stall"},
    ),
    "coinpurse": Tool(
        id="coinpurse",
        label="a coin purse",
        phrase="a soft coin purse",
        helps_with={"choose_kind_offer"},
    ),
    "lantern_hook": Tool(
        id="lantern_hook",
        label="a lantern hook",
        phrase="a small hook for carrying a lantern",
        helps_with={"missing_lantern"},
    ),
}

CHILD_NAMES = ["Mina", "Owen", "Lina", "Pip", "Nora", "Theo"]
ADULT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            for quest_id, quest in QUESTS.items():
                for tool_id, tool in TOOLS.items():
                    if quest_id == "choose_kind_offer" and tool_id == "coinpurse":
                        out.append((place, prob_id, quest_id, tool_id))
                    elif quest_id == "find_market_stall" and tool_id == "map":
                        out.append((place, prob_id, quest_id, tool_id))
                    elif quest_id == "compare_clues" and tool_id in {"map", "coinpurse"}:
                        out.append((place, prob_id, quest_id, tool_id))
                    elif prob_id == "missing_lantern" and tool_id == "lantern_hook":
                        out.append((place, prob_id, quest_id, tool_id))
    return out


def reasonableness_gate(problem: Problem, quest: QuestStep, tool: Tool) -> bool:
    if quest.id not in tool.helps_with and not (problem.id == "missing_lantern" and tool.id == "lantern_hook"):
        return False
    return True


def explain_rejection(problem: Problem, quest: QuestStep, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not reasonably help with {quest.action} "
        f"for {problem.label}. Choose a tool that fits the clue and the quest.)"
    )


def select_tool(rng: random.Random, prob_id: str, quest_id: str, tool_id: str) -> tuple[Problem, QuestStep, Tool]:
    problem = PROBLEMS[prob_id]
    quest = QUESTS[quest_id]
    tool = TOOLS[tool_id]
    if not reasonableness_gate(problem, quest, tool):
        raise StoryError(explain_rejection(problem, quest, tool))
    return problem, quest, tool


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: freighter, bazaar, quest, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_TYPES)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.quest is None or c[2] == args.quest)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, prob_id, quest_id, tool_id = rng.choice(sorted(filtered))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(ADULT_TYPES)
    if gender == "girl" and name in {"Owen", "Pip", "Theo"}:
        name = rng.choice([n for n in CHILD_NAMES if n not in {"Owen", "Pip", "Theo"}])
    if gender == "boy" and name in {"Mina", "Lina", "Nora"}:
        name = rng.choice([n for n in CHILD_NAMES if n not in {"Mina", "Lina", "Nora"}])
    return StoryParams(place=place, child_name=name, child_gender=gender, adult_type=adult, problem=prob_id, quest=quest_id, tool=tool_id)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_type, label=params.adult_type))
    problem = world.add(Entity(id="problem", type=PROBLEMS[params.problem].id, label=PROBLEMS[params.problem].label, phrase=PROBLEMS[params.problem].phrase))
    tool = world.add(Entity(id="tool", type=TOOLS[params.tool].id, label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase, owner=child.id, carried_by=child.id))
    world.facts.update(child=child, adult=adult, problem=problem, tool=tool, quest=QUESTS[params.quest], params=params)
    return world


def tell_story(world: World) -> World:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    problem: Entity = f["problem"]
    tool: Entity = f["tool"]
    quest: QuestStep = f["quest"]

    world.say(f"On a quiet evening, {child.label} rode on a freighter with {child.pronoun('possessive')} {adult.type}.")
    world.say(f"The freighter moved slowly beside {world.setting.place}, where the bazaar glowed like a string of lanterns.")
    world.say(f"But there was a small worry: {PROBLEMS[f['params'].problem].worry}.")
    world.para()
    world.say(f"{child.label} and {adult.label} began a gentle quest.")
    world.say(f"They would {quest.action} and carry {tool.phrase} to help them.")
    world.say(f"Their hearts felt a little serious, but not scared, because {child.label} held the clue in mind.")
    world.para()
    if quest.id == "find_market_stall":
        world.say(f"They walked past baskets and ribbons until {PROBLEMS[f['params'].problem].clue} shone in the dim light.")
        world.say(f"That clue led them to the right stall, where a kind seller smiled and gave them what they needed.")
    elif quest.id == "compare_clues":
        world.say(f"{child.label} looked again at the clue and matched it with the goods on the shelves.")
        world.say(f"After a few careful moments, they found the correct item waiting almost exactly where it should be.")
    else:
        world.say(f"{child.label} found a stallkeeper who listened, checked the request, and offered the honest fix.")
        world.say(f"The helpful seller wrapped it neatly so it would travel safely back to the freighter.")
    world.para()
    world.say(f"By the time the sky turned deep blue, the problem was solved, and the freighter felt peaceful again.")
    world.say(f"{child.label} learned that calm thinking, asking for help, and following clues can turn a worry into a happy ending.")
    world.say(f"And so, with the {problem.label} made right, {child.label} curled up warm and sleepy, ready for dreams.")

    world.facts["solved"] = True
    world.facts["lesson"] = "calm thinking and kind help solve problems"
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    prob = PROBLEMS[p.problem]
    return [
        f"Write a bedtime story about a freighter stopping near a bazaar, where {p.child_name} solves a small problem.",
        f"Tell a gentle quest story for a child who needs to find {prob.phrase} in the bazaar.",
        f"Write a bedtime-style story with a freighter, a bazaar, and a lesson learned about patient problem solving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    prob = PROBLEMS[p.problem]
    quest = QUESTS[p.quest]
    tool = TOOLS[p.tool]
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]

    return [
        QAItem(
            question=f"Where did {child.label} and the {adult.type} travel in the story?",
            answer=f"They traveled on a freighter near {world.setting.place}, where the bazaar was waiting with soft evening lights.",
        ),
        QAItem(
            question=f"What problem made the quest begin?",
            answer=f"The problem was {prob.label}. They needed {prob.phrase} before the night got too deep.",
        ),
        QAItem(
            question=f"What did {child.label} use to help with the quest?",
            answer=f"{child.label} used {tool.phrase} while they followed the clue and stayed calm.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"They solved it by using the quest plan to {quest.action}, which led them to the right answer in the bazaar.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer="The lesson learned was that calm thinking and kind help can solve a problem without any fuss.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a freighter?",
            answer="A freighter is a large ship that carries goods across water.",
        ),
        QAItem(
            question="What is a bazaar?",
            answer="A bazaar is a busy market with many stalls where people buy and sell things.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small journey or mission to find something or solve a problem.",
        ),
        QAItem(
            question="What does lesson learned mean in a story?",
            answer="A lesson learned is the helpful idea the character understands by the end of the story.",
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for qid, quest in QUESTS.items():
        for tid in TOOLS:
            if qid in TOOLS[tid].helps_with or (qid == "compare_clues" and tid in {"map", "coinpurse"}):
                lines.append(asp.fact("helps", tid, qid))
    for pid, prob in PROBLEMS.items():
        for qid in QUESTS:
            for tid, tool in TOOLS.items():
                if reasonableness_gate(prob, QUESTS[qid], tool):
                    lines.append(asp.fact("valid", pid, qid, tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,Q,T) :- valid(P,Q,T).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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
    StoryParams(place="harbor", child_name="Mina", child_gender="girl", adult_type="mother", problem="missing_lantern", quest="find_market_stall", tool="lantern_hook"),
    StoryParams(place="dockside", child_name="Theo", child_gender="boy", adult_type="father", problem="missing_tea", quest="compare_clues", tool="map"),
    StoryParams(place="harbor", child_name="Lina", child_gender="girl", adult_type="mother", problem="missing_berries", quest="choose_kind_offer", tool="coinpurse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.child_name}: {p.problem} / {p.quest} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
