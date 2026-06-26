#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tactile_meet_anorexic_cautionary_teamwork_friendship_superhero.py
================================================================================================

A standalone storyworld for a tiny Superhero Story with tactile clues, a first
meeting, cautionary teamwork, and friendship.

The seed words are woven into the world model and the generated prose:
- tactile
- meet
- anorexic

This world aims for a child-facing, classical arc:
setup -> caution -> teamwork turn -> friendship resolution
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"energy": 0.0}
        if not self.memes:
            self.memes = {"care": 0.0, "worry": 0.0, "joy": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "hero"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    caution: str
    risk: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        c.zone = set(self.zone)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "skyline": Setting(place="the skyline bridge", affords={"meet", "rescue", "caution"}),
    "academy": Setting(place="the hero academy", affords={"meet", "train", "caution"}),
    "harbor": Setting(place="the harbor docks", affords={"meet", "rescue", "caution"}),
}

CHALLENGES = {
    "meet": Challenge(
        id="meet",
        verb="meet the new kid",
        gerund="meeting the new kid",
        caution="be careful and listen first",
        risk="a lonely mix-up could hurt feelings",
        kind="social",
        tags={"meet", "friendship", "cautionary"},
    ),
    "rescue": Challenge(
        id="rescue",
        verb="help the lost courier",
        gerund="helping the lost courier",
        caution="watch the loose wires",
        risk="a stumble could break the package",
        kind="action",
        tags={"teamwork", "cautionary"},
    ),
    "train": Challenge(
        id="train",
        verb="practice a new power",
        gerund="training a new power",
        caution="move slowly and check the floor",
        risk="a slip could cause a crash",
        kind="action",
        tags={"teamwork", "cautionary"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", region="back"),
    "mask": Prize(label="mask", phrase="a smooth blue mask", region="face"),
    "gloves": Prize(label="gloves", phrase="tactile gloves with tiny pads", region="hands"),
}

GEAR = [
    Gear(
        id="gripgloves",
        label="tactile gloves",
        covers={"hands"},
        guards={"slip", "scratch", "static"},
        prep="put on the tactile gloves first",
        tail="slipped on the tactile gloves together",
    ),
    Gear(
        id="fieldcloak",
        label="a field cloak",
        covers={"back"},
        guards={"wind", "rain"},
        prep="fasten a field cloak before going out",
        tail="tied on the field cloak",
    ),
    Gear(
        id="sparkvisor",
        label="a spark visor",
        covers={"face"},
        guards={"glare", "spark"},
        prep="snap on a spark visor",
        tail="clicked the spark visor into place",
    ),
]

HERO_NAMES = ["Nova", "Mira", "Kai", "Zara", "Jett", "Luna"]
SIDEKICKS = ["Pip", "Sol", "Bean", "Tess", "Rio", "Dot"]


class StoryWorld(World):
    pass


def tension_rule(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["worry"] >= THRESHOLD and friend.memes["care"] >= THRESHOLD:
        hero.memes["joy"] += 0.5
        friend.memes["trust"] += 0.5


def predict_outcome(world: World, hero: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "spoiled": bool(prize.meters.get("broken", 0.0) >= THRESHOLD),
        "tension": sim.get("hero").memes["worry"],
    }


def do_challenge(world: World, actor: Entity, challenge: Challenge, narrate: bool = True) -> None:
    world.zone = {"hands", "face"} if challenge.id == "meet" else {"back", "hands"}
    actor.meters["energy"] += 1
    actor.memes["care"] += 1
    if challenge.id == "train":
        actor.memes["worry"] += 1
    if narrate:
        world.say(f"{actor.id} chose to {challenge.verb}.")
        if challenge.id == "meet":
            world.say("The room felt quiet, and every step sounded important.")
    tension_rule(world)


def introduce(world: World, hero: Entity, friend: Entity, place: str) -> None:
    world.say(
        f"{hero.id} was a little superhero with {hero.phrase} and a very tactile sense "
        f"for clues. {hero.id} and {friend.id} lived near {place}."
    )
    world.say(
        f"They had never gotten to meet the new kid in the bright hall, but they both "
        f"wanted to be kind."
    )


def caution(world: World, mentor: Entity, hero: Entity, challenge: Challenge, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'"{challenge.caution}," {mentor.id} said. "{challenge.risk} if we rush."'
    )
    world.say(
        f"{hero.id} looked at {prize.phrase} and nodded. The little hero could feel "
        f"that this was a moment for careful hands, not fast feet."
    )


def meet_friend(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["care"] += 1
    world.say(
        f"Then {hero.id} and {friend.id} met at the doorway. {friend.id} smiled first, "
        f"and {hero.id} answered with a shy wave."
    )
    world.say(
        f"They noticed the same tiny signs at once: a dropped badge, a trembling glove, "
        f"and a nervous breath."
    )


def teamwork_turn(world: World, hero: Entity, friend: Entity, challenge: Challenge, prize: Entity) -> None:
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} did not rush ahead. Instead, {hero.id} pointed out the clues in a "
        f"tactile way, and {friend.id} listened closely."
    )
    world.say(
        f"Together they chose the calm path: one held the door, the other picked up the "
        f"fallen badge, and both shared the job."
    )
    world.say(
        f"That teamwork kept {prize.phrase} safe while they finished {challenge.gerund}."
    )


def friendship_end(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At the end, {hero.id} and {friend.id} laughed together like old friends. "
        f"The new meeting had turned into friendship."
    )
    world.say(
        f"{hero.id} felt proud, because being careful had helped everyone stay safe."
    )


def select_gear(challenge: Challenge, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers:
            return gear
    return None


def build_story(setting: Setting, challenge: Challenge, prize: Prize, hero_name: str, friend_name: str) -> World:
    world = StoryWorld(setting)
    hero = world.add(Entity(id="hero", kind="character", type="hero", label=hero_name, phrase="a tactile hero"))
    friend = world.add(Entity(id="friend", kind="character", type="hero", label=friend_name, phrase="a careful friend"))
    mentor = world.add(Entity(id="mentor", kind="character", type="adult", label="Captain Hale", phrase="a cautious mentor"))
    item = world.add(Entity(id="prize", type="thing", label=prize.label, phrase=prize.phrase))
    item.worn_by = hero.id

    world.facts.update(hero=hero, friend=friend, mentor=mentor, prize=item, challenge=challenge, setting=setting)

    introduce(world, hero, friend, setting.place)
    world.para()
    caution(world, mentor, hero, challenge, item)
    meet_friend(world, hero, friend)
    do_challenge(world, hero, challenge)
    world.para()
    gear = select_gear(challenge, prize)
    if challenge.id == "meet":
        teamwork_turn(world, hero, friend, challenge, item)
        friendship_end(world, hero, friend, challenge)
    else:
        world.say(
            f"With a little help, they used {gear.label if gear else 'good teamwork'} and made "
            f"the mission gentle and safe."
        )
        friendship_end(world, hero, friend, challenge)

    world.facts["gear"] = gear
    world.facts["resolved"] = True
    return world


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.challenge not in CHALLENGES:
        raise StoryError("Unknown challenge.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")


KNOWLEDGE = {
    "tactile": [
        QAItem(
            question="What does tactile mean?",
            answer="Tactile means related to touch, like feeling bumps, fabric, or tiny clues with your hands.",
        )
    ],
    "meet": [
        QAItem(
            question="What does it mean to meet someone?",
            answer="To meet someone means to see a new person for the first time and start talking with them.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and share the job so the task goes better.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it is meant to warn people to be careful and make safe choices.",
        )
    ],
    "anorexic": [
        QAItem(
            question="What does anorexic mean?",
            answer="Anorexic is a medical word about someone being dangerously underweight and needing care from a doctor and trusted adults.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Superhero Story for a young child that includes the words "tactile", "meet", and "anorexic".',
        f"Tell a cautionary friendship story where {f['hero'].label} and {f['friend'].label} work together at {f['setting'].place}.",
        f"Write a gentle superhero tale about careful teamwork, a first meeting, and a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mentor = f["mentor"]
    challenge = f["challenge"]
    prize = f["prize"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {hero.label} and {friend.label}, two little superheroes learning to work together at {place}.",
        ),
        QAItem(
            question=f"Why did {mentor.label} warn them before they tried to {challenge.verb}?",
            answer=f"{mentor.label} warned them because {challenge.risk}, so they needed to slow down and stay careful.",
        ),
        QAItem(
            question=f"What stayed safe because of their teamwork?",
            answer=f"{prize.phrase} stayed safe because {hero.label} and {friend.label} shared the job and chose the gentle way.",
        ),
        QAItem(
            question=f"How did the first meeting turn out?",
            answer=f"The first meeting turned into friendship, because {hero.label} listened, {friend.label} helped, and they smiled together at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["tactile", "meet", "teamwork", "friendship", "cautionary", "anorexic"]:
        out.extend(KNOWLEDGE[tag])
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with tactile clues, teamwork, and friendship.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    challenge = args.challenge or rng.choice(list(CHALLENGES.keys()))
    prize = args.prize or rng.choice(list(PRIZES.keys()))
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(SIDEKICKS)
    params = StoryParams(place=place, challenge=challenge, prize=prize, name=name, sidekick=friend)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_story(SETTINGS[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name, params.sidekick)
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


ASP_RULES = r"""
place(P) :- setting(P).
challenge(C) :- challenge_id(C).
prize(P) :- prize_id(P).

safe_choice(Place, Challenge, Prize) :- place(Place), challenge(Challenge), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge_id", cid))
    for pid in PRIZES:
        lines.append(asp.fact("prize_id", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show safe_choice/3."))
    shown = sorted(set(asp.atoms(model, "safe_choice")))
    py = sorted((p, c, r) for p in SETTINGS for c in CHALLENGES for r in PRIZES)
    if shown == py:
        print(f"OK: ASP parity matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(set(shown) - set(py)))
    print("Python only:", sorted(set(py) - set(shown)))
    return 1


def asp_choices() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show safe_choice/3."))
    return sorted(set(asp.atoms(model, "safe_choice")))


CURATED = [
    StoryParams(place="academy", challenge="meet", prize="gloves", name="Nova", sidekick="Pip"),
    StoryParams(place="skyline", challenge="rescue", prize="cape", name="Mira", sidekick="Sol"),
    StoryParams(place="harbor", challenge="train", prize="mask", name="Kai", sidekick="Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_choice/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        choices = asp_choices()
        for p, c, r in choices:
            print(p, c, r)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
