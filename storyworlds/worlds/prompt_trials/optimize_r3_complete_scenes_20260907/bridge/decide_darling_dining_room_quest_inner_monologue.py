#!/usr/bin/env python3
"""A small dining-room quest about deciding kindly when a surprise goes wrong."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Mara"
    darling: str = "Niko"
    trouble: str = "spilled"
    approach: str = "listen"
    seed: int = 777


NAMES = ("Mara", "Niko", "Lena", "Owen", "Pia", "Theo")
TROUBLES = ("spilled", "missing", "cold")
APPROACHES = ("listen", "notice")
PROMPT = (
    "Write a heartwarming children's story set in a dining room, where a child "
    "must decide how to complete a suspenseful quest with a darling friend."
)

ASP_RULES = """
valid(T) :- trouble(T).
#show valid/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "dining_room",
                           memes={"care": 0.5, "worry": 0.4}),
            "darling": Entity("darling", params.darling, "character", "dining_room",
                              memes={"hope": 0.7, "trust": 0.5}),
            "quest": Entity("quest", "birthday surprise", "object", "dining_room",
                            meters={"complete": 0, "safe": 1}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def scene(self, text: str, *, question="", cause="", result=""):
        self.history.append(Event("scene", text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, who: str, text: str, *, to=""):
        speaker = self.entities[who].label
        ending = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {speaker} {ending}.',
                                  speaker=who, listener=to, state=self.snapshot()))


def validate(params: StoryParams):
    if params.trouble not in TROUBLES:
        raise StoryError("Choose a known dining-room trouble.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either listen or notice.")
    if params.hero == params.darling:
        raise StoryError("The two characters need different names.")
    if any(not name[:1].isupper() or not name.isalpha() for name in
           (params.hero, params.darling)):
        raise StoryError("Names must be simple alphabetic names beginning with capitals.")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World(params)
    trouble_data = {
        "spilled": ("cake", 0, 1),
        "missing": ("candle", 0, 1),
        "cold": ("soup", 1, 0),
    }
    item, ready, safe = trouble_data[params.trouble]
    world.entities["quest"].label = f"birthday {item}"
    world.entities["quest"].meters.update(ready=ready, safe=safe)
    return world


def finish(world: World):
    quest = world.entities["quest"]
    if quest.meters["complete"] != 1 or quest.location != "table":
        raise StoryError("The quest must end visibly complete on the dining table.")
    if world.entities["hero"].memes["care"] < 1:
        raise StoryError("The decision must show care.")
    if world.entities["darling"].memes["hope"] < 1:
        raise StoryError("The darling must finish hopeful.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, d = params.hero, params.darling
    world.scene(
        f"In the dining room, {h} carried a small birthday surprise toward {d}. "
        f"The candles were hidden, the plates gleamed, and a quiet suspense curled around the table."
    )
    world.say("hero", f"{d}, darling, will you help me decide how to finish one little quest?")
    world.say("darling", "I will, but please do not tell me the surprise yet.")
    world.entities["hero"].memes["care"] += 0.2

    if params.trouble == "spilled":
        if params.approach == "notice":
            world.scene(
                f"{h} noticed a shining trail beside the cake stand before anyone touched it. "
                f"A glass had tipped near the table edge."
            )
        else:
            world.say("hero", "Why does the table sound wet?")
            world.say("darling", "I heard a tiny drip, too.")
            world.scene(
                f"{d} pointed beneath the cake stand, where juice had spread toward the cloth. "
                f"The surprise could be saved, but only if they moved it quickly."
            )
        world.say("darling", "The cake is safe, but the cloth is not.")
        world.say("hero", "Should I hide the spill or tell Grandma?")
        world.say("darling", "Tell her. A secret puddle could make someone slip.")
        world.entities["hero"].beliefs["truth"] = "the puddle is dangerous"
        world.entities["darling"].beliefs["truth"] = "the puddle is dangerous"
        world.entities["hero"].memes["care"] += 0.5
        world.scene(
            f"{h} decided to tell Grandma and moved the cake to the dry end of the table. "
            f"Grandma wiped the puddle while {d} held the plates steady.",
            question="Why did the children tell Grandma about the spill?",
            cause="The juice had spread toward the table edge and could make someone slip.",
            result="They moved the cake and had the puddle wiped before the birthday meal.",
        )
        world.entities["quest"].location = "table"
        world.entities["quest"].meters.update(complete=1, safe=1)

    elif params.trouble == "missing":
        world.scene(
            f"{h} lifted the napkin beside the birthday plate and found no candle. "
            f"The empty little dish made the quest feel suddenly suspenseful."
        )
        world.say("hero", "The candle is missing. Did you see where it went?")
        world.say("darling", "I saw a silver glint under the sideboard.")
        world.say("hero", "Then I will look there, but you stay beside the table.")
        world.say("darling", "I can watch the cake and call if the cat comes near.")
        world.entities["darling"].beliefs["clue"] = "silver glint under sideboard"
        world.scene(
            f"{h} knelt beside the sideboard and found the candle in a fallen spoon's reflection. "
            f"The cat had nudged the spoon, but the candle itself was untouched.",
            question="What clue helped them find the missing candle?",
            cause="The darling remembered seeing a silver glint under the sideboard.",
            result="The glint led them to the candle beside a fallen spoon.",
        )
        world.say("hero", "I found it. Your sharp eyes solved the hardest part.")
        world.say("darling", "Then put it in the cake, and I will guard the matches.")
        world.entities["hero"].memes["care"] += 0.5
        world.entities["quest"].location = "table"
        world.entities["quest"].meters.update(complete=1, safe=1)

    else:
        world.scene(
            f"{h} touched the soup pot and pulled back from its cold handle. "
            f"The birthday supper was ready, but its warm welcome had gone quiet."
        )
        world.say("hero", "The soup is cold. Should we serve something else?")
        world.say("darling", "Wait. The recipe card says to warm it slowly.")
        world.say("hero", "I thought the quest was to hurry.")
        world.say("darling", "It is to make everyone comfortable, not merely to finish first.")
        world.entities["darling"].beliefs["clue"] = "warm slowly"
        world.entities["hero"].memes["care"] += 0.5
        world.scene(
            f"{h} decided to warm the soup slowly while {d} set out the bowls. "
            f"They stirred together until a curl of steam rose above the dining-room table.",
            question="Why did they warm the soup slowly?",
            cause="The recipe card said slow warming would restore the soup without spoiling it.",
            result="They waited together until the soup sent up a warm curl of steam.",
        )
        world.say("hero", "You changed my mind, darling.")
        world.say("darling", "You listened, so the supper will taste like patience.")
        world.entities["quest"].location = "table"
        world.entities["quest"].meters.update(complete=1, safe=1)

    world.entities["hero"].memes["care"] = 1.0
    world.entities["darling"].memes["hope"] = 1.0
    world.scene(
        f"The dining-room table glowed with the finished surprise. {h} and {d} smiled at "
        f"the small proof that a good decision could make a celebration safer and kinder.",
        question="How did the quest end?",
        cause=f"{h} and {d} shared what they knew and chose a careful solution to the {params.trouble} trouble.",
        result="The birthday surprise rested safely on the dining-room table, ready for everyone.",
    )
    finish(world)
    story = "\n\n".join(event.text for event in world.history)
    sample = StorySample(
        params=params,
        story=story,
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem("Where did the story take place?",
                   "It took place in a dining room."),
            QAItem("What did the characters practice?",
                   "They practiced sharing information and making a caring decision."),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    finish(sample.world)
    speech = [e for e in sample.world.history if e.kind == "speech"]
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "darling" for e in speech):
        raise StoryError("Both characters need to speak.")
    if len(sample.story_qa) < 2:
        raise StoryError("The completed path needs grounded questions and answers.")
    if "decide" not in sample.story or "darling" not in sample.story.lower():
        raise StoryError("The story must include the decision and darling seed words.")


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("trouble", trouble) for trouble in TROUBLES)


def asp_troubles() -> set[str]:
    from asp import atoms, one_model
    return {row[0] for row in atoms(one_model(asp_facts() + ASP_RULES), "valid")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--trouble", choices=TROUBLES)
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    darling = args.darling or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(hero=hero, darling=darling,
                         trouble=args.trouble or rng.choice(TROUBLES),
                         approach=args.approach or rng.choice(APPROACHES),
                         seed=args.seed)
    validate(params)
    return params


def verify():
    if asp_troubles() != set(TROUBLES):
        raise StoryError("Python and ASP disagree about valid troubles.")
    count = 0
    for trouble in TROUBLES:
        for approach in APPROACHES:
            generate(StoryParams(trouble=trouble, approach=approach))
            count += 1
    print(f"OK: {count} story states; {len(TROUBLES)} ASP-compatible troubles.")


def emit(sample: StorySample, *, trace=False, qa=False):
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({"entities": sample.world.snapshot(),
                          "history": [asdict(e) for e in sample.world.history]},
                         indent=2))


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
            print(json.dumps(sorted(asp_troubles())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(hero=args.hero or "Mara", darling=args.darling or "Niko",
                            trouble=trouble, approach=approach, seed=args.seed)
                for trouble in TROUBLES for approach in APPROACHES
                if args.trouble is None or args.trouble == trouble
                if args.approach is None or args.approach == approach
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                if len(samples) > 1:
                    print(f"\n### Story {index + 1}\n")
                emit(sample, trace=args.trace, qa=args.qa)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
