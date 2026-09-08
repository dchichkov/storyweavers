#!/usr/bin/env python3
"""
A standalone adventure storyworld about a tandem journey.

Two young riders must travel together to return a lost bell to a hilltop
lookout before sunset. Their first rush causes trouble, but listening,
sharing the pedals, and trusting one another lead to a happy ending and a
lesson learned.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class TrailWorld:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    rider_one: str
    rider_two: str
    trail: str
    destination: str
    treasure: str
    obstacle_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    turn_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


RIDER_NAMES = ["Luna", "Milo", "Ari", "Nia", "Theo", "Zoe"]
TRAILS = ["the pine trail", "the river path", "the rocky ridge"]
DESTINATIONS = ["the hilltop lookout", "the old fire tower", "the lighthouse garden"]
TREASURES = ["the brass trail bell", "the silver map tube", "the red signal flag"]

SCENES = [
    {
        "problem": "a fallen branch blocked the narrow trail",
        "clue": "fresh wheel marks showed that the path beside the stream was still firm",
        "turn": "they stopped pedaling, lifted the front wheel together, and carried the tandem around the branch",
        "result": "the riders reached the lookout before the last stripe of sunlight disappeared",
        "image": "the returned bell rang above the valley as orange light touched the handlebars",
        "lesson": "a tandem adventure works when both riders move with care instead of trying to lead alone",
    },
    {
        "problem": "a sudden shower turned the red clay into a slippery ribbon",
        "clue": "flat stones made a dry line beneath the cedar trees",
        "turn": "they shared the steering, slowed their pedals, and followed the stones beneath the trees",
        "result": "the riders arrived safely while raindrops glittered on the lookout rail",
        "image": "the treasure rested under a dry cloth while a rainbow opened over the trail",
        "lesson": "slowing down together can carry friends farther than rushing ahead",
    },
    {
        "problem": "the trail split into two paths beside a mossy sign",
        "clue": "a tiny arrow scratched into the sign pointed toward the stream crossing",
        "turn": "they read the arrow together and chose the path with the blue stones",
        "result": "the correct path led them to the destination just as the keeper lit the lantern",
        "image": "the lantern shone on two muddy pairs of boots beside the waiting tandem",
        "lesson": "good teamwork means sharing what you notice before making a choice",
    },
    {
        "problem": "one pedal began to wobble halfway up the ridge",
        "clue": "the repair pouch held a small wrench clipped beneath the back seat",
        "turn": "they leaned the tandem against a stump and tightened the pedal before continuing",
        "result": "the bicycle climbed the final bend and delivered its important cargo",
        "image": "the repaired pedal flashed while the destination flag waved in the evening wind",
        "lesson": "asking for help and checking your tools can turn a setback into progress",
    },
    {
        "problem": "a family of ducklings blocked the bridge",
        "clue": "the mother duck guided them toward a quiet patch of reeds",
        "turn": "they waited silently, then rolled across only after the ducklings had waddled away",
        "result": "they crossed without frightening the ducks and arrived with time to spare",
        "image": "the ducklings bobbed below the bridge while the treasure gleamed in its basket",
        "lesson": "an adventure is better when we protect the small travelers who share our path",
    },
]

OPENINGS = [
    "At dawn, {one} and {two} found an important message tied to their tandem.",
    "The mountain keeper needed help, so {one} and {two} set off on their tandem.",
    "A bright bell had to reach {destination} before sunset, and {one} and {two} volunteered.",
    "{one} and {two} gripped the handlebars as their tandem waited at the edge of {trail}.",
]

DIALOGUES = [
    '"I can pedal faster!" said {one}. "And I can steer better!" said {two}.',
    '"Let us listen to the trail," said {one}. "Together," agreed {two}.',
    '"I see something ahead," said {one}. "Tell me before we move," replied {two}.',
    '"We are a team, not a race," said {one}. {two} nodded. "Then we will match our rhythm."',
]

ENDINGS = [
    "The keeper smiled and thanked them for bringing the treasure.",
    "The keeper hung the treasure in its place and gave them each a warm cup of cocoa.",
    "A cheer rose from the lookout, and the keeper promised to tell everyone about their brave teamwork.",
]


def valid_combo(params: StoryParams) -> bool:
    if not params.rider_one or not params.rider_two:
        return False
    if params.rider_one == params.rider_two:
        return False
    if not params.trail or not params.destination or not params.treasure:
        return False
    return True


def build_world(params: StoryParams) -> TrailWorld:
    if not valid_combo(params):
        raise StoryError("A tandem adventure needs two different riders and a complete destination.")
    world = TrailWorld()
    one = world.add(Entity(
        "rider_one", "child", params.rider_one,
        meters={"energy": 1.0, "balance": 0.8},
        memes={"confidence": 0.7, "patience": 0.4},
    ))
    two = world.add(Entity(
        "rider_two", "child", params.rider_two,
        meters={"energy": 1.0, "balance": 0.8},
        memes={"confidence": 0.6, "patience": 0.5},
    ))
    bike = world.add(Entity(
        "tandem", "vehicle", "the tandem",
        meters={"wheels": 2.0, "shared_pedals": 1.0, "distance": 0.0},
        memes={"trust": 0.4, "teamwork": 0.2},
        props={"owner": "rider_one_and_rider_two"},
    ))
    cargo = world.add(Entity(
        "treasure", "object", params.treasure,
        meters={"safe": 1.0, "importance": 1.0},
        memes={"hope": 1.0},
        props={"destination": params.destination},
    ))
    scene = SCENES[params.obstacle_id % len(SCENES)]
    world.facts.update(
        one=one,
        two=two,
        bike=bike,
        cargo=cargo,
        scene=scene,
        trail=params.trail,
        destination=params.destination,
        resolved=False,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        one=params.rider_one,
        two=params.rider_two,
        trail=params.trail,
        destination=params.destination,
    ))
    world.say(
        f"Their basket held {params.treasure}, which belonged at {params.destination} "
        "before the evening lantern was lit."
    )
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        one=params.rider_one,
        two=params.rider_two,
    ))
    world.say(
        f"They started along {params.trail}, but {scene['problem']}. "
        f"The tandem shivered to a stop."
    )
    one.memes["confidence"] -= 0.1
    two.memes["patience"] += 0.2

    world.say(f'"Wait," said {params.rider_two}. "The clue may be {scene["clue"]}."')
    world.say(
        f'"Then we decide together," said {params.rider_one}. '
        '"One pedal at a time."'
    )
    world.para()

    world.say(f"They noticed that {scene['clue']}.")
    world.say(f"With both riders working carefully, {scene['turn']}.")
    bike.meters["distance"] += 1.0
    bike.memes["trust"] += 0.6
    bike.memes["teamwork"] += 1.0
    one.memes["patience"] += 0.5
    two.memes["patience"] += 0.5
    world.say(
        f'"Your turn to choose the pace," said {params.rider_one}. '
        f'"And your turn to watch the path," said {params.rider_two}.'
    )
    world.para()

    world.say(f"At last, {scene['result']}.")
    world.say(ENDINGS[params.ending_id % len(ENDINGS)])
    world.say(f"{scene['image']}.")
    world.say(
        f"{params.rider_one} and {params.rider_two} had learned that {scene['lesson']}."
    )
    world.facts["resolved"] = True
    cargo.memes["hope"] = 0.0
    return world


ASP_RULES = r"""
two_riders.
shared_pedals.
clue_checked.
teamwork.
delivered.

tandem_ready :- two_riders, shared_pedals, teamwork.
safe_arrival :- tandem_ready, clue_checked.
happy_ending :- safe_arrival, delivered.

#show tandem_ready/0.
#show safe_arrival/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    from storyworlds import asp
    return "\n".join([
        asp.fact("two_riders"),
        asp.fact("shared_pedals"),
        asp.fact("clue_checked"),
        asp.fact("teamwork"),
        asp.fact("delivered"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        symbols = asp.one_model(asp_program())
        names = {symbol.name for symbol in symbols}
        required = {"tandem_ready", "safe_arrival", "happy_ending"}
        if not required.issubset(names):
            print("MISMATCH: ASP twin did not reach the happy ending.")
            return 1
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1

    params = StoryParams("Luna", "Milo", TRAILS[0], DESTINATIONS[0], TREASURES[0])
    sample = generate(params)
    if not sample.world or not sample.world.facts.get("resolved"):
        print("MISMATCH: Python story did not resolve.")
        return 1
    if "tandem" not in sample.story.lower() or "learned" not in sample.story.lower():
        print("MISMATCH: story lost the required narrative instruments.")
        return 1
    print("OK: Python and ASP both describe a resolved tandem adventure.")
    return 0


def generation_prompts(world: TrailWorld) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure about {f['one'].label} and {f['two'].label} traveling by tandem to {f['destination']}.",
        f"Include this obstacle: {f['scene']['problem']}, then use the clue that {f['scene']['clue']}.",
        "End with a happy ending and a clear lesson learned about teamwork.",
    ]


def story_qa(world: TrailWorld) -> list[QAItem]:
    f = world.facts
    one = f["one"].label
    two = f["two"].label
    scene = f["scene"]
    return [
        QAItem(
            f"Why did {one} and {two} ride the tandem?",
            f"They rode the tandem to carry {f['cargo'].label} to {f['destination']} before the evening lantern was lit.",
        ),
        QAItem(
            "What problem stopped the riders?",
            f"The riders had to handle a challenge because {scene['problem']}.",
        ),
        QAItem(
            "What clue helped them choose what to do?",
            f"They noticed that {scene['clue']}.",
        ),
        QAItem(
            "How did the riders solve the problem?",
            f"They worked together so that {scene['turn']}.",
        ),
        QAItem(
            "What lesson did they learn?",
            f"They learned that {scene['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: TrailWorld) -> list[QAItem]:
    return [
        QAItem(
            "What is a tandem?",
            "A tandem is a bicycle built for two riders who share the ride and pedal together.",
        ),
        QAItem(
            "Why is teamwork useful on an adventure?",
            "Teamwork lets travelers share observations, make safer choices, and help one another through obstacles.",
        ),
        QAItem(
            "What makes an ending happy?",
            "A happy ending shows that the important problem was solved and the characters are safe, grateful, or together.",
        ),
        QAItem(
            "What is a lesson learned?",
            "A lesson learned is a useful idea the characters understand because of what happened to them.",
        ),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    one = args.rider_one or rng.choice(RIDER_NAMES)
    choices = [name for name in RIDER_NAMES if name != one]
    two = args.rider_two or rng.choice(choices)
    if one == two:
        raise StoryError("The two tandem riders must have different names.")
    return StoryParams(
        rider_one=one,
        rider_two=two,
        trail=args.trail or rng.choice(TRAILS),
        destination=args.destination or rng.choice(DESTINATIONS),
        treasure=args.treasure or rng.choice(TREASURES),
        obstacle_id=rng.randrange(len(SCENES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        turn_id=rng.randrange(len(SCENES)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: TrailWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind}; meters={entity.meters}; "
            f"memes={entity.memes}; props={entity.props}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tandem adventure storyworld.")
    parser.add_argument("--rider-one")
    parser.add_argument("--rider-two")
    parser.add_argument("--trail")
    parser.add_argument("--destination")
    parser.add_argument("--treasure")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            from storyworlds import asp
            symbols = asp.one_model(asp_program())
            print("\n".join(str(symbol) for symbol in symbols))
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("Luna", "Milo", TRAILS[0], DESTINATIONS[0], TREASURES[0], 0, 0, 1, 0, 0),
            StoryParams("Ari", "Nia", TRAILS[1], DESTINATIONS[1], TREASURES[1], 1, 1, 3, 1, 1),
            StoryParams("Theo", "Zoe", TRAILS[2], DESTINATIONS[2], TREASURES[2], 3, 2, 0, 3, 2),
        ]
        samples = [generate(params) for params in presets]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 20):
            rng = random.Random(base_seed + attempts)
            attempts += 1
            try:
                sample = generate(resolve_params(args, rng))
            except StoryError:
                continue
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.rider_one} and {sample.params.rider_two}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
