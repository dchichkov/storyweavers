#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/monger_porpoise_dialogue_sharing_heartwarming.py
=================================================================================

A small heartwarming storyworld about a market monger, a porpoise, and a kindly
act of sharing.

Premise
-------
A seaside monger is busy at the market when a porpoise appears near the pier,
upset and alone. Through gentle dialogue, the monger learns what the porpoise
needs, shares a simple offering, and the porpoise gives a gift back. The ending
proves the change with a warm shared scene.

This world intentionally stays small:
- typed entities with meters and memes
- a simulated world state that drives the prose
- dialogue and sharing as the main narrative instruments
- a reasonableness gate and inline ASP twin
- grounded Q&A from world state, not from rendered English

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/monger_porpoise_dialogue_sharing_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/monger_porpoise_dialogue_sharing_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/monger_porpoise_dialogue_sharing_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/monger_porpoise_dialogue_sharing_heartwarming.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/monger_porpoise_dialogue_sharing_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
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
KINDLY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    light: str
    sounds: str
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
class Need:
    id: str
    label: str
    phrase: str
    risk: str
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
class Gift:
    id: str
    label: str
    phrase: str
    warm: str
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
class StoryParams:
    setting: str
    need: str
    gift: str
    helper_name: str
    helper_type: str
    porpoise_name: str
    porpoise_type: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    p = world.get("porpoise")
    if helper.memes["kindness"] >= THRESHOLD and p.memes["lonely"] >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            p.memes["hope"] += 1
            helper.memes["hope"] += 1
            out.append("__soften__")
    return out


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    p = world.get("porpoise")
    if helper.meters["sharing"] >= THRESHOLD and p.meters["receiving"] >= THRESHOLD:
        sig = ("shared",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["warmth"] += 1
            p.memes["warmth"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("soften", _r_soften), Rule("shared", _r_shared)]


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


def reasonable_combo(setting: Setting, need: Need, gift: Gift) -> bool:
    return "monger" in setting.tags and "porpoise" in setting.tags and need.id in setting.tags and gift.id in setting.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for nid, n in NEEDS.items():
            for gid, g in GIFTS.items():
                if reasonable_combo(s, n, g):
                    combos.append((sid, nid, gid))
    return combos


def story_open(world: World, helper: Entity, p: Entity, setting: Setting) -> None:
    helper.memes["busyness"] += 1
    p.memes["lonely"] += 1
    world.say(
        f"{helper.id} worked at the {setting.place}, where the air smelled of salt "
        f"and the water shone softly. A porpoise waited near the edge, and the "
        f"{setting.light} made the morning glow."
    )
    world.say(f'"Hello there," {helper.id} called. "{p.id}, what do you need?"')


def story_answer(world: World, helper: Entity, p: Entity, need: Need) -> None:
    helper.memes["kindness"] += 1
    p.memes["trust"] += 1
    world.say(
        f'"I need {need.phrase}," {p.id} said quietly. "{need.risk} and I lost mine."'
    )
    world.say(
        f'{helper.id} nodded. "I can share mine," {helper.pronoun()} said. '
        f'"You do not have to be alone."'
    )


def share_gift(world: World, helper: Entity, p: Entity, gift: Gift) -> None:
    helper.meters["sharing"] += 1
    p.meters["receiving"] += 1
    helper.meters["gift"] += 1
    p.meters["gift"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} wrapped {gift.phrase} in a clean cloth and shared it with "
        f"{p.id}. {gift.warm.capitalize()}, it fit the moment just right."
    )


def thanks(world: World, helper: Entity, p: Entity) -> None:
    world.say(
        f'"Thank you," {p.id} said, smiling wide. "That was kind."'
    )
    world.say(
        f'"You made my day brighter too," {helper.id} answered, and both of them "
        f"looked calmer at once.'
    )


def ending_image(world: World, helper: Entity, p: Entity, gift: Gift, setting: Setting) -> None:
    helper.memes["warmth"] += 1
    p.memes["warmth"] += 1
    world.say(
        f"Before long, {helper.id} and {p.id} sat side by side at the {setting.place}, "
        f"sharing {gift.label} and watching the water move in gentle little lines."
    )
    world.say(
        f"The porpoise no longer looked lost. The monger no longer looked rushed. "
        f"They were simply there together, safe and glad to share."
    )


def tell(setting: Setting, need: Need, gift: Gift,
         helper_name: str = "Mira", helper_type: str = "woman",
         porpoise_name: str = "Pip", porpoise_type: str = "porpoise") -> World:
    world = World(setting)
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label="the monger", role="helper"))
    p = world.add(Entity(id=porpoise_name, kind="character", type=porpoise_type, label="the porpoise", role="porpoise"))
    world.add(Entity(id="stall", type="place", label=setting.place))

    helper.memes["hope"] = 0.0
    p.memes["hope"] = 0.0

    story_open(world, helper, p, setting)
    world.para()
    story_answer(world, helper, p, need)
    world.para()
    share_gift(world, helper, p, gift)
    thanks(world, helper, p)
    world.para()
    ending_image(world, helper, p, gift, setting)

    world.facts.update(
        helper=helper, porpoise=p, setting=setting, need=need, gift=gift,
        shared=helper.meters["sharing"] >= THRESHOLD,
        answered=p.memes["trust"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "harbor": Setting(id="harbor", place="harbor market", light="water", sounds="wave music", tags={"monger", "porpoise"}),
    "pier": Setting(id="pier", place="wooden pier", light="sunlight", sounds="gulls", tags={"monger", "porpoise"}),
    "dock": Setting(id="dock", place="little dock stall", light="morning", sounds="soft tides", tags={"monger", "porpoise"}),
}

NEEDS = {
    "fish": Need(id="fish", label="fish", phrase="a fish for breakfast", risk="my tummy is empty", tags={"fish", "monger"}),
    "net": Need(id="net", label="net", phrase="a net to guide me home", risk="I drifted away from my pod", tags={"net", "porpoise"}),
    "song": Need(id="song", label="song", phrase="a song to calm my heart", risk="the waves felt too big today", tags={"song", "porpoise"}),
}

GIFTS = {
    "small_fish": Gift(id="small_fish", label="small fish", phrase="a small fish", warm="fresh and kindly given", tags={"fish", "sharing"}),
    "warm_blanket": Gift(id="warm_blanket", label="warm blanket", phrase="a warm blanket", warm="soft and cozy", tags={"sharing", "net"}),
    "shell_charm": Gift(id="shell_charm", label="shell charm", phrase="a shell charm", warm="simple and bright", tags={"sharing", "song"}),
}

CURATED = [
    StoryParams(setting="harbor", need="fish", gift="small_fish", helper_name="Mira", helper_type="woman", porpoise_name="Pip", porpoise_type="porpoise"),
    StoryParams(setting="pier", need="net", gift="warm_blanket", helper_name="Nora", helper_type="woman", porpoise_name="Bobo", porpoise_type="porpoise"),
    StoryParams(setting="dock", need="song", gift="shell_charm", helper_name="Tess", helper_type="woman", porpoise_name="Sunny", porpoise_type="porpoise"),
]


def explain_rejection(setting: Setting, need: Need, gift: Gift) -> str:
    return "(No story: this combination does not fit the gentle market meeting.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming monger and porpoise storyworld with dialogue and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--porpoise")
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
              and (args.need is None or c[1] == args.need)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, need, gift = rng.choice(sorted(combos))
    helper_name = args.name or rng.choice(["Mira", "Nora", "Tess", "Lena"])
    porpoise_name = args.porpoise or rng.choice(["Pip", "Bobo", "Sunny", "Nim"])
    return StoryParams(
        setting=setting, need=need, gift=gift,
        helper_name=helper_name, helper_type="woman",
        porpoise_name=porpoise_name, porpoise_type="porpoise",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a monger named {f["helper"].id} and a porpoise named {f["porpoise"].id} that includes dialogue and sharing.',
        f"Tell a gentle seaside story where {f['helper'].id} helps a porpoise with {f['need'].phrase} and they share something kind.",
        f'Write a warm story that uses the words "monger" and "porpoise" and ends with a shared, happy scene.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    h, p = f["helper"], f["porpoise"]
    need, gift = f["need"], f["gift"]
    return [
        ("Who is the story about?",
         f"It is about {h.id}, a monger at the market, and {p.id}, a porpoise who came to speak gently and ask for help."),
        ("What did the porpoise need?",
         f"{p.id} needed {need.phrase}. That mattered because {need.risk}, and the porpoise did not want to stay alone."),
        ("How did the monger help?",
         f"{h.id} shared {gift.phrase} with {p.id}. The sharing mattered because it answered the porpoise's need and made both of them feel safer."),
        ("How did the story end?",
         f"They ended side by side at the {f['setting'].place}, sharing {gift.label} and feeling warm and calm. The ending shows that kindness changed the mood from lonely to together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a monger?",
         "A monger is a person who sells things, often at a market or by the water."),
        ("What is a porpoise?",
         "A porpoise is a sea animal that swims in the ocean. It is gentle and clever."),
        ("What does sharing mean?",
         "Sharing means letting someone else use or have part of something. It is a kind way to help another person or animal."),
        ("Why is dialogue helpful?",
         "Dialogue lets characters tell each other what they need. That makes it easier to solve a problem kindly."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
kindly(helper) :- helper(H), kindness(H, K), K >= 1.
shared_story :- helper(H), porpoise(P), sharing(H, S), receiving(P, R), S >= 1, R >= 1.
valid(setting(S), need(N), gift(G)) :- setting(S), need(N), gift(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    try:
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH between clingo and valid_combos():")
            print("  only in clingo:", sorted(clingo_set - python_set))
            print("  only in python:", sorted(python_set - clingo_set))
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        print(f"OK: smoke story generated ({len(sample.story)} chars).")
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.need not in NEEDS or params.gift not in GIFTS:
        raise StoryError("Invalid StoryParams")
    world = tell(SETTINGS[params.setting], NEEDS[params.need], GIFTS[params.gift],
                 helper_name=params.helper_name, helper_type=params.helper_type,
                 porpoise_name=params.porpoise_name, porpoise_type=params.porpoise_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
