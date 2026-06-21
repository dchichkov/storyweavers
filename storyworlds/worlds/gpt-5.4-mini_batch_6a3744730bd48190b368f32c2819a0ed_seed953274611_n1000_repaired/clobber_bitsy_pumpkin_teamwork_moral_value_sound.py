#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clobber_bitsy_pumpkin_teamwork_moral_value_sound.py
====================================================================================

A tiny tall-tale storyworld about a clobbery pumpkin rescue with teamwork,
moral value, and sound effects.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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


@dataclass
class FieldSetting:
    id: str
    place: str
    terrain: str
    weather: str
    sound: str
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
class Friend:
    id: str
    gender: str
    trait: str
    sound_word: str
    job: str
    style: str = "tall tale"
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
class Pumpkin:
    id: str
    label: str
    weight: int
    stuck_in: str
    clobber_sfx: str
    can_roll: bool = True
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
class Tool:
    id: str
    label: str
    help_text: str
    teamwork_bonus: int
    sound: str
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


class World:
    def __init__(self, setting: FieldSetting) -> None:
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str
    friend1: str
    friend2: str
    pumpkin: str
    tool: str
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


SETTINGS = {
    "field": FieldSetting("field", "the wide field", "mud", "windy", "WHOOO"),
    "patch": FieldSetting("patch", "the pumpkin patch", "clay", "foggy", "HOOH"),
    "barnyard": FieldSetting("barnyard", "the barnyard", "roots", "bright", "KLOP"),
}

FRIENDS = {
    "bitsy": Friend("Bitsy", "girl", "quick", "zip-zap", "loom rope"),
    "clobber": Friend("Clobber", "boy", "brave", "boom-boom", "pushing log"),
    "mira": Friend("Mira", "girl", "steady", "hmm-hmm", "wooden lever"),
    "jo": Friend("Jo", "boy", "cheerful", "tap-tap", "wagon plank"),
}

PUMPKINS = {
    "pumpkin": Pumpkin("Pumpkin", "a giant pumpkin", 9, "mud", "CLOBBER!"),
    "moonpumpkin": Pumpkin("Moon Pumpkin", "a round pumpkin bright as a lantern", 7, "roots", "CLACK!"),
    "hillpumpkin": Pumpkin("Hill Pumpkin", "a big hill pumpkin", 8, "clay", "THUD!"),
}

TOOLS = {
    "team_rope": Tool("rope", "a long rope", "the two friends tie it together and pull in rhythm", 2, "HUP-HUP"),
    "wheelbarrow": Tool("barrow", "a wheelbarrow", "they lift the pumpkin and roll it carefully", 3, "RATTLE"),
    "lever": Tool("lever", "a wooden lever", "they pry the pumpkin free together", 2, "CREAK"),
}

GIRL_NAMES = ["Bitsy", "Mabel", "Nell", "Ruby", "Wren"]
BOY_NAMES = ["Clobber", "Orrin", "Tob", "Bram", "Hank"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for f1 in FRIENDS:
            for f2 in FRIENDS:
                if f1 == f2:
                    continue
                for p in PUMPKINS:
                    for t in TOOLS:
                        out.append((s, f1, f2, p))
    return out


def _lookup(d: dict, key: str, what: str):
    if key not in d:
        raise StoryError(f"Unknown {what}: {key}")
    return d[key]


def _pair_names(rng: random.Random) -> tuple[str, str]:
    a = rng.choice(GIRL_NAMES + BOY_NAMES)
    b = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a])
    return a, b


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with teamwork, morals, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--friend1", choices=FRIENDS)
    ap.add_argument("--friend2", choices=FRIENDS)
    ap.add_argument("--pumpkin", choices=PUMPKINS)
    ap.add_argument("--tool", choices=TOOLS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    friend1 = args.friend1 or rng.choice(list(FRIENDS))
    friend2 = args.friend2 or rng.choice([k for k in FRIENDS if k != friend1])
    pumpkin = args.pumpkin or rng.choice(list(PUMPKINS))
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(setting=setting, friend1=friend1, friend2=friend2, pumpkin=pumpkin, tool=tool)


ASP_RULES = r"""
friend(X) :- friend_cfg(X).
tool(X) :- tool_cfg(X).
pumpkin(X) :- pumpkin_cfg(X).
setting(X) :- setting_cfg(X).
valid(S,F1,F2,P,T) :- setting_cfg(S), friend_cfg(F1), friend_cfg(F2), F1 != F2, pumpkin_cfg(P), tool_cfg(T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("setting_cfg", k))
    for k in FRIENDS:
        lines.append(asp.fact("friend_cfg", k))
    for k in PUMPKINS:
        lines.append(asp.fact("pumpkin_cfg", k))
    for k in TOOLS:
        lines.append(asp.fact("tool_cfg", k))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/5.", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH in ASP gate.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, friend1=None, friend2=None, pumpkin=None, tool=None), random.Random(7)))
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        ok = 1
        print(f"SMOKE TEST FAILED: {e}")
    return ok


def _clobber(world: World, pumpkin: Entity, f1: Entity, f2: Entity, tool: Tool) -> None:
    pumpkin.meters["stuck"] += 1
    f1.memes["gumption"] += 1
    f2.memes["gumption"] += 1
    world.say(
        f"{f1.id} and {f2.id} found {pumpkin.label} sunk in the muck, and the air rang out with {pumpkin.id.lower()}-trouble and {tool.sound}."
    )


def _teamwork(world: World, pumpkin: Entity, f1: Entity, f2: Entity, tool: Tool) -> None:
    pumpkin.meters["free"] += 1
    f1.memes["joy"] += 1
    f2.memes["joy"] += 1
    world.say(
        f"They teamed up, one tugging and the other guiding, until the {tool.label} did its good work."
    )


def _moral(world: World, f1: Entity, f2: Entity) -> None:
    f1.memes["wisdom"] += 1
    f2.memes["wisdom"] += 1
    world.say(
        f"{f1.id} and {f2.id} shared the credit, for a helper who hoards the glory is a poor horse in a tall tale."
    )
    world.say("So they promised to help each other first and boast second.")


def tell(params: StoryParams) -> World:
    setting = _lookup(SETTINGS, params.setting, "setting")
    f1cfg = _lookup(FRIENDS, params.friend1, "friend")
    f2cfg = _lookup(FRIENDS, params.friend2, "friend")
    pcfg = _lookup(PUMPKINS, params.pumpkin, "pumpkin")
    tcfg = _lookup(TOOLS, params.tool, "tool")

    w = World(setting)
    f1 = w.add(Entity(id=f1cfg.id, kind="character", type=f1cfg.gender, role="helper"))
    f2 = w.add(Entity(id=f2cfg.id, kind="character", type=f2cfg.gender, role="helper"))
    pump = w.add(Entity(id=pcfg.id, kind="thing", type="pumpkin", label=pcfg.label))
    tool = w.add(Entity(id=tcfg.id, kind="thing", type="tool", label=tcfg.label))

    w.say(f"In {setting.place}, where the wind could whistle a tune through a keyhole, {f1.id} and {f2.id} met at the {setting.id}.")
    w.say(f"They had one giant task and two brave hearts, which is a fine recipe for a tall tale.")
    w.para()
    _clobber(w, pump, f1, f2, tcfg)
    w.para()
    _teamwork(w, pump, f1, f2, tcfg)
    w.say(f"At last the {pcfg.label} rolled free with a {pcfg.clobber_sfx} and a laugh as loud as a church bell in a thunderstorm.")
    w.para()
    _moral(w, f1, f2)
    w.say(f"By sunset, the {pcfg.label} sat safe on the wagon, and {f1.id} and {f2.id} walked home with mud on their boots and pride in their pockets.")

    w.facts.update(setting=params.setting, friend1=params.friend1, friend2=params.friend2, pumpkin=params.pumpkin, tool=params.tool)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the words "clobber", "bitsy", and "pumpkin" and shows teamwork.',
        f"Tell a moral story where {f['friend1']} and {f['friend2']} work together to free a {PUMPKINS[f['pumpkin']].label.lower()} with a funny sound effect.",
        f'Write a child-friendly tall tale with a clear lesson about sharing credit and helping together, and include a noisy "clobber" moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="Who worked together in the story?", answer=f"{f['friend1']} and {f['friend2']} worked together. They shared the task and used teamwork to solve the problem."),
        QAItem(question="What was stuck?", answer=f"{PUMPKINS[f['pumpkin']].label} was stuck in the muck. The friends had to pull, guide, and trust each other to get it moving."),
        QAItem(question="What moral did the story teach?", answer="It taught that teamwork works best when everyone helps and nobody hogs the praise. The friends were happier when they shared the credit."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is teamwork?", answer="Teamwork means people help each other and do a job together. When they share the work, hard things can become easier."),
        QAItem(question="Why do stories use sound effects?", answer="Sound effects make a story feel lively and fun. They help you hear the action in your head."),
        QAItem(question="What is a moral?", answer="A moral is the lesson a story wants to teach. It shows what choice is kind, wise, or fair."),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.friend1 not in FRIENDS or params.friend2 not in FRIENDS or params.pumpkin not in PUMPKINS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="field", friend1="bitsy", friend2="clobber", pumpkin="pumpkin", tool="team_rope"),
    StoryParams(setting="patch", friend1="mira", friend2="bitsy", pumpkin="moonpumpkin", tool="wheelbarrow"),
    StoryParams(setting="barnyard", friend1="clobber", friend2="jo", pumpkin="hillpumpkin", tool="lever"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        friend1=args.friend1 or rng.choice(list(FRIENDS)),
        friend2=args.friend2 or rng.choice([k for k in FRIENDS if k != (args.friend1 or "")]),
        pumpkin=args.pumpkin or rng.choice(list(PUMPKINS)),
        tool=args.tool or rng.choice(list(TOOLS)),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos[:50]:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_story_params(args, random.Random(base_seed + i))
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
