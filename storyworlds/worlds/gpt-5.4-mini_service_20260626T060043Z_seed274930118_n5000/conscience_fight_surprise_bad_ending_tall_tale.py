#!/usr/bin/env python3
"""
A tall-tale story world about a stubborn fight, a noisy conscience, a surprise,
and a bad ending.

This world is intentionally small and classical: one hero, one warning voice,
one argument, and one surprise that turns the ending sour. The prose is driven
by a simulated world model, not a template swap.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
            keys = [upper, upper + "S", upper + "ES"]
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
    phrase: str = ""
    owner: Optional[str] = None
    wore: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    rival: object | None = None
    def __post_init__(self) -> None:
        for key in ["dust", "bruise", "broken", "distance", "weight"]:
            self.meters.setdefault(key, 0.0)
        for key in ["fear", "worry", "anger", "shame", "pride", "relief", "guilt"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "uncle", "cowboy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

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
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "fair": Setting(
        place="the county fair",
        detail="The ferris wheel turned slow and high, and every booth in the rows of tents had a loud grin.",
        affords={"fight"},
    ),
    "station": Setting(
        place="the rail station",
        detail="The boards were hot from the sun, and the train whistle could be heard way off like a long horn.",
        affords={"fight"},
    ),
    "ridge": Setting(
        place="the windy ridge",
        detail="The grass leaned one way and the clouds leaned another, as if the whole world had a mind to argue.",
        affords={"fight"},
    ),
}

HEROES = [
    ("Hank", "boy"),
    ("Mose", "boy"),
    ("Ruby", "girl"),
    ("June", "girl"),
    ("Jed", "boy"),
]

RIVALS = [
    ("Big Ike", "boy"),
    ("Slant Jim", "boy"),
    ("Bellie Bea", "girl"),
    ("Tumble Tom", "boy"),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def tall_tale_detail(hero: Entity) -> str:
    return f"{hero.id} was so stubborn that even the dust around {hero.pronoun('possessive')} boots seemed to stand up straighter."


def conscience_line(hero: Entity) -> str:
    return f"A little voice called conscience lived in {hero.pronoun('possessive')} chest and never whispered; it always sounded like a dinner bell."


def set_up_fight(world: World, hero: Entity, rival: Entity) -> None:
    world.say(f"At {world.setting.place}, {hero.id} met {rival.id}, who bragged as big as a thundercloud.")
    world.say(tall_tale_detail(hero))
    world.say(conscience_line(hero))
    world.say(f"{hero.id} wanted to prove {hero.pronoun('subject')} was the roughest hand in the place, but conscience said, \"Don't start a fight you don't need.\"")
    hero.memes["pride"] += 1
    hero.memes["worry"] += 1
    rival.memes["anger"] += 1
    world.facts["warned"] = True


def surprise_turn(world: World, hero: Entity, rival: Entity) -> None:
    world.say(f"Then came the surprise: {rival.id} showed a torn satchel and hollered that {hero.id} had stepped on his only map and cracked the glass inside.")
    world.say(f"Everybody in the crowd gasped so hard the popcorn forgot to pop.")
    hero.memes["shame"] += 1
    hero.memes["fear"] += 1
    world.facts["surprise"] = True


def fight_scene(world: World, hero: Entity, rival: Entity) -> None:
    hero.memes["anger"] += 1
    rival.memes["anger"] += 1
    hero.meters["dust"] += 1
    rival.meters["dust"] += 1
    world.say(f"{hero.id} ignored conscience and started the fight anyway.")
    world.say(f"They tangled up like two fishhooks in a pocket, and the dust rose so high it made a little brown cloud over their heads.")
    world.say(f"{rival.id} shoved first, and {hero.id} shoved back, and neither one of them looked wise enough to stop.")
    world.facts["fight"] = True


def bad_ending(world: World, hero: Entity, rival: Entity) -> None:
    hero.meters["bruise"] += 1
    hero.memes["shame"] += 2
    hero.memes["guilt"] += 1
    rival.memes["pride"] += 1
    world.say(f"In the end, {hero.id} lost the fight and came away with a sore jaw and a torn sleeve.")
    world.say(f"The sheriff made both of them sweep the boardwalk while the crowd watched the sunset and shook their heads.")
    world.say(f"{hero.id}'s conscience finally quieted down, but only because {hero.id} was too tired to answer it.")
    world.say(f"When the lanterns blinked on, {hero.id} walked home with dust on {hero.pronoun('possessive')} hat and a bad feeling that stuck like tar.")
    world.facts["bad_ending"] = True


def tell(setting: Setting, hero_name: str, hero_type: str, rival_name: str, rival_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type))
    world.facts.update(hero=hero, rival=rival, setting=setting)

    world.say(f"Once, at {setting.place}, there was a {hero_type} named {hero_name} and a troublemaker named {rival_name}.")
    world.say(setting.detail)
    world.para()

    set_up_fight(world, hero, rival)
    world.para()

    surprise_turn(world, hero, rival)
    fight_scene(world, hero, rival)
    world.para()

    bad_ending(world, hero, rival)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "fight" not in setting.affords:
            continue
        for hero_name, hero_type in HEROES:
            for rival_name, rival_type in RIVALS:
                if hero_type != rival_type:
                    combos.append((place, hero_name, rival_name))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only tells a tall-tale fight when the setting can plausibly hold the dust-up.)"


def choose_names(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str, str]:
    hero_name, hero_type = rng.choice(HEROES)
    rival_name, rival_type = rng.choice(RIVALS)
    if getattr(args, "hero_name", None):
        hero_name = getattr(args, "hero_name", None)
    if getattr(args, "hero_type", None):
        hero_type = getattr(args, "hero_type", None)
    if getattr(args, "rival_name", None):
        rival_name = getattr(args, "rival_name", None)
    if getattr(args, "rival_type", None):
        rival_type = getattr(args, "rival_type", None)
    return hero_name, hero_type, rival_name, rival_type


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: conscience, fight, surprise, bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--rival-name")
    ap.add_argument("--rival-type", choices=["boy", "girl"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name, hero_type, rival_name, rival_type = choose_names(rng, args)
    if hero_type == rival_type:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type,
                       rival_name=rival_name, rival_type=rival_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a tall tale about a conscience that warns a hotheaded child not to start a fight.",
        f"Tell a dusty, child-friendly tall tale set at {f['setting'].place} with a surprise and a bad ending.",
        f"Write a short story where {f['hero'].id} ignores conscience, gets into a fight, and things go wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    rival: Entity = _safe_fact(world, world.facts, "rival")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, world.facts, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id}, who met {rival.id} at {setting.place}.",
        ),
        QAItem(
            question=f"What did conscience warn {hero.id} not to do?",
            answer=f"Conscience warned {hero.id} not to start a fight.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {rival.id} said {hero.id} had damaged a map and cracked the glass inside a satchel.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended badly: {hero.id} lost the fight, got bruised, and had to go home feeling ashamed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a conscience?",
            answer="A conscience is the part of you that helps you know when something feels wrong or unkind.",
        ),
        QAItem(
            question="What is a fight?",
            answer="A fight is a rough argument or tussle where people hurt each other instead of solving the problem with words.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect and did not see coming.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when a story finishes with things going wrong or feeling sad instead of working out well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fair", hero_name="Hank", hero_type="boy", rival_name="Big Ike", rival_type="boy"),
    StoryParams(place="station", hero_name="Ruby", hero_type="girl", rival_name="Slant Jim", rival_type="boy"),
    StoryParams(place="ridge", hero_name="June", hero_type="girl", rival_name="Bellie Bea", rival_type="girl"),
]


ASP_RULES = r"""
place(P) :- setting(P).
compatible(P,H,R) :- place(P), hero(H), rival(R), different(H,R), affords(P,fight).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for h, t in HEROES:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("hero_type", h, t))
    for r, t in RIVALS:
        lines.append(asp.fact("rival", r))
        lines.append(asp.fact("rival_type", r, t))
    for h, ht in HEROES:
        for r, rt in RIVALS:
            if ht != rt:
                lines.append(asp.fact("different", h, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.hero_name, params.hero_type, params.rival_name, params.rival_type)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible tall-tale combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} vs {p.rival_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
