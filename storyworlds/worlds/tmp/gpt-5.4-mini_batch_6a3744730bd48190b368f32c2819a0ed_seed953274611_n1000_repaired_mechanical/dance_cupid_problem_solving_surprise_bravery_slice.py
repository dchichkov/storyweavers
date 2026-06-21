#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dance_cupid_problem_solving_surprise_bravery_slice.py
=====================================================================================

A small slice-of-life storyworld about a child dance rehearsal, a surprising
decorated prop, a brave fix, and a calm ending image.

Seed words:
- dance
- cupid

Features:
- Problem Solving
- Surprise
- Bravery

This script is standalone and uses only the Python stdlib plus the shared
storyworlds/results.py containers. ASP support is inline and imported lazily.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    surprise: str
    fix_hint: str
    risk: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    action: str
    cost: int
    power: int
    result_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["tangled"] < THRESHOLD:
            continue
        sig = ("tangled", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__tangle__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    sim.get("prop").meters["tangled"] += 1
    propagate(sim, narrate=False)
    return {"tangled": sim.get("prop").meters["tangled"] >= THRESHOLD, "worry": sim.get("team").memes["worry"]}


def solve_problem(world: World, fix: Fix, problem: Problem, narrate: bool = True) -> None:
    world.get("prop").meters["tangled"] = 0.0
    world.get("team").memes["worry"] = 0.0
    if narrate:
        world.say(fix.result_line.format(problem=problem.label))


def tell(place: Place, problem: Problem, fix: Fix, child_name: str, child_type: str,
         helper_name: str, helper_type: str, surprise_name: str) -> World:
    w = World()
    child = w.add(Entity(id=child_name, kind="character", type=child_type, role="dancer"))
    helper = w.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    team = w.add(Entity(id="team", kind="group", label="the little dance team"))
    prop = w.add(Entity(id="prop", kind="thing", label="the ribbon hoop"))
    stage = w.add(Entity(id="stage", kind="place", label=place.label))
    cupid = w.add(Entity(id="cupid", kind="thing", label=surprise_name, tags={"cupid"}))
    w.facts.update(child=child, helper=helper, team=team, prop=prop, stage=stage,
                   cupid=cupid, place=place, problem=problem, fix=fix)

    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    w.say(
        f"On a quiet afternoon at {place.label}, {child.id} and {helper.id} practiced a dance. "
        f"The music was soft, and {child.id} kept time by tapping {child.pronoun('possessive')} shoes."
    )
    w.say(
        f"Then came a surprise: a tiny cupid decoration had fallen into the ribbon hoop. "
        f"It peeked out like a secret, and everyone froze for a second."
    )
    w.para()
    w.say(
        f"{child.id} took a small breath. {child.pronoun().capitalize()} did not shout. "
        f"Instead, {child.pronoun()} said, \"Let's solve it.\""
    )
    predicted = predict_problem(w, problem)
    w.facts["predicted"] = predicted
    if predicted["tangled"]:
        child.memes["bravery"] += 1
        helper.memes["trust"] += 1
        w.say(
            f"The hoop could get tangled if they kept dancing with it, and that would make the next step messy. "
            f"So {helper.id} held the hoop steady while {child.id} slipped the cupid piece out."
        )
    else:
        w.say(f"The surprise was harmless, but they still set it on the bench so the floor would stay clear.")
    w.para()
    child.memes["bravery"] += 1
    helper.memes["relief"] += 1
    solve_problem(w, fix, problem)
    w.say(
        f"After that, {child.id} tried the dance again. {fix.action}, and the ribbon trail moved in a neat bright arc."
    )
    w.say(
        f"The little cupid sat on the bench watching them spin, and the room felt warm, calm, and ready for the next song."
    )
    w.facts["resolved"] = True
    return w


PLACE_REGISTRY = {
    "community_center": Place(id="community_center", label="the community center", cozy=True, tags={"dance", "slice"}),
    "school_gym": Place(id="school_gym", label="the school gym", cozy=False, tags={"dance", "slice"}),
    "living_room": Place(id="living_room", label="the living room", cozy=True, tags={"dance", "slice"}),
}

PROBLEM_REGISTRY = {
    "tangle": Problem(
        id="tangle",
        label="a tangled ribbon hoop",
        surprise="cupids",
        fix_hint="untangle the ribbon before the next song",
        risk="the ribbon could snag a shoe and spoil the turn",
        tags={"problem", "surprise", "dance", "cupid"},
    ),
    "spill": Problem(
        id="spill",
        label="a spilled cup of glitter water",
        surprise="cupids",
        fix_hint="wipe the floor and move the cups away",
        risk="the floor could get slippery",
        tags={"problem", "surprise", "dance"},
    ),
}

FIX_REGISTRY = {
    "careful_unwind": Fix(
        id="careful_unwind",
        label="careful hands",
        action="they gently unwound the ribbon and laid the hoop flat",
        cost=1,
        power=2,
        result_line="Their careful hands fixed {problem} without hurting the dance",
        tags={"problem", "bravery"},
    ),
    "towel_and_shift": Fix(
        id="towel_and_shift",
        label="a towel and a chair",
        action="they slid a towel under the wet spot and moved the water aside",
        cost=1,
        power=2,
        result_line="The towel and chair solved {problem} in a calm, smart way",
        tags={"problem"},
    ),
}

NAMES_GIRL = ["Mina", "Lena", "Sofia", "Nia", "Pia", "Tessa"]
NAMES_BOY = ["Owen", "Theo", "Luca", "Evan", "Milo", "Noah"]
HELPER_NAMES = ["Rae", "Iris", "Ben", "June", "Kai", "Mara"]


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    cupid_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACE_REGISTRY:
        for prob in PROBLEM_REGISTRY:
            for fix in FIX_REGISTRY:
                combos.append((pid, prob, fix))
    return combos


def explain_invalid(problem: Problem, fix: Fix) -> str:
    return f"(No story: the chosen fix does not fit the problem '{problem.label}'. Try a calmer problem-solving move.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life dance storyworld with surprise, bravery, and problem solving.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEM_REGISTRY)
    ap.add_argument("--fix", choices=FIX_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--cupid-name", default="cupid")
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
    if args.place and args.problem and args.fix:
        if (args.place, args.problem, args.fix) not in valid_combos():
            raise StoryError(explain_invalid(PROBLEM_REGISTRY[args.problem], FIX_REGISTRY[args.fix]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    child_type = rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY)
    helper_type = "girl" if child_type == "boy" else "boy"
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if helper_name == child_name:
        helper_name = helper_name + "y"
    return StoryParams(
        place=place,
        problem=problem,
        fix=fix,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        cupid_name=args.cupid_name,
    )


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "problem", "fix"):
        if key not in params.__dict__:
            raise StoryError(f"Missing StoryParams field: {key}")
    if params.place not in PLACE_REGISTRY or params.problem not in PROBLEM_REGISTRY or params.fix not in FIX_REGISTRY:
        raise StoryError("(Invalid params: unknown registry key.)")
    world = tell(
        PLACE_REGISTRY[params.place],
        PROBLEM_REGISTRY[params.problem],
        FIX_REGISTRY[params.fix],
        params.child_name,
        params.child_type,
        params.helper_name,
        params.helper_type,
        params.cupid_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child about a dance practice at {f["place"].label} that includes the word "dance".',
        f'Write a gentle story where a surprise cupid decoration appears during a dance and the children solve the problem calmly.',
        f'Write a short story about bravery and problem solving at a small dance rehearsal with a cupid surprise.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    qa = [
        ("Where did the story happen?", f"It happened at {place.label}. The setting stayed ordinary and cozy, like a real afternoon practice."),
        ("What surprise showed up?", f"A tiny cupid decoration showed up inside the ribbon hoop. That surprise changed the mood for a moment and made everyone pause."),
        ("How did they solve the problem?", f"{child.id} stayed brave and said they should solve it, then {helper.id} helped with careful hands. They fixed {problem.label} before the next dance step."),
        ("How did the child feel at the end?", f"{child.id} felt proud and calm. The problem was solved, so the dance could go on with a brighter, safer feeling."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cupid?", "A cupid is a little figure often shown with wings and a bow. It can be used as a decoration in a story or a holiday display."),
        ("What does it mean to solve a problem?", "It means you look at what is wrong and find a good way to fix it. A good solution makes the situation easier or safer."),
        ("What does bravery look like?", "Bravery means doing the helpful thing even when you feel startled or nervous. It can be quiet and calm, not loud."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R, F) :- place(P), problem(R), fix(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in PLACE_REGISTRY:
        lines.append(asp.fact("place", k))
    for k in PROBLEM_REGISTRY:
        lines.append(asp.fact("problem", k))
    for k in FIX_REGISTRY:
        lines.append(asp.fact("fix", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, fix=None, name=None, helper_name=None, cupid_name="cupid"), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(place="community_center", problem="tangle", fix="careful_unwind", child_name="Mina", child_type="girl", helper_name="Ben", helper_type="boy", cupid_name="cupid"),
    StoryParams(place="living_room", problem="spill", fix="towel_and_shift", child_name="Owen", child_type="boy", helper_name="Mara", helper_type="girl", cupid_name="cupid"),
]


def world_knowledge_story_tags(world: World) -> set[str]:
    return {"dance", "cupid", "problem", "bravery"}


def generate_qa_sets(sample: StorySample) -> None:
    return None


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place} ({p.problem}, {p.fix})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
