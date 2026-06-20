#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/acquiesce_church_happy_ending_adventure.py
===========================================================================

A small storyworld for an adventure-flavored, happy-ending tale about two kids
on the way to church, where one child wants to take a daring shortcut, the other
warns them, and the story turns when they acquiesce and choose the safer path.

The domain is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- state-driven narrative beats
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in the simulated world
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

NAMES = ["Mia", "Nora", "Eli", "Theo", "Ava", "Ben", "Luna", "Finn"]
TRAILS = ["stone path", "narrow lane", "grassy hill", "old steps"]
ARTICLES = ["map", "lantern", "snack", "songbook"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    danger: str
    blocked_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class PathChoice:
    id: str
    label: str
    sense: int
    safety: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    adult: str
    adult_gender: str
    risk: str
    choice: str
    seed: Optional[int] = None


SETTINGS = {
    "path": Setting("path", "the church path", "The church bell rang in the distance, and the path curved past a little creek.", {"creek", "shortcut"}),
    "hill": Setting("hill", "the hill road", "The road climbed past wild grass and a low stone wall.", {"shortcut"}),
}

RISKS = {
    "creek": Risk("creek", "creek", "the creek", "the water below", blocked_by={"shortcut"}, tags={"water"}),
    "gate": Risk("gate", "gate", "the iron gate", "the locked gate", blocked_by=set(), tags={"gate"}),
}

CHOICES = {
    "shortcut": PathChoice("shortcut", "take the shortcut", 3, 3,
                           "picked the safe path back to the church steps and crossed the little bridge instead",
                           "ran toward the shortcut anyway, but it led to trouble",
                           "took the safe path back to the church steps",
                           tags={"shortcut"}),
    "wait": PathChoice("wait", "wait and ask for help", 3, 3,
                       "stopped to ask the older helper and then followed the wide path to church",
                       "kept hurrying and nearly slipped",
                       "asked for help and chose the wide path",
                       tags={"help"}),
    "turn_back": PathChoice("turn_back", "turn back", 2, 2,
                            "turned back, found the proper road, and arrived smiling at church",
                            "kept going and got lost for a while",
                            "turned back and found the proper road",
                            tags={"turn"}),
}

ASP_RULES = r"""
risk(setting(path), creek) :- afford(path, creek).
valid_choice(choice(shortcut)) :- choice(shortcut), sense(shortcut, S), sense_min(M), S >= M.
valid_story(S, C, R) :- setting(S), choice(C), risk(S, R).
outcome(acquiesced) :- guide_wins, choice(shortcut).
outcome(happy) :- not guide_wins.
"""

CAUTIOUS_TRAITS = {"careful", "cautious", "sensible"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid in setting.afford:
            for cid in CHOICES:
                if hazard_at_risk(setting, RISKS[rid], CHOICES[cid]):
                    combos.append((sid, rid, cid))
    return combos


def hazard_at_risk(setting: Setting, risk: Risk, choice: PathChoice) -> bool:
    return (risk.id in setting.afford) and ("shortcut" in choice.tags or choice.id == "wait" or choice.id == "turn_back")


def sensible_choices() -> list[PathChoice]:
    return [c for c in CHOICES.values() if c.sense >= SENSE_MIN]


def reason_gate(choice: PathChoice) -> bool:
    return choice.sense >= SENSE_MIN


def _rule_fear(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["worry"] >= THRESHOLD and ("fear" not in e.attrs):
            e.memes["fear"] += 1
            e.attrs["fear"] = True
            out.append("__fear__")
    return out


CAUSAL_RULES = [type("Rule", (), {"name": "fear", "apply": _rule_fear})]


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


def predict(world: World, risk: Risk, choice: PathChoice) -> dict:
    sim = world.copy()
    _make_choice(sim, sim.get("hero"), sim.get("guide"), risk, choice, narrate=False)
    return {
        "safe": sim.facts.get("safe", False),
        "late": sim.facts.get("late", False),
    }


def _make_choice(world: World, hero: Entity, guide: Entity, risk: Risk, choice: PathChoice, narrate: bool = True) -> None:
    if choice.id == "shortcut":
        hero.memes["daring"] += 1
        guide.memes["worry"] += 1
        world.say(f'{hero.id} leaned toward the {risk.phrase} and said, "Let us take the shortcut!"')
        world.say(f'{guide.id} looked at {risk.danger} and whispered, "That road is not safe."')
        if "acquiesce" in world.facts:
            world.say(f'{hero.id} paused, listened, and chose to acquiesce.')
            world.facts["safe"] = True
        else:
            world.say(f'{hero.id} did not listen, and the shortcut became a small problem.')
            world.facts["safe"] = False
    elif choice.id == "wait":
        world.say(f'{guide.id} pointed to the wider road and said they should wait for help.')
        world.say(f'{hero.id} agreed at once, and the adventure stayed calm.')
        world.facts["safe"] = True
    else:
        world.say(f'{hero.id} turned back with {guide.id} and found the proper road again.')
        world.facts["safe"] = True
    propagate(world, narrate=narrate)


def tell(setting: Setting, risk: Risk, choice: PathChoice,
         hero_name: str = "Mia", hero_gender: str = "girl",
         guide_name: str = "Nora", guide_gender: str = "girl",
         adult_name: str = "Father", adult_gender: str = "man",
         acquiesced: bool = True) -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    guide = world.add(Entity(guide_name, kind="character", type=guide_gender, role="guide"))
    adult = world.add(Entity(adult_name, kind="character", type=adult_gender, role="adult", label="the adult"))
    world.facts.update(acquiesce=acquiesced)
    world.say(f"On a bright morning, {hero.id} and {guide.id} set out for church along {setting.place}.")
    world.say(setting.detail)
    world.say(f'{hero.id} wanted the bold way, but {guide.id} warned about {risk.danger}.')
    world.para()
    _make_choice(world, hero, guide, risk, choice)
    world.para()
    if world.facts.get("safe"):
        world.say(f"{adult.label_word.capitalize()} found them at the church gate and smiled.")
        world.say(f'They went inside, sang softly, and the bells rang like a happy answer.')
        world.say(f'By the end, {hero.id} had acquiesced, and the whole adventure ended safely at church.')
    else:
        world.say(f"{adult.label_word.capitalize()} arrived in time to lead them back, and the day still ended safely.")
        world.say(f'They reached church together, wiser and glad for the warning.')
    world.facts.update(hero=hero, guide=guide, adult=adult, risk=risk, choice=choice, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write an adventure story for a young child that includes the words "acquiesce" and "church" and ends happily.',
        f"Tell a gentle adventure where {f['hero'].id} and {f['guide'].id} are trying to get to church, then choose the safer path after a warning.",
        "Write a short story about a child who wants a daring shortcut, but listens, acquiesces, and reaches church safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    adult = f["adult"]
    risk = f["risk"]
    choice = f["choice"]
    out = [
        QAItem(
            question="What was the adventure about?",
            answer=f"It was about {hero.id} and {guide.id} trying to reach church. The path felt adventurous, but they had to decide whether to take a risky shortcut.",
        ),
        QAItem(
            question=f"Why did {guide.id} warn {hero.id}?",
            answer=f"{guide.id} warned {hero.id} because the shortcut led near {risk.danger}. That made the trip exciting, but also unsafe if they rushed ahead.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with everyone reaching church safely. {hero.id} listened, the danger was avoided, and the bells made the ending feel bright.",
        ),
    ]
    if world.facts.get("acquiesce"):
        out.append(QAItem(
            question=f"What did {hero.id} do after {guide.id} warned {hero.id}?",
            answer=f"{hero.id} acquiesced and chose the safer way instead of pushing ahead. That kept the adventure calm and led them right to church.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is church?",
            answer="A church is a place where people may gather to pray, sing, and be quiet together. In this story, it is the place the children are trying to reach.",
        ),
        QAItem(
            question="What does acquiesce mean?",
            answer="To acquiesce means to agree to something, usually after thinking about it. Here it means the child listens and chooses the safer path.",
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("path", "Mia", "girl", "Nora", "girl", "Father", "man", "creek", "shortcut"),
    StoryParams("hill", "Eli", "boy", "Ava", "girl", "Mother", "woman", "gate", "turn_back"),
]


def explain_rejection(choice: PathChoice) -> str:
    return f"(No story: {choice.label} does not make a strong enough, sensible adventure turn.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos() vs ASP.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print("MISMATCH: generate smoke test failed:", e)
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: acquiesce, church, happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["Mother", "Father"])
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--choice", choices=CHOICES)
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
    if args.choice and not reason_gate(CHOICES[args.choice]):
        raise StoryError(explain_rejection(CHOICES[args.choice]))
    choices = [c for c in CHOICES if args.choice is None or c == args.choice]
    if not choices:
        raise StoryError("(No valid choice matches the given options.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    risk = args.risk or rng.choice(list(SETTINGS[setting].afford))
    choice = args.choice or rng.choice(choices)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES)
    guide = args.guide or rng.choice([n for n in NAMES if n != hero])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult = args.adult or ("Mother" if adult_gender == "woman" else "Father")
    return StoryParams(setting, hero, hero_gender, guide, guide_gender, adult, adult_gender, risk, choice)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RISKS[params.risk], CHOICES[params.choice],
                 params.hero, params.hero_gender, params.guide, params.guide_gender,
                 params.adult, params.adult_gender, acquiesced=True)
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
        print(asp_program(show="#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for item in combos:
            print("  ", item)
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
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.hero} and {p.guide}: {p.setting} -> {p.choice}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
