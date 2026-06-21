#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pheasant_personnel_transformation_sharing_heartwarming.py
========================================================================================

A standalone story world for a heartwarming tiny tale about personnel at a farm
and a shy pheasant who is transformed by kindness. The world keeps a small,
state-driven simulation with physical meters and emotional memes, a reasonableness
gate, an inline ASP twin, and three Q&A sets.

Premise
-------
A group of personnel at a farm notices a lonely pheasant. One worker gently
shares food, a small shelter, and patient attention. The bird transforms from
afraid to trusting, and the whole yard feels warmer at the end.

This script is self-contained and stdlib-only.
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
CARE_MIN = 2


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    warm: bool = True

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
class Bird:
    id: str
    label: str
    phrase: str
    shy: bool = True
    hungry: bool = True
    can_transform: bool = True

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
class Sharing:
    id: str
    item: str
    phrase: str
    help_text: str
    kindness: int
    warmth: int

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    bird = world.entities.get("pheasant")
    helper = world.entities.get("worker")
    if not bird or not helper:
        return out
    if bird.memes["safe"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("warm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.memes["trust"] += 1
    helper.memes["joy"] += 1
    out.append("__warm__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    bird = world.entities.get("pheasant")
    if not bird:
        return out
    if bird.memes["trust"] < THRESHOLD or bird.meters["fed"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.meters["color_shift"] += 1
    bird.memes["brave"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("warm", "social", _r_warm), Rule("transform", "physical", _r_transform)]


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


def reasonableness_ok(params: "StoryParams") -> bool:
    return params.sharing in SHARINGS and params.bird in BIRDS and params.setting in SETTINGS


def build_nest(world: World, worker: Entity, bird: Entity, setting: Setting) -> None:
    worker.memes["kindness"] += 1
    bird.memes["safe"] += 1
    world.say(
        f"At {setting.place}, the personnel moved quietly so they would not startle the pheasant."
    )
    world.say(
        f"{worker.id} noticed the small bird first, standing alone near the fence with a thin, worried look."
    )


def share_food(world: World, worker: Entity, bird: Entity, sharing: Sharing) -> None:
    bird.meters["fed"] += 1
    worker.meters["shared"] += 1
    world.say(
        f'{worker.id} smiled and shared {sharing.phrase}. "{sharing.help_text}"'
    )
    world.say(
        f"The pheasant pecked at the food, little by little, and the yard grew quieter."
    )


def offer_cover(world: World, worker: Entity, bird: Entity) -> None:
    world.say(
        f"{worker.id} also offered a small sheltered box with dry straw, just enough for a tired bird to rest."
    )
    bird.meters["covered"] += 1


def transform(world: World, bird: Entity, sharing: Sharing) -> None:
    propagate(world, narrate=False)
    if bird.meters["color_shift"] >= THRESHOLD:
        bird.label = "bright pheasant"
        world.say(
            f"By the time the sun lowered, the pheasant stood a little taller, its feathers catching the gold light."
        )
        world.say(
            f"It was still the same bird, but now it looked calm and strong, as if kindness had transformed it from the inside out."
        )


def ending(world: World, worker: Entity, bird: Entity, sharing: Sharing) -> None:
    world.say(
        f"{worker.id} stood back with a gentle grin, happy to have shared enough for the bird to feel welcome."
    )
    world.say(
        f"The personnel finished the day with softer voices, and the pheasant stayed nearby, safe and full."
    )
    world.say(
        f"At last, the little pheasant was no longer alone; it was part of the warm, shared life of the farm."
    )


def tell(setting: Setting, bird_cfg: Bird, sharing: Sharing, worker_name: str = "Mara",
         worker_type: str = "woman", helper_name: str = "Jon", helper_type: str = "man") -> World:
    world = World(setting)
    worker = world.add(Entity(id=worker_name, kind="character", type=worker_type, role="personnel", label="the worker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="personnel", label="the helper"))
    bird = world.add(Entity(id="pheasant", kind="character", type="bird", label=bird_cfg.label, traits=["shy"], attrs={"phrase": bird_cfg.phrase}))
    world.add(Entity(id="feed", type="thing", label="seed", attrs={"kind": "food"}))
    world.add(Entity(id="box", type="thing", label="small shelter"))

    build_nest(world, worker, bird, setting)
    world.para()
    share_food(world, worker, bird, sharing)
    offer_cover(world, worker, bird)
    world.para()
    transform(world, bird, sharing)
    ending(world, worker, bird, sharing)

    world.facts.update(setting=setting, bird=bird, sharing=sharing, worker=worker, helper=helper,
                       transformed=bird.meters["color_shift"] >= THRESHOLD,
                       fed=bird.meters["fed"] >= THRESHOLD)
    return world


SETTINGS = {
    "farm": Setting("farm", "the little farm"),
    "barnyard": Setting("barnyard", "the barnyard"),
    "orchard": Setting("orchard", "the orchard"),
}

BIRDS = {
    "pheasant": Bird("pheasant", "pheasant", "a shy pheasant"),
}

SHARINGS = {
    "seed": Sharing("seed", "seed", "a handful of seed", "There, little one. You can have some too.", kindness=2, warmth=2),
    "corn": Sharing("corn", "corn", "a small bowl of corn", "You do not need to hurry. There is enough to share.", kindness=3, warmth=3),
    "berries": Sharing("berries", "berries", "a plate of berries", "We saved these for anyone who was hungry and lonely.", kindness=3, warmth=2),
}

GIRL_NAMES = ["Mara", "Lina", "Tess", "Nora", "Iris"]
BOY_NAMES = ["Jon", "Evan", "Owen", "Theo", "Sam"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    bird: str
    sharing: str
    worker: str
    worker_type: str
    helper: str
    helper_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for b in BIRDS:
            for sh in SHARINGS:
                combos.append((s, b, sh))
    return combos


def explain_rejection() -> str:
    return "(No story: this tiny world only knows about a pheasant and simple sharing at a farm.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about a pheasant, personnel, transformation, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--sharing", choices=SHARINGS)
    ap.add_argument("--worker")
    ap.add_argument("--helper")
    ap.add_argument("--worker-type", choices=["woman", "man"])
    ap.add_argument("--helper-type", choices=["woman", "man"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bird is None or c[1] == args.bird)
              and (args.sharing is None or c[2] == args.sharing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bird, sharing = rng.choice(sorted(combos))
    worker_type = args.worker_type or rng.choice(["woman", "man"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    worker = args.worker or rng.choice(GIRL_NAMES if worker_type == "woman" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != worker])
    return StoryParams(setting, bird, sharing, worker, worker_type, helper, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words "{f["bird"].label}" and "personnel".',
        f"Tell a gentle story where {f['worker'].id} and the personnel share food with a lonely pheasant and it changes for the better.",
        f"Write a short story about sharing and transformation at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who is the story about?", f"It is about a pheasant and the personnel at {f['setting'].place}. {f['worker'].id} helped the bird feel safe."),
        QAItem("What did the worker share?", f"{f['worker'].id} shared {f['sharing'].phrase}. That gave the hungry pheasant food and comfort."),
        QAItem("What changed about the pheasant?", f"It transformed from shy and worried to calm and brave. The sharing and gentle care helped it trust the people."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pheasant?", "A pheasant is a bird that lives on the ground and can have bright feathers."),
        QAItem("What does sharing mean?", "Sharing means giving some of what you have to someone else so both people can enjoy it."),
        QAItem("Who are personnel?", "Personnel are the people who work at a place, like helpers on a farm or in a building."),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B, Sh) :- setting(S), bird(B), sharing(Sh).
warm_up :- valid(_, _, _).
transform :- warm_up, shared_food, pheasant_trust.
shared_food :- sharing(_).
pheasant_trust :- warm_up.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BIRDS:
        lines.append(asp.fact("bird", b))
    for sh in SHARINGS:
        lines.append(asp.fact("sharing", sh))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        ok = False
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BIRDS[params.bird], SHARINGS[params.sharing],
                 params.worker, params.worker_type, params.helper, params.helper_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, b, sh in asp_valid_combos():
            print(f"  {s:10} {b:10} {sh}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, "pheasant", sh, "Mara", "woman", "Jon", "man")) for s, _, sh in valid_combos()[:3]]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
