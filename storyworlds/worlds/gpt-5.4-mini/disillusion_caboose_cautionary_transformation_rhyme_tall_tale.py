#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disillusion_caboose_cautionary_transformation_rhyme_tall_tale.py
=================================================================================================

A standalone storyworld for a tall-tale, cautionary, rhyming tale about a child
who is dazzled by a caboose, gets disillusioned, and transforms from boastful to
thoughtful after a safe, grounded lesson.

Premise
-------
A child thinks the caboose is a glamorous place full of sparkle and status.
A wiser companion warns that the caboose is only the last car, and that chasing
or climbing a moving train is dangerous. The child sees the truth, grows humble,
and helps turn the caboose into a practical, cozy helper-car instead.

This world keeps the simulation small:
- typed entities with physical meters and emotional memes
- a forward-chained causal rule engine
- a reasonableness gate
- three QA sets grounded in the world state
- an inline ASP twin for parity checks

The prose style aims for a tall-tale rhythm: concrete, a little boastful, then
careful, then transformed into a safer ending image.
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
class Setting:
    id: str
    place: str
    mood: str
    vantage: str


@dataclass
class Caboose:
    id: str
    label: str
    sparkle: str
    purpose: str
    transform: str
    warning: str
    safe_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    danger: str
    trigger: str
    avoid: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_disillusion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["boast"] < THRESHOLD:
        return out
    sig = ("disillusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["disillusion"] += 1
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    out.append("__disillusion__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    caboose = world.get("caboose")
    if hero.memes["lesson"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    caboose.meters["helpful"] += 1
    hero.memes["humility"] += 1
    hero.memes["helpfulness"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("disillusion", "social", _r_disillusion),
    Rule("transform", "social", _r_transform),
]


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


def sensible() -> bool:
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HAZARDS:
            combos.append((s, h))
    return combos


@dataclass
class StoryParams:
    setting: str
    hazard: str
    name: str
    friend: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "station": Setting("station", "the station platform", "busy and bright", "down the tracks"),
    "village": Setting("village", "the village yard", "dusty and wide", "over the hill"),
    "river": Setting("river", "the river bend", "windy and loud", "beside the bridge"),
}

CABOOSEES = {
    "caboose": Caboose(
        "caboose",
        "the caboose",
        "red as a cherry and shiny as a spoon",
        "the last car on the train",
        "turned from a boast into a helpful home",
        "A caboose may look grand, but it is not a playground and never a toy.",
        "a lantern car with warm benches and a little map shelf",
        tags={"caboose", "train", "transformation"},
    ),
    "boxcar": Caboose(
        "boxcar",
        "the boxcar",
        "square and steady with plain brown boards",
        "the cargo car behind the engine",
        "turned from a box of brag into a hardworking store",
        "A moving boxcar is not for climbing or chasing.",
        "a supply car with tools and blankets",
        tags={"boxcar", "train"},
    ),
}

HAZARDS = {
    "chase": Hazard("chase", "chasing the train", "You can slip if you run beside moving wheels.", "run after the caboose", "keep both feet on the platform", tags={"danger", "train"}),
    "climb": Hazard("climb", "climbing up the car", "A moving car can jerk and toss you down.", "climb the ladder", "wait for the train to stop", tags={"danger", "train"}),
}

NAMES = ["Milo", "Lena", "Pip", "Nora", "Otis", "June"]
FRIENDS = ["Bea", "Hank", "Tess", "Ollie", "Ruth", "Ezra"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "proud", "careful", "bold", "dreamy"]


def reasonableness_gate(caboose: Caboose, hazard: Hazard) -> bool:
    return caboose.id == "caboose" and hazard.id in {"chase", "climb"}


def explain_rejection(caboose: Caboose, hazard: Hazard) -> str:
    return (
        f"(No story: this world needs the caboose and a real danger together. "
        f"{caboose.label.capitalize()} with {hazard.label} is a valid tall-tale warning, "
        f"but other pairings are too thin to tell.)"
    )


def setting_line(setting: Setting, caboose: Caboose) -> str:
    return (
        f"It was {setting.mood} at {setting.place}, and the old train stood there like a long black snake with a red tail. "
        f"The {caboose.label} looked {caboose.sparkle}, {setting.vantage}."
    )


def tell(setting: Setting, caboose: Caboose, hazard: Hazard, hero: Entity, friend: Entity, parent: Entity) -> World:
    world = World()
    world.add(hero)
    world.add(friend)
    world.add(parent)
    caboose_ent = world.add(Entity(id="caboose", kind="thing", type="traincar", label=caboose.label))
    hero.memes["pride"] = 1.0
    hero.memes["boast"] = 1.0
    friend.memes["caution"] = 1.0

    world.say(
        f"{hero.id} was a tall-tale talker who could brag so big the barn cats blinked twice."
    )
    world.say(
        f"{friend.id} was the kind of friend who kept {friend.pronoun('possessive')} eyes open and {friend.pronoun('possessive')} feet slow."
    )
    world.say(setting_line(setting, caboose))
    world.say(
        f'"Look at that {caboose.label}!" {hero.id} cried. "It must be a grand gold room with ruby rugs and a kingly broom."'
    )
    world.say(
        f'"Nonsense," said {friend.id}. "{caboose.warning}"'
    )
    world.para()
    world.say(
        f"But {hero.id} leaned close, all starry-eyed and swagger-bright, and wanted to {hazard.trigger}."
    )
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "{hazard.avoid.capitalize()}," {friend.id} said. "{caboose.safe_use} is the safer view."'
    )
    if hero.type == "boy":
        hero.memes["defiance"] += 1
    else:
        hero.memes["defiance"] += 1

    world.say(
        f"Then the whistle blew, and the truth came tripping along: the {caboose.label} was not a throne at all, but the train's helper tail."
    )
    hero.memes["disillusion"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id}'s grin shrank to a chip, then softened into a nod. The shiny dream was gone, and the sensible truth was shown."
    )
    world.para()
    caboose_ent.meters["helpful"] += 1
    hero.memes["humility"] += 1
    hero.memes["helpfulness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came along and said, \"A caboose is not for fooling around; it is for carrying a lantern, a map, and a kind word.\""
    )
    world.say(
        f"So {hero.id} climbed down, helped {friend.id} polish the rail sign, and watched the {caboose.label} transform from a boastful box into a cozy helper car."
    )
    world.say(
        f"By sunset, the train sat still and neat, the caboose glowing like a little red barn at the end of the line."
    )
    world.facts.update(
        setting=setting,
        caboose=caboose,
        hazard=hazard,
        hero=hero,
        friend=friend,
        parent=parent,
        transformed=True,
        disillusioned=True,
        helpful=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale cautionary story that includes the words "disillusion" and "caboose" and ends with a safe transformation.',
        f"Tell a rhyming cautionary story where {f['hero'].id} thinks the {f['caboose'].label} is glamorous, but learns the truth and changes their tune.",
        f"Write a child-friendly tall tale about a train caboose, a warning, and a surprising transformation from boastful to humble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    caboose = f["caboose"]
    hazard = f["hazard"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Why was {hero.id} disillusioned?",
            answer=(
                f"{hero.id} was disillusioned because the caboose was not the glamorous place they imagined. "
                f"It turned out to be the last car on the train, and the friend and parent explained the truth."
            ),
        ),
        QAItem(
            question=f"What did {friend.id} warn about?",
            answer=(
                f"{friend.id} warned that {hazard.label} was dangerous and that moving train cars were not for climbing or chasing. "
                f"The warning kept the story from becoming a risky game."
            ),
        ),
        QAItem(
            question=f"What changed about the caboose at the end?",
            answer=(
                f"The caboose changed from a boastful dream into a helpful car. "
                f"It became a cozy helper-car with useful things aboard, which proved the transformation."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} change?",
            answer=(
                f"{hero.id} stopped bragging so much and grew more humble. "
                f"By the end, {hero.id} was helping instead of boasting, which shows the transformation clearly."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caboose?",
            answer=(
                "A caboose is the last car on a train. In old stories it often carries tools, lamps, or a helper's supplies."
            ),
        ),
        QAItem(
            question="Why is it unsafe to chase a moving train?",
            answer=(
                "A moving train can be hard to keep up with, and wheels and steps can be dangerous. "
                "Staying back keeps a child from slipping or getting hurt."
            ),
        ),
        QAItem(
            question="What does disillusion mean?",
            answer=(
                "Disillusion means learning that something is not as magical or wonderful as you thought. "
                "The guess fades, and the truth shows up."
            ),
        ),
        QAItem(
            question="What is a transformation?",
            answer=(
                "A transformation is a big change from one state to another. "
                "In stories it can mean a person, place, or thing becomes different in an important way."
            ),
        ),
    ]


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    lines.append(asp.fact("caboose", "caboose"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, H) :- setting(S), hazard(H), caboose("caboose").
outcome(disillusioned) :- valid(S, H).
outcome(transformed) :- outcome(disillusioned).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome() -> set[str]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    return {a for (a,) in asp.atoms(model, "outcome")}


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))

    # smoke test normal generation
    try:
        sample = generate(resolve_params(argparse.Namespace(seed=None), random.Random(7)))
        assert sample.story.strip()
        assert sample.prompts and sample.story_qa and sample.world_qa
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print("MISMATCH: generation smoke test failed:", exc)

    # verify story generation is stable for curated params
    try:
        for p in CURATED:
            s = generate(p)
            assert "caboose" in s.story.lower()
        print("OK: curated generation passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print("MISMATCH: curated generation failed:", exc)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale caboose storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.hazard and args.hazard not in HAZARDS:
        raise StoryError("(No story: unknown hazard.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    if not reasonableness_gate(CABOOSEES["caboose"], HAZARDS[hazard]):
        raise StoryError(explain_rejection(CABOOSEES["caboose"], HAZARDS[hazard]))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting=setting, hazard=hazard, name=name, friend=friend, parent=parent)


def generate(params: StoryParams) -> StorySample:
    hero = Entity(id=params.name, kind="character", type="boy", role="hero", traits=["tall-tale", "braggy"])
    friend = Entity(id=params.friend, kind="character", type="girl", role="friend", traits=["cautious"])
    parent = Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent")
    world = tell(SETTINGS[params.setting], CABOOSEES["caboose"], HAZARDS[params.hazard], hero, friend, parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("station", "climb", "Milo", "Bea", "mother"),
    StoryParams("village", "chase", "Lena", "Hank", "father"),
]


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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, h in combos:
            print(f"  {s:10} {h}")
        print(f"outcomes: {sorted(asp_outcome())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.hazard}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
