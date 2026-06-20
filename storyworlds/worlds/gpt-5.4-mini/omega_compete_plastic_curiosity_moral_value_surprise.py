#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/omega_compete_plastic_curiosity_moral_value_surprise.py
======================================================================================

A small standalone storyworld for an Adventure-style tale about a curious child,
a plastic relic, a friendly competition, a moral choice, and a surprise reveal.

Seed words:
- omega
- compete
- plastic

Required features:
- Curiosity
- Moral Value
- Surprise

The world is modeled as a tiny expedition: a child and a companion race toward
the last marker in an old map, discover a plastic object, face a temptation to
win unfairly, and choose the honest path when a surprise changes the stakes.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    detail: str
    path: str
    weather: str

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
class Relic:
    id: str
    label: str
    phrase: str
    lure: str
    moral: str
    surprise: str
    plastic: bool = True
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
class Rivalry:
    id: str
    stakes: str
    prize: str
    time_limit: int
    honest_rule: str
    cheat: str
    win: str
    lose: str
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


def _r_curiosity(world: World) -> list[str]:
    out = []
    explorer = world.get("child")
    if explorer.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curiosity",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    explorer.memes["wonder"] += 1
    out.append("__curiosity__")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    if world.facts.get("surprise_seen"):
        return out
    if world.facts.get("relic_found") and world.facts.get("honest_choice"):
        world.facts["surprise_seen"] = True
        world.get("child").memes["joy"] += 1
        world.get("companion").memes["joy"] += 1
        out.append("__surprise__")
    return out


CAUSAL_RULES = [
    Rule("curiosity", "mind", _r_curiosity),
    Rule("surprise", "story", _r_surprise),
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


def _do_search(world: World, narrate: bool = True) -> None:
    world.get("child").meters["travel"] += 1
    world.get("companion").meters["travel"] += 1
    world.facts["searched"] = True
    propagate(world, narrate=narrate)


def _discover(world: World, relic: Entity) -> None:
    world.facts["relic_found"] = True
    relic.meters["found"] += 1
    world.say(
        f"At the end of the path, they found {relic.phrase}, tucked inside a dusty box "
        f"like a prize from an old adventure."
    )


def _compete(world: World, rivalry: Rivalry, child: Entity, companion: Entity) -> None:
    child.memes["drive"] += 1
    companion.memes["drive"] += 1
    world.say(
        f"Then the two friends decided to compete to reach the stone arch first. "
        f"The rule was simple: whoever arrived honestly would get the {rivalry.prize}."
    )


def _tempt_cheat(world: World, rivalry: Rivalry, child: Entity, companion: Entity) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"The wind tossed a shortcut sign, and for a moment it felt easy to use the "
        f"{rivalry.cheat} instead of following the path."
    )


def _choose_moral(world: World, rivalry: Rivalry, child: Entity, companion: Entity) -> None:
    child.memes["moral_value"] += 1
    companion.memes["moral_value"] += 1
    world.facts["honest_choice"] = True
    world.say(
        f"{companion.id} looked at {child.id} and said, "
        f'"{rivalry.honest_rule}" {rivalry.cheat} would not count.'
    )
    world.say(
        f"{child.id} nodded and chose the honest path, even though it was slower."
    )


def _surprise_reveal(world: World, relic: Relic) -> None:
    world.say(
        f"That was when the surprise came: the {relic.label} was not treasure at all, "
        f"but a map marker with one last clue hidden inside."
    )
    world.say(
        f"The clue pointed to omega, the final camp beyond the ridge, and suddenly the "
        f"whole journey felt bigger than the race."
    )


def _ending(world: World) -> None:
    child = world.get("child")
    companion = world.get("companion")
    world.say(
        f"In the end, {child.id} and {companion.id} reached omega together, dusty and smiling."
    )
    world.say(
        "They had competed, but they had not cheated, and that made the victory feel bright and clean."
    )


def tell(setting: Setting, relic: Relic, rivalry: Rivalry, child_name: str = "Milo",
         child_gender: str = "boy", companion_name: str = "Nia",
         companion_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="explorer"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))

    child.memes["curiosity"] = 1.0
    companion.memes["curiosity"] = 1.0

    world.say(
        f"On a windy afternoon, {child.id} and {companion.id} followed an old trail through {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"{child.id} kept asking questions, because curiosity made every rock and shadow feel important."
    )

    world.para()
    _do_search(world)
    _discover(world, world.add(Entity(id="relic", kind="thing", type="thing", label=relic.label)))
    _compete(world, rivalry, child, companion)
    _tempt_cheat(world, rivalry, child, companion)

    world.para()
    _choose_moral(world, rivalry, child, companion)
    _surprise_reveal(world, relic)
    _ending(world)

    world.facts.update(
        child=child,
        companion=companion,
        parent=parent,
        setting=setting,
        relic=relic,
        rivalry=rivalry,
        honest_choice=True,
        relic_found=True,
        surprise_seen=True,
    )
    return world


SETTINGS = {
    "ridge": Setting(
        "ridge",
        "the ridge trail",
        "Below them, the valley looked like a green sea, and the path curled toward a stone arch.",
        "the ridge path",
        "windy",
    ),
    "cove": Setting(
        "cove",
        "the hidden cove",
        "The water flashed silver between the rocks, and a narrow path led toward the cliffs.",
        "the cliff path",
        "bright",
    ),
    "ruins": Setting(
        "ruins",
        "the old ruins",
        "Broken walls stood like sleepy giants, and vines wrapped around every corner.",
        "the ruin path",
        "quiet",
    ),
}

RELICS = {
    "token": Relic(
        "token",
        "plastic token",
        "a small plastic token with a shiny star on it",
        "it looked valuable enough to make anyone curious",
        "the right thing was to return what you find",
        "it turned out to be only a marker, not treasure",
        tags={"plastic", "surprise"},
    ),
    "compass": Relic(
        "compass",
        "plastic compass",
        "a cracked plastic compass in a bright blue shell",
        "it looked like it might lead to hidden treasure",
        "good explorers tell the truth when they find something",
        "inside was a tiny note folded into the lid",
        tags={"plastic", "surprise"},
    ),
    "badge": Relic(
        "badge",
        "plastic badge",
        "a faded plastic badge with an omega symbol",
        "it gleamed in the grass like something important",
        "a moral choice can matter more than winning",
        "it hid a secret message under the back clip",
        tags={"omega", "plastic", "surprise"},
    ),
}

RIVALRIES = {
    "race": Rivalry(
        "race",
        "the finish line at the stone arch",
        "a small ribbon",
        1,
        "The honest path is the only path that counts",
        "a shortcut under the roots",
        "the ribbon",
        "the race",
        tags={"compete", "moral"},
    ),
    "treasure_run": Rivalry(
        "treasure_run",
        "the last camp marker",
        "the brass whistle",
        1,
        "Winning should never mean tricking someone",
        "cutting across the brush",
        "the whistle",
        "the run",
        tags={"compete", "moral"},
    ),
}

NAMES_GIRL = ["Nia", "Mina", "Zoe", "Ava", "Lina", "Maya"]
NAMES_BOY = ["Milo", "Theo", "Jasper", "Noah", "Eli", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    relic: str
    rivalry: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid in RELICS:
            for vid in RIVALRIES:
                if "plastic" in RELICS[rid].tags and "compete" in RIVALRIES[vid].tags:
                    combos.append((sid, rid, vid))
    return combos


def explain_rejection(_: Relic, __: Rivalry) -> str:
    return "(No story: the domain needs a plastic relic, a fair competition, and a moral choice.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld about curiosity, moral choice, surprise, and a plastic omega clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--rivalry", choices=RIVALRIES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.relic and args.rivalry:
        if (args.setting, args.relic, args.rivalry) not in valid_combos():
            raise StoryError(explain_rejection(RELICS[args.relic], RIVALRIES[args.rivalry]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.relic is None or c[1] == args.relic)
              and (args.rivalry is None or c[2] == args.rivalry)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, relic, rivalry = rng.choice(sorted(combos))
    child_gender = rng.choice(["boy", "girl"])
    companion_gender = "girl" if child_gender == "boy" else "boy"
    child = rng.choice(NAMES_BOY if child_gender == "boy" else NAMES_GIRL)
    companion = rng.choice(NAMES_GIRL if companion_gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, relic, rivalry, child, child_gender, companion, companion_gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an Adventure-style story that includes the words "{f["relic"].label_word}", "compete", and "omega".',
        f"Tell a child-friendly adventure where {f['child'].id} and {f['companion'].id} find a plastic clue, compete fairly, and learn a moral lesson.",
        f"Write a surprise ending about a plastic object that turns out to be a clue to omega.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, companion, relic, rivalry = f["child"], f["companion"], f["relic"], f["rivalry"]
    return [
        QAItem(
            question="What were the children doing?",
            answer=f"They were exploring an old path, then they decided to compete to reach the finish first. The competition mattered, but they still chose to be honest."
        ),
        QAItem(
            question=f"What did {child.id} almost do instead of taking the fair path?",
            answer=f"{child.id} almost used a shortcut, but {companion.id} reminded {child.pronoun('object')} that the honest path is the only path that counts. {child.id} listened and chose the slower way."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The plastic {relic.label} was not treasure at all. It was a clue that pointed to omega, which made the whole adventure mean something bigger."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does plastic mean?",
            answer="Plastic is a man-made material that can be shaped into many things, like toys, bottles, and little tools."
        ),
        QAItem(
            question="What does omega mean?",
            answer="Omega often means the last or final one in a group, so it can be used for the end of a trail or a final clue."
        ),
        QAItem(
            question="Why is curiosity helpful in an adventure?",
            answer="Curiosity helps a character notice clues and ask questions. That can lead to discoveries that the character would miss if they did not look closely."
        ),
        QAItem(
            question="What is moral value in a story?",
            answer="Moral value is the good choice a character makes, like telling the truth, sharing fairly, or refusing to cheat."
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ridge", "badge", "race", "Milo", "boy", "Nia", "girl", "mother"),
    StoryParams("cove", "compass", "treasure_run", "Ava", "girl", "Theo", "boy", "father"),
    StoryParams("ruins", "token", "race", "Finn", "boy", "Maya", "girl", "mother"),
]


ASP_RULES = r"""
valid(S,R,V) :- setting(S), relic(R), rivalry(V), plastic(R), compete(V).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.plastic:
            lines.append(asp.fact("plastic", rid))
    for vid in RIVALRIES:
        lines.append(asp.fact("rivalry", vid))
        lines.append(asp.fact("compete", vid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        raise StoryError(f"Smoke test failed: {exc}") from exc
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        RELICS[params.relic],
        RIVALRIES[params.rivalry],
        params.child,
        params.child_gender,
        params.companion,
        params.companion_gender,
        params.parent,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, r, v in asp_valid_combos():
            print(f"  {s:8} {r:10} {v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} & {p.companion}: {p.relic} / {p.rivalry}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
