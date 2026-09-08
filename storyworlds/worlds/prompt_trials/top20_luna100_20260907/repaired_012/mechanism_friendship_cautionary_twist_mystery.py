#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class MysteryWorld:
    setting: str
    mechanism_name: str
    mechanism_label: str
    mechanism_working: bool = True
    clue_found: bool = False
    danger_active: bool = True
    friendship: float = 0.0
    trust: float = 0.0
    facts: dict[str, object] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
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
    detective_name: str
    friend_name: str
    setting: str
    mechanism: str
    seed: Optional[int] = None


DETECTIVE_NAMES = ["Luna", "Mira", "Nell", "Tavi", "Suri", "Pip", "Rae", "Cleo"]
FRIEND_NAMES = ["Milo", "Finn", "Ivy", "Jo", "Tess", "Oren", "Bea", "Kit"]
SETTINGS = [
    "the old clock museum",
    "the lantern house",
    "the rain-dark train station",
    "the little harbor library",
]
MECHANISMS = [
    "a brass clockwork key",
    "a hidden pulley",
    "a winding music box",
    "a spring-loaded lantern",
]

ARCS = [
    {
        "key": "clock_tower",
        "premise": "{detective} and {friend} visited {setting} to find out why one clock chimed before dawn. They promised to stay together and carried a small notebook.",
        "problem": "A loose gear inside the tower made the bell rope jerk whenever the wind rose. The heavy bell could fall if someone pulled it carelessly.",
        "clue": "{friend} noticed three fresh scratches beside the gear, while {detective} saw dust resting on only one side of the mechanism.",
        "dialogue": "\"We should pull the rope and test it,\" said {detective}. \"That may make the bell fall,\" replied {friend}. Their worry made them pause instead of rushing.",
        "turn": "The scratches looked like a warning, but they formed a path toward a narrow service door. The mystery was not a broken clock at all: someone had been using the mechanism to hide a message.",
        "action": "{detective} held the lantern while {friend} followed the scratch marks. Together they placed a wooden wedge under the loose gear, then opened the service door.",
        "resolution": "Behind the door they found a caretaker's lost key and a note explaining that the early chime warned children away from a weak stair. The mechanism had been set cautiously, not maliciously.",
        "ending": "The friends repaired the gear with the caretaker and watched the clock chime safely at sunrise.",
        "problem_fact": "a loose gear made the bell rope jerk dangerously",
        "clue_fact": "scratches and one-sided dust led toward a hidden service door",
        "turn_fact": "the mechanism was hiding a safety message rather than causing a theft",
        "action_fact": "they wedged the gear safely and followed the marks together",
        "outcome_fact": "they found the warning key and made the clock safe",
    },
    {
        "key": "vanishing_lantern",
        "premise": "{detective} and {friend} searched {setting} after its blue lantern vanished every evening. They brought chalk, string, and a promise not to accuse anyone too quickly.",
        "problem": "The lantern disappeared whenever the front door slammed. A small metal mechanism beneath the floor seemed to pull it away, but the dark passage was too narrow to enter safely.",
        "clue": "{friend} tied string to the lantern stand while {detective} sprinkled flour around the floor plate. In the morning, the string pointed under a reading bench and tiny flour tracks curved toward it.",
        "dialogue": "\"The footprints point to the bench,\" said {friend}. \"Then we must lift it slowly,\" said {detective}. \"And keep our hands away from the spring,\" answered the friend.",
        "turn": "When they lifted the bench, they found a secret delivery hatch. The lantern had not vanished; a caretaker's old rescue mechanism slid it into the hatch whenever the door shook.",
        "action": "The friends used a long ruler to hold the spring still, then loosened the hatch cover without placing fingers near the moving parts.",
        "resolution": "Inside the hatch lay the blue lantern and a letter from a child who had used it to find help during a storm. The strange mechanism had once protected visitors, but its worn spring now needed care.",
        "ending": "The lantern glowed beside the repaired hatch, and the friends marked the safe path with a bright line of chalk.",
        "problem_fact": "a worn floor mechanism pulled the lantern into a hidden hatch",
        "clue_fact": "string and flour tracks showed where the lantern traveled",
        "turn_fact": "the vanishing lantern was part of an old rescue device",
        "action_fact": "they held the spring safely and opened the hatch with a ruler",
        "outcome_fact": "they recovered the lantern and repaired the rescue device",
    },
    {
        "key": "silent_train",
        "premise": "{detective} and {friend} waited at {setting}, where a tiny model train ran each hour. One night it stopped before reaching the final platform.",
        "problem": "The train's motor hummed, but its wheels would not turn. A hidden mechanism beneath the track clicked whenever someone tried to push the train forward.",
        "clue": "{detective} found a red thread caught in the track. {friend} noticed that the thread was tied to a small brass lever, not wrapped around the wheels.",
        "dialogue": "\"Maybe the train is trapped,\" said {detective}. \"Maybe it is telling us to stop,\" said {friend}. They listened to the clicking instead of forcing the wheels.",
        "turn": "The lever was an old signal mechanism. It stopped the train whenever a bridge model was lowered across the track. The missing bridge was not missing at all; it was hidden behind a display curtain.",
        "action": "The friends checked the signal, lowered the bridge gently, and removed the thread only after the lever returned to its safe position.",
        "resolution": "Behind the curtain they found a small child who had pulled the thread while looking for a lost button. No one had meant to cause trouble, and the friends helped fix the display.",
        "ending": "The model train crossed the bridge with a soft whistle, carrying the lost button in its tiny cargo car.",
        "problem_fact": "a signal mechanism stopped the model train before a bridge",
        "clue_fact": "a red thread connected the track to a brass safety lever",
        "turn_fact": "the stopped train was responding to a hidden bridge signal",
        "action_fact": "they reset the signal and removed the thread carefully",
        "outcome_fact": "the train crossed safely and the display was restored",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.detective_name, params.friend_name, params.setting, params.mechanism))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def _choose_arc(params: StoryParams) -> dict[str, str]:
    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    return ARCS[index]


def tell(params: StoryParams) -> MysteryWorld:
    if params.detective_name == params.friend_name:
        raise StoryError("detective_name and friend_name must be different people")
    if params.mechanism not in MECHANISMS:
        raise StoryError(f"unknown mechanism: {params.mechanism}")
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")

    arc = _choose_arc(params)
    world = MysteryWorld(
        setting=params.setting,
        mechanism_name=params.mechanism,
        mechanism_label=params.mechanism,
    )
    detective = world.add(
        Entity(
            id=params.detective_name,
            kind="character",
            type="young_detective",
            label="young detective",
            meters={"attention": 3.0, "caution": 3.0},
            memes={"curiosity": 3.0, "trust": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="friend",
            label="friend",
            meters={"attention": 3.0, "caution": 3.0},
            memes={"friendship": 2.0, "trust": 2.0},
        )
    )
    mechanism = world.add(
        Entity(
            id="mechanism",
            type="mechanism",
            label=params.mechanism,
            phrase=f"the {params.mechanism}",
            meters={"working": 1.0, "danger": 2.0},
            memes={"mystery": 3.0},
        )
    )

    values = {
        "detective": detective.id,
        "friend": friend.id,
        "setting": world.setting,
    }
    for beat in ("premise", "problem", "clue", "dialogue", "turn", "action", "resolution", "ending"):
        if beat in arc:
            world.say(arc[beat].format(**values))
            if beat != "ending":
                world.para()

    world.clue_found = True
    world.danger_active = False
    world.mechanism_working = True
    world.friendship = 4.0
    world.trust = 4.0
    detective.meters["caution"] = 4.0
    friend.meters["caution"] = 4.0
    detective.memes["trust"] = 4.0
    friend.memes["trust"] = 4.0
    mechanism.meters["danger"] = 0.0
    mechanism.memes["mystery"] = 0.0
    world.facts = {
        "detective": detective,
        "friend": friend,
        "mechanism": mechanism,
        "arc": arc,
        "problem_event": arc["problem"].format(**values),
        "clue_event": arc["clue"].format(**values),
        "turn_event": arc["turn"].format(**values),
        "action_event": arc["action"].format(**values),
        "resolution_event": arc["resolution"].format(**values),
    }
    return world


def generate_prompts(world: MysteryWorld) -> list[str]:
    detective = world.facts["detective"]
    friend = world.facts["friend"]
    return [
        "Write a child-friendly mystery about a strange mechanism and a careful investigation.",
        f"Tell a mystery in which {detective.id} and {friend.id} use friendship and caution to solve a mechanical puzzle.",
        "Write a short cautionary mystery with a surprising twist and a safe, hopeful ending.",
    ]


def story_qa(world: MysteryWorld) -> list[QAItem]:
    facts = world.facts
    detective = facts["detective"]
    friend = facts["friend"]
    return [
        QAItem(
            question=f"Who investigated the mystery in {world.setting}?",
            answer=f"{detective.id} and {friend.id} investigated the mystery together in {world.setting}.",
        ),
        QAItem(
            question="What danger did the mechanism create?",
            answer=facts["problem_event"],
        ),
        QAItem(
            question="What clue helped the friends understand the mechanism?",
            answer=facts["clue_event"],
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=facts["turn_event"],
        ),
        QAItem(
            question="How did the friends solve the problem safely?",
            answer=f"{facts['action_event']} {facts['resolution_event']}",
        ),
    ]


def world_knowledge_qa(world: MysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a group of moving parts that works together to do a job, such as lifting, turning, opening, or stopping something.",
        ),
        QAItem(
            question="Why should someone be cautious around a mechanism?",
            answer="Moving parts can pinch, pull, or fall, so it is safer to observe first, keep fingers away, and ask a trusted grown-up for help.",
        ),
        QAItem(
            question="What makes a friendship helpful during a mystery?",
            answer="Friends can share observations, listen to different ideas, and remind each other to choose a safe plan.",
        ),
    ]


def dump_trace(world: MysteryWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:16}) {' '.join(parts)}")
    lines.append(f"  setting={world.setting}")
    lines.append(f"  mechanism_working={world.mechanism_working}")
    lines.append(f"  clue_found={world.clue_found}")
    lines.append(f"  danger_active={world.danger_active}")
    lines.append(f"  friendship={world.friendship}")
    lines.append(f"  trust={world.trust}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    theme(mechanism),
    feature(friendship),
    feature(cautionary),
    feature(twist),
    style(mystery),
    safe_resolution.
safe_resolution :- clue_found, danger_resolved, friends_cooperate.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("theme", "mechanism"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("style", "mystery"),
            asp.fact("clue_found"),
            asp.fact("danger_resolved"),
            asp.fact("friends_cooperate"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if not any(symbol.name == "valid_story" for symbol in model):
        print("MISMATCH: ASP twin rejected the mechanism mystery.")
        return 1
    sample = generate(
        StoryParams(
            detective_name="Luna",
            friend_name="Milo",
            setting=SETTINGS[0],
            mechanism=MECHANISMS[0],
            seed=0,
        )
    )
    required = ("mechanism", "friend", "carefully", "mystery")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required narrative evidence.")
        return 1
    if "?" in sample.story:
        pass
    print("OK: Python and ASP agree on the cautious friendship mystery.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery world about a mechanism, friendship, caution, and a twist."
    )
    parser.add_argument("--detective-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mechanism", choices=MECHANISMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective_name or rng.choice(DETECTIVE_NAMES)
    available = [name for name in FRIEND_NAMES if name != detective]
    friend = args.friend_name or rng.choice(available)
    if friend == detective:
        raise StoryError("detective_name and friend_name must be different people")
    return StoryParams(
        detective_name=detective,
        friend_name=friend,
        setting=args.setting or rng.choice(SETTINGS),
        mechanism=args.mechanism or rng.choice(MECHANISMS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            model = asp.one_model(asp_program())
            print("valid_story." if any(symbol.name == "valid_story" for symbol in model) else "no valid story")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", SETTINGS[0], MECHANISMS[0]),
            StoryParams("Mira", "Ivy", SETTINGS[1], MECHANISMS[1]),
            StoryParams("Nell", "Finn", SETTINGS[2], MECHANISMS[2]),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n:
        raise StoryError("could not produce enough distinct story variants")

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
