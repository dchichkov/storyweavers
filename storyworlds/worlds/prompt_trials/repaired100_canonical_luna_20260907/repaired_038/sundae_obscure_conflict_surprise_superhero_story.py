#!/usr/bin/env python3
"""
A small superhero storyworld about an obscure sundae mystery.

Luna discovers that the town's festival sundae has vanished into a shadowy
corner. A conflict over how to help becomes a surprise rescue when Luna learns
that the "villain" is a shy little cloud creature hiding under the dessert cart.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Sundae:
    id: str
    flavor: str
    topping: str
    clue: str
    effect: str


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    conflict: str
    surprise: str
    danger: str
    clue: str
    action: str
    ending: str


@dataclass
class StoryParams:
    sundae: str
    name: str
    hero_title: str
    helper: str
    scenario: str
    opening: int
    dialogue: int
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SUNDAES = {
    "moonberry": Sundae(
        "moonberry",
        "moonberry",
        "silver sugar stars",
        "a cool blue spoon mark on the cart",
        "shines softly when someone tells the truth",
    ),
    "comet_caramel": Sundae(
        "comet_caramel",
        "caramel",
        "crunchy comet crumbs",
        "a warm caramel streak beside the wheel",
        "leaves a sparkling trail when carried carefully",
    ),
    "rainbow_peach": Sundae(
        "rainbow_peach",
        "peach",
        "rainbow sprinkles",
        "three bright sprinkles near the fountain",
        "changes color when friends cooperate",
    ),
    "chocolate_cloud": Sundae(
        "chocolate_cloud",
        "chocolate",
        "fluffy cocoa clouds",
        "a soft brown puff caught on a banner",
        "floats for a moment when lifted gently",
    ),
}

SCENARIOS = {
    "vanished_cart": Scenario(
        "vanished_cart",
        "At the town's bright summer fair, Luna arrived just as the famous sundae cart disappeared behind an obscure alley curtain.",
        "Luna wanted to chase the cart's squeaky wheel, but her helper wanted to guard the frightened crowd first.",
        "The missing cart was not stolen at all: a tiny cloud creature had pulled it beneath the stage because the festival music scared it.",
        "The cart was rolling toward a steep ramp, and the melting sundae could spill onto the people below.",
        "a line of tiny sprinkles leading away from the crowd",
        "Luna followed the sprinkles quietly, lowered her superhero cape, and asked the hidden creature what it needed.",
        "The sundae returned to the festival table, while the little cloud watched from a safe, sunny step.",
    ),
    "shadow_topping",
        "During the hero picnic, an obscure black shadow curled around the festival sundae and hid its bright topping.",
        "Luna thought her super-speed could sweep the shadow away, but her helper warned that rushing might scatter it across every plate.",
        "The shadow was a lost patch of night looking for the moon-shaped button on Luna's cape.",
        "The shadow grew wider and covered the picnic path.",
        "the button-shaped gap on Luna's cape",
        "Luna stood still, showed the matching button, and invited the shadow to follow her slowly.",
        "The shadow folded into a small bow beneath the cape button, and the sundae gleamed again.",
    ),
    "fountain_freeze",
        "At the fountain fair, the special sundae froze in midair above an obscure stone basin.",
        "Luna reached up with her strength, while her helper noticed that the ice grew whenever anyone shouted.",
        "The frozen sundae was being protected by a shy frost sprite that believed loud voices meant danger.",
        "A crack spread through the basin as the ice grew heavier.",
        "the ice became thinner whenever the crowd whispered",
        "Luna asked everyone to whisper, then used a warm beam from her wrist badge to guide the sundae down.",
        "The frost sprite warmed beside the cup, and the sundae landed safely on a quiet tray.",
    ),
    "mystery_signal",
        "A strange signal made the fair's sundae bells ring from an obscure rooftop.",
        "Luna wanted to fly straight up, but her helper said the signal might be a call for help rather than a threat.",
        "The signal came from a tiny robot that had copied the bell sound while trying to announce that the sundae freezer was unplugged.",
        "Without the freezer, every dessert would melt before the children arrived.",
        "three short rings followed by one long ring",
        "Luna answered with the same rhythm, found the robot, and helped it reconnect the freezer.",
        "The bells played a cheerful tune, and the cold sundae waited under a bright silver lid.",
    ),
}

OPENINGS = [
    "On a warm afternoon",
    "Before the festival parade",
    "As golden flags fluttered",
    "Just after the town band began",
    "While the fairground lights blinked",
]

DIALOGUES = [
    (
        '"We should hurry!" Luna cried. '
        '"We should listen first," said {helper}. '
        'Luna looked at the clue and nodded. "Then we listen while we move carefully."'
    ),
    (
        '"That sounds like a villain," Luna said. '
        '"Or someone who is scared," replied {helper}. '
        'Luna lowered her fists. "I will ask before I act."'
    ),
    (
        '"My powers can fix this," Luna said. '
        '"Your questions can help us know how," said {helper}. '
        'Luna smiled. "Questions first, powers second."'
    ),
    (
        '"The mystery is getting bigger," Luna whispered. '
        '"Then we need a smaller, calmer step," said {helper}. '
        'Luna took that step and saw the hidden clue.'
    ),
]

NAMES = ["Luna", "Nova", "Milo", "Zara", "Theo", "Pip"]
HERO_TITLES = ["Star Guardian", "Bright Bolt", "Moon Shield", "Kindness Captain"]
HELPERS = ["Mara", "Jules", "Ravi", "Tess", "Ari"]


def set_meter(entity: Entity, name: str, value: float) -> None:
    entity.meters[name] = value


def add_meme(entity: Entity, name: str, amount: float) -> None:
    entity.memes[name] = entity.memes.get(name, 0.0) + amount


def tell(params: StoryParams) -> World:
    sundae = SUNDAES[params.sundae]
    scenario = SCENARIOS[params.scenario]
    world = World()

    hero = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity(params.helper, "character", params.helper))
    dessert = world.add(Entity("festival_sundae", "food", f"{sundae.flavor} sundae"))
    mystery = world.add(Entity("hidden_friend", "creature", "hidden friend"))

    world.facts.update(
        hero=hero,
        helper=helper,
        dessert=dessert,
        mystery=mystery,
        sundae=sundae,
        scenario=scenario,
        title=params.hero_title,
    )

    world.say(
        f"{OPENINGS[params.opening % len(OPENINGS)]}, {params.name}, the "
        f"{params.hero_title}, flew over the fairground with {params.helper}."
    )
    world.say(
        f"At the center of the fair stood a {sundae.flavor} sundae covered with "
        f"{sundae.topping}. It was the festival's grand prize."
    )
    world.say(scenario.opening)
    world.para()

    set_meter(hero, "courage", 1.0)
    set_meter(helper, "patience", 1.0)
    set_meter(dessert, "safety", 0.5)
    add_meme(hero, "curiosity", 1.0)
    add_meme(helper, "trust", 1.0)

    world.say(scenario.conflict)
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(helper=params.helper))
    world.say(scenario.danger)
    world.say(f"Then they noticed {scenario.clue}.")
    world.fired.add("clue_found")
    add_meme(hero, "worry", 1.0)

    world.say(
        f"{params.name} followed the clue instead of charging ahead. "
        f"{scenario.surprise}"
    )
    world.fired.add("surprise_revealed")
    set_meter(mystery, "fear", 0.5)
    add_meme(mystery, "relief", 1.0)

    world.para()
    world.say(
        f'"You do not have to hide," {params.name} said. '
        f'"Can we help?" {params.helper} asked.'
    )
    world.say(
        f"The little friend answered with a tiny nod. {params.name} "
        f"{scenario.action}."
    )
    world.fired.add("careful_action")
    set_meter(hero, "courage", 2.0)
    set_meter(dessert, "safety", 1.0)
    add_meme(hero, "confidence", 1.0)
    add_meme(hero, "kindness", 1.0)

    world.say(scenario.ending)
    world.say(
        f"The {sundae.flavor} sundae was safe because {params.name} used a "
        "superhero's best power: noticing what others needed before making a move."
    )
    world.facts["resolved"] = True
    world.facts["conflict_resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, cid) for sid in sorted(SCENARIOS) for cid in sorted(SUNDAES)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sundae and args.scenario and (args.scenario, args.sundae) not in valid_combos():
        raise StoryError("That sundae and scenario do not form a valid superhero mystery.")

    scenario = args.scenario or rng.choice(sorted(SCENARIOS))
    sundae = args.sundae or rng.choice(sorted(SUNDAES))
    return StoryParams(
        sundae=sundae,
        name=args.name or rng.choice(NAMES),
        hero_title=args.hero_title or rng.choice(HERO_TITLES),
        helper=args.helper or rng.choice(HELPERS),
        scenario=scenario,
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Scenario = f["scenario"]
    sundae: Sundae = f["sundae"]
    return [
        f"Write a superhero story about an obscure mystery involving a {sundae.flavor} sundae.",
        f"Tell a child-friendly conflict-and-surprise story where {f['hero'].id} protects a festival sundae.",
        f"Write a story in which a superhero solves a sundae problem by noticing a clue and listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario: Scenario = f["scenario"]
    sundae: Sundae = f["sundae"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What was special about the {sundae.flavor} sundae?",
            answer=f"It was the festival's grand prize, covered with {sundae.topping}.",
        ),
        QAItem(
            question=f"What conflict did {hero.id} and {helper.id} face?",
            answer=f"They had to protect the sundae from danger while deciding whether to rush in or first understand the obscure clue.",
        ),
        QAItem(
            question="What surprising truth did the heroes discover?",
            answer=scenario.surprise,
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=scenario.clue,
        ),
        QAItem(
            question=f"How did {hero.id} help?",
            answer=f"{hero.id} followed the clue, listened calmly, and {scenario.action}.",
        ),
        QAItem(
            question="How did the ending prove that the problem was solved?",
            answer=scenario.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sundae?",
            answer="A sundae is a dessert made from ice cream with toppings such as fruit, sauce, nuts, candy, or sprinkles.",
        ),
        QAItem(
            question="What does obscure mean?",
            answer="Obscure means difficult to notice, understand, or find because it is hidden, unfamiliar, or not well known.",
        ),
        QAItem(
            question="What makes a superhero helpful?",
            answer="A helpful superhero protects people, pays attention to clues, asks questions, and uses power carefully instead of causing more harm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sundae(X) :- dessert(X).
hero(X) :- character(X).
mystery(X) :- creature(X).
safe_story(S, C) :- scenario(S), sundae_choice(C), conflict, surprise.
resolved_story(S, C) :- safe_story(S, C), careful_action, resolved.
"""


def asp_facts() -> str:
    import asp

    lines = ["conflict.", "surprise.", "careful_action.", "resolved."]
    for sid in SCENARIOS:
        lines.append(asp.fact("scenario", sid))
    for cid in SUNDAES:
        lines.append(asp.fact("sundae_choice", cid))
    lines.append(asp.fact("dessert", "festival_sundae"))
    lines.append(asp.fact("character", "hero"))
    lines.append(asp.fact("creature", "hidden_friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show safe_story/2."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: ASP gate matches Python combinations ({len(expected)} combos).")
        return 0
    print("ASP/Python mismatch.")
    print("Only in Python:", sorted(expected - actual))
    print("Only in ASP:", sorted(actual - expected))
    return 1


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a child-facing superhero sundae mystery."
    )
    parser.add_argument("--sundae", choices=SUNDAES)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--name")
    parser.add_argument("--hero-title", choices=HERO_TITLES)
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


CURATED = [
    StoryParams("moonberry", "Luna", "Star Guardian", "Mara", "vanished_cart", 0, 0),
    StoryParams("comet_caramel", "Nova", "Bright Bolt", "Jules", "shadow_topping", 1, 1),
    StoryParams("rainbow_peach", "Milo", "Moon Shield", "Ravi", "fountain_freeze", 2, 2),
    StoryParams("chocolate_cloud", "Zara", "Kindness Captain", "Tess", "mystery_signal", 3, 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show safe_story/2."))
        print(sorted(set(asp.atoms(model, "safe_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
