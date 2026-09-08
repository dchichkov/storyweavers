#!/usr/bin/env python3
"""
A standalone pirate-tale storyworld about a pompon, moral courage, and transformation.
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
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
pirate_story(S) :- setting(S), has_moral_value(S), has_transformation(S).
honest_choice(S) :- pirate_story(S), returns_treasure(S).
worthy_treasure(T) :- treasure(T), small(T).
good_ending(S) :- pirate_story(S), honest_choice(S), worthy_treasure(pompon).
"""

PLACE = "the Moonwake ship"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    companion: str
    pompon_color: str
    moral_value: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    false_choice: str
    clue: str
    companion_line: str
    repair: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            bits = []
            if entity.meters:
                bits.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                bits.append(f"memes={dict(entity.memes)}")
            if entity.label:
                bits.append(f"label={entity.label!r}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) {' '.join(bits)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The captain needs a name.")
    if not params.companion.strip():
        raise StoryError("The pirate tale needs a companion.")
    if params.pompon_color not in {"red", "blue", "gold", "green", "purple"}:
        raise StoryError("The pompon must have a cheerful, ordinary color.")
    if params.moral_value not in {"honesty", "kindness", "courage", "fairness"}:
        raise StoryError(
            "The moral value must be honesty, kindness, courage, or fairness."
        )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "moonwake_ship"),
            asp.fact("has_moral_value", "moonwake_ship"),
            asp.fact("has_transformation", "moonwake_ship"),
            asp.fact("returns_treasure", "moonwake_ship"),
            asp.fact("treasure", "pompon"),
            asp.fact("small", "pompon"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


SCENARIOS = [
    Scenario(
        key="stormy_flag",
        premise="was polishing the ship's bright flag before the harbor parade",
        trouble="A sudden gust tore the flag loose, and the captain's lucky pompon rolled toward the dark water.",
        false_choice="grabbing the pompon first would leave the frightened deckhand clinging to the slipping flag rope",
        clue="the rope had caught on a brass hook beside the mast",
        companion_line='"Save the sailor before the treasure," the companion cried.',
        repair="secured the deckhand with a safety line, freed the rope from the hook, and caught the pompon in a net",
        result="The deckhand stood safely on deck, and the flag flew again above the Moonwake.",
        lesson="honesty and care matter more than keeping a lucky prize",
        ending="the red pompon bobbed from the flagstaff while every sailor cheered the rescued deckhand",
    ),
    Scenario(
        key="false_treasure",
        premise="was checking the crew's map before sailing toward a little island",
        trouble="A golden pompon appeared in the sand, and the crew began calling it the lost crown jewel.",
        false_choice="claiming it as a royal prize would make the captain rich but would leave the truth buried",
        clue="a neat row of tiny wool fibers led from the beach to a fisher's boat",
        companion_line='"A real owner may be missing it," the companion said.',
        repair="followed the fibers, asked the fisher a careful question, and returned the pompon to a child's cap",
        result="The fisher thanked the crew, and the islanders offered fresh bread for the honest deed.",
        lesson="telling the truth can turn a tempting find into a friendship",
        ending="the golden pompon returned to the child's cap as the Moonwake sailed on under a kinder sun",
    ),
    Scenario(
        key="quiet_cabin",
        premise="was preparing a surprise supper for a homesick sailor",
        trouble="The sailor's small keepsake pompon vanished from the cabin shelf before supper began.",
        false_choice="blaming the newest sailor would make the search quick but could hurt an innocent friend",
        clue="blue wool fibers rested beside the open laundry basket",
        companion_line='"Let us ask before we accuse," the companion whispered.',
        repair="questioned the crew gently, searched the laundry basket, and found the pompon tucked in a warm scarf",
        result="The sailor received the keepsake back and learned that nobody had meant to take it.",
        lesson="fairness gives people room to explain what really happened",
        ending="the blue pompon rested beside the supper bowl while the homesick sailor smiled",
    ),
    Scenario(
        key="reef_signal",
        premise="was guiding the Moonwake through a reef at dawn",
        trouble="The signal pennant fell into the sea, and the ship drifted toward a line of sharp rocks.",
        false_choice="pretending to know the safe channel would keep the captain's pride but endanger everyone aboard",
        clue="the companion remembered three white gulls circling above the deep-water passage",
        companion_line='"I remember the safe way, but we must turn now," the companion said.',
        repair="admitted the mistake, listened to the clue, and turned the ship toward the gulls",
        result="The Moonwake slipped through the deep channel with only a splash against its hull.",
        lesson="courage means telling the truth when others depend on you",
        ending="the green pompon tied to the new signal fluttered above calm water beyond the reef",
    ),
    Scenario(
        key="harbor_scale",
        premise="was weighing fruit for every member of the crew",
        trouble="The scale tipped unfairly, giving one sailor less fruit than the others.",
        false_choice="hiding the uneven scale would save time but would make the smallest sailor go hungry",
        clue="a tiny pompon thread was caught beneath one side of the balance",
        companion_line='"The scale needs a fair chance," the companion said.',
        repair="removed the thread, tested both sides, and measured each portion again",
        result="Every sailor received an equal share, including the one who had waited quietly.",
        lesson="fairness is measured by how the least powerful person is treated",
        ending="the purple pompon hung from the balanced scale as the crew shared fruit in peace",
    ),
]


NAMES = ["Luna", "Mara", "Pip", "Tessa", "Coral", "Finn", "Nico", "Rae"]
COMPANIONS = [
    "a young deckhand",
    "a clever cabin mouse",
    "a shy parrot",
    "an old sailor",
    "a brave harbor child",
]
COLORS = ["red", "blue", "gold", "green", "purple"]
VALUES = ["honesty", "kindness", "courage", "fairness"]

OPENINGS = [
    "At sunrise, Captain {name} stood on the deck of the Moonwake.",
    "The Moonwake rocked gently beneath a sky bright as a polished coin.",
    "Before the first gull called, Captain {name} checked every rope on the ship.",
    "A warm sea wind swept across the deck as Captain {name} began the day's voyage.",
    "The harbor bells rang when Captain {name} raised a hand to the waiting crew.",
]

REACTIONS = [
    "{name} reached toward the pompon, then stopped to look at everyone nearby.",
    '"A treasure is never worth leaving a friend in danger," {name} said.',
    "{name} felt the old pirate urge to boast, but chose to listen instead.",
    '"We will solve the real trouble first," {name} promised.',
    "{name} took a steady breath and asked who might be affected by the next choice.",
]

PLANS = [
    "They named the danger aloud and gave each person one safe job.",
    "They moved the pompon out of the way, then worked slowly together.",
    "They checked the clue twice before touching a rope, sail, or sailor.",
    "They agreed that the best treasure would be everyone reaching safety.",
]

CELEBRATIONS = [
    "The crew clapped, but the captain shared the credit with the companion who noticed the clue.",
    "The companion's smile shone brighter than any coin in the ship's chest.",
    "Nobody called the captain the richest pirate; they called the captain trustworthy.",
    "The crew celebrated with warm bread, bright laughter, and a promise to remember the lesson.",
]


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        companion=rng.choice(COMPANIONS),
        pompon_color=rng.choice(COLORS),
        moral_value=rng.choice(VALUES),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale about a pompon and a transforming moral choice."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--pompon-color", choices=COLORS)
    parser.add_argument("--moral-value", choices=VALUES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.companion:
        params.companion = args.companion
    if args.pompon_color:
        params.pompon_color = args.pompon_color
    if args.moral_value:
        params.moral_value = args.moral_value
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    captain = world.add(
        Entity(id="captain", kind="character", label=params.name)
    )
    companion = world.add(
        Entity(id="companion", kind="character", label=params.companion)
    )
    pompon = world.add(
        Entity(id="pompon", kind="treasure", label=f"{params.pompon_color} pompon")
    )
    ship = world.add(Entity(id="ship", kind="place", label="Moonwake"))
    world.facts.update(
        captain=captain,
        companion=companion,
        pompon=pompon,
        ship=ship,
        place=PLACE,
        moral_value=params.moral_value,
        transformation=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    captain = world.get("captain")
    companion = world.get("companion")
    pompon = world.get("pompon")

    opening = rng.choice(OPENINGS).format(name=captain.label)
    reaction = rng.choice(REACTIONS).format(name=captain.label)
    plan = rng.choice(PLANS)
    celebration = rng.choice(CELEBRATIONS)

    captain.bump_meme("pride")
    companion.bump_meme("trust")
    pompon.bump_meter("importance")

    world.say(opening)
    world.say(
        f"{captain.label} sailed with {companion.label}, and a {pompon.label} "
        f"decorated the captain's hat. {captain.label} {scenario.premise}."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(f"At first, {captain.label} considered {scenario.false_choice}.")
    world.say(reaction)
    world.para()

    captain.bump_meme("reflection")
    companion.bump_meme("courage")
    world.say(f"Then they noticed that {scenario.clue}.")
    world.say(scenario.companion_line)
    world.say(plan)
    world.para()

    captain.bump_meme("moral_courage")
    captain.bump_meter("care", 1)
    pompon.bump_meter("shared_value", 1)
    world.say(
        f"Instead of chasing the {pompon.label}, {captain.label} chose "
        f"{params.moral_value} and {scenario.repair}."
    )
    world.say(scenario.result)
    world.para()

    captain.bump_meme("trustworthiness")
    companion.bump_meme("joy")
    world.say(celebration)
    world.say(f"That was the transformation: {captain.label} learned that {scenario.lesson}.")
    world.say(
        f"As the happy ending, the {pompon.label} became a reminder rather than a prize; "
        f"{scenario.ending}."
    )

    world.facts.update(
        scenario=scenario.key,
        premise=scenario.premise,
        trouble=scenario.trouble,
        false_choice=scenario.false_choice,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        lesson=scenario.lesson,
        ending_image=scenario.ending,
        resolved=True,
        returned_treasure=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    captain = facts["captain"].label
    companion = facts["companion"].label
    value = facts["moral_value"]
    return [
        f"Write a child-friendly pirate tale in which {captain} and {companion} face a difficult choice.",
        f"Tell a pirate story featuring a pompon, the moral value of {value}, and a clear transformation.",
        f"Write a warm adventure where a small treasure matters less than helping someone safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    captain = facts["captain"].label
    companion = facts["companion"].label
    pompon = facts["pompon"].label
    return [
        QAItem(
            question="What trouble did the crew face?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue helped {captain} and {companion}?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"What moral choice did {captain} make?",
            answer=(
                f"{captain} chose {facts['moral_value']} and "
                f"{facts['repair']}."
            ),
        ),
        QAItem(
            question="What changed after the choice?",
            answer=str(facts["result"]),
        ),
        QAItem(
            question=f"What did the {pompon} become at the end?",
            answer=(
                f"The {pompon} became a reminder rather than a prize, and "
                f"{facts['ending_image']}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a belief about how to treat people and choose what is right.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change in a person, thing, or situation.",
        ),
        QAItem(
            question="Why can honesty be brave?",
            answer="Honesty can be brave because telling the truth may be difficult, especially when someone could benefit from hiding it.",
        ),
        QAItem(
            question="What is a pompon?",
            answer="A pompon is a small fluffy ball of yarn or thread, often used as a decoration.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show pirate_story/1.\n"
        "#show honest_choice/1.\n"
        "#show worthy_treasure/1.\n"
        "#show good_ending/1."
    )
    model = asp.one_model(program)
    actual = {
        (
            symbol.name,
            tuple(
                argument.string
                if argument.type.name == "String"
                else argument.name
                if argument.type.name == "Function"
                else str(argument.number)
                for argument in symbol.arguments
            ),
        )
        for symbol in model
        if symbol.name in {
            "pirate_story",
            "honest_choice",
            "worthy_treasure",
            "good_ending",
        }
    }
    expected = {
        ("pirate_story", ("moonwake_ship",)),
        ("honest_choice", ("moonwake_ship",)),
        ("worthy_treasure", ("pompon",)),
        ("good_ending", ("moonwake_ship",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reasonableness model.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    rng = random.Random(77)
    for _ in range(5):
        sample = generate(valid_params(rng))
        if not sample.story or "pompon" not in sample.story:
            print("Generated-story verification failed.")
            return 1

    print("OK: ASP twin matches the Python gate and generated stories.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_ending/1."))
    return sorted(asp.atoms(model, "good_ending"))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        name="Luna",
        companion="a young deckhand",
        pompon_color="red",
        moral_value="honesty",
        seed=17,
    ),
    StoryParams(
        name="Mara",
        companion="a clever cabin mouse",
        pompon_color="gold",
        moral_value="kindness",
        seed=31,
    ),
    StoryParams(
        name="Finn",
        companion="a shy parrot",
        pompon_color="blue",
        moral_value="courage",
        seed=53,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_ending/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible Moonwake pirate stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(
                args, random.Random(rng.randrange(2**31))
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
