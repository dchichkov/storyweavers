#!/usr/bin/env python3
"""
A standalone nursery-rhyme storyworld about a gymnastic twist, a worried voice,
and a kind way to turn a penalty into a lesson.
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
setting(nursery_gym).
has_twist(nursery_gym).
has_kindness(nursery_gym).
has_voice(nursery_gym).
gymnastic(gymnastic).
penalty(penalty).
kind_choice(nursery_gym).
safe_fix(nursery_gym) :- has_twist(nursery_gym), has_kindness(nursery_gym).
good_story(nursery_gym) :- safe_fix(nursery_gym), has_voice(nursery_gym).
"""


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
    friend: str
    prop: str
    coach: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    penalty: str
    clue: str
    dialogue: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = "nursery gym"
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

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
                f"  {entity.id:8} ({entity.kind:10}) {' '.join(bits)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


NAMES = ["Luna", "Milo", "Pip", "Nia", "Toby", "Uma", "Ziggy", "Mara"]
FRIENDS = ["Robin", "Daisy", "Bunny", "Theo", "Mimi", "Otis"]
PROPS = ["blue ribbon", "soft hoop", "yellow scarf", "silver star"]
COACHES = ["Miss Fern", "Coach Bea", "Auntie Rose", "Mr. Sol"]

SCENARIOS = [
    Scenario(
        key="ribbon_twist",
        opening="Luna practiced a bright ribbon dance beneath the morning sun.",
        trouble="On the grand twirl, the ribbon curled around her ankle and made her stop.",
        penalty="The bell rang a penalty for the missed finish, and Luna's cheeks grew pink.",
        clue="Her friend noticed that the ribbon was tied too tightly near the handle.",
        dialogue='"A penalty is a pause, not a name," said Robin. "May we try the knot?"',
        repair="Luna loosened the knot, lifted her foot slowly, and tried the twirl with a smaller twist.",
        result="The ribbon floated in a safe blue loop, and Luna finished with both feet steady.",
        ending="The ribbon made a sky-blue curl while every kind voice clapped in time.",
    ),
    Scenario(
        key="hoop_hop",
        opening="Luna lined up a soft hoop for a sunny gymnastic hop.",
        trouble="The hoop rolled sideways just as she leaped, so her careful landing became a wobble.",
        penalty="One red token marked a penalty beside her name.",
        clue="Daisy saw that one floor mat had folded up like a tiny hill.",
        dialogue='"The hoop did not make a bad dancer," Daisy said. "The mat needs help."',
        repair="They flattened the mat, set the hoop on its bright mark, and practiced the hop close to the floor.",
        result="This time the hoop stayed still, and Luna landed softly inside it.",
        ending="The yellow hoop rested on the flat mat like a little moon at noon.",
    ),
    Scenario(
        key="scarf_spin",
        opening="Luna raised a yellow scarf and began a slow gymnastic spin.",
        trouble="A gust pushed the scarf across the judge's card before the final pose.",
        penalty="The judge gave a gentle penalty for the hidden card, though no one was hurt.",
        clue="Milo heard the window tapping and saw that its latch had popped open.",
        dialogue='"Could we close the window before we blame the scarf?" Luna asked.',
        repair="Milo closed the latch, Luna held the scarf lower, and they repeated the spin with a careful pause.",
        result="The scarf dipped and rose without covering the card.",
        ending="The yellow scarf waved goodbye while the window gave a quiet click.",
    ),
    Scenario(
        key="star_balance",
        opening="Luna balanced a silver star on her palm before the nursery rhyme began.",
        trouble="The star slid when a loose floorboard gave a little squeak.",
        penalty="A penalty bead rolled onto the mat for the unsteady pose.",
        clue="Theo found a tiny pebble tucked beneath the edge of the board.",
        dialogue='"A small pebble can make a big wobble," Theo said. "Let us move it kindly."',
        repair="They lifted the board edge with a safe block, removed the pebble, and practiced the pose beside the mat.",
        result="The floor became quiet, and the silver star rested calmly on Luna's palm.",
        ending="The star shone still as a moon while the rhyme rang bright and clear.",
    ),
    Scenario(
        key="backward_bow",
        opening="Luna rehearsed a backward bow for the end of the gymnastic rhyme.",
        trouble="She twisted the wrong way and bumped a cushion, sending it tumbling.",
        penalty="The cushion earned no blame, but Luna received a penalty for stepping outside her line.",
        clue="Miss Fern saw that the line had faded beneath a patch of sunlight.",
        dialogue='"I could not see my path," Luna said. "Let us make it bright again."',
        repair="They placed two colorful blocks at the line's ends and practiced the bow facing the clear markers.",
        result="Luna found the path, turned safely, and bowed without a bump.",
        ending="Two blocks gleamed like friendly stars at the edges of her straight path.",
    ),
    Scenario(
        key="quiet_count",
        opening="Luna counted one, two, three before a quiet gymnastic leap.",
        trouble="The counting drum stopped mid-beat, and Luna jumped before her feet were ready.",
        penalty="A small penalty card appeared for the hurried leap.",
        clue="Otis found that the drum's bead had slipped beneath its cloth.",
        dialogue='"Your voice can be our drum," Otis said. "I will count, and you can listen."',
        repair="Otis counted in a steady voice while Luna bent her knees, waited, and leaped on the final word.",
        result="The leap rose smoothly because Luna knew exactly when to begin.",
        ending="Otis's voice kept the beat, and Luna's toes touched down like soft raindrops.",
    ),
    Scenario(
        key="matty_misstep",
        opening="Luna stepped onto a green mat to practice a cheerful side-step.",
        trouble="The mat slid a little, and her gymnastic twist ended in a surprised sit.",
        penalty="The teacher marked a penalty for leaving the safe center.",
        clue="Nia noticed two smooth spots beneath the mat where its grip had worn away.",
        dialogue='"We can fix the floor before we fix the footwork," Nia said.',
        repair="They placed a grippy square beneath the mat and marked a smaller practice space.",
        result="Luna side-stepped safely and kept her twist gentle.",
        ending="The green mat held firm while Luna danced a tiny victory step.",
    ),
    Scenario(
        key="voice_and_pose",
        opening="Luna prepared a pose while her voice led the nursery rhyme.",
        trouble="Her voice became so quiet that she missed the cue for the final turn.",
        penalty="The missed cue brought a penalty, and Luna lowered her eyes.",
        clue="Mara saw that the music stand hid the picture showing the next move.",
        dialogue='"Let the picture be seen," Mara said. "Your strong voice can guide us after that."',
        repair="They moved the stand, breathed together, and spoke the next line in a warm, clear voice.",
        result="Luna heard the cue, made the twist slowly, and held her pose.",
        ending="Her voice floated over the mat like a bright bird, and the final pose stayed still.",
    ),
]

OPENINGS = [
    "In the nursery gym, the morning bells went ding-ding-ding.",
    "Beside a row of soft mats, the nursery gym woke with a cheerful spring.",
    "The little gym was bright with ribbons, hoops, and welcoming smiles.",
    "When the sun peeped through the window, the nursery gym began its rhyme.",
]

COACH_LINES = [
    "The kindest champion looks first and hurries last.",
    "A careful twist is better than a speedy tumble.",
    "A penalty can point to a safer next step.",
    "Your voice may ask for help before your feet begin again.",
]

PRAISE = [
    "No one cheered because Luna was perfect; they cheered because she kept learning.",
    "The friends smiled at the safe choice more than at the score.",
    "The penalty card stayed on the bench while the new plan took center stage.",
    "Kindness made the gym feel wide enough for another try.",
]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The gymnast needs a name.")
    if params.friend not in FRIENDS:
        raise StoryError("The friend must be a gentle nursery-gym helper.")
    if params.prop not in PROPS:
        raise StoryError("The prop must be a safe, soft gymnastic object.")
    if params.coach not in COACHES:
        raise StoryError("The coach must be a familiar, caring grown-up.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "nursery_gym"),
            asp.fact("has_twist", "nursery_gym"),
            asp.fact("has_kindness", "nursery_gym"),
            asp.fact("has_voice", "nursery_gym"),
            asp.fact("gymnastic", "gymnastic"),
            asp.fact("penalty", "penalty"),
            asp.fact("kind_choice", "nursery_gym"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        friend=rng.choice(FRIENDS),
        prop=rng.choice(PROPS),
        coach=rng.choice(COACHES),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme gymnastic twist storyworld."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--prop", choices=PROPS)
    parser.add_argument("--coach", choices=COACHES)
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
    if args.friend:
        params.friend = args.friend
    if args.prop:
        params.prop = args.prop
    if args.coach:
        params.coach = args.coach
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    gymnast = world.add(Entity("gymnast", "character", params.name))
    friend = world.add(Entity("friend", "character", params.friend))
    prop = world.add(Entity("prop", "gymnastic prop", params.prop))
    coach = world.add(Entity("coach", "character", params.coach))
    penalty = world.add(Entity("penalty", "rule marker", "penalty"))
    world.facts.update(
        gymnast=gymnast,
        friend=friend,
        prop=prop,
        coach=coach,
        penalty=penalty,
        place="nursery gym",
        feature_twist=True,
        feature_kindness=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS)
    coach_line = rng.choice(COACH_LINES)
    praise = rng.choice(PRAISE)

    gymnast = world.get("gymnast")
    friend = world.get("friend")
    prop = world.get("prop")
    coach = world.get("coach")
    penalty = world.get("penalty")

    gymnast.bump_meme("courage")
    friend.bump_meme("kindness")
    prop.bump_meter("practice")

    world.say(f"{opening} {scenario.opening}")
    world.say(
        f"{gymnast.label} held the {prop.label}, while {friend.label} watched nearby "
        f"and {coach.label} kept a gentle eye on the rhyme."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(scenario.penalty)
    penalty.bump_meter("noticed")
    gymnast.bump_meme("worry")
    world.say(
        f"{gymnast.label} wanted to hide, but {coach.label} said, "
        f'"{coach_line}"'
    )
    world.para()

    world.say(f"Then came the clue: {scenario.clue}")
    world.say(scenario.dialogue)
    friend.bump_meme("helpfulness")
    gymnast.bump_meme("trust")
    world.say(
        f"{gymnast.label} listened to {friend.label}'s voice and chose a kinder plan."
    )
    world.para()

    world.say(f"Together they {scenario.repair}")
    prop.bump_meter("safe_use")
    gymnast.bump_meter("careful_attempt")
    world.say(scenario.result)
    world.para()

    world.say(praise)
    world.say(
        f"The penalty had pointed toward practice, not shame, and the gymnastic "
        f"twist became a safer turn."
    )
    world.say(scenario.ending)
    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        penalty=scenario.penalty,
        clue=scenario.clue,
        dialogue=scenario.dialogue,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved=True,
        voice_used=True,
        twist_safe=True,
        kindness_used=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        (
            f"Write a nursery-rhyme story where {facts['gymnast'].label} faces a "
            f"penalty after a gymnastic twist and receives kindness."
        ),
        (
            f"Tell a child-friendly story in a nursery gym using the words "
            f"penalty, voice, and gymnastic."
        ),
        (
            f"Write a gentle tale where {facts['friend'].label}'s voice helps "
            f"{facts['gymnast'].label} turn a twist into a safe new try."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    gymnast = facts["gymnast"].label
    friend = facts["friend"].label
    prop = facts["prop"].label
    return [
        QAItem(
            question="What went wrong during the gymnastic practice?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What penalty did {gymnast} receive?",
            answer=str(facts["penalty"]),
        ),
        QAItem(
            question=f"What clue did {friend} notice?",
            answer=f"{friend} noticed that {facts['clue']}",
        ),
        QAItem(
            question=f"How did the friends repair the problem with the {prop}?",
            answer=f"Together they {facts['repair']}",
        ),
        QAItem(
            question="How did kindness change the ending?",
            answer=(
                f"Kindness helped the gymnast try again safely: {facts['result']} "
                f"{facts['ending']}"
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a penalty?",
            answer=(
                "A penalty is a rule reminder or consequence given when a rule "
                "is missed; it should help someone learn what to do next."
            ),
        ),
        QAItem(
            question="What is a voice?",
            answer="A voice is the sound a person makes when speaking, singing, or calling.",
        ),
        QAItem(
            question="What does gymnastic mean?",
            answer=(
                "Gymnastic means using balance, strength, and careful body movements "
                "such as stretching, jumping, or turning."
            ),
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means caring about someone and helping in a gentle, respectful way.",
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


def dump_trace(world: World) -> str:
    return world.trace()


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show safe_fix/1.\n#show good_story/1.\n#show gymnastic/1.\n#show penalty/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(
            argument.name
            if argument.type != 4
            else argument.string
            for argument in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"safe_fix", "good_story", "gymnastic", "penalty"}
    }
    expected = {
        ("safe_fix", ("nursery_gym",)),
        ("good_story", ("nursery_gym",)),
        ("gymnastic", ("gymnastic",)),
        ("penalty", ("penalty",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reasonableness gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    rng = random.Random(19)
    for _ in range(5):
        sample = generate(valid_params(rng))
        if not sample.story or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story was not resolved.")
            return 1
    print("OK: ASP twin matches the Python gate and generated stories resolve.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(asp.atoms(model, "good_story"))


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


CURATED = [
    StoryParams("Luna", "Robin", "blue ribbon", "Miss Fern", 11),
    StoryParams("Milo", "Daisy", "soft hoop", "Coach Bea", 29),
    StoryParams("Nia", "Theo", "yellow scarf", "Auntie Rose", 47),
]


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible nursery-gym stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(0, args.n) and attempts < max(50, args.n * 50):
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
