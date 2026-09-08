#!/usr/bin/env python3
"""
A small mythic animal story about a musician, a woof, and a curious rodent.
Repetition turns a strange sound into a clue, while curiosity helps the friends
discover why the valley keeps answering their song.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("energy", "attention", "distance", "readiness"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "joy", "courage", "trust", "wonder"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    musician_name: str = "Luna"
    woof_name: str = "Bramble"
    rodent_name: str = "Nix"
    place: str = "the Echoing Valley"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SCENARIOS = [
    {
        "object": "a silver flute",
        "sound": "one bright note",
        "echo": "the valley answered with two low notes",
        "clue": "the second answer always came after a small stone rolled downhill",
        "discovery": "a hollow stone beneath the old arch",
        "gift": "a clear song for travelers who had lost the path",
        "ending": "the moon shone inside the hollow stone like a listening eye",
    },
    {
        "object": "a little drum",
        "sound": "three gentle taps",
        "echo": "the hill returned three taps and then one",
        "clue": "the extra beat matched the steps of a tiny creature",
        "discovery": "a hidden tunnel where the wind beat on root walls",
        "gift": "a rhythm that guided rain into thirsty gardens",
        "ending": "small drops drummed a welcome on every leaf",
    },
    {
        "object": "a reed whistle",
        "sound": "a soft rising call",
        "echo": "the forest repeated it from behind the blue ferns",
        "clue": "the reply moved closer whenever Nix asked a new question",
        "discovery": "a shy spring guarded by an ancient listening tree",
        "gift": "a song that woke the spring without frightening it",
        "ending": "water curled from the roots and followed the melody",
    },
    {
        "object": "a bronze bell",
        "sound": "one warm chime",
        "echo": "the clouds gave back the chime at the same distance",
        "clue": "the sound was strongest beside a circle of standing stones",
        "discovery": "a stone doorway hidden beneath golden moss",
        "gift": "a bell-call that opened the doorway only for kind visitors",
        "ending": "the doorway glowed, but closed gently after the friends passed",
    },
]


def _index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in params.musician_name + params.woof_name + params.rodent_name)


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[_index(params) % len(SCENARIOS)]
    world = World()

    musician = world.add(Entity(params.musician_name, "character", "musician"))
    woof = world.add(Entity(params.woof_name, "character", "woof"))
    rodent = world.add(Entity(params.rodent_name, "character", "rodent"))
    instrument = world.add(Entity("instrument", "thing", "musical_instrument"))
    valley = world.add(Entity("valley", "place", "echoing_valley"))

    musician.memes["curiosity"] = 1
    rodent.memes["curiosity"] = 2
    woof.memes["trust"] = 1
    musician.meters["attention"] = 1
    rodent.meters["attention"] = 1

    world.say(
        f"In {params.place}, where stones remembered every song, "
        f"{musician.id} the musician traveled with {woof.id} the woof and {rodent.id} the rodent."
    )
    world.say(
        f"At dawn, {musician.id} played {scenario['object']}: {scenario['sound']}."
    )
    world.say(
        f"The friends waited. {scenario['echo'].capitalize()}. "
        f"{woof.id} lifted both ears, while {rodent.id} leaned toward the sound."
    )

    world.para()
    rodent.memes["curiosity"] += 2
    musician.meters["attention"] += 1
    musician.memes["worry"] += 1
    world.say(
        f"{musician.id} played the same phrase again, and then a third time. "
        f"Each repetition brought the same mysterious answer."
    )
    world.say(
        f"'Perhaps the valley is calling us,' said {rodent.id}. "
        f"'Woof?' asked {woof.id}. 'Yes,' said {musician.id}, 'but a song should not make us guess blindly.'"
    )
    world.say(
        f"They listened instead of rushing. The clue was that {scenario['clue']}."
    )

    world.para()
    musician.memes["courage"] += 1
    rodent.memes["wonder"] += 1
    woof.meters["readiness"] += 1
    world.say(
        f"Curiosity led {rodent.id} along the sound, while {woof.id} carefully sniffed the stones. "
        f"At last they found {scenario['discovery']}."
    )
    world.say(
        f"{musician.id} played the phrase once more. This time the friends heard a hidden pattern: "
        f"the repeated notes were not an order, but an invitation."
    )
    world.say(
        f"'Let us answer kindly,' said {musician.id}. "
        f"'And listen after we answer,' replied {rodent.id}. "
        f"{woof.id} gave one soft woof, and the valley grew quiet."
    )

    world.para()
    musician.memes["joy"] += 2
    rodent.memes["trust"] += 1
    woof.memes["joy"] += 1
    world.say(
        f"Together they made {scenario['gift']}. "
        f"The valley repeated the melody, not to copy it, but to carry it farther."
    )
    world.say(
        f"From that day on, the three friends used repetition to notice what stayed true "
        f"and curiosity to ask what they had not yet understood."
    )
    world.say(f"By nightfall, {scenario['ending']}.")

    world.facts.update(
        params=params,
        scenario=scenario,
        musician=musician,
        woof=woof,
        rodent=rodent,
        instrument=instrument,
        valley=valley,
        resolved=True,
        repetition=True,
        curiosity=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a myth about musician {params.musician_name}, a woof named {params.woof_name}, and rodent {params.rodent_name}.",
        f"Use repetition to reveal that {scenario['echo']}.",
        "Show curiosity changing a mystery into a kind discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params = facts["params"]
    scenario = facts["scenario"]
    return [
        QAItem(
            "Who traveled together in the myth?",
            f"{params.musician_name} the musician traveled with {params.woof_name} the woof and {params.rodent_name} the rodent."
        ),
        QAItem(
            "What did repetition reveal?",
            f"Repeating the musical phrase showed that {scenario['echo']}."
        ),
        QAItem(
            "Why did the rodent keep asking questions?",
            f"The rodent was curious and wanted to understand why the valley answered the music."
        ),
        QAItem(
            "How did the friends solve the mystery?",
            f"They listened carefully, followed the clue that {scenario['clue']}, and found {scenario['discovery']}."
        ),
        QAItem(
            "What lesson did the friends learn?",
            "They learned that repetition can reveal a pattern, while curiosity helps friends investigate without rushing."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        "What is a musician?",
        "A musician is someone who makes or performs music with a voice or an instrument."
    ),
    QAItem(
        "What is a woof?",
        "A woof is a short bark-like sound made by a dog or a doglike story creature."
    ),
    QAItem(
        "What is a rodent?",
        "A rodent is a mammal such as a mouse, rat, beaver, or squirrel whose front teeth keep growing."
    ),
    QAItem(
        "Why can repetition help someone learn?",
        "Repetition lets a person notice patterns, practice a skill, and remember what happened before."
    ),
    QAItem(
        "What does curiosity mean?",
        "Curiosity is the wish to learn more by noticing, wondering, and asking questions."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:12} ({entity.type:18}) "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts: repetition={world.facts.get('repetition')} curiosity={world.facts.get('curiosity')}")
    return "\n".join(lines)


ASP_RULES = r"""
musician(moon_singer).
woof(bramble).
rodent(nix).
repetition.
curiosity.
resolved.
pattern_found :- repetition, curiosity.
kind_answer :- pattern_found, resolved.
myth_complete :- kind_answer.
#show pattern_found/0.
#show kind_answer/0.
#show myth_complete/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("musician", "moon_singer"),
            asp.fact("woof", "bramble"),
            asp.fact("rodent", "nix"),
            asp.fact("repetition"),
            asp.fact("curiosity"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    required = {"pattern_found", "kind_answer", "myth_complete"}
    if not required.issubset(names):
        print("MISMATCH: ASP did not derive the complete myth.")
        return 1
    for seed in range(8):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story was not resolved.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story lacks QA.")
            return 1
    print("OK: ASP and Python agree that repetition and curiosity resolve the myth.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic musician, woof, and rodent storyworld.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--musician-name")
    parser.add_argument("--woof-name")
    parser.add_argument("--rodent-name")
    parser.add_argument("--place")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        musician_name=args.musician_name or rng.choice(["Luna", "Orin", "Mira", "Sol"]),
        woof_name=args.woof_name or rng.choice(["Bramble", "Puddle", "Clover", "Rook"]),
        rodent_name=args.rodent_name or rng.choice(["Nix", "Pip", "Tumble", "Moss"]),
        place=args.place or rng.choice(
            ["the Echoing Valley", "the Moonlit Hollow", "the Singing Woods"]
        ),
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
    StoryParams(musician_name="Luna", woof_name="Bramble", rodent_name="Nix", place="the Echoing Valley"),
    StoryParams(musician_name="Orin", woof_name="Clover", rodent_name="Pip", place="the Moonlit Hollow"),
    StoryParams(musician_name="Mira", woof_name="Rook", rodent_name="Moss", place="the Singing Woods"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pattern_found/0.\n#show kind_answer/0.\n#show myth_complete/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        print(asp.one_model(asp_program("#show pattern_found/0.\n#show kind_answer/0.\n#show myth_complete/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(args.n)
        ]
        for index, sample in enumerate(samples):
            sample.params.seed = base_seed + index

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
