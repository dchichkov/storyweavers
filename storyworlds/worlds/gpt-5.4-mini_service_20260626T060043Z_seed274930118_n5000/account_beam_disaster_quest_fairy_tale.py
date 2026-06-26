#!/usr/bin/env python3
"""
storyworlds/worlds/account_beam_disaster_quest_fairy_tale.py
============================================================

A small fairy-tale story world about an account, a beam, a looming disaster,
and a quest that sets things right.

Seed premise:
- A messenger must give an account of a troubling crack in a great beam.
- The crack can become a disaster when the storm rises.
- A quest for a strong oak brace, plus careful hands and honest speech,
  can save the hall before dawn.

The script models a tiny stateful domain with physical meters and emotional
memes, generates a complete child-facing story, and supports grounded QA plus
an inline ASP twin for reasonableness checks.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    stormy: bool = False


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    goal: str
    setting: str
    danger: str
    keyword: str = "quest"


@dataclass
class Beam:
    label: str
    supports: str
    crack_risk: float


@dataclass
class Brace:
    id: str
    label: str
    phrase: str
    guards: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def join2(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def beam_crack_risk(world: World) -> bool:
    beam = world.get("beam")
    return beam.meters.get("crack", 0.0) >= THRESHOLD


def disaster_risk(world: World) -> bool:
    return world.get("beam").meters.get("crack", 0.0) >= THRESHOLD and world.get("storm").meters.get("wind", 0.0) >= THRESHOLD


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    beam = world.get("beam")
    storm = world.get("storm")
    hall = world.get("hall")

    if storm.meters.get("wind", 0.0) >= THRESHOLD and beam.meters.get("crack", 0.0) >= THRESHOLD:
        sig = ("disaster",)
        if sig not in world.fired:
            world.fired.add(sig)
            hall.meters["danger"] = hall.meters.get("danger", 0.0) + 1
            produced.append("The hall shuddered, for the beam might bring disaster.")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_disaster(world: World, quest: Quest) -> bool:
    sim = world.copy()
    sim.get("storm").meters["wind"] = 1.0
    sim.get("beam").meters["crack"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("hall").meters.get("danger", 0.0) >= THRESHOLD


def tell_account(world: World, hero: Entity, elder: Entity, beam: Entity) -> None:
    world.say(
        f"One evening, {elder.label} gave {hero.id} an account of the great beam in the hall: "
        f"it had begun to crack, and no one wanted a disaster to wake in the night."
    )
    hero.memes["concern"] = hero.memes.get("concern", 0.0) + 1
    beam.meters["crack"] = 1.0


def begin_quest(world: World, hero: Entity, quest: Quest, brace: Brace) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} loved the old stories, so {hero.pronoun().capitalize()} set out on a quest to {quest.verb}, "
        f"for the hall needed {brace.phrase} before the storm grew wild."
    )


def warning(world: World, elder: Entity, hero: Entity, beam: Entity) -> None:
    if beam_crack_risk(world):
        world.say(
            f'"If the wind rises," said {elder.label}, "the beam could cause a disaster."'
        )
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1


def journey(world: World, hero: Entity, quest: Quest, brace: Brace) -> None:
    hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1
    world.say(
        f"{hero.id} went through the whispering wood, past a silver brook and under a beam of moonlight, "
        f"until {hero.pronoun()} found the {brace.label} in an old oak grove."
    )


def return_and_fix(world: World, hero: Entity, brace: Brace) -> None:
    beam = world.get("beam")
    hall = world.get("hall")
    storm = world.get("storm")
    beam.meters["crack"] = 0.0
    hall.meters["danger"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} hurried home with the {brace.label}. Together, the good folk set it beneath the beam, "
        f"and the crack was held fast."
    )
    if storm.meters.get("wind", 0.0) >= THRESHOLD:
        world.say(
            f"When the storm finally came, the beam held steady, and the feared disaster never happened."
        )
    else:
        world.say(
            f"Before the storm could grow fierce, the beam was safe, and the hall slept in peace."
        )


def end_account(world: World, hero: Entity, elder: Entity, brace: Brace) -> None:
    world.say(
        f"At dawn, {hero.id} gave the queen an account of the quest, and {elder.label} smiled, "
        f"for the hall shone strong again beneath the beam."
    )


SETTINGS = {
    "castle": Place(name="the castle", stormy=True),
    "hall": Place(name="the great hall", stormy=True),
    "village": Place(name="the village", stormy=False),
}

QUESTS = {
    "brace_quest": Quest(
        id="brace_quest",
        verb="fetch a strong oak brace",
        gerund="fetching a strong oak brace",
        goal="save the hall",
        setting="the old oak grove",
        danger="storm",
    ),
}

BEAMS = {
    "hall_beam": Beam(label="great beam", supports="the hall roof", crack_risk=1.0),
}

BRACES = {
    "oak_brace": Brace(
        id="oak_brace",
        label="oak brace",
        phrase="a strong oak brace",
        guards="the beam",
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Anya", "Rosie", "Elin", "Tessa"]
BOY_NAMES = ["Robin", "Jasper", "Pip", "Evan", "Tobin", "Luca"]
TRAITS = ["brave", "kind", "curious", "cheerful", "gentle"]


@dataclass
class StoryParams:
    place: str
    quest: str
    brace: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("castle", "brace_quest", "oak_brace"), ("hall", "brace_quest", "oak_brace")]


def explain_rejection(quest: Quest, brace: Brace) -> str:
    return (
        f"(No story: this tale needs a quest that truly protects the beam, and "
        f"{brace.label} is the only brace that fits the fairy-tale repair.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world about an account, a beam, a disaster, and a quest."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--brace", choices=BRACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["queen", "king"])
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
              and (args.quest is None or c[1] == args.quest)
              and (args.brace is None or c[2] == args.brace)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest_id, brace_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, brace=brace_id, name=name, gender=gender, elder=elder, trait=trait)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=f"the {params.elder}"))
    hall = world.add(Entity(id="hall", kind="place", type="hall", label="the hall"))
    beam = world.add(Entity(id="beam", kind="thing", type="beam", label="the great beam"))
    storm = world.add(Entity(id="storm", kind="thing", type="storm", label="the storm"))
    brace = world.add(Entity(id="brace", kind="thing", type="brace", label=BRACES[params.brace].label))

    storm.meters["wind"] = 0.0
    beam.meters["crack"] = 0.0
    hall.meters["danger"] = 0.0

    quest = QUESTS[params.quest]

    world.say(f"Once upon a time, in {SETTINGS[params.place].name}, there lived {hero.id}, a {params.trait} little {params.gender}.")
    world.say(f"{hero.id} loved listening to wise folk, and {hero.pronoun().capitalize()} always wanted an honest account of how trouble began.")

    world.para()
    tell_account(world, hero, elder, beam)
    warning(world, elder, hero, beam)
    begin_quest(world, hero, quest, brace)

    world.para()
    journey(world, hero, quest, brace)
    storm.meters["wind"] = 1.0
    propagate(world, narrate=True)

    world.para()
    return_and_fix(world, hero, brace)
    end_account(world, hero, elder, brace)

    world.facts.update(hero=hero, elder=elder, hall=hall, beam=beam, storm=storm, brace=brace, quest=quest)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short fairy tale for a child about {hero.id}, a beam, and a disaster that is averted by a quest.',
        f"Tell a gentle story where {hero.id} hears an account of trouble and goes on a quest to {quest.verb}.",
        f'Write a fairy tale that uses the words "account", "beam", and "disaster" and ends in safety.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    brace = f["brace"]
    qa = [
        QAItem(
            question=f"Who went on the quest to help the hall?",
            answer=f"{hero.id} went on the quest to help the hall after hearing the account of the cracked beam.",
        ),
        QAItem(
            question=f"What did {hero.id} hear an account about?",
            answer=f"{hero.id} heard an account about the great beam in the hall and how it could bring disaster in a storm.",
        ),
        QAItem(
            question=f"What did the quest bring back?",
            answer=f"The quest brought back {brace.label}, which helped keep the beam steady.",
        ),
        QAItem(
            question=f"Who gave the account at dawn?",
            answer=f"{hero.id} gave the account at dawn, while {elder.label} smiled beside the safe beam.",
        ),
    ]
    if disaster_risk(world):
        qa.append(
            QAItem(
                question="Why was the disaster feared?",
                answer="The disaster was feared because the beam was cracked and the storm had begun to rise.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beam?",
            answer="A beam is a long, sturdy piece of wood that can hold up a roof or a ceiling.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a brave journey to find something needed or to help someone in trouble.",
        ),
        QAItem(
            question="What is an account?",
            answer="An account is a spoken or written telling of what happened.",
        ),
        QAItem(
            question="What is a disaster?",
            answer="A disaster is a very bad event that causes harm or great trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa], "", "== World knowledge ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa]]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place, quest, brace) :- place(place), quest(quest), brace(brace).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for b in BRACES:
        lines.append(asp.fact("brace", b))
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
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
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


CURATED = [
    StoryParams(place="castle", quest="brace_quest", brace="oak_brace", name="Mira", gender="girl", elder="queen", trait="brave"),
    StoryParams(place="hall", quest="brace_quest", brace="oak_brace", name="Robin", gender="boy", elder="king", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
