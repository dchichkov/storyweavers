#!/usr/bin/env python3
"""Gingham Magic Nursery Rhyme.

A small nursery-rhyme world in which two friends use a gingham spell cloth
to mend three different little troubles.
"""

from __future__ import annotations

import argparse
import json
import random
import re
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    hero: str = "Mabel"
    friend: str = "Pip"
    path: str = "bell"
    seed: int = 777


NAMES = ("Mabel", "Pip", "Nell", "Toby", "Dot", "Wren")
PATHS = ("bell", "moon", "rain")
PROMPT = "Write a gentle nursery rhyme about two friends using gingham magic to mend a little trouble."
PATH_INFO = {
    "bell": {
        "trouble": "the moon-bell lost its ring",
        "clue": "the bell had been wrapped too tightly in the cloth",
        "object": "moon-bell",
    },
    "moon": {
        "trouble": "the moon slipped behind a cloud and forgot its glow",
        "clue": "the silver moon needed a cheerful tune to remember its light",
        "object": "moon",
    },
    "rain": {
        "trouble": "the garden's silver rain would not fall",
        "clue": "the rain cloud was thirsty for one bright gingham square",
        "object": "rain-cloud",
    },
}

ASP_RULES = """
solves(bell,gingham) :- trouble(bell,missing_ring).
solves(moon,gingham) :- trouble(moon,missing_glow).
solves(rain,gingham) :- trouble(rain,missing_rain).
#show solves/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, memes={"hope": 0.5}),
            "friend": Entity("friend", params.friend, memes={"hope": 0.5}),
            "gingham": Entity("gingham", "the gingham cloth", location="basket",
                              meters={"magic": 1, "folds": 4}),
        }
        self.history: list[Event] = []

    def scene(self, text: str, *, kind="scene", question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result))

    def say(self, who: str, text: str):
        name = self.entities[who].label
        punctuation = "" if text.endswith((".", "!", "?")) else "."
        self.scene(f'"{text}" said {name}{punctuation}', kind="speech")

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("What special cloth belonged to this nursery rhyme?",
                       "The friends used a gingham cloth with a little magic in its folds.")
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("The path must be bell, moon, or rain.")
    if params.hero == params.friend:
        raise StoryError("The two characters need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.friend
    rng = random.Random(params.seed)
    first_lines = (
        f"By the nursery gate, {h} and {f} found a gingham cloth in a basket.",
        f"At dawn, {h} and {f} skipped beside a basket holding a gingham cloth.",
    )
    world.scene(rng.choice(first_lines))
    world.say("hero", "Shall we see what its tiny squares can do?")
    world.say("friend", "Only if we listen carefully to its magic.")

    if params.path == "bell":
        world.entities["moon-bell"] = Entity(
            "moon-bell", "the moon-bell", location="gate",
            meters={"ring": 0, "mended": 0})
        world.scene(
            f"The moon-bell hung over the gate, but it had lost its bright ring. "
            f"{h} tugged the string, and the silent bell only shivered.",
            question="Why did the moon-bell make no sound?",
            cause="The bell's ring had vanished while it was wrapped in gingham.",
            result="Pulling its string made it shiver but did not make music.")
        world.say("hero", "Perhaps the bell needs a louder tug.")
        world.say("friend", f"Listen to the cloth: its folds whisper, '{PATH_INFO['bell']['clue']}'.")
        world.scene(
            f"{f} opened the gingham fold and found a tiny silver ring tucked in its corner. "
            f"{h} learned that the cloth had not broken the bell; it had hidden the ring.",
            question="What did the friends learn about the missing ring?",
            cause="The gingham fold held the ring because the bell had been wrapped too tightly.",
            result=f"{h} learned where the ring was and stopped pulling the bell's string.")
        world.say("hero", "Then let us place the ring back, softly.")
        world.say("friend", "And let the gingham tie the knot.")
        world.entities["moon-bell"].meters.update(ring=1, mended=1)
        world.scene(
            f"Together they fitted the ring beneath the bell and tied it with a gingham bow. "
            f"The moon-bell chimed once, twice, and three times above the gate.",
            question="How did the friends mend the moon-bell?",
            cause="They found the silver ring in the gingham fold and fitted it beneath the bell.",
            result="The bell rang three bright notes after the gingham bow was tied.")
        ending = f"The gate sang ding-ding-ding, while the gingham bow danced in the morning breeze."
    elif params.path == "moon":
        world.entities["moon"] = Entity(
            "moon", "the moon", location="sky", meters={"glow": 0, "mended": 0})
        world.scene(
            f"The moon hid behind a gray cloud and forgot to glow. "
            f"{h} waved a lantern, but the sky stayed dim.",
            question="Why was the night sky dim?",
            cause="The moon had slipped behind a cloud and lost its glow.",
            result="A lantern below could not make the hidden moon shine.")
        world.say("hero", "Should I climb the tallest hill?")
        world.say("friend", "Not yet. The gingham squares are humming a tune.")
        world.scene(
            f"{f} tapped four gingham squares. The cloth hummed a little lullaby, "
            f"and {h} learned that the silver moon needed a cheerful tune to remember its light.",
            question="What did the friends learn from the gingham cloth?",
            cause="The humming squares revealed that the moon needed a cheerful tune.",
            result=f"{h} learned that climbing the hill was not the answer.")
        world.say("hero", "Then I will sing, and you may keep the beat.")
        world.say("friend", "I will tap the cloth softly.")
        world.entities["moon"].meters.update(glow=1, mended=1)
        world.scene(
            f"{h} sang a small rhyme while {f} tapped the gingham cloth: "
            f"'Silver moon, shine soon!' The cloud parted, and the moon glowed like a pearl.",
            question="How did the friends restore the moon's glow?",
            cause="They sang the tune learned from the gingham cloth and tapped its squares.",
            result="The cloud parted and the moon shone brightly again.")
        ending = f"The moon smiled over the nursery roof, and the gingham cloth kept time with the stars."
    else:
        world.entities["rain-cloud"] = Entity(
            "rain-cloud", "the silver rain cloud", location="garden",
            meters={"rain": 0, "mended": 0})
        world.scene(
            f"The garden's flowers drooped beneath a silver rain cloud that would not rain. "
            f"{h} shook a watering can, but it held only one dusty drop.",
            question="Why did the garden flowers droop?",
            cause="The silver rain cloud had stopped sending down rain.",
            result="The watering can could not give the garden enough water.")
        world.say("hero", "Perhaps we should carry the flowers to the pond.")
        world.say("friend", "Wait. One gingham square is glowing blue.")
        world.scene(
            f"{f} showed {h} the glowing square. It whispered that the rain cloud was thirsty "
            f"for one bright gingham square, so {h} learned what the cloud needed.",
            question="What did the glowing gingham square reveal?",
            cause="Its magic said that the thirsty rain cloud needed one bright square.",
            result=f"{h} learned to feed the cloud instead of moving the flowers.")
        world.say("hero", "Then I will hold the square up high.")
        world.say("friend", "And I will ask the cloud to share.")
        world.entities["rain-cloud"].meters.update(rain=1, mended=1)
        world.scene(
            f"{h} lifted the glowing gingham square, and {f} called a kind hello to the cloud. "
            f"Silver drops began to patter over the flowers until every petal stood tall.",
            question="How did the friends bring rain back to the garden?",
            cause="They held the glowing gingham square up for the thirsty cloud.",
            result="The cloud rained gently and the flowers lifted their petals.")
        ending = f"The garden drank its silver rain, and the gingham square twinkled like a tiny blue pond."

    world.scene(ending, kind="ending")
    check_sample(world)
    return world.sample()


def check_sample(world: World):
    path = world.params.path
    obj = world.entities[PATH_INFO[path]["object"]]
    if obj.meters.get("mended") != 1:
        raise StoryError("The chosen trouble was not visibly resolved.")
    speech = [e for e in world.history if e.kind == "speech"]
    if not any(world.entities["hero"].label in e.text for e in speech):
        raise StoryError("The hero must speak.")
    if not any(world.entities["friend"].label in e.text for e in speech):
        raise StoryError("The friend must speak.")
    if len([e for e in world.history if e.question]) != 3:
        raise StoryError("Each path needs three grounded questions.")
    if not world.history[-1].kind == "ending":
        raise StoryError("The story needs a final image.")


def valid_combos() -> list[tuple[str, str]]:
    return [(path, "gingham") for path in PATHS]


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("trouble", "bell", "missing_ring"),
         fact("trouble", "moon", "missing_glow"),
         fact("trouble", "rain", "missing_rain")]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "solves"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--path", choices=PATHS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [n for n in NAMES if n != hero]
    friend = args.friend or rng.choice(friend_choices)
    return StoryParams(hero=hero, friend=friend,
                       path=args.path or rng.choice(PATHS),
                       seed=args.seed)


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about the available paths.")
    count = 0
    for path in PATHS:
        sample = generate(StoryParams(path=path))
        check_sample(sample.world)
        count += 1
    print(f"OK: {count} story paths; Python and ASP agree.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": {k: asdict(v) for k, v in sample.world.entities.items()},
            "history": [asdict(e) for e in sample.world.history],
        }, indent=2))


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
            paths = [p for p in PATHS if args.path is None or p == args.path]
            if not paths:
                raise StoryError("No path matches the selected options.")
            params_list = [
                StoryParams(
                    hero=args.hero or rng.choice(NAMES),
                    friend=args.friend or rng.choice([n for n in NAMES if n != (args.hero or "")]),
                    path=path,
                    seed=args.seed + index,
                )
                for index, path in enumerate(paths)
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(p) for p in params_list]
        if args.json:
            data = [s.to_dict() for s in samples]
            print(json.dumps(data[0] if len(data) == 1 else data,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
