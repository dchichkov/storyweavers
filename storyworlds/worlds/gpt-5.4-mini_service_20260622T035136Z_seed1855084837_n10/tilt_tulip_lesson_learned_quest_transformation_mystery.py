#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035136Z_seed1855084837_n10/tilt_tulip_lesson_learned_quest_transformation_mystery.py
=================================================================================================

A compact mystery storyworld about a child solving a small garden puzzle, making
a quest, learning a lesson, and seeing a transformation at the end.

Seed story sketch:
---
A child notices a strange tilt in a flower bed. A tulip is missing from its pot,
and little muddy tracks lead away from the porch. The child follows the tracks,
asks a neighbor, and discovers the tulip had been moved into the shed by mistake.
After bringing it back, the child tilts the pot the other way to let the roots
rest, and the tulip straightens up in the sun.

World model:
---
    object tilt / move     -> object.position, object.angle change
    object hidden in shed  -> search shows clue trail; owner worry rises
    bring tulip home       -> tulip.hydration recovers, owner relief rises
    lesson learned         -> child caution/attention rises
    transformation        -> tulip.opens and child notices the garden looks new

Style:
---
Mystery-first, child-facing, concrete, with a clear clue trail and a gentle
ending image proving what changed.
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

# Robust import of shared result containers and lazy ASP helper access.
_HERE = os.path.abspath(__file__)
_ROOT = os.path.dirname(_HERE)
while True:
    if os.path.exists(os.path.join(_ROOT, "results.py")):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent
sys.path.insert(0, _ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    location: str = ""
    color: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    tulip_color: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    clue_spot: str
    weather: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Puzzle:
    id: str
    clue: str
    trail: str
    discovery: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transform:
    id: str
    action: str
    result: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.history: list[str] = []
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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.history = list(self.history)
        clone.paragraphs = [list(p) for p in self.paragraphs]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "porch": Setting(place="the porch garden", clue_spot="the porch step", weather="warm", mood="quiet", tags={"garden", "porch"}),
    "backyard": Setting(place="the backyard garden", clue_spot="the flower bed edge", weather="soft", mood="hushed", tags={"garden", "backyard"}),
    "greenhouse": Setting(place="the greenhouse path", clue_spot="the potting bench", weather="glassy", mood="still", tags={"greenhouse", "garden"}),
}

PUZZLES = {
    "track": Puzzle(id="track", clue="muddy little footprints", trail="a line of muddy little footprints", discovery="the footprints led to the shed door", tags={"clue", "mud"}),
    "tilt": Puzzle(id="tilt", clue="a strange tilt", trail="a strange tilt in the pot stand", discovery="the tilt showed the tulip had been moved", tags={"tilt", "pot"}),
    "petal": Puzzle(id="petal", clue="a single crushed petal", trail="a single crushed petal on the step", discovery="the petal hinted the tulip had been carried carefully", tags={"petal", "clue"}),
}

TRANSFORMS = {
    "straighten": Transform(id="straighten", action="tilt the pot back", result="the tulip lifted its head again", ending_image="the tulip stood straight in the sun", tags={"tilt", "tulip"}),
    "bloom": Transform(id="bloom", action="water the roots and wait", result="the bud opened into a brighter flower", ending_image="the tulip opened wide like a tiny flag", tags={"tulip", "flower"}),
    "return": Transform(id="return", action="bring the pot home", result="the tulip looked awake again", ending_image="the tulip glowed at the center of the bed", tags={"tulip", "home"}),
}

CHILDREN = [("Maya", "girl"), ("Leo", "boy"), ("Nina", "girl"), ("Owen", "boy"), ("Ruby", "girl"), ("Finn", "boy")]
HELPERS = [("Aunt June", "woman"), ("Dad", "father"), ("Mom", "mother"), ("Mr. Bell", "man")]
COLORS = ["red", "pink", "gold", "white", "purple"]


def choose_combo(place: Optional[str], puzzle: Optional[str], transform: Optional[str]) -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        if place and p != place:
            continue
        for q in PUZZLES:
            if puzzle and q != puzzle:
                continue
            for t in TRANSFORMS:
                if transform and t != transform:
                    continue
                combos.append((p, q, t))
    return combos


def valid_combos() -> list[tuple[str, str, str]]:
    return choose_combo(None, None, None)


def explain_rejection() -> str:
    return "(No story: the requested choices do not fit this small mystery garden world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery garden storyworld about tilt, tulip, lesson learned, quest, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--color", choices=COLORS)
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
              and (args.puzzle is None or c[1] == args.puzzle)
              and (args.transform is None or c[2] == args.transform)]
    if not combos:
        raise StoryError(explain_rejection())
    place, puzzle, transform = rng.choice(sorted(combos))
    child_name, child_type = (args.name, args.child_type) if args.name and args.child_type else rng.choice(CHILDREN)
    helper_name = args.helper or rng.choice(HELPERS)[0]
    helper_type = args.helper_type or rng.choice(HELPERS)[1]
    color = args.color or rng.choice(COLORS)
    return StoryParams(place=place, child_name=child_name, child_type=child_type, helper_name=helper_name, helper_type=helper_type, tulip_color=color)


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    tulip = world.add(Entity(id="tulip", kind="thing", type="thing", label="tulip", phrase=f"a {params.tulip_color} tulip", location="bed", color=params.tulip_color, tags={"tulip", "flower"}))
    pot = world.add(Entity(id="pot", kind="thing", type="thing", label="pot", phrase="a clay pot", location="bed", tags={"pot"}))
    shed = world.add(Entity(id="shed", kind="thing", type="thing", label="shed", phrase="the shed", location="yard", tags={"shed"}))
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    helper.memes["calm"] += 1
    world.facts.update(child=child, helper=helper, tulip=tulip, pot=pot, shed=shed)
    return world


def predict_loss(world: World) -> bool:
    sim = world.copy()
    return sim.get("tulip").location == "shed" and sim.get("pot").meters["tilt"] >= THRESHOLD


def tell_story(world: World, puzzle: Puzzle, transform: Transform) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    tulip = world.facts["tulip"]
    pot = world.facts["pot"]
    shed = world.facts["shed"]

    world.say(f"On {world.setting.place}, {child.label} noticed {puzzle.clue} near {world.setting.clue_spot}.")
    world.say(f"The little mystery felt odd, because the tulip in its bed had gone quiet and the pot showed {puzzle.clue}.")
    world.para()
    world.say(f"{child.label} began a small quest, following {puzzle.trail} past the porch and toward the shed.")
    world.say(f"The trail ended there, and {puzzle.discovery}.")
    if predict_loss(world):
        child.memes["alarm"] += 1
    world.para()
    world.say(f"{helper.label} listened, then helped {child.label} {transform.action}.")
    pot.meters["tilt"] = 0.0
    tulip.meters["hydration"] += 1
    tulip.meters["open"] += 1
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    tulip.location = "bed"
    world.say(f"That was the lesson learned: a small mistake could hide a flower, but a careful look could bring it home.")
    world.para()
    world.say(f"By the end, {transform.result}, and {transform.ending_image}.")
    world.facts.update(puzzle=puzzle, transform=transform, resolved=True)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery for a 3-to-5-year-old that includes the words "tilt" and "tulip".',
        f"Tell a gentle quest story where {f['child'].label} follows clues in {world.setting.place} to find a tulip and learns a lesson.",
        f"Write a child-sized mystery about a strange tilt, a missing tulip, and a happy transformation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    tulip = f["tulip"]
    puzzle = f["puzzle"]
    transform = f["transform"]
    return [
        QAItem(
            question=f"What mystery did {child.label} notice at {world.setting.place}?",
            answer=f"{child.label} noticed {puzzle.clue}. That clue made the garden feel puzzling, so {child.label} started to look more carefully.",
        ),
        QAItem(
            question=f"Where did the quest lead {child.label}?",
            answer=f"It led toward the shed, following {puzzle.trail}. The trail mattered because it showed where the tulip had been taken.",
        ),
        QAItem(
            question=f"How did {helper.label} help with the tulip problem?",
            answer=f"{helper.label} listened and helped {child.label} {transform.action}. That careful help let the tulip come back to its bed and learn to stand right again.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The lesson was learned, and the tulip transformed. {transform.ending_image}, which proved the mystery had been solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flower with smooth petals and a tall stem. It often stands up neatly in a garden bed.",
        ),
        QAItem(
            question="What does it mean to tilt something?",
            answer="To tilt something means to lean it to one side. When something tilts, it is not standing straight anymore.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a little piece of information that helps someone solve a mystery. Clues can be tracks, marks, or a strange shape.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.tulip_color not in COLORS:
        raise StoryError("Invalid parameters for this garden mystery.")
    world = _make_world(params)
    puzzle = PUZZLES.get("tilt") if params.place == "greenhouse" else PUZZLES.get("track")
    transform = TRANSFORMS["straighten"] if params.place != "greenhouse" else TRANSFORMS["bloom"]
    tell_story(world, puzzle, transform)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            parts = []
            if meters:
                parts.append(f"meters={dict(meters)}")
            if memes:
                parts.append(f"memes={dict(memes)}")
            if e.location:
                parts.append(f"location={e.location}")
            if e.color:
                parts.append(f"color={e.color}")
            print(f"  {e.id:8} ({e.kind:7}) {' '.join(parts)}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
mystery_clue(tilt) :- clue_word(tilt).
mystery_clue(tulip) :- clue_word(tulip).
valid_story(P, Q, T) :- place(P), puzzle(Q), transform(T), clue_word(tilt), clue_word(tulip).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in PUZZLES:
        lines.append(asp.fact("puzzle", q))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    lines.append(asp.fact("clue_word", "tilt"))
    lines.append(asp.fact("clue_word", "tulip"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos_py = set(valid_combos())
    combos_as = set(asp_valid_combos())
    ok = True
    if combos_py != combos_as:
        ok = False
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, puzzle=None, transform=None, name=None, child_type=None, helper=None, helper_type=None, color=None, n=1, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(777)))
        assert sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed ({len(combos_py)} combos).")
        return 0
    return 1


CURATED = [
    StoryParams(place="porch", child_name="Maya", child_type="girl", helper_name="Mom", helper_type="mother", tulip_color="pink"),
    StoryParams(place="backyard", child_name="Leo", child_type="boy", helper_name="Dad", helper_type="father", tulip_color="red"),
    StoryParams(place="greenhouse", child_name="Ruby", child_type="girl", helper_name="Aunt June", helper_type="woman", tulip_color="gold"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
