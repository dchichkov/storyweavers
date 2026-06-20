#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/incessant_surprise_friendship_lesson_learned_nursery_rhyme.py
=============================================================================================

A standalone tiny storyworld in a nursery-rhyme voice: a child expects the same
little surprise again and again, a friend keeps helping, the surprise changes,
and a lesson is learned about noticing others' feelings.

This world is built from a small simulated domain rather than a frozen paragraph.
It models:
- a child with a persistent request,
- a friend who can share, wait, or reveal a surprise,
- a small object of surprise that can run out,
- friendship as an emotional state,
- a lesson learned at the end.

The keyword "incessant" appears in the story when the child's repeated asking
matters to the plot.

The story aims to feel like a nursery rhyme: short beats, concrete images,
simple repetition, and a final image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/incessant_surprise_friendship_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/incessant_surprise_friendship_lesson_learned_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/incessant_surprise_friendship_lesson_learned_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4-mini/incessant_surprise_friendship_lesson_learned_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4-mini/incessant_surprise_friendship_lesson_learned_nursery_rhyme.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""  # child | friend | grownup | object
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class SurpriseThing:
    id: str
    label: str
    phrase: str
    sparkle: str
    one_time: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Reaction:
    id: str
    sense: int
    text: str
    fallback: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    grownup: str
    surprise: str
    reaction: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


CHILD_NAMES = ["Mia", "Lily", "Noah", "Theo", "Ava", "Milo", "Zoe", "Ben"]
GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ruby"]
BOY_NAMES = ["Noah", "Theo", "Milo", "Ben", "Finn", "Leo"]
GROWNUPS = ["mom", "dad", "grandma", "grandpa"]
TRAITS = ["bright", "small", "gentle", "cheery", "curious"]

SURPRISES = {
    "bells": SurpriseThing(
        "bells", "jingle bells", "a small tin of jingle bells", "tinkly and bright",
        tags={"sound", "toy"},
    ),
    "bubbles": SurpriseThing(
        "bubbles", "bubble wand", "a bubble wand with a blue ring", "shiny and round",
        tags={"bubbles", "toy"},
    ),
    "lantern": SurpriseThing(
        "lantern", "paper lantern", "a little paper lantern", "glowy and warm",
        tags={"light", "paper"},
    ),
}

REACTIONS = {
    "share": Reaction(
        "share", 3,
        "shared the surprise with a smile",
        "tried to share it, but there was not enough left",
        tags={"kind", "share"},
    ),
    "wait": Reaction(
        "wait", 3,
        "waited a little while and then offered it again",
        "waited, but the surprise had already ended",
        tags={"kind", "wait"},
    ),
    "teach": Reaction(
        "teach", 4,
        "showed how a friend can take turns and listen",
        "could not make it right, because the surprise was already gone",
        tags={"lesson", "turns"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about incessant asking, surprise, friendship, and a lesson learned."
    )
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, r, "story") for s in SURPRISES for r in REACTIONS if REACTIONS[r].sense >= 3]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for r, rr in REACTIONS.items():
        lines.append(asp.fact("reaction", r))
        lines.append(asp.fact("sense", r, rr.sense))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- reaction(R), sense(R,S), sense_min(M), S >= M.
valid(S, R) :- surprise(S), reaction(R), sensible(R).
"""


def asp_program(extra: str = "", show: str = "#show valid/2.\n#show sensible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def explain_rejection() -> str:
    return "(No story: that choice would not support a gentle nursery-rhyme lesson.)"


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= 3]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reaction and REACTIONS[args.reaction].sense < 3:
        raise StoryError("(No story: that reaction is too weak for a clear lesson.)")
    combos = valid_combos()
    if not combos:
        raise StoryError("(No story: no valid combos.)")
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    reaction = args.reaction or rng.choice(sorted(r.id for r in sensible_reactions()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    child = args.child or rng.choice(child_pool)
    friend = args.friend or rng.choice([n for n in friend_pool if n != child] or friend_pool)
    grownup = args.grownup or rng.choice(GROWNUPS)
    return StoryParams(child, child_gender, friend, friend_gender, grownup, surprise, reaction)


def _rule_repeat(world: World) -> None:
    child = world.get("child")
    if child.memes["ask"] >= THRESHOLD and ("repeat",) not in world.fired:
        world.fired.add(("repeat",))
        child.memes["eager"] += 1
        world.say(f"{child.id} asked again and again, in an incessant little ring.")


def _rule_friendship(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["shared"] >= THRESHOLD and friend.memes["kind"] >= THRESHOLD and ("friendship",) not in world.fired:
        world.fired.add(("friendship",))
        child.memes["friendship"] += 1
        friend.memes["friendship"] += 1


def propagate(world: World, narrate: bool = True) -> None:
    _rule_repeat(world)
    _rule_friendship(world)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    grownup = world.add(Entity(id=params.grownup.capitalize(), kind="character", type="mother", role="grownup", label=params.grownup))
    surprise = world.add(Entity(id=params.surprise, kind="thing", type="thing", label=SURPRISES[params.surprise].label))
    reaction = REACTIONS[params.reaction]

    child.memes["ask"] = 1.0
    friend.memes["kind"] = 1.0

    world.say(f"On a merry little morning, {child.id} and {friend.id} went skipping hand in hand.")
    world.say(f"{child.id} wanted a surprise, and asked, then asked, then asked again, with incessant cheer.")
    world.para()
    world.say(f"{friend.id} brought out {SURPRISES[params.surprise].phrase}, {SURPRISES[params.surprise].sparkle}.")
    world.say(f"The little gift was for sharing, and both children clapped their hands.")
    world.say(f"But {child.id} kept wanting more, and the surprise could not stay forever.")
    child.memes["ask"] += 1
    surprise.meters["used"] += 1
    if params.reaction == "share":
        child.memes["shared"] += 1
        friend.memes["kind"] += 1
        world.say(f"{friend.id} {reaction.text}.")
        world.say(f"{child.id} learned that a surprise is sweeter when friends take turns and smile.")
    elif params.reaction == "wait":
        friend.memes["kind"] += 1
        world.say(f"{friend.id} {reaction.text}.")
        world.say(f"{grownup.label_word.capitalize()} said, 'A kind heart knows when to wait.'")
    else:
        child.memes["shared"] += 1
        friend.memes["kind"] += 1
        world.say(f"{friend.id} {reaction.text}.")
        world.say(f"{grownup.label_word.capitalize()} showed them how a friend can share, listen, and make the moment last in a better way.")
    propagate(world, narrate=False)
    world.para()
    child.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(f"In the end, {child.id} and {friend.id} held hands and sang their small song.")
    if params.reaction == "share":
        world.say(f"The jingle bells rang once, then rested quiet, and friendship rang louder.")
    elif params.reaction == "wait":
        world.say(f"The bubble ring floated away, but the waiting made their bond grow bright.")
    else:
        world.say(f"The paper lantern glowed softly, and the lesson learned shone even after the light went out.")

    world.facts.update(
        child=child, friend=friend, grownup=grownup, surprise=surprise,
        reaction=reaction, outcome=params.reaction, story_kind="nursery",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery rhyme with the word 'incessant' about {f['child'].id} and {f['friend'].id}, surprise, and friendship.",
        f"Tell a small sing-song story where {f['child'].id} keeps asking for a surprise and {f['friend'].id} helps a lesson be learned.",
        f"Write a gentle rhyme about a surprise that changes because a friend keeps sharing with kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    grownup = f["grownup"]
    surprise = f["surprise"]
    out = f["outcome"]
    ans1 = (
        f"{child.id} kept asking for a surprise, and {friend.id} stayed beside {child.pronoun('object')}."
        f" The story turns because the asking is incessant and the friendship stays warm."
    )
    ans2 = (
        f"{friend.id} shared the surprise, waited, or taught a kinder turn, depending on the beat."
        f" That choice helped the children keep smiling instead of feeling upset."
    )
    ans3 = (
        f"{grownup.label_word.capitalize()} helped at the end and made the lesson clear."
        f" The small surprise could not last forever, but the friendship did."
    )
    return [
        QAItem(f"Who are the story children?", ans1),
        QAItem("What changed when the surprise could not stay forever?", ans2),
        QAItem("Who helped the children learn the lesson?", ans3),
        QAItem("How did the story end?", f"It ended with {child.id} and {friend.id} holding hands and learning that sharing and waiting keep friendship bright."),
        QAItem("What was the surprise?", f"It was {surprise.phrase}."),
        QAItem("What was learned?", f"The children learned to be kind with a surprise and to respect a friend.")
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    s = f["surprise"].label
    if s == "jingle bells":
        return [QAItem("What do jingle bells do?", "Jingle bells make a light ringing sound when they move."), QAItem("Why can a small surprise be exciting?", "A small surprise feels exciting because it is new and sparkly and makes children want to look again.")]
    if s == "bubble wand":
        return [QAItem("What does a bubble wand make?", "A bubble wand makes bubbles by blowing or waving so little round bubbles float in the air."), QAItem("Why do bubbles feel magical?", "Bubbles look shiny, float softly, and vanish quickly, so they feel magical to children.")]
    return [QAItem("What is a paper lantern?", "A paper lantern is a light made with paper that glows gently when lit safely."), QAItem("Why should grown-ups help with lights?", "Grown-ups help so the light stays safe and kind.")]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    parts.append("")
    parts.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mia", "girl", "Noah", "boy", "mom", "bells", "share"),
    StoryParams("Theo", "boy", "Ava", "girl", "dad", "bubbles", "wait"),
    StoryParams("Lily", "girl", "Ben", "boy", "grandma", "lantern", "teach"),
]


def asp_verify() -> int:
    import asp
    p = set(asp_valid_combos())
    q = set(valid_combos())
    ok = 0
    if p != q:
        ok = 1
        print("MISMATCH in valid combos.")
        if p - q:
            print(" only in ASP:", sorted(p - q))
        if q - p:
            print(" only in Python:", sorted(q - p))
    s = set(asp_sensible())
    r = {x.id for x in sensible_reactions()}
    if s != r:
        ok = 1
        print("MISMATCH in sensible reactions.")
    smoke = generate(resolve_params(argparse.Namespace(child=None, child_gender=None, friend=None, friend_gender=None, grownup=None, surprise=None, reaction=None), random.Random(7)))
    if not smoke.story.strip():
        ok = 1
        print("SMOKE FAIL: empty story.")
    return ok


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reaction and REACTIONS[args.reaction].sense < 3:
        raise StoryError("(No story: that reaction is too weak for a lesson learned.)")
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, r in combos:
            print(f"  {s:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_args(args, random.Random(seed))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
