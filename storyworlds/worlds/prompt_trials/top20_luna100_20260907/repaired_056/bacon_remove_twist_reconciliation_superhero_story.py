#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "rooftop kitchen": {
        "setting": "the rooftop kitchen above Bright City",
        "safe": True,
        "has_bacon": True,
        "has_alarm": True,
    },
    "sunny food truck": {
        "setting": "the sunny food-truck square",
        "safe": True,
        "has_bacon": True,
        "has_alarm": True,
    },
    "harbor diner": {
        "setting": "the harbor diner by the blue docks",
        "safe": True,
        "has_bacon": True,
        "has_alarm": False,
    },
    "moonlight bakery": {
        "setting": "the moonlight bakery",
        "safe": True,
        "has_bacon": True,
        "has_alarm": True,
    },
}

HEROES = ("Luna", "Nova", "Skye", "Mira", "Zara", "Pip")
PARTNERS = ("Tess", "Milo", "Juno", "Kai", "Ari", "Bea")
POWERS = ("super hearing", "wind lifting", "spark vision", "kindness beams")
MOODS = ("brave", "careful", "cheerful", "patient")

CASES = (
    {
        "name": "the sizzling signal",
        "opening": "At breakfast time, the city's emergency beacon began flashing beside a tray of sizzling bacon.",
        "mistake": "Luna thought the bacon itself was causing the alarm and tried to remove every slice from the kitchen.",
        "clue": "the flashing light blinked whenever the oven timer rang, not whenever anyone touched the bacon",
        "twist": "the beacon was not warning about breakfast at all; it was a practice signal hidden inside the timer",
        "action": "removed the loose timer battery and reset the beacon with the cook",
        "result": "the alarm stopped, and the bacon stayed warm for the hungry helpers",
        "reconcile": "Luna apologized for blaming the breakfast, and the cook thanked her for checking before throwing food away",
        "lesson": "a quick rescue begins with finding the real cause",
        "ending": "The city beacon glowed green while the bacon crackled safely on its pan.",
        "sound": "beep-beep",
    },
    {
        "name": "the cape and the bacon",
        "opening": "A gust of wind swept through the food-truck square just as a superhero breakfast was being served.",
        "mistake": "Luna believed a strip of bacon had wrapped around the signal flag and pulled it down.",
        "clue": "the flag rope was tangled in a red cape, while the bacon rested untouched on a plate",
        "twist": "the supposed bacon snare was actually Luna's own cape caught on the rope",
        "action": "asked her partner to hold the pole steady and carefully removed her cape from the knot",
        "result": "the flag rose again, and no breakfast had to be wasted",
        "reconcile": "Luna admitted her mistake, and her partner laughed kindly instead of teasing her",
        "lesson": "heroes can be honest when their own choices cause a problem",
        "ending": "The flag danced above the square, and the rescued bacon smelled delicious below.",
        "sound": "flap-flap",
    },
    {
        "name": "the missing breakfast",
        "opening": "The harbor diner called for help when its breakfast delivery seemed to vanish before sunrise.",
        "mistake": "Luna suspected someone had removed the bacon from the delivery basket.",
        "clue": "greasy paw prints led from the basket to a sleepy cat curled beneath the dock stairs",
        "twist": "the bacon was not stolen; the cook had placed it in a cooler marked with a star",
        "action": "followed the trail, found the cooler, and gently moved the cat away from the basket",
        "result": "the diner received its full breakfast and the cat received a safer fish treat",
        "reconcile": "Luna thanked the cook for explaining the star mark, and the cook thanked her for protecting the cat",
        "lesson": "asking a clear question can solve a mystery faster than blaming someone",
        "ending": "The cat purred beside its fish treat while bacon sizzled in the diner window.",
        "sound": "purr-purr",
    },
    {
        "name": "the smoky rainbow",
        "opening": "A rainbow smoke trail curled over the moonlight bakery during the city's hero parade.",
        "mistake": "Luna thought the baker had burned the bacon and tried to remove the parade banner instead.",
        "clue": "the smoke came from a harmless colored fog machine behind the banner",
        "twist": "the strange smoke was a rehearsal effect for the parade, not a kitchen fire",
        "action": "checked the warm ovens, then switched off the fog machine with the parade leader",
        "result": "the air cleared, and the bakery's bacon remained crisp rather than burned",
        "reconcile": "Luna apologized for rushing, and the parade leader promised to label the machine more clearly",
        "lesson": "a surprising sight deserves careful checking before a hero takes action",
        "ending": "The parade rolled on beneath clean stars, with a warm bacon breakfast waiting backstage.",
        "sound": "whoosh",
    },
)

OPENINGS = (
    "Every hero needs courage, but courage works best with careful eyes.",
    "Bright City woke to an ordinary breakfast and an extraordinary puzzle.",
    "Luna's cape was ready for action before the first kettle began to sing.",
    "A small misunderstanding can make a big hero stop and think.",
    "The morning seemed peaceful until one unusual sound crossed the street.",
)

DIALOGUE = (
    ("I should remove it right away!", "Wait. What do we know for sure?"),
    ("The bacon must be the problem.", "Let's ask who placed it there and watch what changes."),
    ("I am a superhero. I should already know.", "Superheroes still listen when a friend sees another clue."),
    ("Someone must have caused this trouble.", "We can solve it without blaming anyone."),
    ("The fastest answer feels right.", "The safest answer is the one the evidence supports."),
)

ASP_RULES = r"""
kind(bacon).
kind(remove).
kind(twist).
kind(reconciliation).
kind(superhero_story).

feature(bacon) :- kind(bacon).
feature(remove) :- kind(remove).
feature(twist) :- kind(twist).
feature(reconciliation) :- kind(reconciliation).
feature(superhero_story) :- kind(superhero_story).

setting("rooftop_kitchen").
setting("sunny_food_truck").
setting("harbor_diner").
setting("moonlight_bakery").

bacon_ok("rooftop_kitchen").
bacon_ok("sunny_food_truck").
bacon_ok("harbor_diner").
bacon_ok("moonlight_bakery").

alarm_ok("rooftop_kitchen").
alarm_ok("sunny_food_truck").
alarm_ok("moonlight_bakery").

compatible(P) :- setting(P), bacon_ok(P).
safe_rescue(P) :- setting(P), bacon_ok(P), alarm_ok(P).

#show compatible/1.
#show safe_rescue/1.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    partner: str
    power: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly superhero storyworld about bacon, removal, a twist, and reconciliation."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_facts() -> str:
    import asp

    lines = []
    for place, meta in PLACES.items():
        atom = place.replace(" ", "_")
        lines.append(asp.fact("setting", atom))
        if meta["has_bacon"]:
            lines.append(asp.fact("bacon_ok", atom))
        if meta["has_alarm"]:
            lines.append(asp.fact("alarm_ok", atom))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    python_compatible = {
        place.replace(" ", "_")
        for place, meta in PLACES.items()
        if meta["has_bacon"]
    }
    python_safe = {
        place.replace(" ", "_")
        for place, meta in PLACES.items()
        if meta["has_bacon"] and meta["has_alarm"]
    }
    model = asp.one_model(asp_program("#show compatible/1.\n#show safe_rescue/1."))
    clingo_compatible = {row[0] for row in asp.atoms(model, "compatible")}
    clingo_safe = {row[0] for row in asp.atoms(model, "safe_rescue")}
    if python_compatible == clingo_compatible and python_safe == clingo_safe:
        print("OK: clingo gate matches Python reasoning.")
        return 0
    print("MISMATCH:")
    print("compatible only in clingo:", sorted(clingo_compatible - python_compatible))
    print("compatible only in Python:", sorted(python_compatible - clingo_compatible))
    print("safe only in clingo:", sorted(clingo_safe - python_safe))
    print("safe only in Python:", sorted(python_safe - clingo_safe))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    if not PLACES[place]["has_bacon"]:
        raise StoryError("This superhero story requires bacon to be present in the setting.")
    hero = args.hero or rng.choice(HEROES)
    possible_partners = [name for name in PARTNERS if name != hero]
    partner = args.partner or rng.choice(possible_partners)
    if partner == hero:
        raise StoryError("The hero and partner must be different characters.")
    power = args.power or rng.choice(POWERS)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, partner=partner, power=power, mood=mood)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    key = "|".join((params.place, params.hero, params.partner, params.power, params.mood))
    return int.from_bytes(hashlib.blake2b(key.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero == params.partner:
        raise StoryError("A reconciliation needs two different characters.")

    seed = story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUE[
        (seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUE)
    ]
    place = PLACES[params.place]

    world = World(place=place["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="superhero",
        type="hero",
        meters={"energy": 1.0, "distance_to_problem": 2.0},
        memes={"courage": 1.0, "trust": 0.6},
        location=params.place,
    )
    partner = Entity(
        id=params.partner,
        kind="character",
        label="partner",
        type="helper",
        meters={"energy": 0.8, "distance_to_problem": 2.0},
        memes={"courage": 0.7, "trust": 0.7},
        location=params.place,
    )
    bacon = Entity(
        id="bacon",
        kind="food",
        label="warm bacon",
        type="bacon",
        meters={"warmth": 0.8, "distance_to_problem": 1.0},
        memes={"blamed": 0.0, "safe": 0.5},
        location=params.place,
    )
    problem = Entity(
        id="problem",
        kind="event",
        label="mysterious trouble",
        type="alarm",
        meters={"danger": 0.3},
        memes={"understood": 0.0},
        location=params.place,
    )
    world.entities = {
        entity.id: entity for entity in (hero, partner, bacon, problem)
    }

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} superhero with {params.power}, arrived at "
        f"{world.place} with {params.partner}."
    )
    world.say(case["opening"])

    world.para()
    world.say(
        f"The trouble made a strange sound: '{case['sound']}.' "
        f"{params.hero} saw the bacon nearby and {case['mistake']}"
    )
    world.say(f"'{dialogue[0]}' {params.hero} said. '{dialogue[1]}' {params.partner} replied.")
    world.say(
        f"Instead of rushing, they watched together. Then they noticed that {case['clue']}."
    )

    world.para()
    world.say(
        f"That was the twist: {case['twist']}. "
        f"The bacon had never been the true danger."
    )
    world.say(
        f"{params.hero} lowered their cape and said, 'I am sorry. I made a fast guess.'"
    )
    world.say(
        f"{params.partner} smiled. 'Thank you for saying that. We can fix it together.'"
    )
    world.say(
        f"Working as a team, they {case['action']}. "
        f"Because they checked the cause first, {case['result']}."
    )

    world.para()
    world.say(f"The reconciliation was simple: {case['reconcile']}.")
    world.say(f"They learned that {case['lesson']}.")
    world.say(case["ending"])

    hero.meters["energy"] = 0.7
    hero.meters["distance_to_problem"] = 0.0
    hero.memes["courage"] = 1.2
    hero.memes["trust"] = 1.0
    partner.meters["distance_to_problem"] = 0.0
    partner.memes["trust"] = 1.0
    bacon.memes["blamed"] = 0.0
    bacon.memes["safe"] = 1.0
    problem.memes["understood"] = 1.0
    problem.meters["danger"] = 0.0

    world.trace = [
        f"noticed:bacon at {params.place}",
        f"misunderstood:{case['mistake']}",
        f"observed:{case['clue']}",
        f"twist:{case['twist']}",
        f"removed_or_fixed:{case['action']}",
        f"reconciled:{case['reconcile']}",
    ]
    world.facts = {
        "hero": params.hero,
        "partner": params.partner,
        "place": params.place,
        "setting": place["setting"],
        "power": params.power,
        "case": case["name"],
        "bacon": "warm bacon was present and kept safe",
        "mistake": case["mistake"],
        "clue": case["clue"],
        "twist": case["twist"],
        "action": case["action"],
        "reconciliation": case["reconcile"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a child-friendly superhero story about {params.hero} and {params.partner} at {place['setting']}.",
        f"Include bacon, an attempt to remove something, a surprising twist, and a reconciliation between {params.hero} and {params.partner}.",
        f"Show how careful evidence changes what the superhero decides to do in the {case['name']} case.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} first think the bacon caused?",
            answer=f"{params.hero} first believed that {case['mistake'].rstrip('.')}. That was an untested guess, not the real cause.",
        ),
        QAItem(
            question="What clue revealed the twist?",
            answer=f"They noticed that {case['clue']}. This showed that {case['twist'].capitalize()}.",
        ),
        QAItem(
            question=f"What did {params.hero} do to help?",
            answer=f"{params.hero} and {params.partner} {case['action']}. Their careful choice meant that {case['result']}.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.partner} reconcile?",
            answer=f"{case['reconcile'].capitalize()}. They repaired their teamwork by speaking honestly and kindly.",
        ),
        QAItem(
            question="What lesson did the superheroes learn?",
            answer=f"They learned that {case['lesson']}. The twist became useful because it encouraged them to check the real cause.",
        ),
    ]

    world_qa = [
        QAItem(
            question="Why should a superhero check before removing something?",
            answer="A superhero should check first because removing the wrong thing can create a new problem or waste something useful.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters think is happening.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement so people can understand one another and work together again.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.label:
                details.append(f"label={entity.label}")
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(details)}")
        for event in sample.world.trace:
            print(f"  event: {event}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(
        place="rooftop kitchen",
        hero="Luna",
        partner="Tess",
        power="super hearing",
        mood="brave",
    ),
    StoryParams(
        place="sunny food truck",
        hero="Nova",
        partner="Milo",
        power="wind lifting",
        mood="careful",
    ),
    StoryParams(
        place="moonlight bakery",
        hero="Skye",
        partner="Juno",
        power="kindness beams",
        mood="patient",
    ),
    StoryParams(
        place="harbor diner",
        hero="Mira",
        partner="Kai",
        power="spark vision",
        mood="cheerful",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1.\n#show safe_rescue/1."))
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for params in CURATED:
            sample = generate(params)
            if not sample.story.strip() or len(sample.story_qa) < 3:
                print("MISMATCH: generated story validation failed.")
                sys.exit(1)
        print("OK: generated stories passed validation.")
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show compatible/1.\n#show safe_rescue/1."))
        print("compatible:", asp.atoms(model, "compatible"))
        print("safe_rescue:", asp.atoms(model, "safe_rescue"))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            attempt += 1
            local_rng = random.Random(base_seed + attempt * 7919)
            params = resolve_params(args, local_rng)
            params.seed = base_seed + attempt * 7919
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
