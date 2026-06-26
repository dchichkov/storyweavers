#!/usr/bin/env python3
"""
storyworlds/worlds/chemistry_tradition_suspense_cautionary_heartwarming.py
===========================================================================

A small storyworld about a child helping with a family tradition, a little
chemistry, and a cautious turn that ends warmly.

Seed premise:
- A child wants to help with a yearly lantern-cleaning tradition.
- The work uses simple chemistry: vinegar, baking soda, water, and soap.
- Suspense comes from an unlabeled jar and the possibility of a sealed fizz.
- Cautionary note: never seal a fizzy mixture in a closed container, and never
  guess at unlabeled ingredients.
- Heartwarming ending: the child learns, helps safely, and the tradition glows.

This world is intentionally tiny and constraint-driven. It is not a frozen
paragraph with swapped names: the simulated state decides the prose and QA.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    sealed: bool = False
    open: bool = True
    clean: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    tradition: str
    weather: str = "cool evening"


@dataclass
class Reaction:
    id: str
    name: str
    ingredients: tuple[str, str]
    vessel: str
    safe_vessel: str
    result: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    open: bool
    can_hold: set[str]
    safe_for_fizz: bool
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _r_warn_sealed_fizz(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    vessel = world.entities.get("vessel")
    mix = world.facts.get("reaction")
    if not hero or not vessel or not mix:
        return out
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if vessel.sealed and mix.id == "fizz":
        sig = ("warn", vessel.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        out.append("The lid looked tight, and the fizz inside it felt too eager.")
    return out


def _r_open_relief(world: World) -> list[str]:
    out: list[str] = []
    vessel = world.entities.get("vessel")
    grandma = world.entities.get("guide")
    if not vessel or not grandma:
        return out
    if not vessel.open:
        return out
    sig = ("relief", vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The open bowl let the bubbles breathe instead of press against the lid.")
    grandma.memes["relief"] = grandma.memes.get("relief", 0) + 1
    return out


CAUSAL_RULES = [_r_warn_sealed_fizz, _r_open_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_valid_combo(reaction: Reaction, vessel: Vessel) -> bool:
    return reaction.safe_vessel == vessel.id or (reaction.vessel == vessel.id and vessel.safe_for_fizz)


def explain_rejection(reaction: Reaction, vessel: Vessel) -> str:
    return (
        f"(No story: {reaction.name} belongs in a {reaction.safe_vessel}, not a {vessel.label}. "
        f"{reaction.caution})"
    )


def make_world(setting: Setting, reaction: Reaction, vessel: Vessel, hero_name: str, hero_type: str,
               guide_name: str, guide_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_type, label=hero_name,
        memes={"curiosity": 1.0, "love": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    guide = world.add(Entity(
        id="guide", kind="character", type=guide_type, label=guide_name,
        memes={"trust": 1.0, "warmth": 1.0, "joy": 0.0, "relief": 0.0},
    ))
    jar = world.add(Entity(
        id="vessel", type="jar", label=vessel.label, open=vessel.open,
        sealed=not vessel.open, plural=vessel.plural,
        meters={"clean": 1.0}, memes={"mystery": 1.0},
    ))
    world.facts.update(hero=hero, guide=guide, vessel=jar, reaction=reaction, trait=trait)
    return world


def tell(setting: Setting, reaction: Reaction, vessel: Vessel, hero_name: str,
         hero_type: str, guide_name: str, guide_type: str, trait: str) -> World:
    world = make_world(setting, reaction, vessel, hero_name, hero_type, guide_name, guide_type, trait)
    hero = world.get("hero")
    guide = world.get("guide")
    jar = world.get("vessel")

    world.say(
        f"Every year, {guide.label}'s family held {setting.tradition}, and {hero.label} loved helping."
    )
    world.say(
        f"{hero.label} was a little {trait} {hero.type} who liked the smell of soap, steam, and fresh air."
    )
    world.say(
        f"This year the work was in {setting.place}, where the old lanterns waited for a careful cleaning."
    )

    world.para()
    world.say(
        f"{hero.label} found a jar and reached for the mixture, because {hero.pronoun('subject')} wanted to help right away."
    )
    if reaction.id == "fizz":
        world.say(
            f"The powder and liquid were meant to make a gentle fizz, but only in an open bowl."
        )
    else:
        world.say(
            f"The ingredients were simple and safe, but they still needed the right vessel."
        )

    if jar.sealed:
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(
            f"{guide.label} put a hand over the lid and said, \"Wait. Never seal a fizzy mix in a closed jar.\""
        )
        world.say(
            f"{hero.label} froze for a moment, listening to the tiny shake of danger inside the jar."
        )
    else:
        world.say(
            f"{guide.label} smiled and pointed to the open bowl, where the bubbles could pop softly and safely."
        )

    world.para()
    vessel_obj = world.get("vessel")
    if vessel_obj.sealed:
        vessel_obj.open = False
        vessel_obj.sealed = True
        world.say(
            f"They poured the ingredients into an open bowl instead, and the bubbles rose like a tiny cloud."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["worry"] = 0.0
        guide.memes["trust"] = guide.memes.get("trust", 0) + 1
        propagate(world)
    else:
        world.say(
            f"They stirred the mixture in the bowl, and the bubbles rose like a tiny cloud."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        guide.memes["trust"] = guide.memes.get("trust", 0) + 1
        propagate(world)

    world.say(
        f"{hero.label} wiped the lanterns until they shone, and {guide.label} let {hero.pronoun('object')} place each one on the clean cloth."
    )
    world.say(
        f"When the work was done, the family hung the bright lanterns for {setting.tradition}, and the whole room felt warm."
    )

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "courtyard": Setting(place="the courtyard", tradition="Lantern Night"),
    "kitchen": Setting(place="the kitchen table", tradition="Grand Clean-Up Day"),
    "porch": Setting(place="the porch", tradition="Festival Eve"),
}

REACTIONS = {
    "fizz": Reaction(
        id="fizz",
        name="a fizzy cleaning mix",
        ingredients=("vinegar", "baking soda"),
        vessel="bowl",
        safe_vessel="bowl",
        result="a gentle foam",
        caution="Never seal a fizzy mix in a closed jar, because pressure can build fast.",
        tags={"chemistry", "fizz", "cautionary"},
    ),
}

VESSELS = {
    "bowl": Vessel(id="bowl", label="open bowl", open=True, can_hold={"fizz"}, safe_for_fizz=True),
    "jar": Vessel(id="jar", label="closed jar", open=False, can_hold={"fizz"}, safe_for_fizz=False),
}

TRAITS = ["careful", "curious", "gentle", "cheerful"]
GIRL_NAMES = ["Mina", "Lina", "Nora", "Tia", "Ava", "Iris"]
BOY_NAMES = ["Noel", "Eli", "Milo", "Finn", "Owen", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for reaction in REACTIONS:
            for vessel in VESSELS:
                if is_valid_combo(REACTIONS[reaction], VESSELS[vessel]):
                    combos.append((place, reaction, vessel))
    return combos


@dataclass
class StoryParams:
    place: str
    reaction: str
    vessel: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    reaction = f["reaction"]
    setting = world.setting
    return [
        f'Write a short heartwarming story about {hero.label} helping with {setting.tradition} in {setting.place}.',
        f'Tell a cautious chemistry story where {hero.label} learns why {reaction.caution}',
        f'Write a gentle story about a child, a family tradition, and a safe fizzy mixture that stays open.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    reaction = f["reaction"]
    vessel = f["vessel"]
    setting = world.setting
    qa = [
        QAItem(
            question=f"What tradition was the family preparing for in {setting.place}?",
            answer=f"They were getting ready for {setting.tradition}, which meant cleaning and brightening the lanterns together.",
        ),
        QAItem(
            question=f"Why did {guide.label} stop {hero.label} from sealing the mixture?",
            answer=f"{guide.label} stopped {hero.label} because {reaction.caution} The mix needed an open bowl, not a closed jar.",
        ),
        QAItem(
            question=f"What happened after they used the open {vessel.label}?",
            answer=f"The mixture made a gentle fizz in the open bowl, and then the lanterns were cleaned and hung up safely.",
        ),
    ]
    if hero.memes.get("worry", 0) > 0:
        qa.append(
            QAItem(
                question=f"How did {hero.label} feel when the jar looked too tight?",
                answer=f"{hero.label} felt worried for a moment, because {hero.pronoun('subject')} learned that fizz can build pressure in a sealed jar.",
            )
        )
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.label} and {guide.label}?",
                answer=f"They finished the work together, and the lanterns glowed warmly for {setting.tradition}.",
            )
        )
    return qa


KNOWLEDGE = {
    "chemistry": [
        (
            "What is chemistry?",
            "Chemistry is the study of what things are made of and how they change when they are mixed, heated, or cleaned.",
        )
    ],
    "fizz": [
        (
            "Why does baking soda and vinegar make bubbles?",
            "They react with each other and make carbon dioxide gas, which shows up as bubbles and foam.",
        )
    ],
    "cautionary": [
        (
            "Why should you not seal a fizzy mixture in a closed jar?",
            "A fizzy mixture can make gas quickly, and if the jar is closed the pressure can build up and push the lid hard.",
        )
    ],
    "tradition": [
        (
            "What is a tradition?",
            "A tradition is something people do again and again because it is special to their family or community.",
        )
    ],
    "lantern": [
        (
            "Why are lanterns used in celebrations?",
            "Lanterns can give off a warm glow and help make a celebration feel bright, cozy, and special.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["reaction"].tags)
    out: list[QAItem] = []
    for tag in ["chemistry", "fizz", "cautionary", "tradition", "lantern"]:
        if tag in tags or tag in {"tradition", "lantern"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.label:
            parts.append(f"label={e.label}")
        if e.open is not None:
            parts.append(f"open={e.open}")
        if e.sealed:
            parts.append("sealed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="courtyard", reaction="fizz", vessel="jar", name="Mina", gender="girl", guide="grandmother", trait="careful"),
    StoryParams(place="kitchen", reaction="fizz", vessel="bowl", name="Eli", gender="boy", guide="aunt", trait="curious"),
    StoryParams(place="porch", reaction="fizz", vessel="jar", name="Nora", gender="girl", guide="grandmother", trait="gentle"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("tradition", sid, s.tradition))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
        lines.append(asp.fact("safe_vessel", rid, r.safe_vessel))
        lines.append(asp.fact("vessel_needed", rid, r.vessel))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if v.open:
            lines.append(asp.fact("open", vid))
        else:
            lines.append(asp.fact("sealed", vid))
        if v.safe_for_fizz:
            lines.append(asp.fact("safe_for_fizz", vid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Reaction, Vessel) :- setting(Place), reaction(Reaction), vessel(Vessel),
                                  safe_vessel(Reaction, Vessel).
invalid(Place, Reaction, Vessel) :- setting(Place), reaction(Reaction), vessel(Vessel),
                                    vessel_needed(Reaction, Need), Need != Vessel.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: chemistry, tradition, suspense, caution, heart.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.reaction and args.vessel:
        if not is_valid_combo(REACTIONS[args.reaction], VESSELS[args.vessel]):
            raise StoryError(explain_rejection(REACTIONS[args.reaction], VESSELS[args.vessel]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.reaction is None or c[1] == args.reaction)
              and (args.vessel is None or c[2] == args.vessel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, reaction, vessel = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["grandmother", "aunt", "mother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, reaction=reaction, vessel=vessel, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        REACTIONS[params.reaction],
        VESSELS[params.vessel],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.guide,
        "woman" if params.guide in {"mother", "grandmother", "aunt"} else "man",
        params.trait,
    )
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
        print(f"{len(combos)} compatible (place, reaction, vessel) combos:\n")
        for place, reaction, vessel in combos:
            print(f"  {place:10} {reaction:10} {vessel:8}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.reaction} at {p.place} (vessel: {p.vessel})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
