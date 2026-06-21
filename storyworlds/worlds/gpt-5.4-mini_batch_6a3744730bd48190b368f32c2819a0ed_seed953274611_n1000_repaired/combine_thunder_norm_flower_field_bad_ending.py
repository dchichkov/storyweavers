#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/combine_thunder_norm_flower_field_bad_ending.py
===============================================================================

A standalone storyworld for a tiny fable-like domain: a child in a flower field
wants to combine things into a bright game, ignores a sensible norm, and thunder
arrives before the day can be fixed. This world only tells a bad ending, but it
still has a complete shape: premise, warning, turn, consequence, and a final
image that proves what changed.

The story is intentionally small and classical:
- the setting is a flower field
- the required seed words appear in the world model and prose: combine, thunder,
  norm
- the style is fable-like, with a simple lesson
- the ending is bad: the flowers are ruined, the game is lost, and the child
  learns too late

This file follows the shared Storyweavers contract:
- StoryParams dataclass
- build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- QA generation from world state, not from parsing story text
- inline ASP_RULES twin plus Python reasonableness gate
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    scene: str
    line: str
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
class Action:
    id: str
    verb: str
    phrase: str
    risk: str
    zone: set[str]
    mess: str
    turns_dark: bool = False
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
class Norm:
    id: str
    wording: str
    warning: str
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
class Force:
    id: str
    line: str
    sound: str
    power: int
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    field = world.entities.get("field")
    child = world.entities.get("child")
    bloom = world.entities.get("bloom")
    if not field or not child or not bloom:
        return out
    if child.meters["bothered"] < THRESHOLD:
        return out
    sig = ("soil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bloom.meters["ruined"] += 1
    field.meters["dark"] += 1
    child.memes["regret"] += 1
    out.append("__soil__")
    return out


def _r_thunder(world: World) -> list[str]:
    out: list[str] = []
    storm = world.entities.get("storm")
    if not storm or storm.meters["thundering"] < THRESHOLD:
        return out
    sig = ("thunder",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__thunder__")
    return out


CAUSAL_RULES = [Rule("soil", "physical", _r_soil), Rule("thunder", "weather", _r_thunder)]


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


def reasonableness_gate(action: Action, force: Force) -> bool:
    return action.turns_dark and force.power >= 1


def could_warn(norm: Norm, action: Action, force: Force) -> bool:
    return bool(norm.warning) and action.turns_dark and force.power >= 1


def predict_bad(world: World, action: Action, force: Force) -> dict:
    sim = world.copy()
    sim.get("child").meters["bothered"] += 1
    sim.get("storm").meters["thundering"] += 1
    propagate(sim, narrate=False)
    return {
        "ruined": sim.get("bloom").meters["ruined"] >= THRESHOLD,
        "dark": sim.get("field").meters["dark"] >= THRESHOLD,
    }


def do_combine(world: World, child: Entity, action: Action) -> None:
    child.memes["delight"] += 1
    world.say(
        f"In a bright flower field, {child.id} tried to {action.verb}. "
        f"{action.phrase}"
    )


def warn(world: World, elder: Entity, child: Entity, norm: Norm, action: Action) -> None:
    child.memes["heed"] += 1
    world.say(
        f'{elder.id} spoke the old {norm.id}: "{norm.wording}. {norm.warning}"'
    )
    world.say(
        f"But {child.id} was eager to make the game more grand, and did not stop."
    )


def ignore(world: World, child: Entity, action: Action) -> None:
    child.meters["bothered"] += 1
    child.memes["boldness"] += 1
    world.say(f"{child.id} ignored the warning and kept trying to combine the pieces.")


def strike(world: World, storm: Entity, force: Force) -> None:
    storm.meters["thundering"] += 1
    world.say(
        f"Then {force.line} came over the field, and {force.sound} rolled so loud "
        f"the petals shook."
    )


def loss(world: World, field: Entity, bloom: Entity, child: Entity) -> None:
    world.say(
        "The thunder broke the calm. The flowers bowed and tore, and the bright "
        "little game fell apart in the wet grass."
    )
    world.say(
        f"When the sky grew quiet again, {child.id} stood among bent stems and "
        f"muddy petals, learning too late that a proud wish can break a gentle norm."
    )


def tell(setting: Setting, action: Action, norm: Norm, force: Force,
         hero_name: str = "Mina", hero_gender: str = "girl",
         elder_name: str = "Grandma", elder_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    field = world.add(Entity(id="field", type="place", label="the flower field"))
    bloom = world.add(Entity(id="bloom", type="thing", label="the flowers"))
    storm = world.add(Entity(id="storm", type="weather", label="the thunderstorm"))
    child.memes["curiosity"] = 1.0
    world.say(
        f"{child.id} loved the flower field because it looked like a painted quilt "
        f"on the ground. The day was quiet, and the {setting.id} felt soft underfoot."
    )
    world.say(
        f"{child.id} had a simple idea: {action.phrase.lower()} and make something new."
    )
    world.para()
    do_combine(world, child, action)
    warn(world, elder, child, norm, action)
    ignore(world, child, action)
    strike(world, storm, force)
    propagate(world, narrate=False)
    world.para()
    loss(world, field, bloom, child)
    world.facts.update(
        child=child,
        elder=elder,
        field=field,
        bloom=bloom,
        storm=storm,
        setting=setting,
        action=action,
        norm=norm,
        force=force,
        outcome="bad",
        ruined=bloom.meters["ruined"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "flower_field": Setting(id="flower_field", scene="a flower field", line="in the flower field"),
}

ACTIONS = {
    "combine": Action(
        id="combine",
        verb="combine leaves and petals",
        phrase="She wanted to combine leaves, petals, and tiny stems into one shining crown.",
        risk="the flowers would be disturbed",
        zone={"field"},
        mess="ruined",
        turns_dark=True,
        tags={"combine", "flower"},
    ),
}

NORMS = {
    "norm": Norm(
        id="norm",
        wording="The old norm says to leave living flowers where they grow",
        warning="A fable should remember that a field is not a basket",
        tags={"norm", "lesson"},
    ),
}

FORCES = {
    "thunder": Force(
        id="thunder",
        line="a thundercloud",
        sound="thunder",
        power=1,
        tags={"thunder", "storm"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    action: str
    norm: str
    force: str
    hero_name: str = "Mina"
    hero_gender: str = "girl"
    elder_name: str = "Grandma"
    elder_gender: str = "woman"
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
    StoryParams(setting="flower_field", action="combine", norm="norm", force="thunder", hero_name="Mina", hero_gender="girl", elder_name="Grandma", elder_gender="woman"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for nid, norm in NORMS.items():
                for fid, force in FORCES.items():
                    if reasonableness_gate(action, force) and could_warn(norm, action, force):
                        combos.append((sid, aid, nid, fid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable in a flower field that uses the words "{f["action"].id}", "{f["force"].id}", and "{f["norm"].id}".',
        "Tell a short moral story where a child ignores a wise norm in a flower field and thunder ruins the game.",
        "Write a child-facing bad-ending fable about trying to combine living flowers into a toy before thunder arrives.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    action = f["action"]
    norm = f["norm"]
    return [
        ("Where did the story happen?",
         f"It happened in a flower field, where the grass was soft and the blooms stood in rows. That setting matters because the flowers were living things that could be ruined."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to {action.verb}. {action.phrase}"),
        (f"What warning did {elder.id} give?",
         f"{elder.id} spoke the old {norm.id} and reminded {child.id} that living flowers should be left where they grow. The warning fit the field because a flower field is not meant to be picked apart for play."),
        ("Why was the ending bad?",
         f"The warning was ignored, and then thunder came over the field. The flowers were bent and ruined, so the bright little game ended in mud and regret."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is thunder?",
         "Thunder is the loud sound that comes after lightning in a storm. It can rumble across the sky and startle people and animals."),
        ("What is a norm?",
         "A norm is a rule people usually follow because it helps everyone live together kindly and safely. In a fable, a norm often teaches a simple lesson."),
        ("Why should you be gentle with flowers?",
         "Flowers are living plants, so rough hands can bend or break them. Gentle care helps them stay bright and growing."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(flower_field).
action(combine).
norm(norm).
force(thunder).

turns_dark(combine).
power(thunder,1).

valid(S,A,N,F) :- setting(S), action(A), norm(N), force(F),
                  turns_dark(A), power(F,P), P >= 1.

bad_end(S,A,N,F) :- valid(S,A,N,F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for nid in NORMS:
        lines.append(asp.fact("norm", nid))
    for fid, force in FORCES.items():
        lines.append(asp.fact("force", fid))
        lines.append(asp.fact("power", fid, force.power))
    for aid, action in ACTIONS.items():
        if action.turns_dark:
            lines.append(asp.fact("turns_dark", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-world in a flower field with thunder and a broken norm.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--norm", choices=NORMS)
    ap.add_argument("--force", choices=FORCES)
    ap.add_argument("--name")
    ap.add_argument("--elder-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.norm is None or c[2] == args.norm)
              and (args.force is None or c[3] == args.force)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, aid, nid, fid = rng.choice(sorted(combos))
    return StoryParams(
        setting=sid,
        action=aid,
        norm=nid,
        force=fid,
        hero_name=args.name or rng.choice(["Mina", "Lena", "Tessa", "Ruby"]),
        hero_gender=args.gender or rng.choice(["girl", "boy"]),
        elder_name=args.elder_name or "Grandma",
        elder_gender=args.elder_gender or "woman",
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("setting", SETTINGS), ("action", ACTIONS), ("norm", NORMS), ("force", FORCES)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    norm = NORMS[params.norm]
    force = FORCES[params.force]
    world = tell(setting, action, norm, force, params.hero_name, params.hero_gender, params.elder_name, params.elder_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, a, n, f in combos:
            print(f"  {s:12} {a:10} {n:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.setting} ({p.action}, {p.force})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
