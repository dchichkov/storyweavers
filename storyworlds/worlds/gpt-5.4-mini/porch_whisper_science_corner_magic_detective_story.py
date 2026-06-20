#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/porch_whisper_science_corner_magic_detective_story.py
====================================================================================

A standalone story world for a tiny detective tale set in a science corner:
a child investigator hears a porch whisper, follows clues around a science table,
and uses a little bit of magic to reveal the truth without breaking anything.

Seed words:
- porch
- whisper

Setting:
- science corner

Features:
- Magic

Style:
- Detective Story
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
    has_porch: bool
    has_science_corner: bool

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
    phrase: str
    place: str
    sparkle: str
    hidden_by_magic: bool = False

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
class MagicTool:
    id: str
    name: str
    reveal: str
    gentle: bool = True

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
    suspect: str
    truth: str
    twist: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_curious(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.memes["curiosity"] >= THRESHOLD and ("curious", "child") not in world.fired:
        world.fired.add(("curious", "child"))
        child.memes["attention"] += 1
        out.append("The clues felt important enough to follow.")
    return out


def _r_magic_reveal(world: World) -> list[str]:
    out: list[str] = []
    magic = world.entities.get("magic")
    clue = world.entities.get("clue")
    if not magic or not clue:
        return out
    sig = ("reveal", clue.id)
    if clue.meters["hidden"] < THRESHOLD:
        return out
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["hidden"] = 0.0
    clue.meters["seen"] += 1
    if magic.memes["calm"] >= THRESHOLD:
        out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("curious", "social", _r_curious),
    Rule("magic_reveal", "magic", _r_magic_reveal),
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


def clue_covered_by_misleading_whisper(clue: Clue) -> bool:
    return clue.hidden_by_magic


def reasonableness_gate(setting: Setting, clue: Clue, tool: MagicTool) -> bool:
    return setting.has_porch and setting.has_science_corner and clue.place in {"porch", "science corner"} and tool.gentle


def predict_reveal(world: World, clue_id: str) -> bool:
    sim = world.copy()
    sim.get(clue_id).meters["hidden"] += 1
    propagate(sim, narrate=False)
    return sim.get(clue_id).meters["seen"] >= THRESHOLD


def setup(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {helper.id} worked in the science corner, "
        f"where jars, rulers, and paper strips waited for a new case."
    )
    world.say(
        f"By the porch, the air moved softly, and somebody had left behind a whisper of a clue."
    )


def clue_scene(world: World, child: Entity, clue: Entity, mystery: Mystery) -> None:
    clue.meters["hidden"] += 1
    world.say(
        f"{child.id} noticed a tiny sign near the beaker stand: a faint {mystery.suspect} of a {clue.label}. "
        f"It looked like it had been hidden on purpose."
    )
    world.say(
        f'"That is odd," {child.id} whispered. "I want to know what happened here."'
    )


def question_and_search(world: World, child: Entity, helper: Entity, clue: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} looked under the chart, beside the magnets, and even near the porch door."
    )
    world.say(
        f"{helper.id} waited patiently while {child.id} followed the trail, one careful step at a time."
    )


def use_magic(world: World, child: Entity, magic: MagicTool, clue: Entity) -> None:
    magic_ent = world.get("magic")
    magic_ent.memes["calm"] += 1
    world.say(
        f"Then {child.id} picked up {magic.name}. It did not boom or flash wildly; it only glowed gently in {child.pronoun('possessive')} hands."
    )
    world.say(
        f'"{magic.reveal}," {child.id} whispered, and the soft magic touched the clue like moonlight.'
    )
    propagate(world, narrate=True)


def reveal_truth(world: World, child: Entity, helper: Entity, clue: Entity, mystery: Mystery) -> None:
    world.say(
        f"The clue finally showed itself: {clue.label}, right where the porch breeze had nudged it."
    )
    world.say(
        f"{child.id} smiled and pointed to the answer. The mystery was not a trick at all; it was {mystery.truth}."
    )
    world.say(
        f"{helper.id} nodded. \"Good eyes,\" {helper.id} said. \"You solved it by listening, looking, and using gentle magic.\""
    )


def ending(world: World, child: Entity, helper: Entity, clue: Entity, mystery: Mystery) -> None:
    world.say(
        f"After that, the science corner felt bright and tidy again, and the porch was only a porch, not a puzzle."
    )
    world.say(
        f"{child.id} tucked the clue card back in place, still smiling at the little truth {mystery.twist}."
    )


def tell(setting: Setting, clue: Clue, magic: MagicTool, mystery: Mystery,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Teacher", helper_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.phrase))
    world.add(Entity(id="magic", type="thing", label=magic.name))
    world.facts["mystery"] = mystery
    world.facts["clue_cfg"] = clue
    world.facts["magic_cfg"] = magic

    setup(world, child, helper, setting)
    world.para()
    clue_scene(world, child, clue_ent, mystery)
    question_and_search(world, child, helper, clue_ent)
    world.para()
    use_magic(world, child, magic, clue_ent)
    reveal_truth(world, child, helper, clue_ent, mystery)
    world.para()
    ending(world, child, helper, clue_ent, mystery)

    world.facts.update(
        child=child,
        helper=helper,
        clue=clue_ent,
        revealed=clue_ent.meters["seen"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "science_corner": Setting("science_corner", "the science corner", True, True),
}

CLUES = {
    "whisper_note": Clue("whisper_note", "whisper note", "porch", "soft and secret", hidden_by_magic=True),
    "chalk_mark": Clue("chalk_mark", "chalk mark", "science corner", "pale and tiny", hidden_by_magic=True),
    "glimmer_tag": Clue("glimmer_tag", "glimmer tag", "science corner", "shiny and small", hidden_by_magic=True),
}

MAGIC_TOOLS = {
    "lantern": MagicTool("lantern", "a tiny magic lantern", "Reveal the hidden clue"),
    "magnifier": MagicTool("magnifier", "a magic magnifier", "Let the hidden thing show itself"),
    "star": MagicTool("star", "a pocket star charm", "Show me what is hidden"),
}

MYSTERIES = {
    "missing_label": Mystery("missing_label", "missing", "a label had blown from the porch onto the science table", "all along"),
    "borrowed_crayon": Mystery("borrowed_crayon", "borrowed", "a crayon had rolled off the porch shelf and hid by the beakers", "right there"),
    "paper_trail": Mystery("paper_trail", "paper", "a paper clue had fluttered from the porch into the science corner", "in the breeze"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Max", "Leo", "Noah", "Finn", "Theo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    magic: str
    mystery: str
    child: str
    child_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for mid, tool in MAGIC_TOOLS.items():
                if reasonableness_gate(setting, clue, tool):
                    combos.append((sid, cid, mid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    clue = f["clue_cfg"]
    return [
        f'Write a short detective story for a 3-to-5-year-old in the science corner that includes the words "porch" and "whisper".',
        f"Tell a gentle mystery story where {f['child'].id} follows a whispery clue from the porch and uses magic to solve {mystery.truth}.",
        f'Write a child-friendly detective story with a science corner, a porch clue, and gentle magic that reveals "{clue.phrase}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue_cfg = f["clue_cfg"]
    mystery = f["mystery"]
    qa = [
        ("Where does the story take place?",
         "It takes place in the science corner, where the child can look closely at clues and try a gentle experiment."),
        ("What clue did the child notice?",
         f"{child.id} noticed a {clue_cfg.phrase} that had come from the porch. It looked secret and a little magical."),
        ("How did the child solve the mystery?",
         f"{child.id} used a gentle magic tool to make the hidden clue show itself, then followed what it revealed."),
        ("What was the mystery really about?",
         f"It was really {mystery.truth}. The strange part was only that it had been hidden until the magic helped."),
    ]
    if f.get("revealed"):
        qa.append((
            "Why did the clue appear at the end?",
            "The magic made the hidden clue visible. Once the child used the soft glow, the clue could not stay tucked away anymore."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a whisper?",
         "A whisper is a very quiet way to talk, often used when someone does not want to disturb others."),
        ("What is a porch?",
         "A porch is a small area at the front of a house where people can stand or sit before going inside."),
        ("What is a science corner?",
         "A science corner is a small place with tools and materials for looking, sorting, measuring, and asking questions."),
        ("What does a magnifier do?",
         "A magnifier makes small things look bigger so they are easier to see."),
        ("Why should magic in a story stay gentle?",
         "Gentle magic keeps the story safe and calm, so the characters can solve a problem without causing harm."),
    ]
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("science_corner", "whisper_note", "lantern", "missing_label", "Mia", "girl", "Teacher", "woman"),
    StoryParams("science_corner", "chalk_mark", "magnifier", "borrowed_crayon", "Leo", "boy", "Teacher", "woman"),
    StoryParams("science_corner", "glimmer_tag", "star", "paper_trail", "Nora", "girl", "Teacher", "woman"),
]


def explain_rejection(setting: Setting, clue: Clue, tool: MagicTool) -> str:
    return (
        f"(No story: this tiny detective tale needs the science corner, the porch, and a gentle magic tool. "
        f"The chosen clue or tool does not fit the premise.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "revealed" if True else "?"


ASP_RULES = r"""
valid(S, C, M) :- setting(S), clue(C), magic(M), science_corner(S), porch_clue(C), gentle_magic(M).
revealed :- chosen_clue(C), chosen_magic(M), hidden(C), gentle_magic(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("science_corner", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("porch_clue", cid))
        lines.append(asp.fact("hidden", cid))
    for mid in MAGIC_TOOLS:
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("gentle_magic", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, magic=None, mystery=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world in a science corner with gentle magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(Invalid setting.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, magic = rng.choice(sorted(combos))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or "woman"
    helper = args.helper or "Teacher"
    return StoryParams(setting, clue, magic, mystery, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], MAGIC_TOOLS[params.magic],
                 MYSTERIES[params.mystery], params.child, params.child_gender,
                 params.helper, params.helper_gender)
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
        print(f"{len(asp_valid_combos())} compatible stories")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
