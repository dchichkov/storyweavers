#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/noxious_problem_solving_bad_ending_bedtime_story.py
====================================================================================

A small standalone storyworld about a bedtime smell problem that the children try
to solve, but the ending stays bad: the noxious smell lingers, bedtime moves to a
different room, and the usual cozy night is ruined. The domain is intentionally
tiny and classical: a child, a parent, a source of the smell, a few reasonable
fixes, and a world state that drives the prose.

This script follows the Storyweavers storyworld contract:
- stdlib only
- StoryParams / build_parser / resolve_params / generate / emit / main
- QAItem / StoryError / StorySample from storyworlds/results.py
- --qa, --json, --trace, --asp, --verify, --show-asp, --all, -n, --seed
- Python reasonableness gate plus inline ASP twin
- generated stories with beginning, turn, and ending image
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Setting:
    id: str
    place: str
    cozy: str
    bedtime_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SmellSource:
    id: str
    label: str
    phrase: str
    noxious_word: str
    spreads: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    src = world.get("source")
    if src.meters["smell"] < THRESHOLD:
        return out
    sig = ("spread", src.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("child", "parent"):
        world.get(eid).memes["unease"] += 1
    out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", "social", _r_spread)]


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


def reasonableness_gate(source: SmellSource, remedy: Remedy) -> bool:
    return source.spreads and remedy.sense >= SENSE_MIN


def could_fix(source: SmellSource, remedy: Remedy) -> bool:
    return remedy.power >= 2 if source.spreads else False


def choose_best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.sense)


def predict_smell(world: World, source: SmellSource) -> dict:
    sim = world.copy()
    sim.get("source").meters["smell"] += 1
    propagate(sim, narrate=False)
    return {"still_there": sim.get("source").meters["smell"] >= THRESHOLD,
            "unease": sim.get("parent").memes["unease"]}


def setup(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    parent.memes["care"] += 1
    world.say(
        f"It was bedtime in {setting.place}. {setting.cozy} {setting.bedtime_line}"
    )
    world.say(f"{child.id} yawned and snuggled close to the blankets.")


def notice(world: World, child: Entity, source: SmellSource) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} wrinkled {child.pronoun('possessive')} nose. "
        f"Something in the room smelled {source.noxious_word}."
    )


def explain(world: World, parent: Entity, source: SmellSource) -> None:
    parent.memes["unease"] += 1
    world.say(
        f'{parent.id} sniffed once and frowned. "That smell is from {source.phrase}. '
        f'We need to fix it before we can sleep."'
    )


def try_fix(world: World, parent: Entity, source: SmellSource, remedy: Remedy) -> None:
    pred = predict_smell(world, source)
    world.facts["predicted_unease"] = pred["unease"]
    world.say(
        f"{parent.id} tried a few careful things. "
        f"{remedy.text.replace('{source}', source.label)}."
    )


def fail_fix(world: World, parent: Entity, source: SmellSource, remedy: Remedy) -> None:
    source.meters["smell"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the room still smelled {source.noxious_word}, and the little fix "
        f"did not win against it."
    )
    world.say(f"{parent.id} sighed because {remedy.fail.replace('{source}', source.label)}.")


def bad_end(world: World, child: Entity, parent: Entity, setting: Setting, source: SmellSource) -> None:
    child.memes["disappointed"] += 1
    parent.memes["tired"] += 1
    world.say(
        f"So they carried the pillows to the couch and tried to make the best of it."
    )
    world.say(
        f"Even there, the noxious smell kept sneaking along in their noses, and "
        f"the bedroom stayed too stinky for a cozy sleep."
    )
    world.say(
        f"At last, {child.id} curled up under a thin blanket on the couch while "
        f"{parent.id} sat beside {child.id} and listened to the quiet, unhappy night."
    )


def tell(setting: Setting, source: SmellSource, remedy: Remedy,
         child_name: str = "Mina", child_type: str = "girl",
         parent_name: str = "Mom", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent"))
    src = world.add(Entity(id="source", label=source.label))
    world.facts["setting"] = setting
    world.facts["source_cfg"] = source
    world.facts["remedy"] = remedy

    setup(world, child, parent, setting)
    world.para()
    notice(world, child, source)
    explain(world, parent, source)
    world.para()
    try_fix(world, parent, source, remedy)
    if could_fix(source, remedy):
        source.meters["smell"] = 0.0
        world.say(f"The room softened for a moment, but the smell came back.")
    else:
        fail_fix(world, parent, source, remedy)
    world.para()
    bad_end(world, child, parent, setting, source)

    world.facts.update(child=child, parent=parent, source=src, outcome="bad")
    return world


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "The lamp was low, the sheets were smooth,", "and the room was quiet."),
    "nursery": Setting("nursery", "the nursery", "The teddy bear sat by the pillow,", "and the nightlight glowed softly."),
    "attic": Setting("attic", "the attic room", "The little window was shut,", "and the old floorboards creaked."),
}

SOURCES = {
    "trash": SmellSource("trash", "the trash can", "the trash can by the bed", "noxious", True, {"trash", "smell"}),
    "sock": SmellSource("sock", "the lost sock", "a lost sock under the blanket", "noxious", True, {"sock", "smell"}),
    "milk": SmellSource("milk", "the spilled milk cup", "a spilled milk cup under the chair", "noxious", True, {"milk", "smell"}),
}

REMEDIES = {
    "window": Remedy("window", 3, 1, "opened the window to let the air move", "opened the window, but the smell still hung there", "opened the window to let the air move", {"air"}),
    "spray": Remedy("spray", 2, 1, "sprayed the curtain with lavender mist", "sprayed the room, but the smell only mixed with it", "sprayed the room with lavender mist", {"spray"}),
    "basket": Remedy("basket", 3, 2, "carried the trash outside and tied a new bag in the bin", "carried the trash, but the smell had already soaked into the room", "carried the trash outside", {"trash"}),
    "sleepout": Remedy("sleepout", 2, 1, "pulled the blankets onto the floor and tried to sleep there", "moved the blankets, but the smell followed them", "moved the blankets", {"sleep"}),
}

STORY_PARAMS = None  # placeholder avoided by contract? not used.


@dataclass
class StoryParams:
    setting: str
    source: str
    remedy: str
    child_name: str
    child_type: str
    parent_name: str
    parent_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for src in SOURCES.values():
            for rid, rem in REMEDIES.items():
                if reasonableness_gate(src, rem):
                    combos.append((sid, src.id, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a noxious smell and a failed fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--parent")
    ap.add_argument("--type", choices=["girl", "boy"])
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
    if args.source and args.remedy:
        if not reasonableness_gate(SOURCES[args.source], REMEDIES[args.remedy]):
            raise StoryError("(No story: this smell-and-fix pairing is not reasonable.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.source is None or c[1] == args.source)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, source, remedy = rng.choice(sorted(combos))
    src = SOURCES[source]
    child_type = args.type or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(["Mina", "Lina", "Noah", "Eli", "Tia", "Owen"])
    parent_type = "mother" if child_type == "girl" else "father"
    parent_name = args.parent or ("Mom" if parent_type == "mother" else "Dad")
    return StoryParams(setting, source, remedy, child_name, child_type, parent_name, parent_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "noxious" and a problem-solving attempt that does not fully work.',
        f"Tell a cozy-but-sad story where {f['child'].id} notices a noxious smell in {f['setting'].place} and {f['parent'].id} tries to fix it, but bedtime still goes badly.",
        f"Write a simple bedtime story about a smell problem, a careful fix, and an ending where the room is still not pleasant enough for sleep.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, src, setting = f["child"], f["parent"], f["source_cfg"], f["setting"]
    remedy = f["remedy"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id} at bedtime in {setting.place}. They are the ones trying to deal with the smell."),
        ("What was wrong in the room?",
         f"There was a noxious smell coming from {src.phrase}. That made bedtime hard because the room did not feel cozy anymore."),
        ("What did the parent try to do?",
         f"{parent.id} tried to {remedy.qa_text}. It was a careful idea, but it did not fully solve the problem."),
        ("How did the story end?",
         f"It ended badly: the smell was still there, so they had to sleep in a different place. The bedroom did not become fresh and cozy."),
    ]
    return qa


KNOWLEDGE = {
    "smell": [("What is a smell?",
               "A smell is something your nose notices in the air. Some smells are nice, and some smells are strong or bad.")],
    "noxious": [("What does noxious mean?",
                 "Noxious means very bad or harmful, like a smell that feels awful and makes you want to get away.")],
    "bedtime": [("What is bedtime?",
                  "Bedtime is the time when children get ready to sleep. People usually want things to be calm, dark, and cozy then.")],
    "trash": [("Why should trash be taken out?",
                "Trash can make a room smell bad if it stays inside too long. Taking it out helps the room stay fresh.")],
    "air": [("Why do people open a window?",
             "People open a window to let fresh air move through a room. Moving air can help with stale or bad smells.")],
}

def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source_cfg"].tags)
    tags.add("bedtime")
    if "air" in world.facts["remedy"].tags:
        tags.add("air")
    out = []
    for key in ["smell", "noxious", "bedtime", "trash", "air"]:
        if key in tags or key in {"smell", "noxious", "bedtime"}:
            out.extend(KNOWLEDGE[key])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "trash", "window", "Mina", "girl", "Mom", "mother"),
    StoryParams("nursery", "sock", "spray", "Noah", "boy", "Dad", "father"),
    StoryParams("attic", "milk", "basket", "Lina", "girl", "Mom", "mother"),
]


def explain_remedy(remedy: Remedy) -> str:
    allowed = " / ".join(sorted(r.id for r in REMEDIES.values() if r.sense >= SENSE_MIN))
    return f"(Refusing remedy '{remedy.id}': it is too weak or too silly for this world. Try: {allowed}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if src.spreads:
            lines.append(asp.fact("spreads", sid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, So, R) :- setting(S), source(So), remedy(R), spreads(So), sense(R, Sen), sense_min(M), Sen >= M.
outcome(bad) :- valid(_, _, _).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, source=None, remedy=None, child=None, parent=None, type=None), random.Random(7)))
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SOURCES[params.source], REMEDIES[params.remedy],
                 params.child_name, params.child_type, params.parent_name, params.parent_type)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
