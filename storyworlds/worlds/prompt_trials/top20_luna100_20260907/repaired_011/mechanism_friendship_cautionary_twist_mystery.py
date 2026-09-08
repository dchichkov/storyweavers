#!/usr/bin/env python3
"""
A small mystery storyworld about friendship, a strange mechanism, and a careful twist.

Seed premise:
A child and a friend discover a mysterious box with a clever mechanism. Their
friendship helps them investigate, but a cautionary clue reminds them not to
force what they do not understand. The twist reveals that the mystery was a
carefully hidden message meant to teach them patience.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    keeper: str
    object_name: str
    clue_material: str
    mechanism: int = 0
    mystery: int = 0
    friendship: int = 0
    caution: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


NAMES = ["Luna", "Milo", "Nia", "Theo", "Ivy", "Jasper", "Mina", "Owen"]
FRIENDS = ["Suri", "Pip", "Rae", "Toby", "Zara", "Finn", "Bea", "Noah"]
KEEPERS = ["Grandma Jo", "Mr. Vale", "Aunt May", "Ms. Rowan"]
OBJECTS = ["a brass puzzle box", "a wooden music box", "a silver compass case", "a clockwork locket"]
MATERIALS = ["blue thread", "a red paper star", "a green glass bead", "a strip of yellow ribbon"]


MECHANISMS = [
    {
        "lead": "The box had a round dial, three tiny teeth, and a copper pin that clicked when touched.",
        "clue": "A faint line ran from the dial to a picture of a moon.",
        "action": "They turned the dial together, one click at a time, while the other hand stayed away from the sharp-looking pin.",
        "result": "the moon-shaped latch opened with a gentle pop",
        "cause": "the dial and moon picture formed a careful three-step mechanism",
        "deed": "turned the dial slowly instead of forcing the latch",
    },
    {
        "lead": "The music box held a row of little windows, each showing a different star.",
        "clue": "Only the stars with one bright dot had a tiny mark beneath them.",
        "action": "They counted the marked stars and pressed them in order, stopping whenever the springs creaked.",
        "result": "a hidden drawer slid out beneath the melody",
        "cause": "the marked stars showed the safe order for the spring mechanism",
        "deed": "followed the marked order and stopped when the springs creaked",
    },
    {
        "lead": "The compass case had a needle that pointed everywhere except north.",
        "clue": "A little arrow was scratched beside the word 'home.'",
        "action": "They placed the case on the flat table and followed the arrow rather than tugging the restless needle.",
        "result": "the case clicked open toward the arrow",
        "cause": "the scratched arrow, not the wandering needle, revealed the release",
        "deed": "trusted the clear arrow and kept the case flat",
    },
    {
        "lead": "The locket had two halves that looked identical, except one had a nearly invisible notch.",
        "clue": "The notch lined up with a painted crescent on the other half.",
        "action": "They matched the notch and crescent, then squeezed gently with both thumbs.",
        "result": "the locket opened without a single snap or scratch",
        "cause": "the notch and crescent made a safe alignment mechanism",
        "deed": "matched the marks before pressing the locket",
    },
    {
        "lead": "Under the lid was a tiny lever and a row of holes that looked like a miniature flute.",
        "clue": "The dust around two holes was fresh, as if someone had touched them recently.",
        "action": "They pressed only those two holes, then waited instead of poking the lever.",
        "result": "a secret panel rose from the bottom",
        "cause": "the two clean holes indicated the mechanism's correct signal",
        "deed": "used the clean marks and left the tempting lever alone",
    },
    {
        "lead": "The box carried a brass wheel with four colored wedges and a button shaped like an eye.",
        "clue": "The eye button was scratched, but the blue wedge was clean.",
        "action": "They rotated the clean blue wedge to the top and watched for a second clue before touching the button.",
        "result": "the wheel released a folded message",
        "cause": "the clean wedge marked the starting position of the wheel",
        "deed": "looked for the clean starting mark before pressing anything",
    },
]

MYSTERIES = [
    {
        "opening": "{name} and {friend} found {object_name} beneath a loose floorboard in the old reading room.",
        "question": "Why had someone hidden such a careful object where dust covered every corner?",
        "sound": "From inside came three soft clicks, then complete silence.",
    },
    {
        "opening": "Rain tapped the library windows when {name} and {friend} noticed {object_name} on a shelf that had been empty that morning.",
        "question": "Who had placed it there, and why did its shadow point toward the locked map cabinet?",
        "sound": "When {name} brushed away the dust, something inside answered with a tiny tick.",
    },
    {
        "opening": "{name} brought {friend} to the attic after finding {object_name} inside an old coat pocket.",
        "question": "The coat had belonged to someone long ago, so what secret could still be waiting in its pocket?",
        "sound": "A hidden spring gave one shiver, like a mouse holding its breath.",
    },
    {
        "opening": "At the community garden, {name} and {friend} discovered {object_name} beneath a stone marked with a crescent.",
        "question": "The crescent appeared on the box too, but no one knew whether it was a warning or an invitation.",
        "sound": "The box made a hollow knock whenever the wind passed over it.",
    },
    {
        "opening": "{name} and {friend} were sorting donations when {object_name} slipped from a bundle of old blankets.",
        "question": "No label named its owner, yet a fresh scratch curved across the lid like a secret signature.",
        "sound": "A small inner wheel turned once and then stopped.",
    },
    {
        "opening": "In the school greenhouse, {name} and {friend} found {object_name} beside a dry flowerpot.",
        "question": "The box seemed too polished to be forgotten, but nobody had seen it before.",
        "sound": "A faint bell rang inside when the sunlight touched its lid.",
    },
]

FRIENDSHIP_LINES = [
    "'We can solve it together,' said {friend}. '{name}, you watch the clues, and I will watch our hands.'",
    "'If you get worried, tell me,' said {name}. {friend} nodded. 'And if I rush, remind me to slow down.'",
    "{friend} whispered, 'A real mystery needs two kinds of noticing.' 'What kinds?' asked {name}. 'The clue kind and the friend kind.'",
    "'Do not pull yet,' said {name}. 'Good catch,' replied {friend}. 'You protect the box, and I will protect our curiosity.'",
    "{name} asked, 'Do you still want to keep looking?' {friend} smiled. 'Yes, but only if we look carefully together.'",
    "'Promise we will leave it alone if it seems unsafe,' said {friend}. 'Promise,' said {name}. Their agreement made the dark room feel smaller.",
]

CAUTIONARY_LINES = [
    "A note under the lid warned, 'A mystery is not an excuse to be careless.'",
    "The keeper had once said, 'When a mechanism resists, listen before you push.'",
    "A red mark beside the latch looked less like decoration and more like a quiet stop sign.",
    "They remembered the simplest rule of old objects: do not force a part that may break or spring free.",
    "The dust showed that the box had waited a long time, so they decided its secret could wait one more careful minute.",
    "The safest clue was the one that told them what not to touch.",
]

TWISTS = [
    "Inside the drawer lay {clue_material} wrapped around a note: 'For the friends who can wait. Look beneath the moonstone.'",
    "The secret panel held a tiny drawing of two children sharing a lantern, signed by {keeper}.",
    "The folded message was not a treasure map at all. It was a recipe for returning the box to the person who had lost it.",
    "Behind the mechanism was a picture of the reading room from years ago, with the same two friends standing beside the hidden floorboard.",
    "The box contained a list of names and a final line: 'The finder who works kindly with a friend may add a name.'",
    "The inner lid revealed a mirror. Beneath it, a note said, 'The mystery was never the box. It was whether you would care for it together.'",
]

ENDINGS = [
    "{keeper} recognized the box and explained that it had belonged to a patient puzzle-maker. {name} and {friend} returned it safely, but kept the lesson about careful teamwork.",
    "They placed the message in the community display, where other children could read it without touching the mechanism. The box rested behind glass, quiet and mysterious again.",
    "Before leaving, {name} and {friend} drew a small moon and two linked hands on their notebook. The mystery had ended, but their promise to help each other had begun.",
    "The rain stopped as they carried the box to {keeper}. A pale moon appeared in the window, just like the mark that had guided their patient hands.",
    "They never learned every detail about the box's first owner. That was all right. Some mysteries become warmer when friends solve only the part they are ready to understand.",
    "The box clicked shut for the night. This time the sound did not feel like a warning; it sounded like a small thank-you.",
]


REGISTRIES = {
    "name": NAMES,
    "friend": FRIENDS,
    "keeper": KEEPERS,
    "object_name": OBJECTS,
    "clue_material": MATERIALS,
}

ASP_RULES = r"""
#show valid/6.
#show valid_story/8.

name(N) :- name_value(N).
friend(F) :- friend_value(F).
keeper(K) :- keeper_value(K).
object_name(O) :- object_value(O).
material(M) :- material_value(M).
mechanism(I) :- mechanism_value(I).
mystery(I) :- mystery_value(I).

valid(N,F,K,O,M,I) :-
    name_value(N),
    friend_value(F),
    keeper_value(K),
    object_value(O),
    material_value(M),
    mechanism_value(I).

valid_story(N,F,K,O,M,I,X,Y) :-
    valid(N,F,K,O,M,I),
    mystery_value(X),
    ending_value(Y).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in NAMES:
        lines.append(asp.fact("name_value", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend_value", value))
    for value in KEEPERS:
        lines.append(asp.fact("keeper_value", value))
    for value in OBJECTS:
        lines.append(asp.fact("object_value", value))
    for value in MATERIALS:
        lines.append(asp.fact("material_value", value))
    for index in range(len(MECHANISMS)):
        lines.append(asp.fact("mechanism_value", index))
    for index in range(len(MYSTERIES)):
        lines.append(asp.fact("mystery_value", index))
    for index in range(len(ENDINGS)):
        lines.append(asp.fact("ending_value", index))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/6.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combinations() -> list[tuple[str, str, str, str, str, int]]:
    return [
        (name, friend, keeper, object_name, material, index)
        for name in NAMES
        for friend in FRIENDS
        for keeper in KEEPERS
        for object_name in OBJECTS
        for material in MATERIALS
        for index in range(len(MECHANISMS))
    ]


def asp_valid_count() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
    return len(asp.atoms(model, "valid"))


def asp_verify() -> int:
    expected = len(valid_combinations())
    actual = asp_valid_count()
    if expected == actual:
        print(f"OK: clingo gate matches Python valid_combinations() ({expected} combinations).")
        return 0
    print(f"MISMATCH: Python has {expected} combinations but clingo has {actual}.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about a mechanism, friendship, caution, and a twist."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("--object-name", dest="object_name", choices=OBJECTS)
    parser.add_argument("--clue-material", dest="clue_material", choices=MATERIALS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        keeper=args.keeper or rng.choice(KEEPERS),
        object_name=args.object_name or rng.choice(OBJECTS),
        clue_material=args.clue_material or rng.choice(MATERIALS),
        mechanism=rng.randrange(len(MECHANISMS)),
        mystery=rng.randrange(len(MYSTERIES)),
        friendship=rng.randrange(len(FRIENDSHIP_LINES)),
        caution=rng.randrange(len(CAUTIONARY_LINES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.mechanism = seed % len(MECHANISMS)
    params.mystery = (seed // len(MECHANISMS)) % len(MYSTERIES)
    params.friendship = (seed // 3) % len(FRIENDSHIP_LINES)
    params.caution = (seed // 5) % len(CAUTIONARY_LINES)
    params.ending = (seed // 7) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    mechanism = MECHANISMS[params.mechanism % len(MECHANISMS)]
    mystery = MYSTERIES[params.mystery % len(MYSTERIES)]

    values = {
        "name": params.name,
        "friend": params.friend,
        "keeper": params.keeper,
        "object_name": params.object_name,
        "clue_material": params.clue_material,
    }

    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            label=params.name,
            memes={"curiosity": 0.0, "confidence": 0.0},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            label=params.friend,
            memes={"trust": 0.0, "caution": 0.0},
        )
    )
    keeper = world.add(Entity(id="keeper", kind="character", label=params.keeper))
    box = world.add(
        Entity(
            id="mechanism",
            kind="object",
            label=params.object_name,
            meters={"spring_tension": 0.0, "latch_open": 0.0},
            memes={"mystery": 1.0},
        )
    )

    world.say(mystery["opening"].format(**values))
    world.say(mystery["question"])
    world.say(mystery["sound"])
    world.say(mechanism["lead"])

    world.para()
    box.meters["spring_tension"] = 1.0
    child.memes["curiosity"] = 1.0
    friend.memes["trust"] = 1.0
    world.say(mystery["sound"])
    world.say(mechanism["clue"])
    world.say(FRIENDSHIP_LINES[params.friendship % len(FRIENDSHIP_LINES)].format(**values))
    world.say(CAUTIONARY_LINES[params.caution % len(CAUTIONARY_LINES)].format(**values))

    world.para()
    child.memes["confidence"] = 1.0
    friend.memes["caution"] = 1.0
    world.say(mechanism["action"])
    world.say(f"They listened for the next click. {mechanism['result'].capitalize()}.")
    world.say(TWISTS[params.mechanism % len(TWISTS)].format(**values))

    world.para()
    box.meters["spring_tension"] = 0.0
    box.meters["latch_open"] = 1.0
    box.memes["mystery"] = 0.0
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        investigator=params.name,
        friend=params.friend,
        keeper=params.keeper,
        object_name=params.object_name,
        clue_material=params.clue_material,
        mechanism=params.mechanism % len(MECHANISMS),
        mystery=params.mystery % len(MYSTERIES),
        cause=mechanism["cause"],
        helpful_action=mechanism["deed"],
        result=mechanism["result"],
        caution_used=True,
        friendship_used=True,
        twist_revealed=True,
        resolved=True,
    )

    prompts = [
        "Write a child-friendly mystery about two friends who discover a strange mechanism and solve it carefully.",
        f"Tell a cautionary friendship story in which {params.name} and {params.friend} investigate {params.object_name} without forcing it.",
        f"Write a mystery with a mechanism, a spoken exchange, a careful choice, and a twist that changes what the children think the object is.",
    ]

    story_qa = [
        QAItem(
            question="Who discovered the mysterious object?",
            answer=f"{params.name} and {params.friend} discovered {params.object_name} and investigated it together.",
        ),
        QAItem(
            question="What made the object mysterious?",
            answer=f"It had a hidden mechanism: {mechanism['cause']}. Its clicks and unusual clues made the friends wonder who had made it.",
        ),
        QAItem(
            question="How did friendship help solve the mystery?",
            answer=f"{params.name} and {params.friend} shared jobs, spoke honestly, and reminded each other to stay calm and careful.",
        ),
        QAItem(
            question="What caution did the friends follow?",
            answer=f"They did not force the object. They {mechanism['deed']}, which let the mechanism open safely.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the hidden message was not simply treasure. It showed that the object had been prepared to reward patience, kindness, and teamwork.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The mechanism opened safely, its message was understood, and {params.name} and {params.friend} left with a stronger friendship and a useful lesson.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, close, or perform a task.",
        ),
        QAItem(
            question="Why should someone avoid forcing an unfamiliar mechanism?",
            answer="Forcing an unfamiliar mechanism can break it or make a spring, sharp part, or loose piece move unexpectedly.",
        ),
        QAItem(
            question="What makes a mystery story interesting?",
            answer="A mystery story gives readers clues and questions, then reveals information that helps explain what happened.",
        ),
        QAItem(
            question="How can friends investigate safely?",
            answer="Friends can share observations, speak up when something seems risky, and agree to slow down instead of rushing.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or readers believe, often caused by a new clue or discovery.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(parts)}")
    if world.facts:
        lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            name="Luna",
            friend="Suri",
            keeper="Grandma Jo",
            object_name="a brass puzzle box",
            clue_material="blue thread",
            mechanism=0,
            mystery=0,
            friendship=0,
            caution=0,
            ending=0,
        ),
        StoryParams(
            name="Milo",
            friend="Pip",
            keeper="Mr. Vale",
            object_name="a wooden music box",
            clue_material="a red paper star",
            mechanism=1,
            mystery=1,
            friendship=1,
            caution=1,
            ending=1,
        ),
        StoryParams(
            name="Nia",
            friend="Rae",
            keeper="Aunt May",
            object_name="a silver compass case",
            clue_material="a green glass bead",
            mechanism=2,
            mystery=2,
            friendship=2,
            caution=2,
            ending=2,
        ),
        StoryParams(
            name="Theo",
            friend="Toby",
            keeper="Ms. Rowan",
            object_name="a clockwork locket",
            clue_material="a strip of yellow ribbon",
            mechanism=3,
            mystery=3,
            friendship=3,
            caution=3,
            ending=3,
        ),
    ]


CURATED = build_curated()


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


def verify_generated() -> int:
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("FAIL: generated an empty story.")
            return 1
        required = [params.name, params.friend, "mechanism", "friend"]
        for word in required:
            if word.lower() not in sample.story.lower():
                print(f"FAIL: generated story is missing required concept {word!r}.")
                return 1
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
            print("FAIL: generated QA sets are incomplete.")
            return 1
    print(f"OK: verified {len(CURATED)} generated stories.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/8."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            raise SystemExit(status)
        raise SystemExit(verify_generated())

    if args.asp:
        count = asp_valid_count()
        print(f"{count} compatible registry combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: the {sample.params.object_name}"
        elif len(samples) > 1:
            header = f"### mystery variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
