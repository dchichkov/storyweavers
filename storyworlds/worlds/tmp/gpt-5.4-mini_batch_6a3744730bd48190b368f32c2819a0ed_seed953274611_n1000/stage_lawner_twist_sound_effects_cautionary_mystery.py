#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stage_lawner_twist_sound_effects_cautionary_mystery.py
======================================================================================

A small standalone storyworld built from the seed words *stage* and *lawner*,
with a mystery tone, a twist, sound effects, and a cautionary ending.

Premise
-------
A child hears odd sounds near a stage and a lawn mower shed, follows clues,
learns that appearances can be misleading, and ends safely with a new rule:
when something feels strange, call a grown-up instead of solving it alone.

This file follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- a state-driven simulation
- prompt, grounded QA, and world-knowledge QA
- Python reasonableness gate plus inline ASP twin
- CLI flags: -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    clues: list[str] = field(default_factory=list)
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
    label: str
    places: list[str]
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CharacterCfg:
    id: str
    type: str
    role: str
    curious: bool = True
    caution: int = 5


@dataclass
class ClueCfg:
    id: str
    sound: str
    source: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistCfg:
    id: str
    reveal: str
    sound: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    clue: str
    twist: str
    seed: Optional[int] = None
    name: str = ""


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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    stage = world.get("stage")
    if stage.meters["strange"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out = []
    if world.get("child").meters["noticed"] >= THRESHOLD and ("clue",) not in world.fired:
        world.fired.add(("clue",))
        world.get("child").meters["clues"] += 1
        out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("clue", _r_clue)]


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


SETTINGS = {
    "school_stage": Setting(
        id="school_stage",
        label="the school stage",
        places=["back curtain", "music box", "props shelf"],
        mood="quiet and echoing",
        tags={"stage", "mystery"},
    ),
    "town_stage": Setting(
        id="town_stage",
        label="the town stage",
        places=["spotlight rope", "trapdoor", "old drum"],
        mood="bright but a little spooky",
        tags={"stage", "mystery"},
    ),
    "yard_shed": Setting(
        id="yard_shed",
        label="the yard by the shed",
        places=["shed door", "grass path", "tool bench"],
        mood="still and creaky",
        tags={"lawner", "mystery"},
    ),
}

CHILDREN = {
    "girl": ["Mina", "Lia", "Tess", "Nora"],
    "boy": ["Eli", "Ben", "Noah", "Owen"],
}

ADULTS = {
    "mother": "Mom",
    "father": "Dad",
}

CLUES = {
    "scratch": ClueCfg(
        id="scratch", sound="scritch-scratch", source="the curtain cord",
        reveal="a bent metal hook was rubbing the curtain cord",
        tags={"sound", "mystery"},
    ),
    "thump": ClueCfg(
        id="thump", sound="thump-thump", source="the stage floor",
        reveal="a loose prop kept tapping under the stage board",
        tags={"sound", "mystery"},
    ),
    "rattle": ClueCfg(
        id="rattle", sound="rattle-click", source="the shed latch",
        reveal="the shed latch was loose and knocking in the wind",
        tags={"sound", "mystery"},
    ),
}

TWISTS = {
    "cat": TwistCfg(
        id="cat",
        reveal="a tiny cat had been hiding in the wings, chasing the blinking light",
        sound="mew-mew",
        lesson="small mysteries can have simple, safe answers",
        tags={"twist", "cautionary"},
    ),
    "robot": TwistCfg(
        id="robot",
        reveal="the spooky noise came from a toy robot that had turned itself on",
        sound="beep-beep",
        lesson="it is wise to check before jumping to scary ideas",
        tags={"twist", "cautionary"},
    ),
    "wind": TwistCfg(
        id="wind",
        reveal="the sound came from the wind nudging loose stage parts and the shed door",
        sound="whoooosh",
        lesson="the world can make odd noises without any danger at all",
        tags={"twist", "cautionary"},
    ),
}

STAGE_WORDS = {"stage", "mystery", "sound", "cautionary", "twist", "lawner"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid in CLUES:
            if sid == "yard_shed" and cid == "scratch":
                continue
            for tid in TWISTS:
                combos.append((sid, cid, tid))
    return combos


def reason_gate(setting: Setting, clue: ClueCfg, twist: TwistCfg) -> bool:
    return True


def explain_rejection(setting: Setting, clue: ClueCfg, twist: TwistCfg) -> str:
    return "(No story: this combination does not build a clear mystery beat.)"


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["noticed"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("child").memes["worry"],
        "clues": sim.get("child").meters["clues"],
    }


def introduce(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} stepped onto {setting.label}, where everything felt {setting.mood}."
    )
    world.say(
        f"The place had a few odd corners: {', '.join(setting.places)}."
    )


def sound_hint(world: World, clue: ClueCfg) -> None:
    world.get("child").meters["noticed"] += 1
    world.say(
        f"Then there came a strange sound: {clue.sound}. It seemed to come from {clue.source}."
    )
    world.say(
        f"{world.get('child').id} froze and listened again."
    )


def caution(world: World, child: Entity, adult: Entity, clue: ClueCfg) -> None:
    pred = predict(world)
    world.facts["predicted"] = pred
    child.memes["fear"] += 1
    world.say(
        f'"Let\'s not rush," {adult.label_word} said. "Odd sounds can have simple causes, and we should stay calm."'
    )
    if pred["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} remembered that if a place feels strange, it is smarter to call a grown-up than to poke around."
        )


def investigate(world: World, child: Entity, clue: ClueCfg) -> None:
    child.meters["noticed"] += 1
    world.say(
        f"{child.id} followed the sound one careful step at a time: {clue.sound}."
    )
    propagate(world, narrate=False)
    world.say(
        f"Near the source, {child.id} found {clue.reveal}."
    )


def twist_reveal(world: World, twist: TwistCfg) -> None:
    world.say(
        f"Twist! {twist.sound} -- and the scary guess was wrong."
    )
    world.say(twist.reveal.capitalize() + ".")
    world.say(f"So the mystery was solved without any danger.")


def ending(world: World, child: Entity, adult: Entity, twist: TwistCfg) -> None:
    child.memes["relief"] += 2
    world.say(
        f"{adult.label_word} smiled and nodded. " +
        f'"{twist.lesson.capitalize()}," {adult.label_word} said.'
    )
    world.say(
        f"{child.id} went home quieter than before, but braver too, and the night sounded ordinary again."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    twist = TWISTS[params.twist]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender, role="adult"))
    stage = world.add(Entity(id="stage", label=setting.label, type="place", tags=setting.tags))
    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["twist"] = twist
    world.facts["adult"] = adult
    world.facts["child"] = child
    world.facts["stage"] = stage

    introduce(world, child, setting)
    world.para()
    sound_hint(world, clue)
    caution(world, child, adult, clue)
    world.para()
    investigate(world, child, clue)
    twist_reveal(world, twist)
    ending(world, child, adult, twist)

    world.facts["outcome"] = "solved"
    return world


PROMPT_TEMPLATES = [
    "Write a child-friendly mystery story that includes the words 'stage' and 'lawner'.",
    "Tell a cautionary mystery with a twist and sound effects, where a child hears an odd noise and learns a safe lesson.",
    "Write a short story about a strange sound near a stage or a lawner, ending with a surprising but harmless reveal.",
]

WORLD_QA = [
    ("What is a stage?",
     "A stage is a raised place where people act, sing, or perform for others to watch."),
    ("What is a lawn mower shed?",
     "A lawn mower shed is a small building that stores garden tools, including a mower."),
    ("Why should a child be cautious about strange sounds?",
     "Strange sounds can come from simple things, but it is safer to stop and call a grown-up than to rush in alone."),
]


def generation_prompts(world: World) -> list[str]:
    return PROMPT_TEMPLATES


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    clue: ClueCfg = f["clue"]
    twist: TwistCfg = f["twist"]
    return [
        (
            f"What did {child.id} hear?",
            f"{child.id} heard {clue.sound} near {clue.source}, which made the place feel mysterious."
        ),
        (
            f"How did {adult.label_word} help?",
            f"{adult.label_word} told {child.id} to stay calm and think carefully. That kept the story safe and helped the mystery feel less scary."
        ),
        (
            "What was the twist?",
            f"The twist was that {twist.reveal}. That changed the scary guess into a simple explanation."
        ),
        (
            "How did the story end?",
            f"It ended with {child.id} learning to be cautious and to ask for help when something sounds strange. The mystery was solved without anyone getting hurt."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return WORLD_QA


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="school_stage", child="Mina", child_gender="girl", adult="Mom", adult_gender="mother", clue="scratch", twist="cat"),
    StoryParams(setting="town_stage", child="Eli", child_gender="boy", adult="Dad", adult_gender="father", clue="thump", twist="robot"),
    StoryParams(setting="yard_shed", child="Tess", child_gender="girl", adult="Dad", adult_gender="father", clue="rattle", twist="wind"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.clue is None or c[1] == args.clue)
        and (args.twist is None or c[2] == args.twist)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, twist = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child = args.name or rng.choice(CHILDREN[child_gender])
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult = ADULTS[adult_gender]
    return StoryParams(
        setting=setting,
        child=child,
        child_gender=child_gender,
        adult=adult,
        adult_gender=adult_gender,
        clue=clue,
        twist=twist,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")
    world = tell(params)
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


ASP_RULES = r"""
setting(school_stage). setting(town_stage). setting(yard_shed).
clue(scratch). clue(thump). clue(rattle).
twist(cat). twist(robot). twist(wind).

valid(S, C, T) :- setting(S), clue(C), twist(T), not bad(S, C, T).

% The yard shed does not pair with the scratch clue in this world: too little
% stage-feel for the mystery tone requested by the seed.
bad(yard_shed, scratch, _).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test generate() produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a stage, a lawner, a twist, and caution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, clue, twist) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child} at {p.setting} ({p.clue}, {p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
