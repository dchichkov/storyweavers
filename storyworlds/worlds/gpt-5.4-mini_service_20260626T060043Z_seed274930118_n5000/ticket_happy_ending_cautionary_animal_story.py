#!/usr/bin/env python3
"""
storyworlds/worlds/ticket_happy_ending_cautionary_animal_story.py
===================================================================

A small animal-story world about a young animal, a special ticket, a moment of
carelessness, and a happy ending that still teaches caution.

Premise:
- A child-like animal wants to go somewhere fun that requires a ticket.
- The ticket is tiny, important, and easy to lose.
- A parent or helper warns the animal to keep the ticket safe.

Turn:
- The animal gets distracted and the ticket slips or is left behind.
- The world model tracks the risk: losing the ticket means missing the fun.

Resolution:
- A careful helper, pouch, or pocket saves the day.
- The animal learns to protect the ticket, and the story ends with the outing.

This script follows the Storyweavers storyworld contract:
- one standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- lazy ASP import in helpers, eager results import for QAItem/StoryError/StorySample
- story-driven world state with physical meters and emotional memes
- inline ASP twin plus Python reasonableness gate
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "care": 0.0, "panic": 0.0}

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
class Setting:
    place: str
    outdoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    clue: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ticket:
    label: str
    phrase: str
    type: str
    needs_holder: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Pouch:
    id: str
    label: str
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.weather = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


SETTINGS = {
    "station": Setting("the station", outdoor=False, affords={"ride"}),
    "fair": Setting("the fairground", outdoor=True, affords={"ride"}),
    "zoo": Setting("the zoo gate", outdoor=True, affords={"visit"}),
    "harbor": Setting("the harbor", outdoor=True, affords={"boat"}),
}

ACTIVITIES = {
    "ride": Activity(
        id="ride",
        verb="ride the bright train",
        gerund="riding the bright train",
        rush="dash onto the train",
        risk="miss the train",
        clue="ticket",
        weather="windy",
        tags={"ticket", "travel"},
    ),
    "visit": Activity(
        id="visit",
        verb="go see the animals",
        gerund="visiting the animals",
        rush="hurry to the gate",
        risk="miss the animal show",
        clue="ticket",
        weather="sunny",
        tags={"ticket", "animals"},
    ),
    "boat": Activity(
        id="boat",
        verb="take the little boat ride",
        gerund="taking the boat ride",
        rush="run down to the dock",
        risk="lose the boarding ticket",
        clue="ticket",
        weather="breezy",
        tags={"ticket", "water"},
    ),
}

TICKETS = {
    "train": Ticket(
        label="ticket",
        phrase="a small train ticket with a blue stripe",
        type="ticket",
        genders={"girl", "boy"},
    ),
    "zoo": Ticket(
        label="ticket",
        phrase="a zoo ticket with a picture of a lion",
        type="ticket",
        genders={"girl", "boy"},
    ),
    "boat": Ticket(
        label="ticket",
        phrase="a boat ticket with a silver stamp",
        type="ticket",
        genders={"girl", "boy"},
    ),
}

POUCHES = [
    Pouch(
        id="pocket_pouch",
        label="a little pocket pouch",
        prep="put the ticket into a little pocket pouch first",
        tail="slipped the ticket into the pocket pouch",
    ),
    Pouch(
        id="string_bag",
        label="a string bag",
        prep="tie the ticket to a string bag",
        tail="tied the ticket to the string bag",
    ),
    Pouch(
        id="helper_hand",
        label="the helper's careful hand",
        prep="let the helper hold the ticket",
        tail="let the helper hold the ticket",
    ),
]

NAMES_GIRL = ["Mina", "Luna", "Pip", "Nina", "Tia", "Mara", "Kiki", "Bela"]
NAMES_BOY = ["Toby", "Milo", "Ollie", "Paco", "Benny", "Rufus", "Jasper", "Arlo"]
TRAITS = ["small", "brave", "curious", "bouncy", "gentle", "cheerful", "silly"]


@dataclass
class StoryParams:
    place: str
    activity: str
    ticket: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def ticket_at_risk(activity: Activity, ticket: Ticket) -> bool:
    return ticket.needs_holder and "ticket" in activity.tags


def select_pouch(activity: Activity, ticket: Ticket) -> Optional[Pouch]:
    if not ticket_at_risk(activity, ticket):
        return None
    return POUCHES[0]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for ticket_id in TICKETS:
                if ticket_at_risk(ACTIVITIES[act_id], TICKETS[ticket_id]):
                    combos.append((place, act_id, ticket_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world about a careful ticket and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--ticket", choices=TICKETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.activity and args.ticket:
        act, tick = ACTIVITIES[args.activity], TICKETS[args.ticket]
        if not ticket_at_risk(act, tick):
            raise StoryError("That ticket would not be at risk in this activity, so there is no story.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.ticket is None or c[2] == args.ticket)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, ticket_id = rng.choice(sorted(combos))
    ticket = TICKETS[ticket_id]
    gender = args.gender or rng.choice(sorted(ticket.genders))
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, ticket=ticket_id, name=name, gender=gender, helper=helper, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["care"] += 0.5
    actor.memes["worry"] += 0.5
    if narrate:
        world.say(f"{actor.id} wanted to {activity.verb}, but {actor.pronoun('possessive')} ticket was easy to lose.")


def predict_loss(world: World, actor: Entity, activity: Activity, ticket_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    ticket = sim.get(ticket_id)
    return ticket.meters["lost"] >= THRESHOLD


def tell(setting: Setting, activity: Activity, ticket_cfg: Ticket, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather if setting.outdoor else ""

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "careless"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    ticket = world.add(Entity(id="ticket", type="ticket", label="ticket", phrase=ticket_cfg.phrase, owner=hero.id, caretaker=helper.id))

    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved adventures.")
    world.say(f"{hero.pronoun().capitalize()} had {ticket_cfg.phrase}, and {hero.id} held {ticket.it()} like a treasure.")
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {helper.label_word} were going to {setting.place} so {hero.id} could {activity.verb}.")

    world.para()
    world.say(f"At the {setting.place}, {hero.id} wanted to {activity.rush}, because {activity.gerund} sounded wonderful.")
    if predict_loss(world, hero, activity, ticket.id):
        hero.memes["worry"] += 1
        world.say(f"But {hero.pronoun('possessive')} {helper.label_word} frowned and warned, 'Keep your {ticket.label} safe, or you'll {activity.risk}.'")
        hero.memes["panic"] += 1
        world.say(f"{hero.id} nearly forgot, and the {ticket.label} slipped from {hero.pronoun('possessive')} paw.")
        ticket.meters["lost"] += 1
        hero.memes["care"] += 1
        world.say(f"Then {hero.pronoun('possessive')} {helper.label_word} reached down quickly and found it before the wind could blow it away.")
        pouch = select_pouch(activity, ticket_cfg)
        if pouch:
            world.para()
            world.say(f"{hero.pronoun('possessive').capitalize()} {helper.label_word} smiled and said, 'Let's be careful now. {pouch.prep}.'")
            ticket.meters["lost"] = 0
            ticket.meters["safe"] += 1
            hero.memes["panic"] = 0
            hero.memes["worry"] = 0
            hero.memes["joy"] += 2
            world.say(f"{hero.id} nodded hard, {pouch.tail}, and kept a hand on {ticket.label} from then on.")
            world.say(f"At last, {hero.id} could {activity.gerund}, and the {ticket.label} stayed safe the whole time.")
    else:
        world.say(f"Nothing went wrong, and {hero.id} remembered to hold the {ticket.label} tight the whole way.")
        world.say(f"That careful choice let {hero.id} enjoy {activity.gerund} without any trouble.")

    world.para()
    if ticket.meters["safe"] >= THRESHOLD:
        world.say(f"In the end, {hero.id} reached the fun place with a safe {ticket.label}, and the day stayed bright.")
    else:
        world.say(f"In the end, {hero.id} still had the {ticket.label}, and the adventure ended happily anyway.")

    world.facts.update(hero=hero, helper=helper, ticket=ticket, activity=activity, setting=setting, ticket_cfg=ticket_cfg)
    return world


ASP_RULES = r"""
ticket_risk(A, T) :- activity(A), ticket(T).
needs_pouch(T) :- ticket(T).
safe_plan(A, T) :- ticket_risk(A, T), pouch(P), protects(P, T), helps(P, A).
valid(Place, A, T) :- affords(Place, A), ticket_risk(A, T), safe_plan(A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid in TICKETS:
        lines.append(asp.fact("ticket", tid))
    for pid in range(len(POUCHES)):
        lines.append(asp.fact("pouch", f"p{pid}"))
        lines.append(asp.fact("protects", f"p{pid}", "ticket"))
        for act_id in ACTIVITIES:
            lines.append(asp.fact("helps", f"p{pid}", act_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a small child about a {f["ticket_cfg"].label} and a careful helper.',
        f"Tell a cautionary but happy story about {f['hero'].id} at {f['setting'].place} and a ticket that must stay safe.",
        f'Write a short story where a little {f["hero"].type} learns to keep a {f["ticket_cfg"].label} safe during {f["activity"].verb}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, ticket, act = f["hero"], f["helper"], f["ticket"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who loves adventures with {hero.pronoun('possessive')} {helper.label_word}.",
        ),
        QAItem(
            question=f"What was the important thing {hero.id} had to keep safe?",
            answer=f"{hero.id} had to keep the {ticket.label} safe so {hero.id} would not {act.risk}.",
        ),
        QAItem(
            question=f"How did the helper help at {f['setting'].place}?",
            answer=f"{helper.label} helped by warning {hero.id} and putting the ticket in a safer place before the fun began.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ticket for?",
            answer="A ticket is a small paper or card that shows you may go in, ride, or attend a place or event.",
        ),
        QAItem(
            question="Why should you keep a ticket safe?",
            answer="You should keep a ticket safe because losing it can mean missing the fun or not being allowed in.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        TICKETS[params.ticket],
        params.name,
        params.gender,
        params.helper,
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


CURATED = [
    StoryParams(place="station", activity="ride", ticket="train", name="Milo", gender="boy", helper="mother", trait="bouncy"),
    StoryParams(place="fair", activity="ride", ticket="train", name="Luna", gender="girl", helper="father", trait="curious"),
    StoryParams(place="zoo", activity="visit", ticket="zoo", name="Tia", gender="girl", helper="mother", trait="gentle"),
    StoryParams(place="harbor", activity="boat", ticket="boat", name="Ollie", gender="boy", helper="grandfather", trait="silly"),
]


def explain_rejection(activity: Activity, ticket: Ticket) -> str:
    return f"(No story: this activity does not put the {ticket.label} at risk in a believable way.)"


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def asp_program_text() -> str:
    return asp_program("#show valid/3.")


def build_sample_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_all_samples() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, ticket) combos:")
        for place, act, ticket in combos:
            print(f"  {place:10} {act:8} {ticket:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (ticket: {p.ticket})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
