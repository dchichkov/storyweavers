#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py
================================================================

A standalone storyworld about a child-facing fairy-tale problem: in the little
kingdom of Thistledown, anyone who crosses Moonbeam Bridge after dusk must carry
a lantern license stamped by the bridge keeper. A small hero hurries to help
someone in need, discovers a license problem at the gate, and solves it with
patience, memory, and kindness rather than sneaking or arguing.

The world models:

* typed entities with physical meters and emotional memes
* a small causal engine (darkness -> worry; repaired trust -> passage)
* a reasonableness gate over which fixes actually solve which license problem
* an inline ASP twin for parity checks
* prose rendered from world state, not from static templates alone

Run it
------
    python storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py --problem forgotten
    python storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py --solution sneak
    python storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/license_problem_solving_fairy_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "witch", "fairy"}
        male = {"boy", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Quest:
    id: str
    needer: str
    item: str
    opening: str
    need_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    keeper_line: str
    fix_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    sense: int
    fixes: set[str]
    action: str
    result: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dark_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    bridge = world.entities.get("bridge")
    if not hero or not bridge:
        return out
    if bridge.meters["waiting"] < THRESHOLD:
        return out
    sig = ("dark_worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_trust_opens(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    keeper = world.entities.get("keeper")
    gate = world.entities.get("gate")
    if not hero or not keeper or not gate:
        return out
    if hero.memes["proved_honesty"] < THRESHOLD:
        return out
    sig = ("trust_opens", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["trust"] += 1
    gate.meters["open"] += 1
    out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule("dark_worry", "emotional", _r_dark_worry),
    Rule("trust_opens", "social", _r_trust_opens),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def solution_fits(problem: Problem, solution: Solution) -> bool:
    return problem.id in solution.fixes and solution.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, problem in PROBLEMS.items():
        for sid, solution in SOLUTIONS.items():
            if solution_fits(problem, solution):
                combos.append((pid, sid))
    return combos


def predict_passage(world: World, problem: Problem, solution: Solution) -> dict:
    sim = world.copy()
    apply_solution(sim, problem, solution, narrate=False)
    propagate(sim, narrate=False)
    return {
        "opened": sim.get("gate").meters["open"] >= THRESHOLD,
        "trust": sim.get("keeper").memes["trust"],
    }


def explain_rejection(problem: Problem, solution: Solution) -> str:
    if solution.sense < SENSE_MIN:
        good = ", ".join(sorted(s.id for s in sensible_solutions()))
        return (
            f"(Refusing solution '{solution.id}': it solves problems the wrong way "
            f"for this world. Fairy-tale problem solving should prefer honest, "
            f"helpful fixes. Try one of: {good}.)"
        )
    return (
        f"(No story: {solution.label} does not fix the problem '{problem.id}'. "
        f"Here the keeper needs {problem.fix_need}, so that choice would not earn "
        f"a valid license.)"
    )


def introduce(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In the mossy little kingdom of Thistledown, {hero.id} lived where "
        f"foxgloves leaned over the path and bells in the reeds rang at dusk."
    )
    world.say(quest.opening)
    world.say(quest.need_line)


def explain_rule(world: World, keeper: Entity) -> None:
    world.say(
        f"Every evening, when the sky turned plum and silver, "
        f"{keeper.label_word} checked each traveler's lantern license at Moonbeam Bridge."
    )
    world.say(
        "The rule was old and kind: only marked lanterns were allowed over the bridge, "
        "so no wandering spark would startle the nesting swans below."
    )


def depart(world: World, hero: Entity, lantern: Entity) -> None:
    hero.memes["hope"] += 1
    lantern.meters["lit"] += 1
    world.say(
        f"So {hero.id} tucked a warm little loaf into a satchel, lifted "
        f"{hero.pronoun('possessive')} lantern, and hurried toward the river road."
    )


def arrive_problem(world: World, hero: Entity, keeper: Entity, problem: Problem) -> None:
    bridge = world.get("bridge")
    gate = world.get("gate")
    bridge.meters["waiting"] += 1
    gate.meters["closed"] += 1
    hero.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At Moonbeam Bridge, {keeper.label_word} peered at the hanging card and frowned."
    )
    world.say(problem.keeper_line)
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s heart gave one small thump. The river looked dark below, "
            "and the far lanterns of the village seemed suddenly very far away."
        )


def think(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["thought"] += 1
    world.say(
        f"But {hero.id} did not stamp or sob. {hero.pronoun().capitalize()} took a slow breath, "
        f"looked at the little card again, and thought about what {problem.fix_need}."
    )


def apply_solution(world: World, problem: Problem, solution: Solution, narrate: bool = True) -> None:
    hero = world.get("hero")
    keeper = world.get("keeper")
    license_card = world.get("license")
    if narrate:
        world.say(solution.action)
    if solution.id == "memory_riddle":
        hero.memes["clever"] += 1
        hero.memes["proved_honesty"] += 1
        license_card.meters["valid"] += 1
        world.facts["method_detail"] = "the secret rhyme and the bridge-keeper's three questions"
    elif solution.id == "kind_deed":
        hero.memes["kindness"] += 1
        hero.memes["proved_honesty"] += 1
        keeper.memes["relief"] += 1
        license_card.meters["valid"] += 1
        world.facts["method_detail"] = "mending the keeper's wet ledger with cattail thread and patience"
    elif solution.id == "witness_mark":
        hero.memes["trust_in_others"] += 1
        hero.memes["proved_honesty"] += 1
        keeper.memes["trust"] += 0.5
        license_card.meters["valid"] += 1
        world.facts["method_detail"] = "a baker's witness ribbon and the flour-star tied to the lantern handle"
    elif solution.id == "sneak":
        hero.memes["fear"] += 1
        keeper.memes["trust"] -= 1
    elif solution.id == "argue":
        hero.memes["frustration"] += 1
        keeper.memes["trust"] -= 1
    propagate(world, narrate=False)
    if narrate and license_card.meters["valid"] >= THRESHOLD:
        world.say(solution.result)


def grant_passage(world: World, hero: Entity, keeper: Entity, quest: Quest) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.get("bridge").meters["crossed"] += 1
    world.say(
        f'"Then you may pass," said {keeper.label_word}, and with a soft clink '
        "the silver chain across the bridge was lifted."
    )
    world.say(
        f"{hero.id} crossed over the shining boards while moonlight trembled in the water below."
    )
    world.say(quest.ending_image)


def close_with_lesson(world: World, hero: Entity) -> None:
    world.say(
        f"After that, {hero.id} kept {hero.pronoun('possessive')} lantern license tucked safely in a dry blue pocket."
    )
    world.say(
        "And whenever a knotty problem appeared, the child of Thistledown remembered "
        "that a calm mind can find a path where pushing never could."
    )


def tell(
    quest: Quest,
    problem: Problem,
    solution: Solution,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    keeper_type: str = "fairy",
    seed_hint: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the bridge keeper", role="keeper"))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern"))
    license_card = world.add(Entity(id="license", type="license", label="license"))
    bridge = world.add(Entity(id="bridge", type="bridge", label="Moonbeam Bridge"))
    gate = world.add(Entity(id="gate", type="gate", label="bridge gate"))
    river = world.add(Entity(id="river", type="river", label="river"))
    world.facts["seed_hint"] = seed_hint

    introduce(world, hero, quest)
    explain_rule(world, keeper)
    depart(world, hero, lantern)

    world.para()
    arrive_problem(world, hero, keeper, problem)
    think(world, hero, problem)

    pred = predict_passage(world, problem, solution)
    world.facts["predicted_open"] = pred["opened"]
    world.facts["predicted_trust"] = pred["trust"]

    world.para()
    apply_solution(world, problem, solution, narrate=True)

    if world.get("gate").meters["open"] >= THRESHOLD and world.get("license").meters["valid"] >= THRESHOLD:
        grant_passage(world, hero, keeper, quest)
        world.para()
        close_with_lesson(world, hero)

    world.facts.update(
        hero=hero,
        keeper=keeper,
        lantern=lantern,
        license=license_card,
        bridge=bridge,
        gate=gate,
        river=river,
        quest=quest,
        problem=problem,
        solution=solution,
        solved=world.get("license").meters["valid"] >= THRESHOLD and world.get("gate").meters["open"] >= THRESHOLD,
        crossed=world.get("bridge").meters["crossed"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "bread": Quest(
        "bread",
        "Grandmother Wren",
        "honey bread",
        "One evening, Grandmother Wren sent word from the far bank that her cough was scratchy and her cupboard was bare.",
        'Mira promised, "I will bring warm honey bread before the moon climbs high."',
        "Before long, the old grandmother was smiling by the window with warm bread in her hands, and the cottage smelled of honey and thyme.",
        tags={"bread", "helping"},
    ),
    "medicine": Quest(
        "medicine",
        "the village baker",
        "mint syrup",
        "One evening, the village baker sent a worried note: his little son had a sore throat and needed mint syrup from the apothecary on the far bank.",
        'The child said, "I will carry it quickly, before the stars grow bright."',
        "Soon the baker's kitchen glowed gold again, and a sleepy child sipped mint syrup while the oven ticked softly.",
        tags={"medicine", "helping"},
    ),
    "thread": Quest(
        "thread",
        "Queen Linnet's tailor",
        "moon-silk thread",
        "One evening, Queen Linnet's tailor cried out that the silver hem of the dawn cloak had torn, and only moon-silk thread from the far bank could mend it.",
        'The child bowed and said, "I will fetch it before the palace bells ring nine."',
        "At last the palace windows glittered, and the dawn cloak shone whole again as if stitched with a strip of moonlight.",
        tags={"thread", "helping"},
    ),
}

PROBLEMS = {
    "forgotten": Problem(
        "forgotten",
        "forgotten card",
        "Your lantern license is missing, little traveler. No card, no crossing until I know whose light you carry.",
        "the old lantern rhyme and proof that the child truly belongs on the road",
        tags={"memory", "license"},
    ),
    "smudged": Problem(
        "smudged",
        "smudged stamp",
        "This lantern license has been splashed by river mist. I cannot read the moon-stamp clearly enough to pass you through.",
        "a clean way to prove the lantern was truly registered",
        tags={"repair", "license"},
    ),
    "torn": Problem(
        "torn",
        "torn ribbon",
        "The witness ribbon on this lantern license has torn loose. The rule says I must see some honest mark tying this light to its owner.",
        "a witness mark or another trustworthy sign",
        tags={"witness", "license"},
    ),
}

SOLUTIONS = {
    "memory_riddle": Solution(
        "memory_riddle",
        "answer the lantern rhyme",
        3,
        {"forgotten"},
        'Mira looked up at the carved swan over the arch and softly recited the old lantern rhyme. Then she answered the keeper\'s three gentle questions about whose light it was, where it had first been blessed, and why she was hurrying tonight.',
        "The keeper's face softened. With a silver pen, she wrote a fresh moon-mark on a new card and tied the license beneath the lantern ring.",
        "answered the old lantern rhyme and proved the lantern truly belonged to the traveler",
        tags={"memory", "rhyme", "license"},
    ),
    "kind_deed": Solution(
        "kind_deed",
        "repair the wet ledger",
        3,
        {"smudged"},
        'Seeing the keeper\'s ledger drooping in the mist, Mira offered a strip of cattail thread from her satchel and helped dry and bind the damp pages. When the last page was straight, the old list of lantern numbers could be read again.',
        "There, beside the date and the bridge seal, lay the lantern's number after all. The keeper brushed the page dry and pressed a clear new stamp onto the license.",
        "helped repair the keeper's wet ledger so the true license record could be checked",
        tags={"repair", "kindness", "license"},
    ),
    "witness_mark": Solution(
        "witness_mark",
        "bring a witness ribbon",
        2,
        {"torn"},
        'Mira remembered the flour-star ribbon the village baker had tied to the lantern handle that morning. She showed the matching star stitched on the baker\'s market note, and the keeper saw at once that the mark and the errand belonged together.',
        "With a nod, the keeper tied on a fresh witness ribbon and fastened the license neatly beneath it.",
        "showed a matching witness mark that proved the lantern and errand belonged together",
        tags={"witness", "proof", "license"},
    ),
    "sneak": Solution(
        "sneak",
        "slip past the chain",
        1,
        set(),
        'For one uneasy blink, Mira wondered if she could duck under the silver chain and run across before anyone noticed.',
        "But that would only break trust, not mend the license.",
        "tried to sneak past the bridge keeper",
        tags={"bad_idea"},
    ),
    "argue": Solution(
        "argue",
        "argue with the keeper",
        1,
        set(),
        'For one hot moment, Mira thought about shouting that rules were foolish when someone needed help.',
        "But loud words could not turn a bad license into a good one.",
        "argued instead of solving the actual problem",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tansy", "Nell", "Ivy", "Elsa", "Wren", "Poppy"]
BOY_NAMES = ["Tobin", "Rowan", "Pip", "Alder", "Finn", "Milo", "Bram", "Leo"]
KEEPER_TYPES = ["fairy", "woman", "wizard"]
TRAITS = ["patient", "brave", "kind", "thoughtful", "steady"]


@dataclass
class StoryParams:
    quest: str
    problem: str
    solution: str
    hero_name: str
    hero_type: str
    keeper_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "license": [(
        "What is a license?",
        "A license is a little paper or card that shows you have permission to do something. In this story, the lantern license proves the light is allowed on the bridge."
    )],
    "memory": [(
        "Why can remembering something help solve a problem?",
        "Remembering important facts can help you prove something is true. A calm memory can work like a key when a door is shut."
    )],
    "repair": [(
        "What does it mean to repair something?",
        "To repair something means to fix what is broken so it can work again. Small careful help can solve a big problem."
    )],
    "witness": [(
        "What is a witness mark?",
        "A witness mark is a sign that helps show who something belongs to or where it came from. It helps other people trust what they are seeing."
    )],
    "problem_solving": [(
        "What is problem solving?",
        "Problem solving means noticing what is wrong, thinking carefully, and choosing a step that really fixes it. It works better than rushing or arguing."
    )],
    "bridge": [(
        "Why might a bridge keeper check travelers?",
        "A bridge keeper checks travelers to keep the crossing orderly and safe. Rules help everyone know what is allowed."
    )],
    "kindness": [(
        "How can kindness help solve a hard problem?",
        "Kindness can make people calmer and more willing to help each other. Sometimes helping with one problem uncovers the answer to another one."
    )],
}
KNOWLEDGE_ORDER = ["license", "problem_solving", "memory", "repair", "witness", "bridge", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    problem = f["problem"]
    solution = f["solution"]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the word "license" and centers on problem solving.',
        f"Tell a gentle fairy tale where {hero.label} must cross a moonlit bridge to deliver {quest.item}, but a {problem.label} blocks the way.",
        f"Write a story where the hero solves a {problem.label} by choosing to {solution.label} instead of pushing or panicking, and ends with help reaching someone in need.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    quest = f["quest"]
    problem = f["problem"]
    solution = f["solution"]
    solved = f["solved"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child in Thistledown, and the bridge keeper at Moonbeam Bridge. The child was hurrying to bring {quest.item} to {quest.needer}."
        ),
        (
            "What problem stopped the hero at the bridge?",
            f"The keeper found a {problem.label} with the lantern license and would not lift the chain yet. The bridge rule needed honest proof before anyone could cross after dusk."
        ),
        (
            "Why did the hero need to cross the bridge?",
            f"{hero.label} was trying to bring {quest.item} to {quest.needer}. That made the delay feel urgent, because someone on the far bank was waiting for help."
        ),
        (
            "How did the hero solve the problem?",
            f"{hero.label} chose to {solution.label}. {solution.qa_text.capitalize()}, which gave the keeper a real reason to trust the license."
        ),
    ]
    if solved:
        qa.append((
            "Why did the keeper finally let the hero pass?",
            f"The keeper let {hero.label} pass because the license problem had truly been fixed, not merely talked around. Once there was honest proof, the rule and the errand could both be honored."
        ))
        qa.append((
            "How did the story end?",
            f"The child crossed Moonbeam Bridge and the needed help reached {quest.needer}. The ending shows that careful thinking turned a delay into a safe, happy ending."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"license", "problem_solving", "bridge"}
    problem = world.facts["problem"]
    solution = world.facts["solution"]
    if "memory" in problem.tags or "memory" in solution.tags:
        tags.add("memory")
    if "repair" in problem.tags or "repair" in solution.tags:
        tags.add("repair")
    if "witness" in problem.tags or "witness" in solution.tags:
        tags.add("witness")
    if "kindness" in solution.tags:
        tags.add("kindness")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bread", "forgotten", "memory_riddle", "Mira", "girl", "fairy", "patient"),
    StoryParams("medicine", "smudged", "kind_deed", "Rowan", "boy", "woman", "kind"),
    StoryParams("thread", "torn", "witness_mark", "Poppy", "girl", "wizard", "thoughtful"),
]


def outcome_of(params: StoryParams) -> str:
    return "solved" if solution_fits(PROBLEMS[params.problem], SOLUTIONS[params.solution]) else "stuck"


ASP_RULES = r"""
sensible(S) :- solution(S), sense(S, V), sense_min(M), V >= M.
fixes_problem(P, S) :- fixes(S, P), sensible(S).
valid(P, S) :- problem(P), solution(S), fixes_problem(P, S).

outcome(solved) :- chosen_problem(P), chosen_solution(S), valid(P, S).
outcome(stuck)  :- chosen_problem(P), chosen_solution(S), not valid(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, s.sense))
        for p in sorted(s.fixes):
            lines.append(asp.fact("fixes", sid, p))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sensible, p_sensible = set(asp_sensible()), {s.id for s in sensible_solutions()}
    if c_sensible == p_sensible:
        print(f"OK: sensible solutions match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible solutions: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a lantern license problem solved with calm thinking."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=KEEPER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (problem, solution) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.solution:
        problem = PROBLEMS[args.problem]
        solution = SOLUTIONS[args.solution]
        if not solution_fits(problem, solution):
            raise StoryError(explain_rejection(problem, solution))

    combos = [c for c in valid_combos()
              if (args.problem is None or c[0] == args.problem)
              and (args.solution is None or c[1] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, solution_id = rng.choice(sorted(combos))
    quest_id = args.quest or rng.choice(sorted(QUESTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper = args.keeper or rng.choice(KEEPER_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        quest=quest_id,
        problem=problem_id,
        solution=solution_id,
        hero_name=hero,
        hero_type=gender,
        keeper_type=keeper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        QUESTS[params.quest],
        PROBLEMS[params.problem],
        SOLUTIONS[params.solution],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        keeper_type=params.keeper_type,
        seed_hint=str(params.seed) if params.seed is not None else "",
    )
    world.get("hero").traits.append(params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, solution) pairs:\n")
        for problem, solution in combos:
            print(f"  {problem:10} {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.hero_name}: {p.problem} -> {p.solution} ({p.quest}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
