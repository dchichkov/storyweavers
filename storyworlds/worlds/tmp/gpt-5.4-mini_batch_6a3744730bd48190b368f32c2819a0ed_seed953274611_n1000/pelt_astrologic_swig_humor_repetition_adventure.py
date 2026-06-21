#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pelt_astrologic_swig_humor_repetition_adventure.py
===================================================================================

A tiny adventure storyworld about a kid and a companion exploring a windy hill,
a cozy observatory, a funny repeated mishap with a pelt, an astrologic chart,
and a celebratory swig.

Seed words:
- pelt
- astrologic
- swig

Features:
- Humor
- Repetition

Style:
- Adventure
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    windy: bool = False
    dark: bool = False
    stars_visible: bool = False
    safe_floor: bool = True


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reaction:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    prop: str
    drink: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_wind(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["carried"] < THRESHOLD:
            continue
        sig = ("wind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("hill").meters["tossed"] += 1
        out.append("__wind__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["confusion"] < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["amused"] += 1
        out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("wind", _r_wind), Rule("laugh", _r_laugh)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prop_id, prop in PROPS.items():
            for drink_id, drink in DRINKS.items():
                if place.dark and "astrologic" in prop.tags and "swig" in drink.tags:
                    combos.append((place_id, prop_id, drink_id))
    return combos


def sensible_responses() -> list[Reaction]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def choose_response(rid: str) -> Reaction:
    if rid not in RESPONSES:
        raise StoryError(f"(Unknown response '{rid}'.)")
    resp = RESPONSES[rid]
    if resp.sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{rid}': too silly to solve the problem.)")
    return resp


def predict(world: World, prop_id: str) -> dict:
    sim = world.copy()
    _do_try(sim, sim.get(prop_id), narrate=False)
    return {
        "tossed": sim.get("hill").meters["tossed"],
        "confusion": sum(e.memes["confusion"] for e in sim.entities.values()),
    }


def _do_try(world: World, prop: Entity, narrate: bool = True) -> None:
    prop.meters["carried"] += 1
    world.get("hill").meters["tossed"] += 1
    propagate(world, narrate=narrate)


def tell(place: Place, prop: Prop, drink: Prop, response: Reaction,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         adult_name: str) -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = w.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = w.add(Entity(id=adult_name, kind="character", type="mother", role="adult"))
    hill = w.add(Entity(id="hill", type="place", label=place.label))
    prop_ent = w.add(Entity(id="prop", type="thing", label=prop.label, phrase=prop.phrase))
    drink_ent = w.add(Entity(id="drink", type="thing", label=drink.label, phrase=drink.phrase))

    hero.memes["bravery"] = 5.0
    friend.memes["curiosity"] = 4.0
    w.facts["place"] = place
    w.facts["prop"] = prop
    w.facts["drink"] = drink
    w.facts["response"] = response

    w.say(
        f"{hero.id} and {friend.id} climbed to {place.label} with a map, a grin, "
        f"and a pocketful of adventure. At the top stood an old observatory, "
        f"and inside it waited {prop.phrase}."
    )
    w.say(
        f"They wanted to explore by the stars, because the night was dark and "
        f"the hill was windy. {prop.label.capitalize()} looked perfect for the quest."
    )

    w.para()
    w.say(
        f'"Let me try it," said {hero.id}. {friend.id} nodded. '
        f'"Try it, try it," {friend.id} said, which was brave and a little bit silly.'
    )
    pred = predict(w, "prop")
    if pred["tossed"] > 0:
        w.say(
            f'"Careful," said {friend.id}, peeking at the roof. '
            f'"The wind likes to pelt things up here. Pelt, pelt, pelt."'
        )
    prop_ent.meters["carried"] += 1
    prop_ent.memes["confusion"] += 1
    _do_try(w, prop_ent)

    w.para()
    w.say(
        f"The wind gave {prop.label} a rude little pelt, pelt, pelt, and the "
        f"astrologic chart skated across the table like a jumpy crab. "
        f"{friend.id} snorted. 'Even the stars are trying to run away,' {friend.id} said."
    )
    w.say(
        f"{hero.id} laughed too, then remembered the plan. {adult.label_word.capitalize()} "
        f"came in with {drink.phrase}, and the room smelled like cedar, paper, and luck."
    )

    contained = response.sense >= SENSE_MIN
    if contained:
        w.say(
            f"{adult.label_word.capitalize()} {response.text.replace('{prop}', prop.label)}."
        )
        w.say(
            f"The chart stopped sliding, the hill stopped rattling, and everyone "
            f"finally got one calm look at the stars."
        )
        w.para()
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1
        w.say(
            f"Then {adult.id} handed out a careful swig of warm cocoa. "
            f"{hero.id} took a swig, then {friend.id} took a swig, and both of them "
            f"made the same surprised face."
        )
        w.say(
            f'"This tastes like victory," said {hero.id}. '
            f'"This tastes like victory and also like a spoon," said {friend.id}.'
        )
        w.say(
            f"They left the observatory with the astrologic chart safe, the pelt "
            f"folded neat, and the stars still shining above them."
        )
        outcome = "contained"
    else:
        w.say(
            f"{adult.label_word.capitalize()} tried to help, but the plan was too weak. "
            f"The chart slid, the lantern tipped, and the windy hill kept pelt-ing the room."
        )
        w.say(
            f"In the end, they had to back away and wait for a better idea."
        )
        outcome = "failed"

    w.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        hill=hill,
        prop_ent=prop_ent,
        drink_ent=drink_ent,
        outcome=outcome,
        contained=contained,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "pelt", "astrologic", and "swig".',
        f"Tell a humorous repeated-action adventure where {f['hero'].id} and {f['friend'].id} visit a windy observatory, use an astrologic chart, and end with a swig of something cozy.",
        f"Write a playful story where the wind keeps saying pelt, pelt, pelt, but the children still finish their starry quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, adult = f["hero"], f["friend"], f["adult"]
    prop, drink = f["prop"], f["drink"]
    qa = [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} and {friend.id} went up the hill together. They explored the observatory as a team and kept each other brave."
        ),
        QAItem(
            question="What did the wind do?",
            answer="The wind kept giving everything a little pelt, pelt, pelt. That repeated bumping made the chart slide and added a funny bit of trouble."
        ),
        QAItem(
            question="What did the grown-up bring?",
            answer=f"{adult.id} brought {drink.phrase}. That gave the children something warm and safe to swig after the windy mess was handled."
        ),
    ]
    if f["contained"]:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"They solved the problem and kept the {prop.label} safe. After that, they enjoyed a calm swig and looked at the stars with smiles."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    qa = [
        QAItem(
            question="What does pelt mean?",
            answer="To pelt something is to hit or toss it quickly, again and again. In a windy story, that can make things bob, rattle, or slide around."
        ),
        QAItem(
            question="What is astrologic about a chart?",
            answer="Astrologic things are about stars and the sky. An astrologic chart helps people look at patterns in the night and imagine what they can find."
        ),
        QAItem(
            question="What does it mean to swig a drink?",
            answer="To swig a drink means to take a big, quick sip. It is a funny word when someone is thirsty and very happy."
        ),
    ]
    return qa


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


PLACES = {
    "hill": Place(id="hill", label="the windy hill", windy=True, dark=True, stars_visible=True),
    "observatory": Place(id="observatory", label="the old observatory", windy=True, dark=True, stars_visible=True),
}

PROPS = {
    "pelt": Prop(id="pelt", label="a fur pelt", phrase="a fur pelt", tags={"pelt", "astrologic"}),
    "chart": Prop(id="chart", label="an astrologic chart", phrase="an astrologic chart", tags={"astrologic"}),
}

DRINKS = {
    "swig": Prop(id="swig", label="a cocoa mug", phrase="a cocoa mug for a warm swig", tags={"swig"}),
    "tea": Prop(id="tea", label="a tea mug", phrase="a tea mug for a careful swig", tags={"swig"}),
}

RESPONSES = {
    "steady": Reaction(
        id="steady",
        sense=3,
        text="set the chart under the heavy pelt and tucked the pelt edges down so the wind could not pelt it away",
        qa_text="set the chart under the heavy pelt and tucked the edges down",
        tags={"astrologic"},
    ),
    "clip": Reaction(
        id="clip",
        sense=2,
        text="clipped the chart to the table and laughed when the clip fought the wind like a tiny dragon",
        qa_text="clipped the chart to the table",
        tags={"astrologic"},
    ),
    "silly": Reaction(
        id="silly",
        sense=1,
        text="waved at the wind and hoped it would behave",
        qa_text="waved at the wind",
        tags={"astrologic"},
    ),
}

GIRL_NAMES = ["Mina", "Iris", "Pia", "Tala", "Nora", "Zoe"]
BOY_NAMES = ["Ari", "Benn", "Kian", "Luca", "Nico", "Owen"]
ADULT_NAMES = ["Mara", "Jon", "Sage", "Rin"]
TRAITS = ["curious", "cheerful", "bold", "quick-thinking"]


def explain_rejection(place: Place, prop: Prop, drink: Prop) -> str:
    return "(No story: this adventure needs the windy dark place, an astrologic thing to fuss over, and a drink for the ending swig.)"


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
at_risk(P) :- prop(P), astrologic(P).
needs_sw ig(D) :- drink(D).
valid(Place, Prop, Drink) :- place(Place), prop(Prop), drink(Drink), dark(Place), at_risk(Prop), needs_sw ig(Drink).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
        if "astrologic" in PROPS[pid].tags:
            lines.append(asp.fact("astrologic", pid))
    for did in DRINKS:
        lines.append(asp.fact("drink", did))
        if "swig" in DRINKS[did].tags:
            lines.append(asp.fact("swig", did))
    for pid, place in PLACES.items():
        if place.dark:
            lines.append(asp.fact("dark", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    if not sample.story.strip():
        print("MISMATCH: story generation failed in smoke test.")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with pelt, astrologic, and swig.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
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
              if (args.place is None or c[0] == args.place)
              and (args.prop is None or c[1] == args.prop)
              and (args.drink is None or c[2] == args.drink)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prop, drink = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    friend_pool = BOY_NAMES if friend_gender == "boy" else GIRL_NAMES
    hero = args.hero or rng.choice(hero_pool)
    friend = args.friend or rng.choice([n for n in friend_pool if n != hero])
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(
        place=place,
        prop=prop,
        drink=drink,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.prop not in PROPS or params.drink not in DRINKS:
        raise StoryError("(Invalid story params.)")
    world = tell(
        PLACES[params.place],
        PROPS[params.prop],
        DRINKS[params.drink],
        choose_response(params.response),
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.adult,
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
    StoryParams(place="observatory", prop="chart", drink="swig", response="steady", hero="Mina", hero_gender="girl", friend="Ari", friend_gender="boy", adult="Mara"),
    StoryParams(place="hill", prop="pelt", drink="tea", response="clip", hero="Luca", hero_gender="boy", friend="Nora", friend_gender="girl", adult="Jon"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
