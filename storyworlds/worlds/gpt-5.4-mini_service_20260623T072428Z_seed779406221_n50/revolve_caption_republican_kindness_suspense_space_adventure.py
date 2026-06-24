#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/revolve_caption_republican_kindness_suspense_space_adventure.py
==============================================================================================================

A standalone story world for a small Space-Adventure-style domain built from
the seed words revolve, caption, and republican, with Kindness and Suspense
driving the turn.

Premise:
- A small orbiting habitat revolves around a blue planet.
- A child wants to add a caption to a mission photo.
- A tense moment arises when a shiny signal panel goes dark and the child
  thinks the wrong caption will make a friend feel small.
- A kinder caption, plus a careful repair, resolves both the social and
  practical problem.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- forward-chained causal rules
- a Python reasonableness gate and an inline ASP twin
- --verify to compare Python/ASP parity and exercise generated stories
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
SUSPENSE_MIN = 1.0
KINDNESS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    target: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    revolves: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    action: str
    gerund: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CaptionPlan:
    id: str
    phrase: str
    kinder_phrase: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    protects: set[str]
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_reveal(world: World) -> list[str]:
    out = []
    panel = world.entities.get("panel")
    if panel and panel.meters["dark"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.characters():
                kid.memes["suspense"] += 1
            out.append("__reveal__")
    return out


def _r_kind(world: World) -> list[str]:
    out = []
    speaker = world.entities.get("child")
    friend = world.entities.get("friend")
    if speaker and friend and speaker.memes["kindness"] >= KINDNESS_MIN:
        sig = ("kind",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["relief"] += 1
            out.append("__kind__")
    return out


CAUSAL_RULES = [
    Rule("reveal", "social", _r_reveal),
    Rule("kind", "social", _r_kind),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonableness_ok(setting: Setting, task: Task, caption: CaptionPlan, fix: Fix) -> bool:
    return setting.revolves and task.id in setting.affords and caption.keyword in task.tags and fix.id in FIXES


def should_risk(task: Task) -> bool:
    return bool(task.zone)


def select_fix(task: Task) -> Optional[Fix]:
    for fix in FIXES.values():
        if task.keyword in fix.tags and task.zone.issubset(fix.protects):
            return fix
    return None


def predict(world: World, task: Task) -> dict:
    sim = world.copy()
    child = sim.get("child")
    task_apply(sim, child, task, narrate=False)
    return {
        "suspense": sim.get("friend").memes["suspense"],
        "kindness": sim.get("child").memes["kindness"],
    }


def task_apply(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    world.zone = set(task.zone)
    actor.meters["move"] += 1
    actor.memes["suspense"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"The station {('revolved' if setting.revolves else 'floated')} above the planet like a silver wheel, and {child.id} and {friend.id} watched the blue glow slide past the window."
    )


def setup_photo(world: World, child: Entity, caption: CaptionPlan) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} wanted to write a caption for the mission photo. {child.pronoun().capitalize()} liked the funny one: \"{caption.phrase}\"."
    )


def tension(world: World, child: Entity, friend: Entity, task: Task, caption: CaptionPlan) -> None:
    friend.memes["suspense"] += 1
    world.say(
        f"Then the little signal panel near the photo board went dim, and the room felt suddenly quiet. {child.id} knew the quick joke would make {friend.id} look small."
    )
    world.say(
        f"{friend.id} stared at the dark panel while the station kept on revolving, slow and steady, around the planet."
    )


def warn(world: World, friend: Entity, child: Entity, task: Task) -> None:
    world.say(
        f'"{child.id}, wait," {friend.id} said. "If you rush that caption, you may forget the kinder words."'
    )
    friend.memes["caution"] += 1


def choose_kindness(world: World, child: Entity, friend: Entity, caption: CaptionPlan) -> None:
    child.memes["kindness"] += 1
    child.memes["suspense"] += 1
    world.say(
        f"{child.id} looked at the smiling faces in the picture, then at {friend.id}. {child.pronoun().capitalize()} crossed out the joke and wrote a kinder caption instead."
    )


def fix_panel(world: World, child: Entity, fix: Fix) -> None:
    panel = world.get("panel")
    panel.meters["dark"] = 0.0
    panel.meters["working"] = 1.0
    world.say(
        f"{child.id} used {fix.label} to steady the panel. Soon the light came back in a tiny clean square."
    )


def ending(world: World, child: Entity, friend: Entity, caption: CaptionPlan, fix: Fix) -> None:
    world.say(
        f"The new caption shone under the picture, and it read, \"{caption.kinder_phrase}\"."
    )
    world.say(
        f"{friend.id} smiled so hard that even the revolving station seemed to sparkle. {child.id} felt brave, kind, and proud."
    )


SETTINGS = {
    "orbital-ring": Setting(place="the orbital ring", revolves=True, affords={"caption", "signal"}),
    "moon-hub": Setting(place="the moon hub", revolves=True, affords={"caption", "signal"}),
}

TASKS = {
    "caption": Task(
        id="caption",
        action="write a caption",
        gerund="writing a caption",
        risk="a teasing caption",
        zone={"screen"},
        keyword="caption",
        tags={"caption"},
    ),
    "signal": Task(
        id="signal",
        action="fix the signal panel",
        gerund="fixing the signal panel",
        risk="a dark panel",
        zone={"panel"},
        keyword="signal",
        tags={"signal", "suspense"},
    ),
}

CAPTIONS = {
    "funny": CaptionPlan(
        id="funny",
        phrase="Look who tripped on zero-g!",
        kinder_phrase="We had an amazing zero-g day together.",
        keyword="caption",
        tags={"caption", "kindness"},
    ),
    "team": CaptionPlan(
        id="team",
        phrase="Best crew, best ship, best everything.",
        kinder_phrase="Best crew, best ship, best kindness.",
        keyword="caption",
        tags={"caption", "kindness"},
    ),
}

FIXES = {
    "glowtab": Fix(
        id="glowtab",
        label="the glow tab",
        protects={"panel"},
        method="steady the panel",
        tags={"signal"},
    ),
    "sparecell": Fix(
        id="sparecell",
        label="the spare cell",
        protects={"panel"},
        method="power the panel again",
        tags={"signal"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Luna", "Rae", "Ivy", "Nia"]
BOY_NAMES = ["Owen", "Kai", "Jace", "Noah", "Ezra", "Levi"]


@dataclass
class StoryParams:
    setting: str
    task: str
    caption: str
    fix: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for c in CAPTIONS:
                if reasonableness_ok(SETTINGS[s], TASKS[t], CAPTIONS[c], FIXES["glowtab"]):
                    combos.append((s, t, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with revolve, caption, republican, kindness, and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--caption", choices=CAPTIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--friend")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              and (args.task is None or c[1] == args.task)
              and (args.caption is None or c[2] == args.caption)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, caption = rng.choice(sorted(combos))
    fix = args.fix or "glowtab"
    cg = args.child_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if cg == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if cg == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    return StoryParams(setting=setting, task=task, caption=caption, fix=fix, child=child, child_gender=cg, friend=friend, friend_gender=fg)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender))
    panel = world.add(Entity(id="panel", type="thing", label="signal panel"))
    world.add(Entity(id="republican", type="thing", label="the Republican shuttle"))
    task = TASKS[params.task]
    cap = CAPTIONS[params.caption]
    fix = FIXES[params.fix]

    intro(world, child, friend, world.setting)
    setup_photo(world, child, cap)
    world.para()
    tension(world, child, friend, task, cap)
    warn(world, friend, child, task)
    choose_kindness(world, child, friend, cap)
    fix_panel(world, child, fix)
    world.para()
    ending(world, child, friend, cap, fix)

    world.facts.update(child=child, friend=friend, task=task, caption=cap, fix=fix, panel=panel, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Space Adventure story for a child where a station revolves above a planet and a caption turns from teasing to kind.',
        f"Tell a gentle suspense story where {f['child'].id} writes a caption, hears {f['friend'].id}'s warning, and chooses kindness instead.",
        'Write a small story that includes the words revolve, caption, and republican, and ends with a kinder message under the picture.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, cap = f["child"], f["friend"], f["caption"]
    return [
        QAItem(
            question=f"What did {child.id} want to write for the mission photo?",
            answer=f"{child.id} wanted to write a caption, first a funny one, and then a kinder one after thinking about {friend.id}.",
        ),
        QAItem(
            question=f"Why did the room feel tense when the signal panel went dim?",
            answer=f"The room felt tense because the panel went dark while {child.id} was thinking about a caption, and nobody wanted to hurt {friend.id}'s feelings.",
        ),
        QAItem(
            question=f"How did {child.id} show kindness at the end?",
            answer=f"{child.id} crossed out the teasing caption and wrote a kinder caption instead, so {friend.id} could smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for a station to revolve?",
            answer="If a station revolves, it turns around in a circle. Space stations can revolve slowly while they travel around a planet.",
        ),
        QAItem(
            question="What is a caption?",
            answer="A caption is a short line of words that goes with a picture and helps explain it or make it fun.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about other people's feelings.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the nervous, waiting feeling you get when you do not yet know what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
revolve_setting(s) :- setting(s), revolves(s).
task_ok(t) :- task(t), risk_zone(t, z), z != "".
kind_caption(c) :- caption(c), kinder(c).
valid(s,t,c) :- revolve_setting(s), task_ok(t), kind_caption(c).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.revolves:
            lines.append(asp.fact("revolves", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risk_zone", tid, "x"))
    for cid, c in CAPTIONS.items():
        lines.append(asp.fact("caption", cid))
        lines.append(asp.fact("kinder", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python combos.")
        return 1
    print("OK: ASP and Python combos match.")
    for seed in range(10):
        p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        _ = tell(p).render()
    print("OK: generated stories exercised.")
    return 0


CURATED = [
    StoryParams(setting="orbital-ring", task="caption", caption="funny", fix="glowtab", child="Mina", child_gender="girl", friend="Owen", friend_gender="boy"),
    StoryParams(setting="moon-hub", task="signal", caption="team", fix="sparecell", child="Kai", child_gender="boy", friend="Rae", friend_gender="girl"),
]


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
