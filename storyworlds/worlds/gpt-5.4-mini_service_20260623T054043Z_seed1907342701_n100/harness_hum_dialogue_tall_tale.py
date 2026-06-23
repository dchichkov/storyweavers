#!/usr/bin/env python3
"""
storyworlds/worlds/harness_hum_dialogue_tall_tale.py
====================================================

A standalone storyworld for a tall-tale style story about a child, a harness,
and a hum that helps a stubborn animal pull through a tricky job.

Seed premise:
- A child wants to help a big, old working horse in a barnyard.
- The horse needs a harness and a calm hum to get moving.
- Something is stuck or spooked, causing tension.
- A helper, a careful harness, and a soft hum turn the moment around.

This world includes:
- typed entities with meters and memes
- a small forward-chaining causal model
- dialogue-driven prose
- a reasonableness gate
- inline ASP twin rules
- three QA sets grounded in world state
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
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    ground: str
    near: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    approach: str
    risk: str
    sign: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    help_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    object: str
    gear: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        other = World(self.place)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_settled(world: World) -> list[str]:
    out: list[str] = []
    horse = world.get("horse")
    if horse.meters["stalled"] < THRESHOLD:
        return out
    if ("settled",) in world.fired:
        return out
    world.fired.add(("settled",))
    horse.memes["calm"] += 1
    out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("settled", "social", _r_settled)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(place: Place, problem: Problem, gear: Gear) -> bool:
    return place.id in PLACES and problem.id in PROBLEMS and gear.id in GEARS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for gear in GEARS:
                if any(tag in PROBLEMS[problem].tags for tag in GEARS[gear].tags):
                    combos.append((place, problem, gear))
    return combos


def make_horse_sound(world: World, horse: Entity) -> None:
    horse.memes["restless"] += 1
    world.say(f'The old horse tossed {horse.pronoun("possessive")} head and gave a long, low hum.')


def setup(world: World, child: Entity, helper: Entity, horse: Entity, gear: Gear, problem: Problem) -> None:
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    horse.memes["restless"] += 1
    world.say(
        f"{child.id} stood in the {world.place.label.lower()} and stared at the big, patient horse."
    )
    world.say(f'"Can we help him pull the cart?" {child.id} asked.')
    world.say(f'"We can if we fit the {gear.label} and keep him calm," {helper.id} said.')
    world.say(f"The cart would not move because the {problem.sign} had made the day feel stuck.")


def fit_gear(world: World, child: Entity, helper: Entity, horse: Entity, gear: Gear) -> None:
    horse.meters["ready"] += 1
    world.say(f'"Hold still," {helper.id} said. "Let me buckle the {gear.label}."')
    world.say(f'"It fits!" {child.id} cried. "Like a moonbeam on a windy roof!"')
    world.say(f"The {gear.label} sat snug and steady, and the horse blinked once, then twice.'")


def calm_with_hum(world: World, child: Entity, helper: Entity, horse: Entity, problem: Problem) -> None:
    horse.memes["trust"] += 1
    horse.meters["stalled"] += 1
    world.say(f'"Hum with me," {helper.id} whispered. "Slow and soft."')
    world.say(f'{child.id} began a tiny tune, and {helper.id} joined in.')
    world.say(f"Before long, the whole barn seemed to hum, and the horse stopped fretting about the {problem.sign}.")


def start_moving(world: World, child: Entity, horse: Entity, place: Place, problem: Problem) -> None:
    horse.meters["moving"] += 1
    world.say(f'"There he goes!" {child.id} shouted.')
    world.say(
        f"The horse leaned into the harness and rolled forward, and the cart sang out over the {place.ground}."
    )
    world.say(f"The {problem.sign} gave way, and the load finally reached the {place.near}.")


def story_ending(world: World, child: Entity, horse: Entity, gear: Gear) -> None:
    world.say(
        f"At the end, {child.id} patted the horse's neck and laughed. "
        f'"You were never stuck," {child.id} said. "You just needed a hum and a harness."'
    )
    world.say(
        f"The horse gave one more easy hum, the {gear.label} stayed bright against the dark coat, and the cart sat where it belonged."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    gear = GEARS[params.gear]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    horse = world.add(Entity(id="Horse", kind="character", type="horse", label="the horse"))
    cart = world.add(Entity(id="Cart", type="thing", label="cart"))
    tack = world.add(Entity(id="Harness", type="thing", label="harness", phrase="a sturdy harness"))

    world.facts.update(
        child=child,
        helper=helper,
        horse=horse,
        cart=cart,
        tack=tack,
        place=place,
        problem=problem,
        gear=gear,
    )

    setup(world, child, helper, horse, gear, problem)
    world.para()
    make_horse_sound(world, horse)
    fit_gear(world, child, helper, horse, gear)
    calm_with_hum(world, child, helper, horse, problem)
    world.para()
    start_moving(world, child, horse, place, problem)
    story_ending(world, child, horse, gear)
    return world


PLACES = {
    "barn": Place(id="barn", label="the barn", ground="packed dirt", near="hay loft", affords={"stalled_cart", "spooked_horse"}),
    "yard": Place(id="yard", label="the yard", ground="sun-baked dust", near="gate", affords={"stalled_cart", "spooked_horse"}),
    "lane": Place(id="lane", label="the lane", ground="red clay", near="road bend", affords={"stalled_cart"}),
    "field": Place(id="field", label="the field", ground="tall grass", near="stone fence", affords={"stalled_cart", "spooked_horse"}),
}

PROBLEMS = {
    "stalled_cart": Problem(id="stalled_cart", verb="move the cart", approach="pull", risk="stuck in place", sign="wheel rut", tags={"cart", "stalled"}),
    "spooked_horse": Problem(id="spooked_horse", verb="settle the horse", approach="hum", risk="jumpy and skittish", sign="big shadow", tags={"horse", "spooked"}),
}

GEARS = {
    "harness": Gear(id="harness", label="harness", phrase="a sturdy harness", help_text="holds the load steady", tags={"cart", "harness"}),
    "bell": Gear(id="bell", label="bell", phrase="a brass bell", help_text="helps the child keep time", tags={"spooked"}),
    "blanket": Gear(id="blanket", label="blanket", phrase="a warm blanket", help_text="keeps the horse from shivering", tags={"horse"}),
    "lamp": Gear(id="lamp", label="lamp", phrase="a small lamp", help_text="lights the road", tags={"cart", "horse"}),
}

GIRL_NAMES = ["Mina", "June", "Ada", "Ruby", "Nell", "Lila"]
BOY_NAMES = ["Eli", "Bram", "Otis", "Pip", "Walt", "Toby"]
TRAITS = ["cheerful", "curious", "bold", "patient"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that includes the words "harness" and "hum" and has dialogue in a barnyard.',
        f"Tell a playful story where {f['child'].id} and {f['helper'].id} help a horse with a {f['problem'].sign}, using a harness and a hum.",
        f"Write a big-voiced, child-friendly tall tale where a harness helps a cart move after someone starts humming.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    horse = f["horse"]
    place = f["place"]
    problem = f["problem"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to help the horse do in the {place.label.lower()}?",
            answer=f"{child.id} wanted to help the horse move the cart. The cart felt stuck because of the {problem.sign}, so the work needed both the harness and a calm hum.",
        ),
        QAItem(
            question=f"Why did {helper.id} say to fit the {gear.label} first?",
            answer=f"{helper.id} said that because the harness would hold the load steady. It gave the horse a safe way to lean into the pull instead of slipping in the {place.ground}.",
        ),
        QAItem(
            question=f"What did {child.id} do after the horse gave that long hum?",
            answer=f"{child.id} started humming too. The two voices made the horse less restless, and that helped the cart get moving.",
        ),
    ]
    if horse.meters["moving"] >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"The horse went from stalled and fussy to moving forward. The harness stayed snug, the hum grew steady, and the cart reached {place.near}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harness?",
            answer="A harness is a set of straps that helps hold and guide an animal or a load. It keeps pulling steady so the work is safer and easier.",
        ),
        QAItem(
            question="What does hum mean?",
            answer="To hum is to make a soft, steady sound with your voice. People hum when they want to calm themselves or keep a rhythm.",
        ),
        QAItem(
            question="Why can a calm sound help a horse?",
            answer="A calm sound can help a horse relax and trust the people nearby. When the horse feels safer, it can pay attention and move more easily.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", problem="stalled_cart", object="cart", gear="harness", name="Mina", gender="girl", helper="father", trait="curious"),
    StoryParams(place="yard", problem="spooked_horse", object="horse", gear="bell", name="Eli", gender="boy", helper="mother", trait="cheerful"),
    StoryParams(place="field", problem="stalled_cart", object="cart", gear="lamp", name="Ruby", gender="girl", helper="father", trait="patient"),
    StoryParams(place="lane", problem="stalled_cart", object="cart", gear="harness", name="Toby", gender="boy", helper="mother", trait="bold"),
]


def explain_rejection(place: Place, problem: Problem, gear: Gear) -> str:
    return f"(No story: the chosen harness, hum, or setting combination does not make a believable tall-tale helper scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale harness-and-hum storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--object", choices=["cart", "horse"])
    ap.add_argument("--gear", choices=GEARS)
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
              and (args.problem is None or c[1] == args.problem)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, object="cart", gear=gear, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.gear not in GEARS:
        raise StoryError("Invalid StoryParams.")
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


ASP_RULES = r"""
fits(G,P) :- gear(G), problem(P).
valid(Pl,Pr,G) :- place(Pl), problem(Pr), gear(G), fits(G,Pr).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for gid, gear in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for tag in sorted(gear.tags):
            lines.append(asp.fact("gear_tag", gid, tag))
    for pid, prob in PROBLEMS.items():
        for tag in sorted(prob.tags):
            lines.append(asp.fact("problem_tag", pid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP/Python parity failed.")
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, object=None, gear=None, gender=None, helper=None, name=None), random.Random(7)))
    if not sample.story:
        print("MISMATCH: story generation failed.")
        return 1
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=False)
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
