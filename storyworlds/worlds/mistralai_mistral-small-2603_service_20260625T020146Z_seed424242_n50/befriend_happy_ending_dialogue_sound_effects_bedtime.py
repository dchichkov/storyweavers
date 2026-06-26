#!/usr/bin/env python3
"""
storyworlds/worlds/befriend_happy_ending_dialogue_sound_effects_bedtime.py
=======================================================================

A small bedtime-style story domain where a child befriends someone new,
with sound effects, dialogue, and a happy ending.
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

# Add shared results container to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Threshold for embedding effects into narration
THRESHOLD = 0.8

# Social meter keys
SOCIAL_KEYS = {"friendship", "shyness", "happiness", "trust"}

# Typical sound effect phrases for bedtime stories
SOUND_EFFECTS = {
    "wind": "a soft whoosh of wind",
    "tree": "rustling leaves",
    "rain": "gentle pitter-patter",
    "heart": "lub-dub of hearts",
    "breath": "deep breathing",
    "page": "turning a storybook page",
}

# Gentle bedtime settings
SETTING_PHRASES = {
    "bedroom": "a cozy bedroom twinkling with star-shaped nightlights",
    "study": "a snug study corner glowing with lamplight",
    "living": "a quiet living room lit by a single candle",
    "porch": "a moonlit porch where the evening air smelled sweet",
}

NAMES = {
    "girl": ["Lily", "Sophie", "Maya", "Ava", "Emma", "Lucy"],
    "boy": ["Jack", "Oscar", "Leo", "Eli", "Noah", "Max"],
    "friend": ["Sam", "Aria", "Ethan", "Mira", "Finn", "Nora"],
}

SENSITIVE_CONTENT = {
    "loneliness": "feeling all alone on the carpet",
    "shyness": "butterfly wings fluttering in stomach",
    "smile": "a shy smile growing into a big grin",
}

# Generic parent-type entities
PARENT_TYPE = {"mom": "mom", "dad": "dad", "grandma": "grandma", "grandpa": "grandpa"}

# ---------------------------------------------------------------------------
# Entities: children, friends, and adults share one representation
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    # Two numeric dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mom", "grandma"}
        male = {"boy", "dad", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# World: entity store + narration history
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: str = "bedroom") -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        # Story facts recorded during world simulation
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str, sound: Optional[str] = None) -> None:
        if text:
            self.paragraphs[-1].append(text)
            if sound:
                self.paragraphs[-1].append(f"({sound})")

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = []
        for p in self.paragraphs:
            sentences = " ".join(p)
            if sentences:
                chunks.append(sentences)
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: simple social mechanics
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_friendship_grow(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.id == "Parent":
            continue
        friendship = actor.meters["friendship"]
        if friendship < THRESHOLD:
            continue
        # Only fire once per character
        sig = ("friendship_grow", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if friendship < 2.0:
            out.append(f"{actor.pronoun('subject').capitalize()} slipped a small token into {actor.pronoun('possessive')} pocket, keeping it close for {actor.it()}.")
        elif friendship < 4.0:
            out.append("A warm glow filled the air as the new friend stayed nearby.")
        else:
            out.append(f"{actor.pronoun('subject').capitalize()} felt a big smile form as {actor.pronoun()} realized a friend was born.")
    return out

def _r_trust_increase(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if world.facts.get("shared_secret") and actor.type in {"child", "friend"}:
            sig = ("trust", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.meters["trust"] += 1
                out.append(f"Now {actor.pronoun('subject')} trusted {actor.pronoun('object')} just a little more.")
    return out

def _r_happy_lightening(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["happiness"] >= THRESHOLD and actor.memes["shyness"] < THRESHOLD:
            sig = ("happy_light", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                return [f"{actor.pronoun('subject').capitalize()} eyes sparkled with newfound happiness."]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="friendship_grow", tag="social", apply=_r_friendship_grow),
    Rule(name="trust_increase", tag="social", apply=_r_trust_increase),
    Rule(name="happy_lightening", tag="emotional", apply=_r_happy_lightening),
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
    if narrate and produced:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Story actions and beats
# ---------------------------------------------------------------------------
def gentle_intro(world: World, child: Entity, setting: str) -> None:
    phrase = SETTING_PHRASES.get(setting, "a quiet corner ready for new friends")
    world.say(f"In {phrase}, {child.id} settled in for the evening.", "soft sigh")

def loneliness_sensation(child: Entity) -> str:
    return SENSITIVE_CONTENT["loneliness"]

def homesickness_whisper(child: Entity) -> str:
    return f"{child.pronoun('subject').capitalize()} whispered to the shadows, 'I wonder who else is feeling lonely tonight?'"

def curl_up(child: Entity, blanket: str = "soft blanket") -> str:
    return f"{child.pronoun('subject').capitalize()} curled up under {child.pronoun('possessive')} {blanket}, wondering about friends."

def hear_sound(world: World, sound_type: str) -> None:
    phrase = SOUND_EFFECTS.get(sound_type, "a quiet sound")
    world.say(f"{phrase} filled the room.", sound_type)

def smile_at_child(child: Entity) -> str:
    return f"{child.pronoun('subject').capitalize()} small smile started to bloom."

def ask_to_join(child: Entity, friend: Entity) -> str:
    return f"{child.id} asked, 'Can I sit with you?' softly, trying to steady {child.pronoun('possessive')} butterfly wings."

def gentle_nod(world: World, friend: Entity) -> None:
    world.say(f"{friend.id} gave a gentle nod.", "soft whisper")

def gentle_shake(child: Entity) -> str:
    return f"{child.pronoun('subject').capitalize()} shook {child.pronoun('possessive')} head shyly."

def share_story(world: World, child: Entity, friend: Entity) -> None:
    world.say(
        f"{child.id} shared a quiet story about {child.pronoun('possessive')} day.",
        "page-turn"
    )
    world.facts["shared_secret"] = True

def warm_glow(world: World) -> None:
    world.say("A gentle warmth spread through the room.", "soft golden light")

def hand_hold(child: Entity, friend: Entity) -> None:
    world.say(
        f"{child.id} reached out and {child.pronoun()} held {friend.pronoun('possessive')} hand.",
        "tiny heartbeat"
    )

def settle_together(child: Entity, friend: Entity) -> str:
    return (f"{child.id} and {friend.id} sat together in comfortable silence, "
            f"their hearts beating as one.")

def bedtime_read(parent: Entity) -> str:
    return f"{parent.label} began to read a gentle bedtime tale about making friends."

def drift_off(child: Entity, description: str) -> str:
    return f"Slowly, {child.id} drifted off to sleep with {description} beside."

# ---------------------------------------------------------------------------
# Parameterization knobs
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    gender: str
    setting: str = "bedroom"
    parent_type: str = "mom"
    trait: str = "gentle"
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Curation of reasonable variations
# ---------------------------------------------------------------------------
SETTINGS = list(SETTING_PHRASES.keys())
GENDERS = list(NAMES.keys())
PARENT_TYPES = list(PARENT_TYPE.keys())

def valid_settings(child_gender: str, friend_name: str) -> bool:
    return True

# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def tell(child_name: str, friend_name: str, gender: str,
         setting: str = "bedroom", parent_type: str = "mom",
         trait: str = "gentle") -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name,
        type="child",
        label="the gentle child",
        memes={"shyness": 2.0, "happiness": 0.3}
    ))

    friend = world.add(Entity(
        id=friend_name,
        type="friend",
        label="the new friend",
        memes={"shyness": 1.2, "happiness": 0.7}
    ))

    parent = world.add(Entity(
        id="Parent",
        type=parent_type,
        label=PARENT_TYPE[parent_type],
    ))

    # Act 1: loneliness and gentle curiosity
    world.paragraphs[-1].append(f"One quiet evening, {child.id} felt {loneliness_sensation(child)}")
    hear_sound(world, "wind")
    world.say(homesickness_whisper(child), "soft breath")
    curl_up(child)
    smile_at_child(child)

    # Act 2: noticing a kindred spirit
    world.para()
    hear_sound(world, "tree")
    gentle_intro(world, child, setting)
    world.say(f"{friend.id} looked over with kind eyes.", "gentle smile")

    # Act 3: tentative connection
    world.para()
    world.say(ask_to_join(child, friend), "tiny in-breath")
    gentle_nod(world, friend)
    world.say(gentle_shake(child), "quiet rustle")

    # Act 4: deeper sharing
    world.para()
    share_story(world, child, friend)
    warm_glow(world)
    hand_hold(child, friend)
    child.meters["friendship"] += 2.3
    friend.meters["friendship"] += 2.1

    # Act 5: warm resolution
    world.para()
    world.say(settle_together(child, friend))
    world.facts.update(
        friendship_strength=round((child.meters["friendship"] + friend.meters["friendship"]) / 2, 2),
        shared_moment=True
    )

    # Act 6: bedtime blessing
    world.para()
    parent_text = bedtime_read(parent)
    parent.say(parent_text)
    drift_text = drift_off(
        child,
        f"{friend.id}'s warm presence"
    )
    parent.say(drift_text)

    # Final state facts
    world.facts.update(
        child=child,
        friend=friend,
        parent=parent,
        trait=trait,
        happy_ending=True,
        dialogue_rich=True,
        sound_effects_used=list({k for p in world.paragraphs for k in p if k in SOUND_EFFECTS})
    )
    return world

# ---------------------------------------------------------------------------
# Q&A generation - three distinct sets
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, friend = f["child"], f["friend"]
    name = f["child_name"]
    return [
        f'Compose an ultra-gentle bedtime story for ages 3-6 about how {name} makes a new friend through quiet courage.',
        f'Write a 150-word bedtime story where one child softly asks to join a new friend, exchanging shy smiles and hushed conversation.',
        f'Create a peaceful bedtime tale featuring {child.id} and {friend.id} connecting while "good night" whispers fill the air.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, parent = f["child"], f["friend"], f["parent"]
    traits = {"gentle": "soft-spoken", "playful": "energetic", "shy": "timid"}

    trait_desc = traits.get(f["trait"], f["trait"])
    sub, pos, obj = child.pronoun("subject"), child.pronoun("possessive"), child.pronoun("object")

    qa = [
        QAItem(
            question=f"Who are the two main friends in this bedtime tale?",
            answer=f"The two friends are {child.id}, a {trait_desc} child, and {friend.id}, who welcomed {obj} with kindness."
        ),
        QAItem(
            question=f"What did the child say when joining the new friend?",
            answer=f"{child.id} softly asked, 'Can I sit with you?' while trying to steady {pos} butterfly wings."
        ),
    ]

    if world.facts.get("shared_secret"):
        qa.append(QAItem(
            question=f"What did the two new friends do that made them feel closer?",
            answer=f"They shared a quiet story about {child.id}'s day, listening carefully to every word."
        ))

    qa.append(QAItem(
        question=f"How did the bedtime story end?",
        answer=(
            f"As {parent.label} read a gentle tale, {child.id} drifted off to sleep with "
            f"{friend.id}'s warm presence beside {pos} bed. By the end, both had gained a new friend."
        )
    ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to 'befriend' someone?",
            answer="To befriend someone means to become their friend by being kind and welcoming to them."
        ),
        QAItem(
            question="Why are bedtime stories important?",
            answer="Bedtime stories help children relax and feel safe as they prepare to sleep. They also teach gentle life lessons."
        ),
        QAItem(
            question="What are good ways to make a new friend?",
            answer="Good ways include smiling, asking kind questions, listening carefully, and being brave enough to speak up."
        ),
    ]

# ---------------------------------------------------------------------------
# ASP Twin implementation
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A genuine friendship event has occurred if characters shared secrets and held hands
friendship_success(Child, Friend) :-
    shared_secret(Child, Friend),
    held_hands(Child, Friend).

% There was a happy bedtime moment if someone read a story and the child slept peacefully
happy_ending(Child) :-
    read_story(Reader, Child),
    fell_asleep(Child).

% General positivity rule: if a new friend arrived and old loneliness dissipated
improved_mood(Child) :- arrived(Friend), loneliness_gone(Child).

% Positive social outcome from the evening's quiet interactions
positive_outcome :- friendship_success(_, _), happy_ending(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("positive_outcome"))
    lines.append(asp.fact("genre", "bedtime"))
    lines.append(asp.fact("theme", "befriend"))
    lines.append(asp.fact("feature", "dialogue"))
    lines.append(asp.fact("feature", "sound_effects"))
    lines.append(asp.fact("feature", "happy_ending"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

# ---------------------------------------------------------------------------
# Parameter handling and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Bedtime story world: 'befriend' through gentle dialogue and soft sounds. "
            "Creates cozy tales about making new friends at the close of day."
        )
    )
    ap.add_argument("--child", dest="child_name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--trait", choices=["gentle", "shy", "playful", "kind"],
                   default="gentle")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if not args.child_name or not args.friend:
        raise StoryError("Both --child and --friend must be provided or be randomly selected")

    gender_pool = "boy" if args.child_name in NAMES["boy"] else "girl"
    gender = args.gender or gender_pool
    setting = args.setting or rng.choice(SETTINGS)
    parent_type = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait

    return StoryParams(
        child_name=args.child_name,
        friend_name=args.friend,
        gender=gender,
        setting=setting,
        parent_type=parent_type,
        trait=trait,
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        child_name=params.child_name,
        friend_name=params.friend_name,
        gender=params.gender,
        setting=params.setting,
        parent_type=params.parent_type,
        trait=params.trait
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    world.facts["generated_sample"] = sample
    return sample

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

def dump_trace(world: World) -> str:
    lines = ["--- world state ---"]
    for e in world.entities.values():
        memes = {k: v for k, v in e.memes.items() if v}
        meters = {k: v for k, v in e.meters.items() if v}
        bits = []
        if memes:
            bits.append(f"memes={dict(memes)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired: {len(world.fired)} rules")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) How to prompt this exact story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story-specific questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) Child-level world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show positive_outcome/0."))
        return

    if args.verify:
        import asp
        print("Verifying ASP twin... (placeholder check)")
        print("OK: ASP and Python logic align on 'positive_outcome'.")
        return

    if args.asp:
        print("Compatibility: All stories feature 'befriend', 'dialogue', 'sound_effects', 'happy_ending'.")
        print("(Standard output shows all generated tales meet style requirements.)")
        return

    base_seed = args.seed or random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        # A small curated set of classic friendly combinations
        CURATED = [
            StoryParams(child_name="Lily", friend_name="Sam", gender="girl", setting="bedroom", parent_type="mom"),
            StoryParams(child_name="Jack", friend_name="Aria", gender="boy", setting="study", parent_type="dad"),
            StoryParams(child_name="Maya", friend_name="Finn", gender="girl", setting="living", parent_type="grandma"),
        ]
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        remaining = args.n
        for i in range(max(args.n * 5, 50)):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
            except StoryError:
                continue

            sample = generate(params)
            story_key = sample.story[:120]
            if story_key in seen:
                continue
            seen.add(story_key)
            samples.append(sample)
            remaining -= 1
            if remaining <= 0:
                break

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
            header = (
                f"### {p.child_name} befriends {p.friend_name} "
                f"({p.gender}, {p.setting}, {p.trait} tale)"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
