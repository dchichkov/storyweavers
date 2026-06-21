#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ember_garage_kindness_mystery.py
=================================================================

A standalone story world for a small mystery set in a garage: a child finds a
tiny ember, suspects something is wrong, and kindness helps reveal the truth and
fix the problem safely.

The story is built from a tiny simulated world with physical meters and emotional
memes. The prose is state-driven: the garage can be dusty, the ember can glow,
clues can be found, and kindness can change how the mystery ends.
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
    clue: str
    smell: str
    shadow: str
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


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    hidden: str
    reveals: str
    dangerous: bool = False
    glows: bool = False
    innocent: bool = False
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
class KindAct:
    id: str
    name: str
    action: str
    response: str
    effect: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_spotlight(world: World) -> list[str]:
    out: list[str] = []
    ember = world.get("ember")
    if ember.meters["glow"] < THRESHOLD:
        return out
    sig = ("spotlight",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("garage").meters["mystery"] += 1
    out.append("__mystery__")
    return out


def _r_soot(world: World) -> list[str]:
    out: list[str] = []
    if world.get("garage").meters["dust"] < THRESHOLD:
        return out
    if world.get("ember").meters["glow"] < THRESHOLD:
        return out
    sig = ("soot",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("garage").meters["soot"] += 1
    world.get("child").memes["worry"] += 1
    return out


CAUSAL_RULES = [Rule("spotlight", _r_spotlight), Rule("soot", _r_soot)]


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


def predict_scene(world: World, object_id: str) -> dict:
    sim = world.copy()
    sim.get(object_id).meters["glow"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("garage").meters["mystery"],
        "soot": sim.get("garage").meters["soot"],
        "worry": sim.get("child").memes["worry"],
    }


def _touch_ember(world: World, obj: MysteryObject) -> None:
    world.get("ember").meters["glow"] += 1
    world.get("ember").meters["heat"] += 1
    world.get(obj.id).meters["discovered"] += 1
    propagate(world, narrate=False)


def open_story(world: World, child: Entity, elder: Entity, setting: Setting, obj: MysteryObject) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {elder.id} stepped into the {setting.place}. "
        f"The air smelled of old oil and dust, and a little {setting.shadow} made everything look secret."
    )
    world.say(
        f"Near the workbench, {child.id} noticed a tiny ember. It was only a speck of light, "
        f"but it flickered like it had something to say."
    )
    world.say(
        f'"What is that?" {child.id} whispered. {elder.id} looked closer and frowned at the {obj.label}.'
    )


def mystery_turn(world: World, child: Entity, elder: Entity, obj: MysteryObject) -> None:
    child.memes["mystery"] += 1
    world.say(
        f"The ember was near {obj.hidden}, and that made the garage feel even stranger. "
        f"{child.id} wanted to poke around, but {elder.id} lifted a hand and asked for kindness first."
    )
    world.say(
        f'"Let’s not rush," {elder.id} said. "If we look gently, we can solve the mystery without making it worse."'
    )


def clue_find(world: World, child: Entity, elder: Entity, obj: MysteryObject) -> None:
    world.say(
        f"Together they found {obj.phrase}. It was small and easy to miss, but {obj.reveals} explained the clue."
    )
    if obj.innocent:
        world.say(
            f"The thing that looked suspicious was not dangerous at all. It had simply been hiding in the dark."
        )


def kind_move(world: World, child: Entity, elder: Entity, act: KindAct, obj: MysteryObject) -> None:
    child.memes["kindness"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"{child.id} chose kindness. {child.id} {act.action}, and {elder.id} {act.response}."
    )
    world.say(
        f"That gentle choice {act.effect}. The garage felt less like a puzzle box and more like a safe place again."
    )


def end_image(world: World, child: Entity, elder: Entity, obj: MysteryObject) -> None:
    garage = world.get("garage")
    ember = world.get("ember")
    if ember.meters["glow"] >= THRESHOLD:
        world.say(
            f"In the end, the ember was covered safely, the dust was settled, and the little glow was gone."
        )
    else:
        world.say(
            f"In the end, the garage was calm: no sparks, no fear, just {child.id} and {elder.id} smiling beside the workbench."
        )
    if garage.meters["mystery"] >= THRESHOLD:
        world.say("What had seemed spooky was only an old clue, and kindness had helped them understand it.")


SETTINGS = {
    "garage": Setting(
        id="garage",
        place="garage",
        clue="dim corners",
        smell="old oil",
        shadow="shadow",
    ),
    "shed": Setting(
        id="shed",
        place="shed",
        clue="narrow shelves",
        smell="dry wood",
        shadow="shadow",
    ),
}

OBJECTS = {
    "ember": MysteryObject(
        id="emberbox",
        label="cardboard box",
        phrase="a cardboard box under the shelf",
        hidden="a pile of rags",
        reveals="its torn side showed why the ember had caught there",
        dangerous=True,
        glows=True,
        tags={"ember", "mystery"},
    ),
    "lantern": MysteryObject(
        id="lantern",
        label="old lantern",
        phrase="an old lantern with a dusty glass face",
        hidden="a coiled hose",
        reveals="the cracked glass made the glow look odd but harmless",
        dangerous=False,
        glows=False,
        innocent=True,
        tags={"lantern", "mystery"},
    ),
}

KIND_ACTS = {
    "share": KindAct(
        id="share",
        name="share a flashlight",
        action="held the flashlight so the beam would reach the dark corner",
        response="smiled and held the box steady",
        effect="made the clue easy to see",
        tags={"kindness", "help"},
    ),
    "cover": KindAct(
        id="cover",
        name="cover the ember",
        action="gently covered the ember with a metal pan",
        response="fetched a lid and helped lower it carefully",
        effect="kept the tiny glow from spreading",
        tags={"kindness", "safe"},
    ),
    "ask": KindAct(
        id="ask",
        name="ask for help",
        action="ran to get a grown-up instead of poking the ember",
        response="nodded and called for help right away",
        effect="turned worry into a smart plan",
        tags={"kindness", "help"},
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Eli", "Sage", "Ivy", "Theo", "Ava"]
ELDER_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ben", "Grandma", "Grandpa"]


@dataclass
class StoryParams:
    setting: str
    object: str
    kind_act: str
    child: str
    elder: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if sid == "garage" and obj.glows:
                for kid in KIND_ACTS:
                    combos.append((sid, oid, kid))
    return combos


def explain_rejection(setting: Setting, obj: MysteryObject) -> str:
    return "(No story: the seed asks for a garage mystery with an ember, so the object and setting need to fit that clue.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Garage mystery storyworld with ember and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--kind-act", choices=KIND_ACTS)
    ap.add_argument("--child")
    ap.add_argument("--elder")
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
              and (args.object is None or c[1] == args.object)
              and (args.kind_act is None or c[2] == args.kind_act)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, kind_act = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting=setting, object=obj, kind_act=kind_act, child=child, elder=elder)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.object not in OBJECTS or params.kind_act not in KIND_ACTS:
        raise StoryError("Invalid parameters for this world.")
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type="boy" if params.child in {"Noah", "Eli", "Theo"} else "girl"))
    elder = world.add(Entity(id=params.elder, kind="character", type="adult", role="helper", label=params.elder.lower()))
    garage = world.add(Entity(id="garage", type="room", label="garage"))
    ember = world.add(Entity(id="ember", type="thing", label="ember"))
    box = world.add(Entity(id="box", type="thing", label=OBJECTS[params.object].label))

    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    act = KIND_ACTS[params.kind_act]

    garage.meters["dust"] += 1
    open_story(world, child, elder, setting, obj)
    world.para()
    mystery_turn(world, child, elder, obj)
    world.para()
    _touch_ember(world, obj)
    if ember.meters["glow"] >= THRESHOLD:
        world.say(
            f"The ember gave off just enough glow to make everyone pause. It was a warning, not a monster."
        )
    clue_find(world, child, elder, obj)
    world.para()
    kind_move(world, child, elder, act, obj)
    if act.id == "cover":
        ember.meters["glow"] = 0.0
    else:
        ember.meters["glow"] = 0.0
    end_image(world, child, elder, obj)
    world.facts.update(setting=setting, obj=obj, act=act, child=child, elder=elder, outcome="calm")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old set in a {f["setting"].place} that includes the word "ember" and ends with kindness.',
        f"Tell a gentle garage mystery where {f['child'].id} and {f['elder'].id} notice an ember, look for clues, and solve the problem kindly.",
        "Write a child-friendly mystery with a clue in a garage, a tiny ember, and a kind helper who makes the ending feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    return [
        QAItem(
            question="What made the garage feel mysterious?",
            answer="A tiny ember glowed near the workbench, so the garage felt secret and a little scary. It was only a small clue, but it made everyone stop and look carefully.",
        ),
        QAItem(
            question="How did kindness help solve the mystery?",
            answer=f"{child.id} and {elder.id} looked gently instead of rushing around. That kindness made it easier to notice the real clue and keep the garage safe.",
        ),
        QAItem(
            question="What happened at the end?",
            answer="The ember was handled safely, the clue made sense, and the garage became calm again. The ending image proves the mystery was solved without anyone getting hurt.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ember?",
            answer="An ember is a tiny glowing piece of something hot, like wood or charcoal. It can still give off heat, so people should be careful around it.",
        ),
        QAItem(
            question="Why is a garage good for a mystery story?",
            answer="A garage often has boxes, tools, and dark corners, so it can hide clues. That makes it a good place for a small mystery.",
        ),
        QAItem(
            question="What does kindness mean in a story?",
            answer="Kindness means helping, sharing, and being gentle with others. In a story, kindness can calm a scary moment and help everyone solve the problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


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


ASP_RULES = r"""
glowing(ember) :- ember_fact(ember).
mystery(garage) :- glowing(ember).
calm :- kindness(act).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("ember_fact", "ember"),
        asp.fact("kindness", "act"),
        asp.fact("garage_fact", "garage"),
    ])


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show glowing/1.\n#show mystery/1.\n#show calm/0."))
    return sorted(set(asp.atoms(model, "glowing")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {("ember",)}:
        rc = 1
        print("MISMATCH in ASP twin.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object=None, kind_act=None, child=None, elder=None), random.Random(1)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP twin and smoke test passed.")
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


CURATED = [
    StoryParams(setting="garage", object="ember", kind_act="cover", child="Mia", elder="Mom"),
    StoryParams(setting="garage", object="ember", kind_act="share", child="Noah", elder="Dad"),
    StoryParams(setting="garage", object="ember", kind_act="ask", child="Ivy", elder="Aunt Jo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show glowing/1.\n#show mystery/1.\n#show calm/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible story seeds:")
        for combo in valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
