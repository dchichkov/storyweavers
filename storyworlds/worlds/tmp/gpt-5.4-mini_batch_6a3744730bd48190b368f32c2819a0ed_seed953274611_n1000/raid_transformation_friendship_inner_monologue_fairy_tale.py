#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/raid_transformation_friendship_inner_monologue_fairy_tale.py
=============================================================================================

A tiny fairy-tale storyworld about a midnight raid, a worrying inner monologue,
and a friendship that changes a frightened creature into a brave helper.

Premise
-------
A small castle keeps a moon-silver cake for the village feast. A greedy raider
tries to steal it at night. A shy friend thinks aloud, remembers a promise, and
finds a surprising transformation: fear turns into courage, and an enchanted
creature becomes a loyal ally.

The world is built as a classical simulation with typed entities, physical
meters, and emotional memes. Story text is rendered from state changes, not
from a frozen template. The story always includes the word "raid".

CLI
---
    python storyworlds/worlds/gpt-5.4-mini/raid_transformation_friendship_inner_monologue_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/raid_transformation_friendship_inner_monologue_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/raid_transformation_friendship_inner_monologue_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/raid_transformation_friendship_inner_monologue_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    transformed: bool = False

    def __post_init__(self):
        if not self.meters:
            self.meters = {"hunger": 0.0, "danger": 0.0, "gold": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "love": 0.0, "bravery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": {"female": "she", "male": "he", "neutral": "they"},
            "object": {"female": "her", "male": "him", "neutral": "them"},
            "possessive": {"female": "her", "male": "his", "neutral": "their"},
        }
        gender = self.attrs.get("gender", "neutral")
        return mapping[case][gender]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    castle: str
    raider: str
    friend: str
    transformed: str
    gift: str
    seed: Optional[int] = None


@dataclass
class Setting:
    castle: str
    hall: str
    treasure: str
    moonlight: str
    sound: str


@dataclass
class Raider:
    id: str
    label: str
    greed: int
    speed: int


@dataclass
class Friend:
    id: str
    label: str
    gender: str
    traits: list[str] = field(default_factory=list)
    timid: bool = True


@dataclass
class Transformation:
    id: str
    before: str
    after: str
    title_before: str
    title_after: str
    condition: str
    label: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_danger(world: World) -> list[str]:
    out = []
    raider = world.get("raider")
    chest = world.get("chest")
    if raider.meters["gold"] >= THRESHOLD and chest.meters["danger"] < THRESHOLD:
        chest.meters["danger"] = 1.0
        out.append("The raid made the moon-silver chest tremble.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    friend = world.get("friend")
    if friend.memes["hope"] >= THRESHOLD and not friend.transformed:
        friend.memes["bravery"] += 1
        out.append("__bravery__")
    return out


CAUSAL_RULES = [Rule("danger", _r_danger), Rule("bravery", _r_bravery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def tell(world: World, setting: Setting, raider: Raider, friend: Friend,
         trans: Transformation, gift: Gift) -> World:
    castle = world.add(Entity(id="castle", kind="place", type="castle", label=setting.castle,
                              meters={"hunger": 0.0, "danger": 0.0, "gold": 0.0},
                              memes={"fear": 0.0, "hope": 0.0, "love": 0.0, "bravery": 0.0}))
    chest = world.add(Entity(id="chest", kind="thing", type="chest", label=setting.treasure,
                             meters={"hunger": 0.0, "danger": 0.0, "gold": 1.0},
                             memes={"fear": 0.0, "hope": 0.0, "love": 0.0, "bravery": 0.0}))
    ra = world.add(Entity(id="raider", kind="character", type="cat", label=raider.label,
                          role="raider", attrs={"gender": "male"}))
    fr = world.add(Entity(id="friend", kind="character", type="sprite", label=friend.label,
                          role="friend", traits=friend.traits, attrs={"gender": friend.gender}))
    frog = world.add(Entity(id="frog", kind="character", type="frog", label=trans.before,
                            role="enchanted", attrs={"gender": "neutral"}))

    world.say(
        f"Under the pale moon, {setting.castle} slept quietly, and {setting.treasure} "
        f"waited in the hall. Even the air listened, because {setting.sound} was all around."
    )
    world.say(
        f"Then a greedy {raider.label} came on a raid and tiptoed toward the treasure."
    )
    ra.meters["gold"] += 1
    friend.memes["fear"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{friend.label} hid behind a pillar and thought, 'If I run, the cake is gone. "
        f"If I speak, my voice may shake.'"
    )

    world.para()
    world.say(
        f"But {friend.label} remembered a promise: {trans.condition}. "
        f"{friend.label} whispered, 'I am small, but I am not alone.'"
    )
    if friend.memes["hope"] >= THRESHOLD:
        frog.transformed = True
        frog.type = trans.after
        frog.label = trans.label
        friend.memes["bravery"] += 1
        friend.memes["fear"] = 0.0
        world.say(
            f"At once, the little enchanted frog changed. Its green skin shone like a "
            f"new leaf, and it became {trans.title_after} {trans.after}."
        )
        world.say(
            f"The new {trans.after} hopped beside {friend.label}, and together they blocked "
            f"the raider's path."
        )
    propagate(world, narrate=True)

    world.para()
    if chest.meters["danger"] >= THRESHOLD:
        ra.meters["gold"] = 0.0
        world.say(
            f"The raider dropped the stolen bite of gold and fled into the dark reeds. "
            f"{gift.label} stayed safe, and the hall grew quiet again."
        )
    else:
        world.say(
            f"The raider was so startled by the sudden friendship that he turned away "
            f"without taking anything at all."
        )

    world.para()
    world.say(
        f"{friend.label} smiled at the transformed helper and held up {gift.phrase}. "
        f"The moonlit hall no longer felt lonely; it felt like a place where friendship "
        f"could change a frightened heart."
    )

    world.facts.update(
        setting=setting,
        raider=raider,
        friend=friend,
        transformation=trans,
        gift=gift,
        chest=chest,
        outcoming_friend=world.get("frog"),
        raid=True,
        transformed=world.get("frog").transformed,
    )
    return world


SETTINGS = {
    "castle": Setting(
        castle="the old ivy castle",
        hall="the great hall",
        treasure="a moon-silver cake",
        moonlight="silver moonbeams",
        sound="the owls' hush",
    ),
    "tower": Setting(
        castle="the little stone tower",
        hall="the winding stair",
        treasure="a honey cake",
        moonlight="pale moonlight",
        sound="the wind's whisper",
    ),
    "garden": Setting(
        castle="the rose garden wall",
        hall="the lantern path",
        treasure="a star-shaped tart",
        moonlight="soft moonbeams",
        sound="the crickets' song",
    ),
}

RAIDERS = {
    "cat": Raider(id="cat", label="black cat thief", greed=3, speed=3),
    "fox": Raider(id="fox", label="red fox raider", greed=4, speed=4),
    "goblin": Raider(id="goblin", label="tiny goblin raider", greed=5, speed=2),
}

FRIENDS = {
    "mouse": Friend(id="mouse", label="a little mouse", gender="neutral", traits=["shy", "kind"], timid=True),
    "bird": Friend(id="bird", label="a bluebird", gender="female", traits=["gentle", "hopeful"], timid=True),
    "page": Friend(id="page", label="a castle page", gender="male", traits=["earnest", "dreamy"], timid=True),
}

TRANSFORMATIONS = {
    "frog_to_knight": Transformation(
        id="frog_to_knight",
        before="frog",
        after="knight",
        title_before="a tiny",
        title_after="a brave",
        condition="the friend dared to speak kindly",
        label="a frog in silver armor",
    ),
    "moth_to_owl": Transformation(
        id="moth_to_owl",
        before="moth",
        after="owl",
        title_before="a soft",
        title_after="a wise",
        condition="the friend chose courage over fear",
        label="an owl with bright eyes",
    ),
}

GIFTS = {
    "ribbon": Gift(id="ribbon", label="a red ribbon", phrase="a red ribbon", glow="like a little flame"),
    "bell": Gift(id="bell", label="a silver bell", phrase="a silver bell", glow="with a bright ring"),
}

CURATED = [
    StoryParams(castle="castle", raider="cat", friend="mouse", transformed="frog_to_knight", gift="ribbon"),
    StoryParams(castle="tower", raider="fox", friend="bird", transformed="moth_to_owl", gift="bell"),
]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RAIDERS:
            for f in FRIENDS:
                for t in TRANSFORMATIONS:
                    for g in GIFTS:
                        combos.append((s, r, f, t, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale raid with friendship and transformation.")
    ap.add_argument("--castle", choices=SETTINGS)
    ap.add_argument("--raider", choices=RAIDERS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--gift", choices=GIFTS)
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
    combos = [c for c in valid_combos()
              if (args.castle is None or c[0] == args.castle)
              and (args.raider is None or c[1] == args.raider)
              and (args.friend is None or c[2] == args.friend)
              and (args.transformation is None or c[3] == args.transformation)
              and (args.gift is None or c[4] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    c = rng.choice(sorted(combos))
    return StoryParams(castle=c[0], raider=c[1], friend=c[2], transformed=c[3], gift=c[4])


def generate(params: StoryParams) -> StorySample:
    for k in ("castle", "raider", "friend", "transformed", "gift"):
        if not hasattr(params, k):
            raise StoryError(f"Invalid StoryParams: missing {k}")
    world = World(SETTINGS[params.castle])
    story_world = tell(world, SETTINGS[params.castle], RAIDERS[params.raider],
                       FRIENDS[params.friend], TRANSFORMATIONS[params.transformed],
                       GIFTS[params.gift])
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(story_world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(story_world)],
        world=story_world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a raid on {f["setting"].treasure} in {f["setting"].castle}, '
        f"where a shy friend finds courage and a transformation happens.",
        f"Tell a story in which {f['friend'].label} thinks aloud, saves the feast, and "
        f"{f['transformation'].condition}.",
        f'Write a child-friendly tale using the word "raid" and ending with friendship '
        f"changing the night into something safe and bright.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    friend = f["friend"].label
    trans = f["transformation"]
    return [
        ("What happened in the castle?",
         f"A raid began when the greedy thief tried to steal {f['setting'].treasure}. "
         f"The moonlit hall became tense because something precious was in danger."),
        ("What was the friend thinking?",
         f"{friend} thought that running away would let the thief win, but speaking up felt "
         f"scary too. In the end, that careful thinking led to courage."),
        ("What changed during the story?",
         f"The enchanted {trans.before} transformed into {trans.after}, and fear changed into "
         f"bravery. Friendship made the change possible, so the friend was not alone anymore."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a raid?",
         "A raid is a sudden taking or attack, usually done quickly in the night. In a fairy tale, it often means someone tries to steal something precious."),
        ("What does transformation mean?",
         "Transformation means a change from one form or state into another. In stories, it can be a magical change or a change in courage."),
        ("What is friendship?",
         "Friendship is when people help, care for, and trust one another. Good friends make hard moments feel less frightening."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} transformed={e.transformed}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,R,F,T,G) :- castle(C), raider(R), friend(F), transformation(T), gift(G).
transformed(F) :- friend(F), hopeful(F).
raid_happens(R) :- raider(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in SETTINGS:
        lines.append(asp.fact("castle", c))
    for r in RAIDERS:
        lines.append(asp.fact("raider", r))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
        if "hopeful" in FRIENDS[f].traits:
            lines.append(asp.fact("hopeful", f))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0 if a == b else 1
    print("OK: ASP matches Python." if rc == 0 else "MISMATCH: ASP differs from Python.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
