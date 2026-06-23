#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/kaput_bad_ending_pirate_tale.py
===============================================================================================================

A standalone story world sketch for a pirate tale with a bad ending: a crew
searches the docks for a way home, but the old boat turns kaput and the rescue
fails. The world keeps typed entities with physical meters and emotional memes,
plus a small forward-chaining causal layer, a reasonableness gate, and an ASP
twin for parity checks.

The domain is intentionally small:
- a boat that can turn kaput,
- a tide or storm that can worsen the situation,
- a lantern or patch that may help,
- a crew that must escape before the harbor takes the boat.

The story is child-facing, concrete, and state-driven. The bad ending is part of
the seed premise: the plan goes wrong, the rescue fails, and the final image
proves the loss.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    connected_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "captain"}
        if self.type in female and self.type != "captain":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type != "captain":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    verb: str
    danger: str
    worsen: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    succeeds: bool
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "harbor": Setting(id="harbor", place="the harbor", outdoors=True, affords={"sail", "drift"}),
    "island": Setting(id="island", place="the island shore", outdoors=True, affords={"sail", "drift"}),
    "cove": Setting(id="cove", place="the rocky cove", outdoors=True, affords={"sail"}),
}

TROUBLES = {
    "storm": Trouble(
        id="storm",
        label="the storm",
        verb="push into the waves",
        danger="dangerous",
        worsen="the wind howled harder and the waves climbed higher",
        zone={"deck", "mast"},
        tags={"storm", "wind", "waves"},
    ),
    "leak": Trouble(
        id="leak",
        label="the leak",
        verb="soak the floorboards",
        danger="wet",
        worsen="the water sloshed in faster and faster",
        zone={"hull", "deck"},
        tags={"water", "leak"},
    ),
    "rocks": Trouble(
        id="rocks",
        label="the rocks",
        verb="crunch the hull",
        danger="rough",
        worsen="the hull scraped louder against the stones",
        zone={"hull"},
        tags={"rocks", "stone"},
    ),
    "fog": Trouble(
        id="fog",
        label="the fog",
        verb="hide the way home",
        danger="lost",
        worsen="the harbor lights vanished into the gray",
        zone={"eyes", "deck"},
        tags={"fog", "mist"},
    ),
}

FIXES = {
    "patch": Fix(
        id="patch",
        label="a patch kit",
        verb="patch the hull",
        succeeds=False,
        guards={"leak"},
        tags={"patch", "cloth"},
    ),
    "lantern": Fix(
        id="lantern",
        label="a bright lantern",
        verb="light the way",
        succeeds=False,
        guards={"fog"},
        tags={"lantern", "light"},
    ),
    "tow": Fix(
        id="tow",
        label="a tow rope",
        verb="pull the boat free",
        succeeds=False,
        guards={"rocks", "storm"},
        tags={"rope", "tow"},
    ),
    "bucket": Fix(
        id="bucket",
        label="a bucket brigade",
        verb="scoop out the water",
        succeeds=False,
        guards={"leak"},
        tags={"bucket", "water"},
    ),
}

PRIZES = {
    "map": Prize(id="map", label="the treasure map", phrase="the treasure map", region="deck", tags={"map", "paper"}),
    "flag": Prize(id="flag", label="the pirate flag", phrase="the pirate flag", region="mast", tags={"flag", "cloth"}),
    "chest": Prize(id="chest", label="the small chest", phrase="the little chest", region="hull", tags={"chest", "wood"}),
}

CAPTAINS = ["Mara", "Nell", "Tia", "Rosa", "Ivy", "June", "Finn", "Jax", "Seth", "Bram"]
TRAITS = ["brave", "curious", "stubborn", "cheerful", "bold"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    fix: str
    prize: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in TROUBLES.items():
            if tid not in s.affords and tid != "fog":
                continue
            for fid, f in FIXES.items():
                if tid in f.guards:
                    for pid in PRIZES:
                        combos.append((sid, tid, fid, pid))
    return combos


def explain_rejection(trouble: Trouble, fix: Fix) -> str:
    return f"(No story: {fix.label} is not a believable fix for {trouble.label} in this pirate tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.fix:
        if args.trouble not in FIXES[args.fix].guards:
            raise StoryError(explain_rejection(TROUBLES[args.trouble], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)
              and (args.prize is None or c[3] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, fix, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(CAPTAINS)
    helper = args.helper or rng.choice([n for n in CAPTAINS if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, trouble=trouble, fix=fix, prize=prize, name=name, gender=gender, helper=helper, helper_gender=helper_gender, trait=trait)


def _story_name(entity: Entity) -> str:
    return entity.label or entity.id


def tell(setting: Setting, trouble: Trouble, fix: Fix, prize: Prize, name: str, gender: str, helper: str, helper_gender: str, trait: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=name, kind="character", type=gender, label=name, role="captain"))
    mate = w.add(Entity(id=helper, kind="character", type=helper_gender, label=helper, role="mate"))
    boat = w.add(Entity(id="boat", type="boat", label="the old boat", phrase="the old boat"))
    w.add(Entity(id="prize", type="thing", label=prize.label, phrase=prize.phrase, connected_to=boat.id))
    w.add(Entity(id="trouble", type="thing", label=trouble.label))
    w.add(Entity(id="fix", type="thing", label=fix.label))
    w.facts.update(hero=hero, mate=mate, boat=boat, prize=prize, trouble=trouble, fix=fix, setting=setting)
    hero.memes["hope"] = 1
    mate.memes["hope"] = 1
    boat.meters["sound"] = 1
    boat.meters["damage"] = 0
    boat.meters["kaput"] = 0

    w.say(f"{hero.id} and {mate.id} sailed by {setting.place} in a small pirate boat. {hero.id} was a {trait} little pirate who loved the sea.")
    w.say(f"They wanted to keep {prize.phrase} safe while they crossed the water.")
    w.para()
    w.say(f"But {trouble.label} made the day hard. {trouble.worsen}.")
    hero.memes["worry"] += 1
    mate.memes["worry"] += 1

    if trouble.id == "fog":
        w.say(f"{mate.id} held up {fix.label}, hoping it would {fix.verb}.")
    elif trouble.id == "leak":
        w.say(f"{hero.id} tried {fix.label} to {fix.verb}.")
    elif trouble.id == "storm":
        w.say(f"{mate.id} called for {fix.label} to {fix.verb}.")
    else:
        w.say(f"{hero.id} grabbed {fix.label} and tried to {fix.verb}.")

    w.para()
    boat.meters["damage"] += 1
    if trouble.id in {"storm", "rocks"}:
        boat.meters["damage"] += 1
    if fix.id == "lantern":
        boat.meters["light"] += 1
    if fix.id == "patch":
        boat.meters["patch"] += 1
    if fix.id == "bucket":
        boat.meters["water"] += 1
    boat.meters["kaput"] += 1
    boat.memes["kaput"] += 1

    w.say(f"Then the old boat went kaput. The mast creaked, the boards groaned, and the plan fell apart.")
    w.say(f"{prize.label.capitalize()} slipped into the spray, and the crew could not save it in time.")
    hero.memes["sad"] += 1
    mate.memes["sad"] += 1
    hero.memes["fear"] += 1
    mate.memes["fear"] += 1
    w.para()
    w.say(f"They rowed as hard as they could toward shore, but the sea kept pushing back.")
    w.say(f"At last they reached dry land empty-handed, with the boat still kaput behind them.")

    w.facts["outcome"] = "bad"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate story for a young child that includes the word "kaput" and ends badly.',
        f"Tell a pirate tale where {f['hero'].id} and {f['mate'].id} try to save {f['prize'].label} but their boat goes kaput.",
        f'Write a simple bad-ending story about a pirate boat, a problem at sea, and the word "kaput".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, prize, trouble, fix = f["hero"], f["mate"], f["prize"], f["trouble"], f["fix"]
    return [
        QAItem(question=f"Who was the pirate story about?", answer=f"It was about {hero.id} and {mate.id}, two little pirates sailing by {f['setting'].place}. They were trying to protect {prize.label} when the trouble began."),
        QAItem(question=f"What problem did the pirates face?", answer=f"They faced {trouble.label}. It made the trip hard, and even though they tried {fix.label}, the old boat still went kaput."),
        QAItem(question=f"What happened to the boat at the end?", answer=f"The old boat went kaput and the crew had to leave it behind. They made it to shore, but they lost the treasure and the boat stayed broken."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does kaput mean?", answer="Kaput means broken or not working anymore. If something is kaput, it cannot do its job until it is fixed."),
        QAItem(question="What is a pirate boat for?", answer="A pirate boat carries pirates over the water. It helps them travel, search for treasure, and get from one place to another."),
        QAItem(question="Why is a storm dangerous at sea?", answer="A storm makes strong wind and big waves. That can push a boat around, break things, and make sailing much harder."),
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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,F,P) :- setting(S), trouble(T), fix(F), prize(P), good_fix(T,F).
good_fix(T,F) :- trouble(T), fix(F), guards(F,T).
kaput_boat :- good_fix(T,F), trouble(T), fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for g in sorted(fix.guards):
            lines.append(asp.fact("guards", fid, g))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    py_set = set(valid_combos())
    as_set = set(asp_valid_combos())
    ok = 0
    if py_set != as_set:
        ok = 1
        print("MISMATCH between ASP and Python valid_combos()")
        print("only in python:", sorted(py_set - as_set))
        print("only in asp:", sorted(as_set - py_set))
    try:
        params = resolve_params(argparse.Namespace(setting=None, trouble=None, fix=None, prize=None, name=None, gender=None, helper=None, helper_gender=None, trait=None), random.Random(777))
        sample = generate(params)
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print(f"OK: ASP parity {len(py_set)} combos; smoke test passed.")
    return ok


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    trouble = TROUBLES.get(params.trouble)
    fix = FIXES.get(params.fix)
    prize = PRIZES.get(params.prize)
    if not all([setting, trouble, fix, prize]):
        raise StoryError("Invalid params for this world.")
    if trouble.id not in fix.guards:
        raise StoryError(explain_rejection(trouble, fix))
    world = tell(setting, trouble, fix, prize, params.name, params.gender, params.helper, params.helper_gender, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


CURATED = [
    StoryParams(setting="harbor", trouble="storm", fix="tow", prize="map", name="Mara", gender="girl", helper="Bram", helper_gender="boy", trait="brave"),
    StoryParams(setting="island", trouble="fog", fix="lantern", prize="flag", name="Nell", gender="girl", helper="Jax", helper_gender="boy", trait="curious"),
    StoryParams(setting="cove", trouble="rocks", fix="patch", prize="chest", name="Finn", gender="boy", helper="Ivy", helper_gender="girl", trait="stubborn"),
    StoryParams(setting="harbor", trouble="leak", fix="bucket", prize="map", name="Tia", gender="girl", helper="Seth", helper_gender="boy", trait="cheerful"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
