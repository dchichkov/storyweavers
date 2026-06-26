#!/usr/bin/env python3
"""
A small storyworld for a cautionary animal tale centered on a shrine.

Premise:
- A curious animal visits a shrine.
- The shrine has simple rules: be quiet, leave offerings alone, and do not disturb
  what is meant to rest there.
- The animal wants something shiny or sweet at the shrine and ignores a warning.
- The disturbance causes an avoidable problem.
- A patient helper explains the rule and restores calm.

The world is intentionally tiny and constraint-driven: only a few plausible
combinations are valid, and invalid explicit choices raise StoryError.
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

SHRINE_WORD = "shrine"


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "helper" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "fox", "rabbit", "mouse", "squirrel", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "helper":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the shrine"
    quiet: bool = True
    offers: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    kind: str = "thing"
    plural: bool = False


@dataclass
class Guide:
    id: str
    label: str
    warning: str
    fix: str
    ending: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


TEMPTATIONS = {
    "bells": Temptation(
        id="bells",
        verb="reach for the bells",
        gerund="reaching for bells",
        rush="dash to the bells",
        mess="noisy",
        soil="loud and tangled",
        keyword="bells",
        tags={"sound", "shrine"},
    ),
    "rice": Temptation(
        id="rice",
        verb="snatch the rice cake",
        gerund="snatching rice cake",
        rush="pounce at the rice cake",
        mess="crumbled",
        soil="smashed and crumbly",
        keyword="rice",
        tags={"food", "shrine"},
    ),
    "flowers": Temptation(
        id="flowers",
        verb="pluck the flowers",
        gerund="plucking flowers",
        rush="run to the flowers",
        mess="broken",
        soil="broken and scattered",
        keyword="flowers",
        tags={"garden", "shrine"},
    ),
}

GUIDES = {
    "keeper": Guide(
        id="keeper",
        label="the shrine keeper",
        warning="The shrine keeper knows the old rules",
        fix="leave the offering alone and ring the little bell only once",
        ending="the shrine looked peaceful again",
    ),
    "grandparent": Guide(
        id="grandparent",
        label="the grandparent",
        warning="A careful grandparent can see trouble coming",
        fix="bow first, then step back and use soft paws",
        ending="the quiet path felt safe once more",
    ),
}

TREASURES = {
    "bell": Treasure(label="bell", phrase="a little brass bell", type="bell"),
    "cake": Treasure(label="cake", phrase="a sweet rice cake", type="cake"),
    "flowers": Treasure(label="flowers", phrase="fresh white flowers", type="flowers", plural=True),
}

ANIMAL_NAMES = ["Milo", "Tiki", "Pip", "Nori", "Bao", "Momo", "Kiki", "Riku", "Sumi"]
ANIMALS = ["cat", "fox", "rabbit", "squirrel", "mouse", "kitten"]
GUIDE_TYPES = ["keeper", "grandparent"]


@dataclass
class StoryParams:
    animal: str
    animal_type: str
    place: str
    temptation: str
    treasure: str
    guide: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for tempt_id in p.offers:
            t = TEMPTATIONS[tempt_id]
            for tr_id in TREASURES:
                if is_risky(t, TREASURES[tr_id]):
                    combos.append((place, tempt_id, tr_id))
    return combos


def is_risky(temptation: Temptation, treasure: Treasure) -> bool:
    if temptation.id == "bells" and treasure.label == "bell":
        return True
    if temptation.id == "rice" and treasure.label == "cake":
        return True
    if temptation.id == "flowers" and treasure.label == "flowers":
        return True
    return False


def select_fix(temptation: Temptation, treasure: Treasure) -> Optional[Guide]:
    # The cautionary rule: a valid fix must match both the temptation and the
    # object at risk, otherwise the story is not reasonable.
    if temptation.id == "bells" and treasure.label == "bell":
        return GUIDES["keeper"]
    if temptation.id == "rice" and treasure.label == "cake":
        return GUIDES["grandparent"]
    if temptation.id == "flowers" and treasure.label == "flowers":
        return GUIDES["keeper"]
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary shrine animal storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal")
    ap.add_argument("--animal-type", choices=ANIMALS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.temptation and args.treasure:
        if not is_risky(TEMPTATIONS[args.temptation], TREASURES[args.treasure]):
            raise StoryError("That temptation does not honestly threaten that treasure.")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.temptation is None or c[1] == args.temptation)
        and (args.treasure is None or c[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("No valid shrine story matches the given options.")

    place, tempt_id, tr_id = rng.choice(sorted(combos))
    animal_type = args.animal_type or rng.choice(ANIMALS)
    name = args.name or rng.choice(ANIMAL_NAMES)
    guide = args.guide or rng.choice(GUIDE_TYPES)
    animal = args.animal or name
    return StoryParams(
        animal=animal,
        animal_type=animal_type,
        place=place,
        temptation=tempt_id,
        treasure=tr_id,
        guide=guide,
        name=name,
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    animal = world.add(Entity(
        id=params.name,
        kind="animal",
        type=params.animal_type,
        label=params.name,
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="helper",
        type=params.guide,
        label=GUIDES[params.guide].label,
    ))
    treasure = world.add(Entity(
        id="Treasure",
        type=TREASURES[params.treasure].type,
        label=TREASURES[params.treasure].label,
        phrase=TREASURES[params.treasure].phrase,
        plural=TREASURES[params.treasure].plural,
    ))
    temptation = TEMPTATIONS[params.temptation]

    # setup
    world.say(f"{animal.label} was a little {animal.type} who liked quiet walks near {place.name}.")
    world.say(f"{animal.label} noticed {treasure.phrase} at the {SHRINE_WORD} and felt curious.")
    world.para()

    # tension
    world.say(f"One bright morning, {animal.label} went to {place.name} with {guide.label}.")
    world.say(f"{animal.label} wanted to {temptation.verb}, but {guide.label} said, \"{GUIDES[params.guide].warning}.\"")
    world.say(f"{animal.label} did not listen and tried to {temptation.rush}.")
    treasure.meters = {"safe": 0}
    treasure.memes = {"alarm": 1}
    world.say(f"That made the {treasure.label} get {temptation.soil}.")
    world.para()

    # turn / resolution
    fix = select_fix(temptation, treasure)
    if fix is None:
        raise StoryError("No reasonable cautionary fix exists for this combination.")
    world.say(f"{guide.label} gently moved {animal.label} back and said, \"{fix.fix}.\"")
    world.say(f"{animal.label} lowered {animal.pronoun('possessive')} paws, listened at last, and stayed still.")
    world.say(f"In the end, {fix.ending}, and {animal.label} remembered that the {SHRINE_WORD} was a place for care, not grabbing.")

    world.facts = {
        "animal": animal,
        "guide": guide,
        "treasure": treasure,
        "temptation": temptation,
        "fix": fix,
        "place": place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    guide = f["guide"]
    tempt = f["temptation"]
    return [
        f"Write a short cautionary animal story about {animal.label} at a shrine.",
        f"Tell a gentle story where {animal.label} is warned not to {tempt.verb} and learns a careful lesson.",
        f"Write a child-friendly animal tale that includes a shrine, a warning, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal = f["animal"]
    guide = f["guide"]
    treasure = f["treasure"]
    tempt = f["temptation"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about at the shrine?",
            answer=f"It was about {animal.label}, a little {animal.type} who visited {place.name}.",
        ),
        QAItem(
            question=f"What did {animal.label} want to do that caused trouble?",
            answer=f"{animal.label} wanted to {tempt.verb}, even after {guide.label} gave a warning.",
        ),
        QAItem(
            question=f"What got messed up when {animal.label} ignored the warning?",
            answer=f"The {treasure.label} got {tempt.soil}, which was the trouble the story warned about.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{guide.label} helped {animal.label} slow down, and the shrine stayed peaceful in the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shrine?",
            answer="A shrine is a special place where people visit quietly, show respect, and often leave small offerings.",
        ),
        QAItem(
            question="Why should you be quiet at a shrine?",
            answer="Being quiet helps keep the place calm and respectful, because shrines are treated as peaceful places.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story is a tale that warns about a mistake and shows why careful choices matter.",
        ),
    ]


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
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = [f"type={e.type}"]
        if e.label:
            bits.append(f"label={e.label}")
        if e.plural:
            bits.append("plural=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: " + " ".join(bits))
    return "\n".join(lines)


SETTINGS = {
    "yard": Place(name="the shrine yard", offers={"bells", "flowers"}),
    "path": Place(name="the stone path by the shrine", offers={"bells", "rice"}),
    "garden": Place(name="the shrine garden", offers={"flowers", "rice"}),
}

PLACES = SETTINGS


CURATED = [
    StoryParams(animal="Milo", animal_type="cat", place="yard", temptation="bells", treasure="bell", guide="keeper", name="Milo"),
    StoryParams(animal="Pip", animal_type="rabbit", place="path", temptation="rice", treasure="cake", guide="grandparent", name="Pip"),
    StoryParams(animal="Sumi", animal_type="fox", place="garden", temptation="flowers", treasure="flowers", guide="keeper", name="Sumi"),
]


ASP_RULES = r"""
risky(A,T) :- temptation(A), treasure(T), match(A,T).
valid(Place,A,T) :- offers(Place,A), risky(A,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.offers):
            lines.append(asp.fact("offers", pid, a))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for tr in TREASURES:
        lines.append(asp.fact("treasure", tr))
    for a, t in [("bells", "bell"), ("rice", "cake"), ("flowers", "flowers")]:
        lines.append(asp.fact("match", a, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("Only in python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible shrine story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n) * 50):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal_type} / {p.temptation} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
