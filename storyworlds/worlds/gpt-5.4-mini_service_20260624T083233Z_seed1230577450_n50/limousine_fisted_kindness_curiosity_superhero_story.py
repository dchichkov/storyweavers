#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50/limousine_fisted_kindness_curiosity_superhero_story.py
==============================================================================================================================

A small superhero-style storyworld about a curious kid hero, a limousine, a
fisted problem, and a kindness-based rescue.

Seed tale sketch:
---
A curious little hero named Nova loved shiny city adventures. One afternoon,
Nova found a long black limousine idling by the museum while a grumpy villain
kept one hand fisted around a stolen badge. Nova did not want a fight. Nova
wanted to learn why the villain had taken it. With kindness and curiosity, Nova
opened the limousine door, offered a snack, and asked gentle questions. The
villain's tight fist softened, the badge was returned, and the city cheered.
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the museum plaza"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    tag: str
    keyword: str
    danger: str
    zone: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps_with: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _clamp(x: float) -> float:
    return max(0.0, x)


def predict(world: World, hero: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    simulate_turn(sim, hero.id, challenge, prize_id, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD,
        "fear": sum(e.memes.get("fear", 0.0) for e in sim.characters()),
    }


def simulate_turn(world: World, hero_id: str, challenge: Challenge, prize_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    prize = world.get(prize_id)
    hero.meters[challenge.tag] = hero.meters.get(challenge.tag, 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    if challenge.zone & {"hands", "torso"}:
        prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
    if narrate and prize.meters.get("dirty", 0.0) >= THRESHOLD:
        world.say(f"{hero.id}'s choice made {prize.label} dirty.")
    if narrate:
        world.say(f"{hero.id} kept going anyway, guided by curiosity.")


def safe_aid(challenge: Challenge, prize: Prize) -> Optional[Aid]:
    if challenge.id == "stuck_fist" and prize.region == "hand":
        return AID["soft_glove"]
    if challenge.id == "stuck_fist" and prize.region == "torso":
        return AID["kind_words"]
    return AID["kind_words"]


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl", mentor_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the mentor"))
    villain = world.add(Entity(id="Villain", kind="character", type="villain", label="the villain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=mentor.id, plural=prize_cfg.plural))

    world.say(
        f"{hero.id} was a little hero with a bright heart and a sharp mind. "
        f"{hero.pronoun('subject').capitalize()} loved curiosity, kindness, and city rescues."
    )
    world.say(
        f"One day, {hero.id} spotted a black limousine waiting near {world.setting.place} "
        f"while {villain.label} stood nearby with a fisted hand."
    )
    world.say(
        f"{hero.id}'s {prize.label} had been taken, and the city felt tense."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {challenge.verb}, but first {hero.pronoun('subject')} looked at "
        f"{villain.label} and wondered why the hand was so tight."
    )
    pred = predict(world, hero, challenge, prize.id)
    if pred["soiled"]:
        world.say(
            f'{mentor.label} said, "Be careful, {hero.id}. The {prize.label} could get ruined if this gets rough."'
        )
    world.say(
        f"{hero.id} climbed into the limousine, because it was a quiet place to think and ask gentle questions."
    )

    world.para()
    simulate_turn(world, hero.id, challenge, prize.id, narrate=True)
    if challenge.id == "stuck_fist":
        world.say(
            f"{hero.id} offered a snack and asked, \"What is making your hand stay fisted?\""
        )
        world.say(
            f"The villain blinked, then slowly opened {villain.pronoun('possessive')} hand."
        )
    aid = safe_aid(challenge, prize_cfg)
    if aid:
        world.say(
            f"{hero.id}'s {mentor.label} smiled and helped with {aid.prep}."
        )

    world.para()
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    villain.memes["softened"] = villain.memes.get("softened", 0.0) + 1
    prize.meters["dirty"] = _clamp(prize.meters.get("dirty", 0.0) - 1)
    world.say(
        f"The villain gave back {prize.it()} and said the tight fist was from worry, not anger."
    )
    world.say(
        f"{hero.id} smiled, because kindness had worked better than a punch."
    )
    world.say(
        f"By sunset, the limousine rolled away, the city felt safe again, and {prize.label} was back with {hero.id}."
    )

    world.facts.update(hero=hero, mentor=mentor, villain=villain, prize=prize,
                       challenge=challenge, setting=setting, aid=aid, predicted=pred)
    return world


SETTINGS = {
    "plaza": Setting(place="the museum plaza", affords={"stuck_fist"}),
    "roof": Setting(place="the city roof", affords={"stuck_fist"}),
    "alley": Setting(place="the lantern alley", affords={"stuck_fist"}),
}

CHALLENGES = {
    "stuck_fist": Challenge(
        id="stuck_fist",
        verb="ask why the hand was fisted",
        gerund="asking gentle questions",
        rush="run up in a hurry",
        tag="pressure",
        keyword="fisted",
        danger="a tense grab",
        zone={"hands"},
    ),
}

PRIZES = {
    "badge": Prize(
        label="badge",
        phrase="a shiny hero badge",
        type="badge",
        region="hand",
    ),
    "star": Prize(
        label="star",
        phrase="a bright golden star token",
        type="star",
        region="hand",
    ),
}

AID = {
    "kind_words": Aid(
        id="kind_words",
        label="kind words",
        prep="a few kind words and a calm smile",
        tail="spoke kindly until the air felt lighter",
        helps_with={"stuck_fist"},
        covers={"hands"},
    ),
    "soft_glove": Aid(
        id="soft_glove",
        label="soft gloves",
        prep="soft gloves so nobody got poked",
        tail="used the soft gloves to help open the hand",
        helps_with={"stuck_fist"},
        covers={"hands"},
    ),
}

HERO_NAMES = ["Nova", "Mira", "Jax", "Piper", "Aria", "Leo"]
VILLAIN_TITLES = ["villain"]
TRAITS = ["kind", "curious", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p, s in SETTINGS.items() for c in s.affords]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: curiosity, kindness, and a limousine.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.challenge:
        combos = [c for c in combos if c[1] == args.challenge]
    if args.prize:
        combos = [c for c in combos if args.prize in PRIZES]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge = rng.choice(sorted(combos))
    prize = args.prize or rng.choice(sorted(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    mentor = args.mentor or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, gender=gender, mentor=mentor, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes "{f["challenge"].keyword}" and a limousine.',
        f"Tell a gentle rescue story where {f['hero'].id} uses kindness and curiosity instead of force.",
        f"Write a short city adventure in which a fisted problem softens and a badge comes home safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, villain, prize, challenge = f["hero"], f["villain"], f["prize"], f["challenge"]
    return [
        QAItem(
            question=f"What did {hero.id} notice near {f['setting'].place}?",
            answer=f"{hero.id} noticed a black limousine and {villain.label} with a fisted hand.",
        ),
        QAItem(
            question=f"Why did {hero.id} use curiosity before rushing in?",
            answer=f"{hero.id} wanted to understand why the hand was fisted, so {hero.pronoun('subject')} chose gentle questions first.",
        ),
        QAItem(
            question=f"How did the story end for the {prize.label}?",
            answer=f"The {prize.label} was returned safely, and {hero.id} brought it home after kindness calmed the trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a limousine?",
            answer="A limousine is a long car used for special rides, often with extra space and a fancy look.",
        ),
        QAItem(
            question="What does fisted mean?",
            answer="Fisted means closed up tight like a hand making a fist.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others gently and helping them feel safe.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is wanting to know more and asking questions to understand something.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
challenge(C) :- challenge_kind(C).
prize(P) :- prize_kind(P).
valid(P,C,R) :- afford(P,C), prize_ok(C,R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge_kind", cid))
    for rid, pr in PRIZES.items():
        lines.append(asp.fact("prize_kind", rid))
        lines.append(asp.fact("prize_ok", "stuck_fist", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, c, "badge") for p, c in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize],
                 params.name, params.gender, params.mentor)
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


CURATED = [
    StoryParams(place="plaza", challenge="stuck_fist", prize="badge", name="Nova", gender="girl", mentor="mother", trait="curious"),
    StoryParams(place="roof", challenge="stuck_fist", prize="star", name="Mira", gender="girl", mentor="father", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
