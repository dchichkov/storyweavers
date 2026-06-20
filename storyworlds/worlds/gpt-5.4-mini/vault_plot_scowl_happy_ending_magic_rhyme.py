#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vault_plot_scowl_happy_ending_magic_rhyme.py
=============================================================================

A standalone storyworld for a small slice-of-life tale about a child, a tiny
problem, a careful grown-up, and a happy ending with a little magic and rhyme.

Seed words: vault, plot, scowl
Features: Happy Ending, Magic, Rhyme
Style: Slice of Life

The world is built around a child helping in a neighborhood garden by the old
vault door behind the community hall. The vault is not treasure in the adventure
sense; it is a heavy storage room for garden tools, seed packets, and old
ribbons. The child wants to help with the flower plot, but the vault key is
stuck and the child scowls. A gentle rhyme, a bit of magic-like whimsy, and a
calm grown-up turn the mood around. The ending proves the change with flowers,
shared work, and a bright smile.

This script follows the Storyweavers contract:
- stdlib only
- eager import of storyworlds/results.py
- StoryParams, build_parser, resolve_params, generate, emit, main
- --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate plus inline ASP twin
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    locked: bool = False
    magical: bool = False
    grows: bool = False

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    details: str

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
class VaultItem:
    id: str
    label: str
    phrase: str
    purpose: str
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
class Problem:
    id: str
    sense: int
    text: str
    resolve: str
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
    tag: str
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


def _r_scowl(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["worry"] >= THRESHOLD and child.memes["hope"] < THRESHOLD:
        sig = ("scowl", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["scowl"] += 1
            out.append("__scowl__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    vault = world.entities.get("vault")
    plot = world.entities.get("plot")
    if not child or not vault or not plot:
        return out
    if child.memes["hope"] >= THRESHOLD and vault.meters["open"] >= THRESHOLD:
        sig = ("magic", vault.id)
        if sig not in world.fired:
            world.fired.add(sig)
            plot.meters["bloom"] += 1
            child.memes["joy"] += 1
            out.append("__magic__")
    return out


CAUSAL_RULES = [
    Rule("scowl", "social", _r_scowl),
    Rule("magic", "physical", _r_magic),
]


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


def sensible_responses() -> list[Problem]:
    return [p for p in PROBLEMS.values() if p.sense >= SENSE_MIN]


def is_reasonable(problem: Problem, setting: Setting, item: VaultItem) -> bool:
    return problem.id == "stuck_key" and setting.id == "community_hall" and "tool" in item.tags


def lock_reason(problem: Problem, item: VaultItem) -> str:
    return f"(No story: {problem.id} needs a real fix, and {item.label} is not the right thing for it.)"


def _open_vault(world: World) -> None:
    world.get("vault").meters["open"] += 1
    world.get("vault").locked = False
    world.get("child").memes["hope"] += 1
    propagate(world, narrate=True)


def _dry_setup(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["delight"] += 1
    world.say(
        f"On a soft afternoon at {setting.place}, {child.id} helped {parent.label_word} near the {setting.scene}. "
        f"{setting.details}"
    )


def _problem(world: World, child: Entity, parent: Entity, problem: Problem, item: VaultItem) -> None:
    child.memes["worry"] += 1
    world.say(
        f"But the {item.label} would not budge, and the little task stopped short. "
        f'{child.id} made a small scowl. "{problem.text}"'
    )


def _rhyme_offer(world: World, parent: Entity, child: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f'{parent.id} smiled and said, "Try a rhyme, one line at a time: '
        f'"Turn and hum, little drum; open gently, let work come.""'
    )


def _resolve(world: World, parent: Entity, child: Entity, problem: Problem, item: VaultItem) -> None:
    _open_vault(world)
    world.say(
        f"The old vault door gave a soft click. {parent.id} turned the key once more, "
        f'and {problem.resolve}.'
    )
    world.say(
        f"Inside were seed packets, string, and bright ribbon for the flower plot. "
        f"{child.id} grinned, and the scowl floated away like a passing cloud."
    )


def _ending(world: World, child: Entity, parent: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Together they walked to the plot, tucked seeds into the soil, and watered them in neat rows. "
        f"By evening, the garden smelled sweet, and {child.id} was smiling beside {parent.id}."
    )
    world.say(
        f"The vault stayed shut again, the plot waited for morning, and the day ended warm and ordinary and happy."
    )


def tell(setting: Setting, problem: Problem, item: VaultItem,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the grown-up"))
    vault = world.add(Entity(id="vault", type="thing", label="the vault", locked=True, magical=True))
    plot = world.add(Entity(id="plot", type="thing", label="the flower plot", grows=True))
    world.facts.update(setting=setting, problem=problem, item=item, child=child, parent=parent, vault=vault, plot=plot)

    _dry_setup(world, child, parent, setting)
    world.para()
    _problem(world, child, parent, problem, item)
    _rhyme_offer(world, parent, child)
    _resolve(world, parent, child, problem, item)
    world.para()
    _ending(world, child, parent)
    return world


SETTINGS = {
    "community_hall": Setting(
        "community_hall",
        "the community hall",
        "little garden room",
        "A chalk sign by the wall showed today's jobs, and a bucket of warm water waited by the sink.",
    ),
    "courtyard": Setting(
        "courtyard",
        "the courtyard",
        "sunny corner",
        "The herb pots lined the steps, and bees buzzed lazily around the thyme.",
    ),
}

ITEMS = {
    "toolbox": VaultItem("toolbox", "toolbox", "the toolbox", "garden tools", {"tool", "vault"}),
    "seed_tin": VaultItem("seed_tin", "seed tin", "the seed tin", "flower seeds", {"vault"}),
    "ribbon_box": VaultItem("ribbon_box", "ribbon box", "the ribbon box", "bright ribbon", {"vault"}),
}

PROBLEMS = {
    "stuck_key": Problem(
        "stuck_key",
        3,
        "The key feels stuck. Maybe we need a tiny rhyme to loosen our nerves.",
        "the key slipped free as if it had been waiting for a song",
        {"magic", "rhyme", "happy"},
    ),
    "muddy_latch": Problem(
        "muddy_latch",
        2,
        "The latch is muddy and hard to turn. Maybe a careful rhyme will help us slow down.",
        "the latch turned after a gentle wipe and a quiet rhyme",
        {"magic", "rhyme"},
    ),
}


GIRL_NAMES = ["Mina", "Luna", "Tessa", "Nora", "Ruby", "Iris", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Eli", "Noah", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for iid, item in ITEMS.items():
                if is_reasonable(prob, setting, item):
                    combos.append((sid, pid, iid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    name: str
    gender: str
    parent: str
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


KNOWLEDGE = {
    "vault": [("What is a vault?", "A vault is a strong room or box used to keep important things safe.")],
    "plot": [("What is a plot in a garden?", "A plot is a small piece of ground where people grow flowers or vegetables.")],
    "scowl": [("What does it mean to scowl?", "To scowl is to make an unhappy, frowning face.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a pattern of words that sound alike at the end.")],
    "magic": [("What is magic in a story?", "Magic in a story is something wonderful that feels a little impossible.")],
    "happy": [("What is a happy ending?", "A happy ending is when the problem gets fixed and the story finishes in a good way.")],
}
KNOWLEDGE_ORDER = ["vault", "plot", "scowl", "rhyme", "magic", "happy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "vault", "plot", and "scowl".',
        f"Tell a gentle story where {f['child'].id} helps around {f['setting'].place} and a stuck vault turns into a happy moment with a rhyme.",
        f'Write a small everyday story with a little magic, a rhyme, and a bright ending in the flower plot.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, problem, item = f["child"], f["parent"], f["problem"], f["item"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {parent.id}, who are working together in a calm, ordinary way."),
        ("Why did {0} scowl?".format(child.id), f"{child.id} scowled because the {item.label} would not open right away. The stuck moment made the task feel slow, but it did not last long."),
        ("What helped fix the problem?", f"A little rhyme helped everyone slow down and try again. The grown-up turned the key carefully, and then the vault opened."),
    ]
    qa.append((
        "What was inside the vault?",
        "There were garden things inside, like seed packets, string, and ribbon. Those items were useful for the flower plot, so the vault was being used for everyday work."
    ))
    qa.append((
        "How did the story end?",
        "It ended happily, with the child smiling, the vault closed again, and the flower plot ready for seeds and water. The scowl was gone by the end."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vault", "plot", "scowl", "rhyme", "magic", "happy"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.locked:
            bits.append("locked")
        if e.magical:
            bits.append("magical")
        if e.grows:
            bits.append("grows")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("community_hall", "stuck_key", "toolbox", "Mina", "girl", "mother"),
    StoryParams("courtyard", "muddy_latch", "seed_tin", "Owen", "boy", "father"),
]


def explain_rejection(problem: Problem, item: VaultItem) -> str:
    return lock_reason(problem, item)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("sense", pid, prob.sense))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("tag", iid, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(P, I) :- problem(P), item(I), sense(P, S), sense_min(M), S >= M, tag(I, vault).
valid(S, P, I) :- setting(S), reasonable(P, I).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python valid_combos()")
    smoke = generate(CURATED[0]).story
    if not smoke:
        rc = 1
        print("MISMATCH: smoke generate returned empty story")
    else:
        print("OK: generate() smoke test produced a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a vault, a plot, a scowl, and a happy rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.item:
        if not is_reasonable(PROBLEMS[args.problem], SETTINGS[args.setting] if args.setting else SETTINGS["community_hall"], ITEMS[args.item]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, problem, item, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], ITEMS[params.item], params.name, params.gender, params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
