#!/usr/bin/env python3
"""
storyworlds/worlds/conclusion_rhyme_comedy.py
=============================================

A small storyworld about a comic little show whose ending must rhyme.

Seed premise:
- A child is making a funny performance.
- The last line, the conclusion, goes missing or goes wrong.
- A helper suggests a playful fix.
- The story ends with a cheerful, rhyming conclusion.

The world is intentionally narrow: it models one tiny domain with a few
plausible variants, all centered on a comedy performance that needs a rhyme
to land the ending.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_stage: bool = True


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    mess: str
    tension: str
    keyword: str
    punchline: str
    rhyme_hint: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    slot: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    action: str
    effect: str
    rhyme_tail: str


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    act: str
    prize: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "stage": Setting(place="the little stage", afford_stage=True),
    "classroom": Setting(place="the classroom corner stage", afford_stage=True),
    "livingroom": Setting(place="the living room stage", afford_stage=True),
}

ACTS = {
    "clown": Act(
        id="clown",
        verb="do a clown bit",
        gerund="doing a clown bit",
        mess="silly",
        tension="the joke fell flat",
        keyword="clown",
        punchline="the banana slipped and made everyone giggle",
        rhyme_hint="frown / clown",
    ),
    "tap": Act(
        id="tap",
        verb="tap-dance around",
        gerund="tap-dancing around",
        mess="tippy",
        tension="the shoes went thunk instead of clack",
        keyword="tap",
        punchline="the tiny steps sounded like happy raindrops",
        rhyme_hint="hop / bop",
    ),
    "poem": Act(
        id="poem",
        verb="say a funny poem",
        gerund="saying a funny poem",
        mess="wordy",
        tension="the last line got stuck",
        keyword="poem",
        punchline="the room waited for a finish that rhymed",
        rhyme_hint="glow / show",
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a bright red hat", type="hat", slot="head"),
    "shirt": Prize(label="shirt", phrase="a clean yellow shirt", type="shirt", slot="torso"),
    "shoes": Prize(label="shoes", phrase="shiny blue shoes", type="shoes", slot="feet", plural=True),
}

FIXES = {
    "bell": Fix(id="bell", label="a tiny bell", action="ring the tiny bell", effect="the ending got a cheerful ding", rhyme_tail="ding / sing"),
    "pie": Fix(id="pie", label="a foam pie", action="hold up the foam pie", effect="the final joke landed with a splat", rhyme_tail="pie / sky"),
    "card": Fix(id="card", label="a rhyme card", action="flip the rhyme card", effect="the last line finally clicked", rhyme_tail="light / bright"),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Ben", "Theo", "Sam", "Noah"]
TRAITS = ["cheerful", "goofy", "curious", "bouncy", "bright"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_spill(world: World):
    out = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("comedy", 0.0) < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id}'s act got a little messy.")
    return out


def _r_laughter(world: World):
    out = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        sig = ("laugh", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["laugh"] = actor.memes.get("laugh", 0.0) + 1
        out.append(f"The mess turned into a laugh.")
    return out


RULES = [Rule("spill", _r_spill), Rule("laugh", _r_laughter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_fix(act: Act, prize: Prize, fix: Fix) -> bool:
    if act.id == "clown":
        return fix.id in {"pie", "card"}
    if act.id == "tap":
        return fix.id in {"bell", "card"}
    if act.id == "poem":
        return fix.id in {"card", "bell"}
    return False


def select_fix(act: Act, prize: Prize) -> Optional[Fix]:
    for fix in FIXES.values():
        if can_fix(act, prize, fix):
            return fix
    return None


def forward_mess(world: World, actor: Entity, act: Act) -> dict:
    sim = world.copy()
    do_act(sim, sim.get(actor.id), act, narrate=False)
    return {
        "mess": sim.get(actor.id).meters.get("mess", 0.0) >= THRESHOLD,
        "laugh": sim.get(actor.id).memes.get("laugh", 0.0) >= THRESHOLD,
    }


def act_setup(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.type} who loved a good joke and a happy ending.")


def introduce_show(world: World, hero: Entity, act: Act) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.id} wanted to {act.verb}, because {act.gerund} made the room feel warm and bright.")


def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(f"{hero.id}'s helper brought out {prize.phrase}, and {hero.id} wore {prize.it()} like it belonged in the spotlight.")


def arrive(world: World, hero: Entity, helper: Entity, setting: Setting, act: Act) -> None:
    world.say(f"At {setting.place}, {hero.id} and {helper.id} stepped onto the little stage.")
    world.say(f"The crowd waited for a clean start, but {act.tension} was already peeking around the corner.")


def start_act(world: World, hero: Entity, act: Act) -> None:
    hero.meters["comedy"] = hero.meters.get("comedy", 0.0) + 1
    world.say(f"{hero.id} began to {act.verb}, and the first bit was {act.punchline}.")


def worry(world: World, helper: Entity, hero: Entity, prize: Entity, act: Act) -> bool:
    pred = forward_mess(world, hero, act)
    if not pred["mess"]:
        return False
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    world.facts["predicted_mess"] = True
    world.say(f'"That last line may wobble," {helper.id} said. "We need a conclusion that rhymes, not a flop in disguise."')
    return True


def stumble(world: World, hero: Entity, act: Act) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} heard that, paused, and tried to keep going anyway.")
    world.say(f"But then {act.tension}.")


def do_act(world: World, actor: Entity, act: Act, narrate: bool = True) -> None:
    actor.meters["comedy"] = actor.meters.get("comedy", 0.0) + 1
    actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1
    propagate(world, narrate=narrate)


def fix_end(world: World, helper: Entity, hero: Entity, act: Act, prize: Entity) -> Optional[Fix]:
    fix = select_fix(act, prize)
    if fix is None:
        return None
    world.facts["fix"] = fix
    world.say(f"Then {helper.id} held up {fix.label} and whispered, \"Try this for the end.\"")
    world.say(f"{hero.id} nodded and took a breath, ready to {fix.action}.")
    return fix


def finish(world: World, hero: Entity, helper: Entity, act: Act, prize: Entity, fix: Fix) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"The ending clicked into place: {fix.effect}. "
        f"{hero.id} gave the last line with a grin, and it landed like a feather in the sun."
    )
    world.say(
        f"At the conclusion, {hero.id} and {helper.id} bowed together. "
        f"{hero.id}'s {prize.label} stayed tidy, and the whole room laughed on the rhyme: {act.rhyme_hint}."
    )


def tell(setting: Setting, act: Act, prize_cfg: Prize, fix_cfg: Fix,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    act_setup(world, hero)
    introduce_show(world, hero, act)
    prize_line(world, hero, prize)
    world.para()
    arrive(world, hero, helper, setting, act)
    start_act(world, hero, act)
    worry(world, helper, hero, prize, act)
    stumble(world, hero, act)
    world.para()
    fix = fix_end(world, helper, hero, act, prize)
    if fix:
        finish(world, hero, helper, act, prize, fix)
    world.facts.update(hero=hero, helper=helper, prize=prize, act=act, fix=fix, setting=setting, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["act"]
    prize = f["prize"]
    return [
        f'Write a short comedy story for a small child about {hero.id} trying to {act.verb} and needing a rhyming conclusion.',
        f"Tell a funny story where {hero.id} worries about {prize.phrase} during a stage act, then finds a cheerful fix.",
        f'Write a playful story that ends with a rhyme and the word "conclusion".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["act"]
    fix = f.get("fix")
    qa = [
        QAItem(
            question=f"What kind of story was this about {hero.id}?",
            answer=f"It was a funny, cheerful story about {hero.id} trying to {act.verb} with help from {helper.id}.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry during the show?",
            answer=f"{helper.id} worried because the ending might not land well, and {act.tension} would spoil the joke.",
        ),
        QAItem(
            question=f"What did {hero.id} wear on stage?",
            answer=f"{hero.id} wore {prize.phrase}, so the performance looked bright and ready for the spotlight.",
        ),
    ]
    if fix:
        qa.append(QAItem(
            question=f"How did {fix.label} help at the end?",
            answer=f"{fix.label.capitalize()} helped by giving the show a better finish, so {hero.id} could end with a rhyme instead of a flop.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with a clean conclusion, a rhyming last line, and everyone laughing together.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when the end sounds of words match, like cat and hat.",
        )
    ],
    "conclusion": [
        QAItem(
            question="What is a conclusion?",
            answer="A conclusion is the ending part of a story or show, where things finish up.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes comedy funny?",
            answer="Comedy is funny because it uses silliness, surprises, and playful mistakes that are safe to laugh at.",
        )
    ],
    "stage": [
        QAItem(
            question="What is a stage for?",
            answer="A stage is a small platform or space where people perform for others to watch.",
        )
    ],
    "bell": [
        QAItem(
            question="What does a bell sound like?",
            answer="A bell makes a clear dinging sound when it is rung.",
        )
    ],
    "pie": [
        QAItem(
            question="Why is a foam pie funny on stage?",
            answer="A foam pie is funny because it looks like a silly pie splash, but it is soft and safe.",
        )
    ],
    "card": [
        QAItem(
            question="What is a card used for?",
            answer="A card can hold a word, a picture, or a reminder that helps someone remember what to say.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"rhyme", "conclusion", "comedy", "stage"}
    fix = world.facts.get("fix")
    if fix:
        tags.add(fix.id)
    out: list[QAItem] = []
    for tag in ["rhyme", "conclusion", "comedy", "stage", "bell", "pie", "card"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="stage", act="clown", prize="hat", fix="pie", name="Mia", gender="girl", helper="mother", trait="goofy"),
    StoryParams(place="classroom", act="poem", prize="shirt", fix="card", name="Leo", gender="boy", helper="teacher", trait="bright"),
    StoryParams(place="livingroom", act="tap", prize="shoes", fix="bell", name="Nora", gender="girl", helper="father", trait="bouncy"),
]


ASP_RULES = r"""
% A performance is at risk when its act naturally creates a messy or unstable ending.
at_risk(A) :- act(A).
% A fix is compatible when it is a valid match for the act.
good_fix(A, F) :- act(A), fix(F), compatible(A, F).
valid_story(S, A, F) :- setting(S), act(A), fix(F), good_fix(A, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTS:
        lines.append(asp.fact("act", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    for aid, act in ACTS.items():
        for fid, fix in FIXES.items():
            if can_fix(act, PRIZES["hat"], fix):
                lines.append(asp.fact("compatible", aid, fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_fix/2."))
    return sorted(set(asp.atoms(model, "good_fix")))


def asp_verify() -> int:
    py = set()
    for a in ACTS:
        for f in FIXES:
            if can_fix(ACTS[a], PRIZES["hat"], FIXES[f]):
                py.add((a, f))
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a rhyming conclusion.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
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
    combos = []
    for place in SETTINGS:
        for act in ACTS:
            for prize in PRIZES:
                for fix in FIXES:
                    if can_fix(ACTS[act], PRIZES[prize], FIXES[fix]):
                        combos.append((place, act, prize, fix))
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.act is None or c[1] == args.act)
              and (args.prize is None or c[2] == args.prize)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, act, prize, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "teacher"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, act=act, prize=prize, fix=fix, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTS[params.act],
        PRIZES[params.prize],
        FIXES[params.fix],
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combos:")
        for t in stories:
            print(" ", t)
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
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.act} at {p.place} (prize: {p.prize}, fix: {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
