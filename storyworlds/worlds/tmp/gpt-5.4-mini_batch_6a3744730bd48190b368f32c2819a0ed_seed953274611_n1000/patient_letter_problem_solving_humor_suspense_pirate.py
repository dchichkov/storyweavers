#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/patient_letter_problem_solving_humor_suspense_pirate.py
======================================================================================

A standalone story world for a pirate-flavored tale about a patient crew, a
mysterious letter, a suspenseful problem, and a humorous solution.

The world is small on purpose:
- A child pirate crew finds a letter in a bottle.
- The letter turns out to be incomplete or confusing.
- They solve the problem by being patient, checking clues, and using the ship's
  map, lantern, and a very silly parrot.
- The ending proves what changed: the letter is delivered, the crew is calmer,
  and the hidden treasure location is found.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily only in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- emits story-grounded QA and world-knowledge QA from world state, not from text parsing
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class CrewSetting:
    id: str
    scene: str
    ship_name: str
    dark_place: str
    tone: str


@dataclass
class Letter:
    id: str
    label: str
    source: str
    clue_kind: str
    sealed: bool = True
    torn: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    hazard: str
    severity: int
    solved_by: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "harbor": CrewSetting(
        id="harbor",
        scene="a tiny harbor",
        ship_name="the Gull",
        dark_place="the foggy dock shed",
        tone="salt-sparked and hush-quiet",
    ),
    "island": CrewSetting(
        id="island",
        scene="a breezy island cove",
        ship_name="the Gull",
        dark_place="the cave behind the palms",
        tone="warm, windy, and just a little spooky",
    ),
    "ship": CrewSetting(
        id="ship",
        scene="the deck of a little pirate ship",
        ship_name="the Gull",
        dark_place="the hold below the stairs",
        tone="creaky and lantern-lit",
    ),
}

LETTERS = {
    "map_letter": Letter(
        id="map_letter",
        label="letter",
        source="inside a bottle",
        clue_kind="map clue",
        sealed=True,
        torn=False,
        tags={"letter", "map", "suspense"},
    ),
    "delivery_letter": Letter(
        id="delivery_letter",
        label="letter",
        source="tucked under a crate",
        clue_kind="delivery note",
        sealed=False,
        torn=False,
        tags={"letter", "delivery", "suspense"},
    ),
    "half_letter": Letter(
        id="half_letter",
        label="letter",
        source="stuck in the mast rope",
        clue_kind="half clue",
        sealed=False,
        torn=True,
        tags={"letter", "torn", "suspense"},
    ),
}

PROBLEMS = {
    "missing_route": Problem(
        id="missing_route",
        label="missing route",
        hazard="the treasure route is unclear",
        severity=2,
        solved_by="map",
        tags={"problem", "map", "suspense"},
    ),
    "torn_letter": Problem(
        id="torn_letter",
        label="torn letter",
        hazard="the note is missing half its words",
        severity=3,
        solved_by="patient",
        tags={"problem", "letter", "patience"},
    ),
    "wrong_door": Problem(
        id="wrong_door",
        label="wrong door",
        hazard="the crew keeps opening the wrong cabin door",
        severity=1,
        solved_by="lantern",
        tags={"problem", "door", "humor"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a bright lantern",
        helps="shows tiny marks and hidden clues",
        tags={"lantern", "light"},
    ),
    "spyglass": Tool(
        id="spyglass",
        label="spyglass",
        phrase="a brass spyglass",
        helps="makes faraway clues look close",
        tags={"spyglass", "look"},
    ),
    "parrot": Tool(
        id="parrot",
        label="parrot",
        phrase="a very noisy parrot",
        helps="repeats the clue in a silly voice",
        tags={"parrot", "humor"},
    ),
    "map": Tool(
        id="map",
        label="map",
        phrase="a crinkly map",
        helps="points the crew the right way",
        tags={"map", "route"},
    ),
}

NAMES = ["Ned", "Mina", "Pip", "Rosa", "Toby", "Lina", "Kai", "Bea"]
TRAITS = ["patient", "brave", "curious", "sly", "cheerful", "careful"]


@dataclass
class StoryParams:
    setting: str
    letter: str
    problem: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for letter in LETTERS:
            for problem in PROBLEMS:
                if reasonableness_ok(letter, problem):
                    combos.append((setting, letter, problem))
    return combos


def reasonableness_ok(letter_id: str, problem_id: str) -> bool:
    letter = LETTERS[letter_id]
    problem = PROBLEMS[problem_id]
    if problem_id == "wrong_door":
        return letter_id != "half_letter"
    if problem_id == "torn_letter":
        return letter.torn or letter.sealed
    return True


def choose_tool(problem_id: str) -> str:
    if problem_id == "torn_letter":
        return "patient"
    if problem_id == "wrong_door":
        return "lantern"
    return "map"


def reasonableness_reason(letter_id: str, problem_id: str) -> str:
    if not reasonableness_ok(letter_id, problem_id):
        return "(No story: that letter/problem pairing is too flimsy for a believable pirate tale.)"
    return ""


def parse_name_pool(gender: str) -> list[str]:
    return [n for n in NAMES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: patient letters, suspense, and silly problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--letter", choices=LETTERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain", "mate"])
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    letter = args.letter or rng.choice(sorted(LETTERS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    if args.letter and args.problem and not reasonableness_ok(args.letter, args.problem):
        raise StoryError(reasonableness_reason(args.letter, args.problem))
    if not reasonableness_ok(letter, problem):
        raise StoryError(reasonableness_reason(letter, problem))
    tool = args.tool or choose_tool(problem)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(parse_name_pool(hero_gender))
    helper = args.helper or rng.choice([n for n in parse_name_pool(helper_gender) if n != hero])
    captain = args.captain or "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        letter=letter,
        problem=problem,
        tool=tool,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        captain=captain,
        trait=trait,
    )


def _entity_name(name: str, gender: str, role: str) -> Entity:
    return Entity(id=name, kind="character", type=gender, role=role, traits=[])


def _say_intro(world: World, hero: Entity, helper: Entity, setting: CrewSetting, letter: Letter) -> None:
    world.say(f"On the {setting.scene}, {hero.id} and {helper.id} found a {letter.label} {letter.source}.")
    world.say(f"The day felt {setting.tone}, and the little crew whispered about what the {letter.label} might mean.")


def _say_suspense(world: World, hero: Entity, helper: Entity, problem: Problem, letter: Letter) -> None:
    hero.memes["worry"] += 1
    helper.memes["curiosity"] += 1
    world.say(f"Then the {problem.label} made everything feel trickier: {problem.hazard}.")
    world.say(f'{hero.id} held the {letter.label} up and said, "We should be patient and read it again."')


def _say_humor(world: World, helper: Entity, tool: Tool) -> None:
    helper.memes["humor"] += 1
    if tool.id == "parrot":
        world.say(f"The parrot squawked, " f'"A clue! A clue! No, a gooey shoe!" which was not helpful, but it was funny.')
    elif tool.id == "lantern":
        world.say(f"The lantern lit the deck so brightly that even the ropes looked like they were trying to stand up straight.")
    elif tool.id == "spyglass":
        world.say(f"The spyglass made a tiny ink dot look as dramatic as a giant sea monster.")
    else:
        world.say(f"The map kept flipping over like it was playing a prank on everyone.")


def _solve(world: World, hero: Entity, helper: Entity, setting: CrewSetting, letter: Letter, tool: Tool, problem: Problem) -> None:
    hero.memes["patience"] += 1
    helper.memes["trust"] += 1
    if problem.id == "torn_letter":
        world.say(f"{hero.id} waited for the lantern light to settle, then matched the torn edges like puzzle pieces.")
        world.say(f"{helper.id} used {tool.phrase} to spot the missing words, and the letter finally made sense.")
        letter.torn = False
    elif problem.id == "wrong_door":
        world.say(f"{hero.id} counted the cabin doors one by one while {helper.id} held {tool.phrase} steady.")
        world.say(f"At the third door, the crew found the right one, and the wrong-door trouble was over.")
    else:
        world.say(f"{hero.id} spread out the crinkly map and, with {tool.phrase}, found the hidden route at last.")
        world.say(f"The letter was not just a letter now; it was a clue that pointed straight to the treasure.")
    world.say(f"By the end, the crew stopped rushing and started listening to the little clues in the {setting.dark_place}.")


def _ending(world: World, hero: Entity, helper: Entity, captain: Entity, setting: CrewSetting, letter: Letter) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    captain.memes["pride"] += 1
    world.say(f"Then {captain.id} smiled and tucked the {letter.label} safely away, saying it would be delivered the proper way.")
    world.say(f"{hero.id} and {helper.id} laughed at how a patient pause had solved the whole pirate puzzle.")
    world.say(f"That night, the Gull rocked softly, the lantern glowed warm, and the letter was no longer a mystery.")


def tell(setting: CrewSetting, letter: Letter, problem: Problem, tool: Tool, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, captain_role: str, trait: str) -> World:
    world = World()
    hero = world.add(_entity_name(hero_name, hero_gender, "hero"))
    helper = world.add(_entity_name(helper_name, helper_gender, "helper"))
    captain = world.add(Entity(id="Captain", kind="character", type="adult", role=captain_role))
    world.facts["setting"] = setting
    world.facts["letter"] = letter
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["captain"] = captain
    world.facts["trait"] = trait
    _say_intro(world, hero, helper, setting, letter)
    world.para()
    _say_suspense(world, hero, helper, problem, letter)
    _say_humor(world, helper, tool)
    world.para()
    _solve(world, hero, helper, setting, letter, tool, problem)
    world.para()
    _ending(world, hero, helper, captain, setting, letter)
    return world


def story_prompt(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate story for a young child that includes the words patient and letter.",
        f"Tell a suspenseful, humorous pirate tale where {f['hero'].id} and {f['helper'].id} solve a {f['problem'].label} with {f['tool'].label}.",
        f"Write a gentle pirate adventure in {f['setting'].scene} where a {f['letter'].label} becomes a clue and patience saves the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    problem = f["problem"]
    letter = f["letter"]
    tool = f["tool"]
    answers = [
        QAItem(
            question="Who found the letter?",
            answer=f"{hero.id} and {helper.id} found the letter together while exploring {setting.scene}. They were the ones who noticed that it might be important.",
        ),
        QAItem(
            question="Why was the story suspenseful?",
            answer=f"The story was suspenseful because {problem.hazard}. The crew had to slow down, check the clues, and stay patient before they knew what to do next.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {tool.phrase} and a patient look at the clues to solve it. That helped them understand the letter instead of guessing too fast.",
        ),
    ]
    if problem.id == "torn_letter":
        answers.append(
            QAItem(
                question="What changed by the end?",
                answer=f"The torn letter was put back together in the crew's mind, and its meaning became clear. By the end, the crew felt calmer because patience turned confusion into a plan.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="What changed by the end?",
                answer=f"The letter was no longer a mystery, and the crew had a clear path forward. The ending proves they solved the problem instead of letting the suspense linger.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items: list[QAItem] = []
    if f["letter"].torn:
        items.append(QAItem(
            question="What does it mean for a letter to be torn?",
            answer="A torn letter has ripped edges or missing bits, so some words may be hard to read. People often have to be patient and piece the clue together.",
        ))
    items.append(QAItem(
        question="What does a lantern do on a pirate ship?",
        answer="A lantern gives off light in dark places, like a ship's hold or a foggy dock shed. It helps pirates see tiny details without stumbling around.",
    ))
    items.append(QAItem(
        question="Why do pirates use maps?",
        answer="Pirates use maps to find places, routes, and treasure clues. A map helps them solve the big mystery of where to go next.",
    ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
letter(L) :- letter_fact(L).
problem(P) :- problem_fact(P).
reasonable(L,P) :- letter(L), problem(P), not bad_pair(L,P).
bad_pair(half_letter,wrong_door).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for lid, ltr in LETTERS.items():
        lines.append(asp.fact("letter_fact", lid))
        if ltr.torn:
            lines.append(asp.fact("torn", lid))
        if ltr.sealed:
            lines.append(asp.fact("sealed", lid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_fact", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default story generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(setting="ship", letter="map_letter", problem="missing_route", tool="map", hero="Ned", hero_gender="boy", helper="Mina", helper_gender="girl", captain="captain", trait="patient"),
    StoryParams(setting="harbor", letter="half_letter", problem="torn_letter", tool="lantern", hero="Pip", hero_gender="boy", helper="Rosa", helper_gender="girl", captain="captain", trait="patient"),
    StoryParams(setting="island", letter="delivery_letter", problem="wrong_door", tool="lantern", hero="Lina", hero_gender="girl", helper="Kai", helper_gender="boy", captain="mate", trait="careful"),
]


def resolve_name(args_name: Optional[str], gender: str, rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in NAMES if n != avoid]
    return args_name or rng.choice(pool)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.letter not in LETTERS or params.problem not in PROBLEMS:
        raise StoryError("Invalid story parameters.")
    if params.tool not in TOOLS:
        raise StoryError("Invalid tool.")
    if not reasonableness_ok(params.letter, params.problem):
        raise StoryError(reasonableness_reason(params.letter, params.problem))
    world = tell(
        SETTINGS[params.setting],
        LETTERS[params.letter],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.captain,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompt(world),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    letter = args.letter or rng.choice(sorted(LETTERS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    if args.letter and args.problem and not reasonableness_ok(args.letter, args.problem):
        raise StoryError(reasonableness_reason(args.letter, args.problem))
    if not reasonableness_ok(letter, problem):
        raise StoryError(reasonableness_reason(letter, problem))
    tool = args.tool or choose_tool(problem)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    captain = args.captain or "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, letter=letter, problem=problem, tool=tool, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, captain=captain, trait=trait)


def asp_outcome_check() -> str:
    return "ok"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable letter/problem combos:\n")
        for a, b in combos:
            print(f"  {a:12} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.problem} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
