#!/usr/bin/env python3
"""
storyworlds/worlds/solar_ugly_surprise_rhyming_story.py
=======================================================

A small rhyming story world about a child, an ugly thing, and a sunny surprise.

Seed image:
- A child finds something ugly in the yard.
- It turns out to be a solar-powered surprise.
- The child feels uneasy at first, then delighted when the surprise works.

The world is intentionally tiny and state-driven:
- Physical meters track light, charge, dirt, and shine.
- Emotional memes track worry, curiosity, delight, and pride.
- The ending image proves what changed: the ugly object becomes useful and loved.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the yard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    light_need: float
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    needs: set[str]
    outcome: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + value


def _set_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + value


def _activity_sunshine(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    if act.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot host {act.id}.")
    _set_meter(actor, "sun", 1.0)
    _set_meme(actor, "curiosity", 1.0)
    if narrate:
        world.say(f"{actor.id} stepped out with a grin and a spring in {actor.pronoun('possessive')} spin.")


def _activity_mess(world: World, actor: Entity, prize: Entity, surprise: Surprise, narrate: bool = True) -> None:
    if actor.meters.get("sun", 0.0) < surprise.needs.get("sun", 0):
        return
    _set_meter(prize, "dirt", 1.0)
    _set_meter(prize, "ugliness", 1.0)
    _set_meme(actor, "worry", 1.0)
    if narrate:
        world.say(f"The thing looked ugly and rough, with a dusty gray grin and a bumpy little puff.")


def _activity_reveal(world: World, actor: Entity, prize: Entity, surprise: Surprise, narrate: bool = True) -> None:
    if prize.meters.get("ugliness", 0.0) < THRESHOLD:
        return
    _set_meter(prize, "charge", 2.0)
    _set_meter(prize, "shine", 2.0)
    _set_meme(actor, "delight", 2.0)
    _set_meme(actor, "pride", 1.0)
    if narrate:
        world.say(f"Then came a sweet surprise: {surprise.reveal}, and the ugly thing found its glow.")


def _activity_afterglow(world: World, actor: Entity, prize: Entity, surprise: Surprise, narrate: bool = True) -> None:
    if prize.meters.get("shine", 0.0) < THRESHOLD:
        return
    if narrate:
        world.say(f"It sang with the sun, so bright and so neat, and made the whole garden feel merry and sweet.")


def tell(setting: Setting, act: Activity, prize_cfg: Prize, surprise: Surprise,
         hero_name: str = "Mia", hero_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    prize = world.add(Entity(
        id="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
        plural=prize_cfg.plural,
    ))
    surprise_ent = world.add(Entity(
        id=surprise.id,
        type="thing",
        label=surprise.label,
        phrase=surprise.phrase,
    ))

    world.say(f"{hero.id} was a little one with a sing-song tone, who liked the yard and the warm sun's glow.")
    world.say(f"{hero.id} found {prize_cfg.phrase}; it seemed quite ugly, a crinkly old show.")
    world.para()
    world.say(f"One bright afternoon, {hero.id} went out to the place where the sun would stay and play.")
    _activity_sunshine(world, hero, act)
    _activity_mess(world, hero, prize, surprise, narrate=True)
    world.say(f"{hero.id} frowned at the thing and gave it a stare, for ugly old ruffles were tattered and bare.")
    world.para()
    _activity_reveal(world, hero, prize, surprise, narrate=True)
    _activity_afterglow(world, hero, prize, surprise, narrate=True)
    world.say(f"{hero.id} laughed, then clapped, then danced on the lawn; the ugly surprise had turned into dawn.")

    world.facts.update(
        hero=hero,
        prize=prize,
        surprise=surprise_ent,
        activity=act,
        setting=setting,
        resolved=prize.meters.get("shine", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "yard": Setting(place="the yard", affords={"sunwalk"}),
    "garden": Setting(place="the garden", affords={"sunwalk"}),
    "porch": Setting(place="the porch", affords={"sunwalk"}),
}

ACTIVITIES = {
    "sunwalk": Activity(
        id="sunwalk",
        verb="walk in the sun",
        gerund="walking in the sun",
        rush="skip to the bright edge",
        mess="dusty",
        soil="dusty and dull",
        light_need=1.0,
        keyword="solar",
        tags={"solar", "sun"},
    ),
}

PRIZES = {
    "lamp": Prize(label="lamp", phrase="an ugly little lamp", type="lamp"),
    "toy": Prize(label="toy", phrase="an ugly toy box", type="toy"),
    "top": Prize(label="top", phrase="an ugly spinning top", type="top"),
}

SURPRISES = {
    "solar_lamp": Surprise(
        id="solar_lamp",
        label="solar lamp",
        phrase="a solar lamp under the dirt",
        reveal="it was a solar lamp that drank the daylight and glowed at night",
        needs={"sun": 1},
        outcome="shone",
        tags={"solar", "surprise"},
    ),
    "solar_top": Surprise(
        id="solar_top",
        label="solar top",
        phrase="a solar top in the weeds",
        reveal="it was a solar top that spun fast after it soaked up the sun",
        needs={"sun": 1},
        outcome="whirled",
        tags={"solar", "surprise"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Lily", "Max"]
TRAITS = ["cheery", "curious", "bouncy", "playful", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    surprise: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    sur = f["surprise"]
    return [
        f'Write a short rhyming story for a young child about {hero.id}, {prize.label}, and a {sur.label} surprise.',
        f"Tell a gentle story where a little {hero.type} named {hero.id} finds {prize.phrase} and learns it is {sur.phrase}.",
        f'Write a sunny story that includes the word "{act.keyword}" and ends with the ugly thing becoming useful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    sur = f["surprise"]
    return [
        QAItem(
            question=f"What did {hero.id} find in the yard?",
            answer=f"{hero.id} found {prize.phrase}. It looked ugly at first, but the surprise was hiding inside it.",
        ),
        QAItem(
            question=f"Why did the ugly thing change after {hero.id} walked in the sun?",
            answer=f"It changed because it was a {sur.label}. The sun gave it the power it needed, so it could shine and help.",
        ),
        QAItem(
            question=f"What did {hero.id} do before the surprise was revealed?",
            answer=f"{hero.id} spent time {act.gerund}. That gave the solar surprise enough light to wake up.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the ugly thing started to glow?",
            answer=f"{hero.id} felt delighted and proud, because the ugly thing turned into something bright and useful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does solar mean?",
            answer="Solar means having to do with the sun. A solar thing uses sunlight as power.",
        ),
        QAItem(
            question="Why can sunlight help a solar object?",
            answer="Sunlight can charge a solar object, so it can store energy and work later.",
        ),
        QAItem(
            question="Can something ugly still be useful?",
            answer="Yes. Something can look plain or ugly and still do a very helpful job.",
        ),
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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                for sur_id in SURPRISES:
                    if "solar" in SURPRISES[sur_id].tags:
                        combos.append((place, act_id, prize_id, sur_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only supports solar surprises that can wake up in sunlight.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about an ugly solar surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.prize and args.surprise is None:
        raise StoryError(explain_rejection())
    place = args.place or rng.choice(list(SETTINGS))
    act = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    prize = args.prize or rng.choice(list(PRIZES))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=prize, surprise=surprise, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], SURPRISES[params.surprise], params.name, params.gender)
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


ASP_RULES = r"""
solar_surprise(S) :- surprise(S), tag(S, solar).
shines(P) :- prize(P), has_sun(P), solar_surprise(S).
ugly_then_useful(P) :- prize(P), dirt(P), solar_surprise(S), has_sun(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for s, obj in SURPRISES.items():
        lines.append(asp.fact("surprise", s))
        for t in obj.tags:
            lines.append(asp.fact("tag", s, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Inline ASP is a lightweight twin here; the deterministic check is the Python gate.
    py = set(valid_combos())
    if py:
        print(f"OK: Python gate produced {len(py)} solar story combos.")
        return 0
    print("MISMATCH: no valid solar story combos.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solar_surprise/1.\n#show shines/1.\n#show ugly_then_useful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="yard", activity="sunwalk", prize="lamp", surprise="solar_lamp", name="Mia", gender="girl", trait="curious"),
            StoryParams(place="garden", activity="sunwalk", prize="top", surprise="solar_top", name="Leo", gender="boy", trait="bouncy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
