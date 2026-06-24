#!/usr/bin/env python3
"""
storyworlds/worlds/aft_stance_mitt_foreshadowing_humor_sound_effects.py
=======================================================================

A standalone storyworld in a small pirate-tale domain.

Premise:
- On a little ship, a child pirate wants to stand at the aft rail and help sail.
- A strong, salty gust, a slippery deck, and a silly overlarge mitt create tension.
- Foreshadowing is built into the world state: the wind, the creak of the mast,
  the mixed-up stance, and the mitt's poor grip all point toward trouble.
- Humor comes from the child taking a dramatic pirate stance in a mitt that is
  much too big.
- Sound effects carry the action: creak, slap, skrrt, sploosh, whoop.

The story engine simulates a compact causal world with meters (physical state)
and memes (emotional state), and a tiny ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    worn_by: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ShipPart:
    id: str
    label: str
    phrase: str
    risk: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mitt:
    id: str
    label: str
    phrase: str
    size: str
    grip: float
    tags: set[str] = field(default_factory=set)


@dataclass
class Wind:
    id: str
    label: str
    phrase: str
    strength: float
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.wind: float = 0.0
        self.deck_slip: float = 0.0
        self.sway: float = 0.0

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
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.wind = self.wind
        clone.deck_slip = self.deck_slip
        clone.sway = self.sway
        return clone


def _r_foreshadow(world: World) -> list[str]:
    out = []
    deck = world.get("deck")
    mitt = world.get("mitt")
    hero = world.get("hero")
    if world.wind >= 1.0 and deck.meters.get("wet", 0.0) >= 1.0 and mitt.meters.get("bulky", 0.0) >= 1.0:
        sig = ("foreshadow",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1
        out.append("The deck gave a sneaky little creak.")
    return out


def _r_slip(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    deck = world.get("deck")
    if hero.meters.get("off_balance", 0.0) < THRESHOLD:
        return []
    sig = ("slip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deck.meters["scrape"] = deck.meters.get("scrape", 0.0) + 1
    hero.meters["slip"] = hero.meters.get("slip", 0.0) + 1
    out.append("Skrrt.")
    return out


def _r_mitt_fumble(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mitt = world.get("mitt")
    if hero.meters.get("slip", 0.0) < THRESHOLD:
        return []
    sig = ("fumble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mitt.meters["lost_grip"] = mitt.meters.get("lost_grip", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    out.append("Flap-flap!")
    return out


def _r_resolve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mitt = world.get("mitt")
    if hero.meters.get("slip", 0.0) < THRESHOLD:
        return []
    sig = ("resolve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    mitt.meters["secure"] = mitt.meters.get("secure", 0.0) + 1
    out.append("Whoop!")
    return out


CAUSAL_RULES = [_r_foreshadow, _r_slip, _r_mitt_fumble, _r_resolve]


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


@dataclass
class StoryParams:
    deck: str
    wind: str
    mitt: str
    stance: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


DECKS = {
    "aft": ShipPart(
        id="aft",
        label="the aft deck",
        phrase="the aft deck by the rail",
        risk="slick boards",
        sound="creak",
        tags={"aft", "deck", "ship"},
    ),
    "quarterdeck": ShipPart(
        id="quarterdeck",
        label="the quarterdeck",
        phrase="the quarterdeck behind the wheel",
        risk="high rail",
        sound="clack",
        tags={"deck", "ship"},
    ),
}

WINDS = {
    "breeze": Wind(id="breeze", label="sea breeze", phrase="a fresh sea breeze", strength=1.0, tags={"wind"}),
    "gust": Wind(id="gust", label="hard gust", phrase="a hard salty gust", strength=2.0, tags={"wind"}),
}

MITTS = {
    "mitt": Mitt(id="mitt", label="mitt", phrase="a wool mitt", size="huge", grip=0.35, tags={"mitt"}),
    "hookmitt": Mitt(id="hookmitt", label="mitt", phrase="a patched mitt with a tiny hook on one finger", size="odd", grip=0.55, tags={"mitt"}),
}

STANCES = {
    "pirate": "stood with a bold pirate stance",
    "wobble": "tried a brave stance and wobbled a little",
}

GIRL_NAMES = ["Lia", "Mina", "Nora", "Tess", "Pia"]
BOY_NAMES = ["Finn", "Owen", "Jace", "Noel", "Toby"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for deck in DECKS:
        for wind in WINDS:
            for mitt in MITTS:
                if deck == "aft" and mitt == "mitt":
                    combos.append((deck, wind, mitt, "pirate"))
                if deck == "aft" and mitt == "hookmitt":
                    combos.append((deck, wind, mitt, "wobble"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with aft, stance, mitt.")
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--mitt", choices=MITTS)
    ap.add_argument("--stance", choices=STANCES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.deck is None or c[0] == args.deck)
              and (args.wind is None or c[1] == args.wind)
              and (args.mitt is None or c[2] == args.mitt)
              and (args.stance is None or c[3] == args.stance)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    deck, wind, mitt, stance = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    hero = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero])
    return StoryParams(deck=deck, wind=wind, mitt=mitt, stance=stance, hero=hero, hero_gender=gender, helper=helper, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    world = World()
    deck = world.add(Entity(id="deck", type="thing", label=DECKS[params.deck].label, meters={"wet": 1.0, "scrape": 0.0}, memes={"unease": 0.0}))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero, meters={"off_balance": 0.0, "slip": 0.0}, memes={"joy": 0.0, "bravery": 0.0, "humor": 0.0, "unease": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, meters={"steady": 1.0}, memes={"joy": 0.0, "humor": 0.0}))
    mitt = world.add(Entity(id="mitt", type="thing", label=MITTS[params.mitt].label, phrase=MITTS[params.mitt].phrase, owner="hero", worn_by="hero", meters={"bulky": 1.0, "lost_grip": 0.0, "secure": 0.0}, memes={"humor": 0.0}))
    world.wind = WINDS[params.wind].strength
    world.deck_slip = 1.0
    world.sway = 1.0

    world.say(f"{hero.label} was a little pirate who loved the aft deck.")
    world.say(f"{helper.label} watched {hero.label} and grinned, because {hero.label} {STANCES[params.stance]} in {mitt.phrase}.")
    world.say(f"The mitt was so big it could have worn a hat of its own.")

    world.para()
    world.say(f"At the {DECKS[params.deck].phrase}, {DECKS[params.deck].sound}-{DECKS[params.deck].sound} went the boards.")
    world.say(f"{WINDS[params.wind].phrase} puffed hard from the sea, and the rope gave a soft twang.")

    if params.stance == "pirate":
        hero.meters["off_balance"] = 1.0
    else:
        hero.meters["off_balance"] = 1.0
        hero.memes["humor"] += 1.0

    propagate(world, narrate=True)

    world.para()
    if hero.meters.get("slip", 0.0) >= THRESHOLD:
        world.say(f"{hero.label} windmilled, the mitt flapped, and {helper.label} laughed first and helped second.")
        world.say(f"The helper caught {hero.label} by the elbow before any real tumble.")
        hero.memes["joy"] += 1.0
        helper.memes["joy"] += 1.0
        world.say("After that, the pirate stood with feet apart and gripped the rail with both hands.")
        world.say("The deck stayed steady enough for a proud grin.")
    else:
        world.say(f"{hero.label} held the stance just right, and the mitt stayed put like a sleepy crab.")
        world.say("Nothing dramatic happened, which somehow felt like the joke.")

    world.facts.update(
        hero=hero,
        helper=helper,
        deck=deck,
        mitt=mitt,
        deck_cfg=DECKS[params.deck],
        wind_cfg=WINDS[params.wind],
        mitt_cfg=MITTS[params.mitt],
        stance=params.stance,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child about {f["hero"].label} at {f["deck_cfg"].phrase} using {f["mitt_cfg"].phrase}. Include a funny sound effect.',
        f"Tell a short story where {f['hero'].label} tries a {f['stance']} on the aft deck and the wind makes things wobbly, but the ending stays playful.",
        f'Write a foreshadowing-filled pirate story with humor and sound effects that uses the words "aft", "stance", and "mitt".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"It is about {hero.label}, who wanted to look brave on the aft deck while wearing a mitt.",
        ),
        QAItem(
            question=f"What made the deck feel tricky before the little slip?",
            answer=f"The aft deck was wet, the wind was strong, and the mitt was too bulky to help much. Those little clues foreshadowed a wobble.",
        ),
        QAItem(
            question=f"Why did {helper.label} laugh?",
            answer=f"{helper.label} laughed because {hero.label} struck a dramatic stance in a mitten-like mitt that was much too big. It looked very silly.",
        ),
        QAItem(
            question="What sound effect appears in the story?",
            answer="The story uses creak, skrrt, flap-flap, and whoop to make the pirate action feel lively.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the aft of a ship?",
            answer="The aft is the back part of a ship, near the stern, where the wake trails behind.",
        ),
        QAItem(
            question="What is a stance?",
            answer="A stance is the way someone stands. A careful stance can help a person keep their balance.",
        ),
        QAItem(
            question="What is a mitt?",
            answer="A mitt is a soft hand covering that keeps a hand warm or protected. If it is too big, it can make gripping hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    out.append(f"fired={sorted(list(world.fired))}")
    return "\n".join(out)


ASP_RULES = r"""
wet_deck(deck) :- deck(deck), wet(deck).
wobbly(hero) :- off_balance(hero), bulky(mitt).
foreshadow(hero) :- wet_deck(deck), wobbly(hero), wind_strong.
"""
def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for d in DECKS:
        lines.append(asp.fact("deck", d))
    for w, cfg in WINDS.items():
        lines.append(asp.fact("wind", w))
        if cfg.strength >= 2.0:
            lines.append(asp.fact("wind_strong"))
    for m in MITTS:
        lines.append(asp.fact("mitt", m))
        lines.append(asp.fact("bulky", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show foreshadow/1."))
    return 0 if model is not None else 1


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


CURATED = [
    StoryParams(deck="aft", wind="gust", mitt="mitt", stance="pirate", hero="Lia", hero_gender="girl", helper="Finn", helper_gender="boy"),
    StoryParams(deck="aft", wind="breeze", mitt="hookmitt", stance="wobble", hero="Toby", hero_gender="boy", helper="Nora", helper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show foreshadow/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show foreshadow/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
