#!/usr/bin/env python3
"""
A small magic-superhero storyworld about a disobedient helper, a jar of mayo,
and a mysterious yawn that reveals why listening matters.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    partner: str
    villain: str
    place: str
    magic: str
    food: str
    seed: Optional[int] = None
    scenario: str = "moon_kitchen"
    telling_mode: int = 0
    variant: int = 0


HERO_NAMES = ["Luna", "Milo", "Ivy", "Tara", "Ezra", "Juno"]
PARTNER_NAMES = ["Pip", "Bea", "Rue", "Ollie", "Skye", "Nico"]
VILLAIN_NAMES = ["Captain Crumble", "Dr. Drowse", "The Sneaky Shadow", "Mister Muddle"]
PLACES = ["Moon Kitchen", "Bright Plaza", "Cloud Harbor", "Starry School"]

SCENARIOS: dict[str, dict[str, str]] = {
    "moon_kitchen": {
        "premise": "the moon-shaped oven began to yawn blue sparks",
        "trouble": "a disobedient enchanted spoon had carried a jar of mayo onto the roof",
        "clue": "each blue spark appeared whenever the spoon ignored a spoken instruction",
        "risk": "grabbing the spoon would make it fling the mayo into the sleepy oven",
        "villain_action": "Captain Crumble had charmed the spoon to obey every silly command except a careful one",
        "hero_action": "held the silver serving tray beneath the drifting jar",
        "partner_action": "read the calm instruction written in the magic cookbook",
        "solution": "the spoon stopped, the mayo landed safely on the tray, and the oven closed its glowing mouth",
        "repair": "washed the spoon, returned the mayo, and removed the charm",
        "lesson": "A brave hero listens before giving magic a command.",
        "ending": "That night, the oven baked moon-shaped sandwiches while the spoon politely waited.",
    },
    "plaza_fountain": {
        "premise": "the town fountain gave a huge yawn and sprayed clouds of white foam",
        "trouble": "a disobedient magic cart was rolling a jar of mayo toward the fountain steps",
        "clue": "the cart turned whenever someone shouted, but paused when someone spoke gently",
        "risk": "chasing it would make the cart race faster down the slippery stones",
        "villain_action": "Dr. Drowse had taught the cart to mistake loudness for important instructions",
        "hero_action": "spread a superhero cape across the bottom step as a soft brake",
        "partner_action": "whispered the cart's true stopping word from the old spell book",
        "solution": "the cart slowed, the mayo stayed upright, and the fountain settled into a quiet yawn",
        "repair": "scrubbed the foam away and changed the cart's spell to reward careful listening",
        "lesson": "Gentle words can guide magic better than a loud command.",
        "ending": "The fountain sparkled peacefully as everyone shared mayo sandwiches in the plaza.",
    },
    "cloud_harbor": {
        "premise": "a sleepy cloud opened its mouth and let out a thunderous yawn",
        "trouble": "a disobedient flying tray was carrying mayo over the harbor boats",
        "clue": "the tray dipped whenever its silver bell rang twice",
        "risk": "jumping at it would scatter the jar and splash the boats below",
        "villain_action": "The Sneaky Shadow had tied the bell to a backwards spell",
        "hero_action": "used a magic umbrella to catch the falling jar",
        "partner_action": "counted the bell rings and reversed the tiny spell",
        "solution": "the tray leveled, the mayo landed in the umbrella, and the boats stayed clean",
        "repair": "untied the bell and taught the tray to follow one clear owner",
        "lesson": "A careful clue is more useful than a hurried leap.",
        "ending": "The cloud gave one small polite yawn while the harbor crew ate supper.",
    },
    "starry_school": {
        "premise": "the school bell yawned instead of ringing for recess",
        "trouble": "a disobedient magic lunchbox had hidden a jar of mayo inside the star map",
        "clue": "the map's stars blinked whenever the lunchbox refused a question",
        "risk": "opening the map too quickly would scatter the stars across the classroom",
        "villain_action": "Mister Muddle had mixed up the lunchbox's question-and-answer spell",
        "hero_action": "covered the map with a soft classroom blanket",
        "partner_action": "asked the lunchbox one patient question at a time",
        "solution": "the stars stayed in place, the mayo came out, and the lunchbox opened with a cheerful click",
        "repair": "sorted the spell cards and helped the lunchbox learn to answer honestly",
        "lesson": "Patience helps a mixed-up magical thing find its right action.",
        "ending": "The bell rang at last, and the children carried their mayo sandwiches outside.",
    },
}

OPENINGS = [
    "In {place}, the superhero team of {hero} and {partner} began its morning patrol.",
    "Every child in {place} knew that {hero} and {partner} protected the town with courage and care.",
    "Above {place}, {hero} and {partner} adjusted their capes and checked their magic supplies.",
    "The bright badge of the superhero team shone as {hero} and {partner} entered {place}.",
]

MONOLOGUES = [
    "{hero} thought, I want to rush in, but a true hero notices what the magic is saying.",
    "{hero} told themself, The yawn is a warning, not an invitation to leap.",
    "Inside, {hero} wondered, Could listening be stronger than my fastest power?",
    "{hero} thought, If the spoon is disobedient, I must discover why before I command it.",
]

DIALOGUES = [
    '"Wait," said {partner}. "The yawn happens for a reason." "Then we will watch first," said {hero}.',
    '"Do not chase it," said {hero}. "Can we speak gently instead?" asked {partner}.',
    '"The clue is in the timing," said {partner}. "And the safe plan is in our teamwork," replied {hero}.',
    '"I hear the magic changing," said {hero}. "Good," said {partner}. "Now let us give it one clear instruction."',
]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magic superhero storyworld about listening and repair.")
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--villain")
    ap.add_argument("--place")
    ap.add_argument("--magic")
    ap.add_argument("--food")
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


def validate_params(p: StoryParams) -> None:
    fields = {
        "hero": p.hero,
        "partner": p.partner,
        "villain": p.villain,
        "place": p.place,
        "magic": p.magic,
        "food": p.food,
    }
    for name, value in fields.items():
        if not value or not value.strip():
            raise StoryError(f"{name} must not be empty.")
    if p.hero.casefold() == p.partner.casefold():
        raise StoryError("hero and partner must be different characters.")
    if p.scenario not in SCENARIOS:
        raise StoryError(f"unknown scenario: {p.scenario}")


def generate_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p.place)
    w.add(Entity("hero", "character", p.hero, "hero", memes={"courage": 0.7, "patience": 0.3}))
    w.add(Entity("partner", "character", p.partner, "hero", memes={"observation": 0.8}))
    w.add(Entity("villain", "character", p.villain, "villain", memes={"accountability": 0.1}))
    w.add(Entity("magic", "thing", p.magic, "magic", meters={"stability": 0.4}))
    w.add(Entity("food", "thing", p.food, "food", owner="town", meters={"safety": 0.7}))
    return w


def tell(world: World, p: StoryParams) -> World:
    case = SCENARIOS[p.scenario]
    rng = random.Random((p.seed or 0) ^ p.variant ^ 0xA91CE)
    hero = world.get("hero")
    partner = world.get("partner")
    villain = world.get("villain")
    magic = world.get("magic")
    food = world.get("food")

    world.say(OPENINGS[p.telling_mode % len(OPENINGS)].format(hero=p.hero, partner=p.partner, place=p.place))
    world.say(f"They carried {p.food} and a {p.magic} charm, because magic is safest when heroes prepare.")
    world.say(f"Then {case['premise']}.")
    world.say(f"At once, they saw the trouble: {case['trouble']}.")

    world.para()
    world.say(f"{p.hero} noticed that {case['clue']}.")
    world.say(rng.choice(MONOLOGUES).format(hero=p.hero))
    world.say(rng.choice(DIALOGUES).format(hero=p.hero, partner=p.partner))
    world.say(f"{p.partner} warned, \"{case['risk'].capitalize()}.\"")
    world.say(f"Instead of rushing, the heroes made a plan around the clue.")

    world.para()
    world.say(f"{p.hero} {case['hero_action']}.")
    world.say(f"Meanwhile, {p.partner} {case['partner_action']}.")
    world.say(f"The plan worked: {case['solution']}.")
    world.say(f"Now the strange yawn made sense. {case['villain_action']}.")

    world.para()
    world.say(f'{p.villain} lowered their head. "I wanted my magic to make everyone notice me, but I made the danger worse."')
    world.say(f'"You can help repair it," said {p.hero}. "Listening is part of being a hero."')
    world.say(f"Together, they {case['repair']}.")
    world.say(f"{case['lesson']} {case['ending']}")

    hero.memes["patience"] = 1.0
    hero.memes["courage"] = 1.0
    partner.memes["trust"] = 1.0
    villain.memes["accountability"] = 1.0
    magic.meters["stability"] = 1.0
    food.meters["safety"] = 1.0
    world.fired.update({"inner_monologue_guided_choice", "magic_stabilized", "harm_repaired"})
    world.facts = {
        "hero": p.hero,
        "partner": p.partner,
        "villain": p.villain,
        "place": p.place,
        "magic": p.magic,
        "food": p.food,
        "premise": case["premise"],
        "trouble": case["trouble"],
        "clue": case["clue"],
        "risk": case["risk"],
        "hero_action": case["hero_action"],
        "partner_action": case["partner_action"],
        "solution": case["solution"],
        "villain_action": case["villain_action"],
        "repair": case["repair"],
        "lesson": case["lesson"],
        "ending": case["ending"],
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero']} and {f['partner']} solving this magical trouble: {f['trouble']}.",
        f"Include a disobedient magical object, mayo, a yawn, dialogue, and the clue {f['clue']}.",
        f"Show an inner monologue that leads to this lesson: {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who were the superheroes?", f"{f['hero']} and {f['partner']} were the superheroes who worked together."),
        QAItem("What caused the trouble?", f"The trouble began because {f['trouble']}."),
        QAItem("What clue did the heroes notice?", f"They noticed that {f['clue']}."),
        QAItem("Why did the heroes avoid rushing?", f"They avoided rushing because {f['risk']}."),
        QAItem("How did the heroes solve the problem?", f"{f['hero']} {f['hero_action']}, while {f['partner']} {f['partner_action']}. As a result, {f['solution']}."),
        QAItem("How was the harm repaired?", f"{f['villain']} admitted the mistake, and together they {f['repair']}."),
        QAItem("What lesson did the superheroes prove?", f"They proved that {f['lesson']}"),
        QAItem("What food was protected?", f"The heroes protected {f['food']}, which was safe after the magic was repaired."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an inner monologue?", "An inner monologue is a character's private thought or feeling that tells what is happening inside their mind."),
        QAItem("What is magic?", "Magic is an imaginary power that can make unusual things happen in a story."),
        QAItem("Why is listening useful?", "Listening helps someone understand a problem before choosing a safe action."),
        QAItem("What is mayo?", "Mayo is a creamy sauce often used in sandwiches and salads."),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("quality", "disobedient"),
        asp.fact("ingredient", "mayo"),
        asp.fact("signal", "yawn"),
        asp.fact("instrument", "inner_monologue"),
        asp.fact("power", "magic"),
        asp.fact("genre", "superhero"),
    ])


ASP_RULES = r"""
safe_choice(inner_monologue, magic) :- instrument(inner_monologue), power(magic).
story_ready :- quality(disobedient), ingredient(mayo), signal(yawn), safe_choice(inner_monologue, magic), genre(superhero).
#show story_ready/0.
"""


def asp_program(show: str = "#show story_ready/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "story_ready"))
    expected = {()}
    if atoms != expected:
        print(f"MISMATCH between clingo and Python: {atoms!r} != {expected!r}")
        return 1
    print("OK: clingo gate matches Python.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Pip", "Captain Crumble", "Moon Kitchen", "moonlight spell", "mayo sandwiches", seed=11, scenario="moon_kitchen", telling_mode=0, variant=11),
    StoryParams("Milo", "Bea", "Dr. Drowse", "Bright Plaza", "whisper charm", "mayo wraps", seed=29, scenario="plaza_fountain", telling_mode=1, variant=29),
    StoryParams("Ivy", "Rue", "The Sneaky Shadow", "Cloud Harbor", "silver umbrella spell", "mayo rolls", seed=47, scenario="cloud_harbor", telling_mode=2, variant=47),
    StoryParams("Tara", "Ollie", "Mister Muddle", "Starry School", "star-map magic", "mayo sandwiches", seed=61, scenario="starry_school", telling_mode=3, variant=61),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    partner_choices = [name for name in PARTNER_NAMES if name.casefold() != hero.casefold()]
    return StoryParams(
        hero=hero,
        partner=args.partner or rng.choice(partner_choices),
        villain=args.villain or rng.choice(VILLAIN_NAMES),
        place=args.place or rng.choice(PLACES),
        magic=args.magic or rng.choice(["moonlight spell", "whisper charm", "silver umbrella spell", "star-map magic"]),
        food=args.food or rng.choice(["mayo sandwiches", "mayo wraps", "mayo rolls"]),
        seed=rng.randrange(2**31),
        scenario=rng.choice(list(SCENARIOS)),
        telling_mode=rng.randrange(len(OPENINGS)),
        variant=rng.randrange(1_000_000_000),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        print(format_json(samples))
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
