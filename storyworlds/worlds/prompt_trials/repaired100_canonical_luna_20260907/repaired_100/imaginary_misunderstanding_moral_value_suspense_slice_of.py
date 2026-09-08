#!/usr/bin/env python3
"""
A small slice-of-life storyworld about an imaginary misunderstanding, a moral
choice, and the suspense of telling the truth.
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

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    details: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


PLACES = {
    "kitchen": Place(
        "the apartment kitchen",
        "home",
        "where a small blue bowl waited beside the sink",
    ),
    "hallway": Place(
        "the apartment hallway",
        "home",
        "where shoes stood in a row beneath the coat hooks",
    ),
    "courtyard": Place(
        "the quiet courtyard",
        "outdoors",
        "where bicycles leaned against the brick wall",
    ),
}

NAMES = ["Luna", "Mara", "Theo", "Nia", "Jonah", "Iris", "Owen", "Pia"]

SCENES = [
    {
        "key": "missing_note",
        "object": "a paper moon",
        "premise": "Luna found a folded note beside the paper moon they had made for the window",
        "misunderstanding": "The note looked like a message saying that the moon was not good enough for the evening display",
        "wrong_action": "She tucked the moon behind a stack of plates and decided not to mention it",
        "clue": "a smear of blue paint crossed the note, matching the paint on her own fingers",
        "truth": "The note was only a reminder from her friend to add a star before hanging it",
        "repair": "Luna brought the moon back, explained what she had thought, and added the star with her friend",
        "ending": "the paper moon shone in the window with one bright star beside it",
        "lesson": "a frightening guess should be checked before it becomes a hurtful fact",
    },
    {
        "key": "quiet_invitation",
        "object": "a jar of sidewalk chalk",
        "premise": "Luna saw her friend whispering near the courtyard gate while holding the chalk jar",
        "misunderstanding": "She imagined that they were planning to leave her out of the drawing game",
        "wrong_action": "She picked up her coat and sat on the stairs without asking",
        "clue": "a chalk arrow on the ground pointed toward a blank wall with a space marked for her name",
        "truth": "Her friend had been preparing a surprise place for Luna's favorite purple sun",
        "repair": "Luna admitted her worry, and the friends finished the wall together",
        "ending": "the purple sun joined the other drawings above a row of chalky shoes",
        "lesson": "being left out can feel real even when the evidence says otherwise",
    },
    {
        "key": "borrowed_book",
        "object": "a library book about imaginary gardens",
        "premise": "Luna noticed a library book missing from the table where she had left it",
        "misunderstanding": "She assumed her friend had hidden it because they did not like the story",
        "wrong_action": "She accused them while they were carrying a basket of laundry",
        "clue": "a bookmark shaped like a leaf stuck out of the laundry basket",
        "truth": "Her friend had moved the book to keep it dry after water spilled near the table",
        "repair": "Luna apologized and helped dry the table before they read the last chapter together",
        "ending": "the imaginary garden book rested safely on the dry shelf",
        "lesson": "careful questions protect friendship better than quick accusations",
    },
    {
        "key": "closed_door",
        "object": "a cardboard train",
        "premise": "Luna found the bedroom door closed while her friend worked inside with the cardboard train",
        "misunderstanding": "She imagined that a secret meeting was happening without her",
        "wrong_action": "She pressed her ear to the door and prepared to complain",
        "clue": "a strip of tape on the floor marked a path leading from the door to a tiny paper ticket",
        "truth": "Her friend was repairing the train so Luna could be the first passenger",
        "repair": "Luna knocked, listened to the explanation, and helped decorate the ticket",
        "ending": "the cardboard train rolled through the hallway with Luna's ticket tucked in front",
        "lesson": "suspense can grow in an empty space where a simple question would fit",
    },
    {
        "key": "unanswered_message",
        "object": "a voice message about dinner",
        "premise": "Luna sent a message asking whether her friend wanted to share soup, but no answer came",
        "misunderstanding": "She decided the silence meant her invitation had been rejected",
        "wrong_action": "She put both bowls away and planned to eat alone",
        "clue": "the phone screen showed the message still waiting to send",
        "truth": "The building had lost its signal, so her friend had never received it",
        "repair": "Luna showed the unsent message, and they carried the soup to the courtyard together",
        "ending": "two warm bowls steamed beneath the courtyard lights",
        "lesson": "silence does not always carry the meaning we give it",
    },
    {
        "key": "imaginary_friend",
        "object": "an imaginary fox named Button",
        "premise": "Luna heard her friend say that Button had knocked over the cushion",
        "misunderstanding": "She thought her friend was blaming an imaginary animal to hide a mistake",
        "wrong_action": "She began fixing the cushion without listening to the whole story",
        "clue": "a real breeze pushed the open window and sent the cushion sliding",
        "truth": "Her friend had been pretending to ask Button for help, then noticed the wind had caused the mess",
        "repair": "Luna laughed, closed the window, and helped place the cushion safely",
        "ending": "Button received an imaginary bow while the real cushion stayed in place",
        "lesson": "pretend play can be honest when everyone understands it is pretend",
    },
]

OPENINGS = [
    "On an ordinary afternoon,",
    "After the dishes were washed,",
    "Just before the evening lights came on,",
    "While the building settled into its quiet sounds,",
    "Near the end of a perfectly normal day,",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An imaginary misunderstanding slice-of-life storyworld."
    )
    parser.add_argument("--setting", choices=sorted(PLACES))
    parser.add_argument("--name")
    parser.add_argument("--friend")
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
    setting = args.setting or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(NAMES)
    friend_name = args.friend or rng.choice([name for name in NAMES if name != hero_name])
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        friend_name=friend_name,
        seed=None,
    )


def tell(params: StoryParams) -> World:
    if params.setting not in PLACES:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    opening = rng.choice(OPENINGS)
    concern = rng.choice(
        [
            "I thought you meant something unkind",
            "I was afraid to ask what was happening",
            "I filled in the quiet with my own story",
            "I did not know what the note meant",
            "I worried that you had changed your mind",
        ]
    )
    response = rng.choice(
        [
            "I can see why that looked worrying, but it was not what I meant",
            "Thank you for telling me instead of keeping the worry secret",
            "The real story was smaller and kinder than the one you imagined",
            "I should have explained before letting the silence grow",
            "I am glad we checked before either of us felt worse",
        ]
    )

    world = World(Place(**PLACES[params.setting].__dict__))
    hero = world.add(
        Entity(
            id=params.hero_name,
            type="child",
            meters={"distance_to_truth": 1.0, "suspense": 0.4},
            memes={"worry": 0.5, "trust": 0.6},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            type="child",
            meters={"distance_to_truth": 0.0, "suspense": 0.2},
            memes={"patience": 0.7, "trust": 0.6},
        )
    )

    world.say(
        f"{opening} {params.hero_name} and {params.friend_name} were together in "
        f"{world.place.name}, {world.place.details}. They had been making {scene['object']}."
    )
    world.say(f"{scene['premise']}.")
    world.para()

    world.say(
        f"{params.hero_name} formed an imaginary explanation: {scene['misunderstanding']}. "
        f"Because of that guess, {scene['wrong_action']}."
    )
    world.say(
        f"The ordinary room suddenly felt suspenseful. Every little sound seemed to ask "
        f"whether the friendship was about to change."
    )
    world.say(f'"{concern}," {params.hero_name} said.')
    world.say(
        f'"I did not know you saw it that way," {params.friend_name} replied. '
        f'"Let us look at what really happened."'
    )
    world.say(f"Then they noticed the clue: {scene['clue']}.")
    world.para()

    world.say(
        f'"{response}," {params.friend_name} said. '
        f'"The truth is that {scene["truth"].lower()}"'
    )
    world.say(
        f"{params.hero_name} listened instead of defending the first guess. "
        f"{params.hero_name} said, 'I am sorry. I should have asked before deciding.'"
    )
    world.say(f"Together, they {scene['repair']}.")
    world.para()

    hero.meters["distance_to_truth"] = 0.0
    hero.meters["suspense"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0

    world.say(
        f"The misunderstanding faded because the friends replaced an imaginary story with "
        f"a real conversation. They agreed to ask questions when a quiet moment felt scary."
    )
    world.say(
        f"The moral value was simple: {scene['lesson']}. "
        f"At the end, {scene['ending']}."
    )

    world.facts.update(
        scene=scene,
        hero=hero,
        friend=friend,
        concern=concern,
        response=response,
        opening=opening,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write a child-friendly slice-of-life story about {scene['object']} and an imaginary misunderstanding.",
        f"Tell a suspenseful story in which two friends check the truth before judging each other.",
        f"Write a gentle story showing that {scene['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    scene = facts["scene"]
    hero: Entity = facts["hero"]
    friend: Entity = facts["friend"]
    return [
        QAItem(
            question=f"What misunderstanding did {hero.id} have about {friend.id}?",
            answer=(
                f"{hero.id} imagined that {scene['misunderstanding'].lower()}. "
                f"It was a guess, not a fact."
            ),
        ),
        QAItem(
            question="What clue helped the friends discover the truth?",
            answer=f"They noticed that {scene['clue']}. That concrete clue challenged the first explanation.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} repair the misunderstanding?",
            answer=(
                f"They talked honestly, apologized for the quick assumption, and "
                f"{scene['repair']}."
            ),
        ),
        QAItem(
            question="Why did the ordinary setting become suspenseful?",
            answer=(
                "The setting became suspenseful because a small unexplained detail made "
                "the hero worry that the friendship was changing."
            ),
        ),
        QAItem(
            question="What moral value did the story show?",
            answer=f"The story showed that {scene['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is imaginary?",
            answer="Imaginary means existing in pretend play, in a thought, or in a story rather than as a physical thing in the real world.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gives the wrong meaning to words, actions, or events.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the worried or curious feeling of waiting to learn what will happen or what something means.",
        ),
        QAItem(
            question="Why is asking a question a moral choice?",
            answer="Asking before judging can protect another person's dignity and gives everyone a fair chance to explain the truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"place: {world.place.name}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(home).
setting(outdoors).
feature(imaginary).
feature(misunderstanding).
feature(moral_value).
feature(suspense).
style(slice_of_life).
moral_choice(ask_before_judging).
resolved_by(conversation).
story_reasonable :-
    feature(imaginary),
    feature(misunderstanding),
    feature(moral_value),
    feature(suspense),
    style(slice_of_life),
    moral_choice(ask_before_judging),
    resolved_by(conversation).
#show feature/1.
#show story_reasonable/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("feature", "imaginary"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "moral_value"),
        asp.fact("feature", "suspense"),
        asp.fact("style", "slice_of_life"),
        asp.fact("moral_choice", "ask_before_judging"),
        asp.fact("resolved_by", "conversation"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show feature/1. #show story_reasonable/0."))
    features = set(asp.atoms(model, "feature"))
    expected = {
        ("imaginary",),
        ("misunderstanding",),
        ("moral_value",),
        ("suspense",),
    }
    reasonable = bool(asp.atoms(model, "story_reasonable"))
    if features != expected or not reasonable:
        print("Mismatch in ASP verification.")
        return 1

    for seed in range(5):
        params = StoryParams(
            setting="kitchen",
            hero_name="Luna",
            friend_name="Mara",
            seed=seed,
        )
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show feature/1. #show story_reasonable/0."))
        print(sorted(asp.atoms(model, "feature")))
        print("story_reasonable:", bool(asp.atoms(model, "story_reasonable")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, scene in enumerate(SCENES):
            params = StoryParams(
                setting=list(PLACES)[index % len(PLACES)],
                hero_name="Luna",
                friend_name="Mara",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
