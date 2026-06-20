#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cappuccino_mystery_to_solve_myth.py
==================================================================

A standalone story world for a tiny mythic mystery about a cappuccino that
mysteriously changes hands, gets solved through careful noticing, and ends with
a warm shared cup.

The domain is intentionally small: one childlike seeker, one older helper, one
special drink, a quiet place, and a clue trail driven by simulated state.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    quiet: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Clue:
    id: str
    label: str
    hint: str
    physical: str
    emotional: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    text: str
    ending: str
    power: int
    sense: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_found: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.clues_found = list(self.clues_found)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    seeker = world.get("seeker")
    if seeker.memes["uncertainty"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        seeker.memes["fear"] += 1
        out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    if seeker.meters["noticing"] < THRESHOLD:
        return out
    for clue in world.facts["clues"]:
        sig = ("clue", clue.id)
        if sig in world.fired:
            continue
        if clue.id in world.clues_found:
            continue
        world.fired.add(sig)
        world.clues_found.append(clue.id)
        seeker.meters["noticing"] += 1
        seeker.memes["hope"] += 1
        out.append(f"That was a clue.")
        break
    return out


def _r_reveal(world: World) -> list[str]:
    seeker = world.get("seeker")
    if len(world.clues_found) < 2:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["certainty"] += 1
    return ["__reveal__"]


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("clue", "physical", _r_clue),
    Rule("reveal", "social", _r_reveal),
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
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, clue: Clue, solution: Solution) -> bool:
    return clue.id in {"foam_ring", "bean_smell", "tiny_spill"} and solution.sense >= SENSE_MIN


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def solve_mystery(world: World, clue: Clue, solution: Solution) -> None:
    seeker = world.get("seeker")
    helper = world.get("helper")
    seeker.meters["noticing"] += 1
    seeker.memes["uncertainty"] += 1
    world.say(
        f"At {world.setting.place}, under {world.setting.quiet}, {seeker.id} saw "
        f"{world.setting.scene}. The {clue.label} sat where it should not have been, "
        f"and the little cappuccino looked almost like a moon-gold secret."
    )
    world.say(
        f'"Why is the cappuccino missing its soft top?" {seeker.id} asked. '
        f'"{helper.id}, do you know the old answer?"'
    )
    world.para()
    world.say(
        f"{seeker.id} followed {clue.hint}. {clue.physical} {clue.emotional}"
    )
    seeker.meters["noticing"] += 1
    seeker.memes["uncertainty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} leaned close and said the last clue aloud: "
        f'"A cappuccino is made by steaming milk and adding foam. This one was moved, '
        f'but not stolen."'
    )
    world.say(
        f"{solution.text} The mystery solved itself when the missing cup was found in "
        f"{solution.ending}."
    )
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1


SETTING = Setting("temple", "the temple courtyard", "the stone cups", "the morning hush")

CLUES = {
    "foam_ring": Clue("foam_ring", "foam ring", "the seeker noticed the white foam ring", "A little ring of foam glimmered on the rim.", "It made the seeker feel curious rather than scared."),
    "bean_smell": Clue("bean_smell", "bean smell", "the seeker smelled roasted beans near the bench", "A warm bean smell drifted from the bench.", "It made the seeker feel closer to the answer."),
    "tiny_spill": Clue("tiny_spill", "tiny spill", "the seeker followed the tiny spill across the stones", "A tiny brown drip led toward the fountain.", "It made the seeker feel brave enough to keep going."),
}

SOLUTIONS = {
    "owl_helper": Solution("owl_helper", "ask the owl", "So the child asked the owl of the courtyard to remember who carried the cup. The owl had watched everything and pointed toward the bench.", "the bench beside the fountain", 3, 3),
    "saved_for_later": Solution("saved_for_later", "save for later", "So the helper smiled and explained that the cappuccino had only been set aside so it would stay warm. No thief had come at all.", "a covered tray by the hearth", 3, 3),
    "gifted_to_guest": Solution("gifted_to_guest", "gift to guest", "So the helper remembered the visiting pilgrim and said the cup had been given away as a kind gift. The missing drink was now part of a welcome.", "the guest seat by the pillar", 2, 2),
}

KNOWLEDGE = {
    "cappuccino": [("What is a cappuccino?", "A cappuccino is a coffee drink made with steamed milk and foam on top. It is usually served warm in a cup.")],
    "foam": [("What is foam on a drink?", "Foam is the soft bubbly top made by air in milk. It looks fluffy and light.")],
    "beans": [("What are coffee beans?", "Coffee beans are roasted seeds that are ground to make coffee. They have a strong smell and flavor.")],
    "mystery": [("What is a mystery?", "A mystery is a problem that has an answer hidden for a while. People solve it by noticing clues and thinking carefully.")],
    "temple": [("What is a temple courtyard?", "A temple courtyard is an open place near a temple where people can walk, rest, or meet. It often feels quiet and special.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery. Clues can be sights, smells, or little details.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like mystery story for a young child that includes the word "cappuccino" and a clear clue trail.',
        f"Tell a gentle mythic mystery where {f['seeker'].id} notices clues in {world.setting.place} and solves what happened to the cappuccino.",
        f'Write a story in a myth style where a lost cappuccino is explained by noticing foam, smell, or a tiny spill, and the ending feels warm and wise.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    clue = f["clue"]
    sol = f["solution"]
    return [
        ("Who is the story about?", f"It is about {seeker.id} and {helper.id}, who worked together to solve the cappuccino mystery. {helper.id} helped turn the clues into an answer."),
        ("What was the mystery?", f"The mystery was what happened to the cappuccino. It seemed missing at first, so {seeker.id} had to follow clues to learn the truth."),
        ("What clue helped the most?", f"The {clue.label} helped the most because it pointed the seeker toward the answer. It was a small detail, but it mattered in the end."),
        ("How was the mystery solved?", f"{sol.text} That explanation answered why the cappuccino was gone and made the story feel calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue"].id.split())
    out: list[tuple[str, str]] = []
    for tag in ["mystery", "clue", "cappuccino", "foam", "beans", "temple"]:
        if tag in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues found: {world.clues_found}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for clue_id in CLUES:
        for sol_id in SOLUTIONS:
            if reasonableness_gate(SETTING, CLUES[clue_id], SOLUTIONS[sol_id]):
                combos.append((clue_id, sol_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    clue: str
    solution: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    ap = argparse.ArgumentParser(description="Mythic cappuccino mystery story world.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.clue and args.solution:
        if not reasonableness_gate(SETTING, CLUES[args.clue], SOLUTIONS[args.solution]):
            raise StoryError("That clue-solution pair is too thin for a real mystery.")
    combos = [c for c in valid_combos()
              if (args.clue is None or c[0] == args.clue)
              and (args.solution is None or c[1] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, solution = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if seeker_gender == "girl" else "girl")
    seeker = args.seeker or rng.choice(["Mina", "Niko", "Lina", "Taro", "Iris"])
    helper = args.helper or rng.choice(["Sage", "Mara", "Orin", "Dara", "Pax"])
    return StoryParams(clue, solution, seeker, seeker_gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    seeker = world.add(Entity(params.seeker, "character", params.seeker_gender, role="seeker"))
    helper = world.add(Entity(params.helper, "character", params.helper_gender, role="helper"))
    clue = CLUES[params.clue]
    sol = SOLUTIONS[params.solution]
    seeker.memes["uncertainty"] = 1.0
    world.facts.update(seeker=seeker, helper=helper, clue=clue, solution=sol, clues=[clue])
    world.say(
        f"Long ago, in {world.setting.place}, the air was quiet and bright."
        f" {seeker.id} stood beneath {world.setting.quiet} beside {helper.id}, "
        f"and both of them noticed that the cappuccino was gone from its stone cup."
    )
    world.para()
    solve_mystery(world, clue, sol)
    seeker.meters["solved"] += 1
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
clue_valid(C) :- clue(C).
solution_valid(S) :- solution(S), sense(S, N), sense_min(M), N >= M.
valid(C,S) :- clue_valid(C), solution_valid(S).

found_clue(C) :- choose_clue(C), clue(C).
mystery_solved :- found_clue(C1), found_clue(C2), C1 != C2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, sol.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
    sample = generate(resolve_params(argparse.Namespace(clue=None, solution=None, seeker=None, seeker_gender=None, helper=None, helper_gender=None), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generated story is empty.")
    else:
        print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("foam_ring", "owl_helper", "Mina", "girl", "Sage", "boy"),
    StoryParams("bean_smell", "saved_for_later", "Niko", "boy", "Dara", "girl"),
    StoryParams("tiny_spill", "gifted_to_guest", "Lina", "girl", "Orin", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{c} {s}" for c, s in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
