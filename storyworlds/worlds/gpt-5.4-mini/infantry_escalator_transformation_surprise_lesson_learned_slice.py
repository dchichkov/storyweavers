#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/infantry_escalator_transformation_surprise_lesson_learned_slice.py
=================================================================================================

A small standalone storyworld for a slice-of-life escalator story about infantry,
a surprising transformation, and a gentle lesson learned.

The domain is intentionally tiny: a child or young person rides an escalator at a
station or mall with a toy or a school project about infantry. A surprise changes
the object or the view of the day, then a calm helper turns it into a lesson
learned. The story is built from simulation state, not from a frozen paragraph.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    details: str

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    topic: str
    transform_into: str
    surprise: str
    lesson: str
    makes_surprise: bool = True
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
class HelperCfg:
    id: str
    label: str
    action: str
    lesson_text: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    object: str
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


SETTINGS = {
    "station": Setting("station", "the escalator at the station", "It hummed beside a bright wall of glass."),
    "mall": Setting("mall", "the escalator at the mall", "Store signs shimmered nearby and people moved softly."),
    "library": Setting("library", "the escalator by the library lobby", "It was quiet except for shoes and a low hum."),
}

OBJECTS = {
    "toy_soldiers": ObjectCfg(
        "toy_soldiers",
        "toy soldiers",
        "a little box of toy soldiers",
        "infantry",
        "glossy painted parade figures",
        "one soldier changed into a tiny paper crane",
        "they were only toys after all",
        tags={"toy", "infantry", "transformation"},
    ),
    "paper_diagram": ObjectCfg(
        "paper_diagram",
        "paper diagram",
        "a folded paper diagram of infantry",
        "infantry",
        "a folded map of bright flowers",
        "the drawing turned into a tiny sticker sheet",
        "surprises can be gentle too",
        tags={"paper", "infantry", "transformation"},
    ),
    "wooden_set": ObjectCfg(
        "wooden_set",
        "wooden set",
        "a small wooden infantry set",
        "infantry",
        "smooth little blocks shaped like houses",
        "the blocks became a rainbow bridge",
        "quiet changes can still be exciting",
        tags={"wood", "infantry", "transformation"},
    ),
}

HELPERS = {
    "grandparent": HelperCfg(
        "grandparent",
        "grandparent",
        "showed how to hold it safely",
        "The day became a lesson learned about patience, careful hands, and noticing what changed.",
        tags={"lesson"},
    ),
    "parent": HelperCfg(
        "parent",
        "parent",
        "helped sort the pieces and smile",
        "The lesson learned was that surprises are easier when someone stays calm and kind.",
        tags={"lesson"},
    ),
    "guide": HelperCfg(
        "guide",
        "station guide",
        "paused to explain the surprise",
        "The lesson learned was to watch closely and keep small things safe on moving stairs.",
        tags={"lesson"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Zoe", "Maya", "Iris", "Hana"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Sam", "Leo", "Finn", "Arlo", "Ben"]
TRAITS = ["careful", "curious", "quiet", "kind", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for o in OBJECTS:
            for h in HELPERS:
                out.append((s, o, h))
    return out


def explain_rejection() -> str:
    return "(No story: no valid combination matches the given options.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life escalator storyworld with infantry, surprise, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, obj, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    return StoryParams(setting, hero, hero_gender, helper, helper_gender, obj)


def _resolve_pronouns(ent: Entity) -> str:
    return ent.label_word


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["surprised"] >= THRESHOLD and ("transform", ent.id) not in world.fired:
            world.fired.add(("transform", ent.id))
            ent.meters["changed"] += 1
            out.append("__transform__")
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def story_setup(world: World, hero: Entity, helper: Entity, obj: Entity, cfg: ObjectCfg) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} rode the escalator slowly, one step at a time, while {hero.pronoun('possessive')} "
        f"{cfg.phrase} rested carefully in {hero.pronoun('possessive')} hands. "
        f"{world.setting.details}"
    )
    world.say(
        f"Beside {hero.id}, {helper.id} watched the moving steps and said, "
        f'"{cfg.topic} is interesting, isn\'t it?"'
    )


def surprise(world: World, hero: Entity, obj: Entity, cfg: ObjectCfg) -> None:
    obj.meters["surprised"] += 1
    hero.memes["surprise"] += 1
    world.say(
        f"Then the escalator gave a tiny jolt, and {cfg.phrase} seemed to shimmer. "
        f"For one blinking moment, one part of it became {cfg.transform_into}."
    )


def transform(world: World, hero: Entity, obj: Entity, cfg: ObjectCfg) -> None:
    obj.meters["changed"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} stared, wide-eyed, as {cfg.surprise}. It was not scary at all, only unexpected."
    )
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} hands steady and looked again to make sure the change was real."
    )


def lesson(world: World, hero: Entity, helper: Entity, cfg: ObjectCfg, helper_cfg: HelperCfg) -> None:
    hero.memes["calm"] += 1
    hero.memes["lesson"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} smiled and {helper_cfg.action}. "
        f"Then {helper_cfg.lesson_text}"
    )
    world.say(
        f"{hero.id} nodded and tucked the {cfg.label} close. "
        f"The escalator kept moving, and the little surprise had become a calm memory."
    )


def tell(setting: Setting, cfg: ObjectCfg, helper_cfg: HelperCfg,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    obj = world.add(Entity(cfg.id, type="object", label=cfg.label))
    story_setup(world, hero, helper, obj, cfg)
    world.para()
    surprise(world, hero, obj, cfg)
    propagate(world, narrate=False)
    transform(world, hero, obj, cfg)
    world.para()
    lesson(world, hero, helper, cfg, helper_cfg)
    world.facts.update(hero=hero, helper=helper, object=obj, cfg=cfg, helper_cfg=helper_cfg, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story set on an escalator that includes the word "infantry" and ends with a lesson learned.',
        f"Tell a small everyday story where {f['hero'].id} sees {f['cfg'].phrase} on an escalator, gets a surprise, and learns something calm from {f['helper'].id}.",
        f"Write a story for a young child about a quiet escalator ride, a surprising transformation, and a kind lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, cfg = f["hero"], f["helper"], f["cfg"]
    return [
        QAItem(
            question=f"What was {hero.id} carrying?",
            answer=f"{hero.id} was carrying {cfg.phrase}. It was the infantry-themed object in the story, and it changed in a surprising way on the escalator."
        ),
        QAItem(
            question="What surprising thing happened?",
            answer=f"One part of {cfg.label} changed into {cfg.transform_into}. The surprise was small and gentle, so it felt magical instead of upsetting."
        ),
        QAItem(
            question=f"What did {helper.id} help with?",
            answer=f"{helper.id} helped keep things calm and explained the moment kindly. That turned the surprise into a lesson learned."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving set of steps that carries people up and down slowly in places like stations and malls."
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry usually means soldiers who move on foot. In a child story, it can also be the topic of a toy, picture, or school project."
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the useful idea someone remembers after something happens. It helps them do better or feel calmer next time."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("station", "Mina", "girl", "grandparent", "girl", "toy_soldiers"),
    StoryParams("mall", "Theo", "boy", "parent", "boy", "paper_diagram"),
    StoryParams("library", "Lila", "girl", "guide", "girl", "wooden_set"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    cfg = OBJECTS[params.object]
    helper_cfg = HELPERS[params.helper]
    helper_name = params.helper.capitalize()
    world = tell(setting, cfg, helper_cfg, params.hero, params.hero_gender, helper_name, params.helper_gender)
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
surprised(O) :- object(O).
transformed(O) :- surprised(O).
lesson_learned(H) :- helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show surprised/1. #show transformed/1. #show lesson_learned/1."))
        atoms = set(asp.atoms(model, "surprised")) | set(asp.atoms(model, "transformed")) | set(asp.atoms(model, "lesson_learned"))
        expected = {(o,) for o in OBJECTS} | {(o,) for o in OBJECTS} | {(h,) for h in HELPERS}
        if atoms != expected:
            print("MISMATCH: ASP twin not aligned.")
            return 1
    except Exception as exc:
        print(f"ASP verify failed: {exc}")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed.")
    return 0


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surprised/1.\n#show transformed/1.\n#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
