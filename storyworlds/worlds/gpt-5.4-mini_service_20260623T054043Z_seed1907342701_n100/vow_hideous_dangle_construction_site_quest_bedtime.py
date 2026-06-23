#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/vow_hideous_dangle_construction_site_quest_bedtime.py
===============================================================================================================================

A standalone story world for a bedtime-style quest at a construction site.

The seed suggests three required words -- vow, hideous, dangle -- plus a quest
frame in a construction site, told in a gentle bedtime-story tone. This world
models a small crew of children and a caretaker, a risky dangling path, a hidden
quest item, a frightful sight, and a vow to keep the site safe before sleep.

The simulation keeps the prose state-driven:
- physical meters track dust, wobble, hush, and repair work
- emotional memes track fear, courage, wonder, and relief
- a forward causal rule turns a loose dangling object into a blocked path
- the story turns when the caretaker predicts the risk and the child vows to
  help, then the quest ends with the hidden item recovered and the site calmed

The generated stories are intentionally small and child-facing, with concrete
images and a clear ending.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    tone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    hidden_in: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DangleThing:
    id: str
    label: str
    phrase: str
    zone: str
    loosens: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "site"
    quest: str = "lantern"
    dangle: str = "hook"
    fix: str = "rope"
    child_name: str = "Mina"
    child_gender: str = "girl"
    caretaker_gender: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_block_path(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    dang = world.get("dangle")
    if child.meters["fear"] < THRESHOLD or dang.meters["wobble"] < THRESHOLD:
        return out
    sig = ("blocked",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("path").meters["blocked"] += 1
    world.get("path").meters["dust"] += 1
    child.memes["unease"] += 1
    out.append("__blocked__")
    return out


CAUSAL_RULES = [Rule("block_path", _r_block_path)]


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


def quest_at_risk(setting: Setting, quest: QuestItem, dangle: DangleThing) -> bool:
    return quest.hidden_in == dangle.zone


def select_fix(dangle: DangleThing, quest: QuestItem) -> Optional[Fix]:
    for fx in FIXES.values():
        if dangle.loosens in fx.effect and quest.hidden_in in fx.effect:
            return fx
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s_id, setting in SETTINGS.items():
        for q_id, q in QUESTS.items():
            for d_id, d in DANGLES.items():
                if quest_at_risk(setting, q, d) and select_fix(d, q):
                    combos.append((s_id, q_id, d_id))
    return combos


def predict_block(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["fear"] += 1
    sim.get("dangle").meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "blocked": sim.get("path").meters["blocked"] >= THRESHOLD,
        "dust": sim.get("path").meters["dust"],
    }


def tell(setting: Setting, quest: QuestItem, dangle: DangleThing, fix: Fix,
         child_name: str, child_gender: str, caretaker_gender: str,
         trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender,
                             label=child_name, role="seeker",
                             attrs={"trait": trait}))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=caretaker_gender,
                                 label={"mother": "mom", "father": "dad"}.get(caretaker_gender, "grown-up"),
                                 role="caretaker"))
    path = world.add(Entity(id="path", type="path", label="the path"))
    qent = world.add(Entity(id="quest", type="quest", label=quest.label,
                            attrs={"item": quest.id}))
    dent = world.add(Entity(id="dangle", type="thing", label=dangle.label))
    world.add(Entity(id="fix", type="tool", label=fix.label))

    world.facts.update(
        child=child, caretaker=caretaker, quest=quest, dangle=dangle, fix=fix, setting=setting
    )

    child.memes["wonder"] += 1
    child.memes["desire"] += 1
    caretaker.memes["watchful"] += 1
    path.meters["dust"] += 1
    dent.meters["wobble"] = 0.0
    dent.meters["hanging"] = 1.0

    world.say(
        f"At {setting.place}, {child.label} and {child.pronoun('possessive')} "
        f"{caretaker.label_word} worked by the soft evening light. {setting.tone}"
    )
    world.say(
        f"{child.label} was on a little quest for {quest.phrase}, because "
        f"{quest.reveals}."
    )

    world.para()
    world.say(
        f"Then {child.label} saw {dangle.phrase}, and it looked {setting.tone} in a "
        f"small, hideous way. It seemed ready to dangle over {dangle.zone}."
    )
    pred = predict_block(world)
    world.facts["predicted_blocked"] = pred["blocked"]

    world.say(
        f'"That could make the way messy," said {caretaker.label}. '
        f'{"If it slips, it will block the path," if pred["blocked"] else "It still looks unsafe."}'
    )
    child.memes["fear"] += 1
    world.say(
        f"{child.label} swallowed hard, then made a tiny vow to stay close and help."
    )
    child.memes["vow"] += 1
    if pred["blocked"]:
        world.say(
            f'"I vow to hold the light and keep the path clear," {child.label} said.'
        )
    else:
        world.say(f'"I vow not to touch it," {child.label} whispered.')

    world.para()
    fx = fix
    child.memes["courage"] += 1
    caretaker.memes["relief"] += 1
    world.say(
        f"{caretaker.label_word.capitalize()} used {fx.phrase}, and the loose piece settled down."
    )
    child.meters["help"] += 1
    world.get("dangle").meters["wobble"] = 0.0
    world.get("path").meters["blocked"] = 0.0
    world.get("path").meters["dust"] = 0.0
    world.say(
        f"Together they found {quest.phrase} tucked where the shadows had hidden it."
    )
    world.say(
        f"By the end, the site was quiet again: {dangle.label} no longer swung, "
        f"{quest.label} was safe in {child.label}'s hands, and the dust was still."
    )

    world.facts["resolved"] = True
    world.facts["path_clear"] = True
    return world


SETTINGS = {
    "site": Setting(id="site", place="the construction site", tone="The cranes were sleepy against the dark sky.", tags={"construction", "bedtime"}),
    "after_hours": Setting(id="after_hours", place="the half-built building", tone="The tool carts stood still like toy trains at rest.", tags={"construction", "bedtime"}),
    "lot": Setting(id="lot", place="the quiet lot behind the fence", tone="The fence made a gentle line around the moonlit dirt.", tags={"construction", "bedtime"}),
    "foundation": Setting(id="foundation", place="the foundation pit", tone="The open pit looked deep, but the lights made it feel gentle.", tags={"construction", "bedtime"}),
}

QUESTS = {
    "lantern": QuestItem(id="lantern", label="lantern", phrase="a small lantern for the watch shelf", hidden_in="hook", reveals="the lantern was tucked where the wall hooks waited", tags={"quest"}),
    "blueprint": QuestItem(id="blueprint", label="blueprint", phrase="the rolled-up blueprint", hidden_in="beam", reveals="the blueprint had slipped behind a beam", tags={"quest"}),
    "key": QuestItem(id="key", label="key", phrase="the little brass key", hidden_in="bucket", reveals="the key had fallen into a bucket", tags={"quest"}),
    "toy": QuestItem(id="toy truck", label="toy truck", phrase="the tiny toy truck", hidden_in="crate", reveals="the toy truck rested inside a crate", tags={"quest"}),
}

DANGLES = {
    "hook": DangleThing(id="hook", label="a loose hook", phrase="a loose hook", zone="hook", loosens="hook", tags={"dangle"}),
    "beam": DangleThing(id="beam", label="a dangling beam strap", phrase="a dangling beam strap", zone="beam", loosens="beam", tags={"dangle"}),
    "bucket": DangleThing(id="bucket", label="a swinging bucket rope", phrase="a swinging bucket rope", zone="bucket", loosens="bucket", tags={"dangle"}),
    "crate": DangleThing(id="crate", label="a dangling crate latch", phrase="a dangling crate latch", zone="crate", loosens="crate", tags={"dangle"}),
}

FIXES = {
    "clip": Fix(id="clip", label="a bright metal clip", phrase="a bright metal clip", effect="hook", tags={"fix"}),
    "strap": Fix(id="strap", label="a steadying strap", phrase="a steadying strap", effect="beam", tags={"fix"}),
    "knot": Fix(id="knot", label="a careful knot", phrase="a careful knot", effect="bucket", tags={"fix"}),
    "latch": Fix(id="latch", label="a safe latch", phrase="a safe latch", effect="crate", tags={"fix"}),
}

NAMES = ["Mina", "Leo", "Nia", "Owen", "Iris", "Theo", "Luna", "Milo"]
TRAITS = ["curious", "gentle", "brave", "sleepy", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, q, d, s = f["child"], f["quest"], f["dangle"], f["setting"]
    return [
        f'Write a bedtime story about a child at {s.place} who goes on a quest for {q.label} and sees {d.label}. Include the words "vow", "hideous", and "dangle".',
        f"Tell a gentle construction-site quest story where {c.label} makes a vow, notices something hideous, and helps keep the way safe.",
        f"Write a short bedtime adventure with {q.label}, {d.label}, and a child who promises to help before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, caretaker, q, d = f["child"], f["caretaker"], f["quest"], f["dangle"]
    return [
        QAItem(
            f"Who went on the quest at {f['setting'].place}?",
            f"{c.label} went on the quest with {caretaker.label_word}. They were looking for {q.phrase} in the quiet construction site.",
        ),
        QAItem(
            f"Why did {c.label} think {d.label} was hideous?",
            f"It looked lopsided and strange in the dark, so it seemed hideous to {c.label}. It also looked like it might dangle over the path and make the way unsafe.",
        ),
        QAItem(
            f"What did {c.label} vow to do?",
            f"{c.label} vowed to stay close and help keep the path clear. That promise helped turn a scary moment into calm teamwork.",
        ),
        QAItem(
            f"What changed after {f['fix'].label} was used?",
            f"The loose piece settled down, the path stopped being blocked, and {q.label} was found safely. By the end, the dust was still and everything felt ready for bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a vow?",
            "A vow is a very serious promise. People make a vow when they want to show they will do something and keep their word.",
        ),
        QAItem(
            "What does dangle mean?",
            "To dangle means to hang down and sway. A thing that dangles can move loosely in the air.",
        ),
        QAItem(
            "What does hideous mean?",
            "Hideous means very ugly or unpleasant to look at. It is a strong word for something that seems scary or strange.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a search for something important. In stories, a quest is often a small adventure with a goal.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="site", quest="lantern", dangle="hook", fix="clip", child_name="Mina", child_gender="girl", caretaker_gender="mother", trait="curious"),
    StoryParams(setting="after_hours", quest="blueprint", dangle="beam", fix="strap", child_name="Leo", child_gender="boy", caretaker_gender="father", trait="gentle"),
    StoryParams(setting="lot", quest="key", dangle="bucket", fix="knot", child_name="Nia", child_gender="girl", caretaker_gender="mother", trait="brave"),
    StoryParams(setting="foundation", quest="toy", dangle="crate", fix="latch", child_name="Owen", child_gender="boy", caretaker_gender="father", trait="careful"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not form a safe quest at the construction site.)"


ASP_RULES = r"""
quest_at_risk(S,Q,D) :- setting(S), quest(Q), dangle(D), hidden_in(Q, Z), zone(D, Z).
has_fix(Q,D,F) :- quest_at_risk(S,Q,D), fix(F), effect(F, Z), hidden_in(Q, Z), loosens(D, Z).
valid(S,Q,D) :- quest_at_risk(S,Q,D), has_fix(Q,D,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", s_id, t))
    for q_id, q in QUESTS.items():
        lines.append(asp.fact("quest", q_id))
        lines.append(asp.fact("hidden_in", q_id, q.hidden_in))
    for d_id, d in DANGLES.items():
        lines.append(asp.fact("dangle", d_id))
        lines.append(asp.fact("zone", d_id, d.zone))
        lines.append(asp.fact("loosens", d_id, d.loosens))
    for f_id, f in FIXES.items():
        lines.append(asp.fact("fix", f_id))
        lines.append(asp.fact("effect", f_id, f.effect))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH between ASP and Python valid_combos().")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        ok = 1
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-style construction-site quest story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--dangle", choices=DANGLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.quest is None or c[1] == args.quest)
              and (args.dangle is None or c[2] == args.dangle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, dangle = rng.choice(sorted(combos))
    fix = args.fix or next(f.id for f in FIXES.values() if FIXES[f.id].effect == DANGLES[dangle].loosens)
    if fix not in FIXES:
        raise StoryError("Invalid fix selection.")
    gender = args.gender or rng.choice(["girl", "boy"])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, dangle=dangle, fix=fix, child_name=name, child_gender=gender, caretaker_gender=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.dangle not in DANGLES or params.fix not in FIXES:
        raise StoryError("Unknown parameter value.")
    if not quest_at_risk(SETTINGS[params.setting], QUESTS[params.quest], DANGLES[params.dangle]):
        raise StoryError(explain_rejection())
    if FIXES[params.fix].effect != DANGLES[params.dangle].loosens:
        raise StoryError(explain_rejection())
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], DANGLES[params.dangle], FIXES[params.fix], params.child_name, params.child_gender, params.caretaker_gender, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
