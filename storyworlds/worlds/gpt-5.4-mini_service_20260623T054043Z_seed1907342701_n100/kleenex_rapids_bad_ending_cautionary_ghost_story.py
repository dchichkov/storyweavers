#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/kleenex_rapids_bad_ending_cautionary_ghost_story.py
===============================================================================================================

A small standalone storyworld for a cautionary ghost story about a child,
a whispering river, and the loss of something soft and ordinary in the rapids.

The world is intentionally tiny: a few settings, a few ghost-story lures, and
one fragile object that can be lost or ruined. The prose is state-driven; the
ending changes when the world changes.

Seed tale idea:
- A child hears a ghostly whisper near the river.
- A box of kleenex matters because it is the one thing the child keeps reaching
  for to wipe tears, noses, or wet hands.
- The rapids are beautiful but dangerous.
- The story should warn rather than comfort: if the child follows the whisper,
  the ending turns bad and the night remembers it.

Contract notes:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- includes a Python reasonableness gate and an inline ASP twin
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    whisper: str
    cue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fragile:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "bridge"
    lure: str = "whisper"
    fragile: str = "kleenex"
    rescue: str = "lantern"
    child_name: str = "Mina"
    child_gender: str = "girl"
    helper_gender: str = "mother"
    helper_name: str = "Aunt Mara"
    seed: Optional[int] = None


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
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "bridge": Setting("bridge", "the old bridge above the rapids", "misty", {"follow", "lose"}),
    "bank": Setting("bank", "the river bank near the rapids", "windy", {"follow", "lose"}),
    "cabin": Setting("cabin", "the porch of the small cabin by the river", "cold", {"warn"}),
}

LURES = {
    "whisper": Lure("whisper", "a soft ghost whisper", "follow the sound", {"ghost", "whisper"}),
    "lantern_glow": Lure("lantern_glow", "a pale lantern glow that drifted like a ghost", "walk toward the glow", {"ghost", "light"}),
    "footprints": Lure("footprints", "bare footprints that appeared and faded in the mud", "step after the prints", {"ghost", "mud"}),
}

FRAGILES = {
    "kleenex": Fragile("kleenex", "kleenex", "a soft box of kleenex", "hands", False, {"kleenex", "paper"}),
    "lantern_cover": Fragile("lantern_cover", "lantern cover", "a paper lantern cover", "hands", False, {"paper"}),
    "note": Fragile("note", "note", "a folded note", "hands", False, {"paper"}),
}

RESCUES = {
    "lantern": Rescue("lantern", "lantern", "a lantern", 3, 3, {"light"}),
    "rope": Rescue("rope", "rope", "a rope tied to the porch rail", 2, 2, {"rope"}),
    "shout": Rescue("shout", "shout", "a loud shout for help", 1, 1, {"voice"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "June", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Max", "Noah"]
HELPER_NAMES = ["Aunt Mara", "Mom", "Dad", "Grandma Rue"]

KNOWLEDGE = {
    "kleenex": [("What is a kleenex box?", "A kleenex box holds soft tissues you can pull out one by one. People use them to wipe noses or tears.")],
    "rapids": [("What are rapids?", "Rapids are parts of a river where the water moves fast and bumps over rocks. They can be very dangerous to stand too close to.")],
    "ghost": [("What is a ghost story?", "A ghost story is a spooky story with whispery sounds, shadows, and mystery. It can be scary without being real.")],
    "light": [("Why can a lantern help at night?", "A lantern makes a steady light so people can see where they are going. It is safer than walking in the dark.")],
    "paper": [("Why does paper get ruined by water?", "Paper soaks up water, bends, and tears easily. Once it gets wet, it is hard to use again.")],
}

KNOWLEDGE_ORDER = ["ghost", "kleenex", "rapids", "light", "paper"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for l in LURES:
            for f in FRAGILES:
                for r in RESCUES:
                    if reasonableness_ok(SETTINGS[s], LURES[l], FRAGILES[f], RESCUES[r]):
                        combos.append((s, l, f, r))
    return combos


def reasonableness_ok(setting: Setting, lure: Lure, fragile: Fragile, rescue: Rescue) -> bool:
    return "follow" in setting.affords and fragile.id == "kleenex" and rescue.sense >= 1


def explain_rejection() -> str:
    return "(No story: this world wants the child, the river, and the kleenex to matter together.)"


def story_outcome(setting: Setting, lure: Lure, fragile: Fragile, rescue: Rescue) -> str:
    if setting.id == "cabin":
        return "warned"
    if rescue.power >= 3 and setting.id == "bridge":
        return "bad"
    return "bad"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary ghost story world: kleenex, rapids, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--fragile", choices=FRAGILES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.lure is None or c[1] == args.lure)
              and (args.fragile is None or c[2] == args.fragile)
              and (args.rescue is None or c[3] == args.rescue)]
    if not combos:
        raise StoryError(explain_rejection())
    s, l, f, r = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(setting=s, lure=l, fragile=f, rescue=r,
                       child_name=child_name, child_gender=gender,
                       helper_gender=helper_gender, helper_name=helper_name)


def _warn_before(world: World, child: Entity, helper: Entity, lure: Lure) -> None:
    child.memes["curiosity"] += 1
    helper.memes["fear"] += 1
    world.say(f"{child.id} stood where the mist from the rapids touched the bridge. {child.id} heard {lure.whisper}, and it sounded like a ghost calling from the water.")
    world.say(f"{helper.id} caught the sound too. \"Do not follow that voice,\" {helper.id} said. \"The rapids are hungry tonight.\"")


def _reach_for_kleenex(world: World, child: Entity, fragile: Entity) -> None:
    child.memes["defiance"] += 1
    child.meters["wet"] += 1
    world.say(f"But {child.id} still reached for the {fragile.label}, because the spray had dampened {child.pronoun('possessive')} hands and the soft box felt like something safe to hold.")
    world.say(f"{child.id} stepped closer to the edge, where the rocks were slick and the water below roared like a hidden drum.")


def _bad_turn(world: World, child: Entity, helper: Entity, fragile: Entity, lure: Lure) -> None:
    fragile.meters["lost"] += 1
    fragile.meters["wet"] += 1
    child.memes["fear"] += 2
    helper.memes["fear"] += 1
    world.say(f"A gust of river wind snatched the {fragile.label}. It spun once, white as a tiny ghost, and flew out over the rapids.")
    world.say(f"{child.id} grabbed at the air, but the box was already gone. The water swallowed it with a cold splash and kept rushing on.")


def _ending(world: World, child: Entity, helper: Entity, fragile: Entity) -> None:
    world.para()
    world.say(f"{helper.id} pulled {child.id} back from the edge and wrapped {child.pronoun('object')} in {helper.pronoun('possessive')} coat.")
    world.say(f"They went home quiet and shaken, and the room near the stove stayed dark while the river kept its secret.")
    world.say(f"Later, when {child.id} reached for the tissues, there was only an empty place where the {fragile.label} had been.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    lure = LURES[params.lure]
    fragile_cfg = FRAGILES[params.fragile]
    rescue = RESCUES[params.rescue]
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child",
                             meters={"wet": 0.0}, memes={"curiosity": 0.0, "defiance": 0.0, "fear": 0.0}))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper",
                              meters={"wet": 0.0}, memes={"fear": 0.0}))
    fragile = world.add(Entity(id="fragile", kind="thing", type="thing", label=fragile_cfg.label,
                               phrase=fragile_cfg.phrase, meters={"wet": 0.0, "lost": 0.0}, memes={}))
    world.facts.update(child=child, helper=helper, setting=setting, lure=lure, fragile=fragile, rescue=rescue,
                       outcome=story_outcome(setting, lure, fragile_cfg, rescue))
    world.say(f"On a misty evening, {child.id} and {helper.id} walked beside {setting.place}. The rapids were loud enough to make the dark feel alive.")
    world.say(f"{child.id} held a {fragile.phrase}, just in case the wind made {child.pronoun('object')} tear up or sneeze.")
    world.para()
    _warn_before(world, child, helper, lure)
    _reach_for_kleenex(world, child, fragile)
    _bad_turn(world, child, helper, fragile, lure)
    _ending(world, child, helper, fragile)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, lure, fragile = f["child"], f["helper"], f["lure"], f["fragile"]
    return [
        f'Write a spooky cautionary story for a 3-to-5-year-old about {child.id}, {helper.id}, a ghostly whisper, and the rapids. Include the word "kleenex".',
        f"Tell a ghost story where {child.id} wants to follow {lure.whisper} near the rapids, but {helper.id} warns them and the kleenex is lost in the end.",
        f'Write a short, child-facing bad-ending story about a river, a whisper, and a {fragile.label}, with the word "rapids" in it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, lure, fragile = f["child"], f["helper"], f["lure"], f["fragile"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=f"It is about {child.id} and {helper.id}. They are the people who stand near the rapids when the ghostly whisper starts pulling at the night.",
        ),
        QAItem(
            question=f"What did {child.id} hear by the rapids?",
            answer=f"{child.id} heard {lure.whisper}. It sounded spooky, like a ghost trying to lead {child.pronoun('object')} closer to the water.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {child.id} not to go closer?",
            answer=f"{helper.id} knew the rapids were dangerous and the ground was slick. The warning was meant to keep {child.id} away from a place where a slip could become a bad ending.",
        ),
        QAItem(
            question=f"What happened to the {fragile.label} at the end?",
            answer=f"The {fragile.label} blew into the rapids and was lost. After that, there was only an empty place where it had been, which made the ending feel sad and cautionary.",
        ),
        QAItem(
            question=f"Was this a happy story?",
            answer=f"No. It was a cautionary ghost story, so the ending stayed bad on purpose. The point was to show that following a spooky whisper near rapids can cost you something important.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["lure"].tags) | set(world.facts["fragile"].tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[key])
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bridge", lure="whisper", fragile="kleenex", rescue="lantern", child_name="Mina", child_gender="girl", helper_gender="mother", helper_name="Aunt Mara"),
    StoryParams(setting="bank", lure="lantern_glow", fragile="kleenex", rescue="rope", child_name="Owen", child_gender="boy", helper_gender="father", helper_name="Dad"),
    StoryParams(setting="cabin", lure="footprints", fragile="kleenex", rescue="shout", child_name="Lena", child_gender="girl", helper_gender="mother", helper_name="Grandma Rue"),
    StoryParams(setting="bridge", lure="footprints", fragile="kleenex", rescue="lantern", child_name="Theo", child_gender="boy", helper_gender="father", helper_name="Mom"),
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        for t in sorted(lure.tags):
            lines.append(asp.fact("tag", lid, t))
    for fid in FRAGILES:
        lines.append(asp.fact("fragile", fid))
    for rid, res in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, res.sense))
    lines.append(asp.fact("sense_min", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,L,F,R) :- setting(S), lure(L), fragile(F), rescue(R), F = kleenex.
good_rescue(R) :- rescue(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between ASP and Python valid_combos")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        ok = False
        print("SMOKE TEST FAILED: empty story")
    emit(sample, trace=False, qa=False)
    if ok:
        print(f"OK: {len(py)} combos, smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="Cautionary ghost story world with kleenex and rapids.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    s, l, f, r = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["mother", "father"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = rng.choice(HELPER_NAMES)
    return StoryParams(setting=s, lure=l, fragile=f, rescue=r,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
