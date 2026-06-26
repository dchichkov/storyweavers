#!/usr/bin/env python3
"""
A small story world about a harmless-looking picnic, a poisonous spill, and a
comic conflict that ends with a safer solution.

The world simulates a child-friendly comedy beat:
- someone wants to use or serve something tasty,
- another character notices it is poisonous,
- the conflict escalates in a silly, not scary way,
- they fix it by switching to a safe bowl or throwing it away,
- the ending image proves the danger was handled.

The script follows the Storyweavers contract:
- standalone stdlib Python
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- supports text, QA, JSON, trace, ASP, and verify modes
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["danger", "mess", "clean", "care", "joy", "conflict", "alarm", "relief"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Toxin:
    id: str
    label: str
    phrase: str
    safe_name: str
    danger_kind: str
    smell: str
    joke: str


@dataclass
class Safety:
    id: str
    label: str
    covers: set[str]
    neutralizes: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Place) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def activity_sentence(action: str) -> str:
    return {
        "make_soup": "make a special soup",
        "taste_jam": "taste the jam",
        "serve_punch": "serve the punch",
        "inspect_mushrooms": "inspect the mushrooms",
    }[action]


def comedy_detail(action: str) -> str:
    return {
        "make_soup": "The spoon clinked like a tiny drum, as if it wanted to join the argument.",
        "taste_jam": "The jar wobbled on the table like it was listening too hard.",
        "serve_punch": "The punch bowl sat there like a shiny red moon with a lid.",
        "inspect_mushrooms": "The basket looked serious, but the rabbit-shaped label did not.",
    }[action]


def safe_fix(toxin: Toxin) -> Safety:
    return SAFETY[toxin.id]


def is_dangerous(toxin: Toxin) -> bool:
    return True


def resolve_conflict(world: World, hero: Entity, parent: Entity, toxin: Toxin) -> None:
    fix = safe_fix(toxin)
    fix_ent = world.add(Entity(
        id=fix.id,
        type="thing",
        label=fix.label,
        protective=True,
        covers=set(fix.covers),
        plural=fix.plural,
    ))
    fix_ent.worn_by = hero.id
    world.say(
        f"{parent.label_word} pointed at the {toxin.label} and said, "
        f'"Nope, not the snack. That is {toxin.phrase}."'
    )
    world.say(
        f"{hero.id} made a face so dramatic it could have won a prize, and then "
        f"{hero.pronoun()} helped {parent.label_word} {fix.prep}."
    )
    world.say(
        f"Once they {fix.tail}, the {toxin.label} stayed out of the bowls, "
        f"and {hero.id} could laugh about the silly mistake."
    )


def tell_story(world: World, hero: Entity, parent: Entity, toxin: Toxin, action: str) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who loved kitchen games "
        f"and very shiny labels."
    )
    world.say(
        f"One afternoon, {hero.id} wanted to {activity_sentence(action)}."
    )
    world.say(comedy_detail(action))
    world.para()
    world.say(
        f"Then {parent.id} noticed the {toxin.label} first and frowned in the "
        f"silly way people do when they almost sip the wrong cup."
    )
    world.say(
        f'"Wait," {parent.label_word} said. "That can be poisonous."'
    )
    hero.memes["conflict"] += 1
    hero.memes["alarm"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{hero.id} gasped, because the tiny party had turned into a big no-thank-you."
    )
    world.say(
        f"{hero.id} tried to argue, but the argument sounded funny even to {hero.pronoun('object')}."
    )
    world.para()
    resolve_conflict(world, hero, parent, toxin)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"In the end, the poisonous thing stayed safely closed, the safe bowl "
        f"sat in the middle of the table, and the room smelled like laughter and clean spoons."
    )
    world.facts.update(hero=hero, parent=parent, toxin=toxin, action=action, fix=safe_fix(toxin))


SETTINGS = {
    "kitchen": Place(id="kitchen", place="the kitchen", indoor=True, affords={"make_soup", "taste_jam", "serve_punch", "inspect_mushrooms"}),
    "picnic": Place(id="picnic", place="the picnic blanket", indoor=False, affords={"taste_jam", "serve_punch"}),
}

TOXINS = {
    "berries": Toxin(
        id="berries",
        label="berries",
        phrase="poisonous berries from the wrong bush",
        safe_name="blueberries",
        danger_kind="poisonous",
        smell="sweet",
        joke="they looked like tiny cherries wearing trouble",
    ),
    "mushrooms": Toxin(
        id="mushrooms",
        label="mushrooms",
        phrase="poisonous mushrooms with pointy hats",
        safe_name="button mushrooms",
        danger_kind="poisonous",
        smell="earthy",
        joke="they looked like umbrellas for ants",
    ),
    "punch": Toxin(
        id="punch",
        label="punch",
        phrase="poisonous punch from the prank bottle",
        safe_name="lemonade",
        danger_kind="poisonous",
        smell="fruity",
        joke="it was red enough to make everyone suspicious",
    ),
}

SAFETY = {
    "berries": Safety(
        id="blueberries",
        label="a bowl of blueberries",
        covers={"mouth"},
        neutralizes={"poisonous"},
        prep="swap the berries out for a safe bowl",
        tail="swapped the berries out for the blueberries",
    ),
    "mushrooms": Safety(
        id="safebasket",
        label="a basket of store-bought mushrooms",
        covers={"hands"},
        neutralizes={"poisonous"},
        prep="put the wild mushrooms back and get safe ones",
        tail="put the wild mushrooms back and got safe ones",
    ),
    "punch": Safety(
        id="lemonade",
        label="a pitcher of lemonade",
        covers={"mouth"},
        neutralizes={"poisonous"},
        prep="pour the punch down the sink and make lemonade",
        tail="poured the punch down the sink and made lemonade",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Toby", "Luna", "Pip", "Mina"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ray"]
TRAITS = ["curious", "silly", "bouncy", "brave"]


@dataclass
class StoryParams:
    place: str
    toxin: str
    action: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for toxin in TOXINS:
                combos.append((place, action, toxin))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic story world about poisonous trouble and a safer fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toxin", choices=TOXINS)
    ap.add_argument("--action", choices=["make_soup", "taste_jam", "serve_punch", "inspect_mushrooms"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad", "Aunt Jo", "Uncle Ray"])
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
              and (args.action is None or c[1] == args.action)
              and (args.toxin is None or c[2] == args.toxin)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action, toxin = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, toxin=toxin, action=action, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero_type = params.gender
    parent_type = "mother" if params.parent in {"Mom", "Aunt Jo"} else "father"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type, traits=[params.trait, "gentle"]))
    parent = world.add(Entity(id=params.parent, kind="character", type=parent_type, label=params.parent.lower()))
    toxin = TOXINS[params.toxin]
    world.facts.update(hero=hero, parent=parent, toxin=toxin, action=params.action)
    tell_story(world, hero, parent, toxin, params.action)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    toxin = f["toxin"]
    return [
        f"Write a short comedy for a child where {hero.id} nearly meets something {toxin.danger_kind}.",
        f"Tell a funny story about a family noticing {toxin.label} before anyone makes a mistake.",
        f"Write a gentle conflict story that ends with a safer choice instead of the poisonous thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    toxin = f["toxin"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who noticed the {toxin.label} first?",
            answer=f"{parent.id} noticed the {toxin.label} first and stopped the mistake before anyone got hurt.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {parent.id} argue for a moment?",
            answer=f"They argued because {hero.id} wanted to go ahead, but {parent.id} saw that the {toxin.label} was poisonous.",
        ),
        QAItem(
            question=f"What safe choice did they use instead of the poisonous thing?",
            answer=f"They used {fix.label} instead, so the dangerous item stayed out of the meal and the story could end happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does poisonous mean?",
            answer="Poisonous means something can make a person or animal sick if they eat it, touch it, or use it the wrong way.",
        ),
        QAItem(
            question="Why do people check food carefully?",
            answer="People check food carefully because some foods look safe but are actually poisonous or spoiled, and careful checking helps keep everyone healthy.",
        ),
        QAItem(
            question="What should you do if you think something is poisonous?",
            answer="You should stop, tell a grown-up right away, and keep away from it until a safe adult checks it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
action(A) :- activity(A).
toxin(T) :- poison(T).

valid(P,A,T) :- affords(P,A), poison(T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TOXINS.items():
        lines.append(asp.fact("poison", tid))
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
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


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
    StoryParams(place="kitchen", toxin="berries", action="make_soup", name="Milo", gender="boy", parent="Mom", trait="silly"),
    StoryParams(place="kitchen", toxin="mushrooms", action="inspect_mushrooms", name="Nina", gender="girl", parent="Dad", trait="curious"),
    StoryParams(place="picnic", toxin="punch", action="serve_punch", name="Pip", gender="boy", parent="Aunt Jo", trait="bouncy"),
]


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
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.toxin} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    toxin = f["toxin"]
    return [
        f"Write a short comedy for a child where {hero.id} nearly meets something {toxin.danger_kind}.",
        f"Tell a funny story about a family noticing {toxin.label} before anyone makes a mistake.",
        f"Write a gentle conflict story that ends with a safer choice instead of the poisonous thing.",
    ]


if __name__ == "__main__":
    main()
