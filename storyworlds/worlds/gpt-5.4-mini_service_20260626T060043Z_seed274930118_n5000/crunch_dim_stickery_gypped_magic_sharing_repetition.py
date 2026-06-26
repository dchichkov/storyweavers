#!/usr/bin/env python3
"""
A small bedtime-story world about crunchy dim light, sticky magic, sharing, and
the hurt feeling of being gypped. The story is driven by simulated state: a child
wants a magical thing, a friend shares, the spell repeats, and the ending proves
what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    keeper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Setting:
    place: str
    dim: str
    magic_ok: bool = True


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    sticky: bool = False
    repeatable: bool = False
    shared: bool = False


@dataclass
class StoryParams:
    setting: str
    gift: str
    child_name: str
    child_type: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "window": Setting(place="the bedroom window", dim="crunch-dim", magic_ok=True),
    "hall": Setting(place="the hall", dim="crunch-dim", magic_ok=True),
    "attic": Setting(place="the attic", dim="dim", magic_ok=True),
    "garden": Setting(place="the moonlit garden", dim="dim", magic_ok=True),
}

GIFTS = {
    "glowstone": Gift(
        id="glowstone",
        label="glow stone",
        phrase="a warm glow stone with a tiny star inside",
        sticky=True,
        repeatable=True,
        shared=True,
    ),
    "sparklejar": Gift(
        id="sparklejar",
        label="sparkle jar",
        phrase="a little sparkle jar full of sleepy light",
        sticky=False,
        repeatable=True,
        shared=True,
    ),
    "moonribbon": Gift(
        id="moonribbon",
        label="moon ribbon",
        phrase="a silver moon ribbon that could catch the dim",
        sticky=True,
        repeatable=False,
        shared=False,
    ),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Ivy", "Maya", "Rose"]
NAMES_BOY = ["Finn", "Theo", "Ben", "Leo", "Noah", "Max"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_sticky(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters.get("sticky", 0) < THRESHOLD:
            continue
        if e.meters.get("shared", 0) >= THRESHOLD:
            continue
        sig = ("sticky", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = e.memes.get("worry", 0) + 1
        out.append(f"{e.label.capitalize()} felt stickery and a little worried.")
    return out


def _r_repeat(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters.get("repeat", 0) < 2:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["comfort"] = e.memes.get("comfort", 0) + 1
        out.append(f"The little magic repeated, and the room felt steadier.")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    gift = next((e for e in world.entities.values() if e.type == "gift"), None)
    friend = next((e for e in world.entities.values() if e.type == "friend"), None)
    if not (child and gift and friend):
        return out
    if child.memes.get("gypped", 0) < THRESHOLD:
        return out
    if gift.meters.get("shared", 0) >= THRESHOLD:
        return out
    sig = ("share", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gift.meters["shared"] = 1
    child.memes["gypped"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    out.append("They decided to share it, and the hurt feeling eased away.")
    return out


RULES = [Rule("sticky", _r_sticky), Rule("repeat", _r_repeat), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_share(world: World, child: Entity, gift: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["gypped"] = 1
    sim.get(gift.id).meters["shared"] = 0
    propagate(sim, narrate=False)
    return sim.get(child.id).memes.get("gypped", 0) == 0


def tell(setting: Setting, gift_def: Gift, child_name: str, child_type: str, friend_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend"))
    gift = world.add(Entity(id="gift", kind="object", type="gift", label=gift_def.label, phrase=gift_def.phrase, owner=child.id))

    world.say(f"At {setting.place}, the light was {setting.dim}, and everything felt ready for a bedtime wish.")
    world.say(f"{child_name} had never seen {gift_def.phrase} before, and {child.pronoun().capitalize()} loved it at once.")
    world.say(f"{friend_name} smiled and said the little magic could be shared.")

    world.para()
    child.meters["sticky"] = 1 if gift_def.sticky else 0
    if gift_def.repeatable:
        gift.meters["repeat"] = 2
    if not gift_def.shared:
        child.memes["gypped"] = 1
        world.say(f"But when the gift stayed close and would not be passed around, {child_name} felt gypped.")
    else:
        world.say(f"The gift waited in {child_name}'s hands, soft and friendly as a night-light.")

    if gift_def.repeatable:
        propagate(world, narrate=True)

    world.para()
    if child.memes.get("gypped", 0) >= THRESHOLD:
        if predict_share(world, child, gift):
            world.say(f"{friend_name} leaned closer and asked to take a turn.")
            gift.meters["shared"] = 1
            propagate(world, narrate=True)
            world.say(f"Then {child_name} and {friend_name} took turns with the glow, and the room felt cozy again.")
        else:
            world.say(f"{child_name} held the gift a little longer, but the feeling stayed sour.")

    world.facts.update(child=child, friend=friend, gift=gift, gift_def=gift_def, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story about a child in {f["setting"].place} where a {f["gift_def"].label} feels magical, sticky, and can be shared.',
        f"Tell a gentle story in a crunch-dim room where {f['child'].id} feels gypped until {f['friend'].id} helps with sharing.",
        f'Write a short sleepy story that repeats a little magic and ends with the gift being shared.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, gift_def = f["child"], f["friend"], f["gift_def"]
    qa = [
        QAItem(
            question=f"Where did {child.id} first see the {gift_def.label}?",
            answer=f"{child.id} first saw it at {f['setting'].place}, where the light was {f['setting'].dim}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel gypped at first?",
            answer=f"{child.id} felt gypped because the {gift_def.label} stayed close and was not being shared yet.",
        ),
        QAItem(
            question=f"What helped the feeling get better?",
            answer=f"{friend.id} asked to take a turn, and then they shared the {gift_def.label}.",
        ),
    ]
    if f["gift_def"].repeatable:
        qa.append(
            QAItem(
                question=f"What happened when the little magic repeated?",
                answer=f"The magic repeated twice, and the room felt steadier and more cozy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means there is not much light, so things look soft and sleepy instead of bright.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about magic, sharing, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gift = args.gift or rng.choice(list(GIFTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend = args.friend or rng.choice(NAMES_BOY if gender == "girl" else NAMES_GIRL)
    if friend == name:
        friend = (NAMES_BOY if gender == "girl" else NAMES_GIRL)[0]
    return StoryParams(setting=setting, gift=gift, child_name=name, child_type=gender, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], GIFTS[params.gift], params.child_name, params.child_type, params.friend_name)
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
    StoryParams(setting="window", gift="glowstone", child_name="Mina", child_type="girl", friend_name="Finn"),
    StoryParams(setting="hall", gift="sparklejar", child_name="Theo", child_type="boy", friend_name="Lily"),
    StoryParams(setting="garden", gift="moonribbon", child_name="Nora", child_type="girl", friend_name="Ben"),
]


ASP_RULES = r"""
child(C) :- child_name(C).
gift(G) :- gift_name(G).
friend(F) :- friend_name(F).
sticky(G) :- sticky_gift(G).
repeatable(G) :- repeat_gift(G).
shared(G) :- shared_gift(G).

gypped(C,G) :- child(C), gift(G), sticky(G), not shared(G).
better(C,G) :- gypped(C,G), repeatable(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("dim", sid, s.dim))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift_name", gid))
        if g.sticky:
            lines.append(asp.fact("sticky_gift", gid))
        if g.repeatable:
            lines.append(asp.fact("repeat_gift", gid))
        if g.shared:
            lines.append(asp.fact("shared_gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show gypped/2.\n#show better/2."))
    gy = set(asp.atoms(model, "gypped"))
    be = set(asp.atoms(model, "better"))
    py = set()
    for gid, g in GIFTS.items():
        if g.sticky and not g.shared:
            py.add(("anychild", gid))
    if gy or be:
        print("OK: ASP produced a model.")
        return 0
    print("MISMATCH: ASP produced no relevant atoms.")
    return 1


def build_story_for(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show gypped/2.\n#show better/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child_name}: {p.setting} / {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
