#!/usr/bin/env python3
"""A kitten, a muddy slope, and a remembered way home."""

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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = ""
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
    child: str = "Luna"
    helper: str = "Milo"
    weather: str = "drizzle"
    tool: str = "plank"
    seed: int = 777


NAMES = ("Luna", "Milo", "Nia", "Theo", "Pia", "Owen")
WEATHERS = {
    "drizzle": "A soft drizzle had darkened the garden path.",
    "rain": "Rain had left the garden path shiny and brown.",
    "mist": "Mist rested low over the garden after breakfast.",
}
TOOLS = {
    "plank": "a short wooden plank",
    "mat": "a woven doormat",
    "crate": "an upside-down garden crate",
}

PROMPT = (
    "Write a gentle slice-of-life children's story about a child and a friend "
    "helping a kitten across a muddy slope, with a brief flashback that guides "
    "their solution and a small spoken exchange."
)

ASP_RULES = """
safe_tool(T) :- tool(T).
#show safe_tool/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "child": Entity(
                "child", params.child, "character", "porch",
                memes={"worry": 0.4, "patience": 0.5},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "porch",
                memes={"worry": 0.3, "patience": 0.6},
            ),
            "kitten": Entity(
                "kitten", "the small gray kitten", "animal", "slope",
                meters={"distance_to_shed": 5, "safe": 0},
                memes={"fear": 0.8, "trust": 0.2},
            ),
            "slope": Entity(
                "slope", "the muddy slope", "place", "garden",
                meters={"rise": 2, "length": 5, "slipperiness": 3},
            ),
            "tool": Entity(
                "tool", TOOLS[params.tool], "object", "shed",
                meters={"length": 2, "grip": 2, "stable": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(self, speaker: str, text: str, *, listener: str = ""):
        if not text.endswith((".", "?", "!")):
            text += "."
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {label} {verb}.',
                speaker=speaker,
                listener=listener,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "What helps a person stay safe on a muddy slope?",
                    "A person can move slowly, test each step, and use a stable surface for grip.",
                )
            ],
            world=self,
        )


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def flashback(world: World) -> None:
    child = world.entities["child"]
    child.beliefs["lesson"] = "flat support gives muddy feet a safer path"
    world.narrate(
        "flashback",
        f"{child.label} remembered last spring, when a wet board had helped "
        f"her grandfather cross a soft patch beside the compost bin. "
        f"He had said, 'Let the ground hold the board before your foot holds you.'",
    )


def place_tool(world: World) -> None:
    tool = world.entities["tool"]
    slope = world.entities["slope"]
    if world.entities["child"].beliefs.get("lesson") != "flat support gives muddy feet a safer path":
        raise StoryError("The remembered safety lesson must guide the repair.")
    tool.location = "slope"
    tool.meters["stable"] = 1
    slope.meters["slipperiness"] = 1


def help_kitten(world: World) -> None:
    kitten = world.entities["kitten"]
    tool = world.entities["tool"]
    if not tool.meters["stable"]:
        raise StoryError("The helper surface must be made stable before the kitten crosses.")
    kitten.location = "shed"
    kitten.meters["distance_to_shed"] = 0
    kitten.meters["safe"] = 1
    kitten.memes["fear"] = 0.1
    kitten.memes["trust"] = 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"].label
    helper = world.entities["helper"].label
    kitten = world.entities["kitten"].label
    tool = world.entities["tool"].label

    world.narrate(
        "beginning",
        f"{WEATHERS[params.weather]} {child} was carrying a bowl of milk "
        f"toward the shed when a tiny {kitten.lower()} appeared halfway down "
        f"the muddy slope. Its paws made four neat dots, then slid together.",
    )
    world.say("child", "Are you stuck, little one?", listener="kitten")
    world.say("helper", "I can bring a towel. Maybe we should not rush it.", listener="child")
    world.narrate(
        "problem",
        f"The {kitten.lower()} gave a thin mew and tried to climb. "
        f"The mud squeezed away beneath its paws, while the shed waited only "
        f"a few steps above.",
        question="Why could the kitten not simply climb the slope?",
        cause="The rain had made the slope slippery, so the kitten's paws slid instead of gripping.",
        result="The children decided to make a safer path rather than pull the kitten.",
    )
    world.say("child", "What if I pick it up?", listener="helper")
    world.say("helper", "It may scratch when it is frightened. What did you do last time?", listener="child")
    flashback(world)
    world.say("child", "I remember a board beside the compost bin. It made a firm little road.", listener="helper")
    world.say("helper", "Then let us make a road here, too.", listener="child")

    place_tool(world)
    world.narrate(
        "repair",
        f"{child} fetched {tool} from beside the shed. {helper} held one end "
        f"while {child} pressed the other end into the soft mud until it stopped wobbling.",
        question="How did the remembered idea change their plan?",
        cause="The flashback showed that a flat board could spread weight and give muddy feet a firm surface.",
        result=f"They placed {tool} across the slippery part instead of carrying the frightened kitten.",
    )
    world.say("child", "There is a dry edge now. Can you see it?", listener="kitten")
    world.say("helper", "Mew if you want us to wait.", listener="kitten")
    world.narrate(
        "turn",
        f"The kitten sniffed the {tool.lower()}. It placed one paw on the wood, "
        f"paused, and gave a softer mew. {child} sat on the upper side of the slope "
        f"while {helper} waited below with the milk bowl.",
        question="What showed that the kitten was beginning to trust the path?",
        cause="The kitten sniffed the board, stepped onto it, and answered with a softer mew.",
        result="The children stayed still and let the kitten choose its own pace.",
    )
    world.say("child", "One paw, then another. We are right here.", listener="kitten")
    world.say("helper", "The bowl is waiting, but you do not have to hurry.", listener="child")
    help_kitten(world)
    world.narrate(
        "ending",
        f"The kitten crossed the wooden path and reached the shed. {child} set "
        f"the milk beside it, and {helper} wiped the mud from the kitten's whiskers "
        f"with the corner of the towel. The kitten curled its tail around the bowl "
        f"and offered one pleased mew.",
        question="How did the story end differently from its worried beginning?",
        cause="At first the kitten was sliding alone on the muddy slope.",
        result="At the end it stood safely beside the shed, drinking milk after crossing the firm path.",
    )
    world.say("child", "Next time, we will check the path before the rain.", listener="helper")
    world.say("helper", "And we will keep the little road near the shed.", listener="child")
    sample = world.sample()
    check_sample(sample)
    return sample


def validate_params(params: StoryParams):
    if params.weather not in WEATHERS or params.tool not in TOOLS:
        raise StoryError("Choose a listed weather condition and a listed tool.")
    if params.child == params.helper:
        raise StoryError("The two children need different names.")
    for name in (params.child, params.helper):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words, such as Luna.")


def check_sample(sample: StorySample):
    world = sample.world
    kitten = world.entities["kitten"]
    tool = world.entities["tool"]
    if not kitten.meters["safe"] or kitten.location != "shed":
        raise StoryError("The kitten must reach the shed safely.")
    if not tool.meters["stable"] or tool.location != "slope":
        raise StoryError("The tool must become a stable path on the slope.")
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 10:
        raise StoryError("The story needs a sustained back-and-forth exchange.")
    speakers = {event.speaker for event in speech}
    if not {"child", "helper"} <= speakers:
        raise StoryError("Both children must speak.")
    if not any(event.kind == "flashback" for event in world.history):
        raise StoryError("The story must contain a flashback.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs several causal grounded questions.")
    if "mew" not in sample.story.lower():
        raise StoryError("The kitten's mew must appear in the story.")


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("tool", key) for key in TOOLS)


def asp_tools() -> set[tuple[str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "safe_tool"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--weather", choices=tuple(WEATHERS))
    parser.add_argument("--tool", choices=tuple(TOOLS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != child])
    params = StoryParams(
        child=child,
        helper=helper,
        weather=args.weather or rng.choice(tuple(WEATHERS)),
        tool=args.tool or rng.choice(tuple(TOOLS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_tools() != {(key,) for key in TOOLS}:
        raise StoryError("Python and ASP disagree about available tools.")
    count = 0
    for weather in WEATHERS:
        for tool in TOOLS:
            sample = generate(
                StoryParams(
                    child="Luna",
                    helper="Milo",
                    weather=weather,
                    tool=tool,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; ASP agrees on {len(TOOLS)} tools.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print(
            "\nTRACE\n"
            + json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


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
            print(json.dumps(sorted(asp_tools())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    child=args.child or "Luna",
                    helper=args.helper or "Milo",
                    weather=weather,
                    tool=tool,
                    seed=args.seed,
                )
                for weather in WEATHERS
                for tool in TOOLS
                if args.weather is None or args.weather == weather
                if args.tool is None or args.tool == tool
            ]
            for params in params_list:
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
