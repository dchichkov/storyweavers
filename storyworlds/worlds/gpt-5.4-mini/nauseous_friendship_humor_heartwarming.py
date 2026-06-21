#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nauseous_friendship_humor_heartwarming.py
========================================================================

A standalone story world for a small heartwarming friendship tale with humor:
someone feels nauseous, friends help in a gentle way, a comic mistake happens,
and the ending proves the friendship became warmer.

Seed idea
---------
Two friends are at a small outing or school moment. One friend feels nauseous.
The other notices, makes space, brings a calm helper object, and keeps things
light with harmless humor. The nauseous friend recovers, they share a kind
ending image, and their friendship deepens.

This world keeps the simulation tiny:
- one sick character
- one caring friend
- one helpful adult or helper
- one setting with a place to sit
- one small comic prop
- one remedy object
- one symptom and one emotional turn

It follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate
- an inline ASP twin
- prompts, story QA, and world QA generated from world state
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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
SICK_MIN = 1.0
HELP_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
    cozy_detail: str
    sitting_spot: str
    noise: str

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
class Helper:
    id: str
    label: str
    object_name: str
    purpose: str
    phrase: str
    gives_comfort: bool = True

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
class ComicProp:
    id: str
    label: str
    action: str
    squeak: str

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
class Remedy:
    id: str
    label: str
    use_text: str
    effect_text: str
    strength: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_relieved(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["nausea"] < THRESHOLD:
            continue
        if e.meters["comfort"] < THRESHOLD:
            continue
        sig = ("relieved", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["nausea"] = max(0.0, e.meters["nausea"] - 1.0)
        e.memes["relief"] += 1
        out.append("__relief__")
    return out


def _r_laugh_softly(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["humor"] < THRESHOLD or e.meters["nausea"] < THRESHOLD:
            continue
        sig = ("humor", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["smile"] += 1
        out.append("__humor__")
    return out


CAUSAL_RULES = [
    Rule("relieved", "physical", _r_relieved),
    Rule("humor", "social", _r_laugh_softly),
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


def reasonableness_ok(setting: Setting, comic: ComicProp, remedy: Remedy) -> bool:
    return bool(setting.sitting_spot and comic.action and remedy.strength >= 1)


def best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.strength)


def should_recover(remedy: Remedy, severity: int) -> bool:
    return remedy.strength >= severity


def predict_help(world: World, sick_id: str, remedy_id: str) -> dict:
    sim = world.copy()
    sick = sim.get(sick_id)
    sick.meters["nausea"] += 1
    sim.get(remedy_id).meters["comfort"] += 1
    propagate(sim, narrate=False)
    return {
        "nausea_after": sim.get(sick_id).meters["nausea"],
        "smile": sim.get(sick_id).memes["smile"],
    }


def usher(world: World, sick: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.place}, {sick.id} was starting to feel nauseous. "
        f"{friend.id} noticed right away and walked close beside {sick.pronoun('object')}."
    )
    world.say(
        f"The little group had been enjoying {setting.cozy_detail}, but the room's "
        f"{setting.noise} suddenly felt too loud."
    )


def comic_moment(world: World, friend: Entity, prop: ComicProp) -> None:
    friend.memes["humor"] += 1
    world.say(
        f"{friend.id} pointed at {prop.label} and said, "
        f'"If we needed a captain for this ship, {prop.label} would do it!" '
        f"{prop.squeak}"
    )
    world.say(
        f"It was a silly thing to say, and it made the scary feeling less sharp."
    )


def help_friend(world: World, helper: Entity, sick: Entity, remedy: Remedy, setting: Setting) -> None:
    sick.meters["comfort"] += 1
    helper.meters["helped"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came over with {remedy.label}. "
        f"{helper.pronoun().capitalize()} {remedy.use_text}."
    )
    world.say(
        f"Then {helper.pronoun()} {remedy.effect_text}, and {sick.id} sat near {setting.sitting_spot} to rest."
    )
    propagate(world, narrate=False)


def recovery(world: World, sick: Entity, friend: Entity, remedy: Remedy, setting: Setting) -> None:
    if should_recover(remedy, 1):
        sick.meters["nausea"] = 0.0
    sick.memes["trust"] += 1
    friend.memes["love"] += 1
    world.say(
        f"After a while, {sick.id}'s face turned brighter. {sick.id} took a slow breath, "
        f"and the dizzy feeling drifted away."
    )
    world.say(
        f"{friend.id} stayed close until {sick.id} could smile again. "
        f"By the end, both friends were curled up safely by {setting.sitting_spot}."
    )


def ending_image(world: World, sick: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"{sick.id} leaned against {friend.pronoun('object')} shoulder, and {friend.id} "
        f"held a cup of water like it was something precious."
    )
    world.say(
        f"The day still had its funny wobble, but it ended warm: two friends, "
        f"a quiet corner, and a much steadier smile."
    )


SETTINGS = {
    "cafeteria": Setting("cafeteria", "the school cafeteria", "warm sunlight on the window seat", "a bench by the wall", "the clatter of trays"),
    "bus": Setting("bus", "the bus ride home", "the bump of the wheels", "the front seat", "the humming engine"),
    "bedroom": Setting("bedroom", "the bedroom play corner", "soft pillows and picture books", "the rug near the window", "the rain tapping the glass"),
}

COMIC_PROPS = {
    "hat": ComicProp("hat", "a tiny paper hat", "wobbled", "It slipped sideways and looked very serious."),
    "sock": ComicProp("sock", "one striped sock", "waved", "It flopped like a flag in a breeze."),
    "spoon": ComicProp("spoon", "a plastic spoon", "saluted", "It gave a ridiculous little shine."),
}

REMEDIES = {
    "water": Remedy("water", "a cold cup of water", "offered it carefully and told {sick} to sip slowly", "placed it within easy reach", 2, {"water"}),
    "cracker": Remedy("cracker", "a plain cracker", "broke it into small pieces for {sick}", "said it might help settle the stomach", 1, {"food"}),
    "coolcloth": Remedy("coolcloth", "a cool wet cloth", "put it on {sick}'s forehead", "let the cool cloth rest gently there", 3, {"cloth"}),
}

FRIENDS = ["Mina", "Jules", "Sami", "Nora", "Theo", "Pip", "Lena", "Noah"]
HELPERS = ["Nurse Bell", "the teacher", "the kind parent"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    friend1: str
    friend2: str
    comic_prop: str
    remedy: str
    helper: str
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
    for sid, setting in SETTINGS.items():
        for cid in COMIC_PROPS:
            for rid, remedy in REMEDIES.items():
                if reasonableness_ok(setting, COMIC_PROPS[cid], remedy):
                    combos.append((sid, cid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small friendship story world with nauseous humor and a heartwarming ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=COMIC_PROPS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, remedy = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(HELPERS)
    name1 = args.name1 or rng.choice(FRIENDS)
    name2 = args.name2 or rng.choice([n for n in FRIENDS if n != name1])
    return StoryParams(setting, name1, name2, prop, remedy, helper)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    sick = world.add(Entity(params.friend1, kind="character", type="child", role="sick"))
    friend = world.add(Entity(params.friend2, kind="character", type="child", role="friend"))
    helper = world.add(Entity("Helper", kind="character", type="adult", role="helper", label=params.helper))
    prop = COMIC_PROPS[params.comic_prop]
    remedy = REMEDIES[params.remedy]

    sick.meters["nausea"] = 1.0
    friend.memes["humor"] = 0.0

    world.say(
        f"{sick.id} and {friend.id} were sharing {setting.cozy_detail} at {setting.place}."
    )
    usher(world, sick, friend, setting)

    world.para()
    comic_moment(world, friend, prop)

    world.para()
    helper.meters["helped"] += 0
    helper.label = params.helper
    helper.label_word = helper.label_word if hasattr(helper, "label_word") else params.helper
    helper.label = params.helper
    world.say(
        f"{helper.label} noticed the problem and came over with something helpful."
    )
    help_friend(world, helper, sick, remedy, setting)

    world.para()
    recovery(world, sick, friend, remedy, setting)
    ending_image(world, sick, friend, setting)

    world.facts.update(
        setting=setting,
        sick=sick,
        friend=friend,
        helper=helper,
        prop=prop,
        remedy=remedy,
        outcome="recovered" if sick.meters["nausea"] < THRESHOLD else "still_sick",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming friendship story that includes the word "nauseous" and a little joke about {f["prop"].label}.',
        f"Tell a gentle story where {f['sick'].id} feels nauseous, {f['friend'].id} helps with humor, and everyone ends up feeling closer.",
        f"Write a short story about friends at {f['setting'].place} where a helper brings {f['remedy'].label} and the mood becomes warm again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sick, friend, helper, prop, remedy, setting = (
        f["sick"], f["friend"], f["helper"], f["prop"], f["remedy"], f["setting"]
    )
    return [
        ("Who felt nauseous in the story?",
         f"{sick.id} felt nauseous first, which is why the day turned careful and slow. {friend.id} noticed right away and stayed close."),
        ("How did the friend help?",
         f"{friend.id} used a small joke about {prop.label} to make the moment lighter. Then {friend.id} kept {sick.id} company until help arrived."),
        ("What did the helper bring?",
         f"{helper.label} brought {remedy.label} and used it gently. That helped {sick.id} rest near {setting.sitting_spot} and feel better."),
        ("How did the story end?",
         f"It ended with both friends calm and together, which made the whole scene heartwarming. The ending image proves that the scary feeling passed and friendship stayed strong."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does nauseous mean?",
         "Nauseous means feeling like you might throw up or need to sit down and rest. It is a yucky feeling, but it can pass."),
        ("What helps when someone feels nauseous?",
         "A person may need a quiet place, a little water, and a calm helper nearby. Gentle care can make the feeling easier."),
        ("Why can a funny joke help a friend?",
         "A kind, silly joke can help a worried person smile a little. Smiling does not fix everything, but it can make the moment feel less scary."),
        ("What is a heartwarming story?",
         "A heartwarming story is one that leaves you feeling kind, safe, and happy inside. It often shows friends helping each other."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, R) :- setting(S), prop(P), remedy(R), ok(S, P, R).
outcome(recovered) :- chosen_remedy(R), strength(R, N), N >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in COMIC_PROPS:
        lines.append(asp.fact("prop", pid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("strength", rid, r.strength))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prop=None, remedy=None, helper=None, name1=None, name2=None), random.Random(1)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def explain_rejection(setting: Setting, prop: ComicProp, remedy: Remedy) -> str:
    return "(No story: this combination is not a reasonable little friendship scene.)"


def valid_choice_reason(setting: Setting, prop: ComicProp, remedy: Remedy) -> bool:
    return reasonableness_ok(setting, prop, remedy)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams("cafeteria", "Mina", "Jules", "hat", "water", "Nurse Bell"),
    StoryParams("bus", "Sami", "Nora", "sock", "coolcloth", "the teacher"),
    StoryParams("bedroom", "Theo", "Pip", "spoon", "cracker", "the kind parent"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
