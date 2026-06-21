#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tug_sis_bravery_adventure.py
=============================================================

A small standalone storyworld about a brave little adventure between two
siblings on a windy trail. One child wants to keep tugging a rope to reach a
far thing; the sister warns about a drop, and bravery turns the moment into a
safe, exciting climb.

The world uses a tiny simulated model with physical meters and emotional memes,
a forward causal pass, a Python reasonableness gate, and an inline ASP twin.
It supports the standard Storyweavers CLI modes plus QA and trace output.
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

BRAVERY_MIN = 1.0
TENSION_MIN = 1.0
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
        female = {"girl", "mother", "mom", "sister", "woman"}
        male = {"boy", "father", "dad", "brother", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"sister": "sis", "brother": "bro", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    look: str
    goal: str
    drop: str
    wind: str
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
class RopeThing:
    id: str
    label: str
    phrase: str
    use: str
    risky: bool = False
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
class HelperTool:
    id: str
    label: str
    phrase: str
    glow: str
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
class Response:
    id: str
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_fear(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["danger"] >= THRESHOLD and (("fear",) not in world.fired):
            world.fired.add(("fear",))
            for kid in list(world.entities.values()):
                if kid.role in {"sis", "tug"}:
                    kid.memes["fear"] += 1
            out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                lines.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in lines:
            world.say(s)
    return lines


def valid_combo(setting: Setting, rope: RopeThing, response: Response) -> bool:
    return rope.risky and response.sense >= 1 and setting.goal and setting.drop


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for rid, r in ROPE.items():
            for respid, resp in RESPONSES.items():
                if valid_combo(s, r, resp):
                    combos.append((sid, rid, respid))
    return combos


def risk_predict(world: World, setting: Setting, rope: RopeThing) -> bool:
    sim = world.copy()
    sim.get("rope").meters["pull"] += 1
    if rope.risky:
        sim.get("drop").meters["danger"] += 1
    return sim.get("drop").meters["danger"] >= THRESHOLD


def tug_attempt(world: World, tug: Entity, sis: Entity, rope: RopeThing, setting: Setting) -> None:
    tug.memes["bravery"] += 1
    world.say(
        f"On a bright day, {tug.id} and {sis.id} headed up the trail for {setting.place}. "
        f"{setting.look}"
    )
    world.say(
        f'{tug.id} grinned and gave the rope a tug. "I can reach the {setting.goal}!"'
    )
    world.say(
        f'"Wait, {tug.id}," {sis.id} said. "That path ends at {setting.drop}. '
        f"We should be careful."'
    )


def choose_brave(world: World, tug: Entity, sis: Entity, rope: RopeThing) -> None:
    tug.memes["bravery"] += 1
    sis.memes["bravery"] += 0.5
    world.say(
        f"{tug.id} took a deep breath. The brave tug felt shaky, but {tug.id} kept going."
    )


def danger_turn(world: World, setting: Setting, rope: RopeThing) -> None:
    world.get("drop").meters["danger"] += 1
    world.get("trail").meters["strain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The rope pulled tight, and the wind worried the trail near {setting.drop}. "
        f"For one scary moment, the edge looked wobbly."
    )


def sister_wise(world: World, sis: Entity) -> None:
    sis.memes["caution"] += 1
    world.say(f"{sis.id} kept her footing and shouted for {sis.id.lower()} to slow down.")


def safe_fix(world: World, response: Response, helper: HelperTool, setting: Setting) -> None:
    world.get("drop").meters["danger"] = 0
    world.say(
        f"Then a grown-up came running with {helper.phrase} that {helper.glow}. "
        f"In a flash {response.text.replace('{setting}', setting.goal)}."
    )


def finish_adventure(world: World, tug: Entity, sis: Entity, setting: Setting, rope: RopeThing) -> None:
    tug.memes["joy"] += 1
    sis.memes["joy"] += 1
    world.say(
        f"After that, {tug.id} and {sis.id} crossed the trail together and reached {setting.goal}. "
        f"This time they took the safe path, and the brave tug turned into a brave climb."
    )


def tell(setting: Setting, rope: RopeThing, response: Response, helper: HelperTool) -> World:
    world = World()
    tug = world.add(Entity(id="tug", kind="character", type="boy", role="tug", traits=["brave"]))
    sis = world.add(Entity(id="sis", kind="character", type="girl", role="sis", traits=["wise"]))
    world.add(Entity(id="trail", type="trail", label="the trail"))
    world.add(Entity(id="drop", type="drop", label=setting.drop))
    world.add(Entity(id="rope", type="rope", label=rope.label))

    tug.memes["bravery"] = 1.5
    sis.memes["bravery"] = 0.5

    tug_attempt(world, tug, sis, rope, setting)
    world.para()
    choose_brave(world, tug, sis, rope)
    danger_turn(world, setting, rope)
    sister_wise(world, sis)
    world.para()
    safe_fix(world, response, helper, setting)
    finish_adventure(world, tug, sis, setting, rope)

    world.facts.update(
        tug=tug,
        sis=sis,
        setting=setting,
        rope=rope,
        response=response,
        helper=helper,
        danger=world.get("drop").meters["danger"],
    )
    return world


SETTINGS = {
    "ridge": Setting(
        id="ridge",
        place="the ridge path",
        look="The rocks were sharp, the grass was thin, and the wind whistled like a kite string.",
        goal="the blue flag on the hilltop",
        drop="the steep drop",
        wind="windy",
        tags={"adventure", "ridge"},
    ),
    "cave": Setting(
        id="cave",
        place="the cave trail",
        look="The stones were slick, and the cave mouth looked dark and thrilling.",
        goal="the shiny lantern marker",
        drop="the dark hole",
        wind="cool",
        tags={"adventure", "cave"},
    ),
    "dock": Setting(
        id="dock",
        place="the dock walk",
        look="The boards creaked over the water, and gulls cried overhead.",
        goal="the red lookout bell",
        drop="the water below",
        wind="breezy",
        tags={"adventure", "dock"},
    ),
}

ROPE = {
    "kite": RopeThing(
        id="kite",
        label="kite rope",
        phrase="the bright kite rope",
        use="reach the kite",
        risky=True,
        tags={"rope", "kite"},
    ),
    "tugrope": RopeThing(
        id="tugrope",
        label="tug rope",
        phrase="the long tug rope",
        use="pull the cart",
        risky=True,
        tags={"rope", "tug"},
    ),
}

HELPERS = {
    "lantern": HelperTool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        glow="glowed warm and steady",
        tags={"lantern"},
    ),
    "flashlight": HelperTool(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="shone bright as a star",
        tags={"flashlight"},
    ),
}

RESPONSES = {
    "hold_fast": Response(
        id="hold_fast",
        power=2,
        sense=2,
        text="held the rope fast, pointed the way with the lantern, and guided them safely along the trail",
        fail="tried to hold the rope fast, but the trail had already slipped too much",
        qa_text="held the rope fast and guided them safely along the trail",
        tags={"safety"},
    ),
    "back_away": Response(
        id="back_away",
        power=3,
        sense=3,
        text="backed them away from the edge, then helped them cross the safe part of the trail",
        fail="backed them away, but the danger still spread before anyone could stop it",
        qa_text="backed them away from the edge and helped them cross safely",
        tags={"safety"},
    ),
}

@dataclass
class StoryParams:
    setting: str = "ridge"
    rope: str = "kite"
    response: str = "hold_fast"
    helper: str = "lantern"
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


CURATED = [
    StoryParams(
        setting="ridge", rope="kite", response="hold_fast", helper="lantern", seed=101
    ),
    StoryParams(
        setting="cave", rope="tugrope", response="back_away", helper="flashlight", seed=202
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f'Write an adventure story that includes the words "tug" and "sis" on {setting.place}.',
        f"Tell a brave sibling story where tug wants to keep tugging the rope, but sis warns about the danger.",
        f'Write a short story for a child about bravery, a rope tug, and a safe ending in the {setting.id} setting.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting = f["setting"]
    qa = [
        (
            "Who are the main characters?",
            "The main characters are tug and sis. They are siblings on a small adventure together.",
        ),
        (
            "Why did sis worry?",
            f"Sis worried because the trail ended at {setting.drop}, and tugging harder could make the edge unsafe. She wanted them to stay brave without being reckless.",
        ),
        (
            "What changed by the end?",
            f"By the end, tug and sis reached {setting.goal} safely. The scary wobble passed, and their adventure became a careful success.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is bravery?",
            "Bravery is doing something scary while still being careful and thinking about safety. A brave child can slow down, listen, and keep going wisely.",
        ),
        (
            "What should you do if a path looks unsafe?",
            "You should stop, look, and call for a grown-up if needed. Staying safe matters more than reaching a place fast.",
        ),
        (
            "What can a flashlight do?",
            "A flashlight gives bright light without a flame. It helps people see in the dark while keeping an adventure safe.",
        ),
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


def explain_rejection(rope: RopeThing) -> str:
    return f"(No story: {rope.label} is not a plausible adventure hazard here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about tug, sis, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rope", choices=ROPE)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.rope and args.rope not in ROPE:
        raise StoryError(explain_rejection(ROPE[args.rope]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rope is None or c[1] == args.rope)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rope, response = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, rope=rope, response=response, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.rope not in ROPE:
        raise StoryError(f"Unknown rope: {params.rope}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    world = tell(SETTINGS[params.setting], ROPE[params.rope], RESPONSES[params.response], HELPERS[params.helper])
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


ASP_RULES = r"""
valid(S,R,Resp) :- setting(S), rope(R), response(Resp), risky(R), sense(Resp, N), N >= 1.
brave(T) :- bravery(T), T = tug.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in ROPE.items():
        lines.append(asp.fact("rope", rid))
        if r.risky:
            lines.append(asp.fact("risky", rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("bravery", "tug"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP valid combos match Python ({len(valid_combos())}).")
    else:
        rc = 1
        print("Mismatch between ASP and Python valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"Smoke test failed: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
