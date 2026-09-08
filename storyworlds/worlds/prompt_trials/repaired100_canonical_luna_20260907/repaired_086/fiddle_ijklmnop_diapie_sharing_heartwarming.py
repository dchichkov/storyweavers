#!/usr/bin/env python3
"""Heartwarming StoryWorld about a fiddle, ijklmnop, diapie, and sharing."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


CHILD_NAMES = ["Luna", "Mina", "Theo", "Pia", "Jules", "Niko"]
FRIEND_NAMES = ["Ari", "Bea", "Sol", "Milo", "Nell", "Tavi"]
PLACES = ["the sunny village square", "the little riverside porch", "the garden beneath the lanterns"]
TREATS = ["apple diapie", "berry diapie", "honey diapie", "peach diapie"]

OPENINGS = [
    "On a golden afternoon",
    "When the first lanterns began to glow",
    "After a soft spring rain",
    "One bright morning",
    "As the village woke to birdsong",
    "Near the end of a warm day",
]

FIDDLE_TUNES = [
    "a gentle tune about helping hands",
    "a bouncy song for passing plates",
    "a sleepy melody that made everyone smile",
    "a bright tune with a skipping rhythm",
    "a warm song that sounded like home",
]

SHARING_LINES = [
    '"There is enough when we pass it around," Luna said.',
    '"A treat tastes sweeter with a friend," said Luna.',
    '"Let us make room at our blanket," Luna offered.',
    '"We can share the music and the diapie," Luna promised.',
]

TURN_LINES = [
    "Then Luna saw that one small plate and one fiddle could not welcome everyone at once.",
    "But a shy guest stood beyond the lantern light, holding an empty cup.",
    "Just then, the fiddle string gave a tiny twang, and the last diapie was left on the tray.",
    "The smallest visitor had come late and was afraid there would be nothing left.",
]

ENDING_IMAGES = [
    "the fiddle resting beside an empty shared plate while new friends hummed together",
    "crumbs sparkling on the cloth as every child held a warm cup",
    "the diapie tray returning empty beneath the happy lanterns",
    "Luna's fiddle shining while the whole circle sang the tune together",
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    child_name: str
    friend_name: str
    treat: str
    fiddle_tune: str
    opening_id: int = 0
    sharing_id: int = 0
    turn_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        return copy.deepcopy(self)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming StoryWorld about a fiddle, ijklmnop, diapie, and sharing."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--treat", choices=TREATS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child_name or rng.choice(CHILD_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != child]
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        child_name=child,
        friend_name=args.friend_name or rng.choice(friend_choices),
        treat=args.treat or rng.choice(TREATS),
        fiddle_tune=rng.choice(FIDDLE_TUNES),
        opening_id=rng.randrange(len(OPENINGS)),
        sharing_id=rng.randrange(len(SHARING_LINES)),
        turn_id=rng.randrange(len(TURN_LINES)),
        ending_id=rng.randrange(len(ENDING_IMAGES)),
    )


def tell(params: StoryParams) -> World:
    if params.child_name == params.friend_name:
        raise StoryError("The child and friend must have different names.")
    if params.treat not in TREATS:
        raise StoryError(f"Unknown treat: {params.treat}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")

    world = World(params.place)
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type="musician",
            label=params.child_name,
            role="fiddle player",
            meters={"warmth": 0.5, "food": 1.0},
            memes={"generosity": 0.4, "confidence": 0.5},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type="neighbor",
            label=params.friend_name,
            role="new friend",
            meters={"warmth": 0.2, "food": 0.0},
            memes={"shyness": 0.8, "belonging": 0.1},
        )
    )
    fiddle = world.add(
        Entity(
            id="fiddle",
            kind="instrument",
            type="fiddle",
            label="a little wooden fiddle",
            role="shared music",
            meters={"strings": 4.0},
            memes={"joy": 0.5},
        )
    )
    diapie = world.add(
        Entity(
            id="diapie",
            kind="food",
            type="diapie",
            label=params.treat,
            role="shared treat",
            meters={"pieces": 2.0},
            memes={"comfort": 0.7},
        )
    )
    alphabet = world.add(
        Entity(
            id="ijklmnop",
            kind="keepsake",
            type="letter_card",
            label="the ijklmnop card",
            role="welcome card",
            meters={"letters": 8.0},
            memes={"welcome": 0.5},
        )
    )

    world.facts.update(
        child=child,
        friend=friend,
        fiddle=fiddle,
        diapie=diapie,
        ijklmnop=alphabet,
        shared=False,
        pieces_before=2,
        pieces_after=0,
        lesson="sharing can turn a small welcome into a large friendship",
        tune=params.fiddle_tune,
        resolved=False,
    )

    world.say(f"{OPENINGS[params.opening_id]}, {child.label} carried a little wooden fiddle to {params.place}.")
    world.say(
        f"On the blanket lay a warm {params.treat} and a card that said ijklmnop, "
        "a silly welcome word the village children used for new beginnings."
    )
    world.say(
        f"{child.label} planned to play {params.fiddle_tune} while friends gathered beneath the lanterns."
    )
    world.para()

    world.say(f"{child.label} tucked the fiddle beneath their chin and played a bright, careful bow.")
    world.say(f"{params.sharing_id}")
    world.say(
        f"Across the square, {friend.label} listened quietly but stayed near the garden gate."
    )
    world.say(f"{TURN_LINES[params.turn_id]}")
    world.say(
        f'{child.label} called, "Would you like to come closer?" '
        f'{friend.label} answered, "I do, but I do not know the ijklmnop welcome word."'
    )
    world.say(
        f'{child.label} smiled. "You do not need a perfect word. You can share the next song with us."'
    )
    friend.memes["shyness"] = 0.5
    world.para()

    world.say(
        f"{child.label} moved the blanket aside and broke the {params.treat} into two cheerful pieces."
    )
    world.say(
        f"{child.label} gave one piece to {friend.label}, then handed over the ijklmnop card "
        "so they could hold it together."
    )
    world.say(
        f"{friend.label} took a small bite and said, "
        '"It tastes better because I am not eating it alone."'
    )
    world.say(
        f'{child.label} replied, "Then let us share the fiddle too. You may choose the next sound."'
    )
    world.say(
        f"{friend.label} tapped the fiddle's wooden side while {child.label} played "
        f"{params.fiddle_tune} once more."
    )
    child.memes.update(generosity=1.0, confidence=0.9)
    friend.memes.update(shyness=0.0, belonging=1.0)
    fiddle.memes["joy"] = 1.0
    diapie.meters["pieces"] = 0.0
    alphabet.memes["welcome"] = 1.0
    world.facts.update(
        shared=True,
        pieces_after=0,
        resolved=True,
        repair="the treat, music, and welcome card were shared",
    )
    world.para()

    world.say(
        f"Other children heard the tune and joined the circle, each bringing something small to share."
    )
    world.say(
        f"Someone brought berries, someone brought cups, and {friend.label} kept the ijklmnop card "
        "upright beside the lantern."
    )
    world.say(
        f"{child.label} no longer played for an audience; {child.label} played with {friend.label}."
    )
    world.say(
        f"The evening ended with {ENDING_IMAGES[params.ending_id]}."
    )
    world.say(
        f"Everyone learned that {world.facts['lesson']}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"].label
    friend = world.facts["friend"].label
    treat = world.facts["diapie"].label
    return [
        f"Write a heartwarming story about {child} sharing a fiddle and {treat} with {friend}.",
        f"Include the playful word ijklmnop as a welcome sign and show how sharing changes {friend}'s feelings.",
        "End with music, friendship, and a concrete image proving that everyone belongs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"].label
    friend = world.facts["friend"].label
    treat = world.facts["diapie"].label
    return [
        QAItem(
            question=f"Why did {friend} stay near the gate at first?",
            answer=f"{friend} felt shy because they did not know the ijklmnop welcome word and were unsure whether they belonged.",
        ),
        QAItem(
            question=f"How did {child} make {friend} feel welcome?",
            answer=f"{child} invited {friend} closer, shared the {treat}, offered the fiddle's music, and let {friend} choose the next sound.",
        ),
        QAItem(
            question="What changed after the diapie and music were shared?",
            answer="The shy visitor became part of the circle. Sharing changed the gathering from one child's performance into a friendship enjoyed together.",
        ),
        QAItem(
            question="What did ijklmnop mean in the story?",
            answer="IJKLMNOP was a playful welcome word on the card. It reminded everyone that a new beginning could start with a simple invitation.",
        ),
        QAItem(
            question="What ending image proves the problem was solved?",
            answer=f"The story ends with {ENDING_IMAGES[world.params.ending_id] if hasattr(world, 'params') else 'the fiddle shining while friends share the circle'}, showing that the new friend truly belongs.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fiddle?",
            answer="A fiddle is a bowed string instrument. In this story, its music helps people gather and take part together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly giving or using something together so another person can benefit too.",
        ),
        QAItem(
            question="Why can food help people connect?",
            answer="Offering food is a concrete way to show care. Eating together can make a shy person feel noticed and safe.",
        ),
        QAItem(
            question="What makes a welcome meaningful?",
            answer="A meaningful welcome includes an invitation, room to participate, and actions that show the invitation is sincere.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.params = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} "
            f"role={entity.role} meters={entity.meters} memes={entity.memes}"
        )
    for key in ("shared", "pieces_before", "pieces_after", "repair", "lesson", "resolved"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="the sunny village square",
        child_name="Luna",
        friend_name="Ari",
        treat="apple diapie",
        fiddle_tune="a gentle tune about helping hands",
        opening_id=0,
        sharing_id=0,
        turn_id=0,
        ending_id=0,
    ),
    StoryParams(
        place="the little riverside porch",
        child_name="Mina",
        friend_name="Sol",
        treat="berry diapie",
        fiddle_tune="a bouncy song for passing plates",
        opening_id=2,
        sharing_id=1,
        turn_id=1,
        ending_id=1,
    ),
    StoryParams(
        place="the garden beneath the lanterns",
        child_name="Theo",
        friend_name="Bea",
        treat="honey diapie",
        fiddle_tune="a warm song that sounded like home",
        opening_id=4,
        sharing_id=3,
        turn_id=3,
        ending_id=3,
    ),
]


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("domain", "music_friendship"),
        asp.fact("feature", "sharing"),
        asp.fact("style", "heartwarming"),
        asp.fact("object", "fiddle"),
        asp.fact("object", "ijklmnop"),
        asp.fact("object", "diapie"),
        asp.fact("safe", "welcome"),
    ]
    return "\n".join(facts)


ASP_RULES = """
valid_story :-
    domain(music_friendship),
    feature(sharing),
    style(heartwarming),
    object(fiddle),
    object(ijklmnop),
    object(diapie),
    safe(welcome).
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the sharing story.")
        return 1
    sample = generate(CURATED[0])
    required = ("fiddle", "ijklmnop", "diapie", "share")
    if not all(word in sample.story.lower() for word in required):
        print("Mismatch: generated story lacks required narrative evidence.")
        return 1
    print("OK: ASP gate accepted the sharing story and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        print("compatible story:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
