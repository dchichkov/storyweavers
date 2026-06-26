#!/usr/bin/env python3
"""
A bedtime-story world about a child, a spam message, and a learned lesson.

Premise:
A child gets a strange message in a cozy evening scene. The message is spam,
and the child must learn not to trust it or click it.

World model:
- physical meters: screen_glow, tiredness, clutter, calm
- emotional memes: curiosity, worry, trust, relief, pride, caution, learned
- the spam can add clutter and worry if clicked
- a caregiver helps the child pause, check the sender, and delete the spam
- the ending proves the lesson by showing the inbox calm and the child ready
  for sleep
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the bedroom"
    cozy_detail: str = "a small lamp glowed by the bed"


@dataclass
class SpamMessage:
    subject: str
    sender: str
    bait: str
    danger: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    caregiver: str
    caregiver_type: str
    spam_kind: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", cozy_detail="a soft lamp glowed beside the bed"),
    "study_nook": Setting(place="the study nook", cozy_detail="a warm desk light made the papers look sleepy"),
    "living_room": Setting(place="the living room", cozy_detail="the couch was tucked under a quiet blanket"),
}

SPAM_REGISTRY = {
    "prize": SpamMessage(
        subject="You have won a prize!",
        sender="Lucky Cloud",
        bait="a shiny prize",
        danger="a bad link",
        lesson="not every bright promise is true",
    ),
    "game": SpamMessage(
        subject="Free game coins inside!",
        sender="Game Spark",
        bait="free coins",
        danger="a trick to click a strange button",
        lesson="free things can hide a trap",
    ),
    "dragon": SpamMessage(
        subject="Click here for a dragon surprise!",
        sender="Spark Mail",
        bait="a surprise",
        danger="a fake button",
        lesson="a friendly-looking note can still be spam",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Ava", "Noah", "Luna", "Eli", "Zoe", "Finn"]
CAREGIVER_NAMES = ["Mom", "Dad", "Nana", "Papa", "Aunt Rose", "Uncle Ben"]
TRAITS = ["sleepy", "curious", "gentle", "small", "brave", "quiet"]


class World:
    def __init__(self, setting: Setting, spam: SpamMessage) -> None:
        self.setting = setting
        self.spam = spam
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting, self.spam)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _inc(e: Entity, key: str, amount: float = 1.0, target: str = "memes") -> None:
    store = e.meters if target == "meters" else e.memes
    store[key] = store.get(key, 0.0) + amount


def spam_is_risky(world: World, child: Entity) -> bool:
    return True


def _inspect_message(world: World, child: Entity) -> None:
    if "inspect" in world.fired:
        return
    world.fired.add("inspect")
    _inc(child, "curiosity", 1.0)
    _inc(child, "caution", 1.0)
    world.say(
        f"{child.id} saw a new message with the subject '{world.spam.subject}'."
    )


def _spam_pull(world: World, child: Entity) -> None:
    if "spam_pull" in world.fired:
        return
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return
    world.fired.add("spam_pull")
    _inc(child, "worry", 1.0)
    _inc(child, "trust", -0.5)
    _inc(child, "clutter", 1.0, target="meters")
    world.say(
        f"The note looked bright, but it was only spam, with a trick hiding inside."
    )


def _caregiver_help(world: World, child: Entity, caregiver: Entity) -> None:
    if "help" in world.fired:
        return
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return
    world.fired.add("help")
    _inc(child, "relief", 1.0)
    _inc(child, "caution", 1.0)
    _inc(child, "learned", 1.0)
    _inc(caregiver, "pride", 1.0)
    world.say(
        f"{caregiver.id} sat beside {child.id} and said, 'Let's check the sender before we touch anything.'"
    )


def _delete_spam(world: World, child: Entity) -> None:
    if "delete" in world.fired:
        return
    if child.memes.get("learned", 0.0) < THRESHOLD:
        return
    world.fired.add("delete")
    _inc(child, "relief", 1.0)
    _inc(child, "calm", 1.0)
    _inc(child, "trust", 0.5)
    world.say(
        f"{child.id} deleted the spam, and the inbox felt lighter right away."
    )


def _bedtime_settle(world: World, child: Entity, caregiver: Entity) -> None:
    if "bedtime" in world.fired:
        return
    world.fired.add("bedtime")
    _inc(child, "tiredness", 1.0, target="meters")
    _inc(child, "calm", 1.0)
    world.say(
        f"Then {caregiver.id} pulled up the blanket, and {child.id} rested with a quiet smile."
    )


def propagate(world: World) -> None:
    child = next(e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"})
    caregiver = next(e for e in world.entities.values() if e.kind == "character" and e.id != child.id)
    _inspect_message(world, child)
    _spam_pull(world, child)
    _caregiver_help(world, child, caregiver)
    _delete_spam(world, child)
    _bedtime_settle(world, child, caregiver)


def build_story(world: World) -> World:
    child = world.add(Entity(id=world.facts["child"], kind="character", type=world.facts["child_type"]))
    caregiver = world.add(Entity(id=world.facts["caregiver"], kind="character", type=world.facts["caregiver_type"]))

    _inc(child, "tiredness", 1.0, target="meters")
    _inc(child, "curiosity", 1.0)
    _inc(child, "calm", 1.0)

    world.say(f"It was bedtime in {world.setting.place}, and {world.setting.cozy_detail}.")
    world.say(f"{child.id} was a {world.facts['trait']} little {child.type}, snug under the covers.")
    world.say(f"Just then, a message popped up with the line '{world.spam.subject}'.")

    propagate(world)

    world.say(
        f"By the end, {child.id} knew that {world.spam.lesson}, and the screen was dark and still again."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story for a young child about {f['child']} noticing spam and learning a safe habit.",
        f"Tell a gentle story in which {f['child']} is tempted by a fake message, but {f['caregiver']} helps {f['child']} make a careful choice.",
        f"Create a cozy bedtime tale where the lesson is that {world.spam.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    spam = world.spam
    return [
        QAItem(
            question=f"What did {child} see on the screen at bedtime?",
            answer=f"{child} saw a spam message with the subject '{spam.subject}'.",
        ),
        QAItem(
            question=f"What did {caregiver} tell {child} to do before touching the message?",
            answer=f"{caregiver} told {child} to check the sender first and not click right away.",
        ),
        QAItem(
            question=f"What lesson did {child} learn by the end of the story?",
            answer=f"{child} learned that {spam.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is spam?",
            answer="Spam is an unwanted message or email that often tries to trick people into clicking, buying, or sharing something unsafe.",
        ),
        QAItem(
            question="What should you do when a message looks suspicious?",
            answer="You should pause, check who sent it, and ask a trusted adult before clicking anything.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: v for k, v in e.memes.items() if abs(v) > 1e-9}
        parts = [f"{e.id} ({e.type})"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append("  " + " ".join(parts))
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for k, spam in SPAM_REGISTRY.items():
        lines.append(asp.fact("spam_kind", k))
        lines.append(asp.fact("spam_subject", k, spam.subject))
        lines.append(asp.fact("spam_sender", k, spam.sender))
        lines.append(asp.fact("spam_lesson", k, spam.lesson))
    return "\n".join(lines)


ASP_RULES = r"""
% A spam kind is suspicious when it promises bait and a danger.
suspicious(K) :- spam_kind(K), spam_subject(K,_), spam_sender(K,_), spam_lesson(K,_).

% A good lesson is learned when the child pauses, asks for help, and deletes spam.
learned(K) :- suspicious(K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as ex:
        print(f"ASP unavailable: {ex}")
        return 1
    model = asp.one_model(asp_program("#show suspicious/1."))
    suspicious = sorted(set(asp.atoms(model, "suspicious")))
    expected = sorted((k,) for k in SPAM_REGISTRY)
    if suspicious != expected:
        print("MISMATCH between ASP and Python registry.")
        print("ASP:", suspicious)
        print("PY :", expected)
        return 1
    print(f"OK: ASP matches Python registry ({len(suspicious)} spam kinds).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about spam and a learned lesson.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caregiver")
    ap.add_argument("--caregiver-type", choices=["mother", "father"])
    ap.add_argument("--spam-kind", choices=sorted(SPAM_REGISTRY))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    caregiver_type = args.caregiver_type or rng.choice(["mother", "father"])
    child = args.child or rng.choice(CHILD_NAMES)
    caregiver = args.caregiver or rng.choice(CAREGIVER_NAMES)
    spam_kind = args.spam_kind or rng.choice(list(SPAM_REGISTRY))
    return StoryParams(
        setting=setting,
        child=child,
        child_type=child_type,
        caregiver=caregiver,
        caregiver_type=caregiver_type,
        spam_kind=spam_kind,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    spam = SPAM_REGISTRY[params.spam_kind]
    world = World(setting, spam)
    world.facts.update(
        child=params.child,
        child_type=params.child_type,
        caregiver=params.caregiver,
        caregiver_type=params.caregiver_type,
        trait=random.Random(params.seed or 0).choice(TRAITS),
    )
    build_story(world)
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
    StoryParams(setting="bedroom", child="Mia", child_type="girl", caregiver="Mom", caregiver_type="mother", spam_kind="prize"),
    StoryParams(setting="study_nook", child="Leo", child_type="boy", caregiver="Dad", caregiver_type="father", spam_kind="game"),
    StoryParams(setting="living_room", child="Luna", child_type="girl", caregiver="Nana", caregiver_type="mother", spam_kind="dragon"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show suspicious/1.\n#show learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspicious/1.\n#show learned/1."))
        print("suspicious kinds:", sorted(set(asp.atoms(model, "suspicious"))))
        print("learned kinds:", sorted(set(asp.atoms(model, "learned"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.child} + {p.spam_kind}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
