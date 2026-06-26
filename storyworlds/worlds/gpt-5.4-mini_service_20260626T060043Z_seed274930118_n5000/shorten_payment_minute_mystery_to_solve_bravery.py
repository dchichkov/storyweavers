#!/usr/bin/env python3
"""
storyworlds/worlds/shorten_payment_minute_mystery_to_solve_bravery.py
======================================================================

A small superhero storyworld about a brave helper, a tiny mystery, and a
payment that goes missing at exactly the wrong minute.

Seed tale idea:
---
A young hero hears that the city tram cannot open its gate because a payment
token is missing. The hero has only one minute before the parade starts. Brave
and curious, the hero follows a few clues, finds the missing token, and
shortens the wait for everyone by solving the mystery fast.

World model:
---
- The hero has bravery, curiosity, and a time limit measured in minutes.
- The city has a blocked place, a missing payment, and one clue that can reveal
  where the payment went.
- The hero can investigate, discover the hiding place, and restore the payment.
- If the hero acts bravely, the mystery becomes solvable and the wait shortens.

This script follows the Storyweavers world contract:
- standalone stdlib script
- imports shared results eagerly
- imports shared asp lazily
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    crowd: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    clue: str
    verb: str
    search: str
    effect: str
    minute_pressure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    valuable: bool = True


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    grants: str
    prep: str
    ending: str


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_time_pressure(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if hero.meters.get("minutes_left", 0.0) <= 0:
        sig = ("time_out", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["panic"] = hero.memes.get("panic", 0.0) + 1
        out.append("The last minute slipped away.")
    return out


def _r_mystery_solved(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    payment = world.facts.get("payment")
    clue = world.facts.get("clue")
    if not hero or not payment or not clue:
        return out
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if clue.memes.get("found", 0.0) < THRESHOLD:
        return out
    if payment.memes.get("missing", 0.0) < THRESHOLD:
        return out
    sig = ("solve", payment.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    payment.memes["missing"] = 0.0
    payment.location = "gate"
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    out.append("The mystery was solved.")
    return out


CAUSAL_RULES = [
    _r_time_pressure,
    _r_mystery_solved,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was busy, and {setting.crowd} filled the sidewalks."


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a little {hero.type} hero who liked helping people."


def challenge_intro(hero: Entity, challenge: Challenge) -> str:
    return (
        f"{hero.pronoun().capitalize()} noticed a small mystery: someone had hidden "
        f"a payment {challenge.effect}."
    )


def mystery_clue_line(challenge: Challenge) -> str:
    return f"The clue said {challenge.clue}."


def resolve_line(hero: Entity, payment: Entity, tool: Optional[Tool]) -> str:
    if tool is None:
        return f"{hero.id} solved the mystery and brought back the {payment.label}."
    return f"{hero.id} used {tool.label} and brought back the {payment.label}."


def tell(setting: Setting, challenge: Challenge, prize: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"minutes_left": 1.0, "resolve": 1.0},
        memes={"bravery": 0.0, "curiosity": 1.0, "hope": 1.0},
    ))
    sidekick = world.add(Entity(
        id="Sidekick",
        kind="character",
        type="boy",
        meters={"minutes_left": 1.0},
        memes={"worry": 0.0},
    ))
    payment = world.add(Entity(
        id="payment",
        kind="thing",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner="CityGate",
        keeper="Clerk",
        location="somewhere hidden",
        memes={"missing": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="note",
        label="clue note",
        phrase=challenge.clue,
        location="lamp post",
        memes={"found": 0.0},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="key",
        label="searchlight",
        phrase="a bright searchlight",
        location="bench",
        memes={"ready": 1.0},
    ))

    world.say(hero_intro(hero))
    world.say(
        f"{hero.id} loved to help when the city had a problem, especially when "
        f"{hero.pronoun('possessive')} heart beat fast with bravery."
    )
    world.say(
        f"One minute before the parade, {hero.id} saw that the gate could not open "
        f"because the {payment.label} was gone."
    )

    world.para()
    world.say(setting_detail(setting))
    world.say(challenge_intro(hero, challenge))
    world.say(
        f"{hero.id} asked {sidekick.id} to stay close while {hero.pronoun()} began to search."
    )
    world.say(
        f"{hero.id} followed the clue to a quiet spot and looked under the bench."
    )

    hero.memes["bravery"] += 1.0
    clue.memes["found"] = 1.0
    hero.meters["minutes_left"] -= 1.0
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"That brave choice helped {hero.id} move quickly and shorten the wait for everyone."
    )
    if payment.memes.get("missing", 0.0) < THRESHOLD:
        world.say(
            f"{payment.label.capitalize()} was back in the gate box, and the parade could begin."
        )
    else:
        world.say(
            f"{hero.id} kept searching until the {payment.label} turned up."
        )
    world.say(
        f"{hero.id} smiled because the mystery was solved in time."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        payment=payment,
        clue=clue,
        tool=tool,
        challenge=challenge,
        prize=prize,
        setting=setting,
        resolved=payment.memes.get("missing", 0.0) < THRESHOLD,
    )
    return world


SETTINGS = {
    "downtown": Setting(place="downtown square", crowd="busy shoppers and kids", afford={"search"}),
    "harbor": Setting(place="the harbor gate", crowd="seagulls and dock workers", afford={"search"}),
    "museum": Setting(place="the museum steps", crowd="quiet visitors and tour guides", afford={"search"}),
}

CHALLENGES = {
    "lost_token": Challenge(
        id="lost_token",
        clue="the tiny coin rolled under the bench",
        verb="search",
        search="look under the bench",
        effect="that blocked the gate",
        minute_pressure="one minute",
        tags={"mystery", "payment", "minute"},
    ),
    "swapped_box": Challenge(
        id="swapped_box",
        clue="the box was swapped near the lamp post",
        verb="search",
        search="follow the trail near the lamp post",
        effect="that kept the gate closed",
        minute_pressure="one minute",
        tags={"mystery", "payment", "minute"},
    ),
    "hidden_receipt": Challenge(
        id="hidden_receipt",
        clue="the receipt was tucked behind the notice board",
        verb="search",
        search="check behind the notice board",
        effect="that made the clerk worry",
        minute_pressure="one minute",
        tags={"mystery", "payment", "minute"},
    ),
}

PRIZES = {
    "coin": Prize(id="coin", label="coin", phrase="a shiny payment coin", type="coin"),
    "ticket": Prize(id="ticket", label="ticket", phrase="a stamped payment ticket", type="ticket"),
    "token": Prize(id="token", label="token", phrase="a round payment token", type="token"),
}

TOOLS = [
    Tool(id="searchlight", label="a searchlight", helps={"search"}, grants="spot clues", prep="shine", ending="lit the way"),
    Tool(id="magnifier", label="a magnifier", helps={"search"}, grants="read clues", prep="hold up", ending="helped read the tiny clue"),
]

GIRL_NAMES = ["Nova", "Mira", "Ivy", "Luna", "Zia"]
BOY_NAMES = ["Jett", "Kai", "Finn", "Max", "Toby"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, challenge, prize) for place in SETTINGS for challenge in CHALLENGES for prize in PRIZES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: bravery, mystery, payment, and a minute.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the words "shorten", "payment", and "minute".',
        f"Tell a brave mystery story where {f['hero'].id} solves a payment problem before one minute runs out.",
        f"Write a gentle superhero tale about a clue, a missing payment, and a hero who shortens the wait.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    payment: Entity = f["payment"]
    clue: Entity = f["clue"]
    setting: Setting = f["setting"]
    challenge: Challenge = f["challenge"]
    resolved = f["resolved"]
    qa = [
        QAItem(
            question=f"Who was the brave hero in the story?",
            answer=f"The brave hero was {hero.id}, who helped solve the mystery at {setting.place}.",
        ),
        QAItem(
            question=f"What was missing from the gate?",
            answer=f"The missing thing was the {payment.label}, which was the payment the gate needed.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} search?",
            answer=f"The clue was that {clue.phrase}, which helped {hero.id} know where to look.",
        ),
    ]
    if resolved:
        qa.append(QAItem(
            question=f"How did {hero.id} help shorten the wait?",
            answer=f"{hero.id} found the missing {payment.label} and brought it back before the minute was over, so the wait got shorter.",
        ))
    else:
        qa.append(QAItem(
            question=f"Did the mystery get solved in time?",
            answer=f"The story kept searching, but the mystery did not fully finish before the minute ran out.",
        ))
    qa.append(QAItem(
        question=f"Why did {hero.id} need bravery?",
        answer=f"{hero.id} needed bravery to keep searching quickly and face the mystery when the payment was missing.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when it feels a little scary, because it is the right thing to do.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand yet, so you look for clues.",
        ),
        QAItem(
            question="What is a payment?",
            answer="A payment is something you give to pay for a thing or to make something open, start, or happen.",
        ),
        QAItem(
            question="What does it mean to shorten something?",
            answer="To shorten something means to make it take less time or to make it smaller in length.",
        ),
        QAItem(
            question="What is a minute?",
            answer="A minute is a short unit of time. Sixty minutes make one hour.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.type:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
prize(P) :- prize_name(P).
clue(C) :- clue_name(C).

brave(H) :- bravery(H), bravery_threshold(1).
can_solve(H) :- brave(H), has_clue(H), has_payment(H).
shortens_wait(H) :- can_solve(H), minute_left(1).

resolved(H) :- can_solve(H), found_payment(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    for pid in PRIZES:
        lines.append(asp.fact("prize_name", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("clue_name", cid))
    lines.append(asp.fact("bravery_threshold", 1))
    lines.append(asp.fact("minute_left", 1))
    lines.append(asp.fact("has_clue", "nova"))
    lines.append(asp.fact("has_payment", "nova"))
    lines.append(asp.fact("found_payment", "nova"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show shortens_wait/1."))
    got = set(asp.atoms(model, "resolved"))
    if got:
        print("OK: ASP rules produce a resolved story shape.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected result.")
    return 1


def asp_resolved() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="downtown", challenge="lost_token", prize="coin", name="Nova", gender="girl", parent="mother"),
    StoryParams(place="harbor", challenge="swapped_box", prize="token", name="Jett", gender="boy", parent="father"),
    StoryParams(place="museum", challenge="hidden_receipt", prize="ticket", name="Mira", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1.\n#show shortens_wait/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_resolved())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
