#!/usr/bin/env python3
"""
A standalone story world for a small fable-like scene in a bus depot:
a communicative helper, a cautionary warning, an inner monologue, and dialogue.

The domain premise:
- A careful young helper at a bus depot notices a looming problem.
- They nearly make a careless choice.
- Their inner monologue and a warning from an elder redirect them.
- The resolution proves that speaking up kindly can prevent trouble.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- shared result containers imported eagerly
- lazy clingo import inside ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "aunt", "sister"}
        masculine = {"boy", "man", "father", "uncle", "brother"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class Location:
    id: str
    label: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    risk: str
    consequence: str
    cue: str
    tag: str
    zone: set[str]
    keyword: str
    message: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    fragile: bool = False
    owner_type: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    calms: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.location)
        c.entities = _copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        c.lines = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "bus_depot": Location(
        id="bus_depot",
        label="the bus depot",
        indoor=True,
        affords={"announce", "warn", "wait"},
    )
}

EVENTS = {
    "crowd": Event(
        id="crowd",
        verb="speak too loudly",
        risk="startle the waiting riders",
        consequence="cause a scramble",
        cue="The depot was busy with hurrying shoes and rolling bags.",
        tag="noise",
        zone={"hearing"},
        keyword="communicative",
        message="loud voices could echo across the depot",
    ),
    "ticket": Event(
        id="ticket",
        verb="mix up the tickets",
        risk="send the wrong person to the wrong bus",
        consequence="make the line tangle",
        cue="A stack of paper tickets trembled near the counter.",
        tag="paper",
        zone={"hands"},
        keyword="ticket",
        message="a wrong ticket could cause trouble",
    ),
    "spill": Event(
        id="spill",
        verb="leave a juice bottle open",
        risk="wet the seat and floor",
        consequence="make a slippery patch",
        cue="A dropped cup wobbled by the bench.",
        tag="spill",
        zone={"floor", "bench"},
        keyword="spill",
        message="a spill could make the floor unsafe",
    ),
}

ITEMS = {
    "lanyard": Item(
        id="lanyard",
        label="a bright lanyard",
        phrase="a bright lanyard with a paper badge",
        region="neck",
        owner_type={"girl", "boy"},
    ),
    "notebook": Item(
        id="notebook",
        label="a small notebook",
        phrase="a small notebook with tidy notes",
        region="hands",
        owner_type={"girl", "boy"},
    ),
    "cap": Item(
        id="cap",
        label="a depot cap",
        phrase="a neat depot cap",
        region="head",
        owner_type={"girl", "boy"},
    ),
}

AIDS = [
    Aid(
        id="whisper",
        label="a low whisper",
        covers={"hearing"},
        calms={"noise"},
        prep="lower their voice and speak in a low whisper",
        tail="walked back to the bench and spoke softly",
    ),
    Aid(
        id="checklist",
        label="a tidy checklist",
        covers={"hands"},
        calms={"paper"},
        prep="check the list first",
        tail="double-checked the names before speaking",
    ),
    Aid(
        id="towel",
        label="a dry towel",
        covers={"floor", "bench"},
        calms={"spill"},
        prep="put the bottle away and reach for a dry towel",
        tail="cleared the spill before anyone slipped",
    ),
]

GIRL_NAMES = ["Mina", "Lina", "Sara", "Nia", "Tess", "Ada", "June", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Milo", "Theo", "Finn", "Kai", "Jude"]
TRAITS = ["careful", "curious", "gentle", "thoughtful", "brave", "kind"]


def risk_item(event: Event, item: Item) -> bool:
    return item.region in event.zone


def choose_aid(event: Event, item: Item) -> Optional[Aid]:
    for aid in AIDS:
        if event.tag in aid.calms and item.region in aid.covers:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for eid, event in EVENTS.items():
            for iid, item in ITEMS.items():
                if risk_item(event, item) and choose_aid(event, item):
                    out.append((sid, eid, iid))
    return out


def explain_rejection(event: Event, item: Item) -> str:
    if not risk_item(event, item):
        return (
            f"(No story: {event.message}, but {item.label} sits on the {item.region}, "
            f"so that choice would not be truly at risk. The caution needs a real danger.)"
        )
    return (
        f"(No story: no reasonable aid in this depot both calms {event.tag} and covers "
        f"the {item.region}. The fable needs a warning that can actually be answered.)"
    )


@dataclass
class StoryParams:
    place: str
    event: str
    item: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class StoryWorld:
    pass


def inner_monologue(hero: Entity, event: Event, item: Entity) -> str:
    return (
        f"{hero.id} thought, 'If I rush now, {hero.pronoun('possessive')} {item.label} "
        f"might end up in trouble.'"
    )


def cautionary_line(elder: Entity, hero: Entity, event: Event, item: Entity) -> str:
    return (
        f'"Careful," said {elder.ref()}, "because if you {event.verb}, you could '
        f"{event.risk}, and then {hero.pronoun('possessive')} {item.label} would {event.consequence}.""
    )


def dialogue_line(hero: Entity, elder: Entity, aid: Aid, event: Event) -> str:
    return (
        f'"Then let us {aid.prep}," said {hero.id}. "{aid.label.capitalize()} first, '
        f"and the day will stay kind."'
    )


def resolve_event(world: World, hero: Entity, elder: Entity, event: Event, item: Entity, aid: Aid) -> None:
    hero.memes["worry"] += 1
    world.say(event.cue)
    world.say(inner_monologue(hero, event, item))
    world.say(cautionary_line(elder, hero, event, item))
    hero.memes["listening"] += 1
    world.say(f"{hero.id} nodded and chose the safer way.")
    world.say(dialogue_line(hero, elder, aid, event))
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1


def tell(setting: Location, event: Event, item_cfg: Item, name: str, gender: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little", trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the old conductor",
        traits=["wise", "patient"],
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
    ))
    aid = choose_aid(event, item_cfg)
    if aid is None:
        raise StoryError(explain_rejection(event, item_cfg))

    hero.wears.append(item.id)
    world.say(
        f"In {world.location.label}, {hero.id} was a little {trait} {gender} "
        f"who carried {item.phrase} and loved to help people speak clearly."
    )
    world.say(
        f"{hero.id} knew the depot had many voices, many bags, and many buses, "
        f"so {hero.pronoun()} tried to listen for what mattered."
    )
    world.para()
    resolve_event(world, hero, elder, event, item, aid)
    world.para()
    if event.id == "crowd":
        world.say(
            f"From then on, {hero.id} spoke softly in busy places, and the depot "
            f"felt calmer because one careful voice had made room for many others."
        )
    elif event.id == "ticket":
        world.say(
            f"After that, {hero.id} checked every name twice, and the right people "
            f"found the right bus without a fuss."
        )
    else:
        world.say(
            f"After that, {hero.id} kept a towel nearby, and the floor stayed safe "
            f"for every rider who walked through."
        )

    world.facts.update(hero=hero, elder=elder, item=item, aid=aid, event=event, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    item = f["item"]
    return [
        f'Write a short fable about a child at {world.location.label} and the word "{event.keyword}".',
        f"Tell a gentle story where {hero.id} notices {event.message} and chooses a kinder plan.",
        f"Write a child-facing cautionary story that includes dialogue, an inner thought, and ends with {item.label} staying safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    item = f["item"]
    event = f["event"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who is the story about at {world.location.label}?",
            answer=f"The story is about {hero.id}, a little {hero.traits[-1]} child who notices what could go wrong and helps keep the depot calm.",
        ),
        QAItem(
            question=f"What worried {hero.id} before the safer choice was made?",
            answer=f"{hero.id} worried that {event.message}, and that {item.label} could get caught in the trouble.",
        ),
        QAItem(
            question=f"What did {elder.ref()} warn {hero.id} about?",
            answer=(
                f"{elder.ref()} warned {hero.id} that if {hero.id} went ahead carelessly, "
                f"{event.risk} and {item.label} would {event.consequence}."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} chose {aid.label} first, which fit the risk and let the day stay peaceful.",
        ),
        QAItem(
            question="What lesson does the fable suggest?",
            answer="The fable suggests that a careful warning and a kind reply can stop a small mistake from becoming a bigger one.",
        ),
    ]


KNOWLEDGE = {
    "bus_depot": [
        (
            "What is a bus depot?",
            "A bus depot is a place where buses stop, wait, and get ready to carry riders to other places.",
        )
    ],
    "whisper": [
        (
            "What is a whisper?",
            "A whisper is a very quiet way of speaking so you do not bother everyone nearby.",
        )
    ],
    "checklist": [
        (
            "Why do people use a checklist?",
            "A checklist helps people remember steps and keep from forgetting something important.",
        )
    ],
    "towel": [
        (
            "What does a towel do?",
            "A towel soaks up wet spills and helps make a slippery place safe again.",
        )
    ],
    "communicative": [
        (
            "What does communicative mean?",
            "Communicative means someone likes to share thoughts clearly and talk with others in a helpful way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["event"].tag, "bus_depot", "communicative", world.facts["aid"].id}
    out: list[QAItem] = []
    for tag in ["bus_depot", "communicative", "whisper", "checklist", "towel"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.wears:
            bits.append(f"wears={e.wears}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bus_depot", "crowd", "lanyard", "Mina", "girl", "mother", "careful"),
    StoryParams("bus_depot", "ticket", "notebook", "Owen", "boy", "father", "thoughtful"),
    StoryParams("bus_depot", "spill", "cap", "Lina", "girl", "mother", "gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-like story world set in a bus depot.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
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
              and (args.event is None or c[1] == args.event)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        if args.event and args.item:
            raise StoryError(explain_rejection(EVENTS[args.event], ITEMS[args.item]))
        raise StoryError("(No valid combination matches the given options.)")
    place, event, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, event, item, name, gender, elder, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        EVENTS[params.event],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.elder,
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


ASP_RULES = r"""
at_risk(E, I) :- event_zone(E, R), item_region(I, R).
fix(E, I, A) :- at_risk(E, I), event_tag(E, T), aid_calms(A, T), aid_covers(A, R), item_region(I, R).
valid(P, E, I) :- place(P), event(E), item(I), at_risk(E, I), fix(E, I, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("event_tag", eid, ev.tag))
        for r in ev.zone:
            lines.append(asp.fact("event_zone", eid, r))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_region", iid, it.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for c in aid.calms:
            lines.append(asp.fact("aid_calms", aid.id, c))
        for cov in aid.covers:
            lines.append(asp.fact("aid_covers", aid.id, cov))
    return "\n".join(lines)


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
    print("MISMATCH between clingo and python:")
    if a - b:
        print("only in clingo:", sorted(a - b))
    if b - a:
        print("only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, event, item) combos:\n")
        for p, e, i in triples:
            print(f"  {p:10} {e:8} {i:10}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.event} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
