#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mixture_sturdy_gefilte_muddy_slope_sound_effects.py
====================================================================================

A standalone storyworld about a muddy slope, a sturdy little kitchen trick, and a
heartwarming turn that still ends in a bad ending. A child and a grown-up try to
fix a slippery mess with a mixture, sound effects mark the motion, and a gentle
transformation changes what the mixture becomes. The final outcome is sad, but
kindness remains.

Seed words: mixture, sturdy, gefilte
Setting: muddy slope
Features: Sound Effects, Transformation, Bad Ending
Style: Heartwarming
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
from typing import Optional

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
    slope: str
    sound: str
    slickness: int = 1

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
class Mix:
    id: str
    label: str
    phrase: str
    sound: str
    transforms_to: str
    sturdy_needed: bool = True
    edible: bool = False

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
class Tool:
    id: str
    label: str
    phrase: str
    sturdy: bool = True

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

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


SETTINGS = {
    "muddy_slope": Setting("muddy_slope", "the hill path", "muddy slope", "squelch"),
    "bank_path": Setting("bank_path", "the riverbank", "muddy slope", "plop"),
}

MIXTURES = {
    "mixture": Mix("mixture", "mixture", "a small mixture", "glug-glug", "gel", sturdy_needed=True, edible=False),
    "gefilte": Mix("gefilte", "gefilte", "a bowl of gefilte", "plip-plip", "dumpling", sturdy_needed=True, edible=True),
}

TOOLS = {
    "sturdy": Tool("sturdy", "sturdy bowl", "a sturdy bowl", sturdy=True),
    "tin": Tool("tin", "tin cup", "a tin cup", sturdy=False),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Sam", "Leo", "Ben"]
TRAITS = ["gentle", "careful", "hopeful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (sid, mid, tid)
        for sid, s in SETTINGS.items()
        for mid, m in MIXTURES.items()
        for tid, t in TOOLS.items()
        if m.sturdy_needed and t.sturdy
    ]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mixture: str
    tool: str
    child: str
    child_gender: str
    parent: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Muddy-slope heartwarming storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mixture", choices=MIXTURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def explain_rejection(mix: Mix, tool: Tool) -> str:
    if not tool.sturdy:
        return f"(No story: {tool.label} is not sturdy enough for a slippery mixture on the slope.)"
    return "(No story: this combination is not reasonable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not TOOLS[args.tool].sturdy:
        raise StoryError(explain_rejection(MIXTURES[args.mixture] if args.mixture else MIXTURES["mixture"], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mixture is None or c[1] == args.mixture)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mixture, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mixture, tool, name, gender, parent, trait)


def tell(setting: Setting, mix: Mix, tool: Tool, child: str, gender: str, parent: str, trait: str) -> World:
    w = World()
    kid = w.add(Entity(child, "character", gender, role="child", traits=[trait]))
    grown = w.add(Entity("Parent", "character", parent, role="parent", label="the parent"))
    bowl = w.add(Entity("bowl", "thing", "thing", label=mix.label))
    rock = w.add(Entity("rock", "thing", "thing", label="the slope"))
    kid.memes["hope"] += 1
    kid.memes["joy"] += 1
    w.say(f"{child} and {grown.label_word} walked to {setting.place}, where {setting.slope} waited after the rain.")
    w.say(f"{child} held up {mix.phrase} and said it could help on the slippery path. {mix.sound} went the little bowl as {child} tipped it.")
    w.para()
    w.say(f"The wind said {setting.sound}, and the mud slid under their shoes. The parent reached for {tool.phrase}, because it was {tool.label} and would not wobble.")
    bowl.meters["mixed"] += 1
    if mix.id == "mixture":
        bowl.meters["shapeless"] += 1
        bowl.memes["hope"] += 1
        w.say(f"The mixture changed as it rested: first it sloshed, then it thickened into a soft gel, almost like a little blanket for the mud.")
    else:
        bowl.meters["mixed"] += 1
        w.say(f"The gefilte transformed too, settling into a tender dumpling shape that looked calmer than before.")
    w.para()
    kid.meters["slip"] += 1
    w.say(f"{child} stepped forward anyway. {setting.sound.capitalize()}! The slope gave a quick shake, and the child slid faster than expected.")
    tool_entity = w.add(Entity("tool", "thing", "thing", label=tool.label))
    if tool.sturdy:
        tool_entity.meters["steady"] += 1
        w.say(f"{grown.label_word.capitalize()} caught {child} with the {tool.label} and held on tight.")
    w.para()
    kid.memes["fear"] += 1
    grown.memes["love"] += 1
    w.say(f"For a moment they both froze, then {grown.label_word} hugged {child} close and whispered, 'We can still be kind to the day, even when the day is muddy.'")
    w.say(f"They packed the {mix.label} away, and the sturdy bowl stayed in one piece.")
    w.say(f"But the path was too slick; by the time they were ready to go, the little hill had already taken the child's favorite boot.")
    w.say(f"They went home hand in hand, carrying the sound of {setting.sound} and the feeling of being looked after.")
    w.facts.update(setting=setting, mix=mix, tool=tool, child=kid, parent=grown, outcome="bad")
    return w


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MIXTURES[params.mixture], TOOLS[params.tool], params.child, params.child_gender, params.parent, params.trait)
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
    return [
        f"Write a heartwarming story about a muddy slope, a {f['mix'].label}, and a {f['child'].id} who hears {f['setting'].sound} in the wind.",
        f"Tell a story that includes the words mixture, sturdy, and gefilte, and ends sadly but kindly on a muddy slope.",
        f"Write a child-friendly story where a sturdy tool helps a parent, a mixture changes shape, and the ending is a bad ending with warmth in it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mix = f["mix"]
    setting = f["setting"]
    return [
        ("What were the child and parent doing?", f"They were trying to manage a slippery muddy slope together. The parent kept the child safe while the little mixture changed shape in the bowl."),
        ("What happened to the mixture?", f"It transformed as it rested and became softer and thicker. That change made it feel more like something they could carry safely, even though the day still ended badly."),
        ("How did the story end?", f"It ended in a bad way because the slope was too slick and the child lost a boot. Still, {parent.label_word} stayed gentle and comforting, so the ending felt loving even while it was sad."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does sturdy mean?", "Sturdy means strong and steady, so it does not bend or wobble easily."),
        ("What is a mixture?", "A mixture is when two or more things are combined together into one bowl or one mess."),
        ("What is gefilte?", "Gefilte is a food made from a mixture of ingredients shaped into a little piece you can hold and cook."),
        ("Why can a muddy slope be dangerous?", "A muddy slope can be dangerous because mud makes the ground slippery, and feet can slide before you expect it."),
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
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("muddy_slope", "mixture", "sturdy", "Mia", "girl", "mother", "gentle"),
    StoryParams("bank_path", "gefilte", "sturdy", "Eli", "boy", "father", "hopeful"),
]


ASP_RULES = r"""
valid(S, M, T) :- setting(S), mixture(M), tool(T), sturdy_tool(T).
story_word(mixture).
story_word(sturdy).
story_word(gefilte).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MIXTURES:
        lines.append(asp.fact("mixture", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.sturdy:
            lines.append(asp.fact("sturdy_tool", tid))
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
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_story_error() -> str:
    return "(No story: the requested options do not make a reasonable muddy-slope tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mixture is None or c[1] == args.mixture)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError(explain_story_error())
    setting, mixture, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mixture, tool, name, gender, parent, trait)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
        header = "### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
