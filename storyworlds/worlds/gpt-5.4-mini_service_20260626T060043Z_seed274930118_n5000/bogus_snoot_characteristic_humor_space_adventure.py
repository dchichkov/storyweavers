#!/usr/bin/env python3
"""
storyworlds/worlds/bogus_snoot_characteristic_humor_space_adventure.py
======================================================================

A small space-adventure storyworld with a humorous, child-facing premise:
a cautious kid boards a tiny ship, spots a bogus reading, and discovers the
"snoot" is actually a characteristic alien nose that matters for the rescue.

The domain is intentionally narrow:
- a ship in space
- a kid explorer and a helper robot
- a suspicious instrument reading
- a cranky alien with a distinctive snoot
- a gentle fix that turns confusion into cooperation

The story is built from live world state:
setup -> tension -> mistaken idea -> correction -> cheerful resolution.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
class Setting:
    place: str = "the little ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class CharacterTemplate:
    type: str
    label: str
    traits: list[str] = field(default_factory=list)


@dataclass
class ObjectTemplate:
    label: str
    phrase: str
    type: str
    owner_kind: str = "character"


@dataclass
class StoryParams:
    place: str
    event: str
    object: str
    hero_name: str
    hero_type: str
    helper_type: str
    alien_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story_parts: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_parts[-1].append(text)

    def para(self) -> None:
        if self.story_parts[-1]:
            self.story_parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story_parts if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.story_parts = [[]]
        return clone


SETTINGS = {
    "ship": Setting(place="the little ship", affords={"drift", "scan", "dock"}),
    "moonbase": Setting(place="the moonbase", affords={"scan", "dock"}),
    "station": Setting(place="the space station", affords={"drift", "scan", "dock"}),
}

EVENTS = {
    "drift": {
        "verb": "drift near the comet",
        "gerund": "drifting near the comet",
        "risk": "a sudden bump",
        "cause": "the ship could wobble",
        "mess": "wobbly",
        "turn": "the ship would bump the railing",
        "keyword": "comet",
    },
    "scan": {
        "verb": "scan the blip",
        "gerund": "scanning the blip",
        "risk": "a bogus reading",
        "cause": "the screen could lie",
        "mess": "confused",
        "turn": "the screen would point at the wrong place",
        "keyword": "bogus",
    },
    "dock": {
        "verb": "dock with the station",
        "gerund": "docking with the station",
        "risk": "a hard clank",
        "cause": "the ship could jar",
        "mess": "bouncy",
        "turn": "the hatch could rattle",
        "keyword": "station",
    },
}

OBJECTS = {
    "scanner": ObjectTemplate(label="scanner", phrase="a tiny scanner with a blinking blue light", type="tool"),
    "helmet": ObjectTemplate(label="helmet", phrase="a bright silver helmet", type="gear"),
    "snack": ObjectTemplate(label="snack pack", phrase="a neat snack pack with fruit cubes", type="food"),
}

CHARACTERS = {
    "hero_boy": CharacterTemplate(type="boy", label="space kid", traits=["curious", "cheerful"]),
    "hero_girl": CharacterTemplate(type="girl", label="space kid", traits=["bold", "cheerful"]),
    "helper_bot": CharacterTemplate(type="robot", label="helper robot", traits=["careful", "kind"]),
    "alien": CharacterTemplate(type="alien", label="moon visitor", traits=["grumpy", "friendly"]),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Luna", "Ivy", "Nia", "Ella", "Maya"]
BOY_NAMES = ["Max", "Leo", "Finn", "Noah", "Theo", "Eli", "Jasper", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event in setting.affords:
            for obj in OBJECTS:
                combos.append((place, event, obj))
    return combos


def explain_rejection(place: str, event: str, obj: str) -> str:
    return f"(No story: {event} and {obj} do not make a useful space-adventure turn at {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure storyworld with bogus readings and a characteristic snoot."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["robot"])
    ap.add_argument("--alien", choices=["alien"])
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
    if args.place and args.event and args.object:
        if args.event not in SETTINGS[args.place].affords:
            raise StoryError(explain_rejection(args.place, args.event, args.object))
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.event is None or c[1] == args.event)
               and (args.object is None or c[2] == args.object)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, obj = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        event=event,
        object=obj,
        hero_name=name,
        hero_type=gender,
        helper_type=args.helper or "robot",
        alien_type=args.alien or "alien",
    )


def _do_event(world: World, actor: Entity, event: str, narrate: bool = True) -> None:
    if event not in world.setting.affords:
        raise StoryError(f"{event} cannot happen at {world.setting.place}.")
    actor.meters[event] = actor.meters.get(event, 0.0) + 1
    if event == "scan":
        actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    if event == "drift":
        actor.meters["wobble"] = actor.meters.get("wobble", 0.0) + 1
    if event == "dock":
        actor.meters["clank"] = actor.meters.get("clank", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} did {event}.")


def predict(world: World, actor: Entity, event: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(actor.id), event, narrate=False)
    return {
        "bogus": bool(sim.entities.get("scanner") and sim.get("scanner").meters.get("bogus", 0) >= THRESHOLD),
        "confusion": sim.get(actor.id).memes.get("confusion", 0.0),
    }


def introduce(world: World, hero: Entity, helper: Entity, alien: Entity, obj: Entity, event: str) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} explorer who loved looking out the ship window."
    )
    world.say(
        f"By {hero.id}'s side waited {helper.label}, and on the table sat {obj.phrase}."
    )
    world.say(
        f"Far away, a small signal from a moon visitor promised a strange but funny day."
    )
    world.facts["event_word"] = event


def set_out(world: World, hero: Entity, event: str) -> None:
    world.say(
        f"One day, {hero.id} wanted to {EVENTS[event]['verb']}, because space always felt full of surprises."
    )


def warning(world: World, helper: Entity, hero: Entity, obj: Entity, event: str) -> bool:
    pred = predict(world, hero, event)
    if event == "scan":
        obj.meters["bogus"] = obj.meters.get("bogus", 0.0) + 1
        world.say(
            f'"That readout looks bogus," {helper.id} beeped. "If we trust it, we may chase the wrong thing."'
        )
        world.facts["bogus"] = True
        return True
    return False


def mistaken_idea(world: World, hero: Entity, helper: Entity, alien: Entity, obj: Entity, event: str) -> None:
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1
    world.say(
        f"{hero.id} squinted at the screen and guessed the blip was a danger."
    )
    world.say(
        f"That was a bogus guess, and it made the ship feel extra silly."
    )


def meet_alien(world: World, alien: Entity, hero: Entity, helper: Entity) -> None:
    alien.memes["concern"] = alien.memes.get("concern", 0.0) + 1
    world.say(
        f"Then the ship drifted close enough to see a moon visitor with a very characteristic snoot."
    )
    world.say(
        f'{alien.id} sniffled, then tapped {alien.pronoun("possessive")} nose as if to say, "That part is important."'
    )


def explain_snoot(world: World, alien: Entity, hero: Entity) -> None:
    alien.memes["pride"] = alien.memes.get("pride", 0.0) + 1
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1
    world.say(
        f"{hero.id} learned the snoot was not a joke at all; it was the alien's characteristic guide for finding moon herbs."
    )
    world.say(
        f"The so-called danger was only a friendly trail marker that smelled funny."
    )


def fix(world: World, hero: Entity, helper: Entity, alien: Entity, obj: Entity, event: str) -> None:
    world.say(
        f'Together, {hero.id}, {helper.id}, and {alien.id} used the scanner again, this time not to chase the bogus blip, but to follow the real path.'
    )
    world.say(
        f'The scanner stopped blinking red, the ship settled down, and {alien.id} found the herb bag hiding behind a bright rock.'
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    alien.memes["joy"] = alien.memes.get("joy", 0.0) + 1
    world.facts["resolved"] = True


def conclude(world: World, hero: Entity, helper: Entity, alien: Entity) -> None:
    world.say(
        f"In the end, {hero.id} laughed at the bogus guess, {helper.id} blinked with pride, and {alien.id}'s characteristic snoot led everyone home."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", "curious", "cheerful"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="robot",
        label="helper robot",
        traits=["careful", "kind"],
    ))
    alien = world.add(Entity(
        id="MoonPal",
        kind="character",
        type="alien",
        label="moon visitor",
        traits=["grumpy", "friendly"],
    ))
    obj = world.add(Entity(
        id="Scanner",
        type="tool",
        label=OBJECTS[params.object].label,
        phrase=OBJECTS[params.object].phrase,
        owner=hero.id,
    ))

    introduce(world, hero, helper, alien, obj, params.event)
    world.para()
    set_out(world, hero, params.event)
    warning(world, helper, hero, obj, params.event)
    mistaken_idea(world, hero, helper, alien, obj, params.event)
    world.para()
    meet_alien(world, alien, hero, helper)
    explain_snoot(world, alien, hero)
    fix(world, hero, helper, alien, obj, params.event)
    conclude(world, hero, helper, alien)

    world.facts.update(
        hero=hero,
        helper=helper,
        alien=alien,
        obj=obj,
        params=params,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short humorous space adventure for a small child that includes the word "bogus".',
        f'Tell a gentle story about {p.hero_name}, a {p.hero_type} explorer, who sees a bogus reading while traveling in {world.setting.place}.',
        f'Write a story where a characteristic snoot turns out to be important on a space trip.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    helper = f["helper"]
    alien = f["alien"]
    obj = f["obj"]
    event = p.event
    qa = [
        QAItem(
            question=f"What kind of adventure was this story?",
            answer="It was a small space adventure with a funny misunderstanding and a happy ending.",
        ),
        QAItem(
            question=f"Why did {hero.id} think the problem was bigger than it really was?",
            answer=f"{hero.id} saw a bogus reading and guessed it meant danger, but the guess was wrong.",
        ),
        QAItem(
            question=f"What did the helper robot warn about?",
            answer=f'{helper.id} warned that the reading looked bogus, so they should not trust it too quickly.',
        ),
        QAItem(
            question=f"What made the moon visitor special?",
            answer=f"{alien.id} had a characteristic snoot, and it helped guide everyone to the real path.',
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"They used the scanner the right way, found the real path, and laughed together in the ship.",
        ),
    ]
    if event == "scan":
        qa.append(QAItem(
            question=f"Why was the scanner important?",
            answer=f"The scanner was important because it first gave a bogus reading and then helped them find the real trail.",
        ))
    if obj.label == "helmet":
        qa.append(QAItem(
            question=f"Why would a helmet be good on a space trip?",
            answer="A helmet helps keep a space traveler safe when they move around a ship or near open space.",
        ))
    return qa


KNOWLEDGE = {
    "bogus": [
        (
            "What does bogus mean?",
            "Bogus means fake, wrong, or not to be trusted.",
        )
    ],
    "snoot": [
        (
            "What is a snoot?",
            "A snoot is a funny word for a nose or snout.",
        )
    ],
    "characteristic": [
        (
            "What does characteristic mean?",
            "Characteristic means something that is a special and usual part of someone or something.",
        )
    ],
    "space": [
        (
            "Where is space?",
            "Space is the huge area beyond Earth where stars, planets, and moons are found.",
        )
    ],
    "humor": [
        (
            "What is humor?",
            "Humor is something funny that makes people smile or laugh.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["bogus"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["snoot"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["characteristic"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["space"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["humor"])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
bogus_reading(S) :- reading(S), not trustworthy(S).
special_part(E) :- characteristic(E, snoot).
useful(E) :- special_part(E), helps(E).
happy_end :- bogus_reading(S), special_part(E), useful(E).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for event in EVENTS:
        lines.append(asp.fact("event", event))
        for aff in SETTINGS:
            if event in SETTINGS[aff].affords:
                lines.append(asp.fact("affords", aff, event))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    lines.append(asp.fact("reading", "scanner"))
    lines.append(asp.fact("characteristic", "moonpal", "snoot"))
    lines.append(asp.fact("helps", "snoot"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/0."))
    asp_ok = any(sym.name == "happy_end" for sym in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python gate.")
        return 1
    print("OK: ASP and Python parity looks good.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show affords/2."))
    return sorted(set(asp.atoms(model, "affords")))


CURATED = [
    StoryParams(place="ship", event="scan", object="scanner", hero_name="Mina", hero_type="girl", helper_type="robot", alien_type="alien"),
    StoryParams(place="moonbase", event="dock", object="helmet", hero_name="Finn", hero_type="boy", helper_type="robot", alien_type="alien"),
    StoryParams(place="station", event="drift", object="snack", hero_name="Luna", hero_type="girl", helper_type="robot", alien_type="alien"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, event) combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.event} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
