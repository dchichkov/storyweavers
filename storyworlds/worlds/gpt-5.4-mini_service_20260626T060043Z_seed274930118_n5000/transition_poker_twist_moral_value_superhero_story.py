#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transition_poker_twist_moral_value_superhero_story.py
=============================================================================================================================

A small superhero story world built from the seed words:
- transition
- poker

Premise:
A young hero is ready for a big transition into a more responsible kind of
heroism. At a friendly community poker night, a twist reveals that winning is
less important than honesty, trust, and protecting others.

The story logic is state-driven:
- The hero has a mask, a moral value, and a mission.
- A poker game creates tension because bluffing can be tempting.
- A twist exposes a hidden problem.
- The hero chooses a truthful, helpful action, completing the transition.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
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
        female = {"girl", "woman", "mother", "sister", "aunt"}
        male = {"boy", "man", "father", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    crowds: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    activity: str
    tension: str
    twist: str
    turn: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    moral_value: str
    owner_role: str = "friend"


@dataclass
class Gadget:
    id: str
    label: str
    description: str
    helps: set[str]
    moral_bonus: str
    transition_phrase: str


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
        clone = World(self.setting)
        clone.entities = {k: _copy_entity(v) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _copy_entity(e: Entity) -> Entity:
    return Entity(
        id=e.id,
        kind=e.kind,
        type=e.type,
        label=e.label,
        phrase=e.phrase,
        owner=e.owner,
        caretaker=e.caretaker,
        worn_by=e.worn_by,
        plural=e.plural,
        meters=dict(e.meters),
        memes=dict(e.memes),
    )


@dataclass
class StoryParams:
    setting: str
    challenge: str
    prize: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting(place="the rooftop garden", indoor=False, crowds=False, afford={"poker"}),
    "community_center": Setting(place="the community center", indoor=True, crowds=True, afford={"poker"}),
    "library_hall": Setting(place="the library hall", indoor=True, crowds=True, afford={"poker"}),
}

CHALLENGES = {
    "poker_night": Challenge(
        id="poker_night",
        activity="play poker",
        tension="the cards made everyone want to bluff",
        twist="a folded note slipped from under the table",
        turn="the note showed a missing child was waiting next door",
        risk="a dishonest win could waste precious time",
        keyword="poker",
        tags={"poker", "truth", "cards", "transition"},
    ),
    "transition_test": Challenge(
        id="transition_test",
        activity="help with a transition from sidekick to full hero",
        tension="the hero had to act like a leader, not just a helper",
        twist="the old hero suit jammed on a loose panel",
        turn="fixing the suit became a chance to prove patience",
        risk="rushing would damage the suit and the trust",
        keyword="transition",
        tags={"transition", "trust", "hero"},
    ),
}

PRIZES = {
    "truth": Prize(
        label="truth badge",
        phrase="a bright truth badge",
        type="badge",
        moral_value="honesty",
    ),
    "trust": Prize(
        label="team pin",
        phrase="a silver team pin",
        type="pin",
        moral_value="trust",
    ),
    "care": Prize(
        label="care cloak",
        phrase="a soft care cloak",
        type="cloak",
        moral_value="care",
    ),
}

GADGETS = {
    "signal_lamp": Gadget(
        id="signal_lamp",
        label="signal lamp",
        description="a little lamp that flashes a safe signal to teammates",
        helps={"poker_night", "transition_test"},
        moral_bonus="honest signaling",
        transition_phrase="shift from guessing to helping",
    ),
    "helper_gloves": Gadget(
        id="helper_gloves",
        label="helper gloves",
        description="soft gloves for careful repairs and kind fixes",
        helps={"transition_test"},
        moral_bonus="careful work",
        transition_phrase="move from worry to action",
    ),
}

HERO_NAMES = ["Nova", "Jade", "Milo", "Aria", "Pax", "Ivy", "Zane", "Riley"]
SIDEKICK_NAMES = ["Beep", "Scout", "Echo", "Comet", "Patch", "Flip"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "careful", "bright", "steady", "kind", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid, ch in CHALLENGES.items():
            if "poker" not in setting.afford:
                continue
            for pid, prize in PRIZES.items():
                if prize.moral_value in ch.tags:
                    out.append((sid, cid, pid))
    return out


def _hero_desc(hero: Entity, trait: str) -> str:
    return f"little {trait} {hero.type} {hero.id}"


def tell(setting: Setting, challenge: Challenge, prize: Prize,
         hero_name: str, hero_type: str, sidekick_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        memes={"hope": 1.0, "duty": 1.0, "curiosity": 1.0},
        meters={"readiness": 1.0},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name, kind="character", type="thing", label=sidekick_name,
        memes={"worry": 1.0},
    ))
    prize_ent = world.add(Entity(
        id="prize", type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=sidekick.id,
    ))
    hero.memes["moral_value"] = 1.0

    world.say(
        f"{hero.id} was a {_hero_desc(hero, 'steady')} who was ready for a new "
        f"transition into real hero work."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {prize.label}, because "
        f"{hero.pronoun('possessive')} team believed a hero should protect the "
        f"moral value of {prize.moral_value} as well as the city."
    )
    world.say(
        f"{hero.id} and {sidekick.id} went to {setting.place} for a friendly "
        f"community poker night."
    )

    world.para()
    world.say(
        f"At the table, {challenge.tension}. {hero.id} wanted to smile and play "
        f"fair, but the shiny cards felt like a test."
    )
    hero.memes["tempted"] = 1.0
    world.say(
        f"{hero.id} noticed that one quick bluff could win the round, yet it "
        f"could also make {hero.pronoun('object')} look clever instead of kind."
    )

    world.para()
    world.say(
        f"Then came the twist: {challenge.twist}. That changed the whole room at once."
    )
    hero.memes["alert"] = 1.0
    world.say(
        f"The hidden note matched {challenge.turn}, so {hero.id} stopped thinking "
        f"about winning and started thinking about who needed help."
    )

    gadget = None
    if prize.moral_value == "honesty":
        gadget = GADGETS["signal_lamp"]
    elif challenge.id == "transition_test":
        gadget = GADGETS["helper_gloves"]

    if gadget:
        world.say(
            f"{hero.id} picked up {gadget.label} as part of the transition from "
            f"showing off to doing the right thing."
        )
        hero.memes["transition"] = 1.0
        hero.memes["moral_value"] = 2.0
        world.say(
            f"With {gadget.description}, {hero.id} could {gadget.transition_phrase} "
            f"and keep {prize_ent.label} safe."
        )

    world.para()
    hero.memes["resolve"] = 1.0
    sidekick.memes["worry"] = 0.0
    world.say(
        f"{hero.id} told the truth about the cards and led the way to the next room."
    )
    world.say(
        f"That helped the missing child, and it also proved that a hero's best "
        f"win is an honest one."
    )
    world.say(
        f"By the end, {hero.id} had grown into the new role, and {prize_ent.label} "
        f"stood for {prize.moral_value} instead of a simple trophy."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        prize=prize_ent,
        setting=setting,
        challenge=challenge,
        prize_cfg=prize,
        gadget=gadget,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    prize = f["prize_cfg"]
    return [
        f'Write a short superhero story for a young child that includes "{challenge.keyword}" and the word "transition".',
        f"Tell a gentle story where {hero.id} has to choose between bluffing at poker and being honest.",
        f"Write a story with a twist, a moral value, and a brave hero who helps others instead of showing off.",
        f"Create a tiny superhero tale about {hero.id} and {prize.phrase} at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    prize = f["prize_cfg"]
    ch = f["challenge"]
    gadget = f.get("gadget")
    qa = [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, a young hero who is learning a new transition into more responsible hero work.",
        ),
        QAItem(
            question=f"What game were they playing at {f['setting'].place}?",
            answer=f"They were playing poker at {f['setting'].place}, which made the room full of cards, guesses, and careful faces.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {ch.twist.lower()}, so {hero.id} had to stop thinking about winning and start thinking about helping.",
        ),
        QAItem(
            question=f"What moral value mattered most in the story?",
            answer=f"Honesty mattered most, because {hero.id} chose the truthful path instead of bluffing.",
        ),
    ]
    if gadget:
        qa.append(
            QAItem(
                question=f"How did {gadget.label} help?",
                answer=f"{gadget.label.capitalize()} helped {hero.id} make a kind and careful transition, and it supported the honest choice that protected {prize.label}.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and calm, because being honest helped the team and showed what kind of hero {hero.id} wanted to become.",
        )
    )
    qa.append(
        QAItem(
            question=f"Who went with {hero.id}?",
            answer=f"{sidekick.id} went with {hero.id}, and by the end they were working together with less worry and more trust.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "poker": [
        QAItem(
            question="What is poker?",
            answer="Poker is a card game where players take turns, watch carefully, and try to make the best hand or best choice.",
        )
    ],
    "transition": [
        QAItem(
            question="What does transition mean?",
            answer="A transition is a change from one state to another, like moving from one job or role into a new one.",
        )
    ],
    "honesty": [
        QAItem(
            question="Why is honesty important?",
            answer="Honesty is important because people trust you more when you tell the truth and do not trick them.",
        )
    ],
    "hero": [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero protects others, solves problems, and tries to help people stay safe.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story go in a new direction.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    if world.facts.get("gadget"):
        tags.add("transition")
    tags.add("hero")
    out: list[QAItem] = []
    for key in ("poker", "twist", "honesty", "transition", "hero"):
        if key in tags or key in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[key])
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, challenge: Challenge, prize: Prize) -> str:
    return (
        f"(No story: {setting.place} supports poker, but this combination does not "
        f"create a plausible moral turn for {prize.label} in {challenge.id}.)"
    )


ASP_RULES = r"""
setting(S) :- setting_fact(S).
challenge(C) :- challenge_fact(C).
prize(P) :- prize_fact(P).

valid(S, C, P) :- setting(S), challenge(C), prize(P),
                  affords(S, poker),
                  challenge_tag(C, T), prize_value(P, T).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        if s.crowds:
            lines.append(asp.fact("crowds", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge_fact", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("challenge_tag", cid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize_fact", pid))
        lines.append(asp.fact("prize_value", pid, p.moral_value))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with poker, a twist, and a moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--sidekick-name")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.challenge:
        combos = [c for c in combos if c[1] == args.challenge]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, prize = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    return StoryParams(
        setting=setting,
        challenge=challenge,
        prize=prize,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHALLENGES[params.challenge],
        PRIZES[params.prize],
        params.hero_name,
        params.hero_type,
        params.sidekick_name,
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


CURATED = [
    StoryParams(setting="rooftop", challenge="poker_night", prize="truth", hero_name="Nova", hero_type="girl", sidekick_name="Scout"),
    StoryParams(setting="community_center", challenge="poker_night", prize="trust", hero_name="Milo", hero_type="boy", sidekick_name="Echo"),
    StoryParams(setting="library_hall", challenge="transition_test", prize="care", hero_name="Aria", hero_type="girl", sidekick_name="Patch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = seed
            sample.params = params
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
            header = f"### {p.hero_name}: {p.challenge} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
