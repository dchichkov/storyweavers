#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caustic_sun_smash_surprise_myth.py
===================================================================

A small mythic storyworld about a village, a harsh sun, a caustic desert pool,
a surprising helper, and a broken stone seal that must be smashed to save the
day. The story is built from simulated state: thirst, heat, damage, trust, and
a turn where an unexpected gift changes the outcome.

The world keeps the required twin structure:
- Python reasonableness gate over valid combinations
- inline ASP_RULES mirror
- generated facts via asp_facts()

The prose aims for a child-facing myth style: concrete, simple, and complete.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HEAT_LIMIT = 2.0
SURPRISE_GAIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "daughter"}
        male = {"boy", "father", "man", "king", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    caustic: bool
    near_sun: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    smashable: bool
    holds_water: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    gift: str
    method: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hazard: str
    relic: str
    surprise: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    sun = world.get("sun")
    if sun.meters["blaze"] < THRESHOLD:
        return out
    sig = ("heat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.role in {"hero", "helper"}:
            ent.memes["unease"] += 1
            ent.meters["thirst"] += 1
    out.append("__heat__")
    return out


def _r_caustic(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.get("hazard")
    if hazard.meters["exposed"] < THRESHOLD or not hazard.attrs.get("caustic"):
        return out
    sig = ("caustic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.role in {"hero", "helper"}:
            ent.meters["sting"] += 1
    out.append("__sting__")
    return out


def _r_smash(world: World) -> list[str]:
    relic = world.get("relic")
    if relic.meters["cracked"] < THRESHOLD:
        return []
    sig = ("smash",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relic.meters["broken"] += 1
    return ["__smash__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    rules = [Rule("heat", _r_heat), Rule("caustic", _r_caustic), Rule("smash", _r_smash)]
    while changed:
        changed = False
        for rule in rules:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for hz_id, hz in HAZARDS.items():
            for relic_id, relic in RELICS.items():
                if not hz.caustic or not hz.near_sun:
                    continue
                if not relic.smashable or not relic.holds_water:
                    continue
                if place_id not in place.tags:
                    continue
                combos.append((place_id, hz_id, relic_id))
    return combos


def reasonableness_gate(place: Place, hazard: Hazard, relic: Relic) -> bool:
    return place.id in place.tags and hazard.caustic and hazard.near_sun and relic.smashable and relic.holds_water


def choose_surprise(world: World, helper: Entity, surprise: Surprise) -> None:
    helper.memes["hope"] += 1
    helper.meters["gift"] += 1
    world.get("relic").meters["ready"] += 1
    world.say(
        f"Then, as if the sky had been listening, {helper.id} found a {surprise.label}. "
        f"It was no ordinary gift; it came {surprise.gift}."
    )
    world.say(
        f"{helper.id} knew the old way: {surprise.method}. The surprise gave them enough strength to do it."
    )


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    sun = world.add(Entity(id="sun", kind="thing", type="sun", label="the sun"))
    hazard = world.add(Entity(id="hazard", kind="thing", type="hazard", label=HAZARDS[params.hazard].label,
                              attrs={"caustic": HAZARDS[params.hazard].caustic}, tags=set(HAZARDS[params.hazard].tags)))
    relic = world.add(Entity(id="relic", kind="thing", type="relic", label=RELICS[params.relic].label,
                             attrs={"smashable": RELICS[params.relic].smashable, "holds_water": RELICS[params.relic].holds_water},
                             tags=set(RELICS[params.relic].tags)))
    surprise = SURPRISES[params.surprise]

    sun.meters["blaze"] = 1.0
    hazard.meters["exposed"] = 1.0
    relic.meters["sealed"] = 1.0
    hero.memes["dread"] = 1.0
    helper.memes["faith"] = 1.0

    world.say(
        f"Long ago, in {world.place.label}, {hero.id} and {helper.id} went beneath {world.place.scene}. "
        f"Above them burned {sun.label_word}, and below them waited {hazard.label}."
    )
    world.say(
        f"The old people of the valley said the {hazard.label} was caustic, sharp as a bad word. "
        f"It bit the air and made brave faces feel small."
    )
    world.say(
        f"At the end of the path stood {relic.label}, a sealed thing from the first age, made to be smashed only when the right sign arrived."
    )
    world.para()
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} stared at the seal and whispered, \"We must break it before the sun grows fiercer.\""
    )
    world.say(
        f"But {helper.id} held up a hand. \"Wait,\" {helper.pronoun()} said. \"Look at the stone. Look at the sky.\""
    )
    choose_surprise(world, helper, surprise)
    world.para()
    if surprise.power >= 2:
        relic.meters["crack"] += 1
        relic.meters["cracked"] += 1
        hero.memes["surprise"] += 1
        helper.memes["surprise"] += 1
        propagate(world, narrate=False)
        world.say(
            f"With the gift at their backs, {hero.id} lifted the hammer-stone and smashed the seal."
        )
        world.say(
            f"The stone split with a sound like thunder, and from inside poured cool water, clear as moonlight."
        )
        world.say(
            f"The caustic pool hissed and sank away under the fresh water, and the valley breathed again."
        )
        world.para()
        world.say(
            f"Then the people of the valley came running. They were not angry. They were astonished."
        )
        world.say(
            f"They called the day a surprise from the gods, for the smallest gift had saved the oldest place."
        )
        outcome = "saved"
    else:
        relic.meters["crack"] += 1
        world.say(
            f"{hero.id} struck the seal, but the old stone only shivered. The hidden water would not come."
        )
        world.say(
            f"So they covered the relic with cloth and retreated before the caustic heat could sting them too hard."
        )
        outcome = "failed"

    world.facts.update(
        hero=hero,
        helper=helper,
        sun=sun,
        hazard=hazard,
        relic=relic,
        surprise=surprise,
        outcome=outcome,
        place=world.place,
    )
    return world


PLACES = {
    "desert": Place(id="desert", label="the desert shrine", scene="the sun-cracked steps", tags={"desert"}),
    "ruins": Place(id="ruins", label="the old ruins", scene="broken arches and sand", tags={"ruins"}),
}

HAZARDS = {
    "pool": Hazard(id="pool", label="the caustic pool", phrase="a caustic pool", caustic=True, near_sun=True, tags={"caustic", "sun"}),
    "brine": Hazard(id="brine", label="the caustic brine", phrase="caustic brine", caustic=True, near_sun=True, tags={"caustic", "sun"}),
}

RELICS = {
    "seal": Relic(id="seal", label="the stone seal", phrase="a stone seal", smashable=True, holds_water=True, tags={"smash"}),
    "door": Relic(id="door", label="the sealed door", phrase="a sealed door", smashable=True, holds_water=True, tags={"smash"}),
}

SURPRISES = {
    "owl": Surprise(id="owl", label="white owl", gift="from the reeds", method="smash the seal with all their strength", power=2, tags={"surprise"}),
    "child": Surprise(id="child", label="small child", gift="carrying a hidden hammer", method="smash the seal with the hammer", power=3, tags={"surprise"}),
}

GIRLS = ["Mira", "Nia", "Sera", "Lina", "Asha"]
BOYS = ["Kian", "Taro", "Ravi", "Ilan", "Darin"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a young child that includes the words "{f["hazard"].label}" and "sun", and ends with a surprise.',
        f"Tell a short myth where {f['hero'].id} must smash a stone seal near {f['hazard'].label}, and a surprising helper changes the ending.",
        f'Write a simple legend with the word "caustic" and a brave smash that brings water back to the shrine.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, hazard, relic, surprise = f["hero"], f["helper"], f["hazard"], f["relic"], f["surprise"]
    qa = [
        ("Who are the story about?",
         f"It is about {hero.id} and {helper.id}, two travelers in {f['place'].label}. They faced a caustic danger under the hot sun."),
        ("What was dangerous in the story?",
         f"The dangerous thing was {hazard.label}. It was caustic, so it could sting and spoil the dry air around the shrine."),
        ("What needed to be smashed?",
         f"They needed to smash {relic.label}. The seal held the hidden water inside the old stone."),
        ("What was the surprise?",
         f"The surprise was {surprise.label}. {helper.id} found the unexpected help, and that gave them the courage to smash the seal at the right moment."),
    ]
    if f["outcome"] == "saved":
        qa.append((
            "How did the story end?",
            f"It ended with water pouring out and the caustic pool shrinking away. The valley was saved, and the people called it a gift from the gods."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with the seal still shut, so the travelers had to back away. They survived, but the rescue had not yet come."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["hazard"].tags) | set(world.facts["relic"].tags) | set(world.facts["surprise"].tags)
    out = []
    if "caustic" in tags:
        out.append(("What does caustic mean?",
                    "Caustic means something can sting, burn, or eat at other things. It is a harsh kind of danger."))
    if "sun" in tags:
        out.append(("Why can the sun feel dangerous in a desert?",
                    "The sun can make the ground very hot and dry. In a desert, that heat can make travel hard and tiring."))
    if "smash" in tags:
        out.append(("What does smash mean?",
                    "To smash something means to hit it hard so it breaks. People should only do that when it is safe and needed."))
    if "surprise" in tags:
        out.append(("What is a surprise?",
                    "A surprise is something you did not expect. It can be a gift, a helper, or a change that makes a hard day better."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
caustic(H) :- hazard(H), caustic_tag(H).
sunny(H) :- hazard(H), sun_tag(H).
smashable(R) :- relic(R), smash_tag(R).
valid(P,H,R,S) :- place(P), hazard(H), relic(R), surprise(S), caustic(H), sunny(H), smashable(R), holds_water(R).
outcome(saved) :- surprise_power(3).
outcome(saved) :- surprise_power(2).
outcome(failed) :- surprise_power(1).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", h))
        if hz.caustic:
            lines.append(asp.fact("caustic_tag", h))
        if hz.near_sun:
            lines.append(asp.fact("sun_tag", h))
    for r, rel in RELICS.items():
        lines.append(asp.fact("relic", r))
        if rel.smashable:
            lines.append(asp.fact("smash_tag", r))
        if rel.holds_water:
            lines.append(asp.fact("holds_water", r))
    for s, sp in SURPRISES.items():
        lines.append(asp.fact("surprise", s))
        lines.append(asp.fact("surprise_power", sp.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    py = set((p, h, r) for p, h, r in valid_combos())
    cl = set((p, h, r) for p, h, r, _ in valid_story_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, hazard=None, relic=None, surprise=None, hero=None, hero_type=None, helper=None, helper_type=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as ex:
        print(f"FAIL: generation smoke test crashed: {ex}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic sun, caustic pool, smash, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, relic = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRLS if hero_type == "girl" else BOYS)
    helper = args.helper or rng.choice([n for n in (BOYS if helper_type == "boy" else GIRLS) if n != hero])
    return StoryParams(place=place, hazard=hazard, relic=relic, surprise=surprise,
                       hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.relic not in RELICS or params.surprise not in SURPRISES:
        raise StoryError("Invalid parameter key.")
    place = PLACES[params.place]
    world = World(place)
    world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    world.add(Entity(id="sun", kind="thing", type="sun", label="the sun"))
    world.add(Entity(id="hazard", kind="thing", type="hazard", label=HAZARDS[params.hazard].label,
                     attrs={"caustic": True}, tags=set(HAZARDS[params.hazard].tags)))
    world.add(Entity(id="relic", kind="thing", type="relic", label=RELICS[params.relic].label,
                     attrs={"smashable": True, "holds_water": True}, tags=set(RELICS[params.relic].tags)))
    world.add(Entity(id="surprise", kind="thing", type="surprise", label=SURPRISES[params.surprise].label))
    sample_world = tell(world, params)
    return StorySample(
        params=params,
        story=sample_world.render(),
        prompts=generation_prompts(sample_world),
        story_qa=[QAItem(q, a) for q, a in story_qa(sample_world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(sample_world)],
        world=sample_world,
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
    StoryParams(place="desert", hazard="pool", relic="seal", surprise="owl", hero="Mira", hero_type="girl", helper="Kian", helper_type="boy"),
    StoryParams(place="ruins", hazard="brine", relic="door", surprise="child", hero="Ravi", hero_type="boy", helper="Sera", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_story_combos()
        print(f"{len(combos)} compatible stories:\n")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
