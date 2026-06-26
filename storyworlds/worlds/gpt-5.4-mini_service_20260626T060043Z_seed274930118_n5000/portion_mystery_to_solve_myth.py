#!/usr/bin/env python3
"""
storyworlds/worlds/portion_mystery_to_solve_myth.py
===================================================

A small myth-flavored story world about a childlike seeker, a missing portion,
and a mystery that can be solved by following signs.

Seed tale sketch:
---
At the edge of a hill village stood an old shrine with a bronze bowl. Each dawn,
the keeper set out a portion of honey cakes for the river spirit, but one morning
the bowl was almost empty. The keeper was not angry. Instead, a young helper
followed crumbs, wind-tossed reeds, and a muddy footprint to learn who had taken
the portion. In the end, the "thief" was only a hungry fox cub, and the helper
left a fairer portion near a safer stone so the spirit and the fox could both be
fed in peace.

World model:
---
- A sacred offering is prepared as a physical portion of food or light.
- A mystery begins when some of it vanishes or is disturbed.
- The seeker gathers clues, raises certainty, and names a likely cause.
- If the seeker solves the mystery, the ending proves the change by showing a
  wiser offering arrangement.

Meters / memes:
---
- meters: hunger, clue, certainty, spoilage, travel
- memes: wonder, worry, trust, relief, pride, fear

ASP twin:
---
The inline ASP rules mirror the Python reasonableness gate:
- a mystery is valid only when the setting supports the ritual,
- the offering type fits the shrine,
- and the mystery type has at least one strong clue path.
"""

from __future__ import annotations

import argparse
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Shrine:
    place: str = "the shrine"
    setting: str = "hill"
    night: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    type: str
    kind: str
    portion: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Mystery:
    id: str
    label: str
    verb: str
    clue_path: str
    reveal: str
    culprit: str
    sign: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    plural: bool = False


class World:
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.signs: list[str] = []

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
        import copy
        w = World(self.shrine)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.signs = list(self.signs)
        return w


SHRINES = {
    "hill": Shrine(place="the hill shrine", setting="hill", affords={"honey", "grain", "milk"}),
    "grove": Shrine(place="the grove altar", setting="grove", affords={"honey", "grain"}),
    "river": Shrine(place="the river stone", setting="river", affords={"milk", "grain"}),
    "cave": Shrine(place="the cave hearth", setting="cave", affords={"honey", "milk"}),
}

OFFERINGS = {
    "honey": Offering(
        id="honey",
        label="honey cakes",
        phrase="a warm portion of honey cakes",
        type="cakes",
        kind="food",
        portion="portion",
        region="table",
        genders={"girl", "boy"},
    ),
    "grain": Offering(
        id="grain",
        label="grain bowl",
        phrase="a small portion of grain in a clay bowl",
        type="grain",
        kind="food",
        portion="portion",
        region="table",
    ),
    "milk": Offering(
        id="milk",
        label="milk cup",
        phrase="a modest portion of milk in a cup",
        type="milk",
        kind="drink",
        portion="portion",
        region="table",
    ),
}

MYSTERIES = {
    "missing": Mystery(
        id="missing",
        label="missing portion",
        verb="vanish",
        clue_path="follow the signs",
        reveal="someone had taken only a little part of the offering",
        culprit="fox cub",
        sign="crumbs",
        risk="worry",
        tags={"mystery", "missing", "portion"},
    ),
    "spilled": Mystery(
        id="spilled",
        label="spilled portion",
        verb="spill",
        clue_path="read the splash marks",
        reveal="the bowl had tipped in the wind",
        culprit="wind",
        sign="drifted grain",
        risk="spoilage",
        tags={"mystery", "spilled", "portion"},
    ),
    "borrowed": Mystery(
        id="borrowed",
        label="borrowed portion",
        verb="borrow",
        clue_path="ask the villagers",
        reveal="a tired child had taken a fair share and left a token",
        culprit="hungry child",
        sign="a small reed token",
        risk="hunger",
        tags={"mystery", "borrowed", "portion"},
    ),
}

REMEDIES = {
    "share": Remedy(
        id="share",
        label="a second little portion",
        prep="set aside a second little portion for the fox cub",
        tail="placed the portion by a safer stone",
        protects={"missing"},
    ),
    "stone": Remedy(
        id="stone",
        label="a windbreak stone",
        prep="move the bowl behind a windbreak stone",
        tail="rested the bowl behind the stone",
        protects={"spilled"},
    ),
    "token": Remedy(
        id="token",
        label="a reed token",
        prep="leave a reed token for the child",
        tail="put the token beside the bowl",
        protects={"borrowed"},
    ),
}

GIRL_NAMES = ["Mira", "Asha", "Niva", "Ila", "Kora", "Sera", "Tala"]
BOY_NAMES = ["Arun", "Bren", "Cian", "Dari", "Eno", "Kian", "Ravi"]
TRAITS = ["curious", "gentle", "bold", "quiet", "patient", "bright"]


@dataclass
class StoryParams:
    shrine: str
    offering: str
    mystery: str
    name: str
    gender: str
    title: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for shrine_id, shrine in SHRINES.items():
        for offering_id in shrine.affords:
            for mystery_id, mystery in MYSTERIES.items():
                if offering_id == "honey" and mystery_id in {"missing", "borrowed"}:
                    out.append((shrine_id, offering_id, mystery_id))
                if offering_id == "grain" and mystery_id in {"missing", "spilled", "borrowed"}:
                    out.append((shrine_id, offering_id, mystery_id))
                if offering_id == "milk" and mystery_id in {"missing", "spilled"}:
                    out.append((shrine_id, offering_id, mystery_id))
    return out


def reasonableness_gate(shrine: Shrine, offering: Offering, mystery: Mystery) -> bool:
    return offering.id in shrine.affords and (offering.id, mystery.id) in {
        ("honey", "missing"), ("honey", "borrowed"),
        ("grain", "missing"), ("grain", "spilled"), ("grain", "borrowed"),
        ("milk", "missing"), ("milk", "spilled"),
    }


def choose_remedy(mystery: Mystery) -> Optional[Remedy]:
    return {
        "missing": REMEDIES["share"],
        "spilled": REMEDIES["stone"],
        "borrowed": REMEDIES["token"],
    }.get(mystery.id)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic mystery about a missing portion.")
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--title")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shrine and args.offering and args.mystery:
        if not reasonableness_gate(SHRINES[args.shrine], OFFERINGS[args.offering], MYSTERIES[args.mystery]):
            raise StoryError("No story: that shrine, offering, and mystery do not fit together.")
    combos = [
        c for c in valid_combos()
        if (args.shrine is None or c[0] == args.shrine)
        and (args.offering is None or c[1] == args.offering)
        and (args.mystery is None or c[2] == args.mystery)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    shrine_id, offering_id, mystery_id = rng.choice(sorted(combos))
    offering = OFFERINGS[offering_id]
    mystery = MYSTERIES[mystery_id]
    gender = args.gender or rng.choice(sorted(offering.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    title = args.title or rng.choice(["keeper", "seeker", "helper", "child of the shrine"])
    trait = rng.choice(TRAITS)
    return StoryParams(shrine=shrine_id, offering=offering_id, mystery=mystery_id,
                       name=name, gender=gender, title=title, trait=trait)


def awaken(world: World, hero: Entity, title: str) -> None:
    world.say(f"{hero.id} was a {title} of the {world.shrine.setting}, known for noticing small signs.")


def set_scene(world: World, hero: Entity, mystery: Mystery, offering: Offering) -> None:
    world.say(
        f"At {world.shrine.place}, {hero.id} found {hero.pronoun('possessive')} {offering.label} nearly empty."
    )
    world.say(
        f"The loss was only a {offering.portion}, but in old stories a missing portion could wake a whole day of worry."
    )


def gather_clues(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["certainty"] = hero.meters.get("certainty", 0.0) + 1
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.signs.append(mystery.sign)
    world.say(
        f"{hero.id} knelt to {mystery.clue_path}, and found {mystery.sign} near the bowl."
    )


def question_signs(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["certainty"] = hero.meters.get("certainty", 0.0) + 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.5)
    world.say(
        f"{hero.id} followed the sign deeper into the quiet and asked what kind of hand could take only a portion."
    )


def reveal(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    world.say(
        f"By the third sign, {hero.id} understood that {mystery.reveal}, not a cruel thief at all."
    )


def solve(world: World, hero: Entity, mystery: Mystery, remedy: Remedy) -> None:
    hero.meters["certainty"] = hero.meters.get("certainty", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"So {hero.id} chose {remedy.prep}, because a wise shrine leaves room for hunger, wind, and mercy."
    )
    world.say(
        f"Then {hero.id} {remedy.tail}. The mystery was solved, and the old fear left the stones."
    )


def ending_image(world: World, hero: Entity, offering: Offering, mystery: Mystery) -> None:
    world.say(
        f"In the last light, {hero.id} stood beside {world.shrine.place} and watched the new {offering.label} rest safely in peace."
    )
    world.say(
        f"What had once felt like a loss became a fairer {offering.portion}, and the village learned how to honor the same goodness in a kinder way."
    )


def tell(shrine: Shrine, offering: Offering, mystery: Mystery,
         name: str, gender: str, title: str, trait: str) -> World:
    world = World(shrine)
    hero = world.add(Entity(
        id=name, kind="character", type=gender, traits=["little", trait, "stubborn"]
    ))
    world.facts.update(hero=hero, shrine=shrine, offering=offering, mystery=mystery)
    awaken(world, hero, title)
    world.para()
    set_scene(world, hero, mystery, offering)
    gather_clues(world, hero, mystery)
    question_signs(world, hero, mystery)
    reveal(world, hero, mystery)
    remedy = choose_remedy(mystery)
    if remedy is None:
        raise StoryError("No remedy exists for this mystery.")
    world.para()
    solve(world, hero, mystery, remedy)
    ending_image(world, hero, offering, mystery)
    world.facts["remedy"] = remedy
    return world


KNOWLEDGE = {
    "portion": [
        ("What is a portion?", "A portion is a small part of a whole thing, like a share of food or water."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is something puzzling that you can solve by looking for clues."),
    ],
    "clues": [
        ("What are clues?", "Clues are small signs that help you figure out what happened."),
    ],
    "fox": [
        ("Why do foxes sometimes steal food?", "Foxes look for food when they are hungry, so they may take easy snacks."),
    ],
    "wind": [
        ("What can wind do to a bowl?", "Wind can tip, move, or scatter light things if they are not held in place."),
    ],
    "sharing": [
        ("Why is sharing wise?", "Sharing can keep everyone fed and calm, especially when there is not much to go around."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about a missing {f["offering"].portion} at {f["shrine"].place}.',
        f"Tell a gentle mystery story where {f['hero'].id} follows clues to learn what happened to the {f['offering'].label}.",
        f'Write a mythic tale that includes the word "portion" and ends with a wiser way to leave the offering.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, shrine, offering, mystery = f["hero"], f["shrine"], f["offering"], f["mystery"]
    remedy = f["remedy"]
    return [
        QAItem(
            question=f"What did {hero.id} notice at {shrine.place}?",
            answer=f"{hero.id} noticed that the {offering.label} was nearly empty and that only a small {offering.portion} was missing.",
        ),
        QAItem(
            question=f"What kind of story problem was it?",
            answer=f"It was a mystery about a missing portion, and {hero.id} had to follow clues to solve it.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} begin the search?",
            answer=f"The first clue was {mystery.sign}, which showed that something small had moved near the bowl.",
        ),
        QAItem(
            question=f"What did the mystery turn out to be?",
            answer=f"It turned out that {mystery.reveal}. The answer was not a cruel trick, only a sign that something needed to be handled more wisely.",
        ),
        QAItem(
            question=f"How was the problem solved in the end?",
            answer=f"{hero.id} chose {remedy.label} and changed the offering place so the {offering.label} could be kept safer next time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    seen = {"portion", "mystery", "clues", "sharing"}
    if world.facts["mystery"].culprit == "fox cub":
        seen.add("fox")
    if world.facts["mystery"].culprit == "wind":
        seen.add("wind")
    for key in ["portion", "mystery", "clues", "fox", "wind", "sharing"]:
        if key in seen:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}/{e.type:8}) {' '.join(bits)}")
    if world.signs:
        lines.append(f"  signs: {world.signs}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Shrine, Offering, Mystery) :-
    shrine(Shrine), offering(Offering), mystery(Mystery),
    fits(Shrine, Offering), solvable(Offering, Mystery).

has_portion(Offering) :- offering(Offering), portion(Offering).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SHRINES:
        lines.append(asp.fact("shrine", s))
        for a in sorted(SHRINES[s].affords):
            lines.append(asp.fact("fits", s, a))
    for o in OFFERINGS:
        lines.append(asp.fact("offering", o))
        lines.append(asp.fact("portion", o))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for o, m in [("honey", "missing"), ("honey", "borrowed"), ("grain", "missing"),
                 ("grain", "spilled"), ("grain", "borrowed"), ("milk", "missing"),
                 ("milk", "spilled")]:
        lines.append(asp.fact("solvable", o, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asps:
        print("  only in python:", sorted(py - asps))
    if asps - py:
        print("  only in clingo:", sorted(asps - py))
    return 1


def build_story_prompt(world: World) -> list[str]:
    return generation_prompts(world)


def generate(params: StoryParams) -> StorySample:
    world = tell(SHRINES[params.shrine], OFFERINGS[params.offering], MYSTERIES[params.mystery],
                 params.name, params.gender, params.title, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=build_story_prompt(world),
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


CURATED = [
    StoryParams(shrine="hill", offering="honey", mystery="missing", name="Mira", gender="girl", title="keeper", trait="curious"),
    StoryParams(shrine="grove", offering="grain", mystery="spilled", name="Arun", gender="boy", title="seeker", trait="quiet"),
    StoryParams(shrine="river", offering="milk", mystery="spilled", name="Kora", gender="girl", title="helper", trait="bright"),
    StoryParams(shrine="cave", offering="honey", mystery="borrowed", name="Ravi", gender="boy", title="child of the shrine", trait="gentle"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shrine and args.offering and args.mystery:
        if not reasonableness_gate(SHRINES[args.shrine], OFFERINGS[args.offering], MYSTERIES[args.mystery]):
            raise StoryError("No story: these explicit choices do not make a solvable myth.")
    combos = [c for c in valid_combos()
              if (args.shrine is None or c[0] == args.shrine)
              and (args.offering is None or c[1] == args.offering)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    shrine, offering, mystery = rng.choice(sorted(combos))
    off = OFFERINGS[offering]
    gender = args.gender or rng.choice(sorted(off.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    title = args.title or rng.choice(["keeper", "seeker", "helper"])
    trait = rng.choice(TRAITS)
    return StoryParams(shrine=shrine, offering=offering, mystery=mystery,
                       name=name, gender=gender, title=title, trait=trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.mystery} at {p.shrine} ({p.offering})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
