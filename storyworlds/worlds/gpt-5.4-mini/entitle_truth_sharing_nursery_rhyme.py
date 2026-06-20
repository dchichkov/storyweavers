#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/entitle_truth_sharing_nursery_rhyme.py
======================================================================

A small storyworld for a nursery-rhyme style tale about sharing, where a child
tries to entitle a treat, learns the truth, and finds a kinder way to share.

Seed words:
- entitle
- truth

Feature:
- Sharing

Style:
- Nursery rhyme
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    shares: bool = False
    has_treat: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    sweet: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareThing:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["entitled"] < THRESHOLD:
            continue
        sig = ("hurt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["stubborn"] += 1
        out.append("__hurt__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared"):
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["joy"] += 1
                ent.memes["peace"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("hurt", "social", _r_hurt_feelings), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def should_share(world: World, child: Entity, friend: Entity, treat: Treat) -> bool:
    return treat.shareable and child.memes["softened"] >= THRESHOLD


def predict_scene(world: World, child: Entity, friend: Entity, treat: Treat) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["entitled"] += 1
    _argue(sim, sim.get(child.id), sim.get(friend.id), treat, narrate=False)
    return {
        "hurt": sim.get(child.id).memes["stubborn"] >= THRESHOLD,
        "shared": bool(sim.facts.get("shared")),
    }


def _argue(world: World, child: Entity, friend: Entity, treat: Treat, narrate: bool = True) -> None:
    child.memes["entitled"] += 1
    world.say(
        f'{child.id} pointed at the {treat.label} and said, "This one is mine to keep."'
    )
    if narrate:
        propagate(world, narrate=True)


def choose_truth(world: World, friend: Entity, child: Entity, treat: Treat) -> None:
    friend.memes["truthful"] += 1
    pred = predict_scene(world, child, friend, treat)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. '
        f'"That is not the truth," {friend.pronoun()} said. '
        f'"We can share the {treat.label} and both have a turn."'
    )


def soften(world: World, child: Entity, friend: Entity) -> None:
    child.memes["softened"] += 1
    child.memes["entitled"] = 0.0
    world.say(
        f'{child.id} looked again, and {child.pronoun()} softened. '
        f'"I spoke too soon," {child.id} said.'
    )


def share(world: World, child: Entity, friend: Entity, treat: Treat, thing: ShareThing) -> None:
    world.facts["shared"] = True
    child.has_treat = True
    friend.has_treat = True
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"They sat by the little window, and {thing.phrase} helped them take turns. "
        f"{child.id} had one sip, then {friend.id} had one too."
    )
    world.say(
        f"The {treat.label} stayed sweet and bright, and both children smiled at the same moon."
    )


def tell(treat: Treat, thing: ShareThing, child_name: str = "Mia", child_type: str = "girl",
         friend_name: str = "Noah", friend_type: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))

    child.memes["entitled"] = 1.0
    friend.memes["truthful"] = 1.0

    world.say(
        f"{child.id} and {friend.id} sat beneath the moon, as neat as any pair. "
        f"The {treat.label} gleamed there, {treat.sweet}, and round."
    )
    world.say(
        f'"I shall have it all," said {child.id}, "for I am the one who found it first."'
    )

    world.para()
    choose_truth(world, friend, child, treat)
    soften(world, child, friend)

    world.para()
    thing = ShareThing("cup", "little cup", "a little cup", "take turns drinking")
    share(world, child, friend, treat, thing)

    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "The truest treasure is kind hands, not a crown."'
    )

    world.facts.update(
        child=child,
        friend=friend,
        parent=parent,
        treat=treat,
        thing=thing,
        shared=True,
        outcome="shared",
    )
    return world


TREATS = {
    "cake": Treat("cake", "cake", "a little cake", "sweet as honey", tags={"cake", "sharing"}),
    "berries": Treat("berries", "berries", "a bowl of berries", "bright as beads", tags={"berries", "sharing"}),
    "cookie": Treat("cookie", "cookie", "a round cookie", "crumbly and kind", tags={"cookie", "sharing"}),
}

SHARE_THINGS = {
    "cup": ShareThing("cup", "cup", "a little cup", "sip and pass"),
    "plate": ShareThing("plate", "plate", "a small plate", "share one piece at a time"),
    "spoon": ShareThing("spoon", "spoon", "a tiny spoon", "take turns"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Ben", "Max", "Theo"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    treat: str
    share_thing: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    parent_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(t, s) for t in TREATS for s in SHARE_THINGS if TREATS[t].shareable]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treat = f["treat"]
    thing = f["thing"]
    child = f["child"]
    friend = f["friend"]
    return [
        f'Write a nursery-rhyme style story about sharing {treat.label} and telling the truth.',
        f"Tell a gentle story where {child.id} tries to entitle the {treat.label}, but {friend.id} speaks the truth and they share it.",
        f"Write a short rhyming story with the word 'truth' and a kind ending about {thing.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    treat = f["treat"]
    thing = f["thing"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two children who meet a sweet treat and learn to share it."),
        (f"What did {child.id} try to do at first?",
         f"{child.id} tried to keep the {treat.label} all for {child.pronoun('object')}. That was the entitled choice, before the truth was spoken kindly."),
        (f"What was the truth in the story?",
         f"The truth was that the {treat.label} could be shared, and both children could enjoy it. The little {thing.label} helped them take turns."),
        ("How did the story end?",
         f"It ended with both children sharing and smiling together. The treat stayed nice because they chose kindness instead of boasting."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["treat"].tags) | set(world.facts["thing"].tags) | {"sharing"}
    knowledge = {
        "sharing": [("What is sharing?",
                     "Sharing means letting someone else have a turn or a part of something too.")],
        "cake": [("What is cake?",
                  "Cake is a sweet baked treat that people often enjoy on special days.")],
        "berries": [("What are berries?",
                     "Berries are small juicy fruits, and many kinds taste sweet or tart.")],
        "cookie": [("What is a cookie?",
                    "A cookie is a small sweet baked snack, often round and crumbly.")],
        "cup": [("What is a cup for?",
                 "A cup is a small container used for drinking or holding a drink.")],
        "plate": [("What is a plate for?",
                   "A plate is used to hold food so it is easy to share and eat.")],
        "spoon": [("What is a spoon for?",
                   "A spoon is used for scooping and eating soft foods or drinks.")],
    }
    order = ["sharing", "cake", "berries", "cookie", "cup", "plate", "spoon"]
    out: list[tuple[str, str]] = []
    for tag in order:
        if tag in tags:
            out.extend(knowledge[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
entitled(E) :- character(E), meme(E, entitled), meme_value(E, V), V >= 1.
truthful(E) :- character(E), meme(E, truthful), meme_value(E, V), V >= 1.
shared_story :- fact(shared).
resolved :- shared_story.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("shareable", tid))
    for sid in SHARE_THINGS:
        lines.append(asp.fact("thing", sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show shared_story/0."))
    asp_shared = bool(asp.atoms(model, "shared_story"))
    py_shared = True
    if asp_shared == py_shared and valid_combos():
        print("OK: ASP parity and Python validity checks passed.")
    else:
        print("MISMATCH: ASP/Python parity failed.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def explain_rejection() -> str:
    return "(No story: this world always has a shareable treat, but the requested combination was impossible.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world about truth and sharing."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--share-thing", choices=SHARE_THINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    treat = args.treat or rng.choice(sorted(TREATS))
    share_thing = args.share_thing or rng.choice(sorted(SHARE_THINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if child_type == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    friend_pool = GIRL_NAMES if friend_type == "girl" else BOY_NAMES
    friend_name = args.friend_name or rng.choice([n for n in friend_pool if n != child_name] or friend_pool)
    parent_type = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(treat, share_thing, child_name, child_type, friend_name, friend_type, parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(TREATS[params.treat], SHARE_THINGS[params.share_thing],
                 params.child_name, params.child_type, params.friend_name,
                 params.friend_type, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show shared_story/0.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible treat/share combos:")
        for t, s in valid_combos():
            print(f"  {t:8} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(t, s, "Mia", "girl", "Noah", "boy", "mother")) for t, s in valid_combos()]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
