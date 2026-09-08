#!/usr/bin/env python3
"""A comic storyworld about spaghetti, drowse, pride, and a warning ignored."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    pasta: str
    name: str
    helper: str
    topping: str
    mishap: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class ComedyCase:
    warning: str
    temptation: str
    sleepy_sign: str
    bad_turn: str
    consequence: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "community kitchen": Scene("the community kitchen", "busy", "rain tapped the windows"),
    "school hall": Scene("the school hall", "cheerful", "a warm breeze pushed the curtains"),
    "grandma's porch": Scene("Grandma's porch", "cozy", "fireflies blinked in the dusk"),
}
PASTAS = {
    "long spaghetti": "a mountain of long spaghetti",
    "twisty spaghetti": "a bowl of twisty spaghetti",
    "red spaghetti": "a steaming red-sauce spaghetti",
}
NAMES = {"Luna": "girl", "Milo": "boy", "Pip": "child", "Zara": "girl"}
HELPERS = {"Auntie Bea": "adult", "Mina": "girl", "Theo": "boy", "Grandpa Sol": "adult"}
TOPPINGS = {
    "cheese": "a fluffy snowfall of cheese",
    "meatballs": "three wobbly meatballs",
    "peas": "a bright green scoop of peas",
}
MISHAPS = {
    "sneeze": "the pepper shaker stood open beside the pot",
    "ladle": "the giant ladle had a slippery wooden handle",
    "napkin": "a stack of napkins leaned toward the table edge",
    "cat": "a curious cat watched the steam with one hopeful paw raised",
}
ROUTES = ("warning_first", "pride_first", "sniff_test", "audience_first", "countdown_first", "quiet_first")

CASES = {
    "sneeze": ComedyCase(
        "Do not add pepper while yawning near the pot.",
        "the chance to make the biggest, most dramatic chef's flourish",
        "Luna's eyelids bobbed like two tiny window shades",
        "she sneezed a pepper cloud into the sauce and dropped the serving spoon",
        "the spaghetti jumped from the bowl, looped around a chair, and landed on the mayor's hat",
        "scooped the noodles into a clean bowl and washed the hat before dinner",
        "pride is fun until it stops listening to a useful warning",
        "the mayor ate dinner wearing a clean hat and one heroic noodle as a mustache",
    ),
    "ladle": ComedyCase(
        "Hold the ladle with two hands when the sauce is hot.",
        "showing everyone that a famous chef could toss spaghetti one-handed",
        "her head dipped forward each time the ladle swung",
        "she tried the trick, nodded off for one second, and flung sauce onto the ceiling",
        "a red drip landed in the shape of a surprised chicken above the stage",
        "mopped the floor, wiped the ceiling, and served smaller bowls with both hands",
        "being impressive matters less than being awake and careful",
        "the ceiling chicken watched proudly while nobody attempted a second toss",
    ),
    "napkin": ComedyCase(
        "Move the napkins before the hot bowl arrives.",
        "making a tall spaghetti tower without clearing the table",
        "she answered a question with a sleepy little snore",
        "the tower leaned, bumped the napkins, and rolled across the table like a red worm",
        "the napkins parachuted into the sauce and became tomato-colored flags",
        "used clean towels, rebuilt the meal, and placed napkins on a separate tray",
        "a small preparation can prevent a very large mess",
        "the napkins waved safely from their tray while the spaghetti stayed in its bowl",
    ),
    "cat": ComedyCase(
        "Keep the cat away from the steaming pot.",
        "proving that a perfect chef could balance the bowl while posing for applause",
        "her spoon paused in midair while her chin drifted toward her chest",
        "she posed, blinked slowly, and the cat tugged the tablecloth",
        "the bowl slid down the table and emptied into a laundry basket",
        "checked the food, cleaned the basket, and fed the cat a safe snack",
        "pride can make a warning sound very small, but consequences can be very loud",
        "the cat purred beside its snack while the rescued spaghetti steamed on a steady table",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic spaghetti story about drowse and pride.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--pasta", choices=sorted(PASTAS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--topping", choices=sorted(TOPPINGS))
    ap.add_argument("--mishap", choices=sorted(MISHAPS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in sorted(PLACES) for s in sorted(PASTAS)]


ASP_RULES = """
compatible(Place, Pasta) :- place(Place), pasta(Pasta).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        *(asp.fact("place", value) for value in PLACES),
        *(asp.fact("pasta", value) for value in PASTAS),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(symbols, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_set = set(asp_valid_combos())
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - clingo_set), sorted(clingo_set - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        pair for pair in valid_combos()
        if not args.place or pair[0] == args.place
        if not args.pasta or pair[1] == args.pasta
    ]
    if not combos:
        raise StoryError("No valid kitchen story fits those options.")
    place, pasta = rng.choice(combos)
    name = args.name or "Luna"
    helper_choices = [x for x in sorted(HELPERS) if x != name] or sorted(HELPERS)
    return StoryParams(
        place=place,
        pasta=pasta,
        name=name,
        helper=args.helper or rng.choice(helper_choices),
        topping=args.topping or rng.choice(sorted(TOPPINGS)),
        mishap=args.mishap or rng.choice(sorted(MISHAPS)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.place, params.pasta, params.name, params.helper,
        params.topping, params.mishap, params.route,
    ))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    rng = story_rng(params)
    scene = PLACES[params.place]
    case = CASES[params.mishap]
    world = World(scene)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=NAMES.get(params.name, "child"),
        memes={"pride": 0.4, "drowse": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=HELPERS[params.helper],
        memes={"care": 0.8},
    ))
    food = world.add(Entity(
        id="spaghetti",
        kind="food",
        type=params.pasta,
        meters={"heat": 0.8, "stability": 0.8},
        memes={"deliciousness": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, food=food, case=case, scene=scene)

    openings = {
        "warning_first": (
            f"In {scene.place}, {hero.id} stood beside {PASTAS[params.pasta]}, "
            f"ready to feed the whole crowd while {scene.weather}."
        ),
        "pride_first": (
            f"{hero.id} wore a paper chef hat in {scene.place} and announced that "
            f"only a genius could prepare {PASTAS[params.pasta]}."
        ),
        "sniff_test": (
            f"{hero.id} lifted the lid in {scene.place}. The spaghetti smelled wonderful, "
            f"but the pepper, steam, and tired air made one important warning easy to miss."
        ),
        "audience_first": (
            f"Everyone gathered in {scene.place} to watch {hero.id} serve {PASTAS[params.pasta]} "
            f"with {TOPPINGS[params.topping]}."
        ),
        "countdown_first": (
            f"Dinner was almost ready in {scene.place}. {hero.id} had made {PASTAS[params.pasta]}, "
            f"and a hungry crowd began counting down from ten."
        ),
        "quiet_first": (
            f"The kitchen grew quiet as {hero.id} carried {PASTAS[params.pasta]} through {scene.place}. "
            f"Only a little steam curled upward like a sleepy question mark."
        ),
    }
    world.say(openings[params.route])
    world.say(
        f"{helper.id} pointed out that {case.warning} "
        f"The warning mattered because {MISHAPS[params.mishap]}."
    )
    world.say(f'"I heard you," {hero.id} said. "I am a careful chef."')
    world.say(
        f'"Then let us keep the pot steady," {helper.id} replied. '
        f'"A careful chef does not have to prove anything."'
    )
    world.para()

    world.say(
        f"But {hero.id} wanted {case.temptation}. "
        f"The pride in the paper chef hat seemed to grow taller than the hat itself."
    )
    world.say(f"{hero.id} began to feel drowse tugging at the edges of the busy room.")
    world.say(
        f"{case.sleepy_sign.capitalize()}. "
        f"{hero.id}'s pride said, 'One more grand move!'"
    )
    hero.memes["pride"] = 1.0
    hero.memes["drowse"] = 0.8
    world.say(f'"Maybe I should stop," {hero.id} admitted.')
    world.say(f'"That would be wise," {helper.id} said.')
    world.say(
        f"Then the crowd clapped. {hero.id} bowed instead of stopping, "
        f"and ignored the foreshadowing hidden in the sleepy room."
    )
    world.para()

    world.say(f"The bad ending arrived with a wobble: {case.bad_turn}.")
    food.meters["stability"] = 0.1
    food.meters["heat"] = 0.4
    world.say(f"{case.consequence.capitalize()}.")
    world.say(
        rng.choice([
            f"The crowd gasped, then one child asked whether the ceiling chicken needed a fork.",
            f"Auntie Bea brought a mop, while the paper chef hat collapsed like a sad pancake.",
            f"The applause stopped. Even the cat looked disappointed, which was unusually harsh.",
            f"For one long second, everyone stared. Then the spaghetti made a tiny wet plop.",
        ])
    )
    world.say(
        f"{helper.id} did not laugh at {hero.id}. "
        f'"Bad endings can still teach us where the careful path was," {helper.id} said.'
    )
    world.say(
        f"{hero.id} took a deep breath. " 
        f'"I was proud and sleepy. I should have listened before the mess happened."'
    )
    world.say(f'"Now you know," {helper.id} replied. "Let us fix what we can."')
    world.para()

    world.say(f"Together, they {case.repair}.")
    food.meters["stability"] = 0.9
    hero.memes["pride"] = 0.3
    hero.memes["drowse"] = 0.0
    hero.meters["careful_actions"] = 3
    world.say(
        f"The repaired spaghetti received {TOPPINGS[params.topping]}, "
        f"and nobody asked for a performance."
    )
    world.say(f"{hero.id} wrote the lesson on the kitchen board: {case.lesson}.")
    world.say(f"At last, {case.ending}.")
    world.facts.update(
        warning=case.warning,
        temptation=case.temptation,
        consequence=case.consequence,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a funny child-facing story about {facts['hero'].id} making spaghetti while drowse and pride cause trouble.",
        f"Include foreshadowing through this warning: {facts['warning']}",
        f"Give the story a bad ending caused by ignored advice, then show how {facts['hero'].id} repairs the spaghetti and learns that {facts['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    return [
        QAItem(
            question=f"What was {hero} preparing in {f['scene'].place}?",
            answer=f"{hero} was preparing {f['food'].type}, a spaghetti meal with {PASTAS[next(k for k, v in PASTAS.items() if v == f['food'].type)] if f['food'].type in PASTAS.values() else 'toppings'}.",
        ),
        QAItem(
            question=f"What warning did {helper} give {hero} before the trouble?",
            answer=f"{helper} warned that {f['warning']}. The warning mattered because {MISHAPS[next(k for k, v in MISHAPS.items() if v == MISHAPS.get(world.params.mishap, ''))] if False else 'the kitchen contained a specific danger linked to the mishap'}",
        ),
        QAItem(
            question=f"How did drowse and pride affect {hero}'s decision?",
            answer=f"{hero} became sleepy but still wanted {f['temptation']}. Pride pushed {hero} to perform instead of stopping and listening.",
        ),
        QAItem(
            question="What caused the bad ending?",
            answer=f"The bad ending happened because {hero} ignored the warning and continued while drowse was making careful work difficult. Then {f['consequence']}.",
        ),
        QAItem(
            question=f"How did {hero} respond after the spaghetti disaster?",
            answer=f"{hero} admitted being proud and sleepy, then worked with {helper} to {f['repair']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is foreshadowing useful in a funny story?",
            answer="Foreshadowing gives an earlier warning or detail that hints at what may happen later, so the reader can enjoy seeing the clue become important.",
        ),
        QAItem(
            question="Why should someone stop cooking when they are very drowsy?",
            answer="Drowsiness makes it harder to notice heat, spills, and unstable objects. Stopping and asking for help can prevent a dangerous mess.",
        ),
        QAItem(
            question="What is a healthy way to handle pride after a mistake?",
            answer="A person can admit the mistake, listen to helpful advice, repair the damage, and use the lesson next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  warning={world.facts['warning']}")
    lines.append(f"  consequence={world.facts['consequence']}")
    return "\n".join(lines)


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="community kitchen",
        pasta="long spaghetti",
        name="Luna",
        helper="Auntie Bea",
        topping="cheese",
        mishap="sneeze",
        route="warning_first",
        seed=641,
    ),
    StoryParams(
        place="school hall",
        pasta="twisty spaghetti",
        name="Milo",
        helper="Mina",
        topping="meatballs",
        mishap="ladle",
        route="pride_first",
        seed=642,
    ),
    StoryParams(
        place="grandma's porch",
        pasta="red spaghetti",
        name="Luna",
        helper="Grandpa Sol",
        topping="peas",
        mishap="cat",
        route="quiet_first",
        seed=643,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            combos = asp_valid_combos()
        except ImportError:
            print("ASP mode requires clingo.")
            return
        print(f"{len(combos)} compatible combos:\n")
        for place, pasta in combos:
            print(f"  {place:22} {pasta}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
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
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=(
                "### curated story"
                if args.all
                else f"### variant {index + 1}" if len(samples) > 1 else ""
            ),
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
