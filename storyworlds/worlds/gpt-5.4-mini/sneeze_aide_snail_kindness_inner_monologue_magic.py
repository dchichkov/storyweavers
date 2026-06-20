#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sneeze_aide_snail_kindness_inner_monologue_magic.py
===================================================================================

A small storyworld for a gentle adventure about a snail aide, a sudden sneeze,
and a little bit of kindness and magic.

The world keeps a typed model of a tiny expedition: a traveler, an aide, a snail,
a trail-side challenge, and a magical token that can help or fail depending on
how wisely it is used. The story engine simulates a short causal chain:
a problem arises, the aide thinks aloud, kindness changes the plan, and the
ending image shows what improved.

This file is standalone and uses only the Python standard library plus the
shared result containers from storyworlds/results.py.
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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    path: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Problem:
    id: str
    label: str
    cause_word: str
    effect_word: str
    risk_word: str
    severity: int = 1
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class MagicToken:
    id: str
    label: str
    glow: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Resolution:
    id: str
    label: str
    text: str
    result: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
            value = defaultdict(float)
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


def _r_sniffle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["sneeze"] < THRESHOLD:
            continue
        sig = ("sniffle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fluster"] += 1
        out.append("__sniffle__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["brave"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("sniffle", _r_sniffle), Rule("kindness", _r_kindness)]


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


def problem_risk(problem: Problem, setting: Setting) -> bool:
    return True if problem.severity >= 1 else False


def choose_resolution(problem: Problem, token: MagicToken) -> Resolution:
    if token.power >= 2:
        return RESOLUTIONS["glimmer"]
    return RESOLUTIONS["plain"]


def predict(world: World, traveler: Entity, token: MagicToken) -> dict:
    sim = world.copy()
    _cast_magic(sim, sim.get(traveler.id), token, narrate=False)
    return {
        "calmed": sim.get(traveler.id).memes["calm"] >= THRESHOLD,
        "helped": sim.get("snail").memes["helped"] >= THRESHOLD,
    }


def _cast_magic(world: World, traveler: Entity, token: MagicToken, narrate: bool = True) -> None:
    traveler.meters["magic"] += 1
    traveler.memes["hope"] += 1
    if token.power >= 1:
        world.get("snail").memes["helped"] += 1
        world.get("aide").memes["kindness"] += 1
    propagate(world, narrate=narrate)


def start(world: World, traveler: Entity, aide: Entity, snail: Entity, setting: Setting) -> None:
    traveler.memes["joy"] += 1
    aide.memes["watchful"] += 1
    snail.memes["curious"] += 1
    world.say(
        f"On a bright trail near {setting.place}, {traveler.id} set out with "
        f"{aide.id} and a tiny snail named {snail.id}."
    )
    world.say(
        f"The path curved beside {setting.path}, and the day felt like the start "
        f"of an adventure."
    )


def build_tension(world: World, traveler: Entity, problem: Problem, snail: Entity) -> None:
    traveler.meters["sneeze"] += 1
    traveler.memes["alarm"] += 1
    world.say(
        f"Then came a sudden {problem.label}. It burst out so fast that {traveler.id} "
        f"stumbled and looked down at the {snail.id} trail."
    )
    world.say(
        f'In {traveler.id}\'s inner monologue, one thought flashed: "If I keep '
        f"walking, I might scare the snail away."
    )


def warn_and_plan(world: World, aide: Entity, traveler: Entity, token: MagicToken) -> None:
    pred = predict(world, traveler, token)
    aide.memes["kindness"] += 1
    world.facts["predicted_help"] = pred["helped"]
    world.say(
        f"{aide.id} leaned close and said, \"Let's be gentle. I think the snail "
        f"needs calm feet, not rushed ones.\""
    )
    world.say(
        f'In {aide.id}\'s own quiet inner monologue, another thought answered: '
        f'"Kindness can be a lantern, even without real light."'
    )


def act_kindly(world: World, traveler: Entity, aide: Entity, snail: Entity, token: MagicToken) -> None:
    traveler.memes["kindness"] += 1
    if token.id == "glimmer":
        world.say(
            f"{traveler.id} lifted the magic {token.label}, and it {token.glow}."
        )
    else:
        world.say(f"{traveler.id} held the {token.label} carefully and spoke softly.")
    _cast_magic(world, traveler, token)


def resolve(world: World, traveler: Entity, aide: Entity, snail: Entity, res: Resolution) -> None:
    traveler.memes["calm"] += 1
    snail.memes["safe"] += 1
    world.say(
        f"{res.text}. The {snail.id} kept moving, and the trail stayed peaceful."
    )
    world.say(
        f"At the end, {traveler.id} felt calmer, {aide.id} looked proud, and the "
        f"little snail was safe beside the path."
    )


def tell(setting: Setting, problem: Problem, token: MagicToken, resolution: Resolution,
         traveler_name: str = "Lina", traveler_gender: str = "girl",
         aide_name: str = "Moss", aide_gender: str = "boy") -> World:
    world = World()
    traveler = world.add(Entity(traveler_name, "character", traveler_gender, role="traveler"))
    aide = world.add(Entity(aide_name, "character", aide_gender, role="aide", traits=["kind"]))
    snail = world.add(Entity("snail", "character", "thing", label="snail", role="companion"))
    world.add(Entity("path", "thing", "thing", label=setting.path))
    world.add(Entity("place", "thing", "thing", label=setting.place))
    traveler.memes["kindness"] = 1.0
    snail.memes["hope"] = 0.0

    start(world, traveler, aide, snail, setting)
    world.para()
    build_tension(world, traveler, problem, snail)
    warn_and_plan(world, aide, traveler, token)
    world.para()
    act_kindly(world, traveler, aide, snail, token)
    world.para()
    resolve(world, traveler, aide, snail, resolution)

    world.facts.update(
        setting=setting, problem=problem, token=token, resolution=resolution,
        traveler=traveler, aide=aide, snail=snail,
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the old garden gate", "a mossy stone path", "bright"),
    "woods": Setting("woods", "the lantern clearing", "a ferny trail", "quiet"),
    "harbor": Setting("harbor", "the shell dock", "a wooden pier", "salty"),
}

PROBLEMS = {
    "sneeze": Problem("sneeze", "sneeze", "sudden", "flustered", "startled", 1, {"sneeze"}),
    "gust": Problem("gust", "gust of wind", "sudden", "shaky", "scared", 1, {"wind"}),
}

TOKENS = {
    "glimmer": MagicToken("glimmer", "glimmer stone", "glimmered softly", "kind light", 2, {"magic"}),
    "pebble": MagicToken("pebble", "smooth pebble", "warmed in the hand", "comfort", 1, {"magic"}),
}

RESOLUTIONS = {
    "glimmer": Resolution("glimmer", "gentle spell", "The magic made a calm circle of light",
                          "calmed", 2, {"magic"}),
    "plain": Resolution("plain", "soft words", "The words were enough to help",
                        "calmed", 1, {"kindness"}),
}

TRAVELLERS = ["Lina", "Mina", "Tessa", "Nora", "Ava"]
AIDES = ["Moss", "Pip", "Robin", "Sage", "Bram"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    token: str
    resolution: str
    traveler_name: str
    traveler_gender: str
    aide_name: str
    aide_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for t in TOKENS:
                if problem_risk(PROBLEMS[p], SETTINGS[s]):
                    combos.append((s, p, t))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "sneeze", "aide", and "snail".',
        f"Tell a gentle adventure where {f['traveler'].id} gets a sneeze, an aide helps, and a snail stays safe.",
        f"Write a story with inner monologue and a little magic, where kindness changes what happens on a trail.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    traveler, aide, snail = f["traveler"], f["aide"], f["snail"]
    token, setting = f["token"], f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {traveler.id}, {aide.id}, and the snail on a small adventure near {setting.place}."),
        ("What problem happened?",
         f"A sudden {f['problem'].label} startled {traveler.id}. It made the walk feel shaky for a moment."),
        ("How did the aide help?",
         f"{aide.id} stayed calm, thought aloud, and used kindness to help {traveler.id} choose a gentler way forward."),
        ("What changed by the end?",
         f"The trail stayed peaceful, the snail was safe, and {traveler.id} felt calmer because of the magic and kindness."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a snail?",
         "A snail is a tiny crawling animal with a soft body and usually a shell. It moves slowly and likes calm places."),
        ("What is kindness?",
         "Kindness means helping in a gentle way, speaking softly, and caring about how someone else feels."),
        ("What is inner monologue?",
         "Inner monologue is the quiet voice in a character's head. It tells what the character is thinking."),
        ("What is magic in stories?",
         "Magic is a special make-believe power that can change how a story feels or help solve a problem."),
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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "sneeze", "glimmer", "glimmer", "Lina", "girl", "Moss", "boy"),
    StoryParams("woods", "sneeze", "pebble", "plain", "Nora", "girl", "Pip", "boy"),
    StoryParams("harbor", "gust", "glimmer", "glimmer", "Ava", "girl", "Robin", "boy"),
]


def explain_rejection(problem: Problem, token: MagicToken) -> str:
    return f"(No story: {problem.label} and {token.label} do not make a reasonable adventure.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, T) :- setting(S), problem(P), token(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, token=None, resolution=None,
                                                           traveler_name=None, traveler_gender=None, aide_name=None,
                                                           aide_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: sneeze, aide, snail, kindness, inner monologue, magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--traveler-name")
    ap.add_argument("--traveler-gender", choices=["girl", "boy", "thing"])
    ap.add_argument("--aide-name")
    ap.add_argument("--aide-gender", choices=["girl", "boy", "thing"])
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
              and (args.problem is None or c[1] == args.problem)
              and (args.token is None or c[2] == args.token)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, token = rng.choice(sorted(combos))
    resolution = args.resolution or choose_resolution(PROBLEMS[problem], TOKENS[token]).id
    traveler_gender = args.traveler_gender or rng.choice(["girl", "boy"])
    aide_gender = args.aide_gender or rng.choice(["girl", "boy"])
    traveler_name = args.traveler_name or rng.choice(TRAVELLERS)
    aide_name = args.aide_name or rng.choice(AIDES)
    return StoryParams(setting, problem, token, resolution, traveler_name, traveler_gender, aide_name, aide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        TOKENS[params.token],
        RESOLUTIONS[params.resolution],
        params.traveler_name,
        params.traveler_gender,
        params.aide_name,
        params.aide_gender,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for s, p, t in asp_valid_combos():
            print(f"  {s:8} {p:8} {t:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
