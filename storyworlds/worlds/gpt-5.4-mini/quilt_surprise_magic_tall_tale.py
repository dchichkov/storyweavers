#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quilt_surprise_magic_tall_tale.py
=================================================================

A standalone story world for a tiny Tall Tale style domain: a child sews,
hunts for a missing quilt, and a surprising bit of magic turns worry into a
wonderful reveal. The world simulates physical state in meters and emotional
state in memes so the prose follows what changed, not a frozen template.

The seed words and style shape the world:
- quilt
- Surprise
- Magic
- Tall Tale

This script follows the shared storyworld contract.
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
MAGIC_MIN = 1.0


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
    sky: str
    tall_tale_flavor: str

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
class Quilt:
    id: str
    name: str
    pattern: str
    size: str
    hides: str
    feels: str
    magical: bool = False
    prized: bool = True
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
class Surprise:
    id: str
    source: str
    reveal: str
    sparkle: str
    delight: str
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
class Magic:
    id: str
    kind: str
    power: int
    method: str
    side_effect: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_magic_glow(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["magic"] < MAGIC_MIN:
            continue
        sig = ("magic_glow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["wonder"] += 1
        out.append("__magic__")
    return out


CAUSAL_RULES = [Rule("magic_glow", "magic", _r_magic_glow)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for set_id in SETTINGS:
        for qu_id, q in QUILTS.items():
            if not q.prized:
                continue
            for sur_id, sur in SURPRISES.items():
                if qu_id in sur.tags or "quilt" in sur.tags:
                    for ma_id, ma in MAGICS.items():
                        if ma.power >= 1:
                            combos.append((set_id, qu_id, sur_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quilt: str
    surprise: str
    magic: str
    child: str
    child_gender: str
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


SETTINGS = {
    "farm": Setting("farm", "a windy farm", "big blue sky", "bigger than a barn-cat's yawn"),
    "cabin": Setting("cabin", "a hill cabin", "golden sunset", "wider than a moonlit porch"),
    "fair": Setting("fair", "a county fair", "bright flags", "louder than a brass-band sneeze"),
}

QUILTS = {
    "patchwork": Quilt("patchwork", "the patchwork quilt", "stars and squares", "bed-sized", "a warm bed", "soft and heavy", magical=True, tags={"quilt"}),
    "blue": Quilt("blue", "the blue quilt", "blue moons and silver stitches", "bed-sized", "a rocking chair", "cool and silky", magical=True, tags={"quilt"}),
}

SURPRISES = {
    "hidden_note": Surprise("hidden_note", "a folded note", "a note tucked in the hem", "a little gold sparkle", "a happy secret", tags={"quilt"}),
    "moonbeam": Surprise("moonbeam", "moonlight", "moonlight slipping through a window", "a silver twinkle", "a wonder-struck laugh", tags={"quilt"}),
}

MAGICS = {
    "glow": Magic("glow", "glow", 2, "hum a tune and tap three stitches", "the quilt gives off a lantern-soft shine", tags={"magic"}),
    "float": Magic("float", "float", 1, "whisper a wish and lift a corner", "the quilt rises like a stubborn kite", tags={"magic"}),
}


GIRL_NAMES = ["Lily", "Mira", "Nora", "Poppy", "June", "Tessa"]
BOY_NAMES = ["Finn", "Theo", "Jasper", "Milo", "Ben", "Eli"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quilt surprise storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quilt", choices=QUILTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def explain_rejection() -> str:
    return "(No story: that combination does not create a believable quilt surprise.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quilt is None or c[1] == args.quilt)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, quilt, surprise = rng.choice(sorted(combos))
    magic = args.magic or rng.choice(sorted(MAGICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, quilt, surprise, magic, name, gender, parent)


def setting_line(setting: Setting) -> str:
    return f"It was {setting.place}, under a {setting.sky}, with a feel {setting.tall_tale_flavor}."


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    quilt = world.add(Entity("quilt", type="quilt", label=QUILTS[params.quilt].name))
    world.facts.update(hero=hero, parent=parent, quilt=quilt, params=params)

    setting = SETTINGS[params.setting]
    q = QUILTS[params.quilt]
    sur = SURPRISES[params.surprise]
    ma = MAGICS[params.magic]

    hero.memes["hope"] += 1
    world.say(f"{hero.id} lived near {setting.place}. {setting_line(setting)}")
    world.say(f"{hero.id} loved {q.name}, for it felt {q.feels} and kept the bed as warm as a tucked-in puppy.")
    world.say(f"One day, {hero.id} noticed something strange: {sur.reveal}, and that was no ordinary sight.")
    world.para()
    world.say(f'{hero.id} laughed, then gasped. "Oh my stars, what a surprise!" {hero.pronoun()} said.')
    hero.meters["curiosity"] += 1
    hero.meters["magic"] += 1
    propagate(world, narrate=False)
    q_entity = q
    world.say(f"{hero.id} remembered an old trick: {ma.method}.")
    world.say(f"When {hero.id} tried it, {q_entity.name} answered with magic of its own.")
    q_entity.meters["magic"] += ma.power
    q_entity.meters["revealed"] += 1
    q_entity.meters["glow"] += 1
    hero.memes["wonder"] += 1
    world.para()
    world.say(f"The stitches shimmered, and the surprise turned bright as noon in a thunderstorm.")
    if sur.id == "hidden_note":
        world.say("Out slid a folded note, hidden so long it seemed the quilt had been keeping a secret for the whole county.")
    else:
        world.say("A silver moonbeam danced along the squares, as if the night itself had stitched a smile into the cloth.")
    world.say(f"{parent.label_word.capitalize()} came in with a grin as wide as a wagon wheel, and {hero.id} held up {q.name}.")
    world.say(f'"Well now," said {parent.label_word}, "that quilt has a tale bigger than a barn and twice as bright."')
    hero.memes["joy"] += 2
    parent.memes["joy"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a tall tale for a child about a quilt and a surprise, using the word "quilt" and a little magic.',
        f"Tell a story where {p.child} finds a magical surprise in {QUILTS[p.quilt].name} and the grown-up is delighted.",
        f"Write a child-friendly tall tale about {QUILTS[p.quilt].name}, {SURPRISES[p.surprise].reveal}, and a bit of magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    parent = f["parent"]
    q = QUILTS[p.quilt]
    sur = SURPRISES[p.surprise]
    ma = MAGICS[p.magic]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {p.child}, who found a magical surprise in {q.name}. {parent.label_word.capitalize()} was part of the happy ending too."
        ),
        QAItem(
            question="What surprise was hiding in the quilt?",
            answer=f"The surprise was {sur.reveal}. It felt like the quilt had been holding a secret until the right moment."
        ),
        QAItem(
            question="How did the magic change the quilt?",
            answer=f"{hero.id} used {ma.method}, and then {q.name} began to glow and shine. The magic made the surprise bright enough to see at once."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quilt?",
            answer="A quilt is a blanket made from pieces of cloth sewn together. It is often warm and soft."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect. It can make people gasp, laugh, or smile wide."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a make-believe power that can make impossible things happen. In stories, magic helps the tale feel wondrous."
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
    lines.append("== (3) World-knowledge questions ==")
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
        out.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
magic_present(Q) :- quilt(Q), quilt_magic(Q).
wonderful(Q) :- magic_present(Q).
surprising(Q) :- quilt(Q), surprise_in(Q).
valid_story(S, Q, U) :- setting(S), quilt(Q), surprise(U), magic_kind(M), magic_power(M, P), P >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUILTS.items():
        lines.append(asp.fact("quilt", qid))
        if q.magical:
            lines.append(asp.fact("quilt_magic", qid))
    for uid in SURPRISES:
        lines.append(asp.fact("surprise", uid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic_kind", mid))
        lines.append(asp.fact("magic_power", mid, m.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quilt=None, surprise=None, magic=None, name=None, gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
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
    StoryParams("farm", "patchwork", "hidden_note", "glow", "Lily", "girl", "mother"),
    StoryParams("cabin", "blue", "moonbeam", "float", "Theo", "boy", "father"),
    StoryParams("fair", "patchwork", "hidden_note", "glow", "Mira", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
