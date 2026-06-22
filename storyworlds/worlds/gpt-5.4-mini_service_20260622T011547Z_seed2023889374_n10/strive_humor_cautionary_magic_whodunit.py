#!/usr/bin/env python3
"""
storyworlds/worlds/strive_humor_cautionary_magic_whodunit.py
=============================================================

A small storyworld about a silly magical whodunit: somebody tries to help,
misleading clues appear, a cautious child notices what really happened, and the
ending shows the magic was handled safely.

The seed tale is imagined as:
- a child and a grown-up find a puzzling mess,
- magical objects create funny clues,
- one child wants to strive to solve it fast,
- caution and observation reveal the culprit,
- the mistake is fixed, the magic is tamed, and the ending is warm.

This script follows the shared Storyweavers contract with:
- typed entities carrying physical meters and emotional memes,
- a forward causal model,
- a Python reasonableness gate plus inline ASP twin,
- three QA sets grounded in world state,
- default / -n / --all / --seed / --trace / --qa / --json / --asp / --verify / --show-asp.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    magic: bool = False
    clue: bool = False
    suspect: bool = False
    innocent: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    room: str
    mood: str
    clue_place: str
    magic_light: str
    safe_tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    trick: str
    effect: str
    target: str
    harmless: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    clue: str
    can_stain: bool = False
    can_glow: bool = False
    can_spill: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    magic: str
    suspect: str
    clue: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("mischief", 0.0) < THRESHOLD:
            continue
        sig = ("clue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mess"] = world.get("room").meters.get("mess", 0.0) + 1
        out.append(f"A funny clue appeared near {e.label or e.id}.")
    return out


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("warning_given") and not world.facts.get("resolved"):
        hero = world.get(world.facts["hero"])
        helper = world.get(world.facts["helper"])
        sig = ("warn", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
            helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
            out.append(f"{helper.id} pointed at the clue and said to look closely.")
    return out


CAUSAL_RULES = [Rule("clue", _r_clue), Rule("warn", _r_warn)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, magic in MAGICS.items():
            for suid, suspect in SUSPECTS.items():
                for cid, clue in CLUES.items():
                    if magic.harmless and suspect.label != clue.target:
                        continue
                    if suspect.can_stain or suspect.can_glow or suspect.can_spill:
                        combos.append((sid, mid, suid, cid))
    return combos


def reason_for_rejection(setting: Setting, magic: MagicItem, suspect: Suspect, clue: MagicItem) -> str:
    if not magic.harmless:
        return f"(No story: {magic.label} is too wild for a child-safe whodunit.)"
    if suspect.label != clue.target:
        return f"(No story: {clue.label} does not match the likely culprit in {setting.place}.)"
    return "(No story: this combination does not make a clear, child-safe mystery.)"


def choose_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whimsical magical whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
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
        raise StoryError("Unknown setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.magic is None or c[1] == args.magic)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.clue is None or c[3] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, magic, suspect, clue = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or choose_name(rng, hero_gender)
    helper = args.helper or choose_name(rng, helper_gender, avoid=hero)
    adult = args.adult or rng.choice(list(ADULTS))
    return StoryParams(setting=setting, magic=magic, suspect=suspect, clue=clue,
                       hero=hero, hero_gender=hero_gender, helper=helper,
                       helper_gender=helper_gender, adult=adult)


def setup_world(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    magic = MAGICS[params.magic]
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    adult = w.add(Entity(id="Adult", kind="character", type=params.adult, role="adult", label=f"the {params.adult}"))
    room = w.add(Entity(id="room", type="room", label=setting.room))
    item = w.add(Entity(id="magic", type="thing", label=magic.label, magic=True, clue=False, suspect=False))
    sus = w.add(Entity(id="suspect", type="thing", label=suspect.label, suspect=True, clue=False))
    clue_ent = w.add(Entity(id="clue", type="thing", label=clue.label, clue=True))
    hero.meters["mischief"] = 0.0
    hero.memes["strive"] = 1.0
    helper.memes["caution"] = 1.0
    w.facts.update(setting=setting, magic=magic, suspect_cfg=suspect, clue_cfg=clue,
                   hero=params.hero, helper=params.helper, adult=adult.id, warning_given=False,
                   resolved=False, culprit=suspect.label, clue_target=clue.target)
    return w


def tell(params: StoryParams) -> World:
    w = setup_world(params)
    setting = SETTINGS[params.setting]
    magic = MAGICS[params.magic]
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    hero = w.get(params.hero)
    helper = w.get(params.helper)
    adult = w.get("Adult")
    hero.memes["delight"] = 1.0
    helper.memes["delight"] = 1.0
    w.say(f"On a bright morning in {setting.place}, {hero.id} and {helper.id} found a puzzle that looked almost serious.")
    w.say(f"Near {setting.clue_place}, the strange {magic.label} was making a silly {clue.label}, like a joke with secrets.")
    w.para()
    hero.memes["strive"] = hero.memes.get("strive", 0.0) + 1
    w.facts["warning_given"] = True
    w.say(f'{hero.id} wanted to strive to solve the mystery at once. "{magic.narration}," {hero.id} said, '
          f'but {helper.id} frowned and pointed out that the clue could fool them.')
    w.say(f'"If we rush, we may blame the wrong {suspect.label}," {helper.id} said. "{setting.magic_light} can be funny, but it still needs careful eyes."')
    w.para()
    if suspect.can_spill:
        w.get("room").meters["mess"] = w.get("room").meters.get("mess", 0.0) + 1
    w.get("magic").meters["mischief"] = 1.0
    propagate(w, narrate=True)
    w.say(f"They followed the clue to {setting.room}, where a small {suspect.label} sat exactly where the joke had started.")
    w.say(f"At last, the case made sense: {suspect.label} had caused the mess, and the magical trick only made it look mysterious.")
    w.para()
    w.facts["resolved"] = True
    adult.memes["pride"] = adult.memes.get("pride", 0.0) + 1
    hero.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    w.say(f"{adult.label_word.capitalize()} smiled, because the children had not only solved the whodunit, they had solved it kindly.")
    w.say(f"They cleaned up together, and the last magical sparkle faded into a safe little twinkle.")
    w.say(f"{hero.id} and {helper.id} left the room laughing, ready to strive again another day, but this time with slower steps and sharper eyes.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous, cautionary magical whodunit for a young child that includes the word "strive" and takes place in {f["setting"].place}.',
        f"Tell a story where {f['hero']} and {f['helper']} try to solve a magical mystery, but one of them remembers to be careful before they accuse the wrong suspect.",
        f"Write a child-friendly mystery with a funny magical clue, a safe ending, and a lesson about not rushing to blame {f['culprit']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get(f["hero"])
    helper = world.get(f["helper"])
    setting = f["setting"]
    suspect = f["suspect_cfg"]
    clue = f["clue_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {setting.place}?",
            answer=f"{hero.id} wanted to strive to solve the mystery right away. The clue was funny, but {helper.id} knew they needed to look carefully first."
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} not to rush?",
            answer=f"{helper.id} worried they might blame the wrong {suspect.label}. The magical clue looked odd, so careful eyes were needed to tell the joke from the truth."
        ),
        QAItem(
            question=f"What finally explained the puzzling {clue.label}?",
            answer=f"The {suspect.label} had caused the mess, and the magic only made the clue look stranger. Once they noticed that, the mystery made sense."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {helper.id}?",
            answer=f"They solved the mystery kindly, cleaned up, and left laughing. They also remembered to be more cautious the next time a magical trick tried to fool them."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["magic"].tags) | set(f["suspect_cfg"].tags) | set(f["clue_cfg"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
        bits = []
        if e.meters:
            meters = {k: v for k, v in e.meters.items() if v}
            if meters:
                bits.append(f"meters={meters}")
        if e.memes:
            memes = {k: v for k, v in e.memes.items() if v}
            if memes:
                bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.magic not in MAGICS or params.suspect not in SUSPECTS or params.clue not in CLUES:
        raise StoryError("Invalid story parameters.")
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
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if m.harmless:
            lines.append(asp.fact("harmless", mid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.can_stain:
            lines.append(asp.fact("can_stain", sid))
        if s.can_glow:
            lines.append(asp.fact("can_glow", sid))
        if s.can_spill:
            lines.append(asp.fact("can_spill", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("targets", cid, c.target))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,Su,C) :- setting(S), magic(M), suspect(Su), clue(C),
                   harmless(M), targets(C,T), suspect_label(Su,T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in clingo:", sorted(a - p))
        print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(setting="library", magic="ink_bottle", suspect="cat", clue="footprints", hero="Nia", hero_gender="girl", helper="Owen", helper_gender="boy", adult="mother", seed=1),
        StoryParams(setting="parlor", magic="bell", suspect="mouse", clue="sparkles", hero="Milo", hero_gender="boy", helper="Lena", helper_gender="girl", adult="father", seed=2),
        StoryParams(setting="attic", magic="hat", suspect="parrot", clue="ribbons", hero="Rae", hero_gender="girl", helper="Toby", helper_gender="boy", adult="aunt", seed=3),
    ]


SETTINGS = {
    "library": Setting(id="library", place="the library", room="the reading room", mood="quiet", clue_place="the carpet by the shelf", magic_light="glow dust", safe_tool="magnifying glass", tags={"library", "book"}),
    "parlor": Setting(id="parlor", place="the parlor", room="the old parlor", mood="cozy", clue_place="the rug by the piano", magic_light="blink dust", safe_tool="lantern", tags={"room", "home"}),
    "attic": Setting(id="attic", place="the attic", room="the dusty attic", mood="mysterious", clue_place="the trunk corner", magic_light="moon shimmer", safe_tool="lantern", tags={"attic", "dust"}),
}

MAGICS = {
    "ink_bottle": MagicItem(id="ink_bottle", label="an ink bottle spell", trick="splatter", effect="inky swirls", target="cat", harmless=True, tags={"ink", "book"}),
    "bell": MagicItem(id="bell", label="a tiny bell charm", trick="jingle", effect="sparkly rings", target="mouse", harmless=True, tags={"bell"}),
    "hat": MagicItem(id="hat", label="a hat of feathers", trick="flutter", effect="ribbons in the air", target="parrot", harmless=True, tags={"hat", "bird"}),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="cat", motive="chasing a ribbon", clue="footprints", can_spill=False, can_glow=False, can_stain=True, tags={"cat", "paw"}),
    "mouse": Suspect(id="mouse", label="mouse", motive="snatching crumbs", clue="sparkles", can_spill=False, can_glow=True, can_stain=False, tags={"mouse", "tiny"}),
    "parrot": Suspect(id="parrot", label="parrot", motive="tugging shiny things", clue="ribbons", can_spill=True, can_glow=False, can_stain=False, tags={"bird", "feather"}),
}

CLUES = {
    "footprints": MagicItem(id="footprints", label="footprints", trick="tap-tap", effect="little marks", target="cat", harmless=True, tags={"footprints"}),
    "sparkles": MagicItem(id="sparkles", label="sparkles", trick="twinkle", effect="bright specks", target="mouse", harmless=True, tags={"sparkles"}),
    "ribbons": MagicItem(id="ribbons", label="ribbons", trick="flutter", effect="swishing strands", target="parrot", harmless=True, tags={"ribbons"}),
}

GIRL_NAMES = ["Nia", "Rae", "Mina", "Lia", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Toby", "Ezra", "Finn"]
ADULTS = ["mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for mid, m in MAGICS.items():
            for suid, su in SUSPECTS.items():
                for cid, c in CLUES.items():
                    if m.harmless and su.label == c.target:
                        combos.append((sid, mid, suid, cid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_curated()]
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
