#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pollute_doohicky_misunderstanding_space_adventure.py
===================================================================================

A standalone storyworld for a tiny Space Adventure tale built from the seed words
"pollute" and "doohicky", with a misunderstanding beat.

Premise
-------
Two young space explorers are on a moon base with a strange little doohicky.
One child misreads what it does and thinks it will pollute the clean air. The
other child and a calm grown-up explain the mix-up, and the doohicky turns out
to be a helpful machine that keeps the dome safe and bright.

The world is small and classical:
- typed entities with physical meters and emotional memes
- state changes drive the prose
- a simple forward rule engine
- a reasonableness gate plus an inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA

The story always has a clear beginning, a misunderstanding-driven middle turn,
and an ending image showing what changed.
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
    detail: str
    backdrop: str
    affordance: str
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
class Device:
    id: str
    label: str
    phrase: str
    purpose: str
    misunderstood_as: str
    effect: str
    safe: bool = True
    spread: int = 0
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
    sense: int
    text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["alarm"] >= THRESHOLD:
            sig = ("alert", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get("dome").memes["worry"] += 1
            out.append("__alert__")
    return out


CAUSAL_RULES = [Rule("alert", _r_alert)]


def propagate(world: World, narrate: bool = True) -> None:
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


def predict_device(world: World, device: Device) -> dict:
    sim = world.copy()
    _do_misunderstanding(sim, narrate=False)
    return {
        "worry": sim.get("dome").memes["worry"],
        "spark": sim.get("device").meters["spark"],
        "trust": sim.get("pilot").memes["trust"],
    }


def _do_misunderstanding(world: World, narrate: bool = True) -> None:
    device = world.get("device")
    device.meters["spark"] += 1
    world.get("navigator").memes["alarm"] += 1
    propagate(world, narrate=narrate)


def discuss(world: World, hero: Entity, friend: Entity, device: Device) -> None:
    world.say(
        f"On the bright moon base, {hero.id} and {friend.id} floated past "
        f"{world.setting.backdrop}. {world.setting.detail}"
    )
    world.say(
        f"In the middle of the dome sat a small doohicky -- {device.phrase} -- "
        f"meant to {device.purpose}."
    )
    world.say(
        f'"Look at that," {hero.id} said. "I think it might {device.misunderstood_as}."'
    )
    world.say(
        f'{friend.id} blinked at the blinking lights. "No, it looks like it '
        f'wants to help."'
    )


def warn(world: World, friend: Entity, hero: Entity, device: Device) -> None:
    pred = predict_device(world, device)
    friend.memes["care"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{friend.id} pointed at the little vents. "
        f'"If it {device.misunderstood_as}, the dome air could get bad, '
        f'and we would have to call for help."'
    )


def misunderstand(world: World, hero: Entity, device: Device) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f"{hero.id} backed away. For a moment, the shiny doohicky looked like a "
        f"troublemaker instead of a helper."
    )


def explain(world: World, parent: Entity, hero: Entity, friend: Entity, device: Device) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"Then {parent.id} floated over and smiled. "
        f'"That doohicky does not {device.misunderstood_as}," {parent.pronoun()} said. '
        f'"It does the opposite. It helps keep the dome clean so nothing can pollute the air."'
    )
    world.say(
        f"{hero.id} leaned closer and watched the soft lights. The doohicky hummed "
        f"and opened its tiny filter fins."
    )


def repair(world: World, parent: Entity, device: Device) -> None:
    device.meters["spark"] = 0
    world.get("dome").memes["worry"] = 0
    world.say(
        f"{parent.id} tapped the button on the doohicky, and it lit up like a "
        f"little star. A clean breeze drifted through the dome."
    )


def ending(world: World, hero: Entity, friend: Entity, device: Device) -> None:
    for e in (hero, friend):
        e.memes["joy"] += 1
    world.say(
        f"In the end, the base stayed bright and safe. {hero.id} and {friend.id} "
        f"watched the doohicky hum quietly beside the moon plants, keeping the air "
        f"fresh instead of letting anything pollute it."
    )


def tell(setting: Setting, device: Device,
         hero_name: str = "Mina", hero_gender: str = "girl",
         friend_name: str = "Ivo", friend_gender: str = "boy",
         parent_gender: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Commander", kind="character", type=parent_gender, role="parent", label="the commander"))
    dome = world.add(Entity(id="dome", type="place", label="the dome"))
    tool = world.add(Entity(id="device", type="device", label=device.label))
    hero.memes["curiosity"] = 1
    friend.memes["watchfulness"] = 1

    discuss(world, hero, friend, device)
    world.para()
    warn(world, friend, hero, device)
    misunderstand(world, hero, device)
    world.para()
    explain(world, parent, hero, friend, device)
    repair(world, parent, device)
    world.para()
    ending(world, hero, friend, device)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        dome=dome,
        tool=tool,
        device_cfg=device,
        outcome="resolved",
    )
    return world


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    device: Device = f["device_cfg"]
    return [
        f'Write a Space Adventure story for a 3-to-5-year-old that includes the word "{device.id}" and the word "pollute".',
        f"Tell a gentle moon-base story where {f['hero'].id} misunderstands a doohicky and thinks it will pollute the air, but the mix-up gets explained.",
        f'Write a child-friendly space story about a tiny machine, a misunderstanding, and a calm ending that keeps the dome clean.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    parent: Entity = f["parent"]
    device: Device = f["device_cfg"]
    qa = [
        (
            "What did the children see in the dome?",
            f"They saw a small doohicky sitting in the moon dome. It was meant to {device.purpose}, so it was there to help the base stay tidy and safe."
        ),
        (
            "What did {0} worry about?".format(hero.id),
            f"{hero.id} worried that the doohicky would {device.misunderstood_as}. That was the misunderstanding, because the machine was actually made to keep the air clean."
        ),
        (
            "How was the misunderstanding fixed?",
            f"The commander explained what the doohicky really did. After that, {hero.id} and {friend.id} understood that it helped instead of causing trouble."
        ),
        (
            "How did the story end?",
            f"It ended with the dome staying bright and safe. The doohicky hummed quietly, and nothing polluted the air."
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "pollute": [
        ("What does it mean to pollute something?",
         "To pollute something means to make it dirty or unsafe, like when bad stuff gets into air or water.")
    ],
    "doohicky": [
        ("What is a doohicky?",
         "A doohicky is a funny word for a machine or gadget when you do not want to name it exactly.")
    ],
    "space": [
        ("Why do space bases need clean air?",
         "People need clean air to breathe, so space bases use special machines to keep the air safe.")
    ],
    "filter": [
        ("What does a filter do?",
         "A filter catches little bits of dirt and lets cleaner air or water pass through.")
    ],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["device_cfg"].tags)
    tags |= {"pollute", "doohicky", "space", "filter"}
    out: list[tuple[str, str]] = []
    for key in ["pollute", "doohicky", "space", "filter"]:
        if key in tags and key in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


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


SETTING = Setting(
    id="moon_base",
    place="the moon base",
    detail="The silver hallway curved past a glass dome full of little bean plants.",
    backdrop="the white rocket bay",
    affordance="keep the air clean",
)

DEVICES = {
    "doohicky": Device(
        id="doohicky",
        label="little doohicky",
        phrase="a tiny doohicky with blue lights",
        purpose="clean the dome air",
        misunderstood_as="pollute the air",
        effect="cleans",
        safe=True,
        spread=0,
        tags={"doohicky", "pollute", "space"},
    ),
    "filterwheel": Device(
        id="filterwheel",
        label="filter wheel",
        phrase="a spinning filter wheel with a shiny cover",
        purpose="catch dust before it drifts around",
        misunderstood_as="pollute the hallway",
        effect="filters",
        safe=True,
        spread=0,
        tags={"filter", "space"},
    ),
}

@dataclass
class StoryParams:
    device: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent_gender: str
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
        device="doohicky",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Ivo",
        friend_gender="boy",
        parent_gender="mother",
        seed=None,
    ),
    StoryParams(
        device="filterwheel",
        hero_name="Nia",
        hero_gender="girl",
        friend_name="Oren",
        friend_gender="boy",
        parent_gender="father",
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str]]:
    return [(k,) for k, v in DEVICES.items() if v.safe]


def explain_rejection(device: Device) -> str:
    return f"(No story: the chosen device '{device.id}' would not support a gentle misunderstanding tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space Adventure storyworld about a misunderstanding with a doohicky."
    )
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    device = args.device or rng.choice(sorted(DEVICES))
    if device not in DEVICES:
        raise StoryError("Unknown device.")
    if not DEVICES[device].safe:
        raise StoryError(explain_rejection(DEVICES[device]))
    return StoryParams(
        device=device,
        hero_name=args.hero_name or rng.choice(["Mina", "Nova", "Luna", "Pia"]),
        hero_gender="girl",
        friend_name=args.friend_name or rng.choice(["Ivo", "Rex", "Sol", "Timo"]),
        friend_gender="boy",
        parent_gender=args.parent_gender or rng.choice(["mother", "father"]),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.device not in DEVICES:
        raise StoryError("Unknown device.")
    world = tell(
        SETTING,
        DEVICES[params.device],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_gender=params.parent_gender,
    )
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


ASP_RULES = r"""
safe_device(doohicky).
safe_device(filterwheel).
misunderstood(D) :- safe_device(D).
outcome(resolved) :- misunderstood(D).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", SETTING.id)]
    for k, v in DEVICES.items():
        lines.append(asp.fact("device", k))
        if v.safe:
            lines.append(asp.fact("safe", k))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_device/1."))
    return sorted(set(asp.atoms(model, "safe_device")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show safe_device/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("safe devices:", ", ".join(k for (k,) in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
