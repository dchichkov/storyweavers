#!/usr/bin/env python3
"""A child-friendly folk tale about Ruff, sharing, and solving a village problem."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Tale:
    key: str
    place: str
    gift: str
    trouble: str
    first_guess: str
    clue: str
    test: str
    solution: str
    sharing_act: str
    final_image: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Grandmother Iva"
    ruff: str = "Ruff"
    tale: str = "bread_wind"
    mood: str = "golden"
    opening_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


class World:
    def __init__(self, tale: Tale):
        self.tale = tale
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


TALES = {
    "bread_wind": Tale(
        key="bread_wind",
        place="a hill village beside a windy mill",
        gift="a warm round loaf",
        trouble="the village oven would not draw enough air, so every loaf stayed flat",
        first_guess="the mill keeper had hidden the oven's missing breeze",
        clue="the same flour dust lay on the oven door and beneath the mill's old bellows",
        test="carry a ribbon through the mill room and watch how the air moves",
        solution="a fallen flour sack had covered the bellows' lower vent",
        sharing_act="Ruff shared the loaf with the mill keeper and every child who had helped",
        final_image="the repaired bellows puffed flour-white clouds while neighbors broke bread together",
        lesson="A shared gift can open ears, and a careful test can find the real cause of trouble.",
    ),
    "berry_bridge": Tale(
        key="berry_bridge",
        place="a green valley crossed by a narrow wooden bridge",
        gift="a basket of red berries",
        trouble="the bridge rope had snapped, leaving the berry pickers on opposite banks",
        first_guess="the river spirit had taken the rope",
        clue="fresh pine shavings rested beside the broken knot",
        test="compare the splinters with the wood of a fallen branch",
        solution="a branch had rubbed the rope loose during the night's storm",
        sharing_act="Ruff divided the berries between both banks before anyone crossed",
        final_image="the new rope held firm as berry baskets passed from hand to hand",
        lesson="Sharing can calm a frightened crowd, while evidence turns a scary guess into a fix.",
    ),
    "lantern_path": Tale(
        key="lantern_path",
        place="a little forest village beneath tall fir trees",
        gift="a bright honey lantern",
        trouble="the path lanterns went dark before the winter market",
        first_guess="a hungry fox had swallowed the candles",
        clue="wax drops led from the market shed to a loose shutter",
        test="close the shutter and see whether the candle flames stay upright",
        solution="the shutter's cold draft had blown out each flame",
        sharing_act="Ruff passed the honey lantern from traveler to traveler",
        final_image="a warm chain of lights wound through the trees to the market square",
        lesson="When people share light and ask what the clues truly show, a dark problem grows smaller.",
    ),
    "well_song": Tale(
        key="well_song",
        place="a stone village around an old singing well",
        gift="a blue jug of clear water",
        trouble="the well's cheerful echo had vanished",
        first_guess="the moon had taken the song",
        clue="small pebbles filled the wooden echo pipe",
        test="tap the pipe gently and listen before removing one pebble",
        solution="children's skipping stones had rolled into the pipe",
        sharing_act="Ruff shared the clear water with the thirsty singers",
        final_image="the well sang again as the blue jug traveled around the circle",
        lesson="Gentle testing reveals hidden causes, and generosity gives a solution a happy ending.",
    ),
}

HEROES = ("Luna", "Mira", "Nell", "Tavi")
HELPERS = ("Grandmother Iva", "Uncle Bram", "Aunt Sela", "Old Tomas")
MOODS = ("golden", "misty", "crisp", "quiet", "bright")

OPENINGS = (
    "Long ago, when roads were still taught by birds, Luna lived in a small village.",
    "In the days when a clever child could ask a river for advice, Luna walked home at sunset.",
    "Once, beneath a wide and watchful sky, Luna found that one village worry had grown very large.",
    "There was a village where every neighbor knew the sound of a kind deed.",
    "At the edge of an old folk-tale forest, Luna carried a gift that was meant for everyone.",
    "The morning began with birdsong, but by noon the villagers were whispering about trouble.",
)

DIALOGUES = (
    '"Ruff, what do you notice?" Luna asked. "I notice where the dust has settled," said Ruff.',
    '"Should we blame someone?" Luna asked. Ruff shook his ruff. "First, let us test the clue."',
    '"A guess can be loud," said Grandmother Iva, "but evidence speaks more clearly." Luna replied, "Then we will listen together."',
    '"May I help?" asked Luna. "You may help by sharing what you see," said Grandmother Iva.',
    '"The village needs a solution, not a story about a culprit," Luna said. Ruff wagged his ruff as if he agreed.',
    '"What if the trouble has an ordinary cause?" Luna asked. "Then an ordinary tool may mend it," said Grandmother Iva.',
)

TURNS = (
    "That small test changed the tale.",
    "The first guess fell away like a dry leaf.",
    "At last, the mystery pointed not to a villain, but to a cause.",
    "The village learned that a careful question could be braver than a quick accusation.",
    "The clue had been waiting in plain sight.",
    "Ruff's quiet observation gave the whole village a new way to think.",
)


ASP_RULES = r"""
gift(G) :- gift_fact(G).
problem(T) :- problem_fact(T).
solvable(T) :- problem_fact(T), test_fact(T).
sharing_required(T) :- problem_fact(T), sharing_fact(T).
sound_tale(T) :- solvable(T), sharing_required(T).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for tale in TALES.values():
        lines.extend(
            (
                asp.fact("gift_fact", tale.key),
                asp.fact("problem_fact", tale.key),
                asp.fact("test_fact", tale.key),
                asp.fact("sharing_fact", tale.key),
            )
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about Ruff, sharing, and problem solving."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--ruff")
    parser.add_argument("--tale", choices=sorted(TALES))
    parser.add_argument("--mood", choices=MOODS)
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        ruff=args.ruff or "Ruff",
        tale=args.tale or rng.choice(list(TALES)),
        mood=args.mood or rng.choice(MOODS),
        opening_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURNS)),
    )


def tell(params: StoryParams) -> World:
    if params.tale not in TALES:
        raise StoryError(f"Unknown tale: {params.tale}")
    if not params.hero.strip() or not params.helper.strip() or not params.ruff.strip():
        raise StoryError("Hero, helper, and ruff must have names.")

    tale = TALES[params.tale]
    world = World(tale)
    hero = world.add(
        Entity(
            id=params.hero,
            kind="child",
            label=params.hero,
            meters={"distance_to_village": 0.0, "carrying_weight": 1.0},
            memes={"curiosity": 2.0, "generosity": 1.0, "courage": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="elder",
            label=params.helper,
            meters={"distance_to_village": 0.0},
            memes={"wisdom": 2.0, "patience": 2.0},
        )
    )
    ruff = world.add(
        Entity(
            id=params.ruff,
            kind="companion",
            label=params.ruff,
            meters={"distance_to_clue": 0.0},
            memes={"loyalty": 2.0, "attention": 2.0},
        )
    )
    gift = world.add(
        Entity(
            id="gift",
            kind="shared_object",
            label=tale.gift,
            meters={"warmth": 1.0, "amount": 1.0},
            memes={"welcome": 2.0},
        )
    )

    world.say(OPENINGS[params.opening_mode])
    world.say(
        f"On a {params.mood} morning, {hero.label} carried {tale.gift} through {tale.place}. "
        f"{ruff.label}, a small companion with a proud ruff, trotted beside {hero.label}."
    )
    world.say(f"The gift was meant to be shared, but {tale.trouble}.")
    world.para()

    world.say(
        f"At first, {hero.label} wondered whether {tale.first_guess}. "
        f"That guess made the villagers point toward one another."
    )
    world.say(DIALOGUES[params.dialogue_mode].format(hero=hero.label, ruff=ruff.label))
    world.say(
        f"{ruff.label} lowered his nose and found a better clue: {tale.clue}. "
        f"{hero.label} remembered that a clue should lead to a test, not to blame."
    )
    world.say(f"Together, they decided to {tale.test}.")
    world.say(f"The test showed that {tale.solution}.")
    world.say(TURNS[params.turn_mode])
    world.para()

    world.say(
        f"{params.helper} helped {hero.label} make a safe plan. "
        f"They solved the trouble by using the clue, the right tool, and patient teamwork."
    )
    world.say(f"Then {hero.label} carried out the sharing deed: {tale.sharing_act}.")
    world.say(
        f"The villagers stopped arguing and began helping. {tale.final_image}."
    )
    world.say(f"{hero.label} smiled at {ruff.label}. \"You helped us notice the truth.\"")
    world.say(f"{tale.lesson}")

    world.facts.update(
        hero=hero,
        helper=helper,
        ruff=ruff,
        gift=gift,
        tale=tale,
        first_guess=tale.first_guess,
        clue=tale.clue,
        test=tale.test,
        solution=tale.solution,
        sharing_act=tale.sharing_act,
        solved=True,
        shared=True,
    )
    world.trace.extend(
        (
            f"tale:{tale.key}",
            f"clue:{tale.clue}",
            f"test:{tale.test}",
            f"solution:{tale.solution}",
            "sharing:completed",
        )
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]
    hero: Entity = world.facts["hero"]
    return [
        f"Tell a child-friendly folk tale about {hero.label}, Ruff, and sharing {tale.gift}.",
        f"Show problem solving through the clue that {tale.clue}.",
        f"End with a village image proving that {tale.solution} and that the gift was shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    ruff: Entity = world.facts["ruff"]
    return [
        QAItem(
            question=f"What trouble did {hero.label} find in the village?",
            answer=f"The trouble was that {tale.trouble}.",
        ),
        QAItem(
            question=f"What was {hero.label}'s first guess?",
            answer=f"{hero.label} first wondered whether {tale.first_guess}.",
        ),
        QAItem(
            question=f"How did {ruff.label} help solve the problem?",
            answer=f"{ruff.label} noticed that {tale.clue}, which led {hero.label} and {helper.label} to test the cause.",
        ),
        QAItem(
            question="What did the careful test reveal?",
            answer=f"The test revealed that {tale.solution}.",
        ),
        QAItem(
            question="How did sharing change the ending?",
            answer=f"{tale.sharing_act}. Sharing helped the villagers stop arguing and work together.",
        ),
        QAItem(
            question="What lesson did the folk tale teach?",
            answer=tale.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    return [
        QAItem(
            question="Why is sharing useful when a village has a problem?",
            answer="Sharing builds trust, helps people feel included, and makes it easier for neighbors to work together.",
        ),
        QAItem(
            question="What is a good problem-solving habit?",
            answer="Separate a guess from an observation, look for a clue, test the clue safely, and change the plan when the evidence disagrees.",
        ),
        QAItem(
            question="Why should people avoid blaming someone too quickly?",
            answer="A problem may have an ordinary cause. Careful evidence can prevent an innocent person from being blamed.",
        ),
        QAItem(
            question="What clue mattered in this tale?",
            answer=f"The important clue was that {tale.clue}. It led to a safe test instead of a hurried accusation.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(tale="bread_wind"),
    StoryParams(
        hero="Mira",
        helper="Aunt Sela",
        ruff="Ruff",
        tale="lantern_path",
        mood="misty",
        opening_mode=3,
        dialogue_mode=1,
        turn_mode=4,
    ),
    StoryParams(
        hero="Tavi",
        helper="Old Tomas",
        ruff="Ruff",
        tale="well_song",
        mood="bright",
        opening_mode=1,
        dialogue_mode=5,
        turn_mode=2,
    ),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    show = (
        "#show gift/1.\n"
        "#show problem/1.\n"
        "#show solvable/1.\n"
        "#show sharing_required/1.\n"
        "#show sound_tale/1.\n"
    )
    models = asp.solve(asp_program(show), models=0)
    expected = len(TALES)
    if not models:
        print("ASP produced no model.")
        return 1
    if len(models) != expected:
        print(f"ASP parity failed: expected {expected} models, got {len(models)}.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "Ruff" not in sample.story:
            print("Generated story verification failed.")
            return 1
        if not sample.world.facts["solved"] or not sample.world.facts["shared"]:
            print("World-state verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()
    show = (
        "#show gift/1.\n"
        "#show problem/1.\n"
        "#show solvable/1.\n"
        "#show sharing_required/1.\n"
        "#show sound_tale/1.\n"
    )

    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        models = asp.solve(asp_program(show), models=0)
        print(json.dumps([str(symbol) for model in models for symbol in model], indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
