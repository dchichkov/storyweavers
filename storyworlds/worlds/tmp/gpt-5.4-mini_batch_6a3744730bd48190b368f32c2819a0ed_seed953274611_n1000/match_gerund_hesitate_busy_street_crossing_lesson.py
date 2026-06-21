#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/match_gerund_hesitate_busy_street_crossing_lesson.py
====================================================================================

A tiny storyworld set at a busy street crossing, built from the seed words
"match-gerund" and "hesitate" with lesson-learned and sound-effects flavor.

Premise
-------
A child wants to cross a loud, crowded street to reach a glowing place, but a
small unsafe flame idea tempts them to hurry. Another child or a guide notices
the danger, hesitates at the curb, and teaches a safer way: wait, listen, and
cross together when the road is clear.

The world model tracks:
- physical meters: traffic, smoke, safety, distance, flame, signal
- emotional memes: excitement, hesitation, fear, relief, lesson

The prose is rendered from simulated state, not from a fixed paragraph template.
The stories lean mythic in tone: a curb becomes a gate, a crossing becomes a
trial, and the lesson feels like a small blessing learned under bright signs and
rumbling wheels.

This file is standalone and uses only stdlib plus the shared result containers.
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
LESSON_MIN = 1.0
TRAFFIC_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class StoryParams:
    crossing: str
    flame_word: str
    sound_word: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    lesson_style: str
    seed: Optional[int] = None
    chance: int = 0
    speed: int = 0
    lesson_done: bool = False
    smoke: bool = False


@dataclass
class Crossing:
    id: str
    label: str
    sign: str
    curb: str
    signal: str
    sound: str
    myth_name: str


@dataclass
class Flame:
    id: str
    label: str
    gerund: str
    phrase: str
    sound: str
    risky: bool = True


@dataclass
class GuideRule:
    id: str
    sense: int
    power: int
    text: str
    lesson: str
    sound: str


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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    road = world.get("road")
    for ent in world.entities.values():
        if ent.meters["flame"] < THRESHOLD:
            continue
        sig = ("smoke", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        road.meters["danger"] += 1
        world.get("hero").memes["fear"] += 1
        out.append("__smoke__")
    return out


def _r_hesitation(world: World) -> list[str]:
    hero = world.get("hero")
    curb = world.get("curb")
    if hero.memes["hesitation"] >= THRESHOLD and curb.meters["traffic"] >= TRAFFIC_MIN:
        sig = ("hesitation",)
        if sig not in world.fired:
            world.fired.add(sig)
            curb.meters["pause"] += 1
    return []


CAUSAL_RULES = [Rule("smoke", "physical", _r_smoke), Rule("hesitation", "social", _r_hesitation)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def reasonableness_gate(crossing: Crossing, flame: Flame, chance: int) -> bool:
    return crossing.signal and flame.risky and chance >= 0


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid in CROSINGS:
        for fid in FLAMES:
            combos.append((cid, fid))
    return combos


def predict_danger(world: World, flame_id: str) -> dict:
    sim = world.copy()
    ignite(sim, sim.get(flame_id), narrate=False)
    return {"danger": sim.get("road").meters["danger"], "smoke": sim.get("hero").memes["fear"]}


def ignite(world: World, flame_ent: Entity, narrate: bool = True) -> None:
    flame_ent.meters["flame"] += 1
    flame_ent.meters["spark"] += 1
    world.get("road").meters["danger"] += 1
    world.get("hero").memes["alarm"] += 1
    if narrate:
        world.say(f"{flame_ent.label} flickered with a {flame_ent.attrs.get('sound', 'faint crackle')}.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic busy-crossing storyworld with lesson learned and sound effects.")
    ap.add_argument("--crossing", choices=CROSINGS)
    ap.add_argument("--flame", choices=FLAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crossing and args.crossing not in CROSINGS:
        raise StoryError("Unknown crossing.")
    if args.flame and args.flame not in FLAMES:
        raise StoryError("Unknown flame.")
    crossing = args.crossing or rng.choice(list(CROSINGS))
    flame = args.flame or rng.choice(list(FLAMES))
    return StoryParams(
        crossing=crossing,
        flame_word=FLAMES[flame].gerund,
        sound_word=FLAMES[flame].sound,
        hero=rng.choice(HERO_NAMES),
        hero_gender=rng.choice(["girl", "boy"]),
        guide=rng.choice(GUIDE_NAMES),
        guide_gender=rng.choice(["woman", "man"]),
        lesson_style="myth",
        chance=rng.randint(0, 2),
        speed=rng.randint(0, 2),
        lesson_done=False,
        smoke=False,
    )


def tell(params: StoryParams) -> World:
    world = World()
    crossing = CROSINGS[params.crossing]
    flame = FLAMES[next(k for k, v in FLAMES.items() if v.gerund == params.flame_word)]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero, role="walker"))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_gender, label=params.guide, role="teacher"))
    road = world.add(Entity(id="road", type="place", label="the road"))
    curb = world.add(Entity(id="curb", type="place", label=crossing.curb))
    road.meters["traffic"] = 3
    curb.meters["traffic"] = 3
    hero.memes["hesitation"] = 1
    hero.memes["curiosity"] = 1
    world.say(f"At {crossing.label}, where {crossing.sign} glowed like a small star, {hero.label} came to the curb.")
    world.say(f"The city roared: {crossing.sound}. {hero.label} wanted to cross, but {guide.label} could see the road was alive with wheels.")
    world.para()
    world.say(f"{hero.label} glanced at {flame.gerund} on a nearby lantern and almost reached for it.")
    world.say(f'“Wait,” said {guide.label}. “{params.flame_word} is a bad helper here.”')
    hero.memes["hesitation"] += 1
    predict = predict_danger(world, flame.id)
    world.facts["pred"] = predict
    if predict["danger"] >= 1:
        world.say(f"The guide heard the warning in the wind: {flame.sound}.")
    if hero.memes["hesitation"] >= THRESHOLD:
        world.say(f"{hero.label} hesitated, and the pause was wiser than speed.")
    world.para()
    if params.chance == 0:
        world.say(f"Together they waited for the signal. When the light changed, they crossed one step at a time.")
        world.say(f"The road answered with a final {crossing.sound}, then settled.")
        world.say(f"At the far side, {hero.label} bowed to the guide and learned the lesson: {crossing.myth_name} rewards patience.")
        hero.memes["lesson"] += 1
    else:
        ignite(world, world.add(Entity(id="flame", type="thing", label="the flame", attrs={"sound": flame.sound})))
        world.say(f"{hero.label} stumbled back at the {flame.sound}! The guide pulled them away from the edge.")
        world.say(f"They did not cross until the traffic quieted, and the lesson stayed: haste near the road invites trouble.")
        hero.memes["lesson"] += 1
        world.get("road").meters["danger"] = 0
    world.facts.update(hero=hero, guide=guide, crossing=crossing, flame=flame, lesson=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic child story set at a busy street crossing that uses the words "{f["flame"].gerund}" and "hesitate".',
        f"Tell a story where {f['hero'].label} and {f['guide'].label} stand at a crowded crossing, hear sound effects, and learn a lesson about waiting.",
        f'Write a short myth with a street crossing, a dangerous flame idea, and a calm lesson learned at the curb.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    crossing = f["crossing"]
    return [
        QAItem(question="Where did the story happen?", answer=f"It happened at {crossing.label}, a busy street crossing with lights and a noisy road. That is where the choice to wait became important."),
        QAItem(question="Why did the hero hesitate?", answer=f"{hero.label} hesitated because the road was full of traffic and the guide warned that rushing could be dangerous. The pause helped them choose the safer path."),
        QAItem(question="What lesson did they learn?", answer=f'They learned to wait for the signal and cross carefully instead of hurrying with a flame or a bad idea. The curb became a lesson about patience and safety.'),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What should people do at a busy crossing?", answer="People should wait for the signal, look both ways, and cross carefully. That keeps them safer around moving cars."),
        QAItem(question="Why can a flame be dangerous near traffic?", answer="A flame can distract someone and make them rush or lose focus. Near a road, that can lead to danger because cars and bikes move fast."),
    ]


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    parts.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(parts)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("crossing", cid) for cid in CROSINGS]
    lines += [asp.fact("flame", fid) for fid in FLAMES]
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,F) :- crossing(C), flame(F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(crossing=None, flame=None), random.Random(0)))
        _ = sample.story
        print("OK: smoke-tested story generation.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def _pick(seed_rng: random.Random) -> tuple[str, str]:
    return seed_rng.choice(HERO_NAMES), seed_rng.choice(GUIDE_NAMES)


def generate(params: StoryParams) -> StorySample:
    if params.crossing not in CROSINGS:
        raise StoryError("Unknown crossing.")
    if params.flame_word not in {v.gerund for v in FLAMES.values()}:
        raise StoryError("Unknown flame word.")
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


CROSINGS = {
    "market": Crossing(id="market", label="the market crossing", sign="the lantern-sign", curb="the curb by the baker's shop", signal="the bright walk-light", sound="honk-hush, hum-hum", myth_name="the Gate of Waiting"),
    "school": Crossing(id="school", label="the school crossing", sign="the painted bell", curb="the curb by the old elm", signal="the crossing light", sound="brake-brake, step-step", myth_name="the Gate of Lessons"),
}

FLAMES = {
    "match": Flame(id="match", label="a match", gerund="match-gerund", phrase="a tiny flame", sound="fssht", risky=True),
    "candle": Flame(id="candle", label="a candle", gerund="candle-wavering", phrase="a little golden light", sound="whoof", risky=True),
}

HERO_NAMES = ["Mira", "Ari", "Niko", "Lena", "Tavi"]
GUIDE_NAMES = ["Grandma", "Uncle", "Aunt", "Old Watcher", "Road-Keeper"]


def valid_combos() -> list[tuple[str, str]]:
    return [(c, f) for c in CROSINGS for f in FLAMES]


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    crossing = args.crossing or rng.choice(list(CROSINGS))
    flame = args.flame or rng.choice(list(FLAMES))
    hero, guide = _pick(rng)
    return StoryParams(
        crossing=crossing,
        flame_word=FLAMES[flame].gerund,
        sound_word=FLAMES[flame].sound,
        hero=hero,
        hero_gender=rng.choice(["girl", "boy"]),
        guide=guide,
        guide_gender=rng.choice(["woman", "man"]),
        lesson_style="myth",
        chance=rng.randint(0, 1),
        speed=rng.randint(0, 2),
        lesson_done=False,
        smoke=False,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_from_args(args, rng)


def build_parser_final() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for c, f in asp_valid_combos():
            print(c, f)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for c in CROSINGS:
            for f in FLAMES:
                params = StoryParams(
                    crossing=c,
                    flame_word=FLAMES[f].gerund,
                    sound_word=FLAMES[f].sound,
                    hero="Mira",
                    hero_gender="girl",
                    guide="Grandma",
                    guide_gender="woman",
                    lesson_style="myth",
                    chance=0,
                    speed=0,
                    lesson_done=False,
                    smoke=False,
                )
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
