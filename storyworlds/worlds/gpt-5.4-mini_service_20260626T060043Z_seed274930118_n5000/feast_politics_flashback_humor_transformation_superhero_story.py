#!/usr/bin/env python3
"""
storyworlds/worlds/feast_politics_flashback_humor_transformation_superhero_story.py
===================================================================================

A standalone story world inspired by a small superhero tale:
a feast is planned, politics gets in the way, a flashback explains why the hero
cares, humor lightens the tension, and a transformation turns the ending into a
true save-the-day image.

The world is tiny and classical:
- one hero
- one civic problem
- one feast
- one political obstacle
- one transformation that resolves the story

The prose is driven by simulated world state, not a frozen template.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "mayor"}
        male = {"boy", "man", "father", "king", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    name: str
    indoor: bool = False
    holds_feast: bool = False
    politics: bool = False


@dataclass
class Feast:
    id: str
    label: str
    feast_food: str
    joy_word: str
    fuss_word: str
    place_ok: set[str] = field(default_factory=set)


@dataclass
class PoliticalProblem:
    id: str
    label: str
    issue: str
    rumor: str
    blocker: str
    fix_hint: str


@dataclass
class Power:
    id: str
    label: str
    trigger: str
    form: str
    effect: str
    transformation_word: str
    flare: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_done = False
        self.transformed = False

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
        clone = World(self.place)
        clone.entities = dataclasses.replace(self) if False else self.entities.copy()
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_done = self.flashback_done
        clone.transformed = self.transformed
        return clone


def _meter(obj, key: str) -> float:
    return float(obj.meters.get(key, 0.0))


def _mem(obj, key: str) -> float:
    return float(obj.memes.get(key, 0.0))


def _add_meter(obj, key: str, amount: float) -> None:
    obj.meters[key] = _meter(obj, key) + amount


def _add_mem(obj, key: str, amount: float) -> None:
    obj.memes[key] = _mem(obj, key) + amount


def _clamp01(v: float) -> float:
    return max(0.0, v)


def introduce(world: World, hero: Entity, sidekick: Entity, feast: Feast, problem: PoliticalProblem) -> None:
    world.say(
        f"{hero.id} was a small hero with a bright cape and a bigger job than anyone expected."
    )
    world.say(
        f"At {world.place.name}, a feast was being planned with {feast.feast_food}, but politics had turned the hall noisy and sour."
    )
    world.say(
        f"{hero.id} and {sidekick.id} both wanted the feast to feel warm again."
    )
    world.facts["introduced"] = True


def flashback(world: World, hero: Entity, feast: Feast, power: Power) -> None:
    if world.flashback_done:
        return
    world.flashback_done = True
    hero.memes["nostalgia"] = _mem(hero, "nostalgia") + 1
    world.say(
        f"Flashback: when {hero.id} was little, {hero.pronoun('possessive')} favorite thing was a tiny kitchen feast with one candle and one kind smile."
    )
    world.say(
        f"That memory taught {hero.id} that a shared meal could calm even a grumpy room."
    )
    world.facts["flashback"] = True
    world.facts["power_trigger"] = power.trigger


def politics_stirs(world: World, hero: Entity, problem: PoliticalProblem) -> None:
    if ("politics", problem.id) in world.fired:
        return
    world.fired.add(("politics", problem.id))
    _add_mem(hero, "worry", 1)
    _add_mem(hero, "duty", 1)
    world.say(
        f"The council argued that {problem.issue}, and a rumor tried to make the feast look less fair."
    )
    world.say(
        f"{hero.id} frowned because {problem.blocker} sat in the middle of the celebration like a chair nobody wanted."
    )


def humor_breaks_tension(world: World, sidekick: Entity, problem: PoliticalProblem) -> None:
    if ("humor", problem.id) in world.fired:
        return
    world.fired.add(("humor", problem.id))
    _add_mem(sidekick, "mischief", 1)
    _add_mem(sidekick, "hope", 1)
    world.say(
        f"{sidekick.id} leaned in and said the mayor had so many speeches that even the soup needed a nap."
    )
    world.say(
        f"That silly line cracked the room just enough for a few smiles to sneak back in."
    )


def transform(world: World, hero: Entity, power: Power) -> None:
    if world.transformed:
        return
    world.transformed = True
    hero.type = "superhero"
    hero.label = power.form
    hero.meters["power"] = _meter(hero, "power") + 1
    hero.memes["courage"] = _mem(hero, "courage") + 2
    world.say(
        f"{hero.id} touched {hero.pronoun('possessive')} old badge, and with a bright flash {power.transformation_word} changed {hero.id} into {power.form}."
    )
    world.say(
        f"{power.flare} made the room gasp, and the cape seemed to stand up like it was proud."
    )


def resolve(world: World, hero: Entity, sidekick: Entity, feast: Feast, problem: PoliticalProblem) -> None:
    _add_mem(hero, "joy", 1)
    _add_mem(sidekick, "joy", 1)
    _add_mem(hero, "resolve", 1)
    world.say(
        f"Then {hero.id} spoke plainly: the feast was for everyone, and the people should eat before they argued."
    )
    world.say(
        f"The council listened, the rumor went flat, and the blocker moved aside."
    )
    world.say(
        f"At last the feast began with {feast.feast_food}, laughter, and no more sour faces at the table."
    )
    world.say(
        f"{hero.id} stood by the warm plates, still transformed, and the whole hall looked safer and kinder than before."
    )
    world.facts["resolved"] = True


def tell(place: Place, feast: Feast, problem: PoliticalProblem, power: Power, hero_name: str, sidekick_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="person", traits=["kind", "brave"]))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="person", traits=["funny", "quick"]))
    world.add(Entity(id=feast.id, type="feast", label=feast.label, phrase=feast.feast_food))
    world.add(Entity(id=problem.id, type="problem", label=problem.label, phrase=problem.issue))
    world.add(Entity(id=power.id, type="power", label=power.label, phrase=power.form))

    introduce(world, hero, sidekick, feast, problem)
    world.para()
    flashback(world, hero, feast, power)
    politics_stirs(world, hero, problem)
    humor_breaks_tension(world, sidekick, problem)
    transform(world, hero, power)
    resolve(world, hero, sidekick, feast, problem)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        feast=feast,
        problem=problem,
        power=power,
        place=place,
    )
    return world


PLACES = {
    "townhall": Place(id="townhall", name="the town hall", indoor=True, holds_feast=True, politics=True),
    "square": Place(id="square", name="the city square", indoor=False, holds_feast=True, politics=True),
    "garden": Place(id="garden", name="the lantern garden", indoor=False, holds_feast=True, politics=False),
}

FEASTS = {
    "sun": Feast(
        id="sun_feast",
        label="sun feast",
        feast_food="soft bread, berry pies, and sweet soup",
        joy_word="warm",
        fuss_word="sticky",
        place_ok={"townhall", "square", "garden"},
    ),
    "harvest": Feast(
        id="harvest_feast",
        label="harvest feast",
        feast_food="corn cakes, honey apples, and bright juice",
        joy_word="bright",
        fuss_word="crowded",
        place_ok={"townhall", "square"},
    ),
    "moon": Feast(
        id="moon_feast",
        label="moon feast",
        feast_food="silver cookies, noodles, and tiny tarts",
        joy_word="glowy",
        fuss_word="quiet",
        place_ok={"townhall", "garden"},
    ),
}

PROBLEMS = {
    "tax": PoliticalProblem(
        id="tax_tangle",
        label="tax tangle",
        issue="the mayor wanted to raise food taxes",
        rumor="the feast would cost too much",
        blocker="a stack of bill papers",
        fix_hint="share the feast fairly",
    ),
    "seat": PoliticalProblem(
        id="seat_dispute",
        label="seat dispute",
        issue="two council members were fighting over the first seat",
        rumor="the whole feast belonged to the loudest one",
        blocker="a too-big chair",
        fix_hint="move the chairs and share the front table",
    ),
    "banner": PoliticalProblem(
        id="banner_mixup",
        label="banner mixup",
        issue="the victory banner said the wrong neighborhood name",
        rumor="nobody had been invited properly",
        blocker="a crooked sign",
        fix_hint="fix the banner and welcome every district",
    ),
}

POWERS = {
    "spark": Power(
        id="spark_shift",
        label="spark shift",
        trigger="the little badge on his chest",
        form="Captain Brightfeast",
        effect="light",
        transformation_word="transformed",
        flare="A gold spark swirled around his boots",
    ),
    "smile": Power(
        id="smile_shift",
        label="smile shift",
        trigger="the old joke his grandmother told him",
        form="Captain Laughlight",
        effect="smile",
        transformation_word="changed",
        flare="A laughing shimmer bounced from wall to wall",
    ),
    "cape": Power(
        id="cape_shift",
        label="cape shift",
        trigger="the tug of the red cape",
        form="Mayor Guardstar",
        effect="courage",
        transformation_word="transformed",
        flare="The cape snapped like a banner in a windy parade",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tara", "Nia", "June", "Ivy"]
BOY_NAMES = ["Kai", "Arlo", "Finn", "Jude", "Noah", "Eli"]
TRAITS = ["bright", "brave", "cheerful", "quick", "gentle"]


@dataclass
class StoryParams:
    place: str
    feast: str
    problem: str
    power: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, p in PLACES.items():
        for feast, f in FEASTS.items():
            if place not in f.place_ok:
                continue
            for prob in PROBLEMS:
                for power in POWERS:
                    out.append((place, feast, prob, power))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes a feast, politics, and the word "{f["feast"].label}".',
        f"Tell a short story where {f['hero'].id} must help with a feast while politics causes trouble at {f['place'].name}.",
        f"Write a funny, brave story where a hero transforms, remembers something in a flashback, and saves a feast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    feast: Feast = f["feast"]
    problem: PoliticalProblem = f["problem"]
    power: Power = f["power"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who was the story about at {place.name}?",
            answer=f"It was about {hero.id}, a small hero who cared about the feast and wanted things to be fair.",
        ),
        QAItem(
            question=f"What kind of trouble did politics cause at the feast?",
            answer=f"Politics caused a {problem.label}, and it made the room noisy and tense.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember a flashback?",
            answer=f"{hero.id} remembered being little at a small family feast, because that memory showed how a shared meal could help people feel calm.",
        ),
        QAItem(
            question=f"What made the story funny?",
            answer=f"{sidekick.id} made a joke about speeches and soup, and that silly line helped the room smile again.",
        ),
        QAItem(
            question=f"What transformation happened near the end?",
            answer=f"{hero.id} used {power.trigger} and transformed into {power.form}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The argument ended, the feast began, and everyone got to share {feast.feast_food} together.",
        ),
    ]


KNOWLEDGE = {
    "feast": [
        QAItem(
            question="What is a feast?",
            answer="A feast is a big meal with lots of food, often shared with many people.",
        )
    ],
    "politics": [
        QAItem(
            question="What is politics?",
            answer="Politics is how people make decisions about a group, a town, or a country.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier.",
        )
    ],
    "humor": [
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people laugh or smile.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form.",
        )
    ],
    "superhero": [
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero helps others, solves problems, and is brave when trouble comes.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return KNOWLEDGE["feast"] + KNOWLEDGE["politics"] + KNOWLEDGE["flashback"] + KNOWLEDGE["humor"] + KNOWLEDGE["transformation"] + KNOWLEDGE["superhero"]


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  flashback_done: {world.flashback_done}")
    lines.append(f"  transformed: {world.transformed}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="townhall", feast="sun", problem="tax", power="spark", hero_name="Mina", sidekick_name="Jude"),
    StoryParams(place="square", feast="harvest", problem="seat", power="smile", hero_name="Kai", sidekick_name="Ivy"),
    StoryParams(place="garden", feast="moon", problem="banner", power="cape", hero_name="Lena", sidekick_name="Arlo"),
]


ASP_RULES = r"""
feast_place(P,F) :- place(P), feast(F), place_ok(F,P).
problem_at(P,R) :- place(P), problem(R).
compatible(P,F,R,W) :- feast_place(P,F), problem_at(P,R), power(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        if p.holds_feast:
            lines.append(asp.fact("can_hold_feast", pid))
        if p.politics:
            lines.append(asp.fact("politics_place", pid))
    for fid, f in FEASTS.items():
        lines.append(asp.fact("feast", fid))
        lines.append(asp.fact("feast_label", fid, f.label))
        for p in sorted(f.place_ok):
            lines.append(asp.fact("place_ok", fid, p))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
    for wid, w in POWERS.items():
        lines.append(asp.fact("power", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show feast_place/2."))
    return sorted(set(asp.atoms(model, "feast_place")))


def asp_verify() -> int:
    python_set = set((p, f) for p, f, _, _ in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} place/feast pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero feast-politics story world with flashback, humor, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--feast", choices=FEASTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    combos = []
    for place, feast, prob, power in valid_combos():
        if args.place and place != args.place:
            continue
        if args.feast and feast != args.feast:
            continue
        if args.problem and prob != args.problem:
            continue
        if args.power and power != args.power:
            continue
        combos.append((place, feast, prob, power))
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, feast, prob, power = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    return StoryParams(place=place, feast=feast, problem=prob, power=power, hero_name=hero_name, sidekick_name=sidekick)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    feast = FEASTS[params.feast]
    problem = PROBLEMS[params.problem]
    power = POWERS[params.power]
    world = tell(place, feast, problem, power, params.hero_name, params.sidekick_name)
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
        print(asp_program("#show feast_place/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show feast_place/2."))
        combos = sorted(set(asp.atoms(model, "feast_place")))
        print(f"{len(combos)} compatible feast-place combos:")
        for place, feast in combos:
            print(f"  {place} {feast}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.feast} at {p.place} (problem: {p.problem}, power: {p.power})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
