#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/halt_submission_reconciliation_quest_humor_space_adventure.py
==============================================================================================

A tiny space-adventure storyworld about a scout crew, a stubborn shuttle, and a
comic misunderstanding that ends in reconciliation.

Seed words: halt, submission
Features: Reconciliation, Quest, Humor
Style: Space Adventure

The world is intentionally small and classical:
- a crew travels through a few concrete locations
- a machine misreads a command and causes trouble
- the crew must halt, fix the problem, and complete a quest
- the ending proves that reconciliation changed the mood and the mission

The script follows the shared StorySample / QAItem / StoryError contract and
supports prose, JSON, trace, QA, ASP, and verification modes.
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
HUMOR_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "robot", "pilot", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    kind: str
    echoes: bool = False
    dusty: bool = False
    dark: bool = False
    meter_tag: str = ""


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    needed: str
    comic: str
    holds: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    misreads_as: str
    creates: str
    hazard: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    kindness: int
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
    apply: Callable[[World], list[str]]


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    if not ship:
        return out
    if ship.meters["drift"] < THRESHOLD:
        return out
    sig = ("scatter", "ship")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crew").memes["alarm"] += 1
    world.get("crew").memes["humor"] += 1
    out.append("__scatter__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    crew = world.entities.get("crew")
    if not crew:
        return out
    if crew.memes["apology"] < THRESHOLD or crew.memes["forgive"] < THRESHOLD:
        return out
    sig = ("reconcile", "crew")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.memes["warmth"] += 1
    crew.memes["humor"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter), Rule("reconcile", _r_reconcile)]


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


def reasonableness_gate(problem: Problem, item: QuestItem, fix: Fix) -> bool:
    return problem.creates == item.holds and fix.power >= 1 and fix.kindness >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for quest in QUESTS:
        for prob in PROBLEMS.values():
            for fix in FIXES.values():
                if reasonableness_gate(prob, quest, fix):
                    combos.append((quest.id, prob.id, fix.id))
    return combos


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: (f.kindness, f.power))


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    prob = PROBLEMS[problem_id]
    ship = sim.get("ship")
    ship.meters["drift"] += 1
    if prob.creates == "static":
        sim.get("crew").memes["annoyance"] += 1
    propagate(sim, narrate=False)
    return {
        "drift": ship.meters["drift"],
        "alarm": sim.get("crew").memes["alarm"],
    }


def start(world: World, captain: Entity, pilot: Entity, quest: QuestItem, place: Place) -> None:
    captain.memes["joy"] += 1
    pilot.memes["joy"] += 1
    world.say(
        f"On the starship Lantern, {captain.id} and {pilot.id} were chasing "
        f"{quest.phrase} through {place.label}."
    )
    world.say(
        f"{captain.id} promised a {quest.label} would finish the mission, and "
        f"{pilot.id} grinned because even the stars looked like breadcrumbs."
    )


def trouble(world: World, captain: Entity, pilot: Entity, problem: Problem) -> None:
    captain.memes["humor"] += 1
    world.say(
        f"Then the console flashed a silly warning: {problem.phrase}. "
        f'The ship tried to "help" by reading the command as {problem.misreads_as}.'
    )
    world.say(
        f'"{problem.label}! Halt!" {captain.id} shouted, because the ship was '
        f"heading the wrong way."
    )


def defy(world: World, pilot: Entity, problem: Problem) -> None:
    pilot.memes["defiance"] += 1
    world.say(
        f"{pilot.id} laughed anyway and waved at the blinking panel. '
        f'"It only wants submission," {pilot.id} said, "and I am not giving it a sandwich."'
    )


def halt(world: World, captain: Entity, ship: Entity) -> None:
    ship.meters["drift"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The captain slapped the red halt switch. The ship lurched, then stopped "
        f"with a tiny toot, like a trumpet trying not to wake a moon."
    )


def apologize(world: World, pilot: Entity, captain: Entity) -> None:
    pilot.memes["apology"] += 1
    world.say(
        f"{pilot.id} blinked, saw the mess, and said sorry. "
        f"{pilot.id} even bowed to the console, which made the crew snort."
    )


def forgive(world: World, captain: Entity, pilot: Entity) -> None:
    captain.memes["forgive"] += 1
    world.say(
        f"{captain.id} smiled. 'We can fix a mistake,' {captain.id} said. "
        f"'We just cannot keep flying it in circles.'"
    )


def fix_problem(world: World, crew: Entity, fix: Fix, item: QuestItem) -> None:
    crew.memes["warmth"] += 1
    world.say(
        f"They used {fix.phrase} and {fix.action}. The comic little error stopped "
        f"trying to boss them around."
    )


def quest_success(world: World, captain: Entity, pilot: Entity, item: QuestItem, place: Place) -> None:
    captain.memes["joy"] += 1
    pilot.memes["joy"] += 1
    world.say(
        f"At last, they found {item.phrase} tucked in {place.label}. "
        f"{item.comic.capitalize()}, and it held the missing map crystal like a prize."
    )
    world.say(
        f"{captain.id} and {pilot.id} shared a grin, because the quest was done "
        f"and the ship hummed straight again."
    )


def reconciliation_end(world: World, captain: Entity, pilot: Entity) -> None:
    captain.memes["humor"] += 1
    pilot.memes["humor"] += 1
    world.say(
        f"Afterward, {captain.id} and {pilot.id} laughed together in the glow of "
        f"the stars. The apology had become a truce, and the truce felt like home."
    )


def tell(place: Place, quest: QuestItem, problem: Problem, fix: Fix,
         captain_name: str = "Nova", pilot_name: str = "Pip",
         captain_type: str = "girl", pilot_type: str = "boy") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type, role="captain"))
    pilot = world.add(Entity(id=pilot_name, kind="character", type=pilot_type, role="pilot"))
    crew = world.add(Entity(id="crew", kind="group", type="crew", label="the crew"))
    ship = world.add(Entity(id="ship", kind="vehicle", type="ship", label="the ship"))

    start(world, captain, pilot, quest, place)
    world.para()
    trouble(world, captain, pilot, problem)
    defy(world, pilot, problem)
    halt(world, captain, ship)
    apologize(world, pilot, captain)
    forgive(world, captain, pilot)
    world.para()
    fix_problem(world, crew, fix, quest)
    quest_success(world, captain, pilot, quest, place)
    reconciliation_end(world, captain, pilot)

    world.facts.update(
        captain=captain,
        pilot=pilot,
        crew=crew,
        ship=ship,
        place=place,
        quest=quest,
        problem=problem,
        fix=fix,
        outcome="reconciled",
    )
    return world


PLACES = {
    "orbit": Place(id="orbit", label="low orbit above the blue planet", kind="space", echoes=True, dark=False),
    "station": Place(id="station", label="the spinning space station corridor", kind="space", echoes=True, dark=True),
    "moonbase": Place(id="moonbase", label="the moonbase loading dock", kind="space", dusty=True, dark=True),
}

QUESTS = [
    QuestItem(id="crystal", label="quest crystal", phrase="the quest crystal", needed="map", comic="It sparkled so hard it seemed to wink", holds="glow"),
    QuestItem(id="beacon", label="signal beacon", phrase="the signal beacon", needed="route", comic="It beeped like a hiccuping duck", holds="beep"),
    QuestItem(id="sticker", label="star sticker", phrase="the star sticker", needed="badge", comic="It stuck to everything, including the wrong glove", holds="stick"),
]

PROBLEMS = {
    "halt": Problem(id="halt", label="halt", phrase="the halt alarm", misreads_as="a dance routine", creates="static", hazard="wrong direction"),
    "submission": Problem(id="submission", label="submission", phrase="the submission scanner", misreads_as="a snack request", creates="static", hazard="embarrassment"),
}

FIXES = {
    "laugh_and_retry": Fix(id="laugh_and_retry", label="laugh and retry", phrase="a quick laugh and a reset", action="restarted the panel", power=2, kindness=3),
    "gentle_patch": Fix(id="gentle_patch", label="gentle patch", phrase="a gentle patch cable", action="relinked the scanner", power=2, kindness=2),
    "apology_mode": Fix(id="apology_mode", label="apology mode", phrase="the apology mode button", action="told the ship to calm down", power=1, kindness=3),
}

CURATED = [
    StoryParams(
        place="orbit",
        quest="crystal",
        problem="halt",
        fix="laugh_and_retry",
        captain_name="Nova",
        pilot_name="Pip",
        captain_type="girl",
        pilot_type="boy",
        seed=None,
    ),
    StoryParams(
        place="station",
        quest="beacon",
        problem="submission",
        fix="gentle_patch",
        captain_name="Mira",
        pilot_name="Joss",
        captain_type="girl",
        pilot_type="boy",
        seed=None,
    ),
    StoryParams(
        place="moonbase",
        quest="sticker",
        problem="halt",
        fix="apology_mode",
        captain_name="Luna",
        pilot_name="Beck",
        captain_type="girl",
        pilot_type="boy",
        seed=None,
    ),
]


@dataclass
class StoryParams:
    place: str
    quest: str
    problem: str
    fix: str
    captain_name: str = "Nova"
    pilot_name: str = "Pip"
    captain_type: str = "girl"
    pilot_type: str = "boy"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure reconciliation quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices={q.id for q in QUESTS})
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--captain-name")
    ap.add_argument("--pilot-name")
    ap.add_argument("--captain-type", choices=["girl", "boy"])
    ap.add_argument("--pilot-type", choices=["girl", "boy"])
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


def explain_rejection(problem: Problem, quest: QuestItem) -> str:
    return (
        f"(No story: the {problem.label} problem does not fit this quest item. "
        f"Try a combination where the trouble can be halted and resolved with humor.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.quest:
        if not reasonableness_gate(PROBLEMS[args.problem], next(q for q in QUESTS if q.id == args.quest), FIXES[args.fix] if args.fix else best_fix()):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], next(q for q in QUESTS if q.id == args.quest)))
    quest_ids = [q.id for q in QUESTS]
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(quest_ids)
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    captain_name = args.captain_name or rng.choice(["Nova", "Mira", "Luna", "Iris"])
    pilot_name = args.pilot_name or rng.choice(["Pip", "Joss", "Beck", "Tiko"])
    captain_type = args.captain_type or "girl"
    pilot_type = args.pilot_type or "boy"
    if not reasonableness_gate(PROBLEMS[problem], next(q for q in QUESTS if q.id == quest), FIXES[fix]):
        # fail closed; choose a valid combo instead of KeyError or weak story
        combos = valid_combos()
        if not combos:
            raise StoryError("(No valid combination matches the given options.)")
        quest, problem, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        quest=quest,
        problem=problem,
        fix=fix,
        captain_name=captain_name,
        pilot_name=pilot_name,
        captain_type=captain_type,
        pilot_type=pilot_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a space adventure story that includes the words \"halt\" and \"submission\" and ends with reconciliation.",
        f"Tell a humorous quest story where {f['captain'].id} and {f['pilot'].id} must halt a silly machine and then make peace.",
        f"Write a child-facing spaceship tale with a comic mistake, a fix, and a warm ending among the stars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    pilot = f["pilot"]
    quest = f["quest"]
    problem = f["problem"]
    fix = f["fix"]
    place = f["place"]
    return [
        QAItem(
            question="Who are the story's main characters?",
            answer=f"The story is about {captain.id} and {pilot.id}, a crew who go on a space quest together. They begin bickering a little, but they end in reconciliation."
        ),
        QAItem(
            question="Why did they need to halt the ship?",
            answer=f"They had to halt the ship because {problem.phrase} made the console go silly and steer the wrong way. Stopping the ship gave them time to fix the mistake before the quest got lost."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {fix.phrase} to calm the machine and relink the controls. That let them finish the quest without turning the whole trip into a floating joke."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, {captain.id} and {pilot.id} were laughing together again, and the quest item was found at {place.label}. The apology and the fix turned a tense moment into reconciliation."
        ),
        QAItem(
            question=f"What does the word '{quest.label}' mean in this story?",
            answer=f"It is the special thing they are trying to find during the mission. The quest item is the prize that proves the adventure was completed."
        ),
        QAItem(
            question=f"Why is '{problem.label}' important here?",
            answer=f"It is the trouble that makes the crew stop and think. Without that problem, there would be no comic setback and no reason for the crew to reconcile."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a halt mean?",
            answer="A halt means to stop moving for a moment. In a space adventure, a halt keeps a ship from drifting into more trouble."
        ),
        QAItem(
            question="What is submission?",
            answer="Submission means giving in or letting a rule or machine win. In this story it is a funny word the crew treats carefully, because they do not want to obey the wrong command."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a disagreement. They talk, forgive, and start feeling kind again."
        ),
        QAItem(
            question="Why do quests make good stories?",
            answer="A quest gives the characters a clear goal to chase. The goal makes the journey feel exciting and helps the ending feel earned."
        ),
        QAItem(
            question="Why is humor useful in a story?",
            answer="Humor keeps the story light even when things go wrong. It can make a mistake feel friendly enough for the characters to fix together."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
halt_needed(Crew) :- problem(halt), crew(Crew).
submission_needed(Crew) :- problem(submission), crew(Crew).
reconciled(Crew) :- apology(Crew), forgive(Crew).
valid(Place, Quest, Problem, Fix) :- place(Place), quest(Quest), problem(Problem), fix(Fix), compatible(Problem, Quest), works(Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for q in QUESTS:
        lines.append(asp.fact("quest", q.id))
    for p in PROBLEMS.values():
        lines.append(asp.fact("problem", p.id))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        lines.append(asp.fact("works", f.id))
    for q in QUESTS:
        lines.append(asp.fact("compatible", "halt", q.id))
        lines.append(asp.fact("compatible", "submission", q.id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    # smoke test normal generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: story generation failed: {err}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for q in QUESTS:
        for p in PROBLEMS.values():
            for f in FIXES.values():
                if reasonableness_gate(p, q, f):
                    combos.append((q.id, p.id, f.id))
    return combos


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        quest = next(q for q in QUESTS if q.id == params.quest)
        problem = PROBLEMS[params.problem]
        fix = FIXES[params.fix]
    except Exception as err:
        raise StoryError(f"Invalid params: {err}") from err
    if not reasonableness_gate(problem, quest, fix):
        raise StoryError(explain_rejection(problem, quest))
    world = tell(place, quest, problem, fix, params.captain_name, params.pilot_name, params.captain_type, params.pilot_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice([q.id for q in QUESTS])
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[0] == c[0] and c[0] == c[0] and c[0] is not None)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if args.quest and args.problem and args.fix:
        if (args.quest, args.problem, args.fix) not in valid_combos():
            raise StoryError(explain_rejection(PROBLEMS[args.problem], next(q for q in QUESTS if q.id == args.quest)))
    if not combos:
        combos = valid_combos()
    if combos:
        quest, problem, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        quest=quest,
        problem=problem,
        fix=fix,
        captain_name=args.captain_name or rng.choice(["Nova", "Mira", "Luna", "Iris"]),
        pilot_name=args.pilot_name or rng.choice(["Pip", "Joss", "Beck", "Tiko"]),
        captain_type=args.captain_type or "girl",
        pilot_type=args.pilot_type or "boy",
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure reconciliation quest storyworld.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--quest", choices=[q.id for q in QUESTS])
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--fix", choices=list(FIXES))
    ap.add_argument("--captain-name")
    ap.add_argument("--pilot-name")
    ap.add_argument("--captain-type", choices=["girl", "boy"])
    ap.add_argument("--pilot-type", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
