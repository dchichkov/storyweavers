#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what to do for Darling."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass(frozen=True)
class Quest:
    id: str
    obstacle: str
    clue: str
    goal: str
    safe_method: str
    helpful_method: str
    object_label: str


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


QUESTS = {
    "spoon": Quest(
        id="spoon",
        obstacle="Darling's favorite spoon has vanished before supper",
        clue="a tiny silver glint beneath the sideboard",
        goal="find the spoon",
        safe_method="kneel and look beneath the sideboard with a napkin",
        helpful_method="ask Dad to move the sideboard gently",
        object_label="silver spoon",
    ),
    "napkin": Quest(
        id="napkin",
        obstacle="Darling's cloth napkin is missing before the table is set",
        clue="a blue corner peeking from the chair basket",
        goal="find the napkin",
        safe_method="follow the blue corner around the chairs",
        helpful_method="ask Grandma to lift the chair basket",
        object_label="blue napkin",
    ),
    "candle": Quest(
        id="candle",
        obstacle="the little supper candle will not stand straight",
        clue="a warm lump of beeswax beside the candle plate",
        goal="steady the candle",
        safe_method="press the soft wax around its base",
        helpful_method="ask Mom to hold the plate while the child fixes it",
        object_label="little candle",
    ),
    "button": Quest(
        id="button",
        obstacle="Darling's cloth bag has lost its bright button",
        clue="a round button hiding beside a bread crumb",
        goal="find the button",
        safe_method="search the table edge with a folded napkin",
        helpful_method="ask Auntie to bring the small sewing tin",
        object_label="bright button",
    ),
}

NAMES = ["Mara", "Nell", "Theo", "Ivy", "Jonah", "Pia"]
ADULTS = ["Mom", "Dad", "Grandma", "Auntie"]
MOODS = ["hopeful", "brave", "curious", "tender"]
PROBLEMS = {
    "lost": ("spoon", "search"),
    "shaky": ("candle", "steady"),
    "missing": ("napkin", "search"),
    "torn": ("button", "repair"),
}
SOLUTIONS = {
    "spoon": {"search", "help"},
    "napkin": {"search", "help"},
    "candle": {"steady", "help"},
    "button": {"repair", "help"},
}

KNOWLEDGE = {
    "spoon": QAItem(
        "Why are spoons useful at supper?",
        "A spoon helps someone carry soft food or a drink safely from a bowl to a mouth.",
    ),
    "napkin": QAItem(
        "What is a napkin for?",
        "A napkin helps keep hands and faces clean while people eat together.",
    ),
    "candle": QAItem(
        "Why should a child ask before touching a candle?",
        "A candle has a flame and hot wax, so an adult can help keep everyone safe.",
    ),
    "button": QAItem(
        "What does a button do?",
        "A button fastens two pieces of cloth when it slips through a small loop.",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (quest_id, problem_id, solution)
        for quest_id in QUESTS
        for problem_id, (mapped_quest, _) in PROBLEMS.items()
        if mapped_quest == quest_id
        for solution in sorted(SOLUTIONS[quest_id])
    ]


def validate_params(params: "StoryParams") -> None:
    if (params.quest, params.problem, params.solution) not in valid_combos():
        raise StoryError("That problem and solution do not fit this dining-room quest.")
    if params.name.strip().lower() in {"darling", "mom", "dad", "grandma", "auntie"}:
        raise StoryError("The child needs a name different from Darling and the helpers.")
    if not params.name.strip():
        raise StoryError("The child needs a name.")


def opening_line(params: "StoryParams", rng: random.Random) -> str:
    choices = [
        f"In the dining room, {params.name} noticed that Darling's supper was not quite ready.",
        f"The dining room glowed softly as {params.name} began preparing a place for Darling.",
        f"Before anyone sat down, {params.name} saw a small problem waiting beside the supper table.",
    ]
    return rng.choice(choices)


def generate(params: "StoryParams") -> StorySample:
    validate_params(params)
    rng = random.Random(params.seed)
    quest = QUESTS[params.quest]
    world = World(setting="dining room")
    child = world.add(Entity(params.name, "character", params.name))
    darling = world.add(Entity("Darling", "character", "Darling"))
    helper_name = params.helper
    helper = world.add(Entity(helper_name, "character", helper_name))
    target = world.add(Entity("quest_object", "thing", quest.object_label))
    table = world.add(Entity("dining_table", "thing", "dining table"))
    world.facts.update(
        child=child,
        darling=darling,
        helper=helper,
        target=target,
        quest=quest,
        params=params,
        resolved=False,
    )
    child.memes["care"] = 1
    child.memes["suspense"] = 1
    target.meters["hidden"] = 1

    world.record(
        "arrive",
        opening_line(params, rng)
        + f" {quest.obstacle.capitalize()}. The table waited beneath a clean cloth, "
        f"and Darling's place looked lonely without the {quest.object_label}.",
        actor=child.id,
        target=table.id,
        cause=quest.obstacle,
        result="the dining room became the starting place for a small quest",
    )

    world.para()
    if params.problem == "shaky":
        problem_text = (
            f'"The candle is wobbling," {params.name} said. '
            f'"Darling may want the table to shine." {helper_name} leaned close, but '
            f"the flame flickered near the curtain. {params.name} felt a flutter of suspense. "
            f'Inner Monologue: "{params.name} thought, "I must decide carefully; '
            f'Darling is counting on me."'
        )
    elif params.problem == "torn":
        problem_text = (
            f"{params.name} found the loose place where the bright button had been. "
            f'"I could pull harder," {params.name} whispered, "but that might make it worse." '
            f'{helper_name} asked, "What do you notice?" '
            f'"The button is near the crumb," {params.name} replied. '
            f"That clue made the quest feel possible."
        )
    elif params.problem == "missing":
        problem_text = (
            f"{params.name} checked the chair and saw no napkin. "
            f'"Darling likes the blue one," {params.name} said. '
            f'"Could it be hiding?" {helper_name} asked. '
            f'"I will decide after I look for a clue," {params.name} answered, '
            f"while suspense tickled the quiet room."
        )
    else:
        problem_text = (
            f"{params.name} searched the tabletop twice, but the silver spoon was gone. "
            f'"Maybe it ran away," {params.name} said. '
            f'"Or maybe it left a clue," {helper_name} replied. '
            f"{params.name} looked beneath the sideboard and held still, listening."
        )
    world.record(
        "problem",
        problem_text,
        actor=child.id,
        target=target.id,
        cause=quest.obstacle,
        result="the child learned that a careful choice was needed",
    )

    world.para()
    if params.solution == "help":
        method = quest.helpful_method
        decision = (
            f'"I decide to ask for help," {params.name} said. '
            f'"Darling needs this, and safe hands are better than rushing." '
            f'{helper_name} smiled. "Good thinking, darling. Tell me exactly what you saw." '
            f"{params.name} shared the clue: {quest.clue}. "
            f"{helper_name} then helped them {method.replace('ask ', '', 1)}."
        )
        target.meters["helped"] = 1
        target.meters["found"] = 1
        result = f"{helper_name} helped {params.name} recover the {quest.object_label} safely."
        method_kind = "ask_help"
    else:
        method = quest.safe_method
        decision = (
            f'"I decide to {method}," {params.name} said. '
            f'{helper_name} answered, "I will watch while you try." '
            f"{params.name} followed the clue, moving slowly so the dining room stayed neat."
        )
        target.meters["found"] = 1
        result = f"{params.name} used the clue and recovered the {quest.object_label}."
        method_kind = "careful_search"

    world.record(
        method_kind,
        decision,
        actor=child.id,
        target=target.id,
        cause=f"The clue was {quest.clue}.",
        result=result,
    )

    world.para()
    target.meters["hidden"] = 0
    child.memes["suspense"] = 0
    child.memes["confidence"] = 1
    world.facts["resolved"] = True
    endings = [
        f"{params.name} placed the {quest.object_label} at Darling's place. Darling clapped, and the empty spot on the table was empty no longer.",
        f"When Darling came to the dining room, {params.name} held up the {quest.object_label}. Darling smiled so widely that the candlelight seemed warmer.",
        f"The supper table was ready at last. Darling touched the {quest.object_label}, and {params.name} felt the brave little quest settle into happiness.",
    ]
    world.record(
        "resolve",
        rng.choice(endings)
        + f' "{params.name}, you helped me," Darling said. '
        f'"And you helped me decide," {params.name} replied. '
        f'{helper_name} laughed softly as everyone drew their chairs close together.',
        actor=darling.id,
        target=target.id,
        cause="the child chose a safe response and followed the clue",
        result="Darling received the needed object and the family shared supper",
    )

    story_qa = [
        QAItem("What problem began the quest?", f"{quest.obstacle.capitalize()} in the dining room, so Darling's place was not ready."),
        QAItem("What did the child learn before acting?", f"The child learned that {quest.clue}, so rushing was less useful than noticing carefully."),
        QAItem("How did the child solve the problem?", result + f" The chosen plan was to {method}."),
        QAItem("What changed at the end?", f"The {quest.object_label} was placed at Darling's setting, and everyone could sit together for supper."),
    ]
    prompts = [
        f"Write a heartwarming dining-room story about {params.name} helping Darling through a suspenseful quest to {quest.goal}.",
        f"Include an inner monologue, a decision, and spoken dialogue that changes the child's action while solving the problem with {method}.",
    ]
    world_qa = [KNOWLEDGE[params.quest]]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: {entity.kind} {entity.label}; "
            f"meters={meters}; memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
quest(q) :- quest_id(q).
valid(Q, P, S) :- quest_id(Q), problem_for(P, Q), solution_for(S, Q).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for quest_id in QUESTS:
        lines.append(asp.fact("quest_id", quest_id))
    for problem, (quest_id, _) in PROBLEMS.items():
        lines.append(asp.fact("problem_for", problem, quest_id))
    for quest_id, solutions in SOLUTIONS.items():
        for solution in solutions:
            lines.append(asp.fact("solution_for", solution, quest_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid())
    if expected != actual:
        print("MISMATCH: ASP and Python quest paths differ.")
        return 1
    checked = 0
    for quest_id, problem, solution in sorted(expected):
        params = StoryParams(
            quest=quest_id,
            problem=problem,
            solution=solution,
            name="Robin",
            helper="Mom",
            mood="hopeful",
            seed=91,
        )
        sample = generate(params)
        assert sample.world.facts["resolved"]
        assert sample.world.entities["quest_object"].meter("found") == 1
        assert len(sample.story_qa) == 4
        checked += 1
    print(f"OK: {len(actual)} ASP/Python paths and {checked} generated story checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate heartwarming dining-room quests about deciding carefully."
    )
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--solution", choices=sorted({s for v in SOLUTIONS.values() for s in v}))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=ADULTS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.problem:
        mapped = PROBLEMS[args.problem][0]
        if mapped != args.quest:
            raise StoryError("That problem does not belong to the selected quest.")
    candidates = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.problem is None or combo[1] == args.problem)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not candidates:
        raise StoryError("No valid quest path matches the requested choices.")
    quest_id, problem, solution = rng.choice(candidates)
    return StoryParams(
        quest=quest_id,
        problem=problem,
        solution=solution,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(ADULTS),
        mood=args.mood or rng.choice(MOODS),
        seed=None,
    )


@dataclass
class StoryParams:
    quest: str
    problem: str
    solution: str
    name: str
    helper: str
    mood: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("spoon", "lost", "search", "Mara", "Mom", "hopeful", 1),
    StoryParams("spoon", "lost", "help", "Theo", "Dad", "brave", 2),
    StoryParams("napkin", "missing", "search", "Ivy", "Grandma", "curious", 3),
    StoryParams("napkin", "missing", "help", "Pia", "Auntie", "tender", 4),
    StoryParams("candle", "shaky", "steady", "Nell", "Mom", "brave", 5),
    StoryParams("candle", "shaky", "help", "Jonah", "Dad", "hopeful", 6),
    StoryParams("button", "torn", "repair", "Mara", "Grandma", "curious", 7),
    StoryParams("button", "torn", "help", "Theo", "Auntie", "tender", 8),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for quest, problem, solution in asp_valid():
            print(f"{quest}: {problem} -> {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            samples.append(sample)

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### dining-room quest {index + 1}")
        print(sample.story)
        if args.trace:
            print(dump_trace(sample.world))
        if args.qa:
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
