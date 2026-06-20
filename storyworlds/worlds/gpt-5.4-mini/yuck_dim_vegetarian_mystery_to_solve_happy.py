#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yuck_dim_vegetarian_mystery_to_solve_happy.py
==============================================================================

A standalone storyworld for a small comedic mystery with a happy ending:
a child thinks a vegetarian lunch has vanished, follows a few silly clues,
discovers a twist, and ends with everyone laughing over a safe meal.

Seed words:
- yuck-dim
- vegetarian

Features:
- Mystery to Solve
- Happy Ending
- Twist

Style:
- Comedy
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "chef"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher", "chef": "chef"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    mood: str
    mystery: str
    twist_hint: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    clue: str
    silly_tell: str
    innocent: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Solution:
    id: str
    method: str
    reveal: str
    fix: str
    happy_line: str
    sense: int = 3

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if "kid" not in world.entities or "adult" not in world.entities:
        return out
    kid = world.get("kid")
    if kid.memes["worry"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("adult").memes["calm"] += 1
    out.append("__worry__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("revealed"):
        return out
    if world.facts.get("clue_count", 0) >= 2:
        world.facts["revealed"] = True
        out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("reveal", "plot", _r_reveal),
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


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.facts["clue_count"] = sim.facts.get("clue_count", 0) + 2
    _solve(sim, narrate=False)
    return {
        "revealed": sim.facts.get("revealed", False),
        "joy": sim.get("kid").memes["joy"] if "kid" in sim.entities else 0,
    }


def _solve(world: World, narrate: bool = True) -> None:
    world.facts["clue_count"] = world.facts.get("clue_count", 0) + 1
    world.get("kid").memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, scene: Scene, kid: Entity, adult: Entity, suspect: Suspect, lunch: Entity) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon at {scene.place}, {kid.id} found a very odd mystery. "
        f"{scene.mystery}"
    )
    world.say(
        f'{kid.id} held up {lunch.label} and sniffed. "Hmm," {kid.pronoun()} said, '
        f'"this is definitely a {scene.mood} kind of yuck-dim mystery."'
    )
    world.say(
        f'{adult.id} smiled. "Let us look at the clues," {adult.pronoun()} said, '
        f'while {suspect.label} sat nearby looking far too ordinary.'
    )


def clue(world: World, kid: Entity, suspect: Suspect, text: str) -> None:
    kid.memes["worry"] += 1
    world.say(text)
    world.facts["clue_count"] = world.facts.get("clue_count", 0) + 1
    propagate(world, narrate=False)


def mislead(world: World, kid: Entity, suspect: Suspect) -> None:
    world.say(
        f"{kid.id} pointed at {suspect.label}. It had the kind of innocent face "
        f"that made it look guilty in a very silly way."
    )
    world.say(
        f'"Aha!" {kid.id} said. "{suspect.label} is acting suspicious."'
    )


def twist(world: World, adult: Entity, solution: Solution, scene: Scene) -> None:
    adult.memes["pride"] += 1
    world.say(
        f"Then {adult.id} checked the label and laughed. {solution.reveal} "
        f"The whole mystery had been a {scene.twist_hint} twist."
    )
    world.say(
        f"{solution.fix}. {solution.happy_line}"
    )


def ending(world: World, kid: Entity, adult: Entity, scene: Scene, lunch: Entity) -> None:
    kid.memes["joy"] += 2
    kid.memes["relief"] += 2
    adult.memes["joy"] += 1
    world.say(
        f'In the end, {kid.id} grinned at the real answer: {scene.ending_image}. '
        f"{lunch.label_word.capitalize()} was safe, tasty, and vegetarian after all."
    )
    world.say(
        f"{adult.id} handed over a fresh bite, and {kid.id} laughed so hard "
        f"that the mystery almost became dessert."
    )


SCENES = {
    "cafeteria": Scene(
        "cafeteria",
        "the school cafeteria",
        "vegetarian",
        "the missing lunch",
        "sneaky-label",
        "a tray of noodles beside a paper cup of apple slices",
    ),
    "kitchen": Scene(
        "kitchen",
        "the kitchen",
        "yuck-dim",
        "the missing snack",
        "mix-up",
        "a bowl of soup steaming under a cheerful magnet",
    ),
    "picnic": Scene(
        "picnic",
        "the park picnic table",
        "vegetarian",
        "the vanished sandwich",
        "hiding-in-plain-sight",
        "a basket open to tomatoes, crackers, and a smiley napkin",
    ),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "It was napping", "Tiny paw prints on the mat", "one whisker was stuck to a napkin"),
    "brother": Suspect("brother", "big brother", "He had been reading", "A crumb trail to the couch", "he had jam on his cheek"),
    "box": Suspect("box", "the lunch box", "It had not moved", "A sticky note on the lid", "its zipper was open in a very guilty-looking way"),
    "teacher": Suspect("teacher", "the teacher", "She was counting spoons", "The classroom fridge was humming", "she was holding a ladle and a funny grin"),
}

SOLUTIONS = {
    "label": Solution(
        "label",
        "read the label",
        "the lunch was not stolen at all; it had been tucked into the cool shelf with a label that said 'vegetarian'",
        "The teacher moved it back and everyone checked the labels twice",
        "Then the room filled with relieved giggles and very polite munching.",
        sense=3,
    ),
    "mixup": Solution(
        "mixup",
        "open the fridge",
        "the smell came from a pot of vegetable soup, not from the lunch itself",
        "They put the lunch where it belonged and set the soup on the table for anyone who wanted it",
        "After that, nobody sniffed the air without making a dramatic detective face.",
        sense=3,
    ),
    "rabbit": Solution(
        "rabbit",
        "peek behind the table",
        "the mystery culprit was a rabbit nibbling parsley near the garden door",
        "They shooed the rabbit gently away and found the lunch bag exactly where it belonged",
        "The rabbit got a snack of lettuce, which felt fair and also extremely funny.",
        sense=2,
    ),
}

KIDS = ["Mina", "Theo", "Lola", "Finn", "Nora", "Eli", "Ada", "Pip"]
ADULTS = ["Mara", "Ben", "Ivy", "Noah", "June", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene in SCENES:
        for suspect in SUSPECTS:
            for solution in SOLUTIONS.values():
                if solution.sense >= 2:
                    combos.append((scene, suspect, solution.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    suspect: str
    solution: str
    kid: str
    adult: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic vegetarian mystery with a twist and happy ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--kid")
    ap.add_argument("--adult")
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
              if (args.scene is None or c[0] == args.scene)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, suspect, solution = rng.choice(sorted(combos))
    kid = args.kid or rng.choice(KIDS)
    adult = args.adult or rng.choice(ADULTS)
    if kid == adult:
        adult = rng.choice([a for a in ADULTS if a != kid])
    return StoryParams(scene, suspect, solution, kid, adult)


def generate(params: StoryParams) -> StorySample:
    world = World()
    kid = world.add(Entity("kid", kind="character", type="girl" if params.kid in {"Mina", "Lola", "Nora", "Ada"} else "boy", role="detective"))
    kid.id = params.kid
    adult = world.add(Entity("adult", kind="character", type="woman" if params.adult in {"Mara", "Ivy", "June"} else "man", role="helper"))
    adult.id = params.adult
    scene = SCENES[params.scene]
    suspect = SUSPECTS[params.suspect]
    solution = SOLUTIONS[params.solution]
    lunch = world.add(Entity("lunch", type="thing", label="the vegetarian lunch box", label_word="lunch", attrs={"vegetarian": True}))
    world.facts.update(scene=scene, suspect=suspect, solution=solution, lunch=lunch, revealed=False, clue_count=0)
    setup(world, scene, kid, adult, suspect, lunch)
    world.para()
    clue(world, kid, suspect, f"{kid.id} found clue number one: {suspect.clue}.")
    mislead(world, kid, suspect)
    world.para()
    clue(world, kid, suspect, f"Clue number two was even sillier: {suspect.silly_tell}.")
    twist(world, adult, solution, scene)
    world.para()
    ending(world, kid, adult, scene, lunch)
    world.facts.update(outcome="happy", kid=kid, adult=adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    return [
        f'Write a funny mystery story for a child that includes the word "vegetarian" and the phrase "{scene.mystery}".',
        f'Write a comedy story set in {scene.place} where a child follows clues, makes the wrong guess, and then gets a happy twist ending.',
        f'Write a short story with the word "yuck-dim" where a lunch goes missing, but the answer turns out to be harmless and silly.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    kid: Entity = f["kid"]
    adult: Entity = f["adult"]
    suspect: Suspect = f["suspect"]
    solution: Solution = f["solution"]
    lunch: Entity = f["lunch"]
    return [
        ("What kind of story is this?",
         f"It is a funny mystery story. {kid.id} follows clues, gets a little worried, and then learns the answer in a cheerful way."),
        (f"What did {kid.id} think was wrong?",
         f"{kid.id} thought {lunch.label} had gone missing. The yuck-dim clue made it seem extra suspicious, so the mystery felt bigger than it was."),
        (f"Who did {kid.id} suspect?",
         f"{kid.id} suspected {suspect.label}. That guess was wrong, but it was a very silly detective guess and made the story funny."),
        ("What was the twist?",
         f"{solution.reveal[0].upper()}{solution.reveal[1:]}. That changed the whole mystery from spooky to funny and harmless."),
        ("How did the story end?",
         f"It ended happily with everyone laughing and eating safely. {scene.ending_image.capitalize()} showed that the mystery was solved and nothing bad had happened."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does vegetarian mean?",
            answer="Vegetarian means a person does not eat meat. They may eat fruits, vegetables, grains, beans, eggs, or dairy depending on what they choose."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that seems confusing at first. People look for clues until they find the answer."
        ),
        QAItem(
            question="Why do people laugh in a comedy story?",
            answer="Comedy stories use funny surprises, mix-ups, and silly details so the reader smiles or laughs."
        ),
        QAItem(
            question='What does "yuck-dim" suggest in this story?',
            answer='It suggests something a little gross, odd, or funny-sounding, which helps the mystery feel silly instead of scary.'
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cafeteria", "box", "label", "Mina", "Mara"),
    StoryParams("kitchen", "teacher", "mixup", "Theo", "Ben"),
    StoryParams("picnic", "cat", "rabbit", "Lola", "Ivy"),
]


def explain_rejection() -> str:
    return "(No story: that combination would not give a clean mystery-to-solve with a happy comedic twist.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for sid, sol in SOLUTIONS.items():
        if sol.sense >= 2:
            lines.append(asp.fact("solution", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(SC, SU, SO) :- scene(SC), suspect(SU), solution(SO).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    else:
        print("OK: ASP/Python parity and generation smoke test passed.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
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
            header = f"### {p.kid}: {p.scene} / {p.suspect} / {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
