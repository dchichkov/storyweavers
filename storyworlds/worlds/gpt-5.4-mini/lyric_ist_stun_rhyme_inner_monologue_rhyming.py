#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lyric_ist_stun_rhyme_inner_monologue_rhyming.py
===============================================================================

A small, standalone storyworld about a young lyricist, a surprising stage moment,
and a rhyming turn that settles the crowd.

Seed words:
- lyric-ist
- stun

Features:
- Rhyme
- Inner Monologue

Style:
- Rhyming Story

The world builds a tiny performance scene: a child prepares a rhyme, worries
about forgetting the lines, gets stunned by a sudden mishap, then finds a calm
fix and finishes with a bright final verse. The prose is driven by world state,
not by a frozen paragraph template.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Scene:
    id: str
    place: str
    event: str
    audience: str
    sound: str
    ending_glow: str

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
class Mishap:
    id: str
    trigger: str
    effect: str
    can_spook: bool = True

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
class Fix:
    id: str
    tool: str
    action: str
    success_line: str
    fail_line: str
    sense: int = 2
    power: int = 2

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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    stage = world.entities.get("stage")
    if not stage:
        return out
    for e in list(world.entities.values()):
        if e.meters["startled"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        stage.meters["tension"] += 1
        for kid in list(world.entities.values()):
            if kid.role in {"lyricist", "helper"}:
                kid.memes["nerves"] += 1
        out.append("__spook__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook)]


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


def calm_or_stun(scene: Scene, mishap: Mishap) -> bool:
    return scene.id == "open_mic" and mishap.can_spook


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fireless_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def can_stun_audience(mishap: Mishap, scene: Scene) -> bool:
    return mishap.trigger in {"dropped_card", "broken_rhythm", "mic_feedback"} and scene.id in {"open_mic", "school_show"}


def outcome_power(fix: Fix, surprise: int) -> bool:
    return fix.power >= surprise


def do_rehearse(world: World, lyricist: Entity, helper: Entity, scene: Scene) -> None:
    lyricist.memes["hope"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In {scene.place}, {lyricist.id} and {helper.id} made a small stage bright, "
        f"with a chair for a throne and a page for a light."
    )
    world.say(
        f"{lyricist.id} was a lyric-ist with a pocket of rhyme, "
        f"and {helper.id} kept time with a tap-tap chime."
    )


def inner_monologue(world: World, lyricist: Entity, scene: Scene) -> None:
    lyricist.memes["nerves"] += 1
    world.say(
        f"{lyricist.id} breathed in slow. \"I can do this,\" {lyricist.pronoun()} thought. "
        f"\"One line, then two -- keep the beat, keep the view.\""
    )
    world.say(
        f"Inside {lyricist.pronoun('possessive')} head, a tiny voice said, "
        f"\"If the rhyme stays kind, the room will unwind.\""
    )


def begin_performance(world: World, lyricist: Entity, helper: Entity, scene: Scene) -> None:
    world.say(
        f"When the crowd gathered, {lyricist.id} stepped up to {scene.event}, "
        f"and the room went still with a hush and a thrum."
    )
    world.say(
        f"{helper.id} smiled from the side and gave {lyricist.pronoun('object')} a wink, "
        f"like a lantern saying, \"You know the trick.\""
    )


def mishap_hits(world: World, lyricist: Entity, helper: Entity, mishap: Mishap) -> None:
    lyricist.meters["startled"] += 1
    helper.meters["startled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {mishap.trigger.replace('_', ' ')} went wrong with a clatter and a zing; "
        f"it was enough to stun the singing."
    )
    world.say(
        f"{lyricist.id} froze for a blink, then heard {helper.id} say, "
        f"\"Stay with the rhyme -- we have time.\""
    )


def recover(world: World, lyricist: Entity, helper: Entity, fix: Fix, scene: Scene, surprise: int) -> bool:
    if not outcome_power(fix, surprise):
        world.say(
            f"{helper.id} tried {fix.fail_line}, but the moment stayed rough and the crowd was too much."
        )
        return False
    lyricist.memes["courage"] += 1
    helper.memes["support"] += 1
    lyricist.meters["startled"] = 0.0
    world.say(
        f"{helper.id} {fix.action}, and {fix.success_line}."
    )
    world.say(
        f"The hush turned soft, and {lyricist.id} found {scene.ending_glow}."
    )
    return True


def finale(world: World, lyricist: Entity, helper: Entity, scene: Scene) -> None:
    lyricist.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"With a clear breath, {lyricist.id} finished the song in a ring of light, "
        f"and {scene.audience} answered with smiles."
    )
    world.say(
        f"The last rhyme landed like a feather, and the stunned room began to hum."
    )
    world.say(
        f"{lyricist.id} bowed, grinning wide, and {helper.id} beamed beside {lyricist.pronoun('object')}."
    )


def tell(scene: Scene, mishap: Mishap, fix: Fix,
         lyricist_name: str = "Mara", lyricist_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy") -> World:
    world = World()
    lyricist = world.add(Entity(id=lyricist_name, kind="character", type=lyricist_gender, role="lyricist"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    stage = world.add(Entity(id="stage", type="stage", label="the stage"))

    do_rehearse(world, lyricist, helper, scene)
    inner_monologue(world, lyricist, scene)
    world.para()
    begin_performance(world, lyricist, helper, scene)
    mishap_hits(world, lyricist, helper, mishap)
    world.para()
    surprise = 2
    fixed = recover(world, lyricist, helper, fix, scene, surprise)
    if fixed:
        finale(world, lyricist, helper, scene)
    else:
        lyricist.memes["disappointment"] += 1
        world.say(
            f"{lyricist.id} took a deep breath and tried again, but the song lost its bright spark."
        )
    world.facts.update(
        lyricist=lyricist,
        helper=helper,
        scene=scene,
        mishap=mishap,
        fix=fix,
        stage=stage,
        fixed=fixed,
        stunned=lyricist.meters["startled"] >= THRESHOLD,
    )
    return world


SCENES = {
    "open_mic": Scene("open_mic", "the little café", "sing a rhyme at the open mic", "the crowd", "a soft clap", "a warm glow"),
    "school_show": Scene("school_show", "the school hall", "share a rhyme on the little stage", "the class", "a drumbeat", "a bright shine"),
    "story_corner": Scene("story_corner", "the library corner", "speak a rhyme beside the book rug", "the listeners", "a page-flip hush", "a gentle sparkle"),
}

MISHAPS = {
    "dropped_card": Mishap("dropped_card", "a verse card slipped", "the words skittered apart", True),
    "broken_rhythm": Mishap("broken_rhythm", "the drum beat skipped", "the rhyme lost its stride", True),
    "mic_feedback": Mishap("mic_feedback", "the mic gave a squeal", "the sound jumped like a cat", True),
}

FIXES = {
    "count_in": Fix("count_in", "counted the beat on fingers", "counted in, steady and sweet", "kept the song afloat", "counted, but the noise stayed too loud", 2, 2),
    "hum_tune": Fix("hum_tune", "hummed the tune under breath", "hummed a guide so the rhyme could slide", "tucked the song back on track", "hummed, but the moment still stalled", 2, 2),
    "simple_line": Fix("simple_line", "spoke one simple line", "said a short line to gather the rhyme", "made the room calm enough to listen", "spoke, but the crowd stayed stunned", 3, 3),
}

NAMES = ["Mara", "Pia", "Lia", "June", "Nina", "Owen", "Noah", "Ezra", "Theo", "Ivy"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    mishap: str
    fix: str
    lyricist_name: str
    lyricist_gender: str
    helper_name: str
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
    for sid, scene in SCENES.items():
        for mid, mishap in MISHAPS.items():
            if not calm_or_stun(scene, mishap):
                continue
            for fid, fix in FIXES.items():
                if fix.sense >= SENSE_MIN:
                    combos.append((sid, mid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: a lyric-ist, a stun, and a steady rhyme.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--lyricist-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--lyricist-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError("That fix is too weak for this rhyming story.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.mishap is None or c[1] == args.mishap)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, mishap, fix = rng.choice(sorted(combos))
    lg = args.lyricist_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    ln = args.lyricist_name or rng.choice(NAMES)
    hn = args.helper_name or rng.choice([n for n in NAMES if n != ln])
    return StoryParams(scene, mishap, fix, ln, lg, hn, hg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child where {f["lyricist"].id} is a lyric-ist and something goes wrong enough to stun the room.',
        f"Tell a gentle rhyme story where {f['lyricist'].id} uses an inner monologue to stay brave, then {f['helper'].id} helps restore the beat.",
        f'Write a small stage story that includes the words "lyric-ist" and "stun", then ends with a clear rhyming finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lyricist: Entity = f["lyricist"]
    helper: Entity = f["helper"]
    scene: Scene = f["scene"]
    fix: Fix = f["fix"]
    qas = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {lyricist.id}, a lyric-ist, and {helper.id}, who stays close to help. The little stage moment belongs to them both."
        ),
        QAItem(
            question="What does the lyricist think about before performing?",
            answer=f"{lyricist.id} thinks about keeping the beat and finding a kind rhyme. Inside {lyricist.pronoun('possessive')} head, {lyricist.pronoun()} wants the song to stay brave and clear."
        ),
    ]
    if f["fixed"]:
        qas.append(
            QAItem(
                question=f"How did {helper.id} fix the stunned moment?",
                answer=f"{helper.id} {fix.action}, and that helped the rhyme come back on track. The room softened, so {lyricist.id} could finish the song with a calm voice."
            )
        )
        qas.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with a bright performance and smiling listeners. {scene.ending_glow.capitalize()} stayed in the room after the last rhyme."
            )
        )
    return qas


WORLD_KNOWLEDGE = {
    "rhyme": [QAItem(
        question="What is a rhyme?",
        answer="A rhyme is when words sound alike at the end, like light and night. Rhymes help songs and poems feel musical."
    )],
    "inner_monologue": [QAItem(
        question="What is an inner monologue?",
        answer="An inner monologue is the quiet voice a character thinks in their own head. It can show fear, hope, or a plan before the character speaks out loud."
    )],
    "stage": [QAItem(
        question="What is a stage?",
        answer="A stage is a raised place where someone performs for other people. It helps everyone see the singer or speaker."
    )],
    "stun": [QAItem(
        question="What does it mean to be stunned?",
        answer="To be stunned means to be surprised so hard that you pause for a moment. It can happen when something sudden makes you stop and stare."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE[k][0] for k in ["rhyme", "inner_monologue", "stage", "stun"]]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("open_mic", "dropped_card", "count_in", "Mara", "girl", "Noah", "boy"),
    StoryParams("school_show", "broken_rhythm", "hum_tune", "Pia", "girl", "Ezra", "boy"),
    StoryParams("story_corner", "mic_feedback", "simple_line", "Owen", "boy", "Ivy", "girl"),
]


def explain_rejection(scene: Scene, mishap: Mishap) -> str:
    return f"(No story: {mishap.trigger.replace('_', ' ')} does not fit this scene cleanly enough to build a steady rhyme.)"


def outcome_of(params: StoryParams) -> str:
    return "fixed" if FIXES[params.fix].power >= 2 else "stalled"


ASP_RULES = r"""
valid(S, M, F) :- scene(S), mishap(M), fix(F), can_stun(S, M), sensible(F).
outcome(fixed) :- chosen_fix(F), power(F, P), P >= 2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for m in MISHAPS:
        lines.append(asp.fact("mishap", m))
        lines.append(asp.fact("can_stun", m, "yes"))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sensible", fid))
        lines.append(asp.fact("power", fid, f.power))
        lines.append(asp.fact("sense", fid, f.sense))
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
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-test generation works.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], MISHAPS[params.mishap], FIXES[params.fix],
                 params.lyricist_name, params.lyricist_gender,
                 params.helper_name, params.helper_gender)
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
        print(asp_valid_combos())
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
