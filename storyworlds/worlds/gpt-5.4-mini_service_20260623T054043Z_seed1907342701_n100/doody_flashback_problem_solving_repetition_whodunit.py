#!/usr/bin/env python3
"""
storyworlds/worlds/doody_flashback_problem_solving_repetition_whodunit.py
=======================================================================

A tiny standalone storyworld about a curious child, a weird doody mystery, a
flashback clue, and a problem-solving ending.

The world is intentionally small and classical:
- one child notices an odd smell or mess
- a helper or parent helps them think back
- repetition of the clue pattern reveals the whodunit
- the story ends with a concrete clean-up image proving what changed
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    scent: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scent_hint: str
    hiding_spot: str
    clue_word: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    habit: str
    scent: str
    can_doody: bool = True


@dataclass
class Problem:
    id: str
    smell: str
    sign: str
    repetition_line: str
    flashback_line: str
    fix_line: str


@dataclass
class Method:
    id: str
    label: str
    action: str
    ending_image: str


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


@dataclass
class StoryParams:
    place: str
    suspect: str
    problem: str
    method: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "bathroom": Place("bathroom", "the bathroom", "soapy and warm", "behind the tub", "tiles"),
    "hall": Place("hall", "the hallway", "dusty and quiet", "by the coat rack", "shoes"),
    "yard": Place("yard", "the yard", "grassy and damp", "under the bush", "grass"),
    "kitchen": Place("kitchen", "the kitchen", "bready and bright", "near the trash can", "crumbs"),
}

SUSPECTS = {
    "puppy": Suspect("puppy", "the puppy", "dog", "wagged around the room", "doggy"),
    "toddler": Suspect("toddler", "the little toddler", "child", "toddled with a snack", "milky"),
    "cat": Suspect("cat", "the cat", "cat", "hid under chairs", "fishy"),
    "bird": Suspect("bird", "the bird", "bird", "fluttered by the window", "seedy"),
}

PROBLEMS = {
    "stinky": Problem("stinky", "a funny doody smell", "little brown smudges", "again and again", "Back then, the smell had been small and easy to miss.", "They needed to figure out who was nearby."),
    "trail": Problem("trail", "a doody trail", "tiny spots on the floor", "two times in a row", "Earlier, the child had seen the same tiny spots near the door.", "They needed to follow the pattern."),
    "spot": Problem("spot", "a doody spot", "a mark on the rug", "from room to room", "A little while ago, the rug had looked clean and ordinary.", "They needed to use the clue and look carefully."),
}

METHODS = {
    "paper": Method("paper", "paper towels", "wipe the floor clean", "The floor was shiny again, and the paper towels were in the trash."),
    "bath": Method("bath", "warm water and soap", "wash the paw", "The puppy's paw was clean, and a fresh towel hung on the hook."),
    "trash": Method("trash", "a bag and a scoop", "scoop the doody away", "The mess was gone, and the trash bag was tied up tight."),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Finn"]
TRAITS = ["curious", "careful", "patient", "brave", "smart"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for suspect in SUSPECTS:
            for problem in PROBLEMS:
                for method in METHODS:
                    if suspect == "bird" and place == "bathroom":
                        continue
                    out.append((place, suspect, problem, method))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny doody mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.problem is None or c[2] == args.problem)
              and (args.method is None or c[3] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, suspect, problem, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(place=place, suspect=suspect, problem=problem, method=method,
                       child=child, child_gender=gender, helper=helper, helper_gender=helper)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    suspect = SUSPECTS[params.suspect]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]

    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    animal = world.add(Entity(id="suspect", kind="character" if suspect.type == "child" else "thing", type=suspect.type, label=suspect.label, place=place.id, scent=suspect.scent))
    world.add(Entity(id="mop", type="tool", label=method.label))
    world.facts = {
        "child": child, "helper": helper, "suspect": animal, "place": place,
        "problem": problem, "method": method, "params": params, "solved": False,
        "noticed": False, "flashback": False, "repeat_line": False,
    }

    child.memes["worry"] += 0
    helper.memes["calm"] += 1
    if suspect.can_doody:
        animal.meters["mess"] += 1

    world.say(f"{child.label} was playing in {place.label} when {child.pronoun().capitalize()} wrinkled {child.pronoun('possessive')} nose.")
    world.say(f"There was {problem.smell}, and {problem.sign} near {place.hiding_spot}.")
    world.para()
    world.say(f"\"Hmm,\" said {helper.label_word if helper.type in ('mother','father') else helper.label}. \"Let's solve this like a whodunit.\"")
    world.say(f"{child.label} looked once, then again, then once more. {problem.repetition_line} {problem.flashback_line}")
    world.say(f"{child.label} remembered the tiny clue and pointed at {suspect.label}. \"It was {suspect.label}, wasn't it?\"")
    world.say(f"{helper.label_word.capitalize()} nodded. \"That makes sense. {problem.fix_line}\"")
    world.para()
    if params.method == "paper":
        world.say(f"Together they used paper towels to {method.action}. {method.ending_image}")
    elif params.method == "bath":
        world.say(f"Together they used warm water and soap to {method.action}. {method.ending_image}")
    else:
        world.say(f"Together they used a bag and a scoop to {method.action}. {method.ending_image}")
    if suspect.type == "dog":
        world.say(f"The puppy wagged and stayed out of the mess. The room smelled clean again.")
    elif suspect.type == "cat":
        world.say(f"The cat sat by the window, looking innocent and neat while the floor was wiped clean.")
    elif suspect.type == "bird":
        world.say(f"The bird hopped to its perch, and the little trail was gone from the floor.")
    else:
        world.say(f"The little toddler was checked, cleaned up, and soon the room was calm again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "doody" and uses a flashback to solve the mystery in {f["place"].label}.',
        f"Tell a gentle mystery where {f['child'].label} notices a {f['problem'].smell} and solves who made it by looking back at an earlier clue.",
        f'Write a simple story with repetition and problem solving, where the clue is in {f["place"].label} and the ending proves the mess got cleaned up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, suspect, place, problem, method = f["child"], f["helper"], f["suspect"], f["place"], f["problem"], f["method"]
    return [
        QAItem(
            question=f"What kind of story is this about {child.label} in {place.label}?",
            answer=f"It is a little whodunit mystery. {child.label} notices a strange clue, thinks back to what happened before, and solves the problem with help.",
        ),
        QAItem(
            question=f"Why did {child.label} think about the clue again and again?",
            answer=f"{child.label} used repetition to notice the pattern. The same small clue showed up more than once, so the answer became easier to see.",
        ),
        QAItem(
            question=f"What did {helper.label_word} help {child.label} do after the flashback?",
            answer=f"{helper.label_word.capitalize()} helped {child.label} think back to the earlier clue and choose a fix. Then they cleaned the mess together.",
        ),
        QAItem(
            question=f"What proved the mystery was solved at the end?",
            answer=f"The floor or the spot was cleaned with {method.label}, so the smell and the mess were gone. The ending image shows the problem was handled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem("What is a flashback in a story?", "A flashback is a part that shows something from before, so the reader can understand the clue better."),
        QAItem("What does problem solving mean?", "Problem solving means thinking carefully, using clues, and choosing a way to fix what is wrong."),
        QAItem("What is repetition?", "Repetition means showing something again and again. In a mystery, that can help make an important clue stand out."),
        QAItem("What does doody mean here?", "Doody means a messy poop, used in a silly child-friendly way in this story."),
    ]
    if f["suspect"].type == "dog":
        out.append(QAItem("Why might a puppy leave a clue in a room?", "A puppy might leave a doody clue if it had an accident and needed help being cleaned up."))
    elif f["suspect"].type == "cat":
        out.append(QAItem("Why do cats sometimes need cleaning help?", "Cats can get messy too, and grown-ups may help wash or wipe them if needed."))
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
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.place:
            bits.append(f"place={e.place}")
        if e.scent:
            bits.append(f"scent={e.scent}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", suspect="puppy", problem="stinky", method="paper", child="Mia", child_gender="girl", helper="mother", helper_gender="mother"),
    StoryParams(place="hall", suspect="cat", problem="trail", method="trash", child="Leo", child_gender="boy", helper="father", helper_gender="father"),
    StoryParams(place="bathroom", suspect="toddler", problem="spot", method="bath", child="Nora", child_gender="girl", helper="mother", helper_gender="mother"),
    StoryParams(place="yard", suspect="bird", problem="stinky", method="paper", child="Ben", child_gender="boy", helper="father", helper_gender="father"),
]


ASP_RULES = r"""
valid(P, S, R, M) :- place(P), suspect(S), problem(R), method(M), not bad_combo(P,S).
bad_combo(bathroom, bird).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for r in PROBLEMS:
        lines.append(asp.fact("problem", r))
    for m in METHODS:
        lines.append(asp.fact("method", m))
    lines.append(asp.fact("bad_combo", "bathroom", "bird"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = 0
    if python_set != clingo_set:
        ok = 1
        print("MISMATCH between clingo and python valid_combos()")
        print("only in clingo:", sorted(clingo_set - python_set))
        print("only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, suspect=None, problem=None, method=None, gender=None, helper=None, name=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = 1
    return ok


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.suspect not in SUSPECTS or params.problem not in PROBLEMS or params.method not in METHODS:
        raise StoryError("Invalid params.")
    if (params.place, params.suspect, params.problem, params.method) not in valid_combos():
        raise StoryError("(No valid story for those options.)")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
