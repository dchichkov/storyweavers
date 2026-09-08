#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle pirate tale about a historic shutter,
friendship, and problem solving.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "a historic harbor lighthouse"
SEED_WORDS = {"historic", "shutter"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("distance", "weight", "damage", "wind", "brightness"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "trust", "joy", "curiosity", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    captain: str = "Luna"
    friend: str = "Pip"
    ship: str = "The Little Comet"
    trial: int = 0
    narration: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    object_name: str
    trouble: str
    clue: str
    false_lead: str
    question: str
    method: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending_image: str


TRIALS = [
    Trial(
        object_name="the harbor lantern",
        trouble="the old wooden shutter slammed shut and left the lighthouse dark",
        clue="a bright brass pin lying beside the lower hinge",
        false_lead="a trail of wet footprints led toward the pier",
        question="The footprints show who came from the water, but what does the brass pin explain?",
        method="hold the shutter steady while the other checks the hinge box",
        discovery="found the missing hinge spring beneath a coil of rope",
        cause="had tugged the rope away from the wall and loosened the spring while trying to make room for a snack basket",
        repair="fitted the spring back into place, tied the rope safely, and polished the lantern together",
        proof="the shutter opened smoothly and the lantern shone across the calm water",
        lesson="Friends solve problems best when they ask what each clue can actually prove.",
        ending_image="the lighthouse beam swept over the waves like a golden welcome flag",
    ),
    Trial(
        object_name="the keeper's signal flag",
        trouble="a historic shutter caught the flag and tore its blue corner",
        clue="a strip of blue cloth snagged on the shutter's iron latch",
        false_lead="a gull carried another blue scrap toward the roof",
        question="The gull may have found loose cloth, but which clue touched the signal flag?",
        method="watch the roof while the other gently lifts the shutter from its latch",
        discovery="freed the flag from the shutter and found its corner folded inside the latch",
        cause="had pushed the shutter open during a gust without checking that the flag was clear",
        repair="stitched the corner, added a cloth tie, and practiced opening the shutter slowly",
        proof="the flag waved without catching when the next breeze arrived",
        lesson="A careful pause can protect something precious.",
        ending_image="the blue flag fluttered above the lighthouse like a piece of sky",
    ),
    Trial(
        object_name="the captain's brass compass",
        trouble="the compass vanished when the historic shutter banged during a storm",
        clue="a round clean mark on the dusty sill",
        false_lead="a black feather beside the map chest",
        question="The feather may belong to a visiting bird, but what object made the clean round mark?",
        method="search the deck while the other measures the sill and checks beneath the shutter",
        discovery="lifted the shutter and found the compass tucked in its wooden groove",
        cause="had placed the compass on the sill while watching the storm and forgotten it when the shutter swung",
        repair="dried the compass, rubbed oil into the hinge, and placed a safe tray beside the window",
        proof="the needle pointed north and the shutter stayed open against the mild breeze",
        lesson="Putting tools in one safe place prevents a later mystery.",
        ending_image="the compass gleamed beside the map while the repaired shutter framed the stars",
    ),
    Trial(
        object_name="a message from the harbor master",
        trouble="the message slipped behind a historic shutter before the crew could read it",
        clue="one corner of paper showing through a narrow hinge gap",
        false_lead="an empty bottle bobbing near the dock",
        question="The bottle is interesting, but which clue shows where the message is?",
        method="secure the shutter with a belt while the other reaches through the safe gap",
        discovery="pulled the message free without tearing its red wax seal",
        cause="had set the letter on the sill while opening the window and let the wind carry it behind the shutter",
        repair="read the message aloud, added a letter clip, and fixed the loose shutter catch",
        proof="the next letter stayed flat on the desk even when the window was open",
        lesson="Good problem solving combines a safe method with close attention.",
        ending_image="the sealed reply sailed toward the harbor master in a bright little rowboat",
    ),
]


@dataclass
class World:
    captain: Entity
    friend: Entity
    ship: Entity
    shutter: Entity
    lighthouse: Entity
    lantern: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def entity(eid: str, kind: str, type_: str, label: str, location: str = "") -> Entity:
    return Entity(eid, kind, type_, label, location=location)


def build_world(params: StoryParams) -> World:
    captain = entity(params.captain, "character", "child", "the young captain", "lighthouse")
    friend = entity(params.friend, "character", "child", "the first mate", "lighthouse")
    ship = entity("ship", "vehicle", "boat", params.ship, "harbor")
    shutter = entity("shutter", "object", "wooden_shutter", "the historic shutter", "lighthouse")
    lighthouse = entity("lighthouse", "place", "tower", "the harbor lighthouse", "cliff")
    lantern = entity("lantern", "object", "lamp", "the harbor lantern", "lighthouse")
    return World(captain, friend, ship, shutter, lighthouse, lantern)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    c, f, ship, shutter, lighthouse, lantern = (
        world.captain,
        world.friend,
        world.ship,
        world.shutter,
        world.lighthouse,
        world.lantern,
    )
    trial = TRIALS[params.trial % len(TRIALS)]

    c.memes["worry"] = 1
    f.memes["trust"] = 1
    c.memes["curiosity"] = 1
    shutter.meters["damage"] = 1
    shutter.meters["wind"] = 2
    lantern.meters["brightness"] = 0

    openings = [
        f"At dawn, {c.id} and {f.id} sailed {ship.label} toward {THEME}, where sailors still respected every old rope, bell, and {shutter.label}.",
        f"The little pirate crew reached {THEME} before breakfast. {c.id} carried a spyglass, and {f.id} carried the key to the lighthouse.",
        f"Sea mist curled around {THEME} as {c.id} and {f.id} climbed the stone steps with a sailor's promise to care for its historic treasures.",
        f"On a bright morning, {ship.label} rocked below {THEME}. The young friends had one important harbor job before sunset.",
    ]
    world.say(openings[params.narration % len(openings)])
    world.say(f"They planned to light {trial.object_name} so every boat could find the harbor safely.")
    world.say(f"Then {trial.trouble}.")
    world.say(
        f"{c.id} felt worried, because the lighthouse had guided their families for many years. "
        f"{f.id} stayed close and touched the old stone wall."
    )

    world.para()
    world.say(f"Near the steps, the friends noticed {trial.clue}. At the same time, {trial.false_lead}.")
    world.say(f"{c.id} asked, \"Should we follow the footprints?\"")
    world.say(
        f"{f.id} replied, \"Maybe, but {trial.question.lower()}\""
    )
    world.say(
        f"{c.id} nodded. \"You are right. We will test the clue before we make a pirate guess.\""
    )
    world.say(f"Together, they decided to {trial.method}.")
    c.memes["curiosity"] += 1
    f.memes["trust"] += 1
    c.memes["courage"] += 1
    f.memes["courage"] += 1

    world.para()
    world.say(
        f"The first idea led nowhere. The wet marks ended at a bucket, while the brass and wood clues stayed near the lighthouse."
    )
    world.say(f"The friends traded jobs and checked the place slowly. At last, they {trial.discovery}.")
    shutter.meters["damage"] = 0
    lantern.meters["brightness"] = 1
    shutter.location = "open"
    world.say(
        f"{f.id} took a breath. \"I remember now,\" {f.id} said. \"I {trial.cause}. I am sorry I did not tell you sooner.\""
    )
    world.say(
        f"{c.id} answered, \"Thank you for telling me. We can fix a mistake better when we know what happened.\""
    )
    f.memes["worry"] = 0
    c.memes["trust"] += 1
    f.memes["courage"] += 1

    world.para()
    world.say(f"The two friends {trial.repair}.")
    world.say(f"They tested the work: {trial.proof}.")
    c.memes["joy"] += 1
    f.memes["joy"] += 1
    c.memes["pride"] += 1
    f.memes["pride"] += 1
    world.say(f"Their lesson was simple: {trial.lesson}")
    world.say(f"As evening came, {trial.ending_image}.")
    world.say(
        f"{c.id} and {f.id} climbed aboard {ship.label}, pleased that friendship had helped them find a safe answer."
    )

    world.facts.update(
        captain=c,
        friend=f,
        ship=ship,
        shutter=shutter,
        lighthouse=lighthouse,
        lantern=lantern,
        resolved=True,
        trial=trial,
        object_name=trial.object_name,
        trouble=trial.trouble,
        clue=trial.clue,
        false_lead=trial.false_lead,
        discovery=trial.discovery,
        cause=trial.cause,
        repair=trial.repair,
        proof=trial.proof,
        lesson=trial.lesson,
        ending_image=trial.ending_image,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["captain"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"What problem did {c.id} and {friend.id} face at the lighthouse?",
            answer=f"They faced this problem: {f['trouble']}. It mattered because the lighthouse needed to guide boats safely.",
        ),
        QAItem(
            question=f"Which clue helped the friends solve the mystery?",
            answer=f"They focused on {f['clue']}, because it was connected to the historic shutter rather than only to the false lead.",
        ),
        QAItem(
            question=f"What did {friend.id} admit after the object was found?",
            answer=f"{friend.id} admitted that they {f['cause']}. The mistake was accidental, but telling the truth helped the friends repair it.",
        ),
        QAItem(
            question="How did friendship help with the problem?",
            answer=f"The friends listened to each other, tested clues instead of blaming anyone, and then they {f['repair']}.",
        ),
        QAItem(
            question="How did they know their solution worked?",
            answer=f"They tested it and saw that {f['proof']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a solid panel that can cover a window or opening. It can protect a room from wind, rain, or bright sunlight.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important because it belongs to the past or helps people remember something from the past.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, studying useful clues, trying a safe plan, and changing the plan when needed.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship in which people listen, help one another, and treat each other with trust and respect.",
        ),
        QAItem(
            question="What does a lighthouse do?",
            answer="A lighthouse shines a bright light from a tall tower to help boats notice the shore and travel safely.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly pirate tale about {f['captain'].id} and {f['friend'].id} solving this lighthouse problem: {f['trouble']}.",
        f"Use the words historic and shutter, include a brief dialogue exchange, and make the clue {f['clue']} change the characters' plan.",
        "Tell a story showing friendship and problem solving through careful evidence, an honest admission, and a concrete repaired ending.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in (
        world.captain,
        world.friend,
        world.ship,
        world.shutter,
        world.lighthouse,
        world.lantern,
    ):
        meters = {k: v for k, v in item.meters.items() if v}
        memes = {k: v for k, v in item.memes.items() if v}
        lines.append(
            f"  {item.id:10} ({item.kind:8}) location={item.location!r} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(historic_lighthouse).
feature(historic_lighthouse, historic).
feature(historic_lighthouse, shutter).
feature(historic_lighthouse, friendship).
feature(historic_lighthouse, problem_solving).

valid_story(S) :-
    setting(S),
    feature(S, historic),
    feature(S, shutter),
    feature(S, friendship),
    feature(S, problem_solving).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "historic_lighthouse"),
            asp.fact("feature", "historic_lighthouse", "historic"),
            asp.fact("feature", "historic_lighthouse", "shutter"),
            asp.fact("feature", "historic_lighthouse", "friendship"),
            asp.fact("feature", "historic_lighthouse", "problem_solving"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if not ok:
        print("MISMATCH: ASP rules rejected the historic shutter friendship domain.")
        return 1

    for params in (
        StoryParams(trial=0),
        StoryParams(trial=1, captain="Iris", friend="Nico"),
        StoryParams(trial=2, captain="Mara", friend="Sol"),
    ):
        sample = generate(params)
        if not sample.story or not {"historic", "shutter"} <= set(sample.story.lower().split()):
            print("MISMATCH: generated story missed required seed words.")
            return 1
        if not sample.story_qa:
            print("MISMATCH: generated story has no story questions.")
            return 1

    print("OK: ASP and Python recognize the historic shutter friendship domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--ship", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    captain = args.captain or rng.choice(["Luna", "Mara", "Iris", "Tessa", "Nell"])
    friend = args.friend or rng.choice(["Pip", "Nico", "Sol", "Bram", "Kit"])
    ship = args.ship or rng.choice(["The Little Comet", "The Blue Finch", "The Jolly Pebble"])
    if captain == friend:
        raise StoryError("The captain and friend must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        captain=captain,
        friend=friend,
        ship=ship,
        trial=offset % len(TRIALS),
        narration=(offset // len(TRIALS)) % 4,
        dialogue=(offset // (len(TRIALS) * 4)) % 4,
        ending=(offset // (len(TRIALS) * 4 * 4)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


CURATED = [
    StoryParams(captain="Luna", friend="Pip", ship="The Little Comet", trial=0),
    StoryParams(captain="Mara", friend="Nico", ship="The Blue Finch", trial=1),
    StoryParams(captain="Iris", friend="Sol", ship="The Jolly Pebble", trial=2),
    StoryParams(captain="Tessa", friend="Kit", ship="The Little Comet", trial=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n) and index < max(50, args.n * 50):
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
