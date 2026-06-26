#!/usr/bin/env python3
"""
Storyworld: snuggle + transit + curiosity, in a fairy-tale style.

A small child, a soft bundle, and a magical way to travel form the core
premise. Curiosity creates the turn: the hero wants to peek ahead during a
transit ride, but the ride only stays cozy and safe if the snuggle bundle is
kept in place. The ending proves a change in world state: the hero learns to
travel while keeping the bundle close, and the ride becomes calm and bright.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    transit_kind: str
    route: str
    place_words: list[str]


@dataclass
class Transit:
    id: str
    label: str
    verb: str
    gerund: str
    speed: str
    destination: str
    magic: str
    carries: set[str] = field(default_factory=set)


@dataclass
class Snuggle:
    id: str
    label: str
    phrase: str
    type: str
    comfort: str
    weatherproof: bool = False
    plural: bool = False
    kindness: str = "softly"


@dataclass
class StoryParams:
    setting: str
    transit: str
    snuggle: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        return w


def _r_ruffle(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    snuggle = world.facts.get("snuggle_entity")
    if not hero or not snuggle:
        return out
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if snuggle.worn_by != hero.id:
        return out
    if hero.meters.get("in_transit", 0) < THRESHOLD:
        return out
    sig = ("ruffle", hero.id, snuggle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snuggle.meters["shifted"] = snuggle.meters.get("shifted", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append(f"The little bundle slipped a bit as curiosity tugged at the ride.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if hero.meters.get("stopped", 0) < THRESHOLD:
        return out
    sig = ("settle", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    out.append("When the child sat still and hugged the bundle close, the ride grew gentle again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_ruffle, _r_settle):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "forest_cart": Setting(
        name="the moonlit forest road",
        transit_kind="carriage",
        route="along the piney road",
        place_words=["forest", "road", "carriage"],
    ),
    "river_barge": Setting(
        name="the silver river",
        transit_kind="barge",
        route="down the shining water",
        place_words=["river", "barge", "water"],
    ),
    "hill_tram": Setting(
        name="the hill town",
        transit_kind="tram",
        route="up the steep little track",
        place_words=["hill", "tram", "track"],
    ),
}

TRANSITS = {
    "carriage": Transit(
        id="carriage",
        label="a lantern-lit carriage",
        verb="ride in the carriage",
        gerund="riding in the carriage",
        speed="slow and steady",
        destination="the storybook inn",
        magic="the wheels hummed like a lullaby",
        carries={"seated", "hushed"},
    ),
    "barge": Transit(
        id="barge",
        label="a soft river barge",
        verb="float on the barge",
        gerund="floating on the barge",
        speed="gentle and swaying",
        destination="the little dockhouse",
        magic="the water sang against the wood",
        carries={"seated", "snug"},
    ),
    "tram": Transit(
        id="tram",
        label="a bright hill tram",
        verb="take the tram",
        gerund="taking the tram",
        speed="quick but careful",
        destination="the clocktower garden",
        magic="the bell gave a tiny silver ring",
        carries={"seated", "snug"},
    ),
}

SNUGGLES = {
    "blanket": Snuggle(
        id="blanket",
        label="a velvet blanket",
        phrase="a velvet blanket with little stars",
        type="blanket",
        comfort="warmth",
        weatherproof=True,
    ),
    "pillow": Snuggle(
        id="pillow",
        label="a cloud pillow",
        phrase="a cloud pillow sewn from pale blue cloth",
        type="pillow",
        comfort="softness",
    ),
    "doll": Snuggle(
        id="doll",
        label="a tiny doll",
        phrase="a tiny doll in a ribbon dress",
        type="doll",
        comfort="company",
    ),
}

NAMES = {
    "girl": ["Mira", "Lina", "Tessa", "Ivy"],
    "boy": ["Oren", "Theo", "Bram", "Finn"],
}
TRAITS = ["curious", "gentle", "bright-eyed", "dreamy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TRANSITS:
            for n in SNUGGLES:
                combos.append((s, t, n))
    return combos


def prize_at_risk(transit: Transit, snuggle: Snuggle) -> bool:
    return True


def select_fix(transit: Transit, snuggle: Snuggle) -> bool:
    return snuggle.comfort in {"warmth", "softness", "company"}


def explain_rejection(transit: Transit, snuggle: Snuggle) -> str:
    return f"(No story: the {transit.label} and {snuggle.label} do not make a believable fairy-tale journey.)"


def explain_gender(snuggle_id: str, gender: str) -> str:
    return f"(No story: the tale does not fit {gender} with this choice.)"


def tell(setting: Setting, transit: Transit, snuggle: Snuggle, hero_name: str, hero_type: str, trait: str, caretaker: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"curiosity": 0.0}))
    adult = world.add(Entity(id="Caretaker", kind="character", type=caretaker, label=f"the {caretaker}"))
    bundle = world.add(Entity(id="snuggle", type=snuggle.type, label=snuggle.label, phrase=snuggle.phrase, owner=hero.id, caretaker=adult.id, plural=snuggle.plural))
    bundle.worn_by = hero.id

    world.facts.update(hero=hero, caretaker=adult, snuggle_entity=bundle, transit=transit, setting=setting, snuggle=snuggle)

    world.say(f"Once, in {setting.name}, there lived a {trait} child named {hero.id}.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved {transit.gerund} because {transit.magic}.")
    world.say(f"Most of all, {hero.id} cherished {snuggle.phrase} and kept {bundle.it()} close like a secret star.")

    world.para()
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {caretaker} set out {setting.route} on {transit.label}.")
    hero.meters["in_transit"] = 1.0
    hero.memes["curiosity"] = 1.0
    world.say(f"The ride was {transit.speed}, and the road looked full of little wonders.")
    world.say(f"{hero.id} wanted to peek ahead at every turning, yet {bundle.label} rested in {hero.pronoun('possessive')} lap.")
    propagate(world, narrate=True)

    world.para()
    if hero.memes.get("worry", 0) >= THRESHOLD:
        world.say(f"{hero.id} began to wobble and nearly let {bundle.it()} slip while staring at the dark pines.")
        world.say(f"Then {hero.pronoun('possessive')} {caretaker} smiled and said, 'A curious heart can still travel safely.'")
        hero.meters["stopped"] = 1.0
        propagate(world, narrate=True)
        world.say(f"So {hero.id} tucked {bundle.it()} under one arm, sat back, and watched the lanterns pass like fireflies.")
        hero.memes["curiosity"] = 0.0
        hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    else:
        hero.meters["stopped"] = 1.0
        world.say(f"{hero.id} stayed snug and curious at once, listening to the ride without dropping the bundle.")

    world.para()
    world.say(f"By the time they reached {transit.destination}, {hero.id} was still snuggling {bundle.it()} and smiling.")
    world.say(f"The journey ended soft and bright, and even the road seemed to hush as they stepped down together.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    transit = f["transit"]
    snuggle = f["snuggle"]
    return [
        f'Write a short fairy tale for a child named {hero.id} about {transit.gerund} with {snuggle.phrase}.',
        f"Tell a gentle story where curiosity makes {hero.id} almost lose {snuggle.label} during a magical transit ride.",
        f"Write a fairy-tale story about a snug journey, a curious child, and a safe arrival at {transit.destination}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    transit = f["transit"]
    snuggle = f["snuggle"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a curious child named {hero.id} and {hero.pronoun('possessive')} {caretaker.type}.",
        ),
        QAItem(
            question=f"What did {hero.id} love to do?",
            answer=f"{hero.id} loved {transit.gerund} because the journey felt magical and calm.",
        ),
        QAItem(
            question=f"What precious thing did {hero.id} keep close?",
            answer=f"{hero.id} kept {snuggle.phrase} close during the ride.",
        ),
        QAItem(
            question=f"Why did {hero.id} almost fumble the bundle?",
            answer=f"Curiosity made {hero.id} keep peeking ahead, so {snuggle.label} almost slipped during the transit ride.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} reaching {transit.destination} while snuggling {snuggle.label} safely again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    transit = f["transit"]
    snuggle = f["snuggle"]
    return [
        QAItem(
            question="What is transit?",
            answer="Transit means traveling from one place to another by a vehicle or other moving way.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, learn, and ask questions.",
        ),
        QAItem(
            question="What does a snuggle item do?",
            answer=f"A snuggle item helps someone feel safe, warm, and comforted, like {snuggle.label}.",
        ),
        QAItem(
            question=f"What kind of ride was the {transit.label}?",
            answer=f"It was a fairy-tale transit ride that moved {transit.speed}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
caretaker(C) :- caretaker_name(C).
snuggle(S) :- snuggle_name(S).
transit(T) :- transit_name(T).

curious(H) :- hero(H), curiosity(H).
in_transit(H) :- hero(H), riding(H,_).
at_risk(H,S) :- in_transit(H), snuggle(S), worn_by(S,H), curious(H).
slips(S) :- at_risk(_,S).
settles(H,S) :- in_transit(H), snuggle(S), snug(H,S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_name", sid))
    for tid in TRANSITS:
        lines.append(asp.fact("transit_name", tid))
    for sid in SNUGGLES:
        lines.append(asp.fact("snuggle_name", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transit_name/1.\n#show snuggle_name/1.\n#show setting_name/1."))
    if model is None:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP rules compile and produce a model.")
    return 0


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of curiosity, snuggle, and transit.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transit", choices=TRANSITS)
    ap.add_argument("--snuggle", choices=SNUGGLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father", "grandmother", "grandfather"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    transit = args.transit or rng.choice(list(TRANSITS))
    snuggle = args.snuggle or rng.choice(list(SNUGGLES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    caretaker = args.caretaker or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = "curious"
    return StoryParams(setting=setting, transit=transit, snuggle=snuggle, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TRANSITS[params.transit], SNUGGLES[params.snuggle], params.name, params.gender, params.trait, params.caretaker)
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
        print(asp_program("#show transit_name/1.\n#show snuggle_name/1.\n#show setting_name/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_story_combos())} compatible stories")
        for c in valid_story_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="forest_cart", transit="carriage", snuggle="blanket", name="Mira", gender="girl", caretaker="grandmother", trait="curious"),
            StoryParams(setting="river_barge", transit="barge", snuggle="pillow", name="Oren", gender="boy", caretaker="father", trait="gentle"),
            StoryParams(setting="hill_tram", transit="tram", snuggle="doll", name="Lina", gender="girl", caretaker="mother", trait="bright-eyed"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
