#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py
==============================================================================

A standalone storyworld for a small slice-of-life domain about friendship and
sharing. Two children sit down for a snack. One child has a treat with prune
filling from a Chinese bakery. The treat can only be shared sensibly when it is
easy to divide and there is a clean way to serve it, such as a little china
plate or paper napkins.

The world model tracks:
- physical meters like hunger, crumbs, and pieces
- emotional memes like shyness, curiosity, fairness, relief, and friendship

The core tension is simple and child-facing:
a child wants to share, but the food may be awkward to divide or the children
may need a tidy serving method first. A calm grown-up helps only when needed,
and the ending proves that sharing changed the moment.

Run it
------
    python storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py
    python storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py --snack buns --serve china_plate
    python storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py --snack bun
    python storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/prune_china_chinese_friendship_sharing_slice_of.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    source: str
    divisible: bool = False
    piece_word: str = "piece"
    total_pieces: int = 1
    needs_plate: bool = False
    tidy_with_napkin: bool = False
    filling: str = "sweet prune filling"
    tags: set[str] = field(default_factory=set)


@dataclass
class Serve:
    id: str
    label: str
    phrase: str
    clean: bool = True
    can_split: bool = False
    tidy_for_sticky: bool = False
    pretty: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    opener: str
    ask: str
    shy: bool = False
    curious: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    snack: str
    serve: str
    mood: str
    sharer_name: str
    sharer_gender: str
    friend_name: str
    friend_gender: str
    helper: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def share_possible(snack: Snack, serve: Serve) -> bool:
    if not snack.divisible:
        return False
    if serve.can_split:
        return True
    if snack.needs_plate and not serve.can_split:
        return False
    return snack.tidy_with_napkin and serve.tidy_for_sticky


def explain_rejection(snack: Snack, serve: Serve) -> str:
    if not snack.divisible:
        return (
            f"(No story: {snack.phrase} is only one whole serving, so the children "
            f"cannot split it fairly. Pick a snack that comes in easy pieces.)"
        )
    if snack.needs_plate:
        return (
            f"(No story: {snack.phrase} is best shared on a plate, and {serve.phrase} "
            f"does not give the children a clean, fair way to divide it.)"
        )
    return (
        f"(No story: {serve.phrase} is not a tidy enough way to share {snack.phrase}. "
        f"Pick a serving method that can keep the snack neat and fair.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for snack_id, snack in SNACKS.items():
        for serve_id, serve in SERVES.items():
            if share_possible(snack, serve):
                for mood_id in MOODS:
                    combos.append((snack_id, serve_id, mood_id))
    return combos


def introduce(world: World, sharer: Entity, friend: Entity, helper: Entity, snack: Snack, place: str) -> None:
    sharer.meters["hunger"] += 1
    friend.meters["hunger"] += 1
    sharer.memes["care"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"At morning snack time in {place}, {sharer.id} opened a small paper bag from a Chinese bakery."
    )
    world.say(
        f"Inside was {snack.phrase} with {snack.filling}. {helper.label_word.capitalize()} had packed it carefully so it would still feel special."
    )
    world.say(
        f"{friend.id} sat beside {sharer.id}, close enough to smell the warm sweet steam."
    )


def notice(world: World, sharer: Entity, friend: Entity, mood: Mood) -> None:
    if mood.shy:
        friend.memes["shyness"] += 1
    if mood.curious:
        friend.memes["curiosity"] += 1
    world.say(mood.opener.format(friend=friend.id, sharer=sharer.id))
    world.say(mood.ask.format(friend=friend.id, sharer=sharer.id))


def want_to_share(world: World, sharer: Entity, friend: Entity, snack: Snack) -> None:
    sharer.memes["generosity"] += 1
    world.say(
        f"{sharer.id} wanted to say yes right away. Sharing felt kind, and {sharer.pronoun('possessive')} snack smelled too good to keep all alone."
    )
    if not snack.divisible:
        world.say(
            f"But there was only one whole {snack.label}, and {sharer.id} did not know how to make that fair."
        )
    else:
        world.say(
            f"{sharer.pronoun().capitalize()} looked at the snack and tried to count how the pieces could be shared."
        )


def problem(world: World, sharer: Entity, friend: Entity, snack: Snack, serve: Serve) -> None:
    if snack.needs_plate and not serve.can_split:
        sharer.memes["worry"] += 1
        world.say(
            f'"I want to share," {sharer.id} said, "but this one is sticky, and I do not want it to fall apart in our hands."'
        )
    elif snack.divisible and not share_possible(snack, serve):
        sharer.memes["worry"] += 1
        world.say(
            f"{sharer.id} frowned at the crumbs already gathering in the paper bag. Without a better way to serve it, the sharing would turn messy and uneven."
        )
    else:
        world.say(
            f"{sharer.id} still paused for a moment, wanting to be sure that both children would get the same nice bite."
        )


def helper_step(world: World, sharer: Entity, friend: Entity, helper: Entity, serve: Serve, snack: Snack) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.label_word.capitalize()} saw them thinking and came over with {serve.phrase}."
    )
    if serve.id == "china_plate":
        world.say(
            f'"Here," {helper.pronoun()} said, "you can put the prune treat on this little china plate and split it neatly."'
        )
    elif serve.id == "napkins":
        world.say(
            f'"Here are two clean napkins," {helper.pronoun()} said. "That will help you share the sticky bites without a mess."'
        )
    else:
        world.say(
            f'"Here you go," {helper.pronoun()} said. "Now you have a proper place for the pieces."'
        )
    if serve.pretty:
        world.say(
            f"The smooth china made the snack look almost like a tiny bakery window at school."
        )


def split_and_share(world: World, sharer: Entity, friend: Entity, snack: Snack, serve: Serve) -> None:
    pieces_each = snack.total_pieces // 2
    leftover = snack.total_pieces % 2
    sharer.meters["pieces"] += float(pieces_each + leftover)
    friend.meters["pieces"] += float(pieces_each)
    sharer.meters["hunger"] = 0.0
    friend.meters["hunger"] = 0.0
    sharer.memes["relief"] += 1
    friend.memes["relief"] += 1
    sharer.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    sharer.memes["fairness"] += 1
    friend.memes["gratitude"] += 1
    if snack.total_pieces > 1:
        world.say(
            f"{sharer.id} set the snack on {serve.phrase} and counted the {snack.piece_word}s out loud."
        )
        if leftover:
            world.say(
                f"{sharer.pronoun().capitalize()} gave the extra little bit to {friend.id} first, then smiled when {friend.id} insisted they split that tiny piece too."
            )
            sharer.meters["pieces"] = float(pieces_each) + 0.5
            friend.meters["pieces"] = float(pieces_each) + 0.5
        else:
            world.say(
                f"There were just enough for both of them, so each child got the same number."
            )
    else:
        world.say(
            f"Together they broke the soft snack into two careful halves on {serve.phrase}."
        )
        sharer.meters["pieces"] = 0.5
        friend.meters["pieces"] = 0.5
    world.say(
        f'Soon both children were eating prune-filled bites and smiling. "This is good," {friend.id} said, surprised and pleased.'
    )


def ending(world: World, sharer: Entity, friend: Entity, snack: Snack, serve: Serve) -> None:
    world.say(
        f"They talked about how the Chinese bakery near {sharer.id}'s home always smelled warm in the morning."
    )
    world.say(
        f"By the time the snack was gone, {serve.phrase} held only a few crumbs, and the space between the two friends felt smaller and happier."
    )
    world.say(
        f"After that, when one of them brought something special, the other one knew there would be room to share."
    )


def tell(
    snack: Snack,
    serve: Serve,
    mood: Mood,
    sharer_name: str,
    sharer_gender: str,
    friend_name: str,
    friend_gender: str,
    helper_type: str,
    place: str,
) -> World:
    if not share_possible(snack, serve):
        raise StoryError(explain_rejection(snack, serve))

    world = World()
    sharer = world.add(Entity(id=sharer_name, kind="character", type=sharer_gender, role="sharer"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the grown-up"))
    tray = world.add(Entity(id="serve", type="serve", label=serve.label, phrase=serve.phrase, tags=set(serve.tags)))
    food = world.add(Entity(id="snack", type="snack", label=snack.label, phrase=snack.phrase, tags=set(snack.tags)))

    introduce(world, sharer, friend, helper, snack, place)
    world.para()
    notice(world, sharer, friend, mood)
    want_to_share(world, sharer, friend, snack)
    problem(world, sharer, friend, snack, serve)
    world.para()
    helper_step(world, sharer, friend, helper, serve, snack)
    split_and_share(world, sharer, friend, snack, serve)
    ending(world, sharer, friend, snack, serve)

    world.facts.update(
        sharer=sharer,
        friend=friend,
        helper=helper,
        snack=snack,
        serve=serve,
        mood=mood,
        place=place,
        even_split=abs(sharer.meters["pieces"] - friend.meters["pieces"]) < 0.001,
        shared=True,
    )
    return world


SNACKS = {
    "buns": Snack(
        id="buns",
        label="prune buns",
        phrase="two small prune buns",
        source="a Chinese bakery",
        divisible=True,
        piece_word="bun",
        total_pieces=2,
        needs_plate=False,
        tidy_with_napkin=True,
        filling="sweet prune filling",
        tags={"prune", "bakery"},
    ),
    "cake": Snack(
        id="cake",
        label="prune cake",
        phrase="a round prune cake",
        source="a Chinese bakery",
        divisible=True,
        piece_word="slice",
        total_pieces=4,
        needs_plate=True,
        tidy_with_napkin=False,
        filling="dark prune jam tucked inside",
        tags={"prune", "bakery"},
    ),
    "bun": Snack(
        id="bun",
        label="prune bun",
        phrase="one soft prune bun",
        source="a Chinese bakery",
        divisible=False,
        piece_word="half",
        total_pieces=1,
        needs_plate=False,
        tidy_with_napkin=True,
        filling="sweet prune filling",
        tags={"prune", "bakery"},
    ),
}

SERVES = {
    "china_plate": Serve(
        id="china_plate",
        label="china plate",
        phrase="a little blue china plate",
        clean=True,
        can_split=True,
        tidy_for_sticky=True,
        pretty=True,
        tags={"china", "plate"},
    ),
    "napkins": Serve(
        id="napkins",
        label="napkins",
        phrase="two folded paper napkins",
        clean=True,
        can_split=False,
        tidy_for_sticky=True,
        pretty=False,
        tags={"napkin"},
    ),
    "bare_hands": Serve(
        id="bare_hands",
        label="bare hands",
        phrase="only their bare hands",
        clean=False,
        can_split=False,
        tidy_for_sticky=False,
        pretty=False,
        tags={"messy"},
    ),
}

MOODS = {
    "shy": Mood(
        id="shy",
        opener="{friend} watched the paper bag for a moment before speaking.",
        ask='"That smells nice," {friend} said softly. "Is it from the bakery near your house?"',
        shy=True,
        curious=True,
        tags={"shy"},
    ),
    "bright": Mood(
        id="bright",
        opener="{friend} leaned a little closer and grinned.",
        ask='"That smells amazing," {friend} said. "What kind of snack is it?"',
        shy=False,
        curious=True,
        tags={"curious"},
    ),
    "careful": Mood(
        id="careful",
        opener="{friend} tilted {friend}\'s head and looked at the bag with gentle interest.",
        ask='"I have never had that before," {friend} said. "Would you tell me about it?"',
        shy=False,
        curious=True,
        tags={"curious"},
    ),
}

PLACES = {
    "the sunny classroom",
    "the library corner",
    "the art room by the window",
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Mei", "Anna", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Noah", "Eli", "Jun", "Theo", "Max"]

KNOWLEDGE = {
    "prune": [
        (
            "What is a prune?",
            "A prune is a dried plum. It tastes sweet and deep, and people use it in snacks and baked treats."
        )
    ],
    "china": [
        (
            "What is a china plate?",
            "A china plate is a smooth dish made for serving food. It is handy because it gives people a clean place to share a snack."
        )
    ],
    "bakery": [
        (
            "What is a bakery?",
            "A bakery is a place where people make and sell bread, buns, cakes, and other baked food. It often smells warm and sweet."
        )
    ],
    "sharing": [
        (
            "Why is sharing food kindly important?",
            "Kind sharing helps everyone feel included. It also shows that you are thinking about another person's feelings as well as your own."
        )
    ],
    "fair": [
        (
            "What does a fair share mean?",
            "A fair share means each person gets a reasonable part. When two children split a snack fairly, neither one feels left out."
        )
    ],
    "friendship": [
        (
            "How can sharing help a friendship?",
            "Sharing can make a friendship warmer because it shows care and trust. A small kind act can help two people feel close."
        )
    ],
}
KNOWLEDGE_ORDER = ["prune", "china", "bakery", "sharing", "fair", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sharer = f["sharer"]
    friend = f["friend"]
    snack = f["snack"]
    serve = f["serve"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "prune", "china", and "Chinese".',
        f"Tell a gentle friendship story where {sharer.id} shares {snack.phrase} from a Chinese bakery with {friend.id} by using {serve.phrase}.",
        "Write a simple school snack-time story about kindness, fair sharing, and two children becoming better friends.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sharer = f["sharer"]
    friend = f["friend"]
    helper = f["helper"]
    snack = f["snack"]
    serve = f["serve"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {sharer.id} and {friend.id}, at snack time in {place}. A grown-up nearby helps them find a neat way to share."
        ),
        (
            f"What snack did {sharer.id} bring?",
            f"{sharer.id} brought {snack.phrase} from a Chinese bakery. The snack had prune filling, which made it smell sweet and warm."
        ),
        (
            f"Why did {sharer.id} pause before sharing?",
            f"{sharer.id} wanted to be kind, but also wanted the sharing to be fair and tidy. The children needed a good way to divide the snack so nobody felt left out."
        ),
        (
            f"How did {helper.label_word} help the two friends?",
            f"{helper.label_word.capitalize()} brought {serve.phrase} so the snack could be divided neatly. That small help turned a worried pause into an easy act of sharing."
        ),
        (
            f"How did the story show friendship?",
            f"The friends shared the prune snack and talked together while they ate. By the end, they felt closer because the snack became something they enjoyed together instead of alone."
        ),
    ]
    if f["even_split"]:
        qa.append(
            (
                "Was the sharing fair?",
                f"Yes. Both children got the same amount, so the snack felt fair as well as kind. That made the happy ending feel calm and complete."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"prune", "sharing", "fair", "friendship", "bakery"}
    if world.facts["serve"].id == "china_plate":
        tags.add("china")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        snack="cake",
        serve="china_plate",
        mood="bright",
        sharer_name="Mei",
        sharer_gender="girl",
        friend_name="Lily",
        friend_gender="girl",
        helper="teacher",
        place="the sunny classroom",
    ),
    StoryParams(
        snack="buns",
        serve="napkins",
        mood="shy",
        sharer_name="Jun",
        sharer_gender="boy",
        friend_name="Ben",
        friend_gender="boy",
        helper="mother",
        place="the library corner",
    ),
    StoryParams(
        snack="buns",
        serve="china_plate",
        mood="careful",
        sharer_name="Ava",
        sharer_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        helper="teacher",
        place="the art room by the window",
    ),
]


ASP_RULES = r"""
share_possible(S, V) :- snack(S), serve(V), divisible(S), can_split(V).
share_possible(S, V) :- snack(S), serve(V), divisible(S), tidy_with_napkin(S),
                        tidy_for_sticky(V), not needs_plate(S).
valid(S, V, M) :- snack(S), serve(V), mood(M), share_possible(S, V).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        if snack.divisible:
            lines.append(asp.fact("divisible", snack_id))
        if snack.needs_plate:
            lines.append(asp.fact("needs_plate", snack_id))
        if snack.tidy_with_napkin:
            lines.append(asp.fact("tidy_with_napkin", snack_id))
    for serve_id, serve in SERVES.items():
        lines.append(asp.fact("serve", serve_id))
        if serve.can_split:
            lines.append(asp.fact("can_split", serve_id))
        if serve.tidy_for_sticky:
            lines.append(asp.fact("tidy_for_sticky", serve_id))
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _validate_params(params: StoryParams) -> None:
    if params.snack not in SNACKS:
        raise StoryError(f"(No story: unknown snack '{params.snack}'.)")
    if params.serve not in SERVES:
        raise StoryError(f"(No story: unknown serving method '{params.serve}'.)")
    if params.mood not in MOODS:
        raise StoryError(f"(No story: unknown mood '{params.mood}'.)")
    snack = SNACKS[params.snack]
    serve = SERVES[params.serve]
    if not share_possible(snack, serve):
        raise StoryError(explain_rejection(snack, serve))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a small snack-time story about sharing, friendship, and a prune treat from a Chinese bakery."
    )
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--serve", choices=SERVES)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.serve:
        snack = SNACKS[args.snack]
        serve = SERVES[args.serve]
        if not share_possible(snack, serve):
            raise StoryError(explain_rejection(snack, serve))

    combos = [
        combo for combo in valid_combos()
        if (args.snack is None or combo[0] == args.snack)
        and (args.serve is None or combo[1] == args.serve)
        and (args.mood is None or combo[2] == args.mood)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, serve_id, mood_id = rng.choice(sorted(combos))
    sharer_name, sharer_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=sharer_name)
    helper = args.helper or rng.choice(["mother", "father", "teacher"])
    place = args.place or rng.choice(sorted(PLACES))
    return StoryParams(
        snack=snack_id,
        serve=serve_id,
        mood=mood_id,
        sharer_name=sharer_name,
        sharer_gender=sharer_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper=helper,
        place=place,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        snack=SNACKS[params.snack],
        serve=SERVES[params.serve],
        mood=MOODS[params.mood],
        sharer_name=params.sharer_name,
        sharer_gender=params.sharer_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper,
        place=params.place,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (snack, serve, mood) combos:\n")
        for snack, serve, mood in combos:
            print(f"  {snack:8} {serve:12} {mood}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.sharer_name} and {p.friend_name}: {p.snack} with {p.serve}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
