#!/usr/bin/env python3
"""A gentle bedtime story about sharing a nose-shaped treasure and noticing a hint."""

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
    child: str = "Mira"
    companion: str = "Toby"
    path: str = "lantern"
    seed: int = 777


NAMES = ("Mira", "Toby", "Lina", "Owen", "Nia", "Pip")
PATHS = ("lantern", "puppet", "garden")
PROMPT = "Write a warm bedtime story about sharing a nose-shaped object and noticing a helpful clue."
ASP_RULES = """
valid(lantern). valid(puppet). valid(garden).
#show valid/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity("child", params.child, "character",
                            memes={"curiosity": 1.0, "kindness": 0.5}),
            "companion": Entity("companion", params.companion, "character",
                                memes={"curiosity": 0.5, "kindness": 0.5}),
            "nose": Entity("nose", "the round red nose", "object",
                           location="bedroom", meters={"shared": 0, "found": 0}),
        }
        self.history: list[Event] = []

    def scene(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result))

    def say(self, speaker: str, words: str):
        self.history.append(Event("speech", f'{self.entities[speaker].label} said, "{words}"'))

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
                QAItem("What was shared in every story?",
                       "The children shared a round red nose-shaped object."),
                QAItem("Why did the children watch for a clue?",
                       "A small clue helped them decide what kind thing to do next."),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("The story path must be lantern, puppet, or garden.")
    if params.child == params.companion:
        raise StoryError("The two characters need different names.")
    if any(not name or not name[0].isupper() for name in (params.child, params.companion)):
        raise StoryError("Character names must begin with capital letters.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child, companion, nose = (world.entities[key] for key in ("child", "companion", "nose"))
    c, f = child.label, companion.label
    rng = random.Random(params.seed)
    soft = rng.choice(("The moonlight lay softly across the room.",
                       "The sleepy house hummed beneath the moon.",
                       "A silver patch of moonlight rested on the rug."))

    world.scene("beginning",
                f"{soft} {c} found {nose.label} beside the pillow and held it up for {f} to see.")
    world.say("child", "This funny nose can be our bedtime treasure.")
    world.say("companion", "Only if we share it.")

    if params.path == "lantern":
        world.scene("trouble",
                    f"{c} tucked the nose into a blanket fort, but the fort became dark when the last lamp was turned low.",
                    question="Why did the blanket fort become difficult to use?",
                    cause=f"{c} hid the shared nose inside the fort while the room grew dark.",
                    result="The children could not see where to place their story cards.")
        world.say("companion", "I can feel the nose, but I cannot see our cards.")
        world.say("child", "Look at its shiny side. It caught the moonlight earlier.")
        world.scene("learning",
                    f"{f} held the nose near the window and saw a thin bright mark on the floor.",
                    question="What did the children learn from the nose?",
                    cause="The nose reflected a small line of moonlight.",
                    result="That line showed them where the missing story cards had slipped.")
        world.say("companion", "The bright mark points under the pillow.")
        world.say("child", "Then we will share the light and search together.")
        nose.meters["shared"] = 1
        nose.meters["found"] = 1
        nose.location = "between pillows"
        world.scene("resolution",
                    f"They took turns holding the nose by the window. The moonlit mark led them to the cards, and {c} placed the nose between their pillows.",
                    question="How did sharing the nose solve the bedtime problem?",
                    cause="The children passed the nose between them so its shine could guide their search.",
                    result="They found the cards and left the nose between their pillows as a shared night-light.")

    elif params.path == "puppet":
        world.scene("trouble",
                    f"{f} wanted to make a sleepy puppet, but {c} kept the nose in one hand and the puppet's face stayed unfinished.",
                    question="Why could the puppet not become a face?",
                    cause=f"{c} was holding the only nose-shaped piece.",
                    result="The puppet had eyes and a smile but no nose.")
        world.say("companion", "May I borrow it for the puppet's face?")
        world.say("child", "Yes, but I want to tell the puppet good night too.")
        world.scene("learning",
                    f"{f} noticed a loose red thread beside the puppet and understood that the nose could be tied on gently and removed later.",
                    question="What useful thing did the children discover?",
                    cause=f"{f} noticed a loose red thread beside the puppet.",
                    result="They learned they could attach the nose safely and take it off when the puppet's story ended.")
        world.say("companion", "We can both use it if we take turns.")
        world.say("child", "You make the puppet smile, and I will give it the good-night voice.")
        nose.meters["shared"] = 1
        nose.meters["found"] = 1
        nose.location = "puppet"
        world.scene("resolution",
                    f"{f} tied the nose onto the puppet, and {c} gave it a tiny good-night bow. Then they untied it and placed it between their beds.",
                    question="How did the children share the nose with the puppet?",
                    cause="They used the loose thread to attach the nose briefly, then took turns giving the puppet a voice.",
                    result="The puppet became part of bedtime, and the nose returned to its place between the children.")

    else:
        world.scene("trouble",
                    f"{c} carried the nose to the window garden, where a sleepy moth fluttered away each time the children reached for it.",
                    question="Why did the moth keep flying away?",
                    cause="The children reached quickly toward the moth in the dim garden.",
                    result="Their sudden hands frightened it before they could watch its silver wings.")
        world.say("companion", "The moth is hiding whenever we rush.")
        world.say("child", "What if we share the nose as a quiet marker and wait?")
        world.scene("learning",
                    f"{c} placed the nose on a flat stone. Its red color showed both children where to sit, and the moth returned when they grew still.",
                    question="What did the children learn while watching the garden?",
                    cause="The nose gave them one calm place to sit and wait.",
                    result="The moth returned when both children stopped reaching.")
        world.say("companion", "It likes our quiet sharing.")
        world.say("child", "We can watch without trying to hold it.")
        nose.meters["shared"] = 1
        nose.meters["found"] = 1
        nose.location = "garden stone"
        world.scene("resolution",
                    f"They watched the moth circle the flowers. Before bed, {c} and {f} carried the nose back together and set it between their pillows.",
                    question="How did the children protect the moth's visit?",
                    cause="They shared the nose as a marker instead of grabbing at the moth.",
                    result="They sat quietly, saw the moth return, and carried their shared treasure home.")

    child.memes["kindness"] = 1.0
    companion.memes["kindness"] = 1.0
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    nose = world.entities["nose"]
    if nose.meters["shared"] != 1 or nose.meters["found"] != 1:
        raise StoryError("The nose must be shared and used in the resolution.")
    if len(sample.story_qa) < 2:
        raise StoryError("Each path needs two grounded questions.")
    speech = [e for e in world.history if e.kind == "speech"]
    if not any("share" in e.text.lower() for e in speech):
        raise StoryError("The dialogue must make sharing matter.")
    if not any(e.kind == "resolution" for e in world.history):
        raise StoryError("The story needs a visible resolution.")


def valid_combos() -> list[str]:
    return list(PATHS)


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("valid", path) for path in PATHS)


def asp_combos() -> set[tuple[str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--path", choices=PATHS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    companion = args.companion or rng.choice(tuple(name for name in NAMES if name != child))
    path = args.path or rng.choice(PATHS)
    return StoryParams(child=child, companion=companion, path=path, seed=args.seed)


def verify():
    if asp_combos() != {(path,) for path in PATHS}:
        raise StoryError("Python and ASP disagree about story paths.")
    for path in PATHS:
        sample = generate(StoryParams(path=path))
        check_sample(sample)
    print(f"OK: {len(PATHS)} complete story paths verified.")


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
            "entities": {key: asdict(value) for key, value in sample.world.entities.items()},
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
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            paths = [path for path in PATHS if args.path is None or path == args.path]
            if not paths:
                raise StoryError("No path matches the selected options.")
            params_list = [
                StoryParams(child=args.child or rng.choice(NAMES),
                            companion=args.companion or rng.choice(NAMES),
                            path=path, seed=args.seed)
                for path in paths
            ]
            for params in params_list:
                if params.child == params.companion:
                    params.companion = next(name for name in NAMES if name != params.child)
        else:
            params_list = []
            for _ in range(args.n):
                params = resolve_params(args, rng)
                params_list.append(params)
        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
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
