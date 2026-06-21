#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lush_steep_hill_path_foreshadowing_transformation_reconciliation.py
====================================================================================================

A standalone storyworld for a heartwarming, small-domain tale set on a steep hill
path with foreshadowing, transformation, and reconciliation.

Premise:
A child and a caregiver hike a lush steep hill path to deliver a special basket
to a lonely neighbor. A small misstep scares the child, the helper item fails,
and the pair must change their plan. The route becomes gentler, the mood softens,
and the ending proves the relationship is warmer than before.

This script follows the Storyweavers contract:
- self-contained stdlib Python
- imports storyworlds/results.py eagerly
- exposes StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates three QA sets from world state
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
COURAGE_START = 4.0


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
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Hill:
    id: str
    label: str
    lush: bool
    steep: bool
    path_word: str
    path_detail: str
    view_word: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    fragile: bool = False
    helpful: bool = False
    gives_light: bool = False
    gives_balance: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Response:
    id: str
    sense: int
    method: str
    fail_method: str
    qa_text: str
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
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_obj(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def obj(self, oid: str) -> ObjectThing:
        return self.objects[oid]

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
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    hill: str
    guide: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    gift: str
    helper_item: str
    response: str
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
    child = world.get("child")
    hill = world.facts["hill_cfg"]
    if child.meters["slip"] < THRESHOLD:
        return out
    sig = ("slip", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    world.facts["path_change"] = True
    out.append("__slip__")
    if hill.steep:
        world.get("path").meters["danger"] += 1
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if helper.memes["comfort"] < THRESHOLD:
        return out
    sig = ("help", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [Rule("slip", "physical", _r_slip), Rule("help", "social", _r_help)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(hill: Hill, child_tool: ObjectThing) -> bool:
    return hill.steep and child_tool.helpful


def route_condition(hill: Hill) -> str:
    return "a steep hill path" if hill.steep else "a hill path"


def predict(world: World, scenario: str) -> dict:
    sim = world.copy()
    if scenario == "slip":
        sim.get("child").meters["slip"] += 1
        propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "trust": sim.get("child").memes["trust"],
        "danger": sim.get("path").meters["danger"],
    }


def _do_bad_step(world: World, narrate: bool = True) -> None:
    world.get("child").meters["slip"] += 1
    world.say("Halfway up, one shoe slid on the damp stone.")
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, hill: Hill, gift: ObjectThing) -> None:
    child.memes["curiosity"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"On a lush morning, {child.id} and {helper.id} started up {hill.label}, "
        f"following {hill.path_word} lined with soft grass and bright leaves."
    )
    world.say(
        f"They were carrying {gift.phrase} for the neighbor at the top, and the view kept opening wider with each step."
    )


def foreshadow(world: World, child: Entity, hill: Hill, helper_item: ObjectThing) -> None:
    world.say(
        f"The path narrowed where the stones leaned sideways, and {helper_item.label} gave a tiny wobble whenever the wind brushed it."
    )
    world.say(
        f'{helper_item.label_word.capitalize()} knew the hill was waiting for careful feet.'
    )


def worry(world: World, helper: Entity, child: Entity, helper_item: ObjectThing, hill: Hill) -> None:
    pred = predict(world, "slip")
    child.memes["worry"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{helper.id} touched {child.pronoun("possessive")} shoulder and said, "Let us take the slow steps. This {hill.path_word} is slick in places."'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(f"{helper.id} nodded toward the wobbling {helper_item.label} and tucked it closer.")


def slip_and_pause(world: World, child: Entity, helper: Entity, hill: Hill) -> None:
    child.memes["shock"] += 1
    world.say(
        f"{child.id} looked down, breathed fast, and froze for a second."
    )
    world.say(
        f"Then {helper.id} held {child.pronoun('possessive')} hand, and the two of them stood still until the fear passed."
    )


def transformation(world: World, child: Entity, helper: Entity, hill: Hill, response: Response, gift: ObjectThing) -> None:
    child.memes["fear"] = 0.0
    child.memes["bravery"] += 1
    helper.memes["care"] += 1
    world.say(
        f'Instead of hurrying, {helper.id} used {response.method}.'
    )
    world.say(
        f'They changed the way they climbed: slower steps, a steadier grip, and a little song to keep their rhythm.'
    )
    gift.meters["safe"] += 1
    world.say(
        f"The hill did not seem mean anymore. It seemed like part of the adventure."
    )


def reconciliation(world: World, child: Entity, helper: Entity, neighbor: Entity, response: Response, gift: ObjectThing) -> None:
    child.memes["love"] += 1
    helper.memes["love"] += 1
    neighbor.memes["joy"] += 1
    world.say(
        f'At the top, the neighbor opened the gate with a surprised smile.'
    )
    world.say(
        f"{child.id} handed over {gift.phrase}, and {helper.id} explained why they had gone so slowly."
    )
    world.say(
        f'The neighbor laughed kindly, thanked them for coming, and invited them in for tea.'
    )
    world.say(
        f'By then, {child.id} was smiling again, and {helper.id} was too; the little worry had turned into a warm memory.'
    )


def tale(hill: Hill, guide: str, child_name: str, child_gender: str, helper_name: str, helper_gender: str, gift: ObjectThing, helper_item: ObjectThing, response: Response) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    neighbor = world.add(Entity(id="Neighbor", kind="character", type="woman", role="neighbor", label="the neighbor"))
    path = world.add(Entity(id="path", type="path", label=hill.label))
    world.add_obj(gift)
    world.add_obj(helper_item)
    world.facts["hill_cfg"] = hill
    world.facts["guide"] = guide
    world.facts["gift"] = gift
    world.facts["helper_item"] = helper_item
    world.facts["response"] = response
    setup(world, child, helper, hill, gift)
    world.para()
    foreshadow(world, child, hill, helper_item)
    worry(world, helper, child, helper_item, hill)
    world.para()
    _do_bad_step(world)
    slip_and_pause(world, child, helper, hill)
    world.para()
    transformation(world, child, helper, hill, response, gift)
    world.para()
    reconciliation(world, child, helper, neighbor, response, gift)
    world.facts.update(child=child, helper=helper, neighbor=neighbor, path=path, outcome="reconciled")
    return world


HILLS = {
    "steep_hill_path": Hill("steep_hill_path", "the steep hill path", True, True, "the path", "the steep path", "the view", tags={"hill", "path", "steep", "lush"}),
    "gentle_lane": Hill("gentle_lane", "the lane above the garden", True, False, "the lane", "the gentle lane", "the view", tags={"hill", "path", "lush"}),
}

GIFT_ITEMS = {
    "basket": ObjectThing("basket", "basket", "a basket of warm rolls", "gift", helpful=True, tags={"gift", "basket"}),
    "jam": ObjectThing("jam", "jam jar", "a jar of berry jam", "gift", helpful=True, tags={"gift", "jam"}),
    "flowers": ObjectThing("flowers", "bundle of flowers", "a bundle of wildflowers", "gift", helpful=True, tags={"gift", "flowers"}),
}

HELPER_ITEMS = {
    "lantern": ObjectThing("lantern", "lantern", "a little lantern", "tool", helpful=True, gives_light=True, tags={"light", "lantern"}),
    "cane": ObjectThing("cane", "walking stick", "a smooth walking stick", "tool", helpful=True, gives_balance=True, tags={"cane", "balance"}),
    "shawl": ObjectThing("shawl", "shawl", "a soft shawl", "tool", helpful=True, tags={"shawl"}),
}

RESPONSES = {
    "slow_steps": Response("slow_steps", 3, "held hands and took slow steps", "rushed ahead anyway", "They took slow steps, and that kept the climb calm."),
    "counting": Response("counting", 2, "counted each stone together", "lost their footing in a rush", "Counting each stone helped them steady themselves and keep going."),
    "pause_breathe": Response("pause_breathe", 2, "paused to breathe and listen", "kept climbing in a panic", "Pausing to breathe helped the worry fade."),
}

NAMES_GIRL = ["Lily", "Maya", "Nora", "Ava", "Iris", "Zoe", "Ella"]
NAMES_BOY = ["Ben", "Theo", "Finn", "Eli", "Noah", "Leo", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, hill in HILLS.items():
        for gid, gift in GIFT_ITEMS.items():
            for rid, response in RESPONSES.items():
                if hill.steep and gift.helpful and response.sense >= SENSE_MIN:
                    combos.append((hid, gid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a lush steep hill path, foreshadowing, transformation, reconciliation.")
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--gift", choices=GIFT_ITEMS)
    ap.add_argument("--helper-item", choices=HELPER_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing an underpowered response.)")
    combos = [c for c in valid_combos()
              if (args.hill is None or c[0] == args.hill)
              and (args.gift is None or c[1] == args.gift)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hill, gift, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper = args.helper or rng.choice(["Rose", "Mia", "Evan", "Owen"])
    helper_item = args.helper_item or rng.choice(sorted(HELPER_ITEMS))
    return StoryParams(hill, "lush", child, child_gender, helper, helper_gender, gift, helper_item, response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hill = f["hill_cfg"]
    return [
        f'Write a heartwarming story set on {hill.label} that includes the word "lush".',
        f"Tell a story about a child and a helper climbing a steep hill path, where a small scare leads to a kinder plan and a warm reconciliation.",
        f"Write a gentle story with foreshadowing, transformation, and reconciliation on {hill.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    hill = f["hill_cfg"]
    gift = f["gift"]
    helper_item = f["helper_item"]
    response = f["response"]
    return [
        QAItem(
            question="What was the setting of the story?",
            answer=f"It was set on {hill.label}, with lush plants and a steep path that asked for careful steps. The place mattered because it made the climb feel small and serious at the same time."
        ),
        QAItem(
            question=f"What was foreshadowed before the slip?",
            answer=f"The story foreshadowed trouble when the stones leaned sideways and {helper_item.label} wobbled in the wind. That little warning made the later slip feel believable instead of sudden."
        ),
        QAItem(
            question="How did the story transform after the scare?",
            answer=f"{helper.id} changed the climb by slowing down, taking steadier steps, and using {response.method}. The fear turned into focus, so the same path felt kinder."
        ),
        QAItem(
            question="How were the characters reconciled at the end?",
            answer=f"{child.id} and {helper.id} reached the neighbor together, shared {gift.phrase}, and smiled again. The warm invitation inside showed that the worry had passed and their bond was calm once more."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hill_cfg"].tags) | set(world.facts["gift"].tags) | set(world.facts["helper_item"].tags)
    out: list[QAItem] = []
    if "lush" in tags:
        out.append(QAItem("What does lush mean?", "Lush means full of healthy, thick, growing plants. It often makes a place look soft, green, and alive."))
    if "steep" in tags:
        out.append(QAItem("Why can a steep hill be hard to climb?", "A steep hill takes more careful steps because the ground rises quickly. People may need to slow down and hold on tighter."))
    if "gift" in tags:
        out.append(QAItem("Why do people bring gifts to a neighbor?", "People bring gifts to be kind and to show they care. A small gift can help someone feel remembered and welcomed."))
    if "light" in tags:
        out.append(QAItem("What is a lantern for?", "A lantern gives light so people can see in the dark. It is helpful on paths, porches, or camping trips."))
    if "balance" in tags:
        out.append(QAItem("What does a walking stick help with?", "A walking stick can help a person balance and feel steadier. It is useful on uneven ground."))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    for o in world.objects.values():
        meters = {k: v for k, v in o.meters.items() if v}
        if meters:
            lines.append(f"  {o.id:8} ({o.kind:10}) meters={dict(meters)}")
    return "\n".join(lines)


def explain_rejection(hill: Hill, gift: ObjectThing) -> str:
    if not hill.steep:
        return "(No story: the hill is not steep enough for the foreshadowing-and-transformation arc.)"
    if not gift.helpful:
        return "(No story: the chosen item does not support the climb in a believable way.)"
    return "(No story: this combination does not support the heartwarming hill-path arc.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid, h in HILLS.items():
        lines.append(asp.fact("hill", hid))
        if h.lush:
            lines.append(asp.fact("lush", hid))
        if h.steep:
            lines.append(asp.fact("steep", hid))
    for oid, o in GIFT_ITEMS.items():
        lines.append(asp.fact("gift", oid))
        if o.helpful:
            lines.append(asp.fact("helpful", oid))
    for oid, o in HELPER_ITEMS.items():
        lines.append(asp.fact("helper_item", oid))
        if o.gives_light:
            lines.append(asp.fact("gives_light", oid))
        if o.gives_balance:
            lines.append(asp.fact("gives_balance", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, G, R) :- hill(H), steep(H), gift(G), helpful(G), response(R), sense(R, S), sense_min(M), S >= M.
foreshadow(H) :- lush(H), steep(H).
transform(R) :- response(R), sense(R, S), sense_min(M), S >= M.
reconcile(H, G) :- valid(H, G, _).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(hill=None, gift=None, helper_item=None, response=None, child=None, child_gender=None, helper=None, helper_gender=None, seed=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"FAIL: generation smoke test crashed: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tale(HILLS[params.hill], params.guide, params.child, params.child_gender, params.helper, params.helper_gender, GIFT_ITEMS[params.gift], HELPER_ITEMS[params.helper_item], RESPONSES[params.response])
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


CURATED = [
    StoryParams("steep_hill_path", "lush", "Lily", "girl", "Mia", "mother", "basket", "lantern", "slow_steps"),
    StoryParams("steep_hill_path", "lush", "Ben", "boy", "Dad", "father", "jam", "cane", "counting"),
    StoryParams("steep_hill_path", "lush", "Nora", "girl", "Grandma", "grandmother", "flowers", "shawl", "pause_breathe"),
]


def resolve_random_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hill = args.hill or "steep_hill_path"
    gift = args.gift or rng.choice(list(GIFT_ITEMS))
    response = args.response or rng.choice(list(RESPONSES))
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError("(Refusing an underpowered response.)")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or resolve_random_name(rng, child_gender)
    helper_gender = args.helper_gender or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper = args.helper or rng.choice(["Rose", "Maya", "Evan", "Noah"])
    helper_item = args.helper_item or rng.choice(list(HELPER_ITEMS))
    if args.hill and args.gift:
        if not hazard_at_risk(HILLS[args.hill], GIFT_ITEMS[args.gift]):
            raise StoryError(explain_rejection(HILLS[args.hill], GIFT_ITEMS[args.gift]))
    return StoryParams(hill, "lush", child, child_gender, helper, helper_gender, gift, helper_item, response)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming steep hill path storyworld.")
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--gift", choices=GIFT_ITEMS)
    ap.add_argument("--helper-item", choices=HELPER_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father", "grandmother", "grandfather"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show foreshadow/1.\n#show transform/1.\n#show reconcile/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
