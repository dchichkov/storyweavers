#!/usr/bin/env python3
"""
storyworlds/worlds/stationary_semantic_breaking_transformation_teamwork_myth.py
===============================================================================

A small mythic storyworld about a stationary sacred thing, a semantic break in
its meaning, and a teamwork-driven transformation that makes the world feel new.

Seed-tale premise:
---
Long ago, a village kept a still stone gate at the edge of a hill shrine. The
gate did not move, but the words carved into it told the village when to open
the path to the spring below. One dusk, the carved words cracked and lost their
sense. The villagers could not read the gate's promise, so the spring stayed
hidden. A young pair of helpers listened to the old stories, worked together,
and transformed the broken thing into a safe bridge of light.

This script turns that premise into a deterministic little world with:
- typed entities with meters and memes,
- a clear mythic tension and resolution,
- a Python reasonableness gate,
- an inline ASP twin for parity checking,
- story-grounded Q&A and child-level world knowledge Q&A.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    stationed: bool = False
    broken: bool = False
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "priestess"}
        male = {"boy", "father", "man", "brother", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    shrine_name: str
    sky: str
    affordance: str


@dataclass
class Rite:
    id: str
    verb: str
    gerund: str
    risk: str
    break_kind: str
    transform: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    stationary: bool = True
    plural: bool = False


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    effect: str
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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


def _inc(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


def _meters(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _memes(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def reasonableness_gate(setting: Setting, rite: Rite, relic: Relic, remedy: Remedy) -> None:
    if not relic.stationary:
        raise StoryError("The relic must be stationary for this mythic tension to matter.")
    if rite.break_kind not in rite.tags:
        raise StoryError("The rite must carry its own break kind in the storyworld.")
    if remedy.effect != rite.transform:
        raise StoryError("The remedy must truly match the transformation the rite needs.")
    if setting.affordance != rite.id:
        raise StoryError("The setting does not afford this rite.")
    if "semantic" not in rite.tags and "breaking" not in rite.tags:
        raise StoryError("This world needs the semantic breaking seed words to appear in the rite.")


@dataclass
class Rule:
    name: str
    apply: callable


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for rite in world.facts.get("rite_active", []):
        hero = world.get(rite["hero"])
        relic = world.get(rite["relic"])
        if _memes(hero, "desire") < THRESHOLD:
            continue
        if relic.broken:
            continue
        sig = ("break", hero.id, relic.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        relic.broken = True
        _inc(relic.meters, "crack", 1)
        _inc(relic.memes, "meaning_loss", 1)
        _inc(hero.memes, "worry", 1)
        out.append(f"The carved words on the stone grew thin and lost their meaning.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = world.facts.get("crew", [])
    if len(crew) < 2:
        return out
    if not world.facts.get("need_help"):
        return out
    if world.facts.get("teamwork_done"):
        return out
    hero = world.get(crew[0])
    ally = world.get(crew[1])
    sig = ("teamwork", hero.id, ally.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc(hero.memes, "trust", 1)
    _inc(ally.memes, "trust", 1)
    _inc(hero.memes, "hope", 1)
    _inc(ally.memes, "hope", 1)
    world.facts["teamwork_done"] = True
    out.append("Two hands took the burden together, and the old fear became brave work.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("teamwork_done"):
        return out
    remedy = world.facts["remedy"]
    relic = world.get(world.facts["relic_id"])
    if relic.transformed:
        return out
    sig = ("transform", relic.id, remedy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    relic.transformed = True
    relic.broken = False
    relic.label = remedy.label
    _inc(relic.meters, "light", 1)
    _inc(relic.memes, "meaning", 2)
    out.append("What had been broken turned into a shining bridge for the village to cross.")
    return out


CAUSAL_RULES = [
    Rule("break", _r_break),
    Rule("teamwork", _r_teamwork),
    Rule("transform", _r_transform),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


SETTINGS = {
    "hill": Setting(place="the hill shrine", shrine_name="Sunstone Shrine", sky="amber", affordance="chant"),
    "grove": Setting(place="the grove altar", shrine_name="Oak Whisper Shrine", sky="green", affordance="listen"),
    "cave": Setting(place="the cave threshold", shrine_name="Moon Echo Shrine", sky="blue", affordance="sing"),
}

RITES = {
    "chant": Rite(
        id="chant",
        verb="chant to the stone",
        gerund="chanting to the stone",
        risk="the old words could crack",
        break_kind="breaking",
        transform="bridge",
        keyword="stationary",
        tags={"stationary", "semantic", "breaking"},
    ),
    "listen": Rite(
        id="listen",
        verb="listen for the hidden verse",
        gerund="listening for the hidden verse",
        risk="the hidden meanings could fail",
        break_kind="semantic",
        transform="path",
        keyword="semantic",
        tags={"stationary", "semantic", "breaking"},
    ),
    "sing": Rite(
        id="sing",
        verb="sing the old names",
        gerund="singing the old names",
        risk="the binding song could break",
        break_kind="breaking",
        transform="bridge",
        keyword="breaking",
        tags={"stationary", "semantic", "breaking"},
    ),
}

RELICS = {
    "stone_gate": Relic("stone_gate", "stone gate", "a still stone gate with carved runes", "hill"),
    "tablet": Relic("tablet", "stone tablet", "a solemn tablet of old words", "grove"),
    "arch": Relic("arch", "moon arch", "a moonlit arch that never moved", "cave"),
}

REMEDIES = {
    "bridge": Remedy("bridge", "bridge of light", "a bridge of light", "bridge", "lift", "rose across the gap"),
    "path": Remedy("path", "clear path", "a clear path", "path", "uncover", "opened before them"),
}

NAMES_GIRL = ["Mira", "Nia", "Aya", "Sela", "Iris"]
NAMES_BOY = ["Taro", "Kian", "Daren", "Lio", "Arin"]
NAMES_ALL = NAMES_GIRL + NAMES_BOY


@dataclass
class StoryParams:
    setting: str
    rite: str
    relic: str
    name: str
    companion: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for r_id, rite in RITES.items():
            for relic_id, relic in RELICS.items():
                remedy = REMEDIES[rite.transform]
                if s.place.split()[-1] == relic.region and rite.id == s.affordance:
                    try:
                        reasonableness_gate(s, rite, relic, remedy)
                    except StoryError:
                        continue
                    combos.append((s_id, r_id, relic_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with stationary semantic breaking and teamwork transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
              and (args.rite is None or c[1] == args.rite)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("No valid myth matches the given options.")
    setting, rite, relic = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES_ALL)
    companion = args.companion or rng.choice([n for n in NAMES_ALL if n != name])
    return StoryParams(setting=setting, rite=rite, relic=relic, name=name, companion=companion)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    rite = RITES[params.rite]
    relic_cfg = RELICS[params.relic]
    remedy = REMEDIES[rite.transform]
    reasonableness_gate(setting, rite, relic_cfg, remedy)

    w = World(setting)
    hero = w.add(Entity(id=params.name, kind="character", type="girl" if params.name in NAMES_GIRL else "boy"))
    ally = w.add(Entity(id=params.companion, kind="character", type="girl" if params.companion in NAMES_GIRL else "boy"))
    relic = w.add(Entity(id=relic_cfg.id, type="stone", label=relic_cfg.label, phrase=relic_cfg.phrase, stationed=True))
    bridge = w.add(Entity(id=remedy.id, type="wonder", label=remedy.label, phrase=remedy.phrase))

    hero.memes["desire"] = 1
    ally.memes["care"] = 1
    relic.meters["stillness"] = 2
    relic.memes["meaning"] = 2

    w.facts.update(hero=hero.id, ally=ally.id, relic_id=relic.id, remedy=remedy, crew=[hero.id, ally.id], need_help=True)
    w.facts["rite_active"] = [{"hero": hero.id, "relic": relic.id, "rite": rite.id}]

    w.say(f"Long ago, in {setting.place}, there stood {relic.phrase}.")
    w.say(f"It was so { 'stationary' } that even the wind seemed to bow around it.")
    w.say(f"The people trusted its old { 'semantic' } promise, but one dusk that promise began to fail.")
    w.para()
    w.say(f"{hero.id} came with {ally.id} to {rite.gerund}, because the shrine's silence felt like a question.")
    w.say(f"{hero.id} loved the old stories, yet {hero.pronoun('possessive')} heart feared {rite.risk}.")
    propagate(w)
    w.para()
    w.say(f"Then {hero.id} and {ally.id} chose teamwork over fear.")
    w.say(f"They held the stone together, spoke the old meaning aloud, and let the broken thing become new.")
    propagate(w)
    w.facts["relic_obj"] = relic
    w.facts["bridge_obj"] = bridge
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f'Write a short myth for children about a {p["relic_obj"].label} and the word "{p["rite"].keyword}".',
        f"Tell a story where {p['hero']} and {p['ally']} use teamwork to fix a stationary sacred thing.",
        "Write a gentle myth in which a broken meaning becomes a transformation instead of an ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    ally = world.facts["ally"]
    relic = world.facts["relic_obj"]
    rite = world.facts["rite"]
    answer_end = "They worked together, and the broken stone became a bridge of light."
    return [
        QAItem(
            question=f"Who went to the shrine to help with the {relic.label}?",
            answer=f"{hero} and {ally} went together. They were the ones who chose to help the shrine."
        ),
        QAItem(
            question=f"Why did the old stone become a problem in the story?",
            answer=f"The carved words lost their meaning, so the villagers could not trust the old promise anymore."
        ),
        QAItem(
            question=f"What did {hero} and {ally} do when the trouble began?",
            answer=f"They used teamwork. They stayed calm, spoke the old words, and helped the relic change safely."
        ),
        QAItem(
            question=f"What change happened by the end of the myth?",
            answer=answer_end
        ),
    ]


WORLD_KNOWLEDGE = {
    "stationary": [("What does stationary mean?", "Stationary means something stays in one place and does not move.")],
    "semantic": [("What does semantic mean?", "Semantic has to do with meaning and what words stand for.")],
    "breaking": [("What happens when something breaks?", "When something breaks, it cracks, splits, or stops working the way it should.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other and work together toward one goal.")],
    "transformation": [("What is a transformation?", "A transformation is a change where something becomes different, sometimes in a big and surprising way.")],
    "myth": [("What is a myth?", "A myth is an old story that explains a wonder, a rule, or a deep idea in a memorable way.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["rite"].tags)
    tags.update({"teamwork", "transformation", "myth"})
    out: list[QAItem] = []
    for tag in ["stationary", "semantic", "breaking", "teamwork", "transformation", "myth"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.stationed:
            bits.append("stationary=True")
        if e.broken:
            bits.append("broken=True")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A relic is in the valid myth when the rite fits the setting and the relic.
valid(S,R,Rel) :- setting(S), rite(R), relic(Rel), supports(S,R), stationary(Rel), semantic_breaking(R), needs_help(R,Rel).

% Teamwork is required when the relic is broken and two helpers are present.
needs_help(R,Rel) :- rite(R), relic(Rel), breaks_words(R), stationary(Rel).

% Transformation follows teamwork.
transformed(Rel,Rem) :- needs_help(R,Rel), remedy(Rem), transforms(R,Rem).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("supports", sid, s.affordance))
    for rid, rite in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("semantic_breaking", rid))
        lines.append(asp.fact("breaks_words", rid))
        lines.append(asp.fact("transforms", rid, rite.transform))
    for relid, rel in RELICS.items():
        lines.append(asp.fact("relic", relid))
        lines.append(asp.fact("stationary", relid))
    for remid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", remid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible myth combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("hill", "chant", "stone_gate", "Mira", "Taro"),
            StoryParams("grove", "listen", "tablet", "Nia", "Daren"),
            StoryParams("cave", "sing", "arch", "Aya", "Arin"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.rite} at {p.setting} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
