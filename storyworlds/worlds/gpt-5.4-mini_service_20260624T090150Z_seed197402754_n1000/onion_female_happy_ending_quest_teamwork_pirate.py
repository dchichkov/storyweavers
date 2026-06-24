#!/usr/bin/env python3
"""
A tiny pirate storyworld: a female crewmate, an onion quest, teamwork, and a
happy ending.

The simulated premise:
- A young female pirate has a problem: her crew needs a special onion for soup.
- The onion is hidden on a small island.
- The journey starts with worry, turns into teamwork, and ends with a warm meal
  and a cheerful deckside scene.

The state model tracks:
- Physical meters: distance, soggy, tired, onion_found, soup_ready
- Emotional memes: hope, worry, teamwork, joy, pride
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
    gender: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crew: object | None = None
    heroine: object | None = None
    onion: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.gender == "female":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.gender == "male":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    name: str
    harbor: str
    island: str
    weather: str = "breezy"
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
class Goal:
    id: str
    item: str
    place: str
    reason: str
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
    setting: str
    goal: str
    heroine: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "harbor": Setting(name="the harbor", harbor="the harbor", island="the little onion isle"),
    "cove": Setting(name="the cove", harbor="the cove", island="the onion rock"),
}

GOALS = {
    "soup_onion": Goal(id="soup_onion", item="onion", place="the island garden", reason="make supper for the crew"),
}

HEROINES = [
    "Mara", "Nell", "Ava", "Rosa", "Ivy", "Lina",
]

TRAITS = ["brave", "cheerful", "clever", "kind", "spry"]


def bad_reason(setting: Setting, goal: Goal) -> Optional[str]:
    if goal.item != "onion":
        return "This storyworld only supports an onion quest."
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about an onion quest and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--heroine", choices=HEROINES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    goal = getattr(args, "goal", None) or rng.choice(list(GOALS))
    heroine = getattr(args, "heroine", None) or rng.choice(HEROINES)
    setting_obj = _safe_lookup(SETTINGS, setting)
    goal_obj = _safe_lookup(GOALS, goal)
    why = bad_reason(setting_obj, goal_obj)
    if why:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, goal=goal, heroine=heroine)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("harbor", sid, s.harbor))
        lines.append(asp.fact("island", sid, s.island))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("needs", gid, g.item))
        lines.append(asp.fact("at", gid, g.place))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, G) :- setting(S), goal(G), needs(G, onion).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    expected = sorted((sid, gid) for sid in SETTINGS for gid in GOALS)
    if found == expected:
        print(f"OK: ASP matches Python ({len(found)} stories).")
        return 0
    print("MISMATCH")
    print("asp:", found)
    print("py :", expected)
    return 1


def story_knowledge() -> list[QAItem]:
    return [
        QAItem(
            question="What is an onion?",
            answer="An onion is a round vegetable that can make soup taste strong and savory.",
        ),
        QAItem(
            question="Why do pirate crews work together?",
            answer="Pirate crews work together so they can steer the ship, solve problems, and keep everyone safe.",
        ),
    ]


def generate_story(world: World) -> None:
    heroine = world.get("heroine")
    goal = _safe_fact(world, world.facts, "goal")
    helper = world.get("crew")
    onion = world.get("onion")

    world.say(
        f"On {world.setting.name}, {heroine.pronoun('subject').capitalize()} "
        f"was a {world.facts['trait']} female pirate named {heroine.id}."
    )
    world.say(
        f"The crew had one big wish: they needed an onion to {goal.reason}."
    )
    world.say(
        f"But the only onion grew far away, past the harbor and onto {world.setting.island}."
    )

    world.para()
    heroine.memes["hope"] += 1
    heroine.memes["worry"] += 1
    world.say(
        f"{heroine.id} looked at the boat and said, "
        f'"We can do this, but we must do it together."'
    )
    helper.memes["teamwork"] += 1
    world.say(
        f"The first mate tied the rope, the sailor raised the sail, and {heroine.id} took the helm."
    )

    world.para()
    heroine.meters["distance"] += 1
    helper.meters["distance"] += 1
    onion.meters["found"] += 1
    world.say(
        f"They sailed to {world.setting.island}, climbed a windy path, and found the onion hiding in a small patch of dirt."
    )
    heroine.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{heroine.id} lifted it high and laughed, because the quest was not about one pirate alone."
    )

    world.para()
    world.facts["soup_ready"] = True
    heroine.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Back at {world.setting.harbor}, the crew cooked the onion into soup."
    )
    world.say(
        f"They shared the warm bowls under the stars, and {heroine.id} smiled at the happy ending."
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    goal = _safe_lookup(GOALS, params.goal)
    world = World(setting)
    heroine = world.add(Entity(
        id=params.heroine,
        kind="character",
        type="pirate",
        label="female pirate",
        gender="female",
        meters={"distance": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "teamwork": 0.0, "joy": 0.0, "pride": 0.0},
    ))
    crew = world.add(Entity(
        id="crew",
        kind="character",
        type="crew",
        label="the crew",
        gender="neutral",
        meters={"distance": 0.0},
        memes={"teamwork": 1.0, "joy": 0.0, "pride": 0.0},
    ))
    onion = world.add(Entity(
        id="onion",
        type="onion",
        label="onion",
        phrase="a shiny onion",
        meters={"found": 0.0},
        memes={},
    ))
    world.facts.update(
        setting=setting,
        goal=goal,
        heroine=heroine,
        crew=crew,
        onion=onion,
        trait=random.choice(TRAITS),
        soup_ready=False,
    )
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=story_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    heroine = _safe_fact(world, world.facts, "heroine")
    goal = _safe_fact(world, world.facts, "goal")
    return [
        f'Write a short pirate story for young children about {heroine.id} and an onion quest.',
        f"Tell a story where a female pirate needs an onion to {goal.reason} and gets help from the crew.",
        "Write a happy pirate tale about teamwork, a boat, and a found onion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    heroine = _safe_fact(world, world.facts, "heroine")
    goal = _safe_fact(world, world.facts, "goal")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"What did {heroine.id} want to find?",
            answer=f"{heroine.id} wanted to find an onion so the crew could {goal.reason}.",
        ),
        QAItem(
            question="Who helped on the quest?",
            answer="The crew helped by tying the rope, raising the sail, and steering the boat together.",
        ),
        QAItem(
            question=f"Where did they find the onion?",
            answer=f"They found the onion on {setting.island}, after sailing out from {setting.harbor}.",
        ),
        QAItem(
            question=f"How did the story end for {heroine.id}?",
            answer=f"It ended happily, with the crew sharing warm onion soup and smiling together.",
        ),
    ]


def story_knowledge_qa(world: World) -> list[QAItem]:
    return story_knowledge()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        lines.append(
            f"{ent.id}: meters={dict(ent.meters)} memes={dict(ent.memes)}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(setting="harbor", goal="soup_onion", heroine="Mara"),
    StoryParams(setting="cove", goal="soup_onion", heroine="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            header = f"### {sample.params.heroine} at {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
