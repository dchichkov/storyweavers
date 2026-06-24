#!/usr/bin/env python3
"""
storyworlds/worlds/deceased_frown_caper_reconciliation_sound_effects_heartwarming.py
====================================================================================

A small heartwarming storyworld about a child, a missing loved one, a quiet caper,
and a reconciliation carried by sound effects.

Seed premise:
A child feels a deep frown after someone beloved has died. A small caper to make
a memorial surprise goes sideways, but careful listening, shared memories, and a
gentle reconciliation turn the day warm again.

The world uses typed entities with physical meters and emotional memes. The plot
is state-driven: grief can soften into comfort, tension can become repair, and
the ending proves that what changed is the relationship and the room's mood.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP_RULES twin
"""

from __future__ import annotations

import argparse
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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Caper:
    id: str
    verb: str
    sound: str
    mess: str
    tension: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    emotional_weight: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    action: str
    sound: str
    comfort: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "apartment": Setting("the apartment", True, {"caper", "music"}),
    "kitchen": Setting("the kitchen", True, {"caper", "baking"}),
    "living_room": Setting("the living room", True, {"caper", "music"}),
}

CAPERS = {
    "whisper_note": Caper("whisper_note", "slip a note under the door", "rustle-rustle", "rumpled paper", "a nervous hush", {"whisper", "note"}),
    "cookie_caper": Caper("cookie_caper", "sneak a cookie for a surprise plate", "crinkle-crunch", "cookie crumbs", "a little wobble", {"cookie", "treat"}),
    "button_search": Caper("button_search", "search for the lost button", "tap-tap", "tiny buttons", "a careful hush", {"button", "find"}),
}

TREASURES = {
    "photo": Treasure("photo", "photo", "a framed photo", "photo", 2.0, {"memory", "photo"}),
    "scarf": Treasure("scarf", "scarf", "a soft scarf", "scarf", 1.5, {"memory", "scarf"}),
    "bear": Treasure("bear", "bear", "a small stuffed bear", "bear", 1.2, {"memory", "bear"}),
}

REPAIRS = {
    "apology": Repair("apology", "apology", "say sorry together", "soft tap-tap", "a warm hug", {"sorry", "hug"}),
    "tea": Repair("tea", "tea", "make tea and sit together", "clink-clink", "a calm cup of tea", {"tea", "warm"}),
    "song": Repair("song", "song", "sing the old family song", "la-la-la", "a shared smile", {"song", "music"}),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Milo", "Finn"]


@dataclass
class StoryParams:
    setting: str
    caper: str
    treasure: str
    repair: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CAPERS:
            for t in TREASURES:
                if "memory" in TREASURES[t].tags and c in CAPERS:
                    combos.append((s, c, t))
    return combos


def reasonableness_gate(setting: str, caper: str, treasure: str) -> bool:
    return setting in SETTINGS and caper in CAPERS and treasure in TREASURES and "memory" in TREASURES[treasure].tags


def explain_rejection() -> str:
    return "(No story: this world needs a memory treasure and a gentle caper so the reconciliation can matter.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAPERS.items():
        lines.append(asp.fact("caper", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("caper_tag", cid, tag))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("treasure_tag", tid, tag))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for tag in sorted(r.tags):
            lines.append(asp.fact("repair_tag", rid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,T) :- setting(S), caper(C), treasure(T), treasure_tag(T, memory).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.w = World(setting)

    def build(self, params: StoryParams) -> World:
        w = self.w
        child = w.add(Entity(params.name, "character", params.gender))
        parent = w.add(Entity("Parent", "character", params.parent, "parent"))
        dead = w.add(Entity("Deceased", "character", "person", "deceased loved one"))
        caper = CAPERS[params.caper]
        treasure = TREASURES[params.treasure]
        repair = REPAIRS[params.repair]

        child.memes["frown"] = 2.0
        child.memes["love"] = 1.0
        dead.meters["gone"] = 1.0
        w.facts.update(child=child, parent=parent, dead=dead, caper=caper, treasure=treasure, repair=repair)

        w.say(f"{child.id} had a small frown because {dead.label_word} was gone, and the room felt too quiet.")
        w.say(f"{parent.label_word.capitalize()} kept {parent.pronoun('possessive')} voice soft, like a blanket over a chair.")

        w.para()
        w.say(f"To feel close again, {child.id} planned a little caper: {caper.verb}.")
        w.say(f"It made a {caper.sound} sound, and for a moment the air felt busy and brave.")
        child.memes["hope"] = 1.0

        if params.caper == "cookie_caper":
            child.meters["crumbs"] = 1.0
            child.memes["frown"] += 1.0
            w.say(f"But the {caper.mess} made {child.id}'s frown come back, because the surprise plate looked messy.")
        elif params.caper == "whisper_note":
            child.memes["nervous"] = 1.0
            w.say(f"The {caper.sound} was tiny and shy, and that made {child.id} pause and listen more closely.")
        else:
            child.memes["searching"] = 1.0
            w.say(f"Every tap-tap reminder felt like a memory opening a drawer.")

        w.para()
        w.say(f"Then {child.id} found {treasure.phrase} that had belonged to {dead.label_word}.")
        child.memes["grief"] = 1.0
        child.meters["treasure_close"] = 1.0

        w.say(f"{child.id} held it near and whispered, 'I miss you.'")
        w.say(f"{parent.label_word.capitalize()} came beside {child.pronoun('object')} and did not hurry the tears.")

        w.para()
        w.say(f"Together they chose a repair: {repair.action}.")
        w.say(f"It went with a {repair.sound} sound, and soon the room had {repair.comfort} instead of tension.")
        child.memes["frown"] = 0.0
        child.memes["comfort"] = 2.0
        parent.meters["tea"] = 1.0

        w.para()
        if params.repair == "song":
            w.say(f"They sang the old family song, and the last bit of sadness softened into a smile.")
        elif params.repair == "tea":
            w.say(f"The warm tea steamed gently, and the quiet felt kind instead of empty.")
        else:
            w.say(f"The apology was simple and real, and it made room for a hug that lasted a long time.")
        w.say(f"In the end, {child.id} still missed {dead.label_word}, but {child.id} could frown less and breathe easier.")
        w.say(f"The little caper became a warm memory, and the house sounded peaceful again.")

        return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story where {f['child'].id} feels a frown after someone deceased is missed, then follows a small caper that ends in reconciliation.",
        f"Tell a gentle story for a young child about grief, a careful caper, and a warm repair using sound effects like {f['caper'].sound} and {f['repair'].sound}.",
        f"Make a short, comforting story where a child and parent turn a sad day into a softer one by finding a memory treasure and making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, dead, caper, treasure, repair = f["child"], f["parent"], f["dead"], f["caper"], f["treasure"], f["repair"]
    return [
        QAItem(
            question=f"Why did {child.id} start the story with a frown?",
            answer=f"{child.id} had a frown because {dead.label_word} was gone, and that made the room feel quiet and sad.",
        ),
        QAItem(
            question=f"What caper did {child.id} try to do to feel close again?",
            answer=f"{child.id} tried to {caper.verb}, and it made a {caper.sound} sound while the child looked for comfort.",
        ),
        QAItem(
            question=f"What treasure helped {child.id} remember {dead.label_word}?",
            answer=f"A {treasure.label} helped because it had belonged to {dead.label_word} and brought back a loving memory.",
        ),
        QAItem(
            question=f"How did the story end after the sad part?",
            answer=f"{child.id} and {parent.label_word} chose a repair: {repair.action}. That brought reconciliation, a hug, and a calmer room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What is a frown?", "A frown is a face that shows someone feels sad, worried, or upset."),
        QAItem("What is reconciliation?", "Reconciliation is when people make up, listen kindly, and feel close again after a hard moment."),
        QAItem("What are sound effects in a story?", "Sound effects are words that help you hear what happens, like tap-tap, rustle, or clink-clink."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


@dataclass
class StoryParams:
    setting: str
    caper: str
    treasure: str
    repair: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming reconciliation storyworld with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--caper", choices=CAPERS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.setting and args.caper and args.treasure:
        if not reasonableness_gate(args.setting, args.caper, args.treasure):
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.caper is None or c[1] == args.caper)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, caper, treasure = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(REPAIRS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, caper, treasure, repair, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = StoryWorld(SETTINGS[params.setting]).build(params)
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


def asp_verify() -> int:
    import asp
    c = set(asp_valid_combos())
    p = set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if c - p:
        print("only in clingo:", sorted(c - p))
    if p - c:
        print("only in python:", sorted(p - c))
    return 1


CURATED = [
    StoryParams("apartment", "whisper_note", "photo", "apology", "Mia", "girl", "mother"),
    StoryParams("kitchen", "cookie_caper", "scarf", "tea", "Leo", "boy", "father"),
    StoryParams("living_room", "button_search", "bear", "song", "Nora", "girl", "mother"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combined() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_combined():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
