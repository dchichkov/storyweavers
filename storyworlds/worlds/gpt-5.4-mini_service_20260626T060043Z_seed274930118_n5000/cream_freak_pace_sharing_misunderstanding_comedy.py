#!/usr/bin/env python3
"""
A standalone story world: cream, freak, pace, sharing, and a comic misunderstanding.

A tiny child-facing comedy premise:
- One character has something tasty or fancy, like cream.
- Another character gets the wrong idea and freaks out.
- Someone slows down or changes pace to make sharing work.
- The misunderstanding turns into a laugh and a kind ending.

The world model tracks physical "meters" and emotional "memes" so prose is driven
by simulated state rather than a frozen template.
"""

from __future__ import annotations

import argparse
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    pace: str
    affords_sharing: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    taste: str
    shareable: bool = True


@dataclass
class StoryParams:
    setting: str
    item: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    pace: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _pulse_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    item = world.entities.get("item")
    if not hero or not friend or not item:
        return out
    if hero.memes.get("sharing", 0.0) < THRESHOLD:
        return out
    if friend.memes.get("misunderstood", 0.0) < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["freakout"] = max(0.0, friend.memes.get("freakout", 0.0) - 1.0)
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    item.meters["shared"] = item.meters.get("shared", 0.0) + 1.0
    out.append("They shared it, and the whole mix-up melted into laughter.")
    return out


def _slow_pace(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("rush", 0.0) < THRESHOLD:
        return out
    sig = ("pace",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["pace"] = hero.memes.get("pace", 0.0) + 1.0
    out.append(f"{hero.pronoun().capitalize()} slowed down and took a gentler pace.")
    return out


CAUSAL_RULES = [_slow_pace, _pulse_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend))
    item = world.add(Entity(
        id="item",
        type=ITEMS[params.item].type,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, friend=friend, item=item, item_cfg=ITEMS[params.item])

    hero.memes["love"] = 1.0
    hero.memes["sharing"] = 1.0
    hero.memes["rush"] = 1.0 if params.pace == "fast" else 0.0
    friend.memes["curious"] = 1.0

    world.say(
        f"{hero.label} loved their {item.label}, especially the creamy kind that made snack time feel fancy."
    )
    world.say(
        f"At {setting.place}, {hero.label} and {friend.label} were moving at a {setting.pace} pace."
    )
    world.para()
    world.say(
        f"{friend.label} saw the cream and freaked out for a second, thinking it meant a big mess was coming."
    )
    friend.memes["misunderstood"] = 1.0
    friend.memes["freakout"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then {hero.label} laughed, explained the cream was for sharing, and offered some with a spoon."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"In the end, they sat together at a calmer pace, smiling over the same little treat."
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", pace="careful"),
    "cafe": Setting(place="the café", pace="busy"),
    "picnic": Setting(place="the picnic blanket", pace="easy"),
    "garden": Setting(place="the garden table", pace="slow"),
}

ITEMS = {
    "cream": Item(id="cream", label="cream", phrase="a swirl of cream", type="cream", taste="sweet"),
    "whipped_cream": Item(id="whipped_cream", label="whipped cream", phrase="a fluffy cloud of cream", type="cream", taste="sweet"),
    "cream_puff": Item(id="cream_puff", label="cream puff", phrase="a cream puff", type="treat", taste="sweet"),
}

HERO_NAMES = ["Maya", "Lulu", "Nina", "Ben", "Toby", "Ella", "Milo", "Zoe"]
FRIEND_NAMES = ["Pip", "Rae", "Ollie", "June", "Sam", "Ivy", "Nico", "Dot"]
TYPES = {"girl": "girl", "boy": "boy", "neutral": "child"}
PACE_CHOICES = ["fast", "slow", "careful", "easy", "busy"]

KNOWLEDGE = {
    "cream": [
        ("What is cream?", "Cream is the thick, soft part of milk that is often used in food and desserts."),
        ("Why is cream fun to share?", "Cream can be fun to share because a little spoonful can make a treat feel special for more than one person."),
    ],
    "pace": [
        ("What does pace mean?", "Pace means how fast or slow someone moves or does something."),
    ],
    "sharing": [
        ("What is sharing?", "Sharing means letting another person use or enjoy something with you."),
    ],
    "misunderstanding": [
        ("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong idea about what is going on."),
    ],
    "freak": [
        ("What does it mean to freak out?", "To freak out means to feel very surprised, scared, or upset all at once."),
    ],
    "comedy": [
        ("What makes a story funny?", "A story can be funny when someone gets the wrong idea and then everyone laughs after they understand."),
    ],
}


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("pace_mode", sid, s.pace))
        if s.affords_sharing:
            lines.append(asp.fact("affords_sharing", sid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_label", iid, it.label))
        lines.append(asp.fact("item_taste", iid, it.taste))
        if it.shareable:
            lines.append(asp.fact("shareable", iid))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(S) :- shareable(I), setting(S), affords_sharing(S), item(I).
freaks_out(F) :- misunderstanding(S), setting(S), friend(F).
needs_slower_pace(S) :- misunderstanding(S), pace_mode(S, fast).
good_story(S, I) :- setting(S), item(I), shareable(I), affords_sharing(S).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            combos.append((s, i))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic story world about cream, freakouts, pace, sharing, and misunderstandings.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "neutral"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy", "neutral"])
    ap.add_argument("--pace", choices=PACE_CHOICES)
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
    item = args.item or rng.choice(list(ITEMS))
    hero_type = args.hero_type or rng.choice(["girl", "boy", "neutral"])
    friend_type = args.friend_type or rng.choice(["girl", "boy", "neutral"])
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    pace = args.pace or SETTINGS[setting].pace
    if args.item and not ITEMS[item].shareable:
        raise StoryError("Chosen item is not shareable enough for this world.")
    return StoryParams(setting=setting, item=item, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type, pace=pace)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child about cream, sharing, and a misunderstanding at {world.setting.place}.',
        f"Tell a funny story where {f['hero'].label} shares {f['item_cfg'].label} and {f['friend'].label} freaks out before understanding.",
        "Write a gentle funny story that uses the words cream, freak, pace, sharing, and misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    item_cfg = f["item_cfg"]
    return [
        QAItem(
            question=f"What was the story about at {world.setting.place}?",
            answer=f"It was about {hero.label}, {friend.label}, and a creamy treat that got shared after a misunderstanding.",
        ),
        QAItem(
            question=f"Why did {friend.label} freak out at first?",
            answer=f"{friend.label} got the wrong idea and thought the cream meant a big mess, so they freaked out before realizing it was for sharing.",
        ),
        QAItem(
            question=f"What changed when everyone slowed to a gentler pace?",
            answer=f"When {hero.label} slowed down and kept a gentler pace, {friend.label} could understand the joke and join in the sharing.",
        ),
        QAItem(
            question=f"What did {hero.label} offer at the end?",
            answer=f"{hero.label} offered {item_cfg.phrase} so they could share it together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    topics = ["cream", "pace", "sharing", "misunderstanding", "freak", "comedy"]
    out = []
    for t in topics:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[t])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


CURATED = [
    StoryParams(setting="kitchen", item="cream", hero="Maya", hero_type="girl", friend="Pip", friend_type="neutral", pace="fast"),
    StoryParams(setting="cafe", item="whipped_cream", hero="Ben", hero_type="boy", friend="Rae", friend_type="girl", pace="busy"),
    StoryParams(setting="picnic", item="cream_puff", hero="Lulu", hero_type="girl", friend="Ollie", friend_type="boy", pace="easy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.hero}: {p.setting} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
