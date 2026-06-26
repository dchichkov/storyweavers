#!/usr/bin/env python3
"""
Story world: a jaunty, loud pirate tale about a simple transformation.

A small crew sails at dusk. A shy cabin helper finds a magical trinket, changes
into a proper pirate spirit, and helps the crew through a squall. The world model
tracks physical things like meters of distance, tide, and brightness, plus emotional
memes like courage, worry, and cheer.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess", "lass"}
        male = {"boy", "man", "father", "captain", "matey", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class CrewShip:
    name: str = "the Bright Gull"
    deck_height: float = 12.0
    speed: float = 0.0
    tide: str = "calm"
    weather: str = "clear"
    lanterns: float = 1.0


@dataclass
class World:
    ship: CrewShip
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return " ".join(self.story_lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    crew_name: str
    crew_type: str
    captain_name: str
    token: str
    sea_event: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    weather: str
    tide: str


@dataclass
class SeaEvent:
    id: str
    verb: str
    effect: str
    risk: str
    sound: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    before_trait: str
    after_trait: str
    mood_gain: str
    physical_gain: str
    reveal: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "harbor": Setting(place="the harbor", weather="blustery", tide="low"),
    "reef": Setting(place="the reef", weather="windy", tide="rising"),
    "island": Setting(place="the little island cove", weather="warm", tide="gentle"),
}

SEA_EVENTS = {
    "squall": SeaEvent(
        id="squall",
        verb="surge through the squall",
        effect="spray flew across the deck",
        risk="the ropes might slip",
        sound="the wind boomed like a drum",
        zone="deck",
        tags={"wind", "water", "squall"},
    ),
    "fog": SeaEvent(
        id="fog",
        verb="sail through the fog",
        effect="the mast looked far away",
        risk="the crew could not see the rocks",
        sound="the bell rang softly in the haze",
        zone="bow",
        tags={"fog"},
    ),
    "wave": SeaEvent(
        id="wave",
        verb="ride the wave",
        effect="the ship rocked high and low",
        risk="the barrels might roll",
        sound="the boards creaked and sang",
        zone="deck",
        tags={"wave", "water"},
    ),
}

TRANSFORMS = {
    "brave": Transformation(
        id="brave",
        label="a brave pirate charm",
        phrase="a brass charm shaped like a tiny wheel",
        before_trait="shy",
        after_trait="brave",
        mood_gain="courage",
        physical_gain="sparkle",
        reveal="A warm sparkle ran from the charm into the helper's heart",
        tags={"courage", "pirate", "magic"},
    ),
    "captain": Transformation(
        id="captain",
        label="a captain's sash",
        phrase="a striped sash with a silver knot",
        before_trait="plain",
        after_trait="captainly",
        mood_gain="pride",
        physical_gain="shine",
        reveal="The sash tightened with a snap and made the helper stand taller",
        tags={"pirate", "rank", "magic"},
    ),
    "parrot": Transformation(
        id="parrot",
        label="a feathered trinket",
        phrase="a bright feather token tied with blue thread",
        before_trait="quiet",
        after_trait="chatty",
        mood_gain="joy",
        physical_gain="feathers",
        reveal="The token blinked, and feathers fluttered from the helper's sleeves",
        tags={"feather", "pirate", "magic"},
    ),
}

NAMES = ["Mira", "Nell", "Jory", "Pip", "Tessa", "Bram", "Sailor", "Kit", "Luna", "Finn"]
CAPTAIN_NAMES = ["Captain Rook", "Captain Marlow", "Captain June", "Captain Brine"]
CREW_TYPES = ["deckhand", "cabin helper", "matey", "young pirate"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for e in SEA_EVENTS:
            for t in TRANSFORMS:
                combos.append((s, e, t))
    return combos


def explain_invalid(setting: str, event: str, transform: str) -> str:
    return f"(No story: {setting}, {event}, and {transform} do not make a coherent pirate tale.)"


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_squall(world: World) -> list[str]:
    out = []
    ship = world.ship
    event = world.facts.get("event")
    crew = world.facts.get("hero")
    if not event or not crew:
        return out
    hero = world.get(crew.id)
    if event.id == "squall":
        if hero.meters.get("brace", 0) < 1:
            hero.meters["soaked"] = hero.meters.get("soaked", 0) + 1
            ship.speed = max(0.0, ship.speed - 1.0)
            out.append("The deck got slick, and the ship slowed in the squall.")
    return out


def _r_transformation(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    token = world.facts.get("token")
    tr = world.facts.get("transform")
    if not hero or not token or not tr:
        return out
    if hero.memes.get("wonder", 0) >= 1 and token.meters.get("glow", 0) >= 1 and hero.memes.get("resolve", 0) >= 1:
        sig = "transformed"
        if sig not in world.facts:
            world.facts["transformed"] = True
            hero.type = "pirate"
            hero.traits = [tr.after_trait]
            hero.memes[tr.mood_gain] = hero.memes.get(tr.mood_gain, 0) + 2
            hero.meters[tr.physical_gain] = hero.meters.get(tr.physical_gain, 0) + 1
            out.append(tr.reveal + ".")
    return out


RULES = [Rule("squall", _r_squall), Rule("transformation", _r_transformation)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                for s in produced:
                    world.say(s)


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, captain: Entity, setting: Setting) -> None:
    world.say(
        f"On a {setting.weather} day at {setting.place}, a jaunty, loud pirate crew rocked on the waves."
    )
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who admired {captain.id} and wished to be bold."
    )


def setup_item(world: World, hero: Entity, token: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    token.meters["glow"] = 1
    world.say(
        f"While cleaning a small chest, {hero.id} found {token.phrase}."
    )
    world.say(
        f"{token.label.capitalize()} seemed to hum with pirate magic, and {hero.id} held {token.it()} close."
    )


def tension(world: World, hero: Entity, event: SeaEvent) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"Then the sky grew rough, and the crew had to {event.verb}; {event.sound}."
    )
    world.say(
        f"At once, {event.effect}, and {event.risk}."
    )


def choice(world: World, hero: Entity, captain: Entity, token: Entity, transform: Transformation) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    world.say(
        f"{hero.id} looked at {captain.id} and whispered, 'If I wear {transform.label}, maybe I can help.'"
    )
    world.say(
        f"{captain.id} nodded and said, 'A pirate's heart is not born loud; it grows loud when needed.'"
    )


def finish(world: World, hero: Entity, captain: Entity, event: SeaEvent) -> None:
    ship = world.ship
    hero.meters["brace"] = hero.meters.get("brace", 0) + 1
    ship.speed = 1.0
    world.say(
        f"With a deep breath, {hero.id} spread {hero.pronoun('possessive')} arms and faced the wind."
    )
    world.say(
        f"{hero.id} steadied the rope, sang a jaunty shanty, and the whole ship sailed on."
    )
    world.say(
        f"By the end, the deck was wet but safe, the crew was cheering, and {hero.id} felt like a true pirate."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.crew_name]
    event = SEA_EVENTS[params.sea_event]
    transform = TRANSFORMS[params.token]
    world = World(ship=CrewShip(name="the Bright Gull", tide=setting.tide, weather=setting.weather))

    hero = world.add(Entity(
        id=params.captain_name.replace("Captain ", ""),
        kind="character",
        type=params.crew_type,
        traits=[transform.before_trait, "eager"],
    ))
    captain = world.add(Entity(
        id=params.captain_name,
        kind="character",
        type="captain",
        traits=["jaunty", "loud"],
    ))
    token = world.add(Entity(
        id=transform.id,
        kind="thing",
        type="token",
        label=transform.label,
        phrase=transform.phrase,
        owner=hero.id,
    ))

    world.facts["hero"] = hero
    world.facts["captain"] = captain
    world.facts["token"] = token
    world.facts["event"] = event
    world.facts["transform"] = transform

    introduce(world, hero, captain, setting)
    setup_item(world, hero, token)
    tension(world, hero, event)
    choice(world, hero, captain, token, transform)
    propagate(world)
    finish(world, hero, captain, event)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    transform = f["transform"]
    return [
        f'Write a short pirate tale for a child that includes "jaunty" and "loud" and a magical change.',
        f"Tell a story about {hero.id}, a {hero.type}, who finds {transform.phrase} and becomes brave during a storm.",
        f"Write a small pirate adventure where a helper on {world.ship.name} changes through magic and helps the crew.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    event = f["event"]
    transform = f["transform"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {hero.pronoun('subject')} who started out shy and ended up brave."
        ),
        QAItem(
            question=f"What did {hero.id} find?",
            answer=f"{hero.id} found {transform.phrase}, which was a magical pirate treasure."
        ),
        QAItem(
            question=f"What changed after the magic woke up?",
            answer=f"{hero.id} changed from {transform.before_trait} to {transform.after_trait}, and the crew could handle the {event.id} together."
        ),
        QAItem(
            question=f"How did {captain.id} help?",
            answer=f"{captain.id} encouraged {hero.id} to try, and that cheer helped turn worry into resolve."
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a pirate ship?",
        answer="A pirate ship is a boat that sails the sea with a crew who works together, climbs ropes, and handles rough weather."
    ),
    QAItem(
        question="What does jaunty mean?",
        answer="Jaunty means lively, cheerful, and full of confidence."
    ),
    QAItem(
        question="What does loud mean?",
        answer="Loud means making a strong sound that is easy to hear."
    ),
    QAItem(
        question="What is a squall?",
        answer="A squall is a sudden burst of strong wind and rain at sea."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    f = world.facts
    tags |= f["event"].tags
    tags |= f["transform"].tags
    out = []
    for item in WORLD_KNOWLEDGE:
        if "pirate" in item.answer.lower() or "sea" in item.answer.lower():
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
event(E) :- event_fact(E).
transform(T) :- transform_fact(T).

compatible(S,E,T) :- setting(S), event(E), transform(T).

#show compatible/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for e in SEA_EVENTS:
        lines.append(asp.fact("event_fact", e))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform_fact", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A jaunty, loud pirate tale with a magical transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--event", choices=SEA_EVENTS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--crew-type", choices=CREW_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    event = args.event or rng.choice(list(SEA_EVENTS))
    transform = args.transform or rng.choice(list(TRANSFORMS))
    if (setting, event, transform) not in valid_combos():
        raise StoryError(explain_invalid(setting, event, transform))
    name = args.name or rng.choice(NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    crew_type = args.crew_type or rng.choice(CREW_TYPES)
    return StoryParams(
        crew_name=setting,
        crew_type=crew_type,
        captain_name=captain,
        token=transform,
        sea_event=event,
        seed=args.seed,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for e in SEA_EVENTS:
            for t in TRANSFORMS:
                combos.append((s, e, t))
    return combos


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"ship: {world.ship.name}, tide={world.ship.tide}, weather={world.ship.weather}, speed={world.ship.speed}")
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, event, transform) combos:\n")
        for s, e, t in combos:
            print(f"  {s:8} {e:8} {t:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for e in SEA_EVENTS:
                for t in TRANSFORMS:
                    p = StoryParams(
                        crew_name=s,
                        crew_type=random.choice(CREW_TYPES),
                        captain_name=random.choice(CAPTAIN_NAMES),
                        token=t,
                        sea_event=e,
                        seed=base_seed,
                    )
                    samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
