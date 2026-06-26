#!/usr/bin/env python3
"""
storyworlds/worlds/syndrome_humor_bedtime_story.py
==================================================

A small bedtime-story world about a child with a funny little syndrome that
makes evenings feel oversized, noisy, or hard to settle. The story stays gentle
and humorous: the child learns a soothing routine, a helper responds kindly,
and the bedtime turn ends with the syndrome calmed enough for sleep.

The simulated world tracks:
- physical meters: tiredness, silliness, restlessness, comfort, noise
- emotional memes: worry, delight, trust, calm, pride

This world is intentionally small and constraint-driven. It only generates
stories when the syndrome, setting, and bedtime helper create a plausible,
child-facing turn and resolution.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Syndrome:
    id: str
    label: str
    funny_effect: str
    bedtime_trouble: str
    remedy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    night_detail: str
    affords: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    syndrome: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting(
        place="the nursery",
        night_detail="The lamp glowed softly beside the tiny bed, and the moon made silver squares on the floor.",
        affords={"gentle_routine", "story_time"},
    ),
    "bedroom": Setting(
        place="the bedroom",
        night_detail="The blanket was fluffy, and the window held a shy round moon.",
        affords={"gentle_routine", "story_time"},
    ),
    "attic_room": Setting(
        place="the attic room",
        night_detail="The room was warm and quiet, with the ceiling slanting like a sleepy hat.",
        affords={"gentle_routine", "story_time"},
    ),
}

SYNDROMES = {
    "giggle_syndrome": Syndrome(
        id="giggle_syndrome",
        label="Giggle Syndrome",
        funny_effect="made little laughs pop out at the wrong moments",
        bedtime_trouble="kept the child wiggling and chuckling when the eyes wanted to close",
        remedy="slow breaths, a blanket tuck, and one silly bedtime rhyme",
        tags={"humor", "giggle", "bedtime"},
    ),
    "moonbounce_syndrome": Syndrome(
        id="moonbounce_syndrome",
        label="Moonbounce Syndrome",
        funny_effect="made the feet feel like tiny trampolines",
        bedtime_trouble="turned the bed into a bouncy place instead of a sleepy place",
        remedy="pillow presses, a warm drink, and counting five soft stars",
        tags={"humor", "bounce", "bedtime"},
    ),
    "whisper_snicker_syndrome": Syndrome(
        id="whisper_snicker_syndrome",
        label="Whisper-Snicker Syndrome",
        funny_effect="made every serious whisper come out like a tiny snicker",
        bedtime_trouble="kept the room full of almost-laughs",
        remedy="quiet story time, a hand on the chest, and a promise to be still for one minute",
        tags={"humor", "whisper", "bedtime"},
    ),
}

HERO_NAMES = ["Milo", "Nina", "Tess", "Owen", "Luna", "Poppy", "Ben", "Ivy"]
HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandmother": "grandmother",
    "grandfather": "grandfather",
}
TRAITS = ["tiny", "gentle", "bright-eyed", "curious", "cheerful", "sleepy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_name, setting in SETTINGS.items():
        if "gentle_routine" not in setting.affords:
            continue
        for syndrome_name in SYNDROMES:
            combos.append((setting_name, syndrome_name))
    return combos


def reasonableness_gate(setting_name: str, syndrome_name: str) -> None:
    if setting_name not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting_name}")
    if syndrome_name not in SYNDROMES:
        raise StoryError(f"Unknown syndrome: {syndrome_name}")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    syndrome = SYNDROMES[params.syndrome]

    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={}, memes={}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=f"the {params.helper_type}", meters={}, memes={}))

    hero.meters.update(tiredness=1.0, silliness=0.0, restlessness=0.0, comfort=0.0, noise=0.0)
    hero.memes.update(worry=0.5, delight=0.0, trust=0.0, calm=0.0, pride=0.0)
    helper.meters.update(softness=1.0, patience=1.0)
    helper.memes.update(kindness=1.0, humor=0.6)

    world.facts.update(hero=hero, helper=helper, syndrome=syndrome, setting=setting)
    return world


def apply_syndrome(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    syndrome: Syndrome = world.facts["syndrome"]
    sig = ("syndrome", syndrome.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)

    hero.meters["silliness"] += 1.0
    hero.meters["restlessness"] += 0.8
    hero.meters["noise"] += 0.5
    hero.memes["worry"] += 0.3
    return [
        f"At bedtime, {hero.id} had {syndrome.label}.",
        f"It {syndrome.funny_effect}, and that {syndrome.bedtime_trouble}.",
    ]


def apply_laughter_softening(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    syndrome: Syndrome = world.facts["syndrome"]
    sig = ("soften", syndrome.id)
    if sig in world.fired:
        return []
    if hero.meters["silliness"] < THRESHOLD:
        return []
    world.fired.add(sig)
    hero.memes["delight"] += 0.4
    helper.memes["humor"] += 0.1
    return [
        f"{helper.label.capitalize()} did not scold. Instead, {helper.label} smiled at the giggles like they were tiny bells.",
    ]


def apply_routine(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    syndrome: Syndrome = world.facts["syndrome"]
    sig = ("routine", syndrome.id)
    if sig in world.fired:
        return []
    if hero.meters["restlessness"] < THRESHOLD:
        return []
    world.fired.add(sig)

    hero.meters["comfort"] += 1.0
    hero.meters["restlessness"] -= 0.4
    hero.meters["noise"] -= 0.2
    hero.memes["trust"] += 0.8
    helper.memes["kindness"] += 0.2
    return [
        f"{helper.label.capitalize()} tucked the blanket under {hero.id}'s chin, then showed {hero.id} one slow breath and one silly bedtime rhyme.",
        f"The room grew quieter, because the {syndrome.remedy} worked like a soft little bridge to sleep.",
    ]


def apply_sleep_turn(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    sig = ("sleep", hero.id)
    if sig in world.fired:
        return []
    if hero.meters["comfort"] < THRESHOLD:
        return []
    world.fired.add(sig)
    hero.meters["tiredness"] += 0.2
    hero.memes["calm"] += 1.0
    hero.memes["pride"] += 0.5
    hero.meters["restlessness"] = 0.0
    hero.meters["noise"] = max(0.0, hero.meters["noise"] - 0.5)
    return [f"At last, {hero.id}'s eyes grew heavy, and the bed became the sleepiest boat in the whole house."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for fn in (apply_syndrome, apply_laughter_softening, apply_routine, apply_sleep_turn):
        bits = fn(world)
        out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    syndrome: Syndrome = world.facts["syndrome"]

    world.say(f"{hero.id} was a {params.hero_type} with {syndrome.label}.")
    world.say(f"{hero.id} was {random.choice(TRAITS)} and a little {params.hero_name.lower()}-sized bundle of bedtime trouble.")
    world.say(world.setting.night_detail)
    world.para()
    world.say(f"{hero.id} wanted to sleep, but {syndrome.label} kept the room full of funny little wiggles.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"{helper.label.capitalize()} sang a quiet rhyme and said, “We can let the giggles visit, but we do not have to follow them all night.”")
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.2)
    hero.memes["calm"] += 0.4
    world.say(f"{hero.id} tucked the last laugh into a yawn, hugged {helper.label}, and let the blanket do the rest.")
    world.facts.update(resolved=hero.memes["calm"] >= 1.0)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    syndrome: Syndrome = world.facts["syndrome"]
    helper: Entity = world.facts["helper"]
    setting: Setting = world.facts["setting"]
    return [
        f'Write a gentle bedtime story for a young child about {hero.id} and {syndrome.label} in {setting.place}.',
        f"Tell a humorous bedtime story where {helper.label} helps {hero.id} settle down when {syndrome.label} makes the night too wiggly.",
        f'Create a small story with the word "syndrome" that ends with sleep, comfort, and a funny but kind solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    syndrome: Syndrome = world.facts["syndrome"]
    setting: Setting = world.facts["setting"]
    return [
        QAItem(
            question=f"What was {hero.id}'s bedtime problem in {setting.place}?",
            answer=f"{hero.id} had {syndrome.label}, which made bedtime funny, wiggly, and a little hard to settle.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.id} feel calmer?",
            answer=f"{helper.label.capitalize()} used a gentle routine with a blanket tuck, a slow breath, and a silly rhyme.",
        ),
        QAItem(
            question=f"What changed by the end of the story for {hero.id}?",
            answer=f"By the end, {hero.id} was calm, cuddled under the blanket, and ready to fall asleep.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    syndrome: Syndrome = world.facts["syndrome"]
    return [
        QAItem(
            question="What is a syndrome?",
            answer="In this storyworld, a syndrome is a named pattern that changes how bedtime feels or behaves.",
        ),
        QAItem(
            question=f"Why can {syndrome.label} be funny?",
            answer=f"It can be funny because it makes little bedtime actions happen in a silly way, like giggles, wiggles, or almost-laughs.",
        ),
        QAItem(
            question="What helps a child settle down at bedtime?",
            answer="A calm routine, a soft blanket, a quiet voice, and a kind helper can make bedtime feel safe and sleepy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous bedtime storyworld with a syndrome and a gentle resolution.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--syndrome", choices=sorted(SYNDROMES))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=sorted(HELPERS))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    syndrome = args.syndrome or rng.choice(sorted(SYNDROMES))
    reasonableness_gate(setting, syndrome)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(setting=setting, syndrome=syndrome, hero_name=name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
setting(nursery).
setting(bedroom).
setting(attic_room).

syndrome(giggle_syndrome).
syndrome(moonbounce_syndrome).
syndrome(whisper_snicker_syndrome).

compatible(S, Y) :- setting(S), syndrome(Y).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for y in SYNDROMES:
        lines.append(asp.fact("syndrome", y))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: ASP matches python reasonableness gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(python_set - clingo_set))
    print(" only in ASP:", sorted(clingo_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid()
        print(f"{len(pairs)} compatible setting/syndrome pairs:")
        for s, y in pairs:
            print(f"  {s:10} {y}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for y in SYNDROMES:
                p = StoryParams(setting=s, syndrome=y, hero_name="Milo", hero_type="boy", helper_type="mother")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
