#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frown_disobedient_bad_ending_rhyming_story.py
=============================================================================

A standalone story world for a tiny rhyming tale about a child who feels a
frown, acts disobedient, and ends in a bad ending. The domain is intentionally
small: a child wants to do a quiet, simple thing, ignores a clear warning, and
the world model turns that choice into a concrete loss. The prose keeps a
rhyming, nursery-story feel, but the state changes are still causal and
traceable.

This script follows the storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "scuffed": 0.0, "dim": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "frown": 0.0, "lesson": 0.0}

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
    indoors: bool
    dusk: bool
    echoes: str

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
    fragile: bool = False
    special: str = ""
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
class ActionCfg:
    id: str
    verb: str
    rhyme: str
    effect: str
    risk: str
    loss: str
    sense: int
    power: int
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


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("loss", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["dim"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["worry"] += 1
        out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("loss", "physical", _r_loss)]


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


def can_happen(action: ActionCfg, obj: ObjectCfg) -> bool:
    return action.power > 0 and (obj.fragile or obj.makes_noise)


def sensible_actions() -> list[ActionCfg]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def bad_ending(action: ActionCfg, obj: ObjectCfg) -> bool:
    return action.power >= 2 and obj.fragile


def _do_action(world: World, actor: Entity, action: ActionCfg, obj: Entity, narrate: bool = True) -> None:
    actor.memes["frown"] += 1
    obj.meters["lost"] += 1
    obj.meters["scuffed"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, obj: ObjectCfg, action: ActionCfg) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {setting.place}, beneath the dusk so blue, {child.id} played by the "
        f"window while the soft wind blew."
    )
    world.say(
        f'{child.id} loved {obj.phrase}, bright in the room, and every small rhyme '
        f"made the evening bloom."
    )


def warn(world: World, parent: Entity, child: Entity, action: ActionCfg, obj: ObjectCfg) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Oh, do not {action.verb}," {parent.id} said true, '
        f'"for {obj.label} may break, and that would hurt you too."'
    )


def disobey(world: World, child: Entity, action: ActionCfg, obj: ObjectCfg) -> None:
    child.memes["frown"] += 1
    world.say(
        f'But {child.id} was disobedient, with a stubborn little frown; '
        f'{child.pronoun().capitalize()} went on to {action.verb} with a bounce up and down.'
    )
    world.say(
        f"{action.rhyme.capitalize()}, the child thought, and took one more chance, "
        f"as if rules were tiny things made only to dance."
    )


def accident(world: World, child: Entity, obj: Entity, action: ActionCfg) -> None:
    _do_action(world, child, action, obj, narrate=False)
    world.say(
        f"Then a small sharp crack went through the air; {obj.label} slipped from "
        f"{child.pronoun('possessive')} hands and tumbled there."
    )
    world.say(
        f"{obj.label.capitalize()} hit the floor with a pitiful clink, and the bright "
        f"little moment was gone in a blink."
    )


def ending(world: World, parent: Entity, child: Entity, obj: Entity, action: ActionCfg, setting: Setting) -> None:
    world.say(
        f"{parent.id} rushed in, but the damage was done; the {obj.label} was ruined, "
        f"and the fun was none."
    )
    world.say(
        f"{child.id} stared at the mess with a hanging-down face; the frown stayed put "
        f"like a cloud in its place."
    )
    world.say(
        f"So the night grew quiet, and the lesson stayed plain: disobedience brings "
        f"loss, and sometimes tears and pain."
    )
    world.say(
        f"The window kept glowing, but dimmer than before, and {child.id} learned to "
        f"listen a little bit more."
    )


def tell(setting: Setting, action: ActionCfg, obj_cfg: ObjectCfg, child_name: str, child_gender: str, parent_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="room", type="room", label="the room"))
    obj = world.add(Entity(id=obj_cfg.id, type="thing", label=obj_cfg.label))
    setup(world, child, parent, setting, obj_cfg, action)
    world.para()
    warn(world, parent, child, action, obj_cfg)
    disobey(world, child, action, obj_cfg)
    world.para()
    accident(world, child, obj, action)
    world.para()
    ending(world, parent, child, obj, action, setting)
    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        action=action,
        obj_cfg=obj_cfg,
        obj=obj,
        outcome="bad",
    )
    return world


SETTINGS = {
    "window": Setting("window", "the window seat", True, True, "soft"),
    "porch": Setting("porch", "the porch", False, True, "small"),
    "hall": Setting("hall", "the hall", True, False, "gentle"),
}

OBJECTS = {
    "ball": ObjectCfg("ball", "red ball", "a red ball", makes_noise=True, fragile=True, tags={"toy"}),
    "cup": ObjectCfg("cup", "glass cup", "a glass cup", fragile=True, tags={"fragile"}),
    "lamp": ObjectCfg("lamp", "little lamp", "a little lamp", fragile=True, special="glow", tags={"light"}),
}

ACTIONS = {
    "bounce": ActionCfg("bounce", "bounce", "bounce", "bounced too hard", "the toy might crack", "the toy cracked", 2, 2, tags={"toy"}),
    "toss": ActionCfg("toss", "toss", "toss", "tossed it high", "the glass might fall", "the glass fell", 3, 3, tags={"fragile"}),
    "tap": ActionCfg("tap", "tap", "tap", "tapped too sharp", "the lamp might tilt", "the lamp tipped", 2, 2, tags={"light"}),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava"],
    "boy": ["Tom", "Ben", "Leo", "Max"],
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    obj: str
    action: str
    child: str
    child_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for oid, obj in OBJECTS.items():
                if can_happen(action, obj) and bad_ending(action, obj):
                    combos.append((sid, aid, oid))
    return combos


def explain_rejection(action: ActionCfg, obj: ObjectCfg) -> str:
    if not can_happen(action, obj):
        return f"(No story: {action.verb} does not plausibly matter for {obj.label}.)"
    return f"(No story: {action.verb} with {obj.label} is not strong enough for a bad ending.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming bad-ending story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="obj", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.action is None or c[1] == args.action)
              and (args.obj is None or c[2] == args.obj)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, obj, action, child, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], OBJECTS[params.obj], params.child, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, action, obj = f["child"], f["action"], f["obj_cfg"]
    return [
        f'Write a short rhyming story for a small child that includes the words "{child.id}", "{action.id}", "{obj.label}", and "frown".',
        f"Tell a nursery-style bad-ending story where {child.id} is disobedient, ignores a warning, and {obj.label} ends up ruined.",
        f"Write a simple rhyme with a clear beginning, a warning, a bad choice, and a sad ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, action, obj = f["child"], f["parent"], f["action"], f["obj_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}. {child.id} wants to play, but the story turns sad when {child.id} does not listen."),
        ("What did {0.id} want to do?".format(child),
         f"{child.id} wanted to {action.verb} with {obj.label}. The wish sounded small, but it led to a bad ending."),
        ("Why was the ending bad?",
         f"{child.id} was disobedient after {parent.id} gave a warning, so {obj.label} got lost and ruined. The choice changed a happy game into a sad one."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a frown usually mean?",
         "A frown usually means someone is unhappy, worried, or upset."),
        ("What does disobedient mean?",
         "Disobedient means not following a rule or not listening when a grown-up gives a clear instruction."),
        ("Why should children listen to warnings?",
         "Warnings can help keep people safe and keep things from breaking or getting lost."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, O) :- setting(S), action(A), object(O), power(A, P), P >= 2.
sensible(A) :- action(A), sense(A, S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    if set(asp_sensible()) != {a.id for a in sensible_actions()}:
        print("MISMATCH: ASP and Python sensible actions differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: story generation crashed: {exc}")
        rc = 1
    print("OK: verify smoke test completed." if rc == 0 else "VERIFY FAILED.")
    return rc


def explain_response(action: str) -> str:
    a = ACTIONS[action]
    return f"(Refusing action '{action}': it scores too low on common sense (sense={a.sense} < {SENSE_MIN}).)"


CURATED = [
    StoryParams("window", "cup", "toss", "Mina", "girl", "mother"),
    StoryParams("porch", "ball", "bounce", "Toby", "boy", "father"),
    StoryParams("hall", "lamp", "tap", "Leah", "girl", "mother"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible actions: {', '.join(asp_sensible())}")
        print(f"valid combos: {len(asp_valid_combos())}")
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
