#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vacuum_cautionary_surprise_ghost_story.py
===========================================================================

A standalone tiny storyworld in a ghost-story style: a child hears spooky
noises, reaches for a vacuum, gets a cautious warning, and discovers that the
"ghost" has a surprising ordinary source. The world keeps the premise small:
one room, one vacuum, one strange noise, one careful adult, one surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/vacuum_cautionary_surprise_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/vacuum_cautionary_surprise_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/vacuum_cautionary_surprise_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/vacuum_cautionary_surprise_ghost_story.py --verify
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    atmosphere: str
    dark_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    makes_noise: bool = False
    makes_mess: bool = False
    dangerous: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class SurpriseCfg:
    id: str
    reveal: str
    cause: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    apply: Callable[["World"], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return c


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["spooky"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["spooky"] += 1
    world.get("child").memes["fear"] += 1
    out.append("__noise__")
    return out


def _r_reassure(world: World) -> list[str]:
    out: list[str] = []
    if world.get("adult").memes["calm"] < THRESHOLD:
        return out
    sig = ("reassure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["fear"] = max(0.0, world.get("child").memes["fear"] - 1)
    out.append("__reassure__")
    return out


RULES = [Rule("noise", _r_noise), Rule("reassure", _r_reassure)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def vacuum_gate(vacuum: ObjectCfg, target: ObjectCfg) -> bool:
    return vacuum.id == "vacuum" and target.dangerous


def caution_level(setting: Setting) -> int:
    return 3 if "attic" in setting.id else 2


def tell_silently(world: World, target: ObjectCfg) -> None:
    world.get("target").meters["revealed"] += 1
    if target.makes_mess:
        world.get("target").meters["messy"] += 1


def predict(world: World, target: ObjectCfg) -> dict:
    sim = world.copy()
    tell_silently(sim, target)
    return {"revealed": sim.get("target").meters["revealed"] >= THRESHOLD}


def setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a windy evening, {child.id} wandered into {setting.place}. "
        f"{setting.atmosphere}"
    )


def hear_noise(world: World, child: Entity, setting: Setting) -> None:
    world.get("room").meters["spooky"] += 1
    world.say(
        f"Then came a soft sound from {setting.dark_spot} -- a long, little "
        f"whoosh that sounded almost like a whisper."
    )
    world.say(f'{child.id} swallowed hard. "Did you hear that?" {child.pronoun()} whispered.')


def reach_for_vacuum(world: World, child: Entity, vacuum: Entity, obj: ObjectCfg) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} spotted the vacuum by the wall. "
        f'"If I vacuum the noise, the ghost will go away," {child.pronoun()} said.'
    )
    if predict(world, obj)["revealed"]:
        world.facts["predicted_reveal"] = True


def warn(world: World, adult: Entity, child: Entity, vacuum: Entity, obj: ObjectCfg) -> None:
    adult.memes["calm"] += 1
    level = caution_level(world.facts["setting"])
    world.say(
        f'{adult.id} shook {adult.pronoun("possessive")} head. "Don\'t use the vacuum to '
        f'chase a spooky sound," {adult.pronoun()} said. '
        f'"It could suck up {obj.phrase} or tug something loose."'
    )
    if level >= 3:
        world.say(f"{adult.id} listened closely and kept {child.id} from getting too close to {obj.phrase}.")


def fix_and_reveal(world: World, adult: Entity, vacuum: Entity, obj: ObjectCfg, surprise: SurpriseCfg) -> None:
    world.get("target").meters["revealed"] += 1
    world.say(
        f"{adult.id} turned on the vacuum only after checking the floor. "
        f"It rattled, hummed, and then out popped {surprise.reveal} from the hose -- "
        f"{surprise.cause}."
    )
    world.say(
        f"The scary shape was not a ghost at all. It was {surprise.cause}, "
        f"and the vacuum had been nudging it around in the dark."
    )


def ending(world: World, child: Entity, adult: Entity, setting: Setting, surprise: SurpriseCfg) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{adult.id} smiled and handed {child.id} a flashlight instead. "
        f'The beam cut through {setting.dark_spot}, and the room looked ordinary again.'
    )
    world.say(f"{surprise.ending_image}")




SETTINGS = {
    "hall": Setting("hall", "the old hall", "The wallpaper seemed to listen.", "the dark coat rack"),
    "attic": Setting("attic", "the attic", "The beams creaked like sleepy bones.", "the box of old costumes"),
    "basement": Setting("basement", "the basement", "The pipes knocked like tiny ghosts.", "the laundry corner"),
}

OBJECTS = {
    "sheet": ObjectCfg("sheet", "sheet", "a loose white sheet", dangerous=True, tags={"ghost", "sheet"}),
    "curtain": ObjectCfg("curtain", "curtain", "a fluttering curtain", dangerous=True, tags={"ghost", "curtain"}),
    "paperbat": ObjectCfg("paperbat", "paper bat", "a paper bat", dangerous=True, tags={"ghost", "paper"}),
}

SURPRISES = {
    "ghost": SurpriseCfg("ghost", "a lost silver key", "the vacuum had pulled a hanging keychain against the vent",
                         "The key lay in the child's palm, shining like a tiny moon.", tags={"key"}),
    "owl": SurpriseCfg("owl", "a stuffed owl with one button eye", "the vacuum had been bumping an old toy behind the boxes",
                       "The owl sat on the floor, dusty but safe, as if it had never meant to frighten anyone.", tags={"owl"}),
    "kite": SurpriseCfg("kite", "a tangled kite tail", "the vacuum had dragged a string from under the stair",
                        "A ribbon of kite tail curled at the child's feet, bright as candy in the dim light.", tags={"kite"}),
}


@dataclass
class StoryParams:
    setting: str
    obj: str
    surprise: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    ("hall", "vacuum", "sheet", "ghost"),
    ("attic", "vacuum", "curtain", "owl"),
    ("basement", "vacuum", "paperbat", "kite"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, "vacuum", o) for s in SETTINGS for o in OBJECTS if vacuum_gate(OBJECTS[o], OBJECTS[o])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story vacuum cautionary surprise world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="obj", choices=OBJECTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("vacuum", "vacuum")]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("dangerous", oid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O) :- setting(S), object(O), dangerous(O), vacuum(vacuum).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the word "vacuum" and ends with a surprise.',
        f"Tell a spooky-but-gentle story where {f['child'].id} hears a ghostly sound in {f['setting'].place} and wants to use a vacuum.",
        f"Write a cautionary story in a ghost-story style where a grown-up warns that a vacuum should not chase strange noises.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What did the child think the sound was?",
         f"{f['child'].id} thought it might be a ghost, because the noise from {f['setting'].dark_spot} sounded spooky in the dark."),
        ("What did the adult warn about?",
         f"The adult warned not to use the vacuum to chase the noise, because it could pull at loose things or suck up something important."),
        ("What was the surprise?",
         f"The surprise was that the 'ghost' was really {f['surprise'].cause}. The vacuum had only been moving it around in the dark."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a vacuum?",
         "A vacuum is a machine that uses suction to pull up dust and crumbs from the floor."),
        ("Why can a vacuum be noisy?",
         "A vacuum has a motor and moving air inside, so it makes a loud humming sound when it runs."),
        ("Why should you be careful around loose things?",
         "Loose things can get pulled, tangled, or broken if you use a machine the wrong way, so it is smart to ask a grown-up first."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    return "\n".join(lines)


def tell(setting: Setting, obj: ObjectCfg, surprise: SurpriseCfg, child_name: str, child_gender: str,
         adult_name: str, adult_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    vacuum = world.add(Entity(id="vacuum", type="thing", label="vacuum"))
    target = world.add(Entity(id="target", type="thing", label=obj.label))
    world.facts.update(setting=setting, child=child, adult=adult, vacuum=vacuum, target=target, surprise=surprise)

    setup(world, child, adult, setting)
    world.para()
    hear_noise(world, child, setting)
    reach_for_vacuum(world, child, vacuum, obj)
    warn(world, adult, child, vacuum, obj)
    world.para()
    fix_and_reveal(world, adult, vacuum, obj, surprise)
    ending(world, child, adult, setting, surprise)
    world.facts["outcome"] = "surprise"
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obj and args.obj in OBJECTS and not vacuum_gate(OBJECTS[args.obj], OBJECTS[args.obj]):
        raise StoryError("No story: the chosen object is not suitable for this vacuum tale.")
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.obj or rng.choice(list(OBJECTS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    child = args.child or rng.choice(["Mia", "Leo", "Nora", "Sam"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["Mom", "Dad"])
    adult_gender = args.adult_gender or ("mother" if adult == "Mom" else "father")
    return StoryParams(setting, obj, surprise, child, child_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.obj], SURPRISES[params.surprise],
                 params.child, params.child_gender, params.adult, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_asp() -> str:
    return asp_program("#show valid/2.")


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, obj=None, surprise=None, child=None,
                                                            child_gender=None, adult=None, adult_gender=None),
                                         random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = sample.to_json()
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(explain_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        params_list = [
            StoryParams(s, o, su, "Mia", "girl", "Mom", "mother")
            for s, o, su in CURATED
        ]
        samples = [generate(p) for p in params_list]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
