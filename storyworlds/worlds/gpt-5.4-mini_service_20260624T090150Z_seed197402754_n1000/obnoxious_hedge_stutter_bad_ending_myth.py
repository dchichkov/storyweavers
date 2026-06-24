#!/usr/bin/env python3
"""
A small mythic storyworld about a proud speaker, a living hedge, and a tale
that ends badly because boastfulness and hesitation invite trouble.

Seed tale:
A small village kept a sacred hedge around a spring. A young herald wanted to
prove himself clever, but he was obnoxious and always interrupted others. When
the hedge began whispering warnings, he mocked it, then stuttered in fear as he
tried to undo the damage. The spring was lost to the dark, and the village had
to remember the lesson.

This world generates close variants around that premise: a boastful child or
young speaker, a hedge with a voice or a gate, a warning ignored, a confused
stutter, and a bad ending that proves something was lost.
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

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "goddess", "priestess"}
        male = {"boy", "king", "god", "priest", "herald", "shepherd", "hunter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    sacred: bool = False
    has_hedge: bool = True
    has_spring: bool = True
    mood: str = "quiet"


@dataclass
class HeroCfg:
    type: str
    name: str
    trait: str


@dataclass
class Relic:
    label: str
    phrase: str
    vulnerable: bool = True


@dataclass
class Threat:
    label: str
    verb: str
    effect: str
    ruin: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    setting: str
    hero: str
    relic: str
    threat: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "spring_hill": Setting(place="Spring Hill", sacred=True, has_hedge=True, has_spring=True, mood="still"),
    "old_gate": Setting(place="the Old Gate", sacred=False, has_hedge=True, has_spring=False, mood="windy"),
    "green_courtyard": Setting(place="the green courtyard", sacred=True, has_hedge=True, has_spring=True, mood="bright"),
}

HEROES = {
    "herald": HeroCfg(type="herald", name="Aren", trait="obnoxious"),
    "boy": HeroCfg(type="boy", name="Milo", trait="proud"),
    "girl": HeroCfg(type="girl", name="Lena", trait="bold"),
}

RELICS = {
    "spring": Relic(label="spring", phrase="the clear spring"),
    "lamp": Relic(label="lamp", phrase="the lantern of dawn"),
    "crown": Relic(label="crown", phrase="the ash crown"),
}

THREATS = {
    "wolf": Threat(label="wolf", verb="slip through", effect="darkness", ruin="it would drink the water"),
    "fire": Threat(label="fire", verb="crawl through", effect="smoke", ruin="it would burn the leaves"),
    "thorn": Threat(label="thorns", verb="spread through", effect="pain", ruin="they would choke the path"),
}

GIRL_NAMES = ["Lena", "Ira", "Nora", "Mira"]
BOY_NAMES = ["Aren", "Milo", "Tav", "Corin"]
TRAITS = ["obnoxious", "proud", "quick-tongued", "bossy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting has a hedge and the hero's flaw can
% trigger the bad ending: the warning is mocked, the hedge is damaged, and the
% relic is lost.
valid_story(S,H,R,T) :- setting(S), hero(H), relic(R), threat(T),
                        has_hedge(S), vulnerable(R), bad_end(T).

bad_end(T) :- threat(T), ruins(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.sacred:
            lines.append(asp.fact("sacred", sid))
        if s.has_hedge:
            lines.append(asp.fact("has_hedge", sid))
        if s.has_spring:
            lines.append(asp.fact("has_spring", sid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("flaw", hid, h.trait))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.vulnerable:
            lines.append(asp.fact("vulnerable", rid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("ruins", tid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hero_cfg = HEROES[params.hero]
    relic_cfg = RELICS[params.relic]
    threat_cfg = THREATS[params.threat]
    world = World(setting)

    hero = world.add(Entity(id=hero_cfg.name, kind="character", type=hero_cfg.type, label=hero_cfg.name))
    hedge = world.add(Entity(id="hedge", type="hedge", label="the hedge", protected=True))
    relic = world.add(Entity(id="relic", type=relic_cfg.label, label=relic_cfg.label, phrase=relic_cfg.phrase, owner=hero.id))
    threat = world.add(Entity(id=threat_cfg.label, type=threat_cfg.label, label=threat_cfg.label))

    hero.memes["obnoxious"] = 1.0
    hero.memes["pride"] = 1.0
    hedge.meters["alive"] = 1.0
    hedge.memes["wisdom"] = 1.0
    relic.meters["sacred"] = 1.0

    # Act 1
    world.say(f"Long ago, at {setting.place}, there stood {hedge.label} guarding {relic.phrase}.")
    world.say(f"{hero.id} was a little {hero_cfg.trait} {hero_cfg.type} who loved to speak first and listen last.")
    world.say(f"The people said {hero.id} had a sharp tongue and an even sharper boast.")

    # Act 2
    world.para()
    world.say(f"One day the air went thin and the {hedge.label} began to whisper, '{relic_cfg.phrase} must stay closed.'")
    world.say(f"{hero.id} rolled {hero.pronoun('possessive')} eyes and said the hedge was only leaves and old stories.")
    world.say(f"{hero.id} tried to {threat_cfg.verb} the warning, but {hero.pronoun('subject')} only made matters worse.")
    hero.memes["mockery"] = 1.0
    hedge.meters["torn"] = 1.0
    world.say(f"The hedge shivered, and one bright branch broke from the wall like a snapped promise.")

    # Act 3 bad ending
    world.para()
    hero.memes["fear"] = 1.0
    hero.memes["stutter"] = 1.0
    relic.meters["lost"] = 1.0
    relic.meters["safe"] = 0.0
    world.say(f"Then {hero.id} began to stutter: 'I-I d-did not mean—' but the words could not mend the breach.")
    world.say(f"Through the gap came the {threat_cfg.label}, and at once {threat_cfg.ruin}.")
    world.say(f"By dawn the spring was gone, the hedge was torn, and {hero.id} had to bow {hero.pronoun('possessive')} head in shame.")
    world.say("That was the bad ending of the story, and nobody there forgot it.")

    world.facts.update(
        hero=hero,
        hedge=hedge,
        relic=relic,
        threat=threat,
        setting=setting,
        hero_cfg=hero_cfg,
        relic_cfg=relic_cfg,
        threat_cfg=threat_cfg,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic_cfg = f["relic_cfg"]
    return [
        f"Write a short myth about {hero.id}, a {f['hero_cfg'].trait} {hero.type}, who offends a sacred hedge and loses {relic_cfg.phrase}.",
        f"Tell a child-facing myth where an {f['hero_cfg'].trait} speaker stutters after mocking a warning at {f['setting'].place}.",
        f"Write a bad-ending legend about a hedge, a warning, and a lost {relic_cfg.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    relic_cfg = f["relic_cfg"]
    threat_cfg = f["threat_cfg"]
    qa = [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id}, a little {f['hero_cfg'].trait} {hero.type} who spoke in an obnoxious way.",
        ),
        QAItem(
            question=f"What was the hedge guarding?",
            answer=f"The hedge was guarding {relic_cfg.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} get into trouble?",
            answer=f"{hero.id} got into trouble because {hero.pronoun('subject')} mocked the hedge's warning instead of listening.",
        ),
        QAItem(
            question=f"What happened when the danger came through?",
            answer=f"The {threat_cfg.label} came through the broken hedge, and the spring was lost in the bad ending.",
        ),
    ]
    if f.get("bad_ending"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} speak near the end?",
                answer=f"{hero.id} stuttered and could not fix the damage, which showed fear and regret.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hedge?",
            answer="A hedge is a thick row of plants or bushes that can make a wall around a place.",
        ),
        QAItem(
            question="What does it mean to stutter?",
            answer="To stutter means to repeat sounds or words because speaking feels hard or nervous.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things go wrong and the hero does not get a happy finish.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protected:
            bits.append("protected=True")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="spring_hill", hero="herald", relic="spring", threat="wolf"),
    StoryParams(setting="green_courtyard", hero="boy", relic="lamp", threat="fire"),
    StoryParams(setting="old_gate", hero="girl", relic="crown", threat="thorn"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with an obnoxious voice, a hedge, stutter, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--threat", choices=THREATS)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    relic = args.relic or rng.choice(list(RELICS))
    threat = args.threat or rng.choice(list(THREATS))
    return StoryParams(setting=setting, hero=hero, relic=relic, threat=threat)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP verification helpers
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(
        (s, h, r, t)
        for s in SETTINGS
        for h in HEROES
        for r in RELICS
        for t in THREATS
        if SETTINGS[s].has_hedge and RELICS[r].vulnerable
    )
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
