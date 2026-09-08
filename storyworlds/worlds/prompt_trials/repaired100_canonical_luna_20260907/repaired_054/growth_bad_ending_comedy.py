#!/usr/bin/env python3
"""A child-friendly comedy StoryWorld about growth and a bad ending."""

from __future__ import annotations

import argparse
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the sunny community garden"
    first_name: str = "Luna"
    second_name: str = "Bram"
    plant: str = "a bean sprout"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    beginning: str
    trouble: str
    clue: str
    plan: str
    jobs: tuple[str, str]
    result: str
    bad_ending: str
    lesson: str
    image: str


SETTINGS = [
    "the sunny community garden",
    "the school windowsill",
    "the little rooftop greenhouse",
    "the picnic table garden",
]
NAMES = ["Luna", "Bram", "Milo", "Tessa", "Nia", "Otis", "Pip", "Zara"]
PLANTS = ["a bean sprout", "a tomato seedling", "a sunflower shoot", "a tiny pumpkin vine"]

SCENARIOS = [
    Scenario(
        "tall-hat-sprout",
        "They planted a bean and promised to measure its growth every morning.",
        "By noon, the sprout had grown so tall that it wore the watering can like a hat.",
        "A leaf poked through the can's handle and made the whole plant lean sideways.",
        "support the stem with a pencil and water it with a small cup",
        ("held the pencil beside the stem", "carried the small cup very carefully"),
        "The sprout stood straight, although the watering can stayed stuck like a shiny hat.",
        "They pulled too hard, and the can popped free, splashing both children and sending the plant label into a puddle.",
        "growth needs patient care, not a grand tug",
        "the sprout wore one muddy leaf like a bow tie while the children giggled",
    ),
    Scenario(
        "runaway-vine",
        "They planted a pumpkin seed and drew a chart for every new curl.",
        "The vine grew across the table and wrapped around Bram's lunchbox.",
        "Its newest tendril was soft enough to guide without pulling.",
        "unwind the vine slowly and give it a little trellis",
        ("lifted each curl from the lunchbox", "placed sticks in a triangle for support"),
        "The vine reached the trellis and produced one brave yellow flower.",
        "They celebrated too soon, and the vine wrapped around the celebration cake before anyone could eat it.",
        "growing things need room and gentle boundaries",
        "a yellow flower peeked from a cake-shaped vine loop",
    ),
    Scenario(
        "sunflower-sneeze",
        "They watched a sunflower shoot stretch toward the brightest window.",
        "It grew so fast that its fuzzy top brushed Luna's nose.",
        "The plant bent toward light but sprang back when the pot was turned.",
        "rotate the pot each day and leave space above the leaves",
        ("marked the pot with a sun sticker", "moved the chair away from the growing top"),
        "The sunflower stood tall without tickling anyone's nose.",
        "Luna sneezed during the final measurement and knocked the ruler into the watering dish.",
        "growth can be surprising, so careful space matters",
        "the ruler floated in the dish while the sunflower nodded politely",
    ),
    Scenario(
        "measuring-monster",
        "They made a paper ruler to celebrate every new centimeter.",
        "The plant grew beyond the ruler, then beyond the table, then beyond Bram's best guess.",
        "A trail of leaves showed exactly where the stem had reached.",
        "extend the ruler with paper strips and record the growth honestly",
        ("taped three strips into one long ruler", "counted the leaves and wrote down the new height"),
        "Their record showed the plant had grown farther than either child expected.",
        "The paper ruler grew too, until it became a scarf that wrapped around the garden sign.",
        "honest measuring helps us understand real growth",
        "the ruler-scarf fluttered beside a plant that was taller than the sign",
    ),
    Scenario(
        "watering-whistle",
        "They gave a little tomato seedling a morning drink.",
        "The seedling grew so quickly that its leaves blocked the watering can's whistle.",
        "Only dry soil needed water; the shiny leaves did not.",
        "check the soil before watering and keep the whistle clear",
        ("touched the soil to test its dryness", "moved the leaves gently from the spout"),
        "The seedling received just enough water, and the whistle sang again.",
        "They blew the whistle to celebrate and scared a pigeon into the tomato bed.",
        "growth improves when care is thoughtful rather than automatic",
        "the pigeon strutted away beneath a tomato leaf wearing a droplet like a hat",
    ),
    Scenario(
        "rooty-riddle",
        "They wondered whether the plant's roots grew as much as its leaves.",
        "When they peeked under the pot, a root had escaped and curled around a shoe.",
        "The root was firm but flexible, like a tiny brown rope.",
        "return the root to the soil and add a wider pot",
        ("loosened the soil around the root", "held the wider pot steady"),
        "The plant settled into its new home and lifted two fresh leaves.",
        "The escaped root was tickled by the shoe, and the pot rolled downhill before they caught it.",
        "growth below the soil deserves care too",
        "the wider pot rested safely while one root still pointed toward the shoe",
    ),
    Scenario(
        "leafy-applause",
        "They clapped whenever a new leaf opened.",
        "Their loud applause shook loose three leaves before they had finished clapping.",
        "The leaves opened more calmly when the children used quiet fingers.",
        "whisper congratulations and make a soft paper sign",
        ("folded a sign that said 'Grow gently'", "held it beside the newest leaf"),
        "The next leaf opened in peace, and both children whispered their loudest cheers.",
        "Then Bram sneezed, and the paper sign flew into a bucket of compost.",
        "growth can be celebrated without making a growing thing struggle",
        "the compost bucket wore the sign like a very serious hat",
    ),
    Scenario(
        "compost-crown",
        "They mixed compost into the soil to help a sunflower shoot grow.",
        "A clump of compost landed on the shoot and made it look like a crowned king.",
        "The crown slid away when they misted it lightly.",
        "brush the soil off gently and add compost around, not on, the stem",
        ("held the stem upright", "misted the compost until it slipped away"),
        "The shoot stood clean and strong in rich soil.",
        "The crown landed on Otis's head when he leaned over the pot, and everyone bowed to him.",
        "helpful food for soil must still be placed with care",
        "the sunflower stood beside a compost king who wore a leaf for a medal",
    ),
    Scenario(
        "shadow-growth",
        "They marked the plant's shadow each afternoon to watch its changing height.",
        "The shadow grew longer and covered the lunch basket.",
        "The plant had not grown sideways; the sun had moved across the sky.",
        "measure the plant itself and use the shadow only as a clue",
        ("held the ruler against the stem", "moved the lunch basket out of the shadow"),
        "They learned the plant was taller, but not as enormous as its shadow.",
        "They packed the basket in the shadow and discovered the sandwiches were now mysteriously warm.",
        "good observers compare clues before deciding what changed",
        "the long shadow pointed at a basket full of warm sandwiches",
    ),
    Scenario(
        "seedling-parade",
        "They lined up three seedlings and gave each one a tiny flag.",
        "The fastest grower leaned into the parade and knocked every flag over.",
        "Its stem was strong on one side but wobbly on the other.",
        "place a support behind the stem and leave room between the pots",
        ("set a stick behind the leaning seedling", "spaced the pots in a wide row"),
        "The seedlings stood in a neat line, each flag waving.",
        "At the parade's finish, the tallest seedling marched straight into a watering hose.",
        "growth is not a race; each living thing needs its own space",
        "three flags waved while one seedling wore a loop of hose like a belt",
    ),
    Scenario(
        "pumpkin-door",
        "They watched a pumpkin vine grow toward the garden gate.",
        "The vine stretched across the doorway and became a green trip line.",
        "Its newest leaves pointed toward the empty trellis.",
        "guide the vine upward before anyone walks through",
        ("held the doorway clear", "trained the vine along the trellis"),
        "The gate opened freely, and the vine climbed toward the sun.",
        "Luna forgot the trellis was there and walked into the leaves with a soft plop.",
        "growth is welcome when it is guided away from danger",
        "the gate stood open while a leaf rested on Luna's nose",
    ),
    Scenario(
        "giant-name-tag",
        "They made a name tag for a seedling and checked its growth each day.",
        "The seedling grew faster than the tag, so the tag hung from one leaf.",
        "The stem had grown, but the old string had not.",
        "replace the tight string with a loose paper loop",
        ("cut the old string away", "made a wide loop from soft paper"),
        "The new tag rested loosely beside the stem.",
        "Their new tag was so large that the plant looked like it was wearing a sandwich board.",
        "growing bodies need room for their labels and supports",
        "the seedling stood under a giant sign that read 'Probably Tall'",
    ),
]

OPENINGS = [
    "{a} and {b} arrived in {setting} with a seed, a ruler, and an unreasonable amount of excitement.",
    "In {setting}, {a} discovered that a tiny plant could cause a very large problem.",
    "Morning sunshine found {a} and {b} checking on {plant} in {setting}.",
    "The garden was quiet until {plant} made a surprising new move.",
    "{a} and {b} had planned a peaceful growth experiment in {setting}.",
    "A small pot sat in {setting}, but the plant inside was no longer small.",
]

REACTIONS = [
    "'That is definitely taller than breakfast,' said {a}.",
    "{b} blinked. 'Plants are not supposed to be this funny.'",
    "'We need a plan before the plant grows a hat,' {a} said.",
    "{b} pointed at the trouble. 'It changed while we were looking at it!'",
    "They stared for a moment, because the plant seemed to be staring back.",
    "'I vote for careful hands,' said {b}. 'The plant votes for more room.'",
]

DIALOGUE = [
    "'You hold the stem,' said {a}. 'I will handle the surprising part.' 'Agreed,' said {b}.",
    "'What changed?' asked {b}. 'The plant grew into our plan,' said {a}. 'Then we need a bigger plan.'",
    "'Should we pull it?' asked {a}. 'No,' said {b}. 'If growth is gentle, our help should be gentle too.'",
    "'I thought we were measuring a plant,' said {b}. 'We are,' said {a}, 'but the plant is measuring our patience.'",
]

def generate_world(p: StoryParams) -> World:
    if p.first_name == p.second_name:
        raise StoryError("The two gardeners must have different names.")
    if p.setting not in SETTINGS:
        raise StoryError("The setting must be one of the registered growing places.")
    if p.plant not in PLANTS:
        raise StoryError("The plant must be one of the registered garden plants.")

    world = World(p.setting)
    a = world.add(Entity("A", "character", p.first_name))
    b = world.add(Entity("B", "character", p.second_name))
    plant = world.add(Entity("P", "plant", p.plant))
    seed = abs(p.seed or 0)
    scene = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // 11) % len(OPENINGS)].format(
        a=a.label, b=b.label, setting=p.setting, plant=plant.label
    )
    reaction = REACTIONS[(seed // 17) % len(REACTIONS)].format(a=a.label, b=b.label)
    exchange = DIALOGUE[(seed // 23) % len(DIALOGUE)]

    world.say(opening)
    world.say(f"{a.label} and {b.label} {scene.beginning}")
    world.say(f"{a.label} said, 'Let us watch closely.' {b.label} answered, 'And laugh only when the plant is safe.'")
    world.para()
    world.say(scene.trouble)
    world.say(reaction)
    world.say(f"They noticed that {scene.clue}.")
    world.say(exchange)
    world.para()
    world.say(f"They decided to {scene.plan}.")
    world.say(f"{a.label} {scene.jobs[0]}, while {b.label} {scene.jobs[1]}.")
    world.say(scene.result)
    world.para()
    world.say("For one bright moment, the growing problem seemed solved.")
    world.say(f"Then came the bad ending: {scene.bad_ending}")
    world.say(f"They cleaned up, checked the plant, and admitted that {scene.lesson}.")
    world.say(f"At last, {scene.image}.")
    plant.meters.update(height=1.0, cared_for=1.0, growth_seen=1.0)
    a.memes.update(patience=1.0, curiosity=1.0)
    b.memes.update(patience=1.0, cooperation=1.0)
    world.facts.update(
        first=a.label,
        second=b.label,
        plant=plant.label,
        scenario=scene.key,
        beginning=scene.beginning,
        trouble=scene.trouble,
        clue=scene.clue,
        plan=scene.plan,
        first_job=scene.jobs[0],
        second_job=scene.jobs[1],
        result=scene.result,
        bad_ending=scene.bad_ending,
        lesson=scene.lesson,
        image=scene.image,
        growth=True,
        bad_ending=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What was growing in the story, and what trouble did it cause?",
            answer=f"{f['plant']} was growing. The trouble was that {str(f['trouble'])[0].lower() + str(f['trouble'])[1:]}",
        ),
        QAItem(
            question="What clue helped the children make a careful plan?",
            answer=f"They noticed that {f['clue']}. That clue showed them how to help without hurting the growing plant.",
        ),
        QAItem(
            question="How did the two children divide the work?",
            answer=f"{f['first']} {f['first_job']}, while {f['second']} {f['second_job']}. Their different jobs made the plan possible.",
        ),
        QAItem(
            question="What was the bad ending?",
            answer=f"The bad ending was that {f['bad_ending']} Even after the mishap, they checked that the plant was safe.",
        ),
        QAItem(
            question="What did the children learn from the growth?",
            answer=f"They learned that {f['lesson']}. The final image was that {f['image']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does growth mean?",
            answer="Growth means becoming larger, stronger, or more developed over time.",
        ),
        QAItem(
            question="Why do growing plants need room?",
            answer="Growing plants need room so their roots, stems, and leaves can develop without being squeezed or damaged.",
        ),
        QAItem(
            question="What is a bad ending in a funny story?",
            answer="A bad ending is an unfortunate result or comic mishap, though the characters can still learn something and keep everyone safe.",
        ),
        QAItem(
            question="Why should people observe a plant before helping it?",
            answer="Observation shows what has changed and helps people choose gentle care instead of making a guess or pulling too hard.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly comedy about {f['first']} and {f['second']} caring for {f['plant']}.",
        f"Tell a growth story in {world.setting} where {f['trouble']}",
        "Create a funny story with a bad ending that is safe, clear, and teaches patient care.",
    ]


ASP_RULES = r"""
plant_grows(P) :- plant(P), observed_growth(P), cared_for(P).
careful_plan(P) :- plant(P), support(P), water_gently(P).
comic_bad_ending(P) :- plant(P), mishap(P), cared_for(P).
resolved_growth(P) :- plant_grows(P), careful_plan(P), comic_bad_ending(P).
#show plant_grows/1.
#show careful_plan/1.
#show comic_bad_ending/1.
#show resolved_growth/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for plant in ("bean", "tomato", "sunflower", "pumpkin"):
        lines.extend(
            [
                asp.fact("plant", plant),
                asp.fact("observed_growth", plant),
                asp.fact("cared_for", plant),
                asp.fact("support", plant),
                asp.fact("water_gently", plant),
                asp.fact("mishap", plant),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(
        asp_program(
            "#show plant_grows/1. #show careful_plan/1. "
            "#show comic_bad_ending/1. #show resolved_growth/1."
        )
    )
    grown = asp.atoms(symbols, "plant_grows")
    careful = asp.atoms(symbols, "careful_plan")
    comic = asp.atoms(symbols, "comic_bad_ending")
    resolved = asp.atoms(symbols, "resolved_growth")
    if grown and careful and comic and resolved:
        print("OK: ASP found observed growth, careful care, a comic bad ending, and resolution.")
        return 0
    print("MISMATCH: ASP did not find the complete growth story pattern.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--first-name")
    ap.add_argument("--second-name")
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    first = args.first_name or rng.choice(NAMES)
    second = args.second_name or rng.choice([name for name in NAMES if name != first])
    if first == second:
        raise StoryError("The two gardeners must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(SETTINGS),
        first_name=first,
        second_name=second,
        plant=args.plant or rng.choice(PLANTS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the sunny community garden", "Luna", "Bram", "a bean sprout", 4),
    StoryParams("the school windowsill", "Tessa", "Milo", "a sunflower shoot", 29),
    StoryParams("the little rooftop greenhouse", "Nia", "Otis", "a tiny pumpkin vine", 61),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        f = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"scenario={f['scenario']} growth={f['growth']} bad_ending={f['bad_ending']}"
        )
    if qa:
        for i, item in enumerate(sample.story_qa, 1):
            print(f"Q{i}: {item.question}\nA{i}: {item.answer}")
        for i, item in enumerate(sample.world_qa, 1):
            print(f"W{i}: {item.question}\nA{i}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show plant_grows/1. #show careful_plan/1. #show comic_bad_ending/1. #show resolved_growth/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show plant_grows/1. #show careful_plan/1. #show comic_bad_ending/1. #show resolved_growth/1."))
        print(json.dumps({name: asp.atoms(symbols, name) for name in ("plant_grows", "careful_plan", "comic_bad_ending", "resolved_growth")}, indent=2))
        return

    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(base + index))
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
