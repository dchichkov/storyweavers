#!/usr/bin/env python3
"""
A standalone Storyweavers world about a small everyday mystery.

Premise:
- Luna helps prepare a quiet community reading room.
- A strange ping comes from a wooden shelf, and a structural crack worries her.
- A small mystery must be solved before anyone uses the shelf.
- Courage means speaking up, checking carefully, and asking for help.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THEME = "a neighborhood reading room"
SEED_WORDS = {"structural", "ping", "shuck"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("loose", "weight", "crack", "noise", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "bravery", "curiosity", "trust", "relief", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Mara"
    caretaker: str = "Mr. Sol"
    case: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    book: str
    object_name: str
    first_sound: str
    false_lead: str
    clue: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


CASES = [
    Case(
        book="a blue book about tide pools",
        object_name="a brass bookmark",
        first_sound="a bright ping came from the long wooden shelf",
        false_lead="a jar of buttons had rolled near the reading rug",
        clue="a clean scrape on the shelf's lower rail and a silver glint beneath it",
        discovery="slid a ruler beneath the rail and found the brass bookmark wedged in the back corner",
        cause="had placed the bookmark on the shelf while dusting, and a loose board pushed it backward",
        repair="moved the books away, braced the shelf, and put the bookmark in a labeled cup",
        proof="the shelf stood level and stayed quiet when an empty box was placed on it",
        lesson="Bravery can be a calm choice to report danger before trying to fix it alone.",
        ending="The blue tide-pool book opened on the table, with the brass bookmark shining beside it.",
    ),
    Case(
        book="a book of simple garden poems",
        object_name="a tiny silver bell",
        first_sound="one clear ping rang behind the bookcase",
        false_lead="a bicycle bell outside answered through the open window",
        clue="a crescent of dust on the floor and a fresh chip beside the shelf's upright post",
        discovery="looked behind the lowest row and found the silver bell caught between the post and the wall",
        cause="had nudged the bookcase while reaching for a high book, then heard the bell and stepped away",
        repair="asked the caretaker to inspect the structural joint, shifted the heavy books down, and hung the bell safely",
        proof="the joint held firm and the bell rang only when someone touched its ribbon",
        lesson="A mystery becomes safer when guesses wait for evidence.",
        ending="A garden poem rested in the sunlight, and the little bell waited quietly for the next reader.",
    ),
    Case(
        book="a picture book about a traveling fox",
        object_name="a red library card",
        first_sound="a soft ping tapped through the shelf like a spoon on glass",
        false_lead="the radiator clicked in the same corner",
        clue="a red corner beneath the shelf and a hairline structural crack in the side panel",
        discovery="used a flashlight and found the library card under the cracked side panel",
        cause="had pushed the card into the shelf while shucking peas from a snack cup and forgotten it there",
        repair="stopped the shelf from carrying weight, told the caretaker, and moved the card to the desk",
        proof="the panel was replaced before books returned, and the card was dry and unbent",
        lesson="Telling the truth about a small accident helps everyone solve the larger problem.",
        ending="The traveling fox began its journey from a safe shelf, while Luna kept the repaired card close at hand.",
    ),
    Case(
        book="a slim cookbook for rainy afternoons",
        object_name="a wooden puzzle piece",
        first_sound="a sharp ping sounded whenever the shelf gave a tiny shiver",
        false_lead="a spoon in the tea tin made a similar sound",
        clue="a triangular gap in the puzzle and a pale line running along the shelf's back",
        discovery="lifted the bottom board with the caretaker and found the puzzle piece inside",
        cause="had shucked a pea pod over the puzzle tray, bumped the shelf, and swept the piece into the gap",
        repair="sealed the gap, sorted the puzzle pieces, and placed the snack bowl far from the books",
        proof="the complete puzzle showed a rainy kitchen and the shelf no longer shivered",
        lesson="Careful habits protect both objects and people.",
        ending="Rain tapped the window while the finished puzzle showed a bright kitchen beside the cookbook.",
    ),
]


@dataclass
class World:
    luna: Entity
    helper: Entity
    caretaker: Entity
    shelf: Entity
    mystery_object: Entity
    book: Entity
    room: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_world(params: StoryParams, case: Case) -> World:
    luna = Entity(params.name, "character", "child", params.name, location="reading_room")
    helper = Entity(params.helper, "character", "child", params.helper, location="reading_room")
    caretaker = Entity(params.caretaker, "character", "adult", params.caretaker, location="reading_room")
    shelf = Entity("shelf", "structure", "bookcase", "the wooden shelf", location="reading_room")
    mystery_object = Entity("mystery_object", "object", "clue", case.object_name, location="unknown")
    book = Entity("book", "object", "book", case.book, location="shelf")
    room = Entity("room", "place", "room", THEME, location="reading_room")
    return World(luna, helper, caretaker, shelf, mystery_object, book, room)


def tell(params: StoryParams) -> World:
    case = CASES[params.case % len(CASES)]
    world = build_world(params, case)
    luna, helper, caretaker = world.luna, world.helper, world.caretaker
    shelf, obj, book = world.shelf, world.mystery_object, world.book

    luna.memes["worry"] = 1
    luna.memes["curiosity"] = 1
    shelf.meters["crack"] = 1
    shelf.meters["loose"] = 1
    obj.meters["noise"] = 1

    openings = [
        f"Before the afternoon readers arrived, {luna.id} was helping {helper.id} tidy {THEME}.",
        f"The reading room was quiet except for turning pages as {luna.id} and {helper.id} prepared the shelves.",
        f"{luna.id} carried {case.book} to the wooden shelf while {helper.id} straightened the reading rug.",
        f"On an ordinary library afternoon, {luna.id} noticed that one shelf looked different from the others.",
    ]
    world.say(openings[params.opening % len(openings)])
    world.say(f"Then {case.first_sound}. A thin structural crack showed near its side, and the shelf trembled.")
    world.say(f"The missing {case.object_name} turned the odd sound into a mystery to solve.")

    world.para()
    world.say(f"{case.false_lead}, but {case.clue}.")
    luna.memes["bravery"] += 1
    world.say(
        f"{luna.id} took one step back. 'I feel nervous, but I should not climb or pull at a damaged shelf,' "
        f"{luna.id} said."
    )
    dialogue = [
        f"'{helper.id}, will you keep people away while I call {caretaker.id}?' {luna.id} asked. "
        f"'Yes,' said {helper.id}. 'We can investigate without touching the weak part.'",
        f"'Could the ping be outside?' {helper.id} asked. 'Maybe,' said {luna.id}, 'but the crack and the dust are inside. Let's check the safest clue first.'",
        f"{caretaker.id} came over. 'What did you notice?' the caretaker asked. '{case.clue},' {luna.id} replied. 'I want help before we move anything.'",
        f"'I found a sound, not an answer,' said {luna.id}. {helper.id} nodded. 'Then we will look for what the sound could have touched.'",
    ]
    world.say(dialogue[params.dialogue % len(dialogue)])
    world.say(f"They placed a chair in front of the shelf and moved readers to the other side of the room.")

    world.para()
    world.say(
        f"{caretaker.id} examined the shelf while {luna.id} and {helper.id} compared the two clues. "
        "The outside sound explained the false lead, but it did not explain the crack."
    )
    world.say(f"Together, they {case.discovery}.")
    obj.location = "shelf_gap"
    shelf.meters["loose"] = 0
    shelf.meters["safe"] = 1
    luna.memes["relief"] += 1
    world.say(
        f"{luna.id} looked surprised. 'So the ping came from the hidden object moving against the shelf,' "
        f"{luna.id} said. '{case.cause.capitalize()}.''"
    )
    world.say(
        f"{caretaker.id} answered, 'That is our explanation, and we will still repair the shelf before using it.'"
    )

    world.para()
    shelf.meters["crack"] = 0
    world.say(f"The three of them {case.repair}.")
    world.say(f"They tested the result: {case.proof}.")
    luna.memes["bravery"] += 1
    luna.memes["trust"] += 1
    helper.memes["trust"] += 1
    caretaker.memes["trust"] += 1
    world.say(
        f"{luna.id} felt proud, not because the mystery had been scary, but because bravery had meant "
        "speaking clearly and accepting careful help."
    )
    world.say(f"They remembered: {case.lesson}")

    world.para()
    endings = [
        case.ending,
        f"After that, readers returned one at a time. {case.ending}",
        f"The room became ordinary again, in the best way. {case.ending}",
        f"{helper.id} gave {luna.id} a quiet thumbs-up. {case.ending}",
    ]
    world.say(endings[params.ending % len(endings)])

    world.facts.update(
        case=case,
        clue=case.clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    luna = world.luna.id
    helper = world.helper.id
    caretaker = world.caretaker.id
    return [
        QAItem(
            question="What mystery did Luna and her helpers need to solve?",
            answer=f"They needed to explain the ping and find the missing {case.object_name} without using the shelf while its structural crack was unsafe.",
        ),
        QAItem(
            question="What clue mattered more than the false lead?",
            answer=f"The useful clue was {case.clue}. It connected the sound and the shelf to the hidden object.",
        ),
        QAItem(
            question="What caused the strange ping?",
            answer=f"The cause was that {case.cause}. The object moved against the shelf and made the ping.",
        ),
        QAItem(
            question="How did Luna show bravery?",
            answer=f"{luna} showed bravery by stepping back from the damaged shelf, describing what she saw, and asking {caretaker} for help instead of guessing or climbing.",
        ),
        QAItem(
            question="How did the group prove the problem was fixed?",
            answer=f"They {case.repair}. Then they checked that {case.proof}.",
        ),
        QAItem(
            question="What did Luna learn?",
            answer=f"She learned that {case.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does structural mean?",
            answer="Structural means connected to the parts that support or hold up a building, shelf, bridge, or other object.",
        ),
        QAItem(
            question="What is a ping?",
            answer="A ping is a short, clear sound, like a small metal object tapping glass or wood.",
        ),
        QAItem(
            question="What does shuck mean?",
            answer="To shuck something means to remove its outer shell or husk, such as taking a pea from its pod or an ear of corn from its husk.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the safe and right thing even when you feel worried or afraid.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question or puzzling event that people investigate by collecting clues and testing explanations.",
        ),
        QAItem(
            question="Why should people avoid a damaged shelf?",
            answer="A damaged shelf may fall or drop objects, so people should keep away and ask a responsible adult to inspect it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    return [
        f"Write a child-friendly slice-of-life mystery in {THEME} about a strange ping, a structural crack, and a missing {case.object_name}.",
        "Show bravery as speaking up, pausing, and asking for safe help rather than taking a reckless risk.",
        "Use the words structural, ping, and shuck naturally, and end with a concrete image proving the shelf is safe.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [
        world.luna,
        world.helper,
        world.caretaker,
        world.shelf,
        world.mystery_object,
        world.book,
        world.room,
    ]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:15} kind={entity.kind:10} location={entity.location!s:12} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(reading_room).
feature(reading_room, structural).
feature(reading_room, ping).
feature(reading_room, shuck).
theme(reading_room, bravery).
theme(reading_room, mystery_to_solve).

valid_story(S) :-
    setting(S),
    feature(S, structural),
    feature(S, ping),
    feature(S, shuck),
    theme(S, bravery),
    theme(S, mystery_to_solve).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "reading_room"),
            asp.fact("feature", "reading_room", "structural"),
            asp.fact("feature", "reading_room", "ping"),
            asp.fact("feature", "reading_room", "shuck"),
            asp.fact("theme", "reading_room", "bravery"),
            asp.fact("theme", "reading_room", "mystery_to_solve"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = any(atom.name == "valid_story" for atom in models)
    if not asp_ok:
        print("MISMATCH: ASP rules rejected the story domain.")
        return 1

    for index in range(len(CASES)):
        params = StoryParams(case=index, seed=index)
        sample = generate(params)
        required = ("structural", "ping", "shuck", "bravery", "mystery")
        if not all(word in sample.story.lower() for word in required):
            print(f"MISMATCH: generated case {index} lacks required narrative evidence.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print(f"MISMATCH: generated case {index} did not resolve.")
            return 1

    print("OK: ASP and Python recognize the repaired reading-room mystery domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a slice-of-life structural ping mystery."
    )
    parser.add_argument("--name", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--caretaker", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    name = args.name or rng.choice(["Luna", "Nia", "Sora", "Mina"])
    helper = args.helper or rng.choice(["Mara", "Tess", "Ivo", "June"])
    caretaker = args.caretaker or rng.choice(["Mr. Sol", "Ms. Vale", "Aunt Bea"])
    if name == helper:
        raise StoryError("The child and helper must have different names.")
    if caretaker in {name, helper}:
        raise StoryError("The caretaker must be different from the children.")
    offset = sample_seed - base_seed
    return StoryParams(
        name=name,
        helper=helper,
        caretaker=caretaker,
        case=offset % len(CASES),
        opening=(offset // len(CASES)) % 4,
        dialogue=(offset // (len(CASES) * 4)) % 4,
        ending=(offset // (len(CASES) * 4 * 4)) % 4,
        seed=sample_seed,
    )


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


CURATED = [
    StoryParams(name="Luna", helper="Mara", caretaker="Mr. Sol", case=0, seed=0),
    StoryParams(name="Nia", helper="Tess", caretaker="Ms. Vale", case=1, seed=1),
    StoryParams(name="Sora", helper="Ivo", caretaker="Aunt Bea", case=2, seed=2),
    StoryParams(name="Mina", helper="June", caretaker="Mr. Sol", case=3, seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
