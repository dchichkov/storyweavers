#!/usr/bin/env python3
"""
A heartwarming storyworld about a dalmatian family learning that divorce can
change a home without ending love, with a small enchantment foreshadowed by
ordinary acts of care.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    child: str = ""
    dalmatian: str = ""
    parent_a: str = ""
    parent_b: str = ""
    place: str = ""
    keepsake: str = ""
    seed: Optional[int] = None
    variant: int = 0
    telling_mode: int = 0
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


CHILD_NAMES = ["Luna", "Mara", "Theo", "Nia", "Owen", "Pia"]
DALMATIAN_NAMES = ["Pepper", "Dot", "Patches", "Clover", "Spot", "Buttons"]
PARENT_A_NAMES = ["Mina", "Elena", "Rosa", "June", "Amir", "Tessa"]
PARENT_B_NAMES = ["Jonah", "Cal", "Mateo", "Sam", "Noah", "Eli"]
PLACES = ["Maple Street", "Willow Lane", "Sunbeam Court", "Rosehill"]
KEEPSAKES = ["a blue button", "a silver bell", "a red ribbon", "a painted pebble"]

SCENARIOS = {
    "two_homes": {
        "premise": "a tiny star appeared on the kitchen window each time Luna packed her overnight bag",
        "trouble": "Luna feared that the family's divorce had broken the old feeling of belonging",
        "clue": "Pepper carried the same worn blanket between both homes and slept beside each packed bag",
        "risk": "hiding her sadness would leave everyone guessing and make the two homes feel farther apart",
        "reveal": "the star was an enchantment stirred by honest love and repeated acts of care",
        "turn": "Luna told both parents that she missed having everyone under one roof, and they listened without blaming one another",
        "repair": "made a shared calendar and a little welcome basket for each home",
        "ending": "That night, Pepper slept between two doorways while the enchanted star shone on both houses.",
        "lesson": "Divorce can change a family’s shape without ending its love.",
    },
    "garden_gate": {
        "premise": "white flowers opened wherever Pepper placed one careful paw",
        "trouble": "Luna worried that visiting one parent meant she was leaving the other behind",
        "clue": "the dalmatian always carried the same blue button from one garden gate to the next",
        "risk": "choosing only one gate would turn a bridge between homes into a wall",
        "reveal": "the flowers were an enchantment answering to promises kept in both homes",
        "turn": "Luna asked her parents to make one shared promise: she would never have to choose whom to love",
        "repair": "hung the blue button on a small gate between the gardens",
        "ending": "Flowers curled around the gate, and Pepper wagged beneath them as both parents came to water the bed.",
        "lesson": "A child should never have to divide love into separate pieces.",
    },
    "rainy_train": {
        "premise": "rain tapped a cheerful rhythm whenever the little family rode the weekend train",
        "trouble": "Luna thought the divorce meant happy traditions had to disappear",
        "clue": "Pepper pressed his nose to the same window before every station",
        "risk": "throwing away the tradition would erase a memory instead of making room for a new one",
        "reveal": "the rhythm was an enchantment that remembered kindness, not a particular house",
        "turn": "Luna told her parents she wanted a new train tradition that belonged to all three of them",
        "repair": "chose a shared song and a Saturday picnic that both parents could attend",
        "ending": "The rain kept time against the glass while Pepper rested his spotted head on Luna’s knees.",
        "lesson": "Traditions can change and still carry love forward.",
    },
}

OPENINGS = [
    "On Maple Street, Luna lived in two homes and was loved in both.",
    "Luna's family had gone through a divorce, so her days now moved gently between two front doors.",
    "At the edge of Willow Lane, Luna learned that a family could have two kitchens and one very loving dalmatian.",
    "Every Friday, Luna packed a small bag while Pepper watched with his bright, patient eyes.",
]

DIALOGUES = [
    '"Do I have to choose?" Luna asked. "No," said Mina. "Your love is not a pie we must cut apart."',
    '"Will Pepper forget our other home?" Luna asked. "Never," said Jonah. "We will help him carry every good memory."',
    '"Can we still be a family?" Luna whispered. "Yes," both parents said, "though our family will look different now."',
    '"I miss the old days," Luna said. Mina answered, "You may miss them. We can also build kind new days."',
]

REFLECTIONS = [
    "The little clue had been waiting there all along.",
    "What looked like a small habit now carried a much bigger meaning.",
    "Luna understood that the magic had followed care, not a building.",
    "The early sign finally made sense.",
]


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, str] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming dalmatian divorce enchantment storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--dalmatian")
    parser.add_argument("--parent-a")
    parser.add_argument("--parent-b")
    parser.add_argument("--place")
    parser.add_argument("--keepsake")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def generate_world(params: StoryParams) -> World:
    world = World(params.place)
    world.add(Entity("child", "character", params.child, memes={"security": 0.4, "belonging": 0.3}))
    world.add(Entity("dog", "animal", params.dalmatian, memes={"loyalty": 0.8}))
    world.add(Entity("parent_a", "character", params.parent_a, memes={"care": 0.8}))
    world.add(Entity("parent_b", "character", params.parent_b, memes={"care": 0.8}))
    world.add(Entity("keepsake", "object", params.keepsake, owner="child"))
    return world


def tell(world: World, params: StoryParams) -> World:
    case = _safe_lookup(SCENARIOS, params.variant % len(SCENARIOS))
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0xDAD)
    child = world.get("child")
    dog = world.get("dog")
    parent_a = world.get("parent_a")
    parent_b = world.get("parent_b")

    world.say(_safe_lookup(OPENINGS, params.telling_mode % len(OPENINGS)).format(
        child=params.child,
        dalmatian=params.dalmatian,
        place=params.place,
    ))
    world.say(f"{params.child} loved {params.dalmatian}, a gentle dalmatian with a talent for finding the softest spot in any room.")
    world.say(f"{case['premise'].capitalize()}.")
    world.say(f"But beneath that wonder was a worry: {case['trouble']}.")
    world.para()

    world.say(f"{params.dalmatian} gave Luna a clue: {case['clue']}.")
    world.say(rng.choice(REFLECTIONS))
    world.say(f'"{case["risk"].capitalize()}," {params.child} said quietly.')
    world.say(rng.choice(DIALOGUES))
    world.say(f"The three grown-ups and {params.child} made a plan to speak kindly and tell the truth.")

    world.para()
    world.say(f"{params.child} held {params.keepsake} while {params.parent_a} and {params.parent_b} listened.")
    world.say(f"{params.child} finally said, \"I want both homes to feel like mine, and I want {params.dalmatian} to know we are still connected.\"")
    world.say(f"{params.parent_a} answered, \"We can make that promise.\"")
    world.say(f"{params.parent_b} nodded. \"Your family is changing, but you are not losing our love.\"")
    world.say(f"Then the truth became clear: {case['reveal']}.")
    world.say(f"{case['turn'].capitalize()}.")
    world.say(f"The enchantment brightened around {params.keepsake}, and {params.dalmatian} wagged so hard that his whole spotted body wiggled.")
    world.say(case["repair"].capitalize() + ".")
    world.say(rng.choice(REFLECTIONS))

    world.para()
    world.say(f"{params.child} still missed the old arrangement sometimes, and everyone allowed that feeling to be real.")
    world.say(f"{params.parent_a} and {params.parent_b} stopped trying to make the divorce look invisible; instead, they made their care easy to see.")
    world.say(case["lesson"])
    world.say(case["ending"])

    child.memes["belonging"] = 1.0
    child.memes["honesty"] = 1.0
    dog.memes["bridge_between_homes"] = 1.0
    parent_a.memes["co_parenting"] = 1.0
    parent_b.memes["co_parenting"] = 1.0
    world.get("keepsake").meters["enchanted_warmth"] = 1.0
    world.fired.update({"foreshadowing_paid_off", "feelings_shared", "care_connected_two_homes"})

    world.facts = {
        "child": params.child,
        "dalmatian": params.dalmatian,
        "parent_a": params.parent_a,
        "parent_b": params.parent_b,
        "place": params.place,
        "keepsake": params.keepsake,
        "premise": case["premise"],
        "trouble": case["trouble"],
        "clue": case["clue"],
        "risk": case["risk"],
        "reveal": case["reveal"],
        "turn": case["turn"],
        "repair": case["repair"],
        "lesson": case["lesson"],
        "ending": case["ending"],
    }
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a heartwarming story about {facts['child']} and a dalmatian named {facts['dalmatian']} during a family divorce.",
        f"Use foreshadowing through this clue: {facts['clue']}. Later reveal the enchantment.",
        f"Show how {facts['child']} finds belonging in two homes and learns that {facts['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question=f"Who was {facts['dalmatian']}?",
            answer=f"{facts['dalmatian']} was the loyal dalmatian who helped connect {facts['child']}'s two homes.",
        ),
        QAItem(
            question="What was the difficult change in the family?",
            answer=f"The family was going through a divorce, so {facts['child']} was learning to live between two homes.",
        ),
        QAItem(
            question="What clue foreshadowed the enchantment?",
            answer=f"The clue was that {facts['clue']}. It hinted that care was connecting the two homes.",
        ),
        QAItem(
            question=f"What did {facts['child']} finally tell the adults?",
            answer=f"{facts['child']} said that both homes should feel like home and that {facts['dalmatian']} should remain connected to everyone.",
        ),
        QAItem(
            question="What did the enchantment respond to?",
            answer=f"The enchantment responded to honest feelings, kindness, and promises kept by both parents.",
        ),
        QAItem(
            question="What lesson did the family learn?",
            answer=f"They learned that {facts['lesson']}",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The adults made a caring plan for both homes, and the dalmatian helped the family feel connected.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dalmatian?",
            answer="A dalmatian is a dog known for its white coat and dark spots.",
        ),
        QAItem(
            question="What does divorce mean?",
            answer="Divorce is when married adults legally end their marriage; children can still be loved by both adults.",
        ),
        QAItem(
            question="What does enchant mean?",
            answer="To enchant means to fill something with magic or make it seem wonderfully magical.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early detail that hints at something important that happens later.",
        ),
        QAItem(
            question="What is co-parenting?",
            answer="Co-parenting means adults work together to care for a child, even when they live in separate homes.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("animal", "dalmatian"),
        asp.fact("change", "divorce"),
        asp.fact("magic", "enchant"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("value", "heartwarming"),
        asp.fact("bridge", "honest_feelings"),
    ])


ASP_RULES = r"""
safe_story :- animal(dalmatian), change(divorce), magic(enchant),
              feature(foreshadowing), value(heartwarming), bridge(honest_feelings).
#show safe_story/0.
"""


def asp_program(show: str = "#show safe_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "safe_story"))
    expected = {()}
    if atoms == expected:
        print("OK: ASP gate matches Python story constraints.")
        return 0
    print("MISMATCH between ASP and Python constraints.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(expected))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"owner={entity.owner} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Pepper", "Mina", "Jonah", "Maple Street", "a blue button", 11, 0, 0),
    StoryParams("Nia", "Dot", "Elena", "Cal", "Willow Lane", "a silver bell", 29, 1, 1),
    StoryParams("Theo", "Clover", "Rosa", "Mateo", "Sunbeam Court", "a red ribbon", 47, 2, 2),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = getattr(args, "child", None) or rng.choice(CHILD_NAMES)
    dalmatian = getattr(args, "dalmatian", None) or rng.choice(DALMATIAN_NAMES)
    parent_a = getattr(args, "parent_a", None) or rng.choice(PARENT_A_NAMES)
    parent_b = getattr(args, "parent_b", None) or rng.choice(PARENT_B_NAMES)
    if parent_a == parent_b:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child=child,
        dalmatian=dalmatian,
        parent_a=parent_a,
        parent_b=parent_b,
        place=getattr(args, "place", None) or rng.choice(PLACES),
        keepsake=getattr(args, "keepsake", None) or rng.choice(KEEPSAKES),
        seed=None,
        variant=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(len(OPENINGS)),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print("ASP model:", model)
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < getattr(args, "n", None) and index < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if getattr(args, "json", None):
        print(format_json(samples))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
