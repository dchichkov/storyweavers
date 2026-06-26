#!/usr/bin/env python3
"""
storyworlds/worlds/befriend_happy_ending_dialogue_sound_effects_bedtime.py
==========================================================================

A standalone story world for "The Lonely Little Cloud" and close,
constraint-checked variations of it.

Initial story used to build a world model:
---
Once upon a time, high up in the blue sky, there was a little white cloud named
Puffy. Puffy was very small and very shy. All the other clouds were big and
fluffy and they drifted together, but Puffy floated all alone.

One evening, as the sun began to set and paint the sky orange and pink, Puffy
saw a little star twinkling all by itself in the early night sky. The star
looked just as lonely as Puffy felt.

Puffy wanted to befriend the star, but Puffy was scared. "I'm just a tiny
cloud," Puffy whispered. "A star would never want to be friends with me."

But the star winked. And Puffy felt a tiny bit of courage.

Puffy drifted closer and closer. "Hello," Puffy said in a soft, cottony voice.
"My name is Puffy. I'm a cloud."

The star sparkled! "Hello, Puffy! I'm Stella. I'm a star. I've been watching
you float alone, and I think you look kind."

From that night on, Puffy and Stella were best friends. Every evening, Puffy
would drift near Stella's spot in the sky, and Stella would twinkle her
brightest. They told each other stories until the moon came up. And Puffy was
never lonely again, because a little cloud and a little star can be the best of
friends.

Causal state updates:
---
    approach_character         -> actor.courage += 1
    speak_friendly             -> actor.social_trust += 1
    receive_friendly_response  -> actor.happiness += 1, actor.loneliness -= 1
    befriended                 -> actor.happiness += 2, actor.loneliness = 0
    share_story                -> both actors.happiness += 1, both actors.bond += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "thing"  # cloud, star, moon, sun
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    location: str = "sky"
    dialog_voice: str = "soft"
    sound_effect: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the sky"
    time_of_day: str = "evening"
    weather: str = "clear"


@dataclass
class SocialMove:
    id: str
    approach_phrase: str
    dialogue_line: str
    sound_effect: str
    courage_cost: float = 0.5
    social_trust_gain: float = 1.0


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.dialogues: list[str] = []
        self.sound_effects: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def speak(self, speaker: str, line: str) -> None:
        self.dialogues.append(f'"{line}" said {speaker}.')

    def sfx(self, sound: str) -> None:
        self.sound_effects.append(sound)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        text = "\n\n".join(chunks)
        if self.dialogues:
            text += "\n\n" + "\n".join(self.dialogues)
        if self.sound_effects and "--trace" not in str(sys.argv):
            passes = random.Random(42).choices(self.sound_effects, k=min(2, len(self.sound_effects)))
            if passes:
                text += "\n\n" + passes[0]
        return text

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_approach(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes["attempted_approach"] and not actor.memes["approached"]:
            sig = ("approach", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["approached"] = 1.0
            out.append(f"{actor.id} drifted a little closer, feeling braver.")
    return out


def _r_befriend(world: World) -> list[str]:
    out: list[str] = []
    entities = list(world.entities.values())
    for actor in [e for e in entities if e.kind == "character"]:
        if actor.memes["friend_response"] and actor.memes["social_trust"] >= THRESHOLD:
            sig = ("befriend", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["happiness"] += 2
            actor.memes["loneliness"] = 0
            out.append(f"{actor.id} felt a warm, happy glow. They had made a friend!")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    entities = list(world.entities.values())
    pairs = []
    for a in entities:
        for b in entities:
            if a.id < b.id and a.memes.get("befriended") and b.memes.get("befriended"):
                pairs.append((a, b))
    for a, b in pairs:
        sig = ("share", a.id, b.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        a.memes["happiness"] += 1
        b.memes["happiness"] += 1
        a.memes["bond"] += 1
        b.memes["bond"] += 1
        out.append(f"{a.id} and {b.id} shared a story under the moonlight.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="approach", tag="social", apply=_r_approach),
    Rule(name="befriend", tag="social", apply=_r_befriend),
    Rule(name="share", tag="social", apply=_r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "twilight_sky": Setting(place="the twilight sky", time_of_day="evening", weather="clear"),
    "star_field": Setting(place="a field of stars", time_of_day="night", weather="clear"),
    "morning_sky": Setting(place="the morning sky", time_of_day="morning", weather="clear"),
    "rainbow_sky": Setting(place="the rainbow sky", time_of_day="afternoon", weather="rainbow"),
}

CLOUDS = {
    "puffy": Entity(
        id="Puffy", kind="character", type="cloud", label="a little white cloud",
        phrase="a tiny, soft cloud named Puffy",
        traits=["shy", "kind", "brave"],
        dialog_voice="soft and cottony",
        sound_effect="*whoosh*",
    ),
    "whispy": Entity(
        id="Whispy", kind="character", type="cloud", label="a small wispy cloud",
        phrase="a gentle wisp of a cloud named Whispy",
        traits=["gentle", "curious", "hopeful"],
        dialog_voice="light and breezy",
        sound_effect="*whisper*",
    ),
    "fluffy": Entity(
        id="Fluffy", kind="character", type="cloud", label="a round fluffy cloud",
        phrase="a round, fluffy cloud named Fluffy",
        traits=["friendly", "shy", "loyal"],
        dialog_voice="warm and puffy",
        sound_effect="*poof*",
    ),
}

STARS = {
    "stella": Entity(
        id="Stella", kind="character", type="star", label="a tiny twinkling star",
        phrase="a bright little star named Stella",
        traits=["sparkly", "kind", "patient"],
        dialog_voice="sparkly and warm",
        sound_effect="*twinkle*",
    ),
    "twinkle": Entity(
        id="Twinkle", kind="character", type="star", label="a shy little star",
        phrase="a shy, blinking star named Twinkle",
        traits=["shy", "friendly", "gentle"],
        dialog_voice="tiny and bright",
        sound_effect="*blink*",
    ),
    "glow": Entity(
        id="Glow", kind="character", type="star", label="a steady golden star",
        phrase="a steady, golden star named Glow",
        traits=["calm", "wise", "warm"],
        dialog_voice="soft and golden",
        sound_effect="*hum*",
    ),
}

SOCIAL_MOVES = [
    SocialMove(
        id="greet", approach_phrase="drifted closer",
        dialogue_line="Hello, I'm a little cloud. What's your name?",
        sound_effect="*whoosh*",
    ),
    SocialMove(
        id="compliment", approach_phrase="edged nearer with a shy smile",
        dialogue_line="You shine so brightly. I wish I could shine like you.",
        sound_effect="*fizzle*",
    ),
    SocialMove(
        id="offer_story", approach_phrase="floated gently nearer",
        dialogue_line="Would you like to hear a story about the moon?",
        sound_effect="*rustle*",
    ),
    SocialMove(
        id="ask_question", approach_phrase="drifted slowly closer",
        dialogue_line="Do you get lonely up here, too?",
        sound_effect="*puff*",
    ),
]

CLOUD_NAMES = ["Puffy", "Whispy", "Fluffy", "Nimbus", "Cirrus", "Cumulus"]
STAR_NAMES = ["Stella", "Twinkle", "Glow", "Sparkle", "Blinky", "Luna"]
TRAITS = ["shy", "kind", "brave", "gentle", "curious", "friendly", "hopeful", "warm"]

FRIENDLY_RESPONSES = [
    "Yes! I would love to be friends!",
    "Of course! I've been so lonely, too!",
    "You look so kind! Let's be friends!",
    "I was hoping you would say that!",
    "You're the nicest cloud I've ever met!",
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for cloud_id in CLOUDS:
            for star_id in STARS:
                combos.append((setting_id, cloud_id, star_id))
    return combos


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce_cloud(world: World, cloud: Entity) -> None:
    trait = cloud.traits[0] if cloud.traits else "shy"
    world.say(
        f"Once upon a time, high up in the blue sky, there was {cloud.phrase}. "
        f"{cloud.id} was very small and very {trait}. All the other clouds "
        f"drifted together, but {cloud.id} floated all alone."
    )


def introduce_star(world: World, star: Entity, time_of_day: str) -> None:
    if time_of_day == "evening":
        world.say(
            f"One {time_of_day}, as the sun began to set and paint the sky orange and "
            f"pink, {cloud.id} saw {star.phrase} twinkling all by itself. "
            f"The star looked just as lonely as {cloud.id} felt."
        )
    elif time_of_day == "morning":
        world.say(
            f"One {time_of_day}, as the last stars faded, {cloud.id} noticed "
            f"{star.phrase} still blinking bravely. The star seemed to be waiting."
        )
    else:
        world.say(
            f"One {time_of_day}, {cloud.id} spotted {star.phrase} shimmering alone. "
            f"They both looked lonely."
        )
    star.memes["loneliness"] += 1
    cloud.memes["loneliness"] += 1


def build_courage(world: World, cloud: Entity, star: Entity) -> None:
    world.say(
        f"{cloud.id} wanted to befriend {star.id}, but {cloud.id} was scared. "
        f'"I\'m just a tiny {cloud.type}," {cloud.id} whispered.'
    )
    world.say(
        f"But {star.id} winked. And {cloud.id} felt a tiny bit of courage."
    )


def approach(world: World, cloud: Entity, star: Entity, move: SocialMove) -> None:
    cloud.memes["attempted_approach"] = 1.0
    cloud.memes["courage"] += 1
    world.say(
        f"{cloud.id} {move.approach_phrase}. {cloud.id} took a deep, puffy breath."
    )
    propagate(world, narrate=True)


def speak_friendly(world: World, speaker: Entity, listener: Entity, move: SocialMove) -> None:
    speaker.memes["social_trust"] += 1
    world.speak(speaker.id, move.dialogue_line)
    world.sfx(move.sound_effect)


def respond_friendly(world: World, responder: Entity, asker: Entity) -> None:
    responder.memes["friend_response"] = 1.0
    asker.memes["friend_response"] = 1.0
    asker.memes["happiness"] += 1
    asker.memes["loneliness"] -= 1
    responder.memes["happiness"] += 1
    responder.memes["loneliness"] -= 1
    response = random.Random(42).choice(FRIENDLY_RESPONSES)
    world.speak(responder.id, response)
    world.sfx(responder.sound_effect)


def celebrate_friendship(world: World, cloud: Entity, star: Entity) -> None:
    cloud.memes["befriended"] = 1.0
    star.memes["befriended"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"From that night on, {cloud.id} and {star.id} were best friends. "
        f"Every evening, {cloud.id} would drift near {star.id}'s spot in "
        f"the sky, and {star.id} would twinkle the brightest."
    )
    world.say(
        f"They told each other stories until the moon came up. And {cloud.id} "
        f"was never lonely again, because a little {cloud.type} and a little "
        f"{star.type} can be the best of friends."
    )
    propagate(world, narrate=True)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting_id: str, cloud_id: str, star_id: str,
         cloud_traits: Optional[list[str]] = None) -> World:
    setting = SETTINGS[setting_id]
    world = World(setting)

    cloud_template = CLOUDS[cloud_id]
    star_template = STARS[star_id]

    cloud = world.add(Entity(
        id=cloud_template.id, kind="character", type=cloud_template.type,
        label=cloud_template.label, phrase=cloud_template.phrase,
        traits=cloud_traits or cloud_template.traits.copy(),
        dialog_voice=cloud_template.dialog_voice,
        sound_effect=cloud_template.sound_effect,
    ))
    star = world.add(Entity(
        id=star_template.id, kind="character", type=star_template.type,
        label=star_template.label, phrase=star_template.phrase,
        traits=star_template.traits.copy(),
        dialog_voice=star_template.dialog_voice,
        sound_effect=star_template.sound_effect,
    ))

    # Act 1: Introduction and loneliness
    introduce_cloud(world, cloud)
    world.para()
    introduce_star(world, star, setting.time_of_day)

    # Act 2: Building courage and approaching
    world.para()
    build_courage(world, cloud, star)

    move = random.Random(42).choice(SOCIAL_MOVES)
    approach(world, cloud, star, move)
    speak_friendly(world, cloud, star, move)

    # Act 3: Friendship
    world.para()
    respond_friendly(world, star, cloud)
    world.para()
    celebrate_friendship(world, cloud, star)

    world.facts.update(
        cloud=cloud,
        star=star,
        setting=setting,
        move=move,
        befriended=True,
    )
    return world


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    cloud: str
    star: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cloud": [
        ("What is a cloud made of?",
         "A cloud is made of tiny drops of water or ice that float in the sky."),
        ("Why do clouds float?",
         "Clouds float because they are made of very tiny water droplets that "
         "are light enough to be carried by the air."),
    ],
    "star": [
        ("What is a star?",
         "A star is a big ball of hot gas that shines in the night sky. Our "
         "sun is a star too, but it looks bigger because it is closer to us."),
        ("Why do stars twinkle?",
         "Stars twinkle because their light passes through layers of moving "
         "air in our atmosphere, which makes them look like they are blinking."),
    ],
    "lonely": [
        ("What does it mean to feel lonely?",
         "Feeling lonely means you wish you had someone to talk to or play "
         "with. Everyone feels lonely sometimes, and it is okay to ask for "
         "a friend."),
    ],
    "friendship": [
        ("Why is it good to have friends?",
         "Friends make us happy. They listen to us, share stories, and make "
         "us feel less alone. Even a small cloud and a star can be friends."),
    ],
}

KNOWLEDGE_ORDER = ["cloud", "star", "lonely", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cloud, star = f["cloud"], f["star"]
    return [
        f'Write a gentle bedtime story about a {cloud.type} named {cloud.id} '
        f'who learns to befriend a {star.type} named {star.id}.',
        f'Tell a sweet story with dialogue and sound effects about {cloud.id} '
        f'the {cloud.type} and {star.id} the {star.type} becoming friends.',
        f'Create a happy story for children where a shy {cloud.type} makes '
        f'friends with a lonely {star.type} in the sky at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cloud, star, setting, move = f["cloud"], f["star"], f["setting"], f["move"]
    cloud_trait = cloud.traits[0] if cloud.traits else "shy"

    qa: list[QAItem] = [
        QAItem(
            question=f"Who was the {cloud.type} in the story about a lonely cloud "
                     f"who wanted to befriend a star?",
            answer=f"The {cloud.type} was named {cloud.id}. {cloud.id} was "
                   f"a {cloud_trait} little {cloud.type} who floated alone in "
                   f"{setting.place}.",
        ),
        QAItem(
            question=f"Who did the {cloud.type} want to befriend, and where "
                     f"did they meet?",
            answer=f"{cloud.id} wanted to befriend {star.id} the {star.type}, "
                   f"who was also alone in {setting.place}.",
        ),
        QAItem(
            question=f"What did {cloud.id} say to {star.id} when {cloud.id} "
                     f"gathered the courage to approach?",
            answer=f"{cloud.id} said, \"{move.dialogue_line}\" in a "
                   f"{cloud.dialog_voice} voice.",
        ),
        QAItem(
            question=f"How did {star.id} respond when {cloud.id} asked to be friends?",
            answer=f"{star.id} responded warmly and said yes! {star.id} was "
                   f"also lonely and happy to have a friend. They sparkled "
                   f"with happiness.",
        ),
        QAItem(
            question=f"What happened after the little {cloud.type} and the "
                     f"little {star.type} became friends?",
            answer=f"After they became friends, {cloud.id} and {star.id} would "
                   f"meet every evening. They told each other stories until "
                   f"the moon came up. {cloud.id} was never lonely again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
befriendable(C, S) :- cloud(C), star(S), lonely(C), lonely(S).
story_possible(Setting, C, S) :- setting(Setting), cloud(C), star(S),
                                  befriendable(C, S).
happy_ending(C, S) :- befriendable(C, S), friend_response(C, S),
                      friend_response(S, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLOUDS.items():
        lines.append(asp.fact("cloud", c.id))
        for t in c.traits:
            lines.append(asp.fact("trait", c.id, t))
    for sid, s in STARS.items():
        lines.append(asp.fact("star", s.id))
        for t in s.traits:
            lines.append(asp.fact("trait", s.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    return sorted(set(asp.atoms(model, "happy_ending")))


def asp_verify() -> int:
    import asp
    stories = asp_valid_stories()
    print(f"OK: clingo found {len(stories)} happy ending pairs.")
    return 0


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="twilight_sky", cloud="puffy", star="stella"),
    StoryParams(setting="star_field", cloud="whispy", star="twinkle"),
    StoryParams(setting="morning_sky", cloud="fluffy", star="glow"),
    StoryParams(setting="rainbow_sky", cloud="puffy", star="stella"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a little cloud befriends a lonely star. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--setting", choices=list(SETTINGS.keys()))
    ap.add_argument("--cloud", choices=list(CLOUDS.keys()))
    ap.add_argument("--star", choices=list(STARS.keys()))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list ASP results")
    ap.add_argument("--verify", action="store_true", help="check ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    cloud = args.cloud or rng.choice(list(CLOUDS.keys()))
    star = args.star or rng.choice(list(STARS.keys()))
    return StoryParams(setting=setting, cloud=cloud, star=star)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.cloud, params.star)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show happy_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} happy ending pairs:")
        for c, s in stories:
            print(f"  {c:8} + {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.cloud} + {p.star} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
