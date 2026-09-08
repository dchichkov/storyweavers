#!/usr/bin/env python3
"""
A small slice-of-life rhyme about Wend's ordinary quest and a gentle bad ending.

Wend is a child who sets out to bring a warm slice of pie to a neighbor. The
quest is simple, but a hurried choice lets the slice fall. The ending is sad,
not dangerous: Wend returns with an empty plate, then learns that care matters
even on a little errand.
"""

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
    location: str = ""
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("warmth", "crumbs", "wobble", "sad", "care", "hurry", "hope"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Quest:
    key: str
    errand: str
    object_phrase: str
    destination: str
    first_line: str
    trouble: str
    clue: str
    careful_action: str
    consequence: str
    ending_image: str
    lesson: str
    sound: str


@dataclass
class StoryParams:
    name: str = "Wend"
    quest: str = "pie"
    rhyme_mode: str = "couplet"
    seed: Optional[int] = None
    variation: int = 0


QUESTS = [
    Quest(
        "pie",
        "carry a warm slice of pie to a neighbor",
        "a warm slice of apple pie",
        "Mara's blue door",
        "Wend had one small job before the afternoon grew cold.",
        "the path crossed a puddle, and Wend hurried while holding the plate in one hand",
        "the plate was safest when two hands held it level",
        "Wend stopped, used both hands, and stepped around the shining puddle",
        "Before Wend could turn, one shoe splashed and the slice slid into the mud.",
        "At Mara's blue door, an empty plate cooled beside a muddy shoe.",
        "A small kindness still deserves slow, careful hands.",
        "splash-skip-plop",
    ),
    Quest(
        "book",
        "return a picture book to the little library",
        "a picture book with a red kite on its cover",
        "the corner library box",
        "Wend had borrowed one book and promised to bring it back.",
        "a gusty corner made the loose pages flutter while Wend hurried",
        "the book needed its ribbon tied before it went outside",
        "Wend caught the pages and tied the ribbon, but a wet leaf stuck to the cover",
        "The book came home with a torn corner, so story hour had to wait.",
        "A red kite on the cover rested under a cloth while the glue dried.",
        "Returning something kindly means protecting it all the way.",
        "flap-flip-rip",
    ),
    Quest(
        "scarf",
        "take a knitted scarf to a chilly friend",
        "a long green knitted scarf",
        "Ivo's front step",
        "Wend heard a cough and chose a scarf from the hall basket.",
        "the scarf caught on a gate when Wend rushed to beat the evening wind",
        "the loose loop had to be lifted over the gate, not pulled",
        "Wend freed the loop, yet one bright thread had already snapped",
        "The scarf reached Ivo, but its warmest stripe hung loose.",
        "A green scarf lay across the step with one thread trailing like grass.",
        "Good help should arrive with patience, not just speed.",
        "tug-twang-snap",
    ),
    Quest(
        "seedling",
        "carry a bean seedling to the sunny window",
        "a tiny bean seedling in a clay cup",
        "the sunny kitchen window",
        "Wend was trusted with a green beginning.",
        "a rolling marble bumped the cup when Wend tried to take a shortcut",
        "the cup needed a steady path along the wall",
        "Wend caught it, but the stem bent before the plant reached the light",
        "The seedling survived, though its first leaf never opened.",
        "A bent little plant leaned toward a bright window in a quiet room.",
        "Living things need steady care during even a short quest.",
        "roll-rattle-flop",
    ),
    Quest(
        "button",
        "bring a blue button to a grandmother's sewing basket",
        "a bright blue button in a paper fold",
        "the sewing basket by the lamp",
        "Wend carried a tiny treasure for a coat that needed mending.",
        "the paper fold opened when Wend ran down the hall",
        "a button traveled safely inside a closed tin",
        "Wend searched beneath the bench, but the button had rolled into a crack",
        "The coat stayed open, and the missing button could not be sewn on.",
        "A blue thread waited beside an empty place on the coat.",
        "Tiny things deserve a safe pocket and an unhurried trip.",
        "tick-tick-roll",
    ),
]

RHYME_MODES = ["couplet", "counting", "soft", "echo", "ordinary"]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def quest_for(key: str) -> Quest:
    for quest in QUESTS:
        if quest.key == key:
            return quest
    raise StoryError(f"Unknown quest: {key}")


def setup_world(params: StoryParams) -> World:
    quest = quest_for(params.quest)
    world = World(params)
    world.add(Entity("wend", "character", params.name, "home"))
    world.add(Entity("neighbor", "character", "Mara", quest.destination))
    world.add(Entity("quest_object", "thing", quest.object_phrase, "kitchen"))
    world.add(Entity("plate", "thing", "a little plate", "kitchen"))
    world.facts["quest"] = quest
    return world


def tell_story(world: World) -> None:
    quest: Quest = world.facts["quest"]
    wend = world.entities["wend"]
    obj = world.entities["quest_object"]
    plate = world.entities["plate"]
    rng = random.Random(world.params.variation)

    openings = [
        f"{quest.first_line} {world.params.name} was Wend, and the day was plain and bright.",
        f"Wend woke to a small errand: {quest.errand}.",
        f"After lunch, Wend found a quiet job waiting by the door.",
    ]
    transitions = [
        f'"I can do it," said Wend. "I will {quest.errand}."',
        f'"Will you help me?" asked Mara from the doorway. Wend nodded. "I will go now."',
        f'"Two hands and a slow step," Wend said. "That is my plan."',
    ]
    replies = [
        f'"Take care," called Mara. "The shortest way is not always the safest."',
        f'"Come back before the light fades," said Mara. "I will wait."',
        f'"Thank you," said Mara. Wend answered, "I wanted to help."',
    ]
    reactions = [
        '"Oh," whispered Wend. "I hurried past my own good plan."',
        '"I am sorry," said Wend. "I should have listened to the clue."',
        '"It was a little quest," Wend said, "but I still needed to care."',
    ]

    world.say(openings[rng.randrange(len(openings))])
    world.say(f"{transitions[rng.randrange(len(transitions))]} {replies[rng.randrange(len(replies))]}")
    world.say(f"Wend placed {obj.label} on {plate.label} and set off toward {quest.destination}.")
    wend.location = "path"
    obj.location = "path"
    plate.location = "path"
    wend.memes["hope"] += 1
    obj.meters["warmth"] += 1

    world.para()
    world.say(f"The quest was ordinary, but ordinary paths can turn tricky. {quest.trouble}")
    world.say(f"{quest.sound.capitalize()} went the trouble.")
    world.say(f"Then Wend noticed a clue: {quest.clue}")
    world.say(f'"Wait," said Wend. "I know what to do."')
    world.say(quest.careful_action)
    wend.memes["care"] += 1
    wend.meters["hurry"] += 1
    obj.meters["wobble"] += 1

    world.para()
    world.say(f"But the bad ending came before the careful plan could mend the moment. {quest.consequence}")
    world.say(reactions[rng.randrange(len(reactions))])
    wend.meters["sad"] += 1
    obj.meters["crumbs"] += 1
    plate.location = "path"
    obj.location = "mud"
    wend.location = "destination"
    world.say(f"Wend finished the quest with an empty plate and went on to {quest.destination}.")
    world.say(quest.ending_image)

    world.para()
    world.say(f"Mara listened without scolding. '" + "A failed trip can still teach a careful heart," she said.")
    world.say(f"Wend nodded. {quest.lesson}")
    if world.params.rhyme_mode == "couplet":
        world.say("Slow for the way, slow for the care; a little quest needs hands held fair.")
    elif world.params.rhyme_mode == "counting":
        world.say("One hand to hold, two feet to tread, three careful thoughts before you spread.")
    elif world.params.rhyme_mode == "soft":
        world.say("The day grew still, and Wend grew wise; care can begin beneath sad skies.")
    elif world.params.rhyme_mode == "echo":
        world.say("Go slow, said the door. Go slow, said the chair. Go slow, said Wend, with a newly careful care.")
    else:
        world.say("The next time Wend carried something small, Wend walked slowly and used both hands.")

    world.facts.update(
        object_phrase=quest.object_phrase,
        destination=quest.destination,
        consequence=quest.consequence,
        ending_image=quest.ending_image,
        clue=quest.clue,
        lesson=quest.lesson,
        bad_ending=True,
    )


def story_qa(world: World) -> list[QAItem]:
    quest: Quest = world.facts["quest"]
    name = world.params.name
    return [
        QAItem(
            "Who went on the quest?",
            f"{name} went on the quest.",
        ),
        QAItem(
            "What was Wend trying to do?",
            f"Wend was trying to {quest.errand}.",
        ),
        QAItem(
            "What trouble happened on the way?",
            quest.trouble,
        ),
        QAItem(
            "What clue did Wend notice?",
            quest.clue,
        ),
        QAItem(
            "What happened in the bad ending?",
            quest.consequence,
        ),
        QAItem(
            "What ending image showed the result?",
            quest.ending_image,
        ),
        QAItem(
            "What did Wend learn?",
            quest.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey or task that someone sets out to complete.",
        ),
        QAItem(
            "What does it mean to wend?",
            "To wend means to go or travel along a path, often slowly or carefully.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a pattern in which words have matching or similar ending sounds.",
        ),
        QAItem(
            "What is a bad ending in a gentle story?",
            "A bad ending is a disappointing result that is safe to understand and can teach a useful lesson.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a child-facing slice-of-life rhyme about Wend going on a small quest.",
        "Tell a gentle story in which Wend tries to finish an ordinary errand but meets a bad ending.",
        "Use the word wend, a simple quest, spoken dialogue, and a rhyming final lesson.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life rhyme about Wend's small quest and gentle bad ending."
    )
    parser.add_argument("--name", default=None)
    parser.add_argument("--quest", choices=[q.key for q in QUESTS], default=None)
    parser.add_argument("--rhyme-mode", choices=RHYME_MODES, default=None)
    parser.add_argument("--seed", type=int, default=None)
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
    name = args.name or "Wend"
    if not name.strip():
        raise StoryError("The name must not be empty.")
    quest = args.quest or rng.choice(QUESTS).key
    rhyme_mode = args.rhyme_mode or rng.choice(RHYME_MODES)
    return StoryParams(
        name=name,
        quest=quest,
        rhyme_mode=rhyme_mode,
        seed=args.seed,
        variation=rng.getrandbits(63),
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = [f"location={entity.location}"]
        if entity.held_by:
            details.append(f"held_by={entity.held_by}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + " ".join(details))
    return "\n".join(lines)


ASP_RULES = r"""
child(wend).
thing(quest_object).
quest(wend).
hurries(wend).
drops(quest_object).
bad_ending :- quest(wend), hurries(wend), drops(quest_object).
care_lesson :- bad_ending.
#show bad_ending/0.
#show care_lesson/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child", "wend"),
            asp.fact("thing", "quest_object"),
            asp.fact("quest", "wend"),
            asp.fact("hurries", "wend"),
            asp.fact("drops", "quest_object"),
        ]
    )


def asp_program(show: str = "#show bad_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    names = {symbol.name for symbol in model}
    if "bad_ending" not in names:
        print("MISMATCH: ASP twin did not produce the bad ending.")
        return 1
    sample = generate(StoryParams(seed=1, variation=1))
    if "bad ending" not in sample.story.lower():
        print("MISMATCH: generated story did not exercise the bad ending.")
        return 1
    print("OK: ASP twin and generated story agree on the bad ending.")
    return 0


CURATED = [
    StoryParams(name="Wend", quest="pie", rhyme_mode="couplet", variation=11),
    StoryParams(name="Wend", quest="book", rhyme_mode="counting", variation=22),
    StoryParams(name="Wend", quest="seedling", rhyme_mode="soft", variation=33),
    StoryParams(name="Wend", quest="scarf", rhyme_mode="echo", variation=44),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
                samples.append(generate(params))
            except StoryError as exc:
                print(exc, file=sys.stderr)
                raise SystemExit(2)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print()
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
