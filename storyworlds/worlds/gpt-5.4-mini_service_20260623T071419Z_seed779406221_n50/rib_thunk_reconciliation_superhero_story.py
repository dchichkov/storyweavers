#!/usr/bin/env python3
"""
rib_thunk_reconciliation_superhero_story.py

A small superhero storyworld about a young hero, a teammate mistake, a loud thunk,
and a reconciliation that repairs the team before the next rescue.
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



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict = field(default_factory=dict)
    memes: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    gadget: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Team:
    place: str
    setting: str
    afford: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Move:
    id: str
    verb: str
    noise: str
    impact: str
    mess: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    restore: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, team: Team) -> None:
        self.team = team
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


MOVES = {
    "dash": Move(id="dash", verb="dash through the alley", noise="thunk", impact="rib", mess="dusty", zone={"torso", "legs"}, tags={"thunk", "rib"}),
    "flip": Move(id="flip", verb="flip over the rooftop rail", noise="thunk", impact="rib", mess="scraped", zone={"torso", "arms"}, tags={"thunk", "rib"}),
    "rescue": Move(id="rescue", verb="pull the fallen sign clear", noise="thunk", impact="rib", mess="dusty", zone={"torso", "arms"}, tags={"thunk", "rib"}),
}

GEAR = {
    "shield": Gear(id="shield", label="the shield brace", covers={"torso"}, guards={"dusty", "scraped"}, offer="put on the shield brace", restore="restored the shield brace and tried again", tags={"shield"}),
    "pads": Gear(id="pads", label="padded gloves", covers={"arms"}, guards={"scraped"}, offer="grab the padded gloves", restore="put on the padded gloves", tags={"pads"}),
    "cape": Gear(id="cape", label="the rescue cape", covers={"torso", "arms"}, guards={"dusty", "scraped"}, offer="wear the rescue cape", restore="fastened the rescue cape", tags={"cape"}),
}

PLACES = {
    "rooftop": Team(place="the rooftop", setting="bright city rooftop", afford={"dash", "flip", "rescue"}),
    "alley": Team(place="the alley", setting="narrow city alley", afford={"dash", "rescue"}),
    "bridge": Team(place="the sky bridge", setting="windy sky bridge", afford={"dash", "flip", "rescue"}),
}

HEROES = [("Nova", "girl"), ("Bolt", "boy"), ("Spark", "girl"), ("Comet", "boy")]
HELPERS = [("Mira", "girl"), ("Jett", "boy"), ("Piper", "girl"), ("Ray", "boy")]
TRAITS = ["brave", "quick", "careful", "bold"]

CURATED = [
    None,
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, team in PLACES.items():
        for move_id, mv in MOVES.items():
            if move_id not in team.afford:
                continue
            for gear_id, gear in GEAR.items():
                if mv.mess in gear.guards:
                    out.append((place, move_id, gear_id))
    return out


@dataclass
class StoryParams:
    place: str
    move: str
    gear: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with rib, thunk, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "move", None) is None or c[1] == getattr(args, "move", None))
              and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, move, gear = rng.choice(list(combos))
    hero, hg = (getattr(args, "hero", None), getattr(args, "hero_gender", None)) if getattr(args, "hero", None) and getattr(args, "hero_gender", None) else rng.choice(HEROES)
    helper, kg = (getattr(args, "helper", None), getattr(args, "helper_gender", None)) if getattr(args, "helper", None) and getattr(args, "helper_gender", None) else rng.choice(HELPERS)
    if hero == helper:
        helper, kg = next((n, g) for n, g in HELPERS if n != hero)
    return StoryParams(place=place, move=move, gear=gear, hero=hero, hero_gender=hg, helper=helper, helper_gender=kg, trait=rng.choice(TRAITS))


def can_reconcile(world: World, hero: Entity, helper: Entity) -> bool:
    return hero.memes.get("hurt", 0.0) >= THRESHOLD and helper.memes.get("sorry", 0.0) >= THRESHOLD


def tell(team: Team, mv: Move, gear: Gear, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str, trait: str) -> World:
    world = World(team)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", attrs={"trait": trait}, meters={}, memes={"joy": 0.0, "hurt": 0.0, "trust": 0.0}, tags={"hero"}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", attrs={}, meters={}, memes={"sorry": 0.0, "trust": 0.0}, tags={"helper"}))
    gadget = world.add(Entity(id="gear", kind="thing", type="gear", label=gear.label, attrs={}, meters={}, memes={}, tags=gear.tags))
    world.facts.update(hero=hero, helper=helper, move=mv, gear=gear, team=team, gadget=gadget)

    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{hero_name} was a {trait} superhero who loved saving the day in {team.setting}.")
    world.say(f"{helper_name} flew beside {hero_name}, and together they watched the city lights blink like stars.")
    world.say(f"Then {hero_name} tried to {mv.verb}, and the air answered with a loud {mv.noise}.")
    world.para()

    hero.meters["impact"] = 1.0
    hero.meters[mv.impact] = 1.0
    hero.memes["hurt"] += 1
    helper.memes["sorry"] += 1
    world.say(f"The {mv.impact} hit hard, and {hero_name} felt a sting along {hero.pronoun('possessive')} side.")
    world.say(f"{helper_name} gasped and hurried over, because a hero can be hurt even during a rescue.")
    world.para()

    hero.memes["angry"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(f"{hero_name} scowled, but {helper_name} lowered {helper.pronoun('possessive')} voice and said sorry right away.")
    world.say(f"{helper_name} offered {gear.offer}, saying it would help the next move stay safe.")
    if mv.mess in gear.guards:
        hero.memes["trust"] += 1
        helper.memes["trust"] += 1
        hero.memes["hurt"] = 0.0
        helper.memes["sorry"] += 1
        world.para()
        world.say(f"{hero_name} took a breath, nodded, and accepted the help.")
        world.say(f"That was the reconciliation: {hero_name} forgave {helper_name}, and {helper_name} listened instead of arguing.")
        world.say(f"After that, {helper_name} {gear.restore}, and the two teammates finished the rescue side by side.")
    else:
        pass
    world.facts["reconciled"] = can_reconcile(world, hero, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child about {f["hero"].id} and {f["helper"].id} in {f["team"].setting} that includes the words "rib" and "thunk".',
        f"Tell a gentle superhero story where {f['hero'].id} gets a rib bruise with a thunk, then {f['helper'].id} says sorry and they reconcile.",
        f"Write a story about a small hero team, a loud thunk, a sore rib, and a reconciliation that lets them finish the rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, mv, gear = f["hero"], f["helper"], f["move"], f["gear"]
    return [
        QAItem(question=f"Who was the story about?", answer=f"It was about {hero.id} and {helper.id}, two superheroes who worked together in {f['team'].setting}."),
        QAItem(question=f"What happened when {hero.id} tried to {mv.verb}?", answer=f"A loud {mv.noise} sounded, {hero.id} got a sore rib, and the move hurt more than expected."),
        QAItem(question=f"What did {helper.id} do after the mistake?", answer=f"{helper.id} said sorry, offered {gear.label}, and helped make things right."),
        QAItem(question=f"How did the teammates fix the problem?", answer=f"They reconciled. {hero.id} forgave {helper.id}, accepted the help, and they finished the rescue together."),
    ]


WORLD_KNOWLEDGE = {
    "rib": [("What is a rib?", "A rib is one of the bones in your chest that helps protect your body.")],
    "thunk": [("What does thunk mean?", "Thunk is a heavy, dull sound, like something bumping hard against the floor or wall.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation means making up after a disagreement and becoming friends or teammates again.")],
    "hero": [("What is a superhero?", "A superhero is a brave character who helps people and solves problems.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["rib"] + WORLD_KNOWLEDGE["thunk"] + WORLD_KNOWLEDGE["reconciliation"] + WORLD_KNOWLEDGE["hero"]]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs} tags={sorted(e.tags)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,G) :- place(P), move(M), gear(G), afford(P,M), guards(G, dusty), guards(G, scraped).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, team in PLACES.items():
        lines.append(asp.fact("place", p))
        for m in sorted(team.afford):
            lines.append(asp.fact("afford", p, m))
    for m_id, mv in MOVES.items():
        lines.append(asp.fact("move", m_id))
        lines.append(asp.fact("mess", m_id, mv.mess))
    for g_id, gear in GEAR.items():
        lines.append(asp.fact("gear", g_id))
        for x in sorted(gear.guards):
            lines.append(asp.fact("guards", g_id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("ASP mismatch with valid_combos()")
        return 1
    print("OK: ASP matches valid_combos()")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(MOVES, params.move), GEAR[params.gear], params.hero, params.hero_gender, params.helper, params.helper_gender, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for item in sample.prompts:
            print(item)
        print()
        for q in sample.story_qa:
            print("Q:", q.question)
            print("A:", q.answer)
        print()
        for q in sample.world_qa:
            print("Q:", q.question)
            print("A:", q.answer)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        for p in valid_combos():
            params = StoryParams(place=p[0], move=p[1], gear=p[2], hero="Nova", hero_gender="girl", helper="Jett", helper_gender="boy", trait="brave")
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
