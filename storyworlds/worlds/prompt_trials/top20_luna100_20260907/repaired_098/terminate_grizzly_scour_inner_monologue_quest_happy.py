#!/usr/bin/env python3
"""A child-facing superhero quest about Grizzly, a brave search, and a happy ending."""

from __future__ import annotations

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
class Hero:
    name: str
    species: str
    power: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Quest:
    object_name: str
    danger: str
    clue: str
    cause: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    city_name: str = "Brightwood"
    hero_name: str = "Luna"
    hero_species: str = "bear"
    grizzly_name: str = "Grizzly"
    quest: str = "lost_signal"
    route: str = "signal_first"


@dataclass(frozen=True)
class QuestCase:
    object_name: str
    danger: str
    first_action: str
    failed_reason: str
    clue: str
    cause: str
    brave_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    city: Place
    luna: Hero
    grizzly: Hero
    quest: Quest
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CITIES = {
    "Brightwood": Place("Brightwood", "city"),
    "Moon Harbor": Place("Moon Harbor", "city"),
    "Starfall Village": Place("Starfall Village", "village"),
}

HEROES = [
    ("Luna", "bear", "moonlight vision"),
    ("Luna", "fox", "silver-speed"),
    ("Luna", "rabbit", "echo hearing"),
]

GRIZZLIES = [
    ("Grizzly", "grizzly", "super strength"),
    ("Grizzly", "grizzly", "warm mountain roar"),
    ("Grizzly", "grizzly", "stone-steady courage"),
]

CASES = {
    "lost_signal": QuestCase(
        "the rescue beacon",
        "the river bridge would stay dark during the evening crossing",
        "climb the tower and search the beacon from the outside",
        "the tower door was locked and the roof was too slippery to reach safely",
        "a line of blue dust led from the beacon box toward the old clock",
        "a loose clock spring had pulled the beacon's power wire through a wall slot",
        "stay on the ground, scour the safe rooms, and ask Grizzly to lift the covered inspection panel",
        "rewire the beacon, secure the spring, and test its bright signal across the river",
        "a hero uses courage with care instead of turning danger into a stunt",
        "the rescue beacon painted a golden path over the bridge while Luna and Grizzly cheered",
    ),
    "sleeping_alarm": QuestCase(
        "the city alarm",
        "people might miss a warning about a storm",
        "press every alarm button at once",
        "the noise could frighten the city and would not reveal which part had failed",
        "a tiny feather trembled beside the quietest alarm bell",
        "a pigeon feather had jammed the bell's striker after a gust blew it through the vent",
        "listen at a distance and let Grizzly guard the street while the alarm was opened",
        "remove the feather, oil the striker, and test one gentle ring before the storm",
        "careful listening can be stronger than a loud first move",
        "the alarm rang clearly, and every window in the city glowed with safe storm lights",
    ),
    "vanished_map": QuestCase(
        "the moon map",
        "the rescue team would not know which mountain trail to use",
        "scour every shelf by tossing the papers into piles",
        "the map could tear, and a messy search would hide the important clues",
        "silver crumbs curved beneath a rolling supply cart",
        "the cart had rolled over the map and wrapped it around one wheel",
        "stop the cart, block its wheels, and use moonlight to inspect the floor",
        "unroll the map, mend its edge, and place it in a labeled case",
        "a calm search protects the very thing a hero hopes to find",
        "the moon map shimmered in its case as the team chose a safe trail home",
    ),
    "frozen_gate": QuestCase(
        "the shelter gate",
        "families could be stranded outside when the cold night came",
        "strike the gate with a heavy hammer",
        "the blow might damage the lock and leave no way to close the gate later",
        "a warm red thread showed where a scarf was caught in the hinge",
        "a gust had pulled a visitor's scarf into the hinge and stopped the gate",
        "keep everyone back and ask Grizzly to hold the gate while Luna freed the cloth",
        "remove the scarf, warm the hinge, and check that the gate closed twice",
        "protecting people includes preventing a second problem during a repair",
        "the shelter gate clicked shut, and warm soup waited for every family inside",
    ),
    "dark_rooftop": QuestCase(
        "the rooftop garden lamp",
        "the garden's food beds might freeze without their night warmth",
        "race across the dark roof to replace the lamp",
        "the wet roof could make a quick rescue into a fall",
        "a bright reflection blinked from a puddle below the safe stair",
        "the lamp was fine; a fallen mirror was sending its beam away from the garden",
        "follow the lit stair, never the tempting dark roof, and ask Grizzly to watch the edge",
        "move the mirror, anchor it, and aim the lamp back at the garden beds",
        "the safest path can uncover a surprising answer",
        "green leaves glowed beneath the repaired lamp while the city slept warmly",
    ),
}

ROUTES = (
    "signal_first",
    "dialogue_first",
    "inner_thought_first",
    "quest_first",
    "city_first",
    "clue_first",
)


ASP_RULES = r"""
hero(luna).
hero(grizzly).
quest(Q) :- case(Q).
safe_action(luna).
solved(Q) :- quest(Q), safe_action(luna), cause(Q).
happy_ending(Q) :- solved(Q).
valid_story(Q) :- hero(luna), hero(grizzly), quest(Q), happy_ending(Q).
"""


def case_id(name: str) -> str:
    return "case_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", "luna"), asp.fact("hero", "grizzly"), asp.fact("safe_action", "luna")]
    for name, case in CASES.items():
        cid = case_id(name)
        lines.extend([
            asp.fact("case", cid),
            asp.fact("cause", cid),
        ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    found = set(asp.atoms(model, "happy_ending"))
    expected = {(case_id(name),) for name in CASES}
    if found == expected:
        print(f"OK: clingo gate matches python reasoning ({len(expected)} quests).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.city_name, params.hero_name, params.hero_species,
        params.grizzly_name, params.quest, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.city_name not in CITIES:
        raise StoryError(f"Unknown city: {params.city_name}")
    if params.quest not in CASES:
        raise StoryError(f"Unknown quest: {params.quest}")
    if not params.hero_name.strip():
        raise StoryError("Hero name cannot be empty.")
    city = CITIES[params.city_name]
    return World(
        city=Place(city.name, city.kind),
        luna=Hero(params.hero_name, params.hero_species, "moonlight vision"),
        grizzly=Hero(params.grizzly_name, "grizzly", "super strength"),
        quest=Quest(CASES[params.quest].object_name, CASES[params.quest].danger, CASES[params.quest].clue),
    )


def tell_story(world: World, params: StoryParams) -> None:
    luna, grizzly, city, quest = world.luna, world.grizzly, world.city, world.quest
    case = CASES[params.quest]
    rng = story_rng(params)

    luna.memes.update(curiosity=1, courage=0)
    grizzly.memes.update(strength=1, kindness=1)

    openings = {
        "signal_first": f"At sunrise in {city.name}, {luna.name} the {luna.species} superhero heard that {case.object_name} had vanished from its proper work.",
        "dialogue_first": f'"A hero call!" cried {luna.name} in {city.name}. {case.object_name.capitalize()} had stopped working, and the city needed help.',
        "inner_thought_first": f"{luna.name} looked over {city.name}. *I may feel worried, but I can think before I leap,* the superhero told themself when {case.object_name} failed.",
        "quest_first": f"The quest began when {luna.name} discovered that {case.object_name} was not doing its job in {city.name}.",
        "city_first": f"The people of {city.name} loved their bright streets, but that morning {case.object_name} had gone quiet.",
        "clue_first": f"A strange clue appeared near {case.object_name} in {city.name}. It was the first sign that a careful superhero quest had begun.",
    }
    world.say(openings[params.route])
    world.say(f"The trouble mattered because {case.danger}.")
    world.say(f'"Do we rush in?" {grizzly.name} asked. "No," said {luna.name}. "We will scour the safe places first and learn what changed."')

    world.para()
    world.say(f"{luna.name} thought, *A superhero is not someone who never feels afraid. A superhero chooses a useful next step.*")
    world.say(f"First, Luna would {case.first_action}.")
    world.say(f"That plan failed because {case.failed_reason}.")
    world.say(f'"Then the danger is part of the clue," {grizzly.name} said. "Exactly," {luna.name} answered. "We need another path."')
    world.say(f"Together they noticed that {case.clue}.")
    world.say(f"The clue explained everything: {case.cause}.")

    world.para()
    world.say(f"{luna.name} felt a flutter of fear, but chose to {case.brave_action}.")
    luna.memes["courage"] = 1
    luna.meters["safe_steps"] = 3
    world.say(f"Grizzly used {grizzly.power} only where it was safe, and together they {case.repair}.")
    quest.solved = True
    grizzly.memes["pride"] = 1
    city.meters["people_protected"] = 1

    world.para()
    world.say(f"{luna.name} thought, *The quest was not about looking powerful. It was about helping everyone get home safely.*")
    world.say(f'"We did it by checking instead of guessing," {grizzly.name} said. "And by helping each other," {luna.name} replied.')
    world.say(f"At last, {case.ending}.")

    world.facts.update(
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a superhero quest about {world.luna.name} and {world.grizzly.name} solving a problem with {world.quest.object_name}.",
        f"Include an inner monologue in which {world.luna.name} chooses a safe action after learning that {case.cause}.",
        f"End happily with this image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What problem did {world.luna.name} investigate in {world.city.name}?",
            answer=f"{world.luna.name} investigated why {world.quest.object_name} had stopped working. It mattered because {case.danger}.",
        ),
        QAItem(
            question=f"Why did the first plan fail?",
            answer=f"The first plan was to {case.first_action}. It failed because {case.failed_reason}.",
        ),
        QAItem(
            question="What clue revealed the real cause?",
            answer=f"They discovered that {case.clue}. This showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did Luna show superhero courage?",
            answer=f"{world.luna.name} chose to {case.brave_action}, which kept the rescue careful and safe.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"They {case.repair}. Then {case.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to scour a place?",
            answer="To scour a place means to search it carefully and thoroughly.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a helper who uses special abilities, courage, and good judgment to protect others.",
        ),
        QAItem(
            question="Why should a hero avoid an unsafe shortcut?",
            answer="An unsafe shortcut can create a second danger. A careful hero protects people while solving the first problem.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought, shown so readers can understand what the character feels or decides.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest about Luna, Grizzly, and a happy rescue.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--city", choices=sorted(CITIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--grizzly-name")
    ap.add_argument("--quest", choices=sorted(CASES))
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    city_name = args.city or rng.choice(sorted(CITIES))
    hero_name, hero_species, _ = rng.choice(HEROES)
    grizzly_name, _, _ = rng.choice(GRIZZLIES)
    return StoryParams(
        seed=args.seed,
        city_name=city_name,
        hero_name=args.hero_name or hero_name,
        hero_species=hero_species,
        grizzly_name=args.grizzly_name or grizzly_name,
        quest=args.quest or rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world trace ---",
        f"{world.city.name}: meters={world.city.meters}",
        f"{world.luna.name}: meters={world.luna.meters} memes={world.luna.memes}",
        f"{world.grizzly.name}: meters={world.grizzly.meters} memes={world.grizzly.memes}",
        f"quest: object={world.quest.object_name!r} solved={world.quest.solved} cause={world.facts['cause']!r}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/1."))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
