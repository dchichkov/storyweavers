#!/usr/bin/env python3
"""A heartwarming suspense storyworld about a magical loader and a brave repair."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectItem:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Grandma"
    place: str = "the moonlit workshop"
    task: str = "carry a basket of glowing apples"
    magic: str = "a silver loader that moves things with a beam of moonlight"
    danger: str = "the loader's beam begins pulling the basket toward the dark pond"
    promise: str = "bring the apples to the village lantern feast"


@dataclass(frozen=True)
class Scenario:
    key: str
    object_label: str
    trouble: str
    clue: str
    failed_try: str
    hero_action: str
    helper_action: str
    spell: str
    solution: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Milo", "Nia", "Toby", "Iris", "Pip", "Sora", "Wren"]
HELPERS = ["Grandma", "Grandpa", "Aunt Mira", "Uncle Sol", "Dad", "Mom"]
PLACES = [
    "the moonlit workshop",
    "the little hill farm",
    "the village garden",
    "the old lantern shed",
]
TASKS = [
    "carry a basket of glowing apples",
    "lift a box of sleepy fireflies",
    "move a cart of warm bread",
    "gather jars of rainwater",
]
MAGICS = [
    "a silver loader that moves things with a beam of moonlight",
    "a brass loader whose scoop follows kind words",
    "a tiny loader powered by a star-shaped crystal",
    "a blue loader that can lift anything shared by two people",
]
PROMISES = [
    "bring the apples to the village lantern feast",
    "deliver the fireflies before the evening parade",
    "carry the bread to neighbors waiting in the square",
    "fill the garden's empty fountain before dawn",
]

SCENARIOS = [
    Scenario(
        "pond",
        "basket of glowing apples",
        "The loader's moonbeam tugged the basket toward the dark pond.",
        "The beam grew weaker whenever Luna held the control lever alone.",
        "pulling harder made the basket slide faster",
        "kept one wheel from rolling",
        "read the small star marks on the control panel",
        "By moonlight, steady hearts make a steady path.",
        "Luna held the wheel while Grandma pressed the star-shaped switch, and the loader carried the basket safely away from the pond.",
        "The apples reached the feast with every glow still shining.",
        "a frightening problem can become manageable when people share both courage and a clear job",
        "the apples glowed beside the lanterns while Luna and Grandma held hands",
    ),
    Scenario(
        "bridge",
        "box of sleepy fireflies",
        "A wooden bridge creaked as the loader rolled toward the river.",
        "A green light blinked whenever the loader's wheels touched a loose board.",
        "rushing forward made the bridge shake harder",
        "placed flat stones beneath the front wheels",
        "guided the loader from the bank with a ribbon of blue light",
        "No bright path is found by rushing past the warning.",
        "Luna set the stones while the helper guided the loader one careful wheel at a time.",
        "The fireflies arrived before the parade and twinkled like tiny stars.",
        "listening to a warning can be braver than pretending not to be afraid",
        "the fireflies floated above the repaired bridge like a warm, moving sky",
    ),
    Scenario(
        "mist",
        "cart of warm bread",
        "A silver mist swallowed the path, and the loader's scoop pointed in three directions.",
        "The right path smelled faintly of cinnamon from the bakery.",
        "choosing the biggest light sent the cart toward a thorny hedge",
        "held a lantern low to reveal the wheel tracks",
        "follow the true scent, little loader, and carry kindness home",
        "Luna found the tracks while the helper spoke the gentle spell, and the loader turned toward the bakery.",
        "The bread arrived warm enough to comfort every waiting neighbor.",
        "small clues and patient words can guide a worried heart",
        "steam curled from the bread as neighbors welcomed the brave team",
    ),
    Scenario(
        "fountain",
        "jars of rainwater",
        "The loader lifted the jars too high, and a crack opened in the fountain's stone rim.",
        "The crack stopped growing when the loader's scoop rested on the ground.",
        "lifting the jars again made pebbles tumble into the fountain",
        "lowered the scoop and blocked the loose stones",
        "Stone be still, water wait, gentle hands repair the gate",
        "Luna lowered the load while the helper packed soft moss into the crack, then they moved the jars slowly.",
        "The fountain filled before dawn, and its first splash sounded like laughter.",
        "the safest rescue often begins by stopping the motion that caused the trouble",
        "moonlight trembled in the full fountain while the loader rested quietly nearby",
    ),
]

OPENINGS = [
    "{hero} loved the quiet hour when {place} filled with silver light.",
    "Before the village woke, {hero} had one important promise to keep.",
    "The stars were still bright above {place} when {hero} checked the magical loader.",
    "Everyone trusted {hero} with small jobs, but tonight's job felt much bigger.",
]
REACTIONS = [
    '"Something is pulling too hard!" {hero} cried.',
    '"The loader is frightened," {hero} whispered.',
    '"I thought I could guide it alone," {hero} admitted.',
    '"Please do not roll into the dark," {hero} pleaded.',
]
OFFERS = [
    '"I am here. Tell me what you notice," {helper} said.',
    '"Do not fight the magic blindly. We will listen first," {helper} replied.',
    '"Give me one job, and keep one job for yourself," {helper} said.',
    '"A brave plan can still be a careful plan," {helper} reminded {hero}.',
]
DETAILS = [
    "They breathed together before touching the controls.",
    "They counted each wheel turn aloud.",
    "They tested the smallest movement before making a larger one.",
    "They kept their eyes on the clue instead of the frightening shadow.",
    "They passed the lantern back and forth so neither hand grew tired.",
]


def make_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different people")
    if not params.magic.strip():
        raise StoryError("magic description cannot be empty")
    world = World(params=params)
    hero = Person(params.hero, "hero")
    helper = Person(params.helper, "helper")
    loader = ObjectItem("loader", "magical loader", owner=params.hero)
    world.people = {hero.name: hero, helper.name: helper}
    world.items = {"loader": loader}
    world.facts.update(hero=hero, helper=helper, loader=loader, place=params.place)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENARIOS)
    p = params

    world.say(rng.choice(OPENINGS).format(hero=p.hero, place=p.place))
    world.say(f"{p.hero} climbed into {p.place} to {p.task}.")
    world.say(f"Their tool was {p.magic}. It usually hummed like a friendly bee.")
    world.say(f"Tonight, however, {p.danger}.")
    world.para()

    world.say(scene.trouble)
    world.say(rng.choice(REACTIONS).format(hero=p.hero))
    world.say(f"At first, {p.hero} tried alone, but {scene.failed_try}.")
    world.say(f"Then {p.hero} noticed something important: {scene.clue}")
    world.para()

    world.say(rng.choice(OFFERS).format(hero=p.hero, helper=p.helper))
    world.say(f"{p.hero} {scene.hero_action}, while {p.helper} {scene.helper_action}.")
    world.say(f"Together they whispered, '{scene.spell}'")
    world.say(scene.solution)
    world.say(rng.choice(DETAILS))
    world.para()

    world.say(scene.result)
    world.say(f"{p.helper} smiled. 'You kept your promise because you let someone help you,' {p.helper} said.")
    world.say(f"{p.hero} nodded. 'And the loader listened when we listened first.'")
    world.say(f"The lesson stayed with them: {scene.lesson}.")
    world.say(f"At the end of the night, {scene.ending}.")

    world.people[p.hero].memes.update(fear=0.2, courage=1.0, trust=1.0)
    world.people[p.helper].memes.update(care=1.0, patience=1.0)
    world.items["loader"].meters.update(safe=1.0, useful=1.0)
    world.facts.update(
        scenario=scene.key,
        object_label=scene.object_label,
        trouble=scene.trouble,
        clue=scene.clue,
        failed_try=scene.failed_try,
        hero_action=scene.hero_action,
        helper_action=scene.helper_action,
        spell=scene.spell,
        solution=scene.solution,
        result=scene.result,
        lesson=scene.lesson,
        ending=scene.ending,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a heartwarming suspense story about {p.hero} using a magical loader at {p.place}.",
        f"Tell a child-friendly tale where {p.hero} and {p.helper} solve a loader problem with magic and dialogue.",
        f"Create a gentle story about keeping this promise: {p.promise}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    trouble = str(f["trouble"])
    clue = str(f["clue"])
    result = str(f["result"])
    return [
        QAItem(
            f"What danger did the magical loader create?",
            f"The danger was that {trouble[0].lower() + trouble[1:]} This made {f['object_label']} unsafe.",
        ),
        QAItem(
            "What clue helped the characters choose a safer plan?",
            f"They noticed that {clue[0].lower() + clue[1:]} The clue showed them how to use the loader carefully.",
        ),
        QAItem(
            "How did the hero and helper divide the work?",
            f"{p.hero} {f['hero_action']}, while {p.helper} {f['helper_action']}. Their separate jobs made the repair possible.",
        ),
        QAItem(
            "What did the dialogue change?",
            f"{p.helper}'s words helped {p.hero} stop working alone and choose a shared plan. Their spoken spell and instructions changed what they did next.",
        ),
        QAItem(
            "How do we know the problem was solved?",
            f"{result} The final image was that {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is suspense?",
            "Suspense is the feeling of waiting to learn what will happen while a problem or danger is still unresolved.",
        ),
        QAItem(
            "What is magic in a story?",
            "Magic is an imaginative power or rule that makes unusual events possible. Good magical stories still show characters making choices and solving problems.",
        ),
        QAItem(
            "Why can dialogue help solve a problem?",
            "Dialogue lets characters share observations, ask for help, and change their plans. In a strong story, spoken words lead to a meaningful action.",
        ),
        QAItem(
            "Why is a loader useful?",
            "A loader can lift, carry, or move materials. In this world, the loader is magical, but it still needs careful guidance and teamwork.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
loader(L) :- loader_name(L).
magic_loader(L) :- loader(L), magical(L).
safe_rescue(H,K,L) :- hero(H), helper(K), magic_loader(L), shared_guidance(H,K,L), resolved.
heartwarming_story(H,K,L) :- safe_rescue(H,K,L).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("helper_name", p.helper),
            asp.fact("loader_name", "loader"),
            asp.fact("magical", "loader"),
            asp.fact("shared_guidance", p.hero, p.helper, "loader"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "#show heartwarming_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    atoms = asp.atoms(symbols, "heartwarming_story")
    if not atoms:
        print("MISMATCH: ASP story atom missing.")
        return 1
    sample = generate(StoryParams(seed=17))
    required = ["loader", "magic", "said", "help"]
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print("MISMATCH: generated story missing " + ", ".join(missing))
        return 1
    print("OK: ASP and Python agree on a resolved magical loader story.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--magic", choices=MAGICS)
    parser.add_argument("--promise", choices=PROMISES)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(NAMES),
        helper=args.helper or rng.choice([x for x in HELPERS if x != args.hero]),
        place=args.place or rng.choice(PLACES),
        task=args.task or rng.choice(TASKS),
        magic=args.magic or rng.choice(MAGICS),
        promise=args.promise or rng.choice(PROMISES),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(
            "\n--- trace ---"
            f"\nhero={sample.world.params.hero}"
            f"\nhelper={sample.world.params.helper}"
            f"\nscenario={sample.world.facts['scenario']}"
            f"\nclue={sample.world.facts['clue']}"
            f"\nloader_safe={sample.world.items['loader'].meters['safe']}"
            f"\nresolved={sample.world.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program())
        print("1 compatible magical loader rescue." if asp.atoms(models, "heartwarming_story") else "0 compatible stories.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, scenario in enumerate(SCENARIOS):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("number of stories must be at least 1")
        for i in range(args.n):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
