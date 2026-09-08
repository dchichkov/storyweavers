#!/usr/bin/env python3
"""Luna's Luster Plank: a rhyming surprise on changing terrain."""

from __future__ import annotations

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
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Pip"
    terrain: str = "marsh"
    plank: str = "moonlit plank"
    surprise: str = "fireflies"
    seed: int = 777


TERRAINS = {
    "marsh": ("marsh", "The marsh hummed beneath a violet sky.", 0.8),
    "ravine": ("ravine", "The ravine echoed under a windy sky.", 1.0),
    "garden": ("garden", "The garden curled around a sleepy pond.", 0.45),
}

PLANKS = {
    "moonlit plank": ("moonlit plank", "silver", 1.2),
    "red plank": ("red plank", "red", 0.9),
    "old plank": ("old plank", "warm brown", 0.7),
}

SURPRISES = {
    "fireflies": ("fireflies", "Fireflies blinked like tiny stars.", "glow"),
    "frogs": ("frogs", "A choir of frogs sprang up with a bop.", "song"),
    "rabbits": ("rabbits", "Two rabbits popped out with a hop.", "hop"),
}

NAMES = ("Luna", "Milo", "Nia", "Pip", "Tess", "Oren")
PROMPT = "Write a rhyming children's story about a careful crossing, a changing terrain, and a kind surprise."


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind=kind, text=text, question=question,
                                  cause=cause, result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str):
        self.history.append(Event(kind="speech",
                                  text=f'"{text}" said {self.entities[speaker].label}.',
                                  state=self.snapshot()))


def validate_params(params: StoryParams):
    if params.terrain not in TERRAINS:
        raise StoryError("Choose a known terrain.")
    if params.plank not in PLANKS:
        raise StoryError("Choose a known plank.")
    if params.surprise not in SURPRISES:
        raise StoryError("Choose a known surprise.")
    if params.hero == params.helper:
        raise StoryError("The two adventurers need different names.")
    for name in (params.hero, params.helper):
        if not name or not name[0].isupper() or not name.isalpha():
            raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["hero"] = Entity(
        "hero", params.hero, "character", "near_bank",
        meters={"balance": 0.6, "courage": 0.6},
        memes={"worry": 0.6, "trust": 0.5},
    )
    world.entities["helper"] = Entity(
        "helper", params.helper, "character", "near_bank",
        meters={"balance": 0.7, "courage": 0.7},
        memes={"worry": 0.3, "trust": 0.6},
    )
    world.entities["plank"] = Entity(
        "plank", params.plank, "bridge", "ditch",
        meters={"strength": PLANKS[params.plank][2], "wetness": 0.0, "placed": 0},
        memes={"hope": 0.7},
    )
    world.entities["terrain"] = Entity(
        "terrain", TERRAINS[params.terrain][0], "terrain", "between_banks",
        meters={"slickness": TERRAINS[params.terrain][2], "safe": 0},
        memes={"mystery": 0.6},
    )
    world.entities["surprise"] = Entity(
        "surprise", SURPRISES[params.surprise][0], "surprise", "far_bank",
        meters={"revealed": 0},
        memes={"delight": 0.8},
    )
    return world


def check_ending(world: World):
    plank = world.entities["plank"]
    terrain = world.entities["terrain"]
    surprise = world.entities["surprise"]
    if not plank.meters["placed"] or terrain.meters["safe"] != 1:
        raise StoryError("The plank must be placed and the terrain made safe.")
    if not surprise.meters["revealed"]:
        raise StoryError("The surprise must be revealed.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "helper")):
        raise StoryError("The friends must finish by trusting one another.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    plank = world.entities["plank"]
    terrain = world.entities["terrain"]
    surprise = world.entities["surprise"]
    h, f = params.hero, params.helper
    terrain_name, terrain_line, slickness = TERRAINS[params.terrain]
    plank_name, color, strength = PLANKS[params.plank]
    surprise_name, surprise_line, surprise_kind = SURPRISES[params.surprise]

    world.narrate(
        "beginning",
        f"{h} found a {plank_name} beside the {terrain_name}. "
        f"{terrain_line} {h} tapped the board and began to sing: "
        f'"A plank for a path, a step for the day, '
        f"we'll cross this {terrain_name} in a careful way.\"",
    )
    world.say("helper", f"\"Wait, {h}! The {terrain_name} looks slick, and the plank may sway.\"")
    world.say("hero", "\"Then we will test it, not guess it. Will you help me?\"")
    world.say("helper", "\"I will hold one end while you check the ground.\"")
    world.narrate(
        "problem",
        f"The {terrain_name} shifted under {h}'s shoe. "
        f"The {plank_name} shone with {color} luster, but its middle dipped toward the mud.",
        question="Why could the friends not cross at once?",
        cause=f"The {terrain_name} was slick and the {plank_name} had not been secured.",
        result="A quick step might slide the board or tip it into the ditch.",
    )

    world.say("hero", "\"The left stone is firm, but the right side is loose.\"")
    world.say("helper", "\"I see it. Put the plank on the flat stones, not the soft moss.\"")
    world.say("hero", "\"And you keep your foot on this end?\"")
    world.say("helper", "\"Yes. When I say steady, you may step.\"")
    world.narrate(
        "plan",
        f"{h} brushed away moss while {f} held the {plank_name}. "
        "Together they found two flat stones beneath the uneven ground.",
        question="What plan did the friends make?",
        cause=f"{f} noticed that flat stones would support the {plank_name} better than moss.",
        result=f"{h} cleared the moss while {f} held the board steady.",
    )

    plank.location = "flat_stones"
    plank.meters["wetness"] = 0.0
    plank.meters["placed"] = 1
    terrain.meters["safe"] = 1
    hero.location = "plank_start"
    helper.location = "plank_end"
    hero.memes["worry"] = 0.2
    helper.memes["worry"] = 0.1
    world.narrate(
        "turn",
        f"The {plank_name} settled with a soft thump. "
        f"Its {color} luster ran from stone to stone like a little road of light.",
        question="How did the crossing become safer?",
        cause=f"The friends placed the {plank_name} on two flat stones after clearing away the moss.",
        result="The board stopped rocking, so the crossing had firm support.",
    )

    world.say("helper", "\"Steady! One step, then pause.\"")
    world.say("hero", "\"One step, then pause. I can do that.\"")
    hero.location = "far_bank"
    world.narrate(
        "crossing",
        f"{h} stepped, paused, and stepped again. {f} followed with a careful refrain: "
        '"Slow feet, bright eyes, and no surprise."',
        question="How did the friends cross the terrain?",
        cause=f"{h} followed {f}'s instruction to take one careful step and pause.",
        result="They crossed without slipping because they watched the board and the ground.",
    )

    surprise.location = "far_bank"
    surprise.meters["revealed"] = 1
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    helper.memes["trust"] = 1.0
    world.say("hero", "\"We made it! But what is that blinking by the reeds?\"")
    world.say("helper", f"\"A surprise! {surprise_line}\"")
    world.narrate(
        "surprise",
        f"At the far bank, {surprise_line} "
        f"The {surprise_name} had waited quietly while the friends solved the crossing.",
        question="What surprise waited on the far bank?",
        cause=f"The friends crossed carefully and reached the place where the {surprise_name} was hiding.",
        result=f"They discovered {surprise_name} together and shared the delight.",
    )
    world.say("hero", "\"The best surprise is one we can share.\"")
    world.say("helper", "\"Then let's sing it back across the plank!\"")
    world.narrate(
        "ending",
        f"Side by side they sang, \"Bright plank, safe ground, "
        f"new friends all around!\" The {plank_name} gleamed, "
        f"and the {surprise_name} answered with a {surprise_kind}.",
        question="What did the friends learn from the crossing?",
        cause="They listened to each other's observations and moved only after making the board steady.",
        result="Careful teamwork turned a slippery path into a shared adventure.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem("What is a plank used for in this story?",
                   f"The {plank_name} becomes a small bridge across the {terrain_name}."),
            QAItem("Why should someone test uneven terrain?",
                   "Testing it helps reveal slippery or weak places before a person steps across."),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speech = [event for event in sample.world.history if event.kind == "speech"]
    if len(speech) < 8:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any("?" in event.text for event in speech):
        raise StoryError("The dialogue must include a question.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs grounded questions and answers.")
    if "luster" not in sample.story or "plank" not in sample.story or "terrain" not in sample.story:
        raise StoryError("The required story words are missing.")


ASP_RULES = """
usable(T,P,S) :- terrain(T), plank(P), surprise(S), strong(P), safe_terrain(T).
crossing_ready(T,P) :- usable(T,P,_).
#show crossing_ready/2.
"""


def asp_facts() -> str:
    from asp import fact
    lines = []
    for key, (_, _, slickness) in TERRAINS.items():
        lines.append(fact("terrain", key))
        if slickness <= 1.0:
            lines.append(fact("safe_terrain", key))
    for key, (_, _, strength) in PLANKS.items():
        lines.append(fact("plank", key))
        if strength >= 0.7:
            lines.append(fact("strong", key))
    for key in SURPRISES:
        lines.append(fact("surprise", key))
    return "\n".join(lines)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "crossing_ready"))


def valid_combos() -> list[tuple[str, str]]:
    return [(terrain, plank) for terrain in TERRAINS for plank in PLANKS
            if TERRAINS[terrain][2] <= 1.0 and PLANKS[plank][2] >= 0.7]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--terrain", choices=tuple(TERRAINS))
    parser.add_argument("--plank", choices=tuple(PLANKS))
    parser.add_argument("--surprise", choices=tuple(SURPRISES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = valid_combos()
    terrain, plank = rng.choice([
        pair for pair in choices
        if args.terrain is None or pair[0] == args.terrain
        if args.plank is None or pair[1] == args.plank
    ])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    surprise = args.surprise or rng.choice(tuple(SURPRISES))
    params = StoryParams(hero=hero, helper=helper, terrain=terrain,
                         plank=plank, surprise=surprise, seed=args.seed)
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about valid crossing choices.")
    tested = 0
    for terrain, plank in valid_combos():
        for surprise in SURPRISES:
            sample = generate(StoryParams(terrain=terrain, plank=plank,
                                           surprise=surprise))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} ASP-compatible crossings.")


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
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            choices = [
                (terrain, plank, surprise)
                for terrain, plank in valid_combos()
                for surprise in SURPRISES
                if args.terrain is None or terrain == args.terrain
                if args.plank is None or plank == args.plank
                if args.surprise is None or surprise == args.surprise
            ]
            if not choices:
                raise StoryError("No valid combinations match these options.")
            for terrain, plank, surprise in choices:
                params_list.append(StoryParams(
                    hero=args.hero or "Luna",
                    helper=args.helper or "Pip",
                    terrain=terrain,
                    plank=plank,
                    surprise=surprise,
                    seed=args.seed,
                ))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

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


if __name__ == "__main__":
    raise SystemExit(main())
