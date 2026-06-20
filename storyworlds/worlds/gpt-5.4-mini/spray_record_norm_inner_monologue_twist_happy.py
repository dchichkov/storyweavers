#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spray_record_norm_inner_monologue_twist_happy.py
================================================================================

A standalone storyworld for a tiny superhero-style domain: a child hero notices
a rule-breaking spray pattern, worries in an inner monologue, discovers a twist,
and ends happily by using a record and the town norm in a better way.

Seed words:
- spray
- record
- norm

Features:
- Inner Monologue
- Twist
- Happy Ending

Style:
- Superhero Story

This world is self-contained, uses a small causal simulation with typed entities,
physical meters and emotional memes, and includes an ASP twin plus a Python
reasonableness gate.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    norm: str
    hero_display: str
    watchful: str


@dataclass
class Spray:
    id: str
    label: str
    phrase: str
    mess: str
    splash: str
    forbidden: bool = True
    makes_spray: bool = True


@dataclass
class Record:
    id: str
    label: str
    phrase: str
    keeps: str
    prefix: str


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spatter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    target = world.entities.get("target")
    if not hero or not target:
        return out
    if hero.meters["sprayed"] < THRESHOLD:
        return out
    sig = ("spatter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["mess"] += 1
    hero.memes["worry"] += 1
    out.append("__spray__")
    return out


CAUSAL_RULES = [Rule("spatter", "physical", _r_spatter)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def hazard_at_risk(spray: Spray, setting: Setting) -> bool:
    return spray.makes_spray and setting.norm == "clean wall"


def forecast(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["sprayed"] += 1
    propagate(sim, narrate=False)
    return {"mess": sim.get("target").meters["mess"], "worry": sim.get("hero").memes["worry"]}


def setup(world: World, hero: Entity, sidekick: Entity, setting: Setting) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {sidekick.id} patrolled {setting.place}, "
        f"where the town norm was to keep every wall clean and every window shining."
    )
    world.say(
        f"{hero.id} wore a cape in {setting.hero_display} colors, and {sidekick.id} kept watch beside {setting.watchful}."
    )


def inner_monologue(world: World, hero: Entity, spray: Spray, setting: Setting) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'Inside {hero.id}\'s head, a quiet thought flickered: "If that spray hits the wall, '
        f'the norm will be broken, and everybody will notice."'
    )
    world.say(
        f"{hero.id} clenched {hero.pronoun('possessive')} fists and told {hero.pronoun('object')}self to stay calm."
    )


def lure(world: World, hero: Entity, spray: Spray) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then {hero.id} spotted a shiny spray can with a silly label and whispered, "
        f'"Maybe this is the clue."'
    )
    world.say(
        f"{hero.id} lifted it higher, because heroes sometimes think with their feet before their brains catch up."
    )


def reveal_twist(world: World, sidekick: Entity, spray: Spray, record: Record) -> None:
    world.say(
        f"{sidekick.id} gasped, but not because of danger. The twist was that the spray was only stage paint for the town parade."
    )
    world.say(
        f'On the side of the can was a record card that read, "{record.prefix} the parade trail when the silver dots appear."'
    )


def use_spray(world: World, hero: Entity, spray: Spray) -> None:
    hero.meters["sprayed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} pressed the nozzle, and a neat spray of silver dots zipped into the air like tiny stars."
    )
    world.say(
        f"The dots landed exactly where the clue said they would, and for one breath the street looked like a secret sky."
    )


def fix_scene(world: World, fix: Fix, target: Entity, setting: Setting) -> None:
    target.meters["mess"] = 0.0
    world.say(
        f"{setting.watchful.capitalize()} then used the {fix.label} to solve the real problem: {fix.text}."
    )
    world.say(
        f"The wall shone clean again, which meant the town norm stayed true and nobody had to worry."
    )


def happy_end(world: World, hero: Entity, sidekick: Entity, record: Record, setting: Setting) -> None:
    hero.memes["joy"] += 2
    sidekick.memes["joy"] += 2
    world.say(
        f"For a moment, {hero.id} laughed at the twist, then wrote the whole clue into {record.phrase}."
    )
    world.say(
        f"That way the hero could remember the parade path, and the day ended with {hero.id} and {sidekick.id} smiling under a clean {setting.place} sign."
    )


def tell(setting: Setting, spray: Spray, record: Record, fix: Fix,
         hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Pip", sidekick_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    target = world.add(Entity(id="target", type="wall", label="the wall"))
    world.add(Entity(id="record", type="thing", label=record.label))
    world.add(Entity(id="spraycan", type="thing", label=spray.label))
    world.facts["setting"] = setting
    world.facts["spray"] = spray
    world.facts["record"] = record
    world.facts["fix"] = fix

    setup(world, hero, sidekick, setting)
    world.para()
    inner_monologue(world, hero, spray, setting)
    lure(world, hero, spray)
    world.para()
    reveal_twist(world, sidekick, spray, record)
    use_spray(world, hero, spray)
    world.para()
    fix_scene(world, fix, target, setting)
    happy_end(world, hero, sidekick, record, setting)

    world.facts.update(
        hero=hero, sidekick=sidekick, target=target,
        outcome="happy", record_kept=True, mess_fixed=target.meters["mess"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "downtown": Setting("downtown", "downtown avenue", "clean wall", "blue and gold", "the watchtower"),
    "harbor": Setting("harbor", "harbor street", "clean wall", "red and white", "the lighthouse"),
    "park": Setting("park", "city park", "clean wall", "green and silver", "the fountain"),
}

SPRAYS = {
    "silver_spray": Spray("silver_spray", "a silver spray can", "a silver spray can", "spray", "silver spray"),
    "hero_spray": Spray("hero_spray", "a hero spray", "a hero spray", "spray", "hero spray"),
}

RECORDS = {
    "logbook": Record("logbook", "a record book", "the record book", "keeps records safe", "Write down"),
    "ledger": Record("ledger", "a city ledger", "the city ledger", "keeps records in order", "Copy"),
}

FIXES = {
    "wipe": Fix("wipe", 3, 4, "wiped the harmless stage paint away with a soft cloth", "tried to wipe it, but the stain was already too wide", "wiped the stage paint away"),
    "cover": Fix("cover", 2, 3, "covered the wet spot with a clean poster until help arrived", "covered it too late, and the mark kept spreading", "covered the wet spot"),
    "cleaner": Fix("cleaner", 3, 5, "used a gentle cleaner that lifted the paint without a trace", "used the cleaner, but it could not beat the stain", "used gentle cleaner"),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Tess", "Ivy", "Zara"]
BOY_NAMES = ["Pip", "Finn", "Max", "Theo", "Noah", "Jett"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for spray_id, spray in SPRAYS.items():
            if not hazard_at_risk(spray, s):
                continue
            for rid, record in RECORDS.items():
                combos.append((sid, spray_id, rid))
    return combos


@dataclass
class StoryParams:
    setting: str
    spray: str
    record: str
    fix: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with spray, record, and norm.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spray", choices=SPRAYS)
    ap.add_argument("--record", choices=RECORDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for spray_id in SPRAYS:
        lines.append(asp.fact("spray", spray_id))
        lines.append(asp.fact("makes_spray", spray_id))
    for rid in RECORDS:
        lines.append(asp.fact("record", rid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S, P) :- spray(S), setting(P).
sensible(F) :- fix(F), sense(F, V), sense_min(M), V >= M.
valid(Setting, Spray, Record) :- hazard(Spray, Setting), record(Record).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    if set(asp_sensible()) == {f.id for f in sensible_fixes()}:
        print("OK: sensible fixes match.")
    else:
        print("MISMATCH in sensible fixes.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def explain_rejection(spray: Spray, setting: Setting) -> str:
    return f"(No story: {spray.label} would not fit the town norm in {setting.place}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spray:
        if not hazard_at_risk(SPRAYS[args.spray], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(SPRAYS[args.spray], SETTINGS[args.setting]))
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.spray in (None, c[1])
              and args.record in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spray, record = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    side_gender = args.sidekick_gender or ("boy" if gender == "girl" else "girl")
    sidekick = args.sidekick or rng.choice(GIRL_NAMES if side_gender == "girl" else BOY_NAMES)
    if sidekick == hero:
        sidekick = "Quinn"
    return StoryParams(setting, spray, record, fix, hero, gender, sidekick, side_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a child that includes the words "spray", "record", and "norm".',
        f"Tell a happy superhero tale where {f['hero'].id} worries in an inner monologue, then discovers a twist about a spray can and a record book.",
        f"Write a story in which a hero follows the town norm, uses a record to solve a problem, and ends happy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, setting = f["hero"], f["sidekick"], f["setting"]
    record, fix = f["record"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, a young hero, and {sidekick.id}, who helps with the patrol."),
        ("What did the hero worry about?",
         f"{hero.id} worried that the spray would break the town norm and leave a mark on the wall. That fear is what started the inner monologue."),
        ("What was the twist?",
         f"The twist was that the spray was not a disaster at all. It was harmless parade paint, and the record card showed how to use it for a clue."),
        ("How did the story end?",
         f"It ended happily: the wall was cleaned, the record was kept, and {hero.id} and {sidekick.id} smiled in {setting.place}."),
        ("What did the record help with?",
         f"The {record.label} kept the clue safe so the hero could remember it later. That let the hero solve the puzzle without breaking the norm."),
        ("What fixed the wall?",
         f"The {fix.label} fixed the wall by removing the wet paint. After that, the place looked normal again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a norm?",
         "A norm is a rule or habit people follow together so things stay orderly and fair."),
        ("What does spray mean?",
         "Spray is a fine mist or a quick burst of tiny drops that scatters outward."),
        ("What is a record?",
         "A record is something that keeps information so you can remember it later."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("downtown", "silver_spray", "logbook", "wipe", "Nova", "girl", "Pip", "boy"),
    StoryParams("harbor", "hero_spray", "ledger", "cleaner", "Mira", "girl", "Finn", "boy"),
    StoryParams("park", "silver_spray", "logbook", "cover", "Theo", "boy", "Ivy", "girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPRAYS[params.spray], RECORDS[params.record], FIXES[params.fix],
                 params.hero, params.hero_gender, params.sidekick, params.sidekick_gender)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero}: {p.spray} / {p.record} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
