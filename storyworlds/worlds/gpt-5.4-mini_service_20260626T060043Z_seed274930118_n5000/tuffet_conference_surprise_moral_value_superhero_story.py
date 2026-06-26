#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tuffet_conference_surprise_moral_value_superhero_story.py
===============================================================================================================================

A compact superhero-style story world about a small hero, a conference, a
tuffet, a surprise, and a moral-value choice that changes the ending image.

Premise:
- A young hero is invited to a conference in a bright hall.
- The hero sits on a tuffet near the stage and wants to impress everyone.
- A surprise occurs: a fallen sign, a spilled box of ribbons, or a nervous
  helper in trouble.
- The hero must choose between showing off and doing the morally right thing.
- The ending proves the choice by showing who feels safer, happier, or braver.

This file follows the storyworld contract:
- typed entities with meters and memes
- state-driven prose
- explicit invalid choices raise StoryError
- inline ASP twin plus Python reasonableness gate
- generate/emit/CLI support with QA and trace
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
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hall:
    name: str = "the conference hall"
    has_stage: bool = True
    has_tuffet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    surprise: str
    moral_choice: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    wears_on: str
    gender_ok: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.ground_truth: dict[str, bool] = {}

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
        clone = World(self.hall)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.ground_truth = dict(self.ground_truth)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _bump_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = _meter(e, key) + amt


def _bump_mem(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = _mem(e, key) + amt


def _set_mem(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


def _rule_notice(world: World, text: str) -> None:
    world.say(text)


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if _mem(hero, "anticipation") < THRESHOLD:
            continue
        if _mem(hero, "surprise_seen") >= THRESHOLD:
            continue
        if not world.ground_truth.get("surprise_ready", False):
            continue
        sig = ("surprise", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _bump_mem(hero, "surprise_seen", 1.0)
        _bump_mem(hero, "shock", 1.0)
        out.append("A surprise popped up.")
    return out


def _r_moral_value(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if _mem(hero, "choice") < THRESHOLD:
            continue
        if _mem(hero, "moral_value") >= THRESHOLD:
            continue
        sig = ("moral", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.ground_truth.get("chose_help", False):
            _bump_mem(hero, "moral_value", 1.0)
            _bump_mem(hero, "pride", 1.0)
            out.append("The hero chose to help.")
        else:
            _bump_mem(hero, "guilt", 1.0)
            out.append("The hero chose the wrong thing.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for helper in world.characters():
        if _mem(helper, "helped") < THRESHOLD:
            continue
        if _mem(helper, "calm") >= THRESHOLD:
            continue
        sig = ("calm", helper.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _bump_mem(helper, "calm", 1.0)
        out.append("The room felt calmer.")
    return out


RULES = [
    ("surprise", _r_surprise),
    ("moral_value", _r_moral_value),
    ("calm", _r_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in RULES:
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            if line == "A surprise popped up.":
                continue
            if line == "The hero chose to help.":
                continue
            if line == "The hero chose the wrong thing.":
                continue
            if line == "The room felt calmer.":
                continue
            world.say(line)
    return out


HALLS = {
    "conference": Hall(name="the conference hall", has_stage=True, has_tuffet=True,
                       affords={"speech", "demonstration", "talk"}),
    "assembly": Hall(name="the assembly room", has_stage=True, has_tuffet=True,
                     affords={"speech", "demonstration"}),
}


ACTIONS = {
    "speech": Action(
        id="speech",
        verb="give a speech",
        gerund="giving a speech",
        rush="rush up to the microphone",
        surprise="a stack of paper stars slid off the table",
        moral_choice="help gather the stars",
        outcome="the audience cheered for the kind choice",
        tags={"surprise", "moral_value"},
    ),
    "demonstration": Action(
        id="demonstration",
        verb="show a hero trick",
        gerund="showing a hero trick",
        rush="leap onto the stage",
        surprise="a tiny helper dropped a ribbon bundle",
        moral_choice="help the helper first",
        outcome="the helper smiled and the trick waited a moment",
        tags={"surprise", "moral_value"},
    ),
    "talk": Action(
        id="talk",
        verb="speak to the crowd",
        gerund="speaking to the crowd",
        rush="step toward the bright lights",
        surprise="a poster banner came loose and fluttered down",
        moral_choice="hold the banner so nobody got hurt",
        outcome="the banner stayed safe and the crowd relaxed",
        tags={"surprise", "moral_value"},
    ),
}

PRIZES = {
    "cape": Prize(id="cape", label="cape", phrase="a red hero cape", type="cape", wears_on="back"),
    "mask": Prize(id="mask", label="mask", phrase="a shiny mask", type="mask", wears_on="face"),
    "badge": Prize(id="badge", label="badge", phrase="a bright badge", type="badge", wears_on="chest"),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Tess", "Ivy", "Ava"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Max", "Owen", "Eli"]
TRAITS = ["brave", "quick", "gentle", "clever", "spirited", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, hall in HALLS.items():
        for action in hall.affords:
            for prize_id, prize in PRIZES.items():
                if place == "conference" and action in ACTIONS:
                    combos.append((place, action, prize_id))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    return (
        f"(No story: the chosen hero item, {prize.label}, does not fit this "
        f"conference-style problem in a reasonable way for {action.verb}. Try a "
        f"badge, cape, or mask with a stage scene.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].gender_ok))
    return f"(No story: try --gender {ok}; this item does not fit {gender} here.)"


def build_story(world: World, hero: Entity, mentor: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} hero with a {hero.label if hero.label else 'bright smile'} "
        f"and a heart that wanted to do the right thing."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {action.gerund}, and {hero.pronoun('possessive')} "
        f"{mentor.label} had invited {hero.pronoun('object')} to the conference."
    )
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} and sat on a soft tuffet near the stage, "
        f"waiting to look bold."
    )

    world.para()
    world.say(
        f"At {world.hall.name}, {hero.id} wanted to {action.verb}, but then {action.surprise}"
    )
    world.ground_truth["surprise_ready"] = True
    _bump_mem(hero, "anticipation", 1.0)
    _bump_mem(hero, "choice", 1.0)
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} froze for a second, because the surprise was bigger than a neat pose."
    )
    world.say(
        f"Then {hero.pronoun()} chose to {action.moral_choice} instead of showing off."
    )
    world.ground_truth["chose_help"] = True
    _bump_mem(hero, "helped", 1.0)
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{hero.id} bent down, gathered the fallen pieces, and kept the little crowd safe."
    )
    world.say(
        f"After that, {action.outcome}, and {hero.id}'s {prize.label} stayed neat on the tuffet."
    )
    world.say(
        f"{mentor.label.capitalize()} smiled, because a true hero's power was not only strength; "
        f"it was the choice to help."
    )


def tell(hall: Hall, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str,
         mentor_label: str, hero_label: str = "hero", hero_traits: Optional[list[str]] = None) -> World:
    world = World(hall)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_label,
        meters={"balance": 1.0},
        memes={"anticipation": 0.0, "choice": 0.0, "helped": 0.0, "moral_value": 0.0},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type="mentor",
        label=mentor_label,
        meters={"patience": 1.0},
        memes={"pride": 0.0},
    ))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        worn_by=hero.id,
    ))
    build_story(world, hero, mentor, prize, action)
    world.facts.update(hero=hero, mentor=mentor, prize=prize, action=action, hall=hall)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    action: Action = f["action"]
    prize: Entity = f["prize"]
    return [
        f'Write a short superhero story for a young child that includes a tuffet and a conference.',
        f'Write a story where {hero.id} wants to {action.verb} but chooses a moral action after a surprise.',
        f'Write a gentle superhero story that ends with {hero.id} helping instead of showing off, while {prize.label} stays safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    prize: Entity = f["prize"]
    action: Action = f["action"]
    qa = [
        QAItem(
            question=f"Where was {hero.id} when the surprise happened?",
            answer=f"{hero.id} was at {world.hall.name}, sitting on a tuffet near the stage with {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before choosing the kind thing?",
            answer=f"{hero.id} wanted to {action.verb}, but then the surprise made helping more important.",
        ),
        QAItem(
            question=f"Who invited {hero.id} to the conference?",
            answer=f"{mentor.label.capitalize()} invited {hero.id}, and {hero.id} listened carefully.",
        ),
        QAItem(
            question=f"What moral choice did {hero.id} make?",
            answer=f"{hero.id} chose to {action.moral_choice}, which was the right thing to do.",
        ),
        QAItem(
            question=f"What happened to the audience after the choice?",
            answer=f"The room got calmer, because {hero.id} helped first and the surprise was handled safely.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a tuffet?",
            answer="A tuffet is a small soft seat, like a cushion or low stool, that a child can sit on.",
        ),
        QAItem(
            question="What is a conference?",
            answer="A conference is a meeting where people come together to listen, talk, and share ideas.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero tries to protect people, solve problems, and make brave helpful choices.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value means choosing what is kind, fair, and safe instead of choosing selfishness.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears suddenly and can change what happens next.",
        ),
    ]
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise(H) :- hero(H), ready_for_surprise(H).
moral_value(H) :- hero(H), chose_help(H).
calm_room :- hero(H), helped(H).
valid(P,A,R) :- place(P), action(A), prize(R), afforded(P,A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, hall in HALLS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(hall.affords):
            lines.append(asp.fact("afforded", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_reasonable_combo(place: str, action: str, prize: str) -> bool:
    return (place, action, prize) in valid_combos()


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def explain_combo_rejection(action: Action, prize: Prize) -> str:
    return (
        f"(No story: {action.verb} with {prize.label} does not fit this superhero conference "
        f"scene in a meaningful way. Try the conference, a surprise, and a moral choice.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize:
        act = ACTIONS[args.action]
        pr = PRIZES[args.prize]
        if not valid_reasonable_combo(args.place or "conference", args.action, args.prize):
            raise StoryError(explain_combo_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].gender_ok:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=name,
        gender=gender,
        mentor=args.mentor or rng.choice(["Coach", "Aunt", "Guide"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(HALLS[params.place], ACTIONS[params.action], PRIZES[params.prize],
                 params.name, params.gender, params.mentor, hero_label=params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world: tuffet, conference, surprise, moral value."
    )
    ap.add_argument("--place", choices=HALLS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mentor")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="conference", action="speech", prize="badge", name="Mia", gender="girl", mentor="Coach", trait="brave"),
    StoryParams(place="conference", action="demonstration", prize="cape", name="Leo", gender="boy", mentor="Aunt", trait="clever"),
    StoryParams(place="conference", action="talk", prize="mask", name="Nora", gender="girl", mentor="Guide", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for p, a, r in triples:
            print(f"  {p:10} {a:14} {r}")
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
