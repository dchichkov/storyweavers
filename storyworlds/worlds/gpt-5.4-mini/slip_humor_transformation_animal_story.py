#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slip_humor_transformation_animal_story.py
=========================================================================

A standalone storyworld for a tiny animal tale about a comical slip that leads
to a gentle transformation.

Domain:
- A small animal character tries to perform a simple trick.
- A slippery spot causes a funny tumble.
- A kind helper responds with a clever, low-stakes fix.
- The mishap turns into a positive transformation: the character changes outfit,
  look, or role in a way that makes the ending feel earned and visible.

The world keeps state in physical meters and emotional memes, uses a Python
reasonableness gate plus an inline ASP twin, and exposes the standard
storyworld CLI.
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
        if self.type in {"cat", "dog", "rabbit", "fox", "bear", "pig", "mouse", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    surface: str
    affordance: str
    mood: str

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
class Animal:
    id: str
    species: str
    label: str
    plural: bool = False
    can_slip: bool = True
    can_transform: bool = True
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
class SlipSpot:
    id: str
    label: str
    phrase: str
    makes_slip: bool = True
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
class Fix:
    id: str
    label: str
    phrase: str
    sense: int
    effect: str
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
        c.facts = copy.deepcopy(self.facts)
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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    skater = world.get("hero")
    if skater.meters["slip"] < THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    skater.memes["embarrassed"] += 1
    skater.meters["spun"] += 1
    out.append("__slip__")
    return out


def _r_smile(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["slip"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return []
    sig = ("smile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    helper.memes["joy"] += 1
    return ["The little crowd giggled, but nobody was mean about it."]


CAUSAL_RULES = [Rule("slip", "physical", _r_slip), Rule("smile", "social", _r_smile)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for spot_id, spot in SPOTS.items():
            for fix_id, fix in FIXES.items():
                if spot.makes_slip and fix.sense >= SENSE_MIN:
                    combos.append((sid, spot_id, fix_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    spot: str
    fix: str
    name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with a slip, a joke, and a transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
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


def explain_rejection(spot: SlipSpot, fix: Fix) -> str:
    return f"(No story: {spot.label} makes a funny slip, but {fix.label} is too weak for this world.)"


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    return f"(Refusing fix '{fid}': it scores too low on common sense (sense={f.sense} < {SENSE_MIN}).)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.spot and args.fix:
        if not (SPOTS[args.spot].makes_slip and FIXES[args.fix].sense >= SENSE_MIN):
            raise StoryError(explain_rejection(SPOTS[args.spot], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal is None or c[1] == args.spot)
              and (args.spot is None or c[1] == args.spot)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, spot_id, fix_id = rng.choice(sorted(combos))
    animal_id = args.animal or rng.choice(sorted(ANIMALS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting_id, animal_id, spot_id, fix_id, name)


def predict_transformation(world: World, spot: SlipSpot) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["slip"] += 1
    hero.meters["mud"] += 1
    return {"slip": hero.meters["slip"] >= THRESHOLD, "mud": hero.meters["mud"] >= THRESHOLD}


def tell(setting: Setting, animal: Animal, spot: SlipSpot, fix: Fix, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=animal.species, label=name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type="cat", label="Pip", role="helper"))
    helper.memes["kindness"] = 1.0
    helper.memes["joy"] = 1.0
    hero.memes["pride"] = 1.0

    world.say(
        f"{name} was a little {animal.label} who loved {setting.affordance} at {setting.place}. "
        f"One bright morning, {name} trotted across {setting.surface} near {spot.phrase}."
    )
    world.say(
        f"{name} wanted to show off a tiny hop. {name} grinned, took one brave step, and then {name} began to slip."
    )

    hero.meters["slip"] += 1
    hero.meters["mud"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{name} slid in the silliest little way -- paws high, ears wide, eyes round like marbles. "
        f"{name} landed in a soft puff and the birds seemed to giggle with the grass."
    )
    world.say(f"Pip ran over and said, \"That was the funniest slip I have ever seen!\"")

    world.para()
    world.say(
        f"{name} looked down at the splashes and blinked. {name} was muddy, a bit shocked, and very much still okay."
    )
    world.say(
        f"Pip brought {fix.phrase}, and together they made a new plan."
    )
    if fix.id == "bow":
        world.say(
            f"They tied on the bright bow. In a moment, the muddy little {animal.label} had transformed into a neat, fancy performer."
        )
    elif fix.id == "coat":
        world.say(
            f"They shook off the mud and slipped on the tiny coat. The clumsy puddle-pouncer became a tidy little host."
        )
    else:
        world.say(
            f"They used the ribbon to make a funny decoration, and the soggy animal turned into a cheerful show-off."
        )
    world.say(
        f"After that, {name} bowed, everyone laughed kindly, and the same path that caused the slip now felt like part of the joke."
    )

    world.facts.update(hero=hero, helper=helper, setting=setting, animal=animal, spot=spot, fix=fix, name=name)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes the word "slip" and ends in a transformation.',
        f"Tell a funny story where {f['name']}, a little {f['animal'].label}, slips near {f['spot'].label} and ends up changed by {f['fix'].label}.",
        f"Write a gentle animal story with humor: a slip, a kind helper, and a new look at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"Who slipped in the story?", answer=f"{f['name']} slipped near {f['spot'].label}. The tumble was funny, but it was small and harmless."),
        QAItem(question="What happened after the slip?", answer=f"Pip helped by bringing {f['fix'].label}, and that led to a cheerful transformation. {f['name']} ended up looking different and feeling proud."),
        QAItem(question="How did the story end?", answer=f"It ended with laughter, a new look, and a calm animal who could smile about the accident. The slip became part of the joke instead of a problem."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to slip?", answer="To slip means your feet or paws slide unexpectedly on a smooth or wet place. It can make you wobble or fall down for a moment."),
        QAItem(question="Why can slipping be funny in a story?", answer="Slipping can be funny when nobody gets hurt and the fall looks silly. A story can turn the mistake into laughter and a happy change."),
        QAItem(question="What is a transformation?", answer="A transformation is when something changes into a new form or a new role. In a story, it can mean a character looks different or acts in a new way."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "garden": Setting("garden", "the garden", "a patch of shiny grass", "playing tag", "bright"),
    "farm": Setting("farm", "the farm yard", "a wooden plank path", "chasing butterflies", "sunny"),
    "pond": Setting("pond", "the pond bank", "a mossy stone", "watching ducks", "fresh"),
}

ANIMALS = {
    "cat": Animal("cat", "cat", "cat"),
    "duck": Animal("duck", "duck", "duck"),
    "pig": Animal("pig", "pig", "pig"),
    "rabbit": Animal("rabbit", "rabbit", "rabbit"),
}

SPOTS = {
    "moss": SlipSpot("moss", "moss", "a slick patch of moss"),
    "peel": SlipSpot("peel", "banana peel", "a banana peel"),
    "puddle": SlipSpot("puddle", "puddle", "a tiny puddle"),
}

FIXES = {
    "bow": Fix("bow", "a bright bow", "a bright bow", 3, "decorate"),
    "coat": Fix("coat", "a tiny coat", "a tiny coat", 3, "transform"),
    "ribbon": Fix("ribbon", "a ribbon", "a ribbon", 2, "decorate"),
}

NAMES = ["Milo", "Pippa", "Nibbles", "Buzzy", "Cookie", "Sunny"]

CURATED = [
    StoryParams("garden", "rabbit", "moss", "bow", "Milo"),
    StoryParams("farm", "pig", "peel", "coat", "Pippa"),
    StoryParams("pond", "duck", "puddle", "ribbon", "Sunny"),
]


ASP_RULES = r"""
slip_happens(H) :- chosen_spot(S), slippery(S), hero(H).
transformed(H) :- slip_happens(H), chosen_fix(F), sense(F, N), sense_min(M), N >= M.
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("hero", aid))
    for sid, s in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if s.makes_slip:
            lines.append(asp.fact("slippery", sid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show slip_happens/1.\n#show transformed/1."))
    # smoke test using default curated params too
    try:
        generate(CURATED[0])
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: story generation smoke test passed; ASP model had {len(model)} atoms.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show slip_happens/1."))
    return sorted(set(asp.atoms(model, "slip_happens")))


def asp_valid_transforms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show transformed/1."))
    return sorted(set(asp.atoms(model, "transformed")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal], SPOTS[params.spot], FIXES[params.fix], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.spot:
        combos = [c for c in combos if c[1] == args.spot]
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spot, fix = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    name = args.name or resolve_name(rng)
    return StoryParams(setting, animal, spot, fix, name)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show slip_happens/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for c in valid_combos():
            print("  ", c)
        return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
