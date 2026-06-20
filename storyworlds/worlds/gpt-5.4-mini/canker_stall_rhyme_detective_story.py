#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/canker_stall_rhyme_detective_story.py
=====================================================================

A standalone story world for a tiny, rhyming detective tale.

Premise
-------
A child detective visits a market stall, notices a cankered fruit clue, and
solves a small mystery with a calm helper and a sensible ending.

Design notes
------------
- The story is driven by simulated world state, not a frozen paragraph.
- The world uses typed entities with physical meters and emotional memes.
- The prose is child-facing, concrete, and lightly rhymed.
- The required seed words "canker" and "stall" are part of the world model and
  can appear in the story naturally.
- ASP parity is included for the reasonableness gate and the ending choice.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/canker_stall_rhyme_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/canker_stall_rhyme_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/canker_stall_rhyme_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/canker_stall_rhyme_detective_story.py --verify
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
SENSE_MIN = 2


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
    scene: str
    weather: str
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
class Clue:
    id: str
    label: str
    phrase: str
    tell: str
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
class Mystery:
    id: str
    label: str
    cause: str
    solution: str
    fix: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mystery"] < THRESHOLD:
            continue
        if e.id in world.fired:
            continue
        world.fired.add((e.id, "worry"))
        for kid in list(world.entities.values()):
            if kid.role == "detective":
                kid.memes["focus"] += 1
        out.append("__mystery__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry)]


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


def rhyme(a: str, b: str) -> str:
    return f"{a} / {b}"


def reasonableness_gate(clue: Clue, mystery: Mystery) -> bool:
    return clue.id in {"canker_clue", "loose_thread", "muddy_boot"} and mystery.id in {"missing_stamp", "lost_receipt"}


def sensible_mysteries() -> list[Mystery]:
    return [m for m in MYSTERIES.values() if m.id != "fake_alarm"]


def best_fix() -> Mystery:
    return max(MYSTERIES.values(), key=lambda m: m.tags.__len__())


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get(clue_id).meters["mystery"] += 1
    propagate(sim, narrate=False)
    detective = next(e for e in sim.entities.values() if e.role == "detective")
    return {"focus": detective.memes["focus"], "mystery": sim.get(clue_id).meters["mystery"]}


def setup(world: World, det: Entity, helper: Entity, setting: Setting, clue: Clue) -> None:
    det.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {setting.place}, beneath a striped little stall, {det.id} began to prowl. "
        f"{setting.scene}"
    )
    world.say(
        f"{det.id} had a keen little nose for clues and a bright little spark, "
        f"and {helper.id} came along to help."
    )


def notice(world: World, det: Entity, clue: Clue) -> None:
    det.meters["mystery"] += 1
    world.say(
        f"Then {det.id} spotted {clue.phrase}, and the day grew still. "
        f"{clue.tell}"
    )


def ponder(world: World, det: Entity, clue: Clue) -> None:
    pred = predict(world, clue.id)
    det.memes["focus"] += 1
    world.facts["pred_focus"] = pred["focus"]
    world.say(
        f'"A clue this odd can make a crowd feel awed," {det.id} said, with a nod. '
        f'"But a good clue points clean, not mean."'
    )


def inspect(world: World, det: Entity, helper: Entity, clue: Clue, mystery: Mystery) -> None:
    helper.meters["help"] += 1
    world.say(
        f"{helper.id} leaned in slow and said, "
        f'"No need to race; we will trace." '
        f"Together they checked the stall, the cloth, and the crate."
    )
    if clue.id == "canker_clue":
        world.say(
            f"{clue.label.capitalize()} showed the fruit was sick, not hid by trick. "
            f"The canker was the mark, not a prank in the dark."
        )


def solve(world: World, det: Entity, helper: Entity, mystery: Mystery, setting: Setting) -> None:
    det.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, the puzzle fell in place: the stall's missing stamp had slid "
        f"behind the flour bin. The clue was plain, and the path was sane."
    )
    world.say(
        f"The helper grinned, the detective shone, and {setting.place} felt bright "
        f"as a kite."
    )
    world.say(
        f"They set the bin back right, and the little stall stood neat and still."
    )


def tell(setting: Setting, clue: Clue, mystery: Mystery,
         detective_name: str = "Mina", detective_gender: str = "girl",
         helper_name: str = "Uncle Ray", helper_gender: str = "man") -> World:
    world = World()
    det = world.add(Entity(detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    stall = world.add(Entity("stall", type="stall", label="the stall"))
    clue_ent = world.add(Entity(clue.id, type="clue", label=clue.label))
    stamp = world.add(Entity("stamp", type="thing", label="the missing stamp"))

    setup(world, det, helper, setting, clue)
    world.para()
    notice(world, det, clue)
    ponder(world, det, clue)
    inspect(world, det, helper, clue, mystery)
    world.para()
    solve(world, det, helper, mystery, setting)

    world.facts.update(
        detective=det, helper=helper, stall=stall, clue=clue_ent, mystery=mystery,
        setting=setting, stamp=stamp
    )
    return world


SETTINGS = {
    "market": Setting("market", "the market", "Rows of fruit shone under red and gold cloth.", "bright"),
    "fair": Setting("fair", "the fair", "Lanterns swung above the stalls, one by one.", "soft"),
}

CLUES = {
    "canker_clue": Clue("canker_clue", "canker", "a cankered apple", "One apple had a brown canker mark that looked like a tiny map.", {"canker"}),
    "loose_thread": Clue("loose_thread", "loose thread", "a loose red thread", "A loose red thread tugged from the awning like a shy little snake.", {"thread"}),
    "muddy_boot": Clue("muddy_boot", "muddy boot", "a muddy boot print", "A muddy boot print sat by the crate, round and neat.", {"mud"}),
}

MYSTERIES = {
    "missing_stamp": Mystery("missing_stamp", "missing stamp", "a tiny stamp slipped away", "the stamp was hidden", "put the stamp back", {"stamp", "find"}),
    "lost_receipt": Mystery("lost_receipt", "lost receipt", "a receipt fluttered free", "the receipt was under the basket", "pin the paper down", {"paper", "find"}),
    "fake_alarm": Mystery("fake_alarm", "fake alarm", "no real clue at all", "nothing was wrong", "say sorry", {"weak"}),
}

GIRL_NAMES = ["Mina", "Lina", "Rosa", "Tia", "Nia"]
BOY_NAMES = ["Pip", "Noah", "Evan", "Theo", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CLUES.items():
            for mid, m in MYSTERIES.items():
                if reasonableness_gate(c, m):
                    combos.append((sid, cid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    mystery: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
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
    "canker": [("What is canker?", "Canker is a bad mark or sore on a plant or fruit. It means something is wrong with the fruit, not that the fruit is pretending.")],
    "stall": [("What is a stall?", "A stall is a small place where people sell things at a market or fair.")],
    "detective": [("What does a detective do?", "A detective looks for clues and thinks carefully to solve a mystery.")],
    "clue": [("What is a clue?", "A clue is a small sign that helps you figure out what happened.")],
    "fruit": [("Why do people check fruit at a stall?", "People check fruit to make sure it looks fresh and good to eat.")],
}
ORDER = ["canker", "stall", "detective", "clue", "fruit"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming detective story for a child that includes the words "{f["clue"].label}" and "stall".',
        f"Tell a tiny mystery about {f['detective'].id} at {f['setting'].place} where a clue about {f['clue'].label} leads to a calm solution.",
        f'Write a story in gentle rhyme where a child detective spots {f["clue"].phrase} and solves a problem at a market stall.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {det.id}, a child detective, and {helper.id}, who helps solve the mystery at {setting.place}. They work together like a small team."
        ),
        QAItem(
            question=f"What clue did {det.id} notice?",
            answer=f"{det.id} noticed {clue.phrase}. The clue mattered because it pointed the detective toward the real answer instead of a guess."
        ),
        QAItem(
            question="How did the mystery end?",
            answer="It ended calmly and neatly. The missing stamp was found, the stall was set right, and the whole scene felt tidy again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags) | {"stall", "detective", "clue"}
    out: list[QAItem] = []
    for key in ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, _ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "canker_clue", "missing_stamp", "Mina", "girl", "Uncle Ray", "man"),
    StoryParams("fair", "loose_thread", "lost_receipt", "Pip", "boy", "Aunt Jo", "woman"),
]


def explain_rejection(clue: Clue, mystery: Mystery) -> str:
    return f"(No story: this clue and mystery do not make a clean detective puzzle. Try a real clue with a solvable mystery.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,M) :- setting(S), clue(C), mystery(M), sensible(C,M).
sensible(C,M) :- clue(C), mystery(M), not weak_mystery(M).
weak_mystery(fake_alarm).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, mystery=None, detective=None, detective_gender=None, helper=None, helper_gender=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming child detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, mystery = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(["Aunt Jo", "Uncle Ray", "Mr. Lee", "Ms. May"])
    return StoryParams(setting, clue, mystery, detective, detective_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], MYSTERIES[params.mystery],
                 params.detective, params.detective_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
