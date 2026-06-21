#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wooden_moral_value_sharing_bad_ending_adventure.py
===================================================================================

A small adventure storyworld about a wooden thing, a sharing choice, and a moral
lesson that arrives with a bad ending.

Domain sketch
-------------
Two child adventurers explore a little wooden place: a dock, a treehouse, a shed,
or a boat. They discover one useful wooden object, and the story turns on whether
they share it.

This world intentionally supports a bad ending. When a child refuses to share,
the other child cannot solve the obstacle in time, and the adventure ends with
the children separated, disappointed, or stranded. The moral value is concrete:
sharing the helpful thing keeps an adventure together; refusing to share breaks
the plan.

The simulation is state-driven:
- meters track physical conditions like distance, damage, drift, and daylight
- memes track emotions like trust, greed, fear, and relief

The renderer turns state transitions into a child-facing adventure tale.
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
MORAL_MIN = 2


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
    plural: bool = False
    wooden: bool = False
    helpful: bool = False
    fragile: bool = False

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    obstacle: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    use: str
    moral_hook: str
    wooden: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Choice:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for kid in [e for e in world.entities.values() if e.role in {"leader", "helper"}]:
        if kid.memes["split"] < THRESHOLD:
            continue
        sig = ("scatter", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        other = world.get(world.facts["helper"].id if kid.id == world.facts["leader"].id else world.facts["leader"].id)
        other.memes["fear"] += 1
        kid.memes["fear"] += 1
        world.get("path").meters["unsafe"] += 1
        out.append("__scatter__")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_choice(choice: Choice) -> bool:
    return choice.sense >= MORAL_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid, obj in OBJECTS.items():
            for cid, ch in CHOICES.items():
                if obj.wooden and valid_choice(ch):
                    combos.append((sid, oid, cid))
    return combos


@dataclass
class StoryParams:
    setting: str
    object: str
    choice: str
    leader: str
    leader_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a wooden thing, sharing, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--leader")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.choice and not valid_choice(CHOICES[args.choice]):
        raise StoryError(f"(Refusing choice '{args.choice}': it does not support the sharing moral.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, oid, cid = rng.choice(sorted(combos))
    lg = args.leader_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if lg == "girl" and rng.random() < 0.5 else "girl")
    leader = args.leader or rng.choice(GIRL_NAMES if lg == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if hg == "girl" else BOY_NAMES) if n != leader])
    return StoryParams(setting=sid, object=oid, choice=cid, leader=leader,
                       leader_gender=lg, helper=helper, helper_gender=hg)


def predict_bad(world: World, obj_id: str, choice_id: str) -> dict:
    sim = world.copy()
    _do_choice(sim, sim.get("leader"), sim.get("helper"), OBJECTS[obj_id], CHOICES[choice_id], narrate=False)
    return {"separated": sim.get("path").meters["unsafe"] >= THRESHOLD, "fear": sim.get("helper").memes["fear"]}


def _do_choice(world: World, leader: Entity, helper: Entity, obj: ObjectCfg, choice: Choice, narrate: bool = True) -> None:
    leader.memes["split"] += 1
    if choice.id == "share":
        helper.memes["trust"] += 1
        world.get(obj.id).meters["used"] += 1
    else:
        helper.memes["hurt"] += 1
        world.get(obj.id).meters["held_tight"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, obj: ObjectCfg, choice: Choice, leader_name: str, leader_gender: str,
         helper_name: str, helper_gender: str) -> World:
    w = World()
    leader = w.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader", traits=["brave"]))
    helper = w.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["kind"]))
    path = w.add(Entity(id="path", type="place", label="the path"))
    item = w.add(Entity(id=obj.id, type="tool", label=obj.label, wooden=obj.wooden, helpful=True))
    w.facts.update(leader=leader, helper=helper, setting=setting, obj=obj, choice=choice, item=item, path=path)

    w.say(f"On a bright adventure, {leader.id} and {helper.id} set out toward {setting.place}. {setting.scene}")
    w.say(f"They found {obj.phrase}, a {obj.moral_hook} that could help them cross the obstacle.")

    w.para()
    w.say(f"But at {setting.obstacle}, only one good helper was left for the job.")
    if choice.id == "share":
        w.say(f'"Let\'s share it," said {leader.id}, and {helper.id} nodded.')
        w.say(f"Together they used it to {obj.use}, and the path stayed calm.")
        w.say(f"The adventure ended with both children smiling beside {setting.ending_image}.")
    else:
        w.say(f'"It is mine," said {leader.id}, and {helper.id} reached for it too late.')
        pred = predict_bad(w, obj.id, choice.id)
        if pred["separated"]:
            path.meters["unsafe"] += 1
            helper.memes["fear"] += 1
            leader.memes["fear"] += 1
            w.say(f"The wooden thing was held too tight, and the chance to solve the problem slipped away.")
            w.say(f"Their little adventure went wrong: one child moved ahead alone, and the other was left behind at {setting.ending_image}.")
        else:
            w.say(f"Nothing worked the way they hoped, and their plan fell apart.")
    return w


SETTINGS = {
    "dock": Setting(id="dock", place="the old dock", scene="A small wooden boat waited by the water.", obstacle="the gap over the reeds", ending_image="the empty waterline", tags={"wooden", "adventure"}),
    "treehouse": Setting(id="treehouse", place="the treehouse", scene="A ladder creaked up to a little wooden room in the branches.", obstacle="the high gap between branches", ending_image="the dark branches below", tags={"wooden", "adventure"}),
    "shed": Setting(id="shed", place="the shed", scene="A wooden shed hid maps, ropes, and dusty jars.", obstacle="the locked back door", ending_image="the closed shed door", tags={"wooden", "adventure"}),
    "raft": Setting(id="raft", place="the river raft", scene="A tiny wooden raft drifted at the shore.", obstacle="the fast current", ending_image="the rippling river", tags={"wooden", "adventure"}),
}

OBJECTS = {
    "oar": ObjectCfg(id="oar", label="wooden oar", phrase="a wooden oar", use="row across the water", moral_hook="single tool", wooden=True, tags={"wooden"}),
    "bridge_plank": ObjectCfg(id="bridge_plank", label="wooden plank", phrase="a wooden plank", use="bridge the gap", moral_hook="steady plank", wooden=True, tags={"wooden"}),
    "key": ObjectCfg(id="key", label="wooden key", phrase="a small wooden key", use="open the gate", moral_hook="tiny key", wooden=True, tags={"wooden"}),
}

CHOICES = {
    "share": Choice(id="share", sense=3, power=3, text="shared it at once", fail="", tags={"sharing", "moral"}),
    "keep": Choice(id="keep", sense=1, power=1, text="kept it to themselves", fail="kept it too tightly and lost the moment", tags={"greedy", "bad"}),
}

GIRL_NAMES = ["Lily", "Mina", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Max", "Finn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the word "wooden" and a clear sharing lesson.',
        f"Tell a short adventure about {f['leader'].id} and {f['helper'].id} finding {f['obj'].phrase} and making a choice about sharing.",
        f"Write a story with a bad ending where refusing to share {f['obj'].label} ruins the adventure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader, helper, setting, obj, choice = f["leader"], f["helper"], f["setting"], f["obj"], f["choice"]
    qa = [
        ("Who went on the adventure?", f"{leader.id} and {helper.id} went on the adventure together."),
        ("What did they find?", f"They found {obj.phrase}, which was useful because it was made of wooden material and could help them continue."),
        ("What moral lesson does the story teach?", "It teaches that sharing helps an adventure keep going, while refusing to share can leave everyone stuck."),
    ]
    if choice.id == "keep":
        qa.append(("Why did the adventure go badly?", f"{leader.id} would not share {obj.label}, so the other child could not help in time and the adventure fell apart."))
        qa.append(("How did the story end?", f"It ended badly, with the children separated and the useful chance lost at {setting.ending_image}."))
    else:
        qa.append(("How did the children solve the problem?", f"They shared {obj.label} and used it together, so the obstacle became manageable."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does wooden mean?", "Wooden means made from wood, like a treehouse, a plank, or a toy carved from a branch."),
        ("Why is sharing important?", "Sharing helps people work together, take turns, and finish a hard task without leaving someone out."),
        ("What is an adventure?", "An adventure is an exciting journey or task where something new or tricky happens."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.wooden:
            bits.append("wooden=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,C) :- setting(S), object(O), choice(C), wooden(O), good_choice(C).
bad_end(S,O,C) :- valid(S,O,C), refuse(C).
good_choice(share).
refuse(keep).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.wooden:
            lines.append(asp.fact("wooden", oid))
    for cid, ch in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if ch.sense >= MORAL_MIN:
            lines.append(asp.fact("good_choice", cid))
        if cid == "keep":
            lines.append(asp.fact("refuse", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between clingo and valid_combos()")
    try:
        _ = generate(resolve_params(argparse.Namespace(setting=None, object=None, choice=None, leader=None, leader_gender=None, helper=None, helper_gender=None), random.Random(7)))
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: story generation smoke test passed.")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, o, c) for s in SETTINGS for o in OBJECTS for c in CHOICES if OBJECTS[o].wooden and CHOICES[c].sense >= MORAL_MIN]


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    for key, val in ((params.setting, SETTINGS), (params.object, OBJECTS), (params.choice, CHOICES)):
        if key not in val:
            raise StoryError("Invalid params for this world.")
    if not OBJECTS[params.object].wooden:
        raise StoryError("This adventure requires a wooden object.")
    if not valid_choice(CHOICES[params.choice]):
        raise StoryError("The chosen action does not support the moral lesson.")
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], CHOICES[params.choice],
                 params.leader, params.leader_gender, params.helper, params.helper_gender)
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, o, c = rng.choice(sorted(combos))
    lg = args.leader_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if lg == "girl" else "girl")
    leader = args.leader or rng.choice(GIRL_NAMES if lg == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if hg == "girl" else BOY_NAMES) if n != leader])
    return StoryParams(setting=s, object=o, choice=c, leader=leader, leader_gender=lg, helper=helper, helper_gender=hg)


def build_story_from_defaults() -> StorySample:
    params = StoryParams(setting="dock", object="oar", choice="keep", leader="Lily", leader_gender="girl", helper="Tom", helper_gender="boy")
    return generate(params)


CURATED = [
    StoryParams(setting="dock", object="oar", choice="keep", leader="Lily", leader_gender="girl", helper="Tom", helper_gender="boy"),
    StoryParams(setting="treehouse", object="bridge_plank", choice="keep", leader="Mina", leader_gender="girl", helper="Finn", helper_gender="boy"),
    StoryParams(setting="shed", object="key", choice="keep", leader="Ben", leader_gender="boy", helper="Nora", helper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show bad_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
