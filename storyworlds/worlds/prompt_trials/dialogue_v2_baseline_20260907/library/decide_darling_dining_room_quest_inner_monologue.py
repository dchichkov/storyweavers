#!/usr/bin/env python3
"""Darling's Dining-Room Quest: a small decision grows brave through an inner monologue."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Nora"
    darling: str = "Pip"
    quest: str = "choose_place"
    approach: str = "ask"
    token: str = "napkin"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "dining_room",
                meters={"courage": 0.4, "decision": 0},
                memes={"worry": 0.8, "warmth": 0.7},
            ),
            "darling": Entity(
                "darling", params.darling, "companion", "dining_room",
                meters={"helpfulness": 0.8},
                memes={"patience": 0.9, "warmth": 0.9},
            ),
            "table": Entity(
                "table", "the round dining table", "furniture", "dining_room",
                meters={"seats": 4, "set": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(
            kind=kind, text=text, question=question, cause=cause, result=result,
            state=self.snapshot(),
        ))

    def decide(self, choice: str):
        hero = self.entities["hero"]
        if hero.meters["decision"]:
            raise StoryError("The hero has already made the dining-room decision.")
        hero.beliefs["choice"] = choice
        hero.meters["decision"] = 1
        hero.meters["courage"] += 0.5
        hero.memes["worry"] = 0.1

    def complete_quest(self):
        table = self.entities["table"]
        hero = self.entities["hero"]
        if not hero.meters["decision"]:
            raise StoryError("A choice must be made before the table can be prepared.")
        table.meters["set"] = 1
        hero.meters["courage"] = 1.0

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}".strip(),
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="Why can making a small decision help someone?",
                    answer="A small decision can turn worry into a clear next step.",
                ),
                QAItem(
                    question="What makes a dining room feel welcoming?",
                    answer="A welcoming dining room has a prepared place and people who care for one another.",
                ),
            ],
            world=self,
        )


NAMES = ("Nora", "Milo", "Lena", "Theo", "Ivy", "Sam")
DARLINGS = ("Pip", "Bunny", "Sunny", "Clover")
APPROACHES = ("ask", "guess")
TOKENS = {
    "napkin": ("a yellow napkin", "a tiny yellow sun"),
    "spoon": ("a silver spoon", "a bright little moon"),
    "flower": ("a pink flower", "a warm pink star"),
}

PROMPT = (
    "Write a heartwarming children's story about a darling companion helping "
    "someone decide during a suspenseful quest in a dining room."
)

QUESTS = {
    "choose_place": "choose_place",
    "welcome_guest": "welcome_guest",
    "save_supper": "save_supper",
}


def validate_params(params: StoryParams):
    if params.quest not in QUESTS:
        raise StoryError("That dining-room quest is not available.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either asking for help or guessing first.")
    if params.token not in TOKENS:
        raise StoryError("Choose a napkin, spoon, or flower as the story token.")
    if params.hero == params.darling:
        raise StoryError("The hero and darling need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.darling)):
        raise StoryError("Names must be simple capitalized names, such as Nora and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    label, image = TOKENS[params.token]
    world.entities["token"] = Entity(
        "token", label, "table_token", "sideboard",
        meters={"ready": 0},
        memes={"cheer": 0.5},
        beliefs={"image": image},
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"]
    darling = world.entities["darling"]
    table = world.entities["table"]
    token = world.entities["token"]
    h, d = hero.label, darling.label
    token_label, token_image = TOKENS[params.token]

    world.narrate(
        "beginning",
        f"In the dining room, {h} found four chairs waiting around the round table. "
        f"{d}, their darling little helper, carried {token_label} from the sideboard.",
    )

    if params.quest == "choose_place":
        world.narrate(
            "quest",
            f"Tonight {h} had one important job: decide where the guest of honor should sit. "
            "The empty chair by the window looked friendly, but the chair near the lamp looked warm.",
            question="What was the first choice in the dining-room quest?",
            cause=f"{h} needed to decide where the guest of honor should sit.",
            result="The hero had to choose between the window chair and the warm chair by the lamp.",
        )
        world.narrate(
            "inner_monologue",
            f'"The window has the best view," {h} thought. "But what if our guest feels chilly? '
            f"What if I choose wrong?\" The clock gave a soft tick, and the empty chair seemed to wait.",
            question="Why did the decision feel difficult?",
            cause=f"{h} cared about making the guest comfortable.",
            result="The hero worried that either chair might be the wrong choice.",
        )
        if params.approach == "guess":
            world.narrate(
                "suspense",
                f"{h} reached for the window chair. Just then, a cool breeze slipped under the dining-room door. "
                f"{d} held {token_label} close and looked toward the lamp.",
                question="What clue changed the hero's thinking?",
                cause="A cool breeze showed that the window chair might feel chilly.",
                result=f"{h} noticed that the lamp chair would be warmer.",
            )
            world.narrate(
                "dialogue",
                f'"Darling, do you think the lamp chair is kinder tonight?" {h} asked. '
                f'{d} nodded and lifted {token_label}.',
            )
        else:
            world.narrate(
                "dialogue",
                f'"Darling, which chair would help our guest feel welcome?" {h} asked. '
                f'{d} touched the lamp chair, then pointed at the chilly window.',
            )
            world.narrate(
                "suspense",
                f"A breeze whispered through the dining room. {h} looked at the window chair again. "
                "The answer was hiding in the cold air.",
                question="How did the darling help?",
                cause=f"{d} pointed out the lamp chair, and the breeze supplied a useful clue.",
                result=f"{h} understood that the warm chair would be the kinder choice.",
            )
        choice = "the warm chair by the lamp"
        world.decide(choice)
        world.narrate(
            "turn",
            f"{h} took a slow breath and chose {choice}. "
            f'"I decide on this one," {h} said. "We can always listen and change it together."',
            question="What decision did the hero make?",
            cause=f"{h} considered the breeze and {d}'s gentle clue.",
            result=f"{h} chose the warm chair by the lamp for the guest.",
        )
        world.complete_quest()
        world.narrate(
            "ending",
            f"{d} placed {token_label} beside the warm plate. "
            f"The token looked like {token_image}, and the dining room seemed brighter. "
            f"When the guest arrived, {h} smiled because one brave decision had made room for everyone.",
            question="How did the quest end?",
            cause=f"{h} chose a warm place and prepared it with help from {d}.",
            result="The guest felt welcome, and the hero learned that a careful decision can be changed with kindness.",
        )

    elif params.quest == "welcome_guest":
        world.narrate(
            "quest",
            f"{h} was waiting for a new neighbor to arrive. The dining room was ready except for one question: "
            f"should the welcome token go beside the plate or at the empty chair?",
            question="What was the hero trying to prepare?",
            cause=f"{h} wanted to welcome a new neighbor in the dining room.",
            result=f"{h} needed to decide where to place {token_label}.",
        )
        world.narrate(
            "inner_monologue",
            f'"If I put it by the plate, it will be easy to see," {h} thought. '
            f'"But if I put it on the chair, the guest may feel that the place is truly theirs."',
        )
        world.narrate("suspense", "The hallway made a tiny creak.")
        if params.approach == "guess":
            world.narrate(
                "suspense",
                f"{h} carried {token_label} toward the plate. The front door rattled softly, "
                f"and {d} peeked at the empty chair as if it were expecting someone.",
                question="What made the hero pause?",
                cause="The rattling door announced that the guest might arrive soon.",
                result=f"{h} noticed that the empty chair needed a clear welcome.",
            )
        else:
            world.narrate(
                "dialogue",
                f'"Darling, where would you feel welcome?" {h} asked. {d} climbed onto the empty chair '
                f"and patted its seat beside the table.",
                question="What did the darling show?",
                cause=f"{d} climbed onto the empty chair and patted its seat.",
                result=f"{h} understood that the guest should find {token_label} at the chair.",
            )
        world.decide("the empty chair")
        world.narrate(
            "turn",
            f'"I decide to place it on the empty chair," {h} said. '
            f"{d} helped smooth the cloth beneath {token_label}.",
            question="Where did the hero place the welcome token?",
            cause=f"{h} wanted the new neighbor to know which place belonged to them.",
            result=f"{h} placed {token_label} on the empty chair.",
        )
        world.complete_quest()
        world.narrate(
            "ending",
            f"The door opened, and the new neighbor saw {token_label} waiting on the chair. "
            f"{d} gave a happy little wave. {h} felt the worry in their chest grow small "
            "as the whole table made room for one more friend.",
            question="What changed by the end?",
            cause=f"{h} made the chair look truly ready for the new neighbor.",
            result="The neighbor felt invited, and the dining room became a shared place.",
        )

    else:
        world.narrate(
            "quest",
            f"Supper was almost ready, but one small bowl had gone missing. "
            f"{h} searched beneath the dining table while {d} guarded {token_label}.",
            question="What problem began the supper quest?",
            cause="A bowl was missing just before supper.",
            result=f"{h} and {d} needed to find it before the meal began.",
        )
        world.narrate(
            "inner_monologue",
            f'"I must decide where to look first," {h} thought. "The sideboard or the pantry?"',
        )
        world.narrate("suspense", "The dining-room shadows stretched long across the floor.")
        if params.approach == "guess":
            world.narrate(
                "suspense",
                f"{h} opened the sideboard. A stack of plates trembled, but there was no bowl. "
                f"{d} pointed toward the quiet space beneath the table.",
                question="What happened when the first guess failed?",
                cause=f"{h} guessed that the bowl was in the sideboard.",
                result="The sideboard held plates but no bowl, so the search had to change.",
            )
        else:
            world.narrate(
                "dialogue",
                f'"Darling, what do you remember seeing?" {h} asked. '
                f"{d} sniffed beneath the table and found a tiny trail of flour.",
                question="What clue did the darling find?",
                cause=f"{d} noticed a tiny trail of flour beneath the table.",
                result="The flour trail pointed toward the hidden bowl.",
            )
        world.decide("follow the flour trail")
        world.narrate(
            "turn",
            f'"I decide to follow the flour," {h} said. Under the tablecloth, {d} discovered the bowl '
            "beside a fallen napkin ring.",
            question="How did the hero find the bowl?",
            cause=f"{h} chose to follow the flour trail after {d} noticed it.",
            result="They found the bowl beneath the tablecloth.",
        )
        world.complete_quest()
        world.narrate(
            "ending",
            f"{h} set the bowl on the table, and {d} carried {token_label} to its place. "
            "Supper began with warm bread, bright eyes, and a laugh about the bowl's secret hiding place.",
            question="How did supper end?",
            cause="The bowl was found and the table was prepared together.",
            result="Everyone shared supper, and the small quest became a happy memory.",
        )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if not world.entities["hero"].meters["decision"]:
        raise StoryError("The hero must make a real decision.")
    if not world.entities["table"].meters["set"]:
        raise StoryError("The dining table must be prepared by the ending.")
    if world.entities["hero"].meters["courage"] < 1:
        raise StoryError("The hero's courage must grow through the quest.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several grounded question-and-answer pairs.")
    if not any(event.kind == "inner_monologue" for event in world.history):
        raise StoryError("The story needs an inner monologue.")
    if not any(event.kind == "suspense" for event in world.history):
        raise StoryError("The story needs a suspenseful turn.")
    if not sample.story.endswith("."):
        raise StoryError("The story must end with a complete sentence.")
    if any(word in sample.story for word in ("hero_id", "darling_id", "{{", "}}")):
        raise StoryError("Internal identifiers or unresolved template fields leaked into the story.")


ASP_RULES = """
allowed_quest(choose_place).
allowed_quest(welcome_guest).
allowed_quest(save_supper).
allowed_approach(ask).
allowed_approach(guess).
valid(Q,A) :- quest(Q), approach(A), allowed_quest(Q), allowed_approach(A).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("quest", quest) for quest in QUESTS]
        + [fact("approach", approach) for approach in APPROACHES]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def valid_combos() -> list[tuple[str, str]]:
    return [(quest, approach) for quest in QUESTS for approach in APPROACHES]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--quest", choices=tuple(QUESTS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--token", choices=tuple(TOKENS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    quests = [quest for quest in QUESTS if args.quest is None or quest == args.quest]
    approaches = [approach for approach in APPROACHES if args.approach is None or approach == args.approach]
    if not quests or not approaches:
        raise StoryError("No quest matches the selected options.")
    hero = args.hero or rng.choice(NAMES)
    darling_choices = [name for name in DARLINGS if name != hero]
    darling = args.darling or rng.choice(darling_choices)
    params = StoryParams(
        hero=hero,
        darling=darling,
        quest=rng.choice(quests),
        approach=rng.choice(approaches),
        token=args.token or rng.choice(tuple(TOKENS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about valid quest combinations.")
    tested = 0
    for quest, approach in valid_combos():
        for token in TOKENS:
            sample = generate(StoryParams(
                quest=quest,
                approach=approach,
                token=token,
                seed=777,
            ))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} Python/ASP-compatible combinations.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(
            dict(
                entities=sample.world.snapshot(),
                history=[asdict(event) for event in sample.world.history],
            ),
            indent=2,
        ))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            choices = [
                (quest, approach)
                for quest, approach in valid_combos()
                if args.quest is None or quest == args.quest
                if args.approach is None or approach == args.approach
            ]
            if not choices:
                raise StoryError("No compatible combinations match these options.")
            params_list = [
                StoryParams(
                    hero=args.hero or rng.choice(NAMES),
                    darling=args.darling or rng.choice(DARLINGS),
                    quest=quest,
                    approach=approach,
                    token=args.token or rng.choice(tuple(TOKENS)),
                    seed=args.seed,
                )
                for quest, approach in choices
            ]
            for params in params_list:
                if params.hero == params.darling:
                    params.darling = rng.choice([name for name in DARLINGS if name != params.hero])
                validate_params(params)
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
