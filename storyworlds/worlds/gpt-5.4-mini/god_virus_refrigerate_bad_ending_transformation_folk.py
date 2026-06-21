#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/god_virus_refrigerate_bad_ending_transformation_folk.py
========================================================================================

A standalone storyworld in a folk-tale style.

Premise:
- A village receives a sealed charm-jar that holds a sleeping virus.
- The village god or wise guardian says it must be refrigerated in the ice chest.
- A curious child or helper opens it instead of refrigerating it.
- The virus transforms something living into something cold, pale, and changed.
- The ending is bad: the transformation is permanent, and the village learns too late.

The world is small on purpose: fewer plausible variants, stronger causal shape.
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
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "man", "god"}
        female = {"girl", "mother", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Creature:
    id: str
    label: str
    form: str
    safe_cold: bool
    spreads: bool = True
    transforms: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Guardian:
    id: str
    label: str
    label_phrase: str
    warning: str
    safe_action: str
    protect_text: str
    sense: int = 3
    power: int = 3
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    village: str
    creature: str
    guardian: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["virus"] < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in list(world.entities.values()):
            if other.kind == "character":
                other.memes["fear"] += 1
        out.append("__spread__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("transformed"):
        return out
    if world.facts.get("released") and world.facts.get("not_refrigerated"):
        sig = ("transform",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        target = world.get("target")
        target.meters["changed"] += 1
        target.meters["cold"] += 1
        world.facts["transformed"] = True
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("spread", _r_spread),
    Rule("transform", _r_transform),
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


def natural_guardians() -> list[Guardian]:
    return list(GUARDIANS.values())


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for village in VILLAGES:
        for creature in CREATURES:
            for guardian in GUARDIANS:
                combos.append((village, creature, guardian))
    return combos


def reasonableness_gate(creature: Creature, guardian: Guardian) -> bool:
    return guardian.sense >= SENSE_MIN and creature.spreads and creature.transforms


def explain_rejection(creature: Creature, guardian: Guardian) -> str:
    if guardian.sense < SENSE_MIN:
        return f"(No story: {guardian.label_phrase} is too weak-minded for a folk warning.)"
    if not creature.spreads:
        return f"(No story: {creature.label} would not spread, so there is no danger, no turn, and no ending.)"
    if not creature.transforms:
        return f"(No story: {creature.label} would not transform anything, so the folk-tale beat has nothing to do.)"
    return "(No story: this combination is not reasonable.)"


def _touch(world: World, target: Entity, creature: Creature) -> None:
    target.meters["virus"] += 1
    world.facts["released"] = True
    propagate(world, narrate=False)


def predict(world: World, creature: Creature) -> dict:
    sim = world.copy()
    _touch(sim, sim.get("target"), creature)
    return {
        "spread": any(e.memes["fear"] >= THRESHOLD for e in sim.entities.values() if e.kind == "character"),
        "transformed": sim.facts.get("transformed", False),
    }


def intro(world: World, hero: Entity, helper: Entity, village: str, guardian: Guardian, creature: Creature) -> None:
    world.say(
        f"In {village}, {hero.id} and {helper.id} heard the old tale of a sealed jar "
        f"that held a sleeping {creature.label}. At the temple gate, {guardian.label_phrase} "
        f"spoke in a calm voice: {guardian.warning}"
    )


def temptation(world: World, hero: Entity, creature: Creature, target: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"But {hero.id} peered at the jar and thought the answer was close at hand. "
        f'"Maybe I can handle it myself," {hero.id} said, looking at the {target.label}.'
    )
    world.say("The air felt still, as if the village were holding its breath.")


def warn(world: World, helper: Entity, guardian: Guardian, target: Entity) -> None:
    pred = predict(world, CREATURES[world.facts["creature"]])
    helper.memes["caution"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'{helper.id} bit {helper.pronoun("possessive")} lip. "{guardian.warning} '
        f"It must be refrigerated, or it may wake and change things."
    )


def defy(world: World, hero: Entity, creature: Creature, guardian: Guardian) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {hero.id} did not listen. "The cold box can wait," {hero.id} said, '
        f"and lifted the lid instead of putting the jar away."
    )
    world.facts["not_refrigerated"] = True


def release(world: World, hero: Entity, target: Entity, creature: Creature) -> None:
    _touch(world, target, creature)
    world.say(
        f"The jar cracked open with a wet hiss. A pale cloud rose out, and the {creature.label} "
        f"slipped into the room like breath on a winter window."
    )
    world.say(f"{hero.id} cried out too late.")


def bad_end(world: World, hero: Entity, helper: Entity, target: Entity, creature: Creature) -> None:
    world.say(
        f"The {creature.label} crawled over the {target.label} and left it changed forever. "
        f"By dawn, the {target.label} was cold, white, and still, as if the village had been "
        f"turned into a story told in winter."
    )
    world.say(
        f"{hero.id} and {helper.id} stood silent, and even {world.get('god').id} could not take the change back."
    )
    world.say(
        "So the people learned the hard way that some things must be kept cold, sealed, and watched."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    god = world.add(Entity(id="god", kind="character", type="god", role="guardian", label="the god"))
    target = world.add(Entity(id="target", type="thing", label="refrigerator chest"))
    world.facts["village"] = params.village
    world.facts["creature"] = params.creature
    world.facts["guardian"] = params.guardian

    intro(world, hero, helper, params.village, GUARDIANS[params.guardian], CREATURES[params.creature])
    world.para()
    temptation(world, hero, CREATURES[params.creature], target)
    warn(world, helper, GUARDIANS[params.guardian], target)
    defy(world, hero, CREATURES[params.creature], GUARDIANS[params.guardian])
    world.para()
    release(world, hero, target, CREATURES[params.creature])
    bad_end(world, hero, helper, target, CREATURES[params.creature])

    world.facts.update(
        hero=hero, helper=helper, god=god, target=target,
        outcome="bad", transformed=True, released=True, not_refrigerated=True
    )
    return world


VILLAGES = {
    "pine_village": "the pine village",
    "river_village": "the river village",
    "hill_village": "the hill village",
}

CREATURES = {
    "virus": Creature("virus", "virus", "sleeping spore", True, tags={"virus", "transform"}),
    "winter_virus": Creature("winter_virus", "virus", "frost-mist", True, tags={"virus", "refrigerate"}),
}

GUARDIANS = {
    "god": Guardian(
        "god",
        "god",
        "the god of the hill shrine",
        "Keep the jar in the ice chest and do not open it",
        "refrigerate it at once",
        "Only the cold box can hold a sleeping virus",
        sense=3,
        power=3,
        tags={"god", "refrigerate"},
    ),
    "elder": Guardian(
        "elder",
        "elder",
        "the village elder",
        "Keep it cold and sealed",
        "refrigerate it at once",
        "Only the cold box can hold a sleeping virus",
        sense=3,
        power=2,
        tags={"refrigerate"},
    ),
}

NAMES = {
    "boy": ["Milo", "Jorin", "Pek", "Taro"],
    "girl": ["Nina", "Sela", "Mira", "Lina"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: god, virus, refrigerate, transformation, bad ending.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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
    if args.creature and args.guardian:
        if not reasonableness_gate(CREATURES[args.creature], GUARDIANS[args.guardian]):
            raise StoryError(explain_rejection(CREATURES[args.creature], GUARDIANS[args.guardian]))
    combos = [c for c in valid_combos()
              if (args.village is None or c[0] == args.village)
              and (args.creature is None or c[1] == args.creature)
              and (args.guardian is None or c[2] == args.guardian)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    village, creature, guardian = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES[gender])
    helper_gender = args.helper_gender or ("girl" if gender == "boy" else "boy")
    helper = args.helper or rng.choice(NAMES[helper_gender])
    return StoryParams(village, creature, guardian, name, gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale that includes the words "god", "virus", and "refrigerate".',
        f"Tell a short village story where {f['hero'].id} is warned by a god to refrigerate a dangerous virus, but the warning is ignored.",
        "Write a bad-ending transformation story in a folk-tale voice, where the cold choice is missed and something living is changed forever.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    qa = [
        QAItem(
            question="Who was warned about the jar?",
            answer=f"{hero.id} was warned, and {helper.id} tried to help. The warning came from the god at the shrine."
        ),
        QAItem(
            question="What should they have done with the virus?",
            answer="They should have refrigerated it right away and kept the jar sealed. The cold was the only safe place for it."
        ),
        QAItem(
            question="Why is this a bad ending?",
            answer="Because the jar was opened instead of being refrigerated, the virus escaped and caused a lasting transformation. The village could not undo the change."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            QAItem(
                question="What changed after the virus got loose?",
                answer="The target became cold, pale, and changed forever. That transformation showed the virus had already done its worst."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does refrigerate mean?",
            answer="To refrigerate something means to keep it cold in a special box or chill place. Cold can slow down or protect some things from spoiling or waking up."
        ),
        QAItem(
            question="Why can a virus be dangerous?",
            answer="A virus can spread and make living things sick or changed. If it gets loose, it can affect more than one person or thing."
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that feels like it was passed from one person to another. It often has a wise warning, a magical feeling, and a clear lesson."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(V, C, G) :- village(V), creature(C), guardian(G).
bad_end(C) :- creature(C), spreads(C), transforms(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VILLAGES:
        lines.append(asp.fact("village", v))
    for c, creature in CREATURES.items():
        lines.append(asp.fact("creature", c))
        if creature.spreads:
            lines.append(asp.fact("spreads", c))
        if creature.transforms:
            lines.append(asp.fact("transforms", c))
    for g in GUARDIANS:
        lines.append(asp.fact("guardian", g))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if rc == 0:
        print("OK: ASP/Python parity verified.")
    return rc


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show bad_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(v, c, g, rng_name, "boy", helper, "girl")) for v, c, g in valid_combos()[:3] for rng_name, helper in [("Milo", "Nina")]]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
