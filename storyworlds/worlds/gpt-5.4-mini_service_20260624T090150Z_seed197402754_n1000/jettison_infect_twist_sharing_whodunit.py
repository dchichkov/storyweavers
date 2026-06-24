#!/usr/bin/env python3
"""
A tiny whodunit-style story world about sharing, a twist, and jettisoning the
thing that could infect the rest of the pile.

The seed tale behind this world:
---
At a small library party, Mina and her cousin Finn shared a bowl of bright berry
punch and a basket of crackers. Then someone noticed the red cup had a tiny crack
and sticky drops were landing near the crackers. Mina first thought a mouse had
done it, but the twist was that the cracked cup was the real culprit.

Finn did not want anyone to get sick, so he carefully jettisoned the cracked cup
into the trash. Mina wiped the table, the crackers stayed safe, and the mystery
was solved with a shared cleanup.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class Place:
    label: str
    indoors: bool
    shared_spots: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    clue: str


@dataclass
class Trouble:
    id: str
    label: str
    verb: str
    gerund: str
    infection: str
    contamination: str
    spread_target: str
    setting_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shield:
    id: str
    label: str
    prep: str
    tail: str
    guards_infection: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.twist_revealed = False
        self.solved = False

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
        clone.entities = dataclasses.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.twist_revealed = self.twist_revealed
        clone.solved = self.solved
        return clone


PLACES = {
    "library": Place("the library party room", True, {"table", "basket", "trash can"}),
    "kitchen": Place("the kitchen", True, {"counter", "sink", "trash can"}),
    "porch": Place("the porch", False, {"bench", "bucket", "trash can"}),
}

TRUBLICS = {
    "cup": Trouble(
        id="cup",
        label="red cup",
        verb="spill",
        gerund="spilling",
        infection="infect",
        contamination="sticky berry drops",
        spread_target="crackers",
        setting_spot="table",
        tags={"sharing", "twist"},
    ),
    "jar": Trouble(
        id="jar",
        label="jam jar",
        verb="drip",
        gerund="dripping",
        infection="infect",
        contamination="sweet jam streaks",
        spread_target="napkins",
        setting_spot="counter",
        tags={"sharing", "twist"},
    ),
}

SHIELDS = {
    "trash": Shield(
        id="trash",
        label="the trash can",
        prep="carefully jettison the broken cup into the trash can",
        tail="carried the broken cup to the trash can",
        guards_infection=True,
    ),
    "sink": Shield(
        id="sink",
        label="the sink",
        prep="put the cup in the sink and rinse it away",
        tail="moved the cup to the sink",
        guards_infection=True,
    ),
}

HEROES = ["Mina", "Finn", "Pia", "Noah", "Lena", "Owen"]
ADULTS = ["aunt", "uncle", "mom", "dad"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    hero: str
    helper: str
    adult: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TRUBLICS]


ASP_RULES = r"""
% A trouble is dangerous when it can spread to the shared food.
dangerous(T) :- trouble(T), infection(T).
% A safe fix exists when a shield can remove the danger by jettisoning or rinsing.
safe_fix(S, T) :- shield(S), trouble(T), guards_infection(S).
valid(Place, Trouble) :- place(Place), trouble(Trouble), dangerous(Trouble), safe_fix(_, Trouble).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TRUBLICS:
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("infection", tid))
    for sid in SHIELDS:
        lines.append(asp.fact("shield", sid))
        lines.append(asp.fact("guards_infection", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about sharing and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TRUBLICS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--adult", choices=ADULTS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.trouble:
        combos = [c for c in combos if c[1] == args.trouble]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HEROES if h != hero])
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(place=place, trouble=trouble, hero=hero, helper=helper, adult=adult)


def _do_trouble(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.meters["mess"] = hero.meters.get("mess", 0) + 1
    if trouble.infection:
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    trouble = TRUBLICS[params.trouble]
    shield = SHIELDS["trash"]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Mina", "Pia", "Lena"} else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type="girl" if params.helper in {"Mina", "Pia", "Lena"} else "boy"))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult))
    shared = world.add(Entity(id="shared_item", label=trouble.label, phrase=trouble.label, owner=hero.id))
    food = world.add(Entity(id="food", label="crackers", phrase="a basket of crackers"))
    world.facts = {"hero": hero, "helper": helper, "adult": adult, "trouble": trouble, "shared": shared, "food": food, "shield": shield, "place": place}

    world.say(f"It was a quiet party at {place.label}, where {hero.id} and {helper.id} shared {shared.label} and {food.label}.")
    world.say(f"Then {hero.id} noticed a tiny clue: {trouble.contamination} near the {trouble.spread_target}. That was the first twist.")
    world.para()
    world.say(f"{hero.id} thought the mess might be from a mouse, but the real culprit was the {trouble.label}.")

    if trouble.id == "cup":
        world.say(f"It had a crack, so it could {trouble.verb} sticky drops across the table.")
    else:
        world.say(f"It had a loose lid, so it could {trouble.verb} sweet streaks across the counter.")

    _do_trouble(world, hero, trouble)
    world.para()
    world.say(f"{params.helper} did not want the shared food to {trouble.infection} anyone.")
    world.say(f"So {params.helper} {shield.prep}.")
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.solved = True
    world.twist_revealed = True
    world.say(f"Then {hero.id} wiped the table, and the {trouble.spread_target} stayed safe.")
    world.say(f"By the end, the mystery was solved, and everyone could share the clean snacks again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t: Trouble = f["trouble"]
    return [
        f'Write a child-friendly whodunit story about sharing, a twist, and the word "{t.label}".',
        f"Tell a short mystery where {f['hero'].id} and {f['helper'].id} share snacks, notice a clue, and stop something that could {t.infection} the food.",
        f"Write a simple story in which a broken shared item must be jettisoned so the rest of the party stays safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    trouble: Trouble = f["trouble"]
    shield: Shield = f["shield"]
    return [
        QAItem(
            question=f"What were {hero.id} and {helper.id} sharing at the party?",
            answer=f"They were sharing {trouble.label} and a basket of crackers at the party.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that the {trouble.label}, not a mouse, was causing the sticky clue near the food.",
        ),
        QAItem(
            question=f"Why did {helper.id} jettison the broken item?",
            answer=f"{helper.id} jettisoned it so it would not {trouble.infection} the shared food and make anyone sick.",
        ),
        QAItem(
            question=f"How did the story end after the broken item went away?",
            answer=f"The table got wiped clean, the crackers stayed safe, and everyone could share the snacks again.",
        ),
        QAItem(
            question=f"What did the helper use to solve the problem?",
            answer=f"They used {shield.label} to get the broken item out of the way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does jettison mean?",
            answer="Jettison means to throw away or send something off quickly because it should not stay with the rest.",
        ),
        QAItem(
            question="What does infect mean?",
            answer="Infect means to spread germs or sickness to someone or something else.",
        ),
        QAItem(
            question="Why is sharing careful work in a mystery?",
            answer="Because when people share food or objects, a broken or dirty thing can spread trouble to the others.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  twist_revealed={world.twist_revealed} solved={world.solved}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="library", trouble="cup", hero="Mina", helper="Finn", adult="aunt"),
    StoryParams(place="kitchen", trouble="jar", hero="Pia", helper="Owen", adult="mom"),
    StoryParams(place="porch", trouble="cup", hero="Lena", helper="Noah", adult="dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print("  ", v)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.trouble} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
