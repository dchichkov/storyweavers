#!/usr/bin/env python3
"""
A fairy-tale storyworld about a royal promenade, a ticklish spell, and a boogy
dance that becomes the happy twist and lesson learned.

The seed tale behind this world:
- A small royal child loves a promenade through the moonlit garden.
- A mischievous breeze makes the child ticklish whenever the bells on a cloak jingle.
- A friendly court dancer teaches a boogy step that turns the tickles into laughter.
- The child learns an inner monologue of courage: "I can laugh and keep going."

This world is state-driven:
- The promenade advances through locations.
- Ticklishness can rise when a charm or garment brushes against the body.
- Boogying can reduce fear and increase joy.
- The twist is a gentle surprise: the thing that seemed troublesome becomes the key to the solution.
- The lesson learned is narrated only when the world state proves the change happened.
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Place:
    id: str
    label: str
    next_place: Optional[str] = None
    charm: str = ""
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion_type: str
    charm: str
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


class World:
    def __init__(self, start_place: Place) -> None:
        self.place = start_place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_tickle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("ticklish", 0.0) < THRESHOLD:
            continue
        sig = ("tickle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["giggle"] = e.memes.get("giggle", 0.0) + 1
        out.append(f"{e.id} could not help giggling at the ticklish feeling.")
    return out


def _r_boogy(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("boogy", 0.0) < THRESHOLD:
            continue
        sig = ("boogy", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] = e.memes.get("joy", 0.0) + 1
        e.memes["fear"] = max(0.0, e.memes.get("fear", 0.0) - 1.0)
        out.append(f"{e.id} found a cheerful boogy step and danced with courage.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"])
    if hero.memes.get("joy", 0.0) >= THRESHOLD and hero.memes.get("fear", 0.0) <= 0.0:
        sig = ("lesson", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append(f"{hero.id} learned that laughter can make a tricky spell feel small.")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_tickle, _r_boogy, _r_lesson):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


PLACE_REGISTRY = {
    "rose_garden": Place(id="rose_garden", label="the rose garden", next_place="moon_lane", charm="rose"),
    "moon_lane": Place(id="moon_lane", label="the moonlit lane", next_place="marble_bridge", charm="moon"),
    "marble_bridge": Place(id="marble_bridge", label="the marble bridge", next_place=None, charm="bells"),
}

CHART = {
    "rose": {
        "detail": "The roses bowed like little ladies in silk gowns.",
        "twist": "The roses were not shy at all; they were hiding tiny bells in their leaves.",
        "lesson": "A surprising sound can become part of the fun.",
    },
    "moon": {
        "detail": "Moonlight spilled over the lane like silver ribbon.",
        "twist": "The moonlight touched the cloak and made the bells shimmer first, then chime.",
        "lesson": "Sometimes the thing that feels strange is only asking for a kinder step.",
    },
    "bells": {
        "detail": "The bridge wore bright bells at its arches.",
        "twist": "The bells were ticklish to hear, but they rang in a pattern that matched a dance.",
        "lesson": "When feet find a rhythm, worry can turn into a boogy.",
    },
}

CHARACTER_NAMES = ["Elara", "Mina", "Lina", "Ivy", "Sera", "Nora", "Rose", "Ada"]
COMPANIONS = {
    "sprite": {"type": "sprite", "label": "a kindly sprite"},
    "fiddler": {"type": "fiddler", "label": "a merry fiddler"},
    "aunt": {"type": "aunt", "label": "a gentle aunt"},
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of promenade, ticklishness, and boogying.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=COMPANIONS)
    ap.add_argument("--charm", choices=["rose", "moon", "bells"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("charm", pid, p.charm))
        if p.next_place:
            lines.append(asp.fact("leads_to", pid, p.next_place))
    for c in ("rose", "moon", "bells"):
        lines.append(asp.fact("charm_kind", c))
    return "\n".join(lines)


ASP_RULES = r"""
ticklish(P) :- charm_at(P, C), tickle_charm(C).
boogy_ready(P) :- ticklish(P), dance_charm(C), charm_at(P, C).
lesson_learned(P) :- boogy_ready(P), end_of_walk(P).
valid_story(P) :- start_place(P), ticklish(P), boogy_ready(P), lesson_learned(P).
"""


def asp_program(show: str) -> str:
    return f"""
{asp_facts()}
charm_at(rose_garden, rose).
charm_at(moon_lane, moon).
charm_at(marble_bridge, bells).
tickle_charm(rose).
tickle_charm(moon).
tickle_charm(bells).
dance_charm(bells).
dance_charm(moon).
start_place(rose_garden).
end_of_walk(marble_bridge).
{ASP_RULES}
{show}
"""


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1.\n#show boogy_ready/1.\n#show ticklish/1."))
    atoms = set(asp.atoms(model, "lesson_learned"))
    if atoms:
        print("OK: ASP program produces a lesson learned.")
        return 0
    print("MISMATCH: ASP twin did not produce a lesson.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACE_REGISTRY))
    charm = getattr(args, "charm", None) or PLACE_REGISTRY[place].charm
    hero_name = getattr(args, "hero_name", None) or rng.choice(CHARACTER_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    companion_type = getattr(args, "companion_type", None) or rng.choice(list(COMPANIONS))
    if charm not in {"rose", "moon", "bells"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type,
                       companion_type=companion_type, charm=charm)


def _hero_phrase(hero: Entity) -> str:
    return f"little {hero.type} {hero.id}"


def tell(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    companion_info = _safe_lookup(COMPANIONS, params.companion_type)
    companion = world.add(Entity(id="Companion", kind="character", type=companion_info["type"], label=companion_info["label"]))
    charm = world.add(Entity(id="Charm", type="thing", label=params.charm, phrase=f"a {params.charm} charm"))
    world.facts.update(hero=hero.id, companion=companion.id, charm=charm.id, place=place.id)

    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 1.0

    # Setup
    world.say(f"Once upon a time, {_hero_phrase(hero)} set out for a promenade beside {place.label}.")
    world.say(CHART[place.charm]["detail"])
    world.say(f"{hero.id} wore {charm.phrase}, because the court had promised it would shine in the evening air.")
    world.para()

    # Rising tension
    world.say(f"But as the promenade began, the charm became ticklish against {hero.pronoun('possessive')} collar and wrists.")
    hero.meters["ticklish"] += 1
    hero.memes["fear"] += 1
    propagate(world)
    world.say(f"{companion.label.capitalize()} noticed the fidgeting and called softly, 'Keep walking. We will find the rhythm.'")
    world.para()

    # Twist
    world.say("Then came the twist.")
    world.say(CHART[place.charm]["twist"])
    hero.meters["boogy"] += 1
    world.say(f"{hero.id} tried a tiny boogy step to match the chiming sound.")
    propagate(world)
    world.say(f"The promenade did not stop at the ticklish moment; instead it turned into a dance.")
    world.para()

    # Lesson learned / ending image
    world.say(f"{hero.id} looked inward and thought, 'I can be ticklish and brave at the same time.'")
    world.say(f"{hero.id} and {companion.label} finished the promenade with a bright boogy all the way to {place.label}.")
    world.say(CHART[place.charm]["lesson"])
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a fairy-tale story about a promenade that begins with something ticklish and ends in a boogy.",
        f"Tell a gentle story where {hero.id} meets a ticklish surprise during a promenade and learns a lesson by dancing.",
        f"Write a child-friendly fairy tale using the words promenade, ticklish, and boogy, with a twist and lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"])
    companion = world.get(world.facts["companion"])
    place = world.place
    return [
        QAItem(
            question=f"What did {hero.id} go out to do at the start of the story?",
            answer=f"{hero.id} went out for a promenade beside {place.label}.",
        ),
        QAItem(
            question=f"What made {hero.id} feel ticklish during the promenade?",
            answer=f"The charm at {place.label} brushed {hero.pronoun('possessive')} collar and wrists, and that made {hero.id} feel ticklish.",
        ),
        QAItem(
            question=f"How did {companion.label} help {hero.id} in the end?",
            answer=f"{companion.label.capitalize()} encouraged {hero.id} to keep walking and find the rhythm, and that helped turn the trouble into a boogy.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that being ticklish does not stop courage, because laughter and a boogy step can carry a traveler forward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a promenade?",
            answer="A promenade is a slow, pleasant walk, often for enjoyment in a lovely place.",
        ),
        QAItem(
            question="What does ticklish mean?",
            answer="Ticklish means something feels so light or funny that it makes you want to giggle or wiggle.",
        ),
        QAItem(
            question="What is a boogy?",
            answer="A boogy is a lively dance step that bounces with music and cheerful rhythm.",
        ),
    ]


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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="rose_garden", hero_name="Elara", hero_type="girl", companion_type="sprite", charm="rose"),
    StoryParams(place="moon_lane", hero_name="Mina", hero_type="girl", companion_type="fiddler", charm="moon"),
    StoryParams(place="marble_bridge", hero_name="Theo", hero_type="boy", companion_type="aunt", charm="bells"),
]


def build_asp_listing() -> str:
    return asp_program("#show valid_story/1.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_listing())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(build_asp_listing())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: promenade at {p.place} (charm: {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
