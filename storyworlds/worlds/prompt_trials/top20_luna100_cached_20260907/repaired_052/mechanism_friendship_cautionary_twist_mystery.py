#!/usr/bin/env python3
"""
A small mystery storyworld about a hidden mechanism, friendship, and a
cautionary twist: a strange machine seems to threaten a village until friends
learn what it was built to protect.
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
        if self.type in {"boy", "man", "keeper"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
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
    friend_a: str
    friend_b: str
    place: str
    mechanism_name: str
    seed: Optional[int] = None
    mystery: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Mystery:
    key: str
    opening: str
    mechanism: str
    warning: str
    mistake: str
    consequence: str
    clue: str
    careful_action: str
    twist: str
    explanation: str
    repair: str
    outcome: str
    lesson: str
    ending: str


FRIENDS_A = ["Mina", "Tess", "Lina", "Nora", "Pia", "Suri"]
FRIENDS_B = ["Bram", "Ollie", "Jules", "Milo", "Finn", "Theo"]
PLACES = [
    "the old clock tower",
    "the misty hill path",
    "the village greenhouse",
    "the quiet river dock",
    "the lantern market",
    "the little observatory",
]
MECHANISM_NAMES = [
    "the brass listener",
    "the moonwheel",
    "the whispering engine",
    "the silver keywork",
    "the bellwork box",
]
TELLING_MODES = ["arrival", "question", "warning", "clue", "memory", "rumor"]

MYSTERIES = [
    Mystery(
        key="night_bell",
        opening="A bell rang every night even though the village bell rope had been cut",
        mechanism="a small brass mechanism hidden beneath the bell platform",
        warning="its sharp teeth were turning faster whenever someone came near",
        mistake="pulled at the mechanism with a garden hook",
        consequence="the bell boomed once and sent frightened birds scattering over the roofs",
        clue="a tiny glass bead inside it glowed whenever the river rose",
        careful_action="placed a ruler beside the gears and watched them without touching",
        twist="the mechanism was not calling danger; it was measuring the river's height",
        explanation="it had been built long ago to warn families before floods reached the village",
        repair="cleaned the mud from its float and tied a new bell cord where everyone could see it",
        outcome="the bell gave one gentle note when the river swelled and no longer startled the birds",
        lesson="a strange machine should be understood before it is forced to stop",
        ending="that night, two friends listened to one calm bell note and watched the river shine below",
    ),
    Mystery(
        key="locked_greenhouse",
        opening="The greenhouse door locked itself each afternoon, just before the flowers began to wilt",
        mechanism="a wooden mechanism of wheels and sliding pins behind the watering shelf",
        warning="the pins snapped shut whenever the friends tried to lift the door",
        mistake="jammed a spoon into the lock to keep it open",
        consequence="the roof vents closed and warm air curled around the thirsty plants",
        clue="a blue thread on one wheel moved whenever sunlight crossed the seed trays",
        careful_action="followed the thread's path from the window to the hidden wheels",
        twist="the mechanism was not trapping the flowers; it was shading them from a dangerous hot beam",
        explanation="an old gardener had designed it to protect young plants during the afternoon heat",
        repair="replaced the broken shade cloth and reset the pins so the door opened after sunset",
        outcome="the flowers drank deeply and lifted their heads beneath a cool evening sky",
        lesson="a locked door may be guarding something fragile",
        ending="the two friends left the greenhouse together as every flower opened like a small star",
    ),
    Mystery(
        key="vanishing_bridge",
        opening="A bridge disappeared from the brook each morning, leaving only wet stones behind",
        mechanism="a chain-and-pulley mechanism hidden under the wooden walkway",
        warning="the chain rattled whenever either friend stepped onto the first plank",
        mistake="cut the chain with an old pair of shears",
        consequence="the bridge dropped halfway and blocked the brook with a loud splash",
        clue="fresh paw prints ended beside a red release lever",
        careful_action="waited until a family of otters swam safely past before studying the lever",
        twist="the bridge was designed to rise when the brook carried fallen branches",
        explanation="its builder had made it a safety gate, not a vanishing trick",
        repair="joined the cut chain and painted the release lever bright red",
        outcome="the bridge lowered for walkers and rose gently whenever the brook grew crowded",
        lesson="a caution can look like a mystery until we notice whom it protects",
        ending="their friendship felt stronger as they crossed the bridge while otters played below",
    ),
    Mystery(
        key="silent_observatory",
        opening="The observatory telescope stopped showing stars and pointed only at the ground",
        mechanism="a silver tracking mechanism beneath the round floor",
        warning="its pointer trembled whenever the telescope was pushed upward",
        mistake="turned the largest wheel as hard as possible",
        consequence="the dome shutters closed and the room went dark",
        clue="a loose star map showed a red mark beside the hill's old mine",
        careful_action="matched the map's mark to a hidden notch in the tracking wheel",
        twist="the telescope had been following a signal under the hill, not losing the stars",
        explanation="the signal came from a trapped miner's emergency lamp",
        repair="cleared the wheel, opened the shutters, and sent rescuers toward the red mark",
        outcome="the miner was found safely, and the telescope returned to the night sky",
        lesson="when a trusted tool behaves strangely, its new direction may carry a message",
        ending="the friends watched the first star appear while the rescued miner waved below",
    ),
    Mystery(
        key="market_shadow",
        opening="A shadow crossed the lantern market every noon though no cloud passed overhead",
        mechanism="a folding mechanism hidden inside the market's tallest lantern",
        warning="its dark panels snapped open above the fruit stalls",
        mistake="threw a stone at the lantern to make the shadow stop",
        consequence="one panel cracked and a shower of hot sparks fell near the baskets",
        clue="the shadow always covered the same patch of dry wooden roof",
        careful_action="asked the stall keepers what had happened there before touching the lantern",
        twist="the shadow was a sun shield, not a creature passing over the market",
        explanation="the lantern protected a nest of swallows beneath the roof from the noon heat",
        repair="mended the panel and moved the dry baskets away from the warm sparks",
        outcome="the swallows stayed cool and the market lantern cast a safe, tidy shade",
        lesson="fear can grow when we mistake protection for a threat",
        ending="friends and stall keepers shared peaches beneath the lantern's peaceful shadow",
    ),
    Mystery(
        key="whispering_dock",
        opening="The dock whispered a child's name whenever the tide began to turn",
        mechanism="a hollow reed mechanism fastened beneath the dock boards",
        warning="the whisper grew louder when the friends leaned over the dark water",
        mistake="pulled out the reeds and tossed them onto the shore",
        consequence="the dock groaned and a loose plank slipped toward the tide",
        clue="each whisper came after a small red float bumped the dock post",
        careful_action="tied a rope around the float and traced the sound through the boards",
        twist="the mechanism was repeating a warning from a missing tide marker",
        explanation="the red float had been built to call swimmers back before deep water arrived",
        repair="returned the reeds, secured the plank, and painted a clear tide sign",
        outcome="the dock whispered only when the water was unsafe, and children stayed on shore",
        lesson="a warning may sound eerie because it is trying hard to be heard",
        ending="the friends sat beside the quiet dock and watched the red float bob in the moonlight",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about mechanism, friendship, caution, and a twist."
    )
    parser.add_argument("--friend-a", choices=FRIENDS_A)
    parser.add_argument("--friend-b", choices=FRIENDS_B)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mechanism-name")
    parser.add_argument("--mystery", choices=[m.key for m in MYSTERIES])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    friend_a = args.friend_a or rng.choice(FRIENDS_A)
    friend_b = args.friend_b or rng.choice(FRIENDS_B)
    place = args.place or rng.choice(PLACES)
    mechanism_name = args.mechanism_name or rng.choice(MECHANISM_NAMES)
    mystery = args.mystery or rng.choice(MYSTERIES).key
    telling_mode = args.telling_mode or rng.choice(TELLING_MODES)
    return StoryParams(
        friend_a=friend_a,
        friend_b=friend_b,
        place=place,
        mechanism_name=mechanism_name,
        seed=args.seed,
        mystery=mystery,
        telling_mode=telling_mode,
    )


def _opening(params: StoryParams, mystery: Mystery) -> list[str]:
    a = params.friend_a
    b = params.friend_b
    place = params.place
    mode = params.telling_mode or "arrival"
    if mode == "question":
        return [
            f'"Did you hear that?" {a} asked as the friends reached {place}.',
            f"{b} listened. {mystery.opening}.",
        ]
    if mode == "warning":
        return [
            f'"Do not touch anything yet," {b} warned at {place}.',
            f"{a} nodded, because {mystery.opening.lower()}.",
        ]
    if mode == "clue":
        return [
            f"The first clue was a sound beneath the floor at {place}.",
            f"When {a} and {b} followed it, they learned that {mystery.opening.lower()}.",
        ]
    if mode == "memory":
        return [
            f"Long afterward, {a} remembered the strange afternoon at {place}.",
            f"It began when {mystery.opening.lower()}.",
        ]
    if mode == "rumor":
        return [
            f"People in the village whispered about {place}.",
            f"They said that {mystery.opening.lower()}",
        ]
    return [
        f"{a} and {b} arrived at {place} just before the afternoon light faded.",
        f"There they discovered that {mystery.opening.lower()}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.friend_a == params.friend_b:
        raise StoryError("The two friends must have different names.")
    if not params.mechanism_name:
        raise StoryError("A mechanism name is required.")
    rng = random.Random(params.seed)
    mystery = next((m for m in MYSTERIES if m.key == params.mystery), None)
    if mystery is None:
        raise StoryError(f"Unknown mystery: {params.mystery}")

    world = World()
    friend_a = world.add(
        Entity(
            id=params.friend_a,
            kind="character",
            type="girl",
            label="friend",
            phrase=params.friend_a,
            location=params.place,
            meters={"curiosity": 0.8, "caution": 0.4},
            memes={"friendship": 0.7, "trust": 0.6},
            traits=["curious", "brave"],
        )
    )
    friend_b = world.add(
        Entity(
            id=params.friend_b,
            kind="character",
            type="boy",
            label="friend",
            phrase=params.friend_b,
            location=params.place,
            meters={"curiosity": 0.6, "caution": 0.9},
            memes={"friendship": 0.7, "trust": 0.8},
            traits=["careful", "loyal"],
        )
    )
    mechanism = world.add(
        Entity(
            id="mechanism",
            kind="thing",
            type="mechanism",
            label=params.mechanism_name,
            phrase=params.mechanism_name,
            location=params.place,
            meters={"motion": 0.9, "risk": 0.7, "understanding": 0.1},
            memes={"mystery": 1.0, "warning": 0.8},
            traits=["old", "hidden"],
        )
    )
    world.facts.update(
        params=params,
        mystery=mystery.key,
        place=params.place,
        mechanism=params.mechanism_name,
        warning=mystery.warning,
        mistake=mystery.mistake,
        consequence=mystery.consequence,
        clue=mystery.clue,
        twist=mystery.twist,
        explanation=mystery.explanation,
        repair=mystery.repair,
        outcome=mystery.outcome,
    )

    for sentence in _opening(params, mystery):
        world.say(sentence)
    world.say(
        rng.choice(
            [
                f"Behind a loose board, they found {mystery.mechanism}.",
                f"A faint ticking led them to {mystery.mechanism}.",
                f"The mystery seemed to belong to {mystery.mechanism}.",
            ]
        )
    )

    world.para()
    world.say(f"The mechanism's warning was clear: {mystery.warning}.")
    world.say(
        f'"I can make it stop," {friend_a.id} said, and {friend_a.pronoun()} {mystery.mistake}.'
    )
    world.say(f"At once, {mystery.consequence}.")
    world.say(
        f'"Wait," {friend_b.id} said. "We promised to solve this together, not make it louder."'
    )

    world.para()
    world.say(f"The friends stood shoulder to shoulder and looked for a clue. They noticed that {mystery.clue}.")
    world.say(f"{friend_b.id} {mystery.careful_action}.")
    world.say(
        rng.choice(
            [
                f"Then came the twist: {mystery.twist}.",
                f"The hidden truth turned the mystery around. {mystery.twist.capitalize()}.",
                f"The friends had guessed wrong. The twist was that {mystery.twist}.",
            ]
        )
    )
    world.say(f"They understood that {mystery.explanation}.")

    world.para()
    world.say(
        f'"I am sorry I rushed," {friend_a.id} said. "I should have asked what it was doing."'
    )
    world.say(
        f'"You stopped to listen," {friend_b.id} replied. "That helped us find the answer."'
    )
    world.say(f"Together, the friends {mystery.repair}.")
    world.say(f"Because they worked carefully, {mystery.outcome}.")

    world.para()
    world.say(f"They carried the lesson home: {mystery.lesson}.")
    world.say(
        f"As evening settled over {params.place}, {mystery.ending}"
    )

    mechanism.meters["risk"] = 0.1
    mechanism.meters["understanding"] = 1.0
    mechanism.meters["motion"] = 0.3
    mechanism.memes["mystery"] = 0.2
    mechanism.memes["protection"] = 1.0
    friend_a.meters["caution"] = 0.9
    friend_a.memes["trust"] = 1.0
    friend_b.memes["friendship"] = 1.0
    world.facts.update(resolved=True, twist_understood=True, friendship_strengthened=True)

    prompts = [
        f"Write a child-friendly mystery about {params.friend_a} and {params.friend_b} finding {params.mechanism_name} at {params.place}.",
        f"Tell a cautionary friendship story in which a strange mechanism seems dangerous but has a surprising purpose.",
        f"Write a mystery with a twist showing why careful observation is better than rushing.",
    ]
    story_qa = [
        QAItem(
            question=f"What mystery did {params.friend_a} and {params.friend_b} discover?",
            answer=f"They discovered {mystery.mechanism} at {params.place}. It seemed risky because {mystery.warning}.",
        ),
        QAItem(
            question="What mistake did the friends make?",
            answer=f"{params.friend_a} {mystery.mistake}, and the action caused this consequence: {mystery.consequence}.",
        ),
        QAItem(
            question="What clue changed their understanding?",
            answer=f"They noticed that {mystery.clue}. This clue helped them learn that {mystery.twist}.",
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=f"The twist was that {mystery.twist}. The mechanism had actually been made because {mystery.explanation}.",
        ),
        QAItem(
            question="How did the friends repair the problem?",
            answer=f"They apologized, listened to one another, and {mystery.repair}. As a result, {mystery.outcome}.",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {mystery.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, signal, open, close, or help.",
        ),
        QAItem(
            question="Why can a mystery need caution?",
            answer="Caution helps people observe a strange situation before touching it or making the danger worse.",
        ),
        QAItem(
            question="How can friendship help solve a mystery?",
            answer="Friends can share different observations, speak honestly, and make safer choices together.",
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

    return "\n".join(
        [
            asp.fact("domain", "mystery"),
            asp.fact("seed_word", "mechanism"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("style", "mystery"),
            asp.fact("rule", "observe_before_touching"),
            asp.fact("rule", "friends_share_clues"),
        ]
    )


ASP_RULES = r"""
#show domain/1.
#show seed_word/1.
#show feature/1.
#show style/1.
#show rule/1.
safe_choice :- rule(observe_before_touching).
safe_choice :- rule(friends_share_clues).
#show safe_choice/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    features = sorted(set(asp.atoms(model, "feature")))
    wanted = [("cautionary",), ("friendship",), ("twist",)]
    if features != wanted:
        print("MISMATCH: ASP feature facts are wrong.")
        print(features)
        return 1
    if not asp.atoms(model, "safe_choice"):
        print("MISMATCH: ASP safety rule did not fire.")
        return 1
    sample = generate(
        StoryParams(
            friend_a="Mina",
            friend_b="Bram",
            place="the old clock tower",
            mechanism_name="the brass listener",
            seed=17,
            mystery="night_bell",
            telling_mode="question",
        )
    )
    required = ["mechanism", "friend", "twist", "carefully"]
    lowered = sample.story.lower()
    if not all(word in lowered for word in required):
        print("MISMATCH: generated story failed the verification content check.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
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
        print(asp_program("#show feature/1."))
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("== ASP model ==")
        for symbol in sorted(map(str, model)):
            print(symbol)
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                friend_a="Mina",
                friend_b="Bram",
                place="the old clock tower",
                mechanism_name="the brass listener",
                seed=101,
                mystery="night_bell",
                telling_mode="question",
            ),
            StoryParams(
                friend_a="Tess",
                friend_b="Ollie",
                place="the village greenhouse",
                mechanism_name="the moonwheel",
                seed=202,
                mystery="locked_greenhouse",
                telling_mode="warning",
            ),
            StoryParams(
                friend_a="Lina",
                friend_b="Jules",
                place="the little observatory",
                mechanism_name="the silver keywork",
                seed=303,
                mystery="silent_observatory",
                telling_mode="clue",
            ),
            StoryParams(
                friend_a="Nora",
                friend_b="Finn",
                place="the quiet river dock",
                mechanism_name="the whispering engine",
                seed=404,
                mystery="whispering_dock",
                telling_mode="rumor",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n:
        raise StoryError("Could not produce the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.friend_a} and {params.friend_b} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
