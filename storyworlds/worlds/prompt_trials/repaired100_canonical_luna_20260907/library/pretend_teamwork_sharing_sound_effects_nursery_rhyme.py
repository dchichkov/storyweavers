#!/usr/bin/env python3
"""Pretend teamwork and sharing, with playful sound effects."""

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
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
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
    speaker: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Pip"
    pretend: str = "castle"
    prop: str = "boxes"
    sound: str = "drum"
    seed: int = 777


PRETENDS = {
    "castle": {
        "name": "a moonlit castle",
        "prop": "boxes",
        "ending": "a silver castle",
        "line": "The castle gate is wide!",
    },
    "train": {
        "name": "a bright pretend train",
        "prop": "chairs",
        "ending": "a cheerful little train",
        "line": "All aboard for the hill!",
    },
    "rocket": {
        "name": "a brave pretend rocket",
        "prop": "pillows",
        "ending": "a shiny rocket",
        "line": "Blast off to the starry sky!",
    },
}

SOUNDS = {
    "drum": ("Boom-boom!", "a cardboard drum"),
    "bell": ("Ding-ding!", "a silver bell"),
    "whistle": ("Toot-toot!", "a wooden whistle"),
}

NAMES = ("Luna", "Pip", "Milo", "Nia", "Toby", "Zara")
PROMPT = (
    "Write a nursery-rhyme-style children's story about friends who pretend, "
    "share props and sound effects, and learn that teamwork makes play better."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "playroom",
                           memes={"joy": 0.7, "trust": 0.5, "fairness": 0.5}),
            "friend": Entity("friend", params.friend, "character", "playroom",
                             memes={"joy": 0.7, "trust": 0.5, "fairness": 0.5}),
            "props": Entity("props", "the pretend props", "props", "playroom",
                            meters={"shared": 0, "used": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result,
                                  state=self.snapshot()))

    def say(self, speaker: str, text: str):
        if not text.endswith((".", "!", "?")):
            text += "."
        self.history.append(Event("speech", f'"{text}" said {self.entities[speaker].label}.',
                                  speaker=speaker, state=self.snapshot()))

    def share(self):
        props = self.entities["props"]
        props.meters["shared"] = 1
        props.meters["used"] = 1
        for key in ("hero", "friend"):
            self.entities[key].memes["fairness"] = 1.0
            self.entities[key].memes["trust"] = 1.0

    def sample(self) -> StorySample:
        qa = [
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in self.history if event.question
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=qa,
            world_qa=[
                QAItem(
                    "Why is sharing useful in pretend play?",
                    "Sharing lets each player use a prop or sound and helps the whole team build one game together.",
                )
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.pretend not in PRETENDS:
        raise StoryError("Choose castle, train, or rocket for the pretend game.")
    if params.prop != PRETENDS[params.pretend]["prop"]:
        raise StoryError("The selected prop must match the pretend game.")
    if params.sound not in SOUNDS:
        raise StoryError("Choose drum, bell, or whistle for the sound effect.")
    if params.hero == params.friend:
        raise StoryError("The teammates need different names.")
    if any(not name or not name[0].isupper() for name in (params.hero, params.friend)):
        raise StoryError("Names must begin with capital letters.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["props"].label = f"the {params.prop} and {SOUNDS[params.sound][1]}"
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    friend = world.entities["friend"].label
    pretend = PRETENDS[params.pretend]
    sound, sound_item = SOUNDS[params.sound]

    world.narrate(
        "beginning",
        f"{hero} and {friend} tapped their toes on the playroom floor. "
        f"They wished to pretend they were {pretend['name']}, with {params.prop} for building and {sound_item} for noise."
    )
    world.say("hero", f"I will be the captain, and I will use all the {params.prop}!")
    world.say("friend", f"Then I cannot build a part. Can we share the {params.prop}?")
    world.narrate(
        "problem",
        f"{hero} piled the {params.prop} in one tall heap. {friend} stood nearby with empty hands.",
        question="Why did the pretend game stumble at first?",
        cause=f"{hero} kept all the {params.prop}, so {friend} had no prop to use.",
        result="The teammates could not build or play together.",
    )
    world.say("hero", "But I found them first.")
    world.say("friend", "A team needs two sets of hands, even when there is one pile.")
    world.say("hero", "What if we make a sharing plan?")
    world.say("friend", "You build the front, and I build the back.")
    world.share()
    world.narrate(
        "plan",
        f"They counted the {params.prop}: one for {hero}, one for {friend}, and one between them.",
        question="How did the teammates fix the prop problem?",
        cause=f"They made a plan to share the {params.prop} between both builders.",
        result=f"Each teammate built a part, while one prop stayed between them.",
    )
    world.say("hero", f"I will pass you a {params.prop} when you call.")
    world.say("friend", "And I will pass one back when your wall needs help.")
    world.say("hero", f"Ready for the {sound_item}?")
    world.say("friend", f"Ready! I will make the sound when the pretend door opens.")
    world.narrate(
        "teamwork",
        f"{hero} built the front and {friend} built the back. Then {hero} opened the door while {friend} made it say, {sound}",
        question="How did sound effects help the pretend game?",
        cause=f"{friend} used {sound_item} at the moment {hero} opened the pretend door.",
        result="The sound gave their shared game a clear and lively action.",
    )
    world.say("hero", pretend["line"])
    world.say("friend", sound)
    world.say("hero", "Your sound made my castle feel real.")
    world.say("friend", "Your building gave my sound a place to happen.")
    world.narrate(
        "ending",
        f"At last, the {params.prop} stood as {pretend['ending']}. "
        f"{hero} and {friend} bowed together while the playroom rang with {sound}",
        question="What did the friends learn about teamwork?",
        cause="They shared the props and matched each sound effect to a teammate's action.",
        result="Their pretend world became more fun because both friends helped create it.",
    )
    check_sample(world)
    return world.sample()


def check_sample(world: World):
    props = world.entities["props"]
    if props.meters["shared"] != 1 or props.meters["used"] != 1:
        raise StoryError("The story must show props being shared and used.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")):
        raise StoryError("Both teammates must reach a trusting resolution.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any(SOUNDS[world.params.sound][0] in event.text for event in world.history):
        raise StoryError("The chosen sound effect must appear in the story.")


ASP_RULES = """
can_share(hero, friend).
can_share(friend, hero).
playable(P) :- prop(P), shared(P).
teamwork(P) :- playable(P), sound_used(P).
#show playable/1.
#show teamwork/1.
"""


def asp_facts() -> str:
    from asp import fact
    params = [
        fact("prop", "props"),
        fact("shared", "props"),
        fact("sound_used", "props"),
    ]
    return "\n".join(params)


def asp_status() -> set[tuple]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "teamwork"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--pretend", choices=tuple(PRETENDS))
    parser.add_argument("--prop", choices=tuple(item["prop"] for item in PRETENDS.values()))
    parser.add_argument("--sound", choices=tuple(SOUNDS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pretend = args.pretend or rng.choice(tuple(PRETENDS))
    prop = args.prop or PRETENDS[pretend]["prop"]
    if prop != PRETENDS[pretend]["prop"]:
        raise StoryError("That prop does not fit the selected pretend game.")
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        pretend=pretend,
        prop=prop,
        sound=args.sound or rng.choice(tuple(SOUNDS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if not asp_status():
        raise StoryError("ASP did not find the teamwork state.")
    tested = 0
    for pretend, data in PRETENDS.items():
        for sound in SOUNDS:
            sample = generate(StoryParams(
                pretend=pretend,
                prop=data["prop"],
                sound=sound,
                seed=tested,
            ))
            check_sample(sample.world)
            tested += 1
    print(f"OK: {tested} pretend teamwork stories verified.")


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
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
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
            print(json.dumps(sorted(asp_status())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            choices = list(PRETENDS)
            samples = []
            for pretend in choices:
                data = PRETENDS[pretend]
                local = argparse.Namespace(**vars(args))
                local.pretend = pretend
                local.prop = data["prop"]
                samples.append(generate(resolve_params(local, rng)))
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(args.n)
            ]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
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
