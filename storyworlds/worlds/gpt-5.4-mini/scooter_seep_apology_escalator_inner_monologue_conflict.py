#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scooter_seep_apology_escalator_inner_monologue_conflict.py
==========================================================================================

A standalone story world for a tiny folk-tale-like escalator mishap: a child
rides a scooter near an escalator, a wet seep makes the steps slippery, a
conflict rises, and an apology turns the day toward safety.

The world is small on purpose. It keeps a few typed entities, accumulating
physical meters and emotional memes, and a simple causal model that lets the
state drive the prose. The seed words are embedded as actual world ingredients:
scooter, seep, apology, escalator, inner monologue, conflict.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/scooter_seep_apology_escalator_inner_monologue_conflict.py
    python storyworlds/worlds/gpt-5.4-mini/scooter_seep_apology_escalator_inner_monologue_conflict.py --all
    python storyworlds/worlds/gpt-5.4-mini/scooter_seep_apology_escalator_inner_monologue_conflict.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/scooter_seep_apology_escalator_inner_monologue_conflict.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/scooter_seep_apology_escalator_inner_monologue_conflict.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    detail: str

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
class Character:
    id: str
    gender: str
    role: str
    age: int = 0
    traits: list[str] = field(default_factory=list)

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
    kind: str
    wettable: bool = False
    slippery: bool = False

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
class Action:
    id: str
    verb: str
    inner_voice: str
    conflict_line: str
    apology_line: str
    outcome_line: str
    risk: int
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


def _r_seep(world: World) -> list[str]:
    out: list[str] = []
    puddle = world.entities.get("seep")
    escalator = world.entities.get("escalator")
    if not puddle or not escalator:
        return out
    if puddle.meters["wet"] < THRESHOLD:
        return out
    sig = ("seep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    escalator.meters["slippery"] += 1
    world.get("child").memes["worry"] += 1
    out.append("__slippery__")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.entities.get("child")
    guardian = world.entities.get("guardian")
    if not child or not guardian:
        return []
    if child.memes["defiance"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    guardian.memes["conflict"] += 1
    return ["__conflict__"]


def _r_apology(world: World) -> list[str]:
    child = world.entities.get("child")
    guardian = world.entities.get("guardian")
    if not child or not guardian:
        return []
    if child.memes["regret"] < THRESHOLD:
        return []
    sig = ("apology",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["peace"] += 1
    guardian.memes["softened"] += 1
    return ["__apology__"]


CAUSAL_RULES = [Rule("seep", _r_seep), Rule("conflict", _r_conflict), Rule("apology", _r_apology)]


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


def inner_monologue(world: World, child: Entity, action: Action) -> None:
    world.say(
        f"Inside {child.pronoun('possessive')} own heart, {child.id} thought, "
        f'"{action.inner_voice}"'
    )


def setup(world: World, setting: Setting, child: Entity, guardian: Entity, scooter: Entity) -> None:
    child.memes["curiosity"] += 1
    child.memes["love_play"] += 1
    world.say(
        f"Long ago, at {setting.place}, {child.id} loved to glide with {child.pronoun('possessive')} "
        f"scooter while {setting.detail}."
    )
    world.say(
        f"{guardian.id} walked beside {child.id}, watching the path and the people around the escalator."
    )


def introduce_seep(world: World, seep: Entity) -> None:
    seep.meters["wet"] += 1
    world.say(
        "But a little seep from a ceiling crack had made the lower steps damp and shiny."
    )


def tempt(world: World, child: Entity, action: Action) -> None:
    child.memes["desire"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} looked at the escalator and at the scooter, and {child.id} wanted to {action.verb} too close to it."
    )
    inner_monologue(world, child, action)


def warn(world: World, guardian: Entity, child: Entity, action: Action, seep: Entity) -> None:
    world.say(
        f'{guardian.id} raised a hand. "{action.conflict_line} {seep.label} can make the steps slick."'
    )
    child.memes["heard_warning"] += 1


def slip(world: World, child: Entity, escalator: Entity) -> None:
    escalator.meters["danger"] += 1
    child.memes["fear"] += 1
    world.say(
        f"The scooter wobbled on the slick floor, and for a breath the child nearly lost balance beside the moving steps."
    )


def apologize(world: World, child: Entity, guardian: Entity, action: Action) -> None:
    child.memes["regret"] += 1
    world.say(
        f'{child.id} lowered {child.pronoun("possessive")} head. "{action.apology_line}"'
    )
    propagate(world, narrate=False)
    world.say(
        f"{guardian.id} let out a slow breath and knelt down, glad the child had stopped."
    )


def safety_turn(world: World, child: Entity, guardian: Entity, action: Action, scooter: Entity) -> None:
    child.memes["joy"] += 1
    guardian.memes["joy"] += 1
    world.say(
        f'Together they rolled the scooter back from the steps and chose a wide, dry walkway instead.'
    )
    world.say(
        f'This time {child.id} rode in peace, and the scooter hummed along safely while the escalator kept its wet secret to itself.'
    )


def tell(
    setting: Setting,
    action: Action,
    child_cfg: Character,
    guardian_cfg: Character,
    seep_cfg: ObjectCfg,
    escalator_cfg: ObjectCfg,
    scooter_cfg: ObjectCfg,
) -> World:
    world = World()
    child = world.add(Entity(id=child_cfg.id, kind="character", type=child_cfg.gender, role="child"))
    guardian = world.add(Entity(id=guardian_cfg.id, kind="character", type=guardian_cfg.gender, role="guardian"))
    seep = world.add(Entity(id=seep_cfg.id, kind="thing", type=seep_cfg.kind, label=seep_cfg.label))
    escalator = world.add(Entity(id=escalator_cfg.id, kind="thing", type=escalator_cfg.kind, label=escalator_cfg.label))
    scooter = world.add(Entity(id=scooter_cfg.id, kind="thing", type=scooter_cfg.kind, label=scooter_cfg.label))

    setup(world, setting, child, guardian, scooter)
    world.para()
    introduce_seep(world, seep)
    warn(world, guardian, child, action, seep)
    tempt(world, child, action)

    world.para()
    slip(world, child, escalator)
    apologize(world, child, guardian, action)
    safety_turn(world, child, guardian, action, scooter)

    world.facts.update(
        child=child,
        guardian=guardian,
        seep=seep,
        escalator=escalator,
        scooter=scooter,
        action=action,
        setting=setting,
        conflict=child.memes["conflict"] >= THRESHOLD,
        apologized=child.memes["regret"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "escalator": Setting(
        "escalator",
        "the escalator",
        "The handrail gleamed, and the silver steps rose and fell like a little hill made by a giant."
    )
}

ACTIONS = {
    "nearby_scoot": Action(
        "nearby_scoot",
        "scoot near the moving steps",
        "scoot near the moving steps",
        "We do not play by the moving steps",
        "I am sorry. I should have listened.",
        "The child stepped back and chose the safe path",
        risk=3,
        tags={"scooter", "apology", "conflict", "escalator"},
    ),
    "fast_ride": Action(
        "fast_ride",
        "race with the scooter",
        "race with the scooter",
        "Slow your feet by the steps",
        "I am sorry. I will be careful now.",
        "The child took a deep breath and slowed down",
        risk=2,
        tags={"scooter", "apology", "conflict", "escalator"},
    ),
}

ACTORS = {
    "Mila": Character("Mila", "girl", "child", age=6, traits=["curious", "quick"]),
    "Theo": Character("Theo", "boy", "child", age=6, traits=["bold", "restless"]),
    "Grandma": Character("Grandma", "woman", "guardian", age=60, traits=["wise", "gentle"]),
    "Dad": Character("Dad", "man", "guardian", age=35, traits=["steady", "careful"]),
}

OBJECTS = {
    "scooter": ObjectCfg("scooter", "the scooter", "scooter"),
    "seep": ObjectCfg("seep", "the seep", "seep", wettable=True, slippery=True),
    "escalator": ObjectCfg("escalator", "the escalator", "escalator", slippery=True),
}



@dataclass
class StoryParams:
    setting: str
    action: str
    child: str
    guardian: str
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

CURATED = [
    ("escalator", "nearby_scoot", "Mila", "Grandma"),
    ("escalator", "fast_ride", "Theo", "Dad"),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, a, c, g) for s in SETTINGS for a in ACTIONS for c in ACTORS if ACTORS[c].role == "child" for g in ACTORS if ACTORS[g].role == "guardian"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale story world about a scooter, a seep, and an apology by an escalator.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child", choices=[k for k, v in ACTORS.items() if v.role == "child"])
    ap.add_argument("--guardian", choices=[k for k, v in ACTORS.items() if v.role == "guardian"])
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
              and (args.child is None or c[2] == args.child)
              and (args.guardian is None or c[3] == args.guardian)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, child, guardian = rng.choice(combos)
    return StoryParams(setting, action, child, guardian)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIONS[params.action],
        ACTORS[params.child],
        ACTORS[params.guardian],
        OBJECTS["seep"],
        OBJECTS["escalator"],
        OBJECTS["scooter"],
    )
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a folk-tale style story about a scooter by an escalator, where a seep causes a conflict and someone offers an apology.",
        f"Tell a gentle story in which {f['child'].id} sees {f['scooter'].label}, notices the wet {f['seep'].label}, and finally apologizes for a risky choice.",
        "Write a child-friendly escalator story with inner monologue, conflict, and a calm apology that leads back to safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    return [
        QAItem("Who is the story about?", f"It is about {child.id} and {guardian.id}, with the escalator and the scooter nearby."),
        QAItem("Why did the child feel torn inside?", f"{child.id} wanted to use the scooter near the escalator, but the wet seep made that choice unsafe. That is why the child argued inside and then had to decide what to do next."),
        QAItem("What changed after the apology?", f"After {child.id} apologized, the tension softened and both of them stepped back from the wet steps. The scooter was moved to a safer place, and the ending became calm."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a scooter?", "A scooter is a small ride-on toy with wheels and a handlebar. Children can push it along to move around."),
        QAItem("What does seep mean?", "A seep is a little trickle of water that leaks through or out of something. A seep can make a floor damp and slippery."),
        QAItem("What is an apology?", "An apology is when someone says they are sorry for a wrong or risky choice. It helps mend hurt feelings and can calm a conflict."),
        QAItem("Why can an escalator be dangerous?", "An escalator has moving steps, so people must stay careful near it. Wet floors or rough play can make it more risky."),
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
        lines.append(f"  {e.id:10} ({e.type:9}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "escalator"),
        asp.fact("action", "nearby_scoot"),
        asp.fact("action", "fast_ride"),
        asp.fact("child", "Mila"),
        asp.fact("child", "Theo"),
        asp.fact("guardian", "Grandma"),
        asp.fact("guardian", "Dad"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, C, G) :- setting(S), action(A), child(C), guardian(G).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        generate(resolve_params(argparse.Namespace(setting=None, action=None, child=None, guardian=None), random.Random(0)))
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this tiny world only tells escalator stories with a scooter, a seep, conflict, and an apology.)"


def resolve_params_strict(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
