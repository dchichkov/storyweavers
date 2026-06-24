#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/phenomenal_horrify_card_bravery_rhyming_story.py
===============================================================================================================================

A small standalone storyworld inspired by a rhyming, bravery-centered tale.

Premise:
- A child has a special card for a stage or celebration.
- A loud, scary mishap threatens to ruin the moment.
- Bravery means staying calm, using a simple plan, and turning fright into a bright ending.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- inline ASP twin + Python reasonableness gate
- build_parser / resolve_params / generate / emit / main
- story, QA, trace, JSON, verify, and ASP modes
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("fret", "fear", "joy", "bravery", "noise", "damage", "dust"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fair"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    scare: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Guard:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.event_zone: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.event_zone = set(self.event_zone)
        clone.paragraphs = [[]]
        return clone


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.event_zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            item.meters["damage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty and torn.")
    return out


def _r_fear_to_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD or actor.memes["bravery"] < THRESHOLD:
            continue
        sig = ("brave", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} stood tall, and the scare felt smaller.")
    return out


CAUSAL_RULES = [
    _r_noise,
    _r_fear_to_bravery,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def has_risky_rhyme(event: Event, prize: Prize) -> bool:
    return prize.region in event.zone


def select_guard(event: Event, prize: Prize) -> Optional[Guard]:
    for guard in GUARDS:
        if event.scare in guard.guards and prize.region in guard.covers:
            return guard
    return None


def predict_damage(world: World, actor: Entity, event: Event, prize_id: str) -> dict[str, bool]:
    sim = world.copy()
    do_event(sim, sim.get(actor.id), event, narrate=False)
    prize = sim.entities[prize_id]
    return {"damaged": prize.meters["damage"] >= THRESHOLD}


def do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    if event.id not in world.setting.affords:
        return
    world.event_zone = set(event.zone)
    actor.meters["noise"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a brave, bright grin.")
    world.say(f"{hero.pronoun().capitalize()} loved a song that could make a day feel phenomenal.")


def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id} got a special {prize.label} to hold in the show.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and carried {prize.it()} with care.")


def arrive(world: World, hero: Entity, parent: Entity, event: Event) -> None:
    if world.setting.indoors:
        world.say(f"At {world.setting.place}, the lights glowed warm and gold.")
    else:
        world.say(f"At {world.setting.place}, the wind went whirr, then swirled.")
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {parent.type} went there to {event.verb}.")


def want(world: World, hero: Entity, event: Event) -> None:
    world.say(f"{hero.id} wanted to {event.verb}, {event.gerund} with a little hop and a whirl.")


def warn(world: World, parent: Entity, hero: Entity, event: Event, prize: Entity) -> bool:
    pred = predict_damage(world, hero, event, prize.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(f'"If you {event.verb}, your {prize.label} may get {event.risk}," {parent.pronoun("possessive")} parent said.')
    world.say(f'"Let us think of a safer plan," said {parent.pronoun("possessive")} parent, calm and kind.')
    return True


def scare(world: World, hero: Entity, event: Event) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} heard the warning and felt a fluttery fright.")
    world.say(f"{hero.pronoun().capitalize()} tried to {event.rush}, though the moment was tight.")


def freeze(world: World, parent: Entity, hero: Entity, event: Event) -> None:
    hero.memes["fear"] += 1
    world.say(f"Then {parent.pronoun('possessive')} parent held a hand and stood near.")
    world.say(f'"You can be brave," {parent.pronoun("possessive")} parent said, "even when things feel weird."')


def comfort(world: World, hero: Entity) -> None:
    if hero.memes["fear"] >= THRESHOLD:
        world.say(f"{hero.id} took one breath in, then let out one breath clear.")


def compromise(world: World, parent: Entity, hero: Entity, event: Event, prize: Entity) -> Optional[Guard]:
    guard = select_guard(event, prize)
    if guard is None:
        return None
    item = world.add(Entity(
        id=guard.id,
        type="thing",
        label=guard.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(guard.covers),
        plural=guard.plural,
    ))
    item.worn_by = hero.id
    if predict_damage(world, hero, event, prize.id)["damaged"]:
        item.worn_by = None
        del world.entities[item.id]
        return None
    world.say(f'Then {parent.pronoun("possessive")} parent smiled and found a better way.')
    world.say(f'"How about we {guard.prep}?" {parent.pronoun("possessive")} parent said, bright as day.')
    return guard


def ending(world: World, hero: Entity, parent: Entity, event: Event, prize: Entity, guard: Guard) -> None:
    hero.memes["bravery"] += 1
    hero.memes["fear"] = 0.0
    world.say(f"{hero.id} smiled, then nodded, then shone.")
    world.say(f"They {guard.tail}. Soon {hero.id} was {event.gerund}, and the scare was gone.")
    world.say(f"{hero.id}'s {prize.label} stayed neat, a phenomenal sight to see.")
    world.say(f"Brave {hero.id} kept the card safe, and sang with glee.")


def tell(setting: Setting, event: Event, prize_cfg: Prize, hero_name: str = "Mila", hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="card",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    prize_line(world, hero, prize)
    world.para()
    arrive(world, hero, parent, event)
    want(world, hero, event)
    warn(world, parent, hero, event, prize)
    scare(world, hero, event)
    freeze(world, parent, hero, event)
    comfort(world, hero)
    world.para()
    guard = compromise(world, parent, hero, event, prize)
    if guard:
        ending(world, hero, parent, event, prize, guard)

    world.facts.update(hero=hero, parent=parent, prize=prize, event=event, setting=setting, guard=guard)
    return world


SETTINGS = {
    "stage": Setting(place="the stage", indoors=True, affords={"show", "clap"}),
    "fair": Setting(place="the fair", indoors=False, affords={"show", "drum"}),
    "hall": Setting(place="the hall", indoors=True, affords={"show", "sing"}),
}

EVENTS = {
    "drum": Event(
        id="drum",
        verb="beat the drum",
        gerund="beating the drum",
        rush="grab the drum and drum too loud",
        scare="noise",
        risk="too noisy and bent",
        zone={"hands", "torso"},
        tags={"sound", "noise"},
    ),
    "show": Event(
        id="show",
        verb="join the show",
        gerund="joining the show",
        rush="dash into the show and spin too fast",
        scare="dust",
        risk="dusty and torn",
        zone={"hands", "torso"},
        tags={"show", "dust"},
    ),
    "sing": Event(
        id="sing",
        verb="sing a tune",
        gerund="singing a tune",
        rush="rush to the front and sing too loud",
        scare="noise",
        risk="too noisy and bent",
        zone={"hands", "torso"},
        tags={"song", "noise"},
    ),
    "clap": Event(
        id="clap",
        verb="clap along",
        gerund="clapping along",
        rush="clap and wave too fast",
        scare="dust",
        risk="dusty and torn",
        zone={"hands"},
        tags={"show", "dust"},
    ),
}

PRIZES = {
    "card": Prize(label="card", phrase="a shiny card", type="card", region="hands"),
    "banner": Prize(label="banner", phrase="a bright banner", type="banner", region="torso"),
}

GUARDS = [
    Guard(
        id="gloves",
        label="soft gloves",
        prep="put on soft gloves first",
        tail="walked to the stage with soft gloves on",
        covers={"hands"},
        guards={"dust"},
    ),
    Guard(
        id="earmuffs",
        label="quiet earmuffs",
        prep="wear quiet earmuffs first",
        tail="went back to the hall with quiet earmuffs on",
        covers={"hands", "torso"},
        guards={"noise"},
    ),
    Guard(
        id="smock",
        label="a tidy smock",
        prep="put on a tidy smock first",
        tail="went in with a tidy smock on",
        covers={"torso"},
        guards={"dust", "noise"},
    ),
]

HERO_NAMES = ["Mila", "Noa", "Lena", "Rae", "Ivy", "Nia"]
TRAITS = ["brave", "gentle", "steady", "cheery"]


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event_id in setting.affords:
            event = EVENTS[event_id]
            for prize_id, prize in PRIZES.items():
                if has_risky_rhyme(event, prize) and select_guard(event, prize):
                    combos.append((place, event_id, prize_id))
    return combos


def explain_rejection(event: Event, prize: Prize) -> str:
    return f"(No story: {event.gerund} would not truly trouble a {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this prize is not a typical {gender}'s choice here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about bravery, a card, and a scare.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.event and args.prize:
        event, prize = EVENTS[args.event], PRIZES[args.prize]
        if not (has_risky_rhyme(event, prize) and select_guard(event, prize)):
            raise StoryError(explain_rejection(event, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, event, prize = f["hero"], f["parent"], f["event"], f["prize"]
    return [
        'Write a short rhyming story for a child about bravery, a special card, and a surprise scare.',
        f"Tell a gentle rhyme where {hero.id} wants to {event.verb} but {parent.pronoun('possessive')} parent worries about the {prize.label}.",
        f'Create a story that includes the word "phenomenal" and ends with a brave, safe choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, event, prize = f["hero"], f["parent"], f["event"], f["prize"]
    guard = f.get("guard")
    out = [
        QAItem(question=f"What special thing did {hero.id} carry?", answer=f"{hero.id} carried {hero.pronoun('possessive')} {prize.label}, a shiny card for the show."),
        QAItem(question=f"Why did {parent.pronoun('possessive')} parent worry?", answer=f"{parent.pronoun('possessive').capitalize()} parent worried because {event.gerund} could leave the {prize.label} {event.risk}."),
        QAItem(question=f"What did {hero.id} do instead of staying scared?", answer=f"{hero.id} stayed brave, listened, and chose a safer way to {event.verb}."),
    ]
    if guard:
        out.append(QAItem(question=f"How did the {guard.label} help?", answer=f"The {guard.label} helped by covering the right part of the body so the {prize.label} stayed safe while {hero.id} joined in."))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does bravery mean?", answer="Bravery means trying the safe thing even when you feel a little scared."),
        QAItem(question="What is a card?", answer="A card is a small flat piece of paper or cardboard that can hold a message or a picture."),
        QAItem(question="What does phenomenal mean?", answer="Phenomenal means wonderful, amazing, or so good that it stands out in a special way."),
        QAItem(question="What can horrify mean?", answer="Horrify means to scare someone a lot or make them feel shocked and worried."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(E, P) :- splashes(E, R), worn_on(P, R).
protects(G, E, P) :- guard(G), prize_at_risk(E, P), guards(G, S), event_scare(E, S), covers(G, R), worn_on(P, R).
has_fix(E, P) :- protects(_, E, P).
valid(Place, E, P) :- affords(Place, E), prize_at_risk(E, P), has_fix(E, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for e in sorted(s.affords):
            lines.append(asp.fact("affords", pid, e))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("event_scare", eid, e.scare))
        for r in sorted(e.zone):
            lines.append(asp.fact("splashes", eid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GUARDS:
        lines.append(asp.fact("guard", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        EVENTS[params.event],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
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
    StoryParams(place="stage", event="show", prize="card", name="Mila", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="fair", event="drum", prize="card", name="Noa", gender="boy", parent="father", trait="steady"),
    StoryParams(place="hall", event="sing", prize="banner", name="Lena", gender="girl", parent="mother", trait="cheery"),
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
        print(f"{len(combos)} compatible story combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
