#!/usr/bin/env python3
"""
A tall tale about a boast, a tireless race against time, and curiosity that
turns a cautionary warning into a wise choice.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    name: str
    affordances: set[str]


@dataclass(frozen=True)
class Challenge:
    id: str
    opening: str
    obstacle: str
    boast: str
    clue: str
    careful_action: str
    consequence: str
    change: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple[str, str]] = field(default_factory=set)

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


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTING = Setting(
    name="the Cloud-Clock Valley",
    affordances={"race", "question", "repair", "cooperation"},
)

CHALLENGES = {
    "sunset_bridge": Challenge(
        id="sunset_bridge",
        opening="The valley's great rope bridge had to be repaired before the sun touched the western peak.",
        obstacle="One bridge wheel groaned, and every minute made the loose planks swing farther over the ravine.",
        boast="I can cross the whole bridge, mend the wheel, and beat the sunset without stopping for anybody!",
        clue="a small crack ran through the wheel's wooden rim, exactly where the loudest creak began",
        careful_action="asked the bridge keeper to hold the rope, tested the wheel with one gentle pull, and replaced the cracked peg before crossing",
        consequence="the wheel turned smoothly, the bridge steadied, and the travelers reached the far meadow before dusk",
        change="the valley began checking every bridge wheel at noon instead of waiting for a dangerous creak",
        ending="That evening, the sun slipped behind the peak while the repaired bridge hummed safely in the golden wind.",
    ),
    "thunder_cart": Challenge(
        id="thunder_cart",
        opening="A cart of rain barrels had to reach the dry orchard before a thunderstorm rolled over the hills.",
        obstacle="The cart's tire was losing air, while dark clouds marched toward the orchard like a row of enormous boots.",
        boast="I am tireless! I can push this cart alone faster than thunder can find us!",
        clue="the tire sagged beside a thorn hidden in the road, and the shiny hub had begun to wobble",
        careful_action="stopped the cart, pulled out the thorn, shared the hand pump, and tightened the loose hub while the companion counted each turn",
        consequence="the tire held firm, the barrels reached the thirsty trees, and the rain arrived just after the last barrel was poured",
        change="every orchard cart received a tire check and a walking partner before leaving the shed",
        ending="Rain drummed on the leaves, and the repaired tire rested beside the orchard like a round moon that had learned patience.",
    ),
    "moon_clock": Challenge(
        id="moon_clock",
        opening="The moon clock on the tallest tower had to be wound before midnight or the valley's night bells would stay silent.",
        obstacle="Its brass tire-like winding ring spun freely, but one hidden tooth had bent beneath the clock face.",
        boast="I know every gear in this tower! I will wind it with one hand and make midnight hurry!",
        clue="the ring clicked once on the high side and twice on the low side, although the moon clock stood still",
        careful_action="asked the clockmaker to light the gear box, counted the uneven clicks, and straightened the bent tooth before winding",
        consequence="the clock began to turn, the bells rang at midnight, and the valley knew when to bring its animals indoors",
        change="the tower crew began listening to a clock's small warning sounds before touching its large wheels",
        ending="At midnight, the bells rolled across the valley, and even the stars seemed to pause and listen.",
    ),
}

NAMES = ["Luna", "Pip", "Mara", "Tobin", "Nell", "Orin"]
COMPANIONS = ["the patient wheelwright", "a young orchard keeper", "the curious clockmaker"]
TRAITS = ["bold", "curious", "quick-footed", "proud", "inventive"]
DIALOGUES = [
    "What is the smallest thing that could make the biggest trouble?",
    "Should we hurry past that sound, or listen to it first?",
    "What would happen if your strong plan needed one careful hand?",
    "Can we test the wheel before we trust it?",
    "Who else can see what I might be missing?",
]
REFLECTIONS = [
    "A boast can run quickly, but curiosity knows when to stop.",
    "Being tireless is not the same as being careful.",
    "A warning is a gift when someone is curious enough to hear it.",
    "The tallest tale became wiser when its hero made room for another pair of eyes.",
    "Speed is useful, but a safe question can save more time than a reckless sprint.",
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, challenge) for place in [SETTING.name] for challenge in CHALLENGES]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a cautionary curiosity tall tale about a boast and a race against time."
    )
    parser.add_argument("--place", choices=[SETTING.name])
    parser.add_argument("--challenge", choices=CHALLENGES)
    parser.add_argument("--name")
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or SETTING.name
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, challenge, name, companion, trait, args.seed)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != SETTING.name:
        raise StoryError("This tale belongs in the Cloud-Clock Valley.")
    if params.challenge not in CHALLENGES:
        raise StoryError("That challenge is not part of the valley's tall-tale registry.")
    if not params.name.strip():
        raise StoryError("The hero needs a name.")
    if not params.companion.strip():
        raise StoryError("The hero needs a companion who can notice clues.")


def add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meter(key) + amount


def add_meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.meme(key) + amount


def tell(world: World, params: StoryParams) -> None:
    challenge = CHALLENGES[params.challenge]
    number = params.seed if params.seed is not None else sum(
        (index + 1) * ord(char)
        for index, char in enumerate(
            f"{params.name}|{params.challenge}|{params.companion}|{params.trait}"
        )
    )
    dialogue = DIALOGUES[number % len(DIALOGUES)]
    reflection = REFLECTIONS[(number // len(DIALOGUES)) % len(REFLECTIONS)]

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="traveler",
            label=params.name,
            memes={"curiosity": 1.0, "confidence": 1.0, "worry": 0.0},
        )
    )
    companion = world.add(
        Entity(
            id="Companion",
            kind="character",
            type="helper",
            label=params.companion,
            memes={"patience": 1.0, "trust": 1.0},
        )
    )
    tire = world.add(
        Entity(
            id="Tire",
            kind="thing",
            type="wheel",
            label="the working tire",
            meters={"air": 1.0, "strength": 1.0},
        )
    )
    clock = world.add(
        Entity(
            id="Time",
            kind="thing",
            type="clock",
            label="the valley clock",
            meters={"remaining": 1.0},
        )
    )

    world.say(
        f"In the Cloud-Clock Valley, where mountains were tall enough to tickle the moon, "
        f"{params.name} was famous for being {params.trait}."
    )
    world.say(challenge.opening)
    world.say(
        f"The valley clock showed that time was running out, and the {params.companion} "
        f"pointed toward the waiting work."
    )
    world.para()

    add_meme(hero, "confidence", 1.0)
    add_meme(hero, "worry", 1.0)
    add_meter(clock, "remaining", -0.25)
    world.say(challenge.obstacle)
    world.say(f"{params.name} puffed up like a mountain and declared, \"{challenge.boast}\"")
    world.say(
        f"The {params.companion} answered, \"{dialogue}\""
    )
    world.say(
        f"{params.name} almost rushed ahead, but curiosity tugged harder than pride."
    )

    world.para()
    add_meme(hero, "curiosity", 1.0)
    add_meter(clock, "remaining", -0.25)
    world.say(
        f"{params.name} crouched beside the trouble and discovered that {challenge.clue}."
    )
    world.say(
        f"That tiny clue mattered because the {tire.label} could fail if the hidden weakness was ignored."
    )
    world.say(
        f"{params.name} said, \"You were right to ask. Let us find out before we race.\""
    )
    world.say(
        f"Together, {params.name} and the {params.companion} {challenge.careful_action}."
    )
    add_meter(tire, "air", 1.0)
    add_meter(tire, "strength", 1.0)
    add_meme(hero, "trust", 1.0)
    add_meter(clock, "remaining", -0.25)

    world.para()
    world.say(f"The careful plan worked: {challenge.consequence}.")
    add_meme(hero, "pride", 1.0)
    add_meme(hero, "patience", 1.0)
    world.say(
        f"{params.name} had not stopped being brave; {params.name} had learned to make bravery useful."
    )
    world.say(f"The valley changed its custom: {challenge.change}.")
    world.say(f"{reflection} {challenge.ending}")

    world.facts.update(
        hero=hero,
        companion=companion,
        tire=tire,
        clock=clock,
        challenge=challenge,
        dialogue=dialogue,
        reflection=reflection,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    challenge = world.facts["challenge"]
    hero = world.facts["hero"]
    return [
        f"Write a cautionary curiosity tall tale about {hero.id}, a boast, and time running out.",
        f"Tell a child-facing story in which {hero.id} must investigate this trouble: {challenge.obstacle}",
        f"Write a tall tale where a tire, a helper, and one careful question prevent a disaster.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    companion = facts["companion"]
    challenge = facts["challenge"]
    return [
        QAItem(
            question=f"Why was {hero.id} in a hurry?",
            answer=f"{challenge.opening} The valley clock showed that time was running out.",
        ),
        QAItem(
            question=f"What did {hero.id} boast?",
            answer=f"{hero.id} boasted, \"{challenge.boast}\"",
        ),
        QAItem(
            question=f"What clue made {hero.id} slow down?",
            answer=f"{hero.id} noticed that {challenge.clue}.",
        ),
        QAItem(
            question=f"How did the companion help {hero.id}?",
            answer=f"The {companion.label} helped by staying patient and working with {hero.id} while they {challenge.careful_action}.",
        ),
        QAItem(
            question="What happened after the careful repair?",
            answer=f"{challenge.consequence}.",
        ),
        QAItem(
            question="What changed in the valley afterward?",
            answer=f"The valley adopted this safer custom: {challenge.change}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=f"{facts['reflection']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is curiosity useful?",
            answer="Curiosity is useful because it encourages someone to ask questions and inspect clues before choosing an action.",
        ),
        QAItem(
            question="Why can boasting be dangerous?",
            answer="Boasting can be dangerous when pride makes someone hurry, ignore advice, or pretend a problem is simpler than it is.",
        ),
        QAItem(
            question="Why should a tire be checked before a journey?",
            answer="A tire should be checked because a weak or damaged tire can make a cart or vehicle unsafe.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means noticing possible danger and choosing a careful way to proceed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Prompts =="]
    sections.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story QA ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== World QA ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
place(cloud_clock_valley).
challenge(sunset_bridge).
challenge(thunder_cart).
challenge(moon_clock).
valid(cloud_clock_valley, C) :- challenge(C).
safe_action(C) :- valid(cloud_clock_valley, C).
#show valid/2.
#show safe_action/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "cloud_clock_valley"),
            asp.fact("challenge", "sunset_bridge"),
            asp.fact("challenge", "thunder_cart"),
            asp.fact("challenge", "moon_clock"),
        ]
    )


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = {
        ("cloud_clock_valley", challenge) for challenge in CHALLENGES
    }
    actual = set(asp_valid_combos())
    if expected != actual:
        print("MISMATCH: ASP and Python registries differ.")
        return 1
    for seed in range(8):
        rng = random.Random(seed)
        params = resolve_params(
            argparse.Namespace(
                place=None,
                challenge=None,
                name=None,
                companion=None,
                trait=None,
                seed=seed,
            ),
            rng,
        )
        try:
            sample = generate(params)
        except StoryError as error:
            print(f"FAILED generated story verification: {error}")
            return 1
        if not sample.story or len(sample.story_qa) < 4:
            print("FAILED generated story verification: incomplete sample.")
            return 1
    print(f"OK: ASP matches Python ({len(actual)} challenges), and generated stories pass.")
    return 0


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


CURATED = [
    StoryParams("the Cloud-Clock Valley", "thunder_cart", "Luna", "the patient wheelwright", "curious"),
    StoryParams("the Cloud-Clock Valley", "sunset_bridge", "Pip", "a young orchard keeper", "bold"),
    StoryParams("the Cloud-Clock Valley", "moon_clock", "Mara", "the curious clockmaker", "inventive"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show safe_action/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(args.n, 1):
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.challenge}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
