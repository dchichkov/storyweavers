#!/usr/bin/env python3
"""
A small standalone Mystery storyworld about a friendship tested by a strange
mechanism, a cautionary mistake, and a revealing twist.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "inventor"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "watcher"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
    friend: str
    companion: str
    place: str
    mechanism_name: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    mechanism: str
    warning: str
    rash_action: str
    consequence: str
    clue: str
    careful_action: str
    twist: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


FRIENDS = ["Luna", "Mara", "Nia", "Poppy", "Suri", "Wren"]
COMPANIONS = ["Tobin", "Eli", "Finn", "Oren", "Pax", "Theo"]
PLACES = [
    "the old clock tower",
    "the lantern-lit museum",
    "the foggy riverside station",
    "the locked greenhouse",
    "the quiet hill observatory",
]
MECHANISM_NAMES = [
    "the brass whisperer",
    "the moonwheel",
    "the little answer machine",
    "the silver keywork",
]
TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "memory", "mystery", "promise", "question"]

SCENARIOS = [
    Scenario(
        "clock_tower",
        "were searching the old clock tower for a missing friendship medal",
        "a brass mechanism with three turning rings clicked behind the bell",
        "Never turn a mystery mechanism before you know what it protects.",
        "twisted all three rings at once",
        "the tower doors swung shut and every clock began chiming a different hour",
        "the smallest ring stopped whenever someone spoke a true memory",
        "spoke about the day they had first helped each other",
        "the mechanism was not a lock at all; it was listening for a promise strong enough to open the hidden room",
        "admitted that impatience had made the tower louder and harder to understand",
        "turned the rings one at a time while sharing honest memories",
        "the hidden room opened and the friendship medal shone beneath the bell",
        "careful listening protects both objects and friendships",
        "the medal rested between them as the tower finally struck one peaceful hour",
    ),
    Scenario(
        "greenhouse_latch",
        "were looking for the gardener's lost blue seed inside a locked greenhouse",
        "a glass-and-copper mechanism pulsed beside the moonflowers",
        "A warning label can be a kindness, not a challenge.",
        "pulled the bright lever marked with a red dot",
        "the roof vents opened and a cold wind scattered the seed trays",
        "one vine curled around the lever whenever someone blamed the other friend",
        "stopped arguing and examined the vine's pattern together",
        "the mechanism was a weather guide, and the red dot meant that the greenhouse was asking for warmth",
        "said sorry for blaming the other friend before checking the signs",
        "used a warm lantern and followed the vine's safe sequence",
        "the vents closed gently and the blue seed was found beneath a leaf",
        "a warning is useful when friends pause long enough to read it",
        "the blue seed glowed in its pot while two friends marked the warning clearly",
    ),
    Scenario(
        "museum_music",
        "were following a faint tune through a museum after the closing bell",
        "an old music mechanism turned by itself inside a glass case",
        "Do not break a case simply because the answer is hidden inside.",
        "tapped the glass with a heavy display stand",
        "the tune stopped and a row of tiny doors sprang open across the museum",
        "the same three notes appeared on their friendship bracelet",
        "played the notes softly on the nearby wooden xylophone",
        "the mechanism had been waiting for a matching friendship song, not a forceful rescue",
        "confessed that the tapping had frightened the museum's sleeping exhibits",
        "played the tune together and followed the doors in order",
        "the final door revealed the museum's lost welcome bell",
        "gentle clues can solve what force only scatters",
        "the welcome bell rang once, and the museum seemed to smile in the dark",
    ),
    Scenario(
        "river_station",
        "were carrying a message to a friend who had missed the last train",
        "a ticket mechanism blinked beneath the empty station clock",
        "A strange signal should be checked before it is trusted.",
        "fed the mechanism the only ticket they had",
        "the platform lights went dark and a false train whistle echoed from the tunnel",
        "the blink pattern matched the pauses in their friend's message",
        "counted the pauses instead of pushing another ticket inside",
        "the machine was a signal repeater sending their friend's message from the safe waiting room",
        "apologized for nearly using the only ticket as a guess",
        "followed the safe light pattern and answered with their lantern",
        "their friend found the correct platform and the message arrived",
        "checking a signal can keep friendship from becoming a fearful chase",
        "three lanterns blinked together while the last train rolled safely in",
    ),
    Scenario(
        "observatory_lens",
        "were trying to find a star-shaped clue in the hill observatory",
        "a silver mechanism shifted the telescope whenever the roof creaked",
        "Not every sudden movement means that someone is hiding something.",
        "accused the other friend of touching the controls",
        "the telescope swung toward a dark patch and the clue disappeared",
        "dust on the gear carried the shape of a tiny bird track",
        "cleaned the gear and watched which way the track pointed",
        "a nesting bird had been moving the mechanism to shelter its chick from the cold roof",
        "withdrew the accusation and promised to ask before guessing",
        "made a warm cover for the nest and reset the telescope slowly",
        "the star-shaped clue appeared in the correct window",
        "trust grows when friends replace blame with evidence",
        "the chick slept beside the quiet gear while the star clue blinked above it",
    ),
    Scenario(
        "lantern_archive",
        "were seeking an old map in the lantern-lit archive",
        "a drawer mechanism locked whenever its little glass eye saw a shadow",
        "A hurried shortcut may hide the very thing you need.",
        "covered the glass eye with a scarf",
        "the drawer opened halfway and folded the map into a narrow slot",
        "the mechanism opened fully when two shadows stood side by side",
        "placed their hands together beneath the lamp",
        "the drawer was designed to open for two friends carrying one shared light",
        "admitted that trying to trick it had damaged the map's corner",
        "held the map flat and turned the key together",
        "the missing route appeared across the restored map",
        "some doors are made to teach cooperation, not defeat it",
        "their joined shadows stretched across the map like one long road",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about friendship, caution, twists, and a mechanism."
    )
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mechanism-name", choices=MECHANISM_NAMES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    friend = args.friend or rng.choice(FRIENDS)
    companion = args.companion or rng.choice(COMPANIONS)
    place = args.place or rng.choice(PLACES)
    mechanism_name = args.mechanism_name or rng.choice(MECHANISM_NAMES)
    return StoryParams(
        friend=friend,
        companion=companion,
        place=place,
        mechanism_name=mechanism_name,
        seed=args.seed,
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    friend = params.friend
    companion = params.companion
    place = params.place
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Wait," {companion} warned as {friend} reached {place}. "That door was locked yesterday."',
            f"They had come because they {scenario.premise}.",
        ]
    if mode == "dialogue":
        return [
            f'"Do you hear that?" {friend} asked. "I hear a mystery," {companion} replied.',
            f"Together they entered {place because False}.",
        ]
    if mode == "countdown":
        return [
            f"The old clock counted down from five as {friend} and {companion} entered {place}.",
            f"They had only a little time to discover why they {scenario.premise}.",
        ]
    if mode == "memory":
        return [
            f"{friend} remembered that {place} had once been bright and busy.",
            f"Now the quiet place held a mystery: they {scenario.premise}.",
        ]
    if mode == "mystery":
        return [
            f"The first clue was a click from somewhere inside {place}.",
            f"{friend} and {companion} followed it because they {scenario.premise}.",
        ]
    if mode == "promise":
        return [
            f"{friend} had promised not to leave {companion} alone in {place}.",
            f"So the two friends searched together while they {scenario.premise}.",
        ]
    if mode == "question":
        return [
            f'"Who would build something like that?" {friend} asked at {place}.',
            f"{companion} had no answer yet. They {scenario.premise}.",
        ]
    return [
        f"{friend} and {companion} arrived at {place with False}.",
        f"They were there because they {scenario.premise}.",
    ]


def _opening_fixed(params: StoryParams, scenario: Scenario) -> list[str]:
    friend = params.friend
    companion = params.companion
    place = params.place
    mode = params.telling_mode or "arrival"
    if mode == "dialogue":
        return [
            f'"Do you hear that?" {friend} asked. "I hear a mystery," {companion} replied.',
            f"Together they entered {place}. They {scenario.premise}.",
        ]
    if mode == "arrival":
        return [
            f"{friend} and {companion} arrived at {place}.",
            f"They were there because they {scenario.premise}.",
        ]
    return _opening(params, scenario)


def generate(params: StoryParams) -> StorySample:
    if not params.friend or not params.companion:
        raise StoryError("A story needs both a friend and a companion.")
    if params.friend == params.companion:
        raise StoryError("The friend and companion must be different characters.")
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), None)
    if scenario is None:
        raise StoryError(f"Unknown mystery scenario: {params.scenario}")

    world = World()
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="girl",
        label="friend",
        phrase=params.friend,
        location=params.place,
        memes={"trust": 0.7, "curiosity": 0.8},
        traits=["curious", "loyal"],
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="boy",
        label="companion",
        phrase=params.companion,
        location=params.place,
        memes={"trust": 0.7, "caution": 0.5},
        traits=["observant", "kind"],
    ))
    mechanism = world.add(Entity(
        id="mechanism",
        kind="object",
        type="mechanism",
        label="mysterious mechanism",
        phrase="the mysterious mechanism",
        location=params.place,
        meters={"mystery": 1.0, "risk": 0.6, "function_known": 0.0},
        memes={"warning": 1.0, "friendship_test": 1.0},
    ))
    world.facts.update(
        params=params,
        scenario=scenario.key,
        premise=scenario.premise,
        mechanism=scenario.mechanism,
        warning=scenario.warning,
        rash_action=scenario.rash_action,
        consequence=scenario.consequence,
        clue=scenario.clue,
        twist=scenario.twist,
        repair=scenario.repair,
        outcome=scenario.outcome,
        lesson=scenario.lesson,
    )

    for sentence in _opening_fixed(params, scenario):
        world.say(sentence)
    world.say(f"Behind a dusty panel, they found {scenario.mechanism}.")
    world.say(f"It was called {params.mechanism_name}, though neither friend knew who had named it.")

    world.para()
    world.say(f"A tiny plate carried a caution: {scenario.warning}")
    world.say(
        f'"We should study it first," {companion.id} said. '
        f'"Mysteries are safer when we solve them together," {friend.id} answered.'
    )
    world.say(f"But the mechanism seemed to answer their voices, and {friend.id} {scenario.rash_action}.")
    world.say(f"At once, {scenario.consequence}.")

    world.para()
    world.say(f"The friends stopped pulling and began looking. They noticed that {scenario.clue}.")
    world.say(
        f'"I thought you caused this," {companion.id} admitted. '
        f'"I thought you knew more than you told me," {friend.id} replied.'
    )
    world.say(f"Instead of arguing, they {scenario.careful_action}.")
    world.say(f"That careful test revealed the twist: {scenario.twist}.")

    world.para()
    world.say(f"{friend.id} {scenario.apology}.")
    world.say(f'"Friends can change a mistake if they tell the truth," {companion.id} said.')
    world.say(f"Together they {scenario.repair}.")
    world.say(f"Then {scenario.outcome}.")

    world.para()
    world.say(f"They carried away a caution: {scenario.lesson}.")
    world.say(f"The mystery had tested their friendship, but listening had made it stronger.")
    world.say(f"In the end, {scenario.ending}")

    mechanism.meters["function_known"] = 1.0
    mechanism.meters["risk"] = 0.0
    mechanism.location = "understood and safely resting"
    mechanism.memes["friendship_test"] = 0.0
    friend.memes["trust"] = 1.0
    companion.memes["trust"] = 1.0
    world.facts.update(resolved=True, friendship_repaired=True, caution_heeded=True, twist_revealed=True)

    prompts = [
        f"Write a child-friendly Mystery about {params.friend} and {params.companion} discovering a mechanism in {params.place}.",
        f"Tell a Friendship story where a cautionary warning leads to a surprising twist: {scenario.warning}",
        f"Write an ending that shows how the friends repair their mistake: {scenario.repair}.",
    ]
    story_qa = [
        QAItem(
            question="What mystery did the friends discover?",
            answer=f"They discovered {scenario.mechanism} at {params.place}. Its purpose was hidden until they followed the clues.",
        ),
        QAItem(
            question="What caution did the mechanism give them?",
            answer=f"The mechanism warned them that {scenario.warning} They should have studied it before acting.",
        ),
        QAItem(
            question="What happened after the rash action?",
            answer=f"After they {scenario.rash_action}, {scenario.consequence}. This showed that the warning mattered.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario.twist} The mechanism was mysterious, but it was not their enemy.",
        ),
        QAItem(
            question="How did the friends repair the problem?",
            answer=f"They admitted their mistakes and {scenario.repair}. Their honest teamwork led to the result that {scenario.outcome}.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {scenario.lesson} Their friendship became stronger because they listened to evidence and to each other.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, signal, or change.",
        ),
        QAItem(
            question="Why are cautions important in a mystery?",
            answer="Cautions can point out hidden risks and give characters time to understand a strange object before using it.",
        ),
        QAItem(
            question="How can friendship help solve a mystery?",
            answer="Friends can compare observations, speak honestly, and help one another choose a careful solution.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("theme", "mystery"),
        asp.fact("feature", "friendship"),
        asp.fact("feature", "cautionary"),
        asp.fact("feature", "twist"),
        asp.fact("seed_word", "mechanism"),
        asp.fact("object", "mechanism"),
        asp.fact("requires", "careful_observation"),
        asp.fact("requires", "honest_dialogue"),
    ]
    return "\n".join(facts)


ASP_RULES = r"""
safe_feature(friendship) :- feature(friendship), requires(honest_dialogue).
safe_feature(cautionary) :- feature(cautionary), requires(careful_observation).
resolved(twist) :- feature(twist), object(mechanism), safe_feature(friendship).
#show feature/1.
#show seed_word/1.
#show resolved/1.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    features = sorted(set(asp.atoms(model, "feature")))
    resolved = asp.atoms(model, "resolved")
    wanted = [("cautionary",), ("friendship",), ("twist",)]
    if features != wanted or resolved != [("twist",)]:
        print("MISMATCH: ASP model does not match the storyworld contract.")
        print("features:", features)
        print("resolved:", resolved)
        return 1
    for scenario in SCENARIOS:
        params = StoryParams(
            friend="Luna",
            companion="Tobin",
            place="the old clock tower",
            mechanism_name="the moonwheel",
            seed=17,
            scenario=scenario.key,
            telling_mode="dialogue",
        )
        sample = generate(params)
        if not all(word in sample.story.lower() for word in ("mechanism", "friend", "caution", "twist")):
            print(f"MISMATCH: generated story lost required concepts in {scenario.key}.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            bits = [f"type={entity.type}"]
            if entity.location:
                bits.append(f"location={entity.location}")
            if entity.meters:
                bits.append(f"meters={entity.meters}")
            if entity.memes:
                bits.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {' '.join(bits)}")
        print(f"  facts: {sample.world.facts}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feature/1.\n#show resolved/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(json.dumps({
            "features": asp.atoms(model, "feature"),
            "seed_words": asp.atoms(model, "seed_word"),
            "resolved": asp.atoms(model, "resolved"),
        }, indent=2))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Tobin", "the old clock tower", "the moonwheel", 101, "clock_tower", "mystery"),
            StoryParams("Mara", "Eli", "the locked greenhouse", "the brass whisperer", 202, "greenhouse_latch", "warning"),
            StoryParams("Nia", "Finn", "the lantern-lit museum", "the little answer machine", 303, "museum_music", "dialogue"),
            StoryParams("Poppy", "Oren", "the foggy riverside station", "the silver keywork", 404, "river_station", "question"),
            StoryParams("Suri", "Pax", "the quiet hill observatory", "the moonwheel", 505, "observatory_lens", "memory"),
            StoryParams("Wren", "Theo", "the lantern-lit museum", "the brass whisperer", 606, "lantern_archive", "promise"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            attempt += 1
            attempt_seed = base_seed + attempt
            rng = random.Random(attempt_seed)
            params = resolve_params(args, rng)
            params.seed = attempt_seed
            sample = generate(params)
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
        if args.all:
            header = f"### {sample.params.friend} and {sample.params.companion} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
