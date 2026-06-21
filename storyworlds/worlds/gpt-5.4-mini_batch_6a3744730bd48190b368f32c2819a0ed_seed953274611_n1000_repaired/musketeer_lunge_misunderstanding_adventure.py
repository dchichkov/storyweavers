#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/musketeer_lunge_misunderstanding_adventure.py
==============================================================================

A small storyworld for an adventure mishap: a child playing at being a musketeer
makes a reckless lunge, another character misunderstands the move as an attack,
and the muddle is cleared up by a calm explanation and a better plan.

This world is built from a tiny causal model with typed entities, physical
meters, and emotional memes. It includes a Python reasonableness gate plus an
inline ASP twin so the story logic can be checked for parity.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 5.0
UNDERSTANDING_GOAL = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    risk_spot: str
    style: str = "adventure"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    makes_misread: bool = False
    challenge: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Move:
    id: str
    label: str
    verb: str
    risk: int
    recovery: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str = "courtyard"
    prop: str = "cloak"
    move: str = "lunge"
    hero: str = "Nina"
    hero_gender: str = "girl"
    partner: str = "Tomas"
    partner_gender: str = "boy"
    mentor: str = "captain"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "courtyard": Setting("courtyard", "the old courtyard", "stone arches and a cracked fountain", "the narrow path"),
    "bridge": Setting("bridge", "the rope bridge", "windy planks over a deep ravine", "the middle plank"),
    "harbor": Setting("harbor", "the moonlit harbor", "masts and lanterns and a salty breeze", "the dock edge"),
}

PROPS = {
    "cloak": Prop("cloak", "cloak", "a bright red cloak", makes_misread=True, tags={"cloak", "red"}),
    "feather_hat": Prop("feather_hat", "feathered hat", "a feathered hat", makes_misread=True, tags={"hat"}),
    "map": Prop("map", "map", "a folded map", makes_misread=False, tags={"map"}),
}

MOVES = {
    "lunge": Move("lunge", "lunge", "make a lunge", risk=2, recovery="step back and bow", tags={"lunge", "adventure"}),
    "dash": Move("dash", "dash", "dash forward", risk=1, recovery="slow down and explain", tags={"dash"}),
}

GIRL_NAMES = ["Nina", "Maya", "Iris", "Lina", "Sofia", "Ava"]
BOY_NAMES = ["Tomas", "Leo", "Eli", "Arlo", "Milo", "Noah"]
MENTORS = {
    "captain": "the captain",
    "guide": "the guide",
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPS.items():
            for mid, move in MOVES.items():
                if prop.makes_misread and move.risk >= 1:
                    out.append((sid, pid, mid))
    return out


def explain_rejection(setting: Setting, prop: Prop, move: Move) -> str:
    if not prop.makes_misread:
        return f"(No story: {prop.label} does not create the misunderstanding needed for this adventure.)"
    return f"(No story: {move.label} is too mild here; the story needs a clearer mistaken lunge.)"


def predict_misunderstanding(world: World, hero_id: str, partner_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    partner = sim.get(partner_id)
    hero.memes["intent"] += 1
    partner.memes["startled"] += 1
    partner.memes["understanding"] += 0
    return {
        "misread": True,
        "startled": partner.memes["startled"] >= THRESHOLD,
    }


def _do_move(world: World, hero: Entity, partner: Entity, move: Move, prop: Prop, narrate: bool = True) -> None:
    hero.meters["action"] += 1
    hero.memes["boldness"] += 1
    partner.memes["startled"] += 1
    if prop.makes_misread:
        partner.memes["misunderstanding"] += 1
    if narrate:
        world.say(f"{hero.id} moved first, and {partner.id} froze at the sudden motion.")


def explain(world: World, hero: Entity, partner: Entity, mentor: Entity, prop: Prop, move: Move, setting: Setting) -> None:
    partner.memes["understanding"] += 1
    partner.memes["fear"] = 0.0
    world.say(
        f'"Wait," {hero.id} said, lifting {hero.pronoun("possessive")} hands. '
        f'"I only meant to {move.verb} like a musketeer in a play."'
    )
    world.say(
        f"{mentor.label_word.capitalize()} nodded and showed how the red {prop.label} and the fast step "
        f"could look threatening in {setting.place}."
    )


def resolve(world: World, hero: Entity, partner: Entity, mentor: Entity, move: Move, prop: Prop) -> None:
    partner.memes["understanding"] += 1
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'{mentor.label_word.capitalize()} laughed softly, and {partner.id} laughed too. '
        f'The misunderstanding melted away.'
    )
    world.say(
        f"Then {hero.id} did it again, this time by {move.recovery}, and the two of them "
        f"turned it into a safe practice for a true musketeer."
    )


def tell(setting: Setting, prop: Prop, move: Move,
         hero_name: str, hero_gender: str, partner_name: str, partner_gender: str,
         mentor_role: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["brave"]))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", traits=["wary"]))
    mentor = world.add(Entity(id=mentor_role, kind="character", type="adult", label=MENTORS.get(mentor_role, "the grown-up"), role="mentor"))
    world.add(Entity(id="setting", kind="thing", type="place", label=setting.place))
    world.add(Entity(id="prop", kind="thing", type=prop.label))
    hero.memes["bravery"] = BRAVERY_INIT

    world.say(
        f"At {setting.place}, under {setting.detail}, {hero.id} dressed like a musketeer with {prop.phrase}."
    )
    world.say(
        f"{hero.id} wanted adventure and {move.verb}, because the whole place felt like a stage for a daring quest."
    )
    world.para()
    partner.memes["care"] += 1
    world.say(
        f"But when {hero.id} rushed toward the narrow path, {partner.id} misunderstood the move and stepped back at once."
    )
    world.say(
        f'"{partner.id}!" {hero.id} called. "I am not attacking. I am only practicing a musketeer\'s move."'
    )
    world.para()
    explain(world, hero, partner, mentor, prop, move, setting)
    resolve(world, hero, partner, mentor, move, prop)

    world.facts.update(
        hero=hero,
        partner=partner,
        mentor=mentor,
        setting=setting,
        prop=prop,
        move=move,
        misunderstood=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story that includes the words "{f["prop"].label}" and "musketeer" and shows a misunderstanding about a sudden {f["move"].label}.',
        f"Tell a child-friendly adventure where {f['hero'].id} makes a {f['move'].label}, {f['partner'].id} misreads it, and an adult clears up the confusion.",
        f'Write a short story with a mistaken action, a calm explanation, and a brave ending in {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    mentor = f["mentor"]
    prop = f["prop"]
    move = f["move"]
    setting = f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {partner.id}, with {mentor.label_word} helping them sort out a misunderstanding. The adventure starts with a dress-up moment and ends with everyone understanding each other."
        ),
        QAItem(
            question=f"What did {hero.id} do that caused trouble?",
            answer=f"{hero.id} made a {move.label} while wearing {prop.phrase}. It looked sharper and scarier than {hero.id} meant it to look, so {partner.id} thought something bad was happening."
        ),
        QAItem(
            question="How did the misunderstanding get fixed?",
            answer=f"{hero.id} explained the move, and {mentor.label_word} showed why it looked confusing in {setting.place}. That calm explanation helped {partner.id} understand that the motion was part of play, not a real attack."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a musketeer?",
            answer="A musketeer is a sword fighter from adventure stories. In this world, the word means a brave pretend-hero with quick steps and dramatic poses."
        ),
        QAItem(
            question="What does it mean to lunge?",
            answer="To lunge means to make a sudden forward movement. It can look serious or surprising, so people may misunderstand it if they do not know the game."
        ),
        QAItem(
            question="Why can a misunderstanding happen during an adventure game?",
            answer="Adventure games often include fast movement, costumes, and pretend danger. If someone sees only the motion and not the intention, they may think the action is real."
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstood(H, P) :- hero(H), partner(P), prop_misread(PROP), move_risky(MOVE).
resolved(H, P) :- misunderstood(H, P), explain(H, P), mentor(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.makes_misread:
            lines.append(asp.fact("prop_misread", pid))
    for mid, move in MOVES.items():
        lines.append(asp.fact("move", mid))
        if move.risk >= 1:
            lines.append(asp.fact("move_risky", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    # Smoke test ordinary generation first.
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prop=None, move=None, hero=None, hero_gender=None, partner=None, partner_gender=None, mentor=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a musketeer misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=MENTORS)
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
    if args.prop and args.move:
        prop, move = PROPS[args.prop], MOVES[args.move]
        if not prop.makes_misread or move.risk < 1:
            raise StoryError(explain_rejection(SETTINGS[args.setting or "courtyard"], prop, move))
    setting = args.setting or rng.choice(list(SETTINGS))
    prop = args.prop or rng.choice(list(PROPS))
    move = args.move or rng.choice(list(MOVES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != hero])
    mentor = args.mentor or rng.choice(list(MENTORS))
    if (setting, prop, move) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(setting=setting, prop=prop, move=move, hero=hero, hero_gender=hero_gender, partner=partner, partner_gender=partner_gender, mentor=mentor)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.prop not in PROPS or params.move not in MOVES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(SETTINGS[params.setting], PROPS[params.prop], MOVES[params.move],
                 params.hero, params.hero_gender, params.partner, params.partner_gender,
                 params.mentor)
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
    StoryParams(setting="courtyard", prop="cloak", move="lunge", hero="Nina", hero_gender="girl", partner="Tomas", partner_gender="boy", mentor="captain"),
    StoryParams(setting="bridge", prop="feather_hat", move="lunge", hero="Leo", hero_gender="boy", partner="Maya", partner_gender="girl", mentor="guide"),
    StoryParams(setting="harbor", prop="cloak", move="dash", hero="Ava", hero_gender="girl", partner="Milo", partner_gender="boy", mentor="captain"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for combo in valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
