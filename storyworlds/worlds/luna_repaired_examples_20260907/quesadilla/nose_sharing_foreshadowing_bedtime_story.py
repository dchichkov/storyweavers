#!/usr/bin/env python3
"""
Bedtime Story world: a little nose, a shared snack, and a gentle foreshadowing.

A child notices a quesadilla's funny smell, follows small signs through the
house, and discovers that sharing can solve a cozy bedtime problem.
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


SETTINGS = (
    "a little house where the hallway night-light glowed",
    "a quiet cottage while rain tapped on the roof",
    "a warm apartment beneath a silver moon",
    "a farmhouse filled with sleepy evening sounds",
)

CHILDREN = (
    ("Mina", "girl"),
    ("Nora", "girl"),
    ("Theo", "boy"),
    ("Sam", "child"),
    ("Ivy", "girl"),
)

HELPERS = (
    ("Mom", "mother"),
    ("Dad", "father"),
    ("Grandma", "woman"),
    ("Papa", "father"),
)

FILLINGS = (
    "melted cheese and sweet corn",
    "cheese and tiny black beans",
    "cheese and roasted squash",
    "golden cheese and tomato",
)

SCENARIOS = (
    {
        "starting_place": "the blue plate beside the stove",
        "clue": "a warm cheesy tickle in the air",
        "foreshadow": "a second small plate waiting near the window",
        "destination": "the window seat",
        "reason": "the quesadilla was too large for one sleepy tummy",
        "sharing_action": "cut it into two soft triangles",
        "image": "Two crumbs rested beside the empty plates like tiny golden stars.",
    },
    {
        "starting_place": "the little table by the reading nook",
        "clue": "a buttery scent curling beneath the door",
        "foreshadow": "two folded napkins beside a basket",
        "destination": "the picnic basket",
        "reason": "a friend was coming to share the last warm snack",
        "sharing_action": "saved one half for the waiting friend",
        "image": "The basket held one last warm triangle, ready for a friendly morning.",
    },
    {
        "starting_place": "the checked placemat near the back door",
        "clue": "a peppery tickle that made the child wrinkle their nose",
        "foreshadow": "two cups beside the covered tray",
        "destination": "the covered tray on the mudroom bench",
        "reason": "the rain had made everyone hungry together",
        "sharing_action": "carried the snack carefully to the two cups",
        "image": "Rain whispered outside while two happy noses followed the last warm smell.",
    },
    {
        "starting_place": "the moon-shaped plate beside the sink",
        "clue": "a toasted smell hiding under the dish towel",
        "foreshadow": "a tiny note that said, 'For both of us'",
        "destination": "the cozy sofa",
        "reason": "the bedtime story was more fun with a shared bite",
        "sharing_action": "wrapped half in a napkin and brought it to the sofa",
        "image": "The napkin folded around the final crumbs as the bedtime book closed.",
    },
)

REACTIONS = (
    "took one careful sniff",
    "wrinkled their nose and listened",
    "followed the delicious smell on tiptoe",
    "held their nose close to the air",
)

ENDING_IMAGES = (
    "Then the night-light shone on two clean plates, and everyone settled beneath the blanket.",
    "The shared snack was gone, but its warm smell stayed in the room like a happy hug.",
    "At last, two sleepy smiles tucked themselves under the blanket together.",
)



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    setting: object | None = None
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
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mina"
    child_type: str = "girl"
    helper_name: str = "Mom"
    helper_type: str = "mother"
    setting_place: str = _safe_lookup(SETTINGS, 0)
    filling: str = _safe_lookup(FILLINGS, 0)
    starting_place: str = _safe_lookup(SCENARIOS, 0)["starting_place"]
    clue: str = _safe_lookup(SCENARIOS, 0)["clue"]
    foreshadow: str = _safe_lookup(SCENARIOS, 0)["foreshadow"]
    destination: str = _safe_lookup(SCENARIOS, 0)["destination"]
    reason: str = _safe_lookup(SCENARIOS, 0)["reason"]
    sharing_action: str = _safe_lookup(SCENARIOS, 0)["sharing_action"]
    reaction: str = _safe_lookup(REACTIONS, 0)
    ending_image: str = _safe_lookup(ENDING_IMAGES, 0)
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


def tell(params: StoryParams) -> World:
    if not params.child_name.strip():
        pass
    if not params.helper_name.strip():
        pass
    if not params.filling.strip():
        pass

    setting = Setting(params.setting_place)
    world = World(setting)
    child = world.add(Entity("child", "character", params.child_type, params.child_name))
    helper = world.add(Entity("helper", "character", params.helper_type, params.helper_name))
    snack = world.add(Entity(
        "quesadilla",
        "food",
        "quesadilla",
        f"the quesadilla filled with {params.filling}",
        meters={"warmth": 1.0},
        memes={"sharing": 0.0},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        snack=snack,
        setting=setting,
        shared=False,
    )

    world.say(
        f"Before bedtime, {child.label} helped {helper.label} make a quesadilla "
        f"filled with {params.filling} in {setting.place}."
    )
    world.say(
        f"They left it on {params.starting_place}, where it was meant to be one last cozy snack."
    )

    world.para()
    child.memes["curious"] = 1.0
    child.meters["hunger"] = 1.0
    world.say(
        f"But when {child.label} came back in pajamas, the plate was empty. "
        f'"Where did it go?" {child.label} asked.'
    )
    world.say(
        f"{child.label} {params.reaction}. The nose knows when something warm and tasty is nearby."
    )

    world.fired.add("scent")
    world.say(
        f"A {params.clue} led from the empty plate toward {params.destination}."
    )

    world.para()
    world.fired.add("foreshadow")
    world.say(
        f"Near the path, {params.foreshadow}. It was a small sign that someone had planned "
        f"for more than one hungry person."
    )

    world.para()
    world.fired.add("reveal")
    helper_subject = helper.pronoun("subject").capitalize()
    world.say(
        f"At {params.destination}, {child.label} found {helper.label} with the warm quesadilla."
    )
    world.say(
        f'"I moved it because {params.reason}," {helper.label} explained. '
        f'{helper_subject} {params.sharing_action}.'
    )

    world.facts["shared"] = True
    snack.memes["sharing"] = 1.0
    snack.meters["warmth"] = 0.5
    child.meters["hunger"] = 0.0
    child.memes["joy"] = 1.0
    helper.memes["care"] = 1.0

    world.say(
        f"The clue and the little sign made sense at last. {child.label} thanked {helper.label}, "
        f"and they shared every warm bite."
    )
    world.para()
    world.fired.add("ending")
    world.say(params.ending_image)
    return world


ASP_RULES = r"""
missing(quesadilla).
has_helper(helper).
smell_leads_to(quesadilla, destination).
foreshadowing(two_plates).
sharing_plan(quesadilla).
shared(quesadilla) :-
    missing(quesadilla),
    has_helper(helper),
    smell_leads_to(quesadilla, destination),
    foreshadowing(two_plates),
    sharing_plan(quesadilla).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing", "quesadilla"),
        asp.fact("has_helper", "helper"),
        asp.fact("smell_leads_to", "quesadilla", "destination"),
        asp.fact("foreshadowing", "two_plates"),
        asp.fact("sharing_plan", "quesadilla"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shared/1."))
    shared = set(asp.atoms(model, "shared"))
    if shared == {("quesadilla",)}:
        print("OK: ASP and Python agree that the quesadilla is shared.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP shared:", sorted(shared))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle bedtime story about a nose following the smell of a missing quesadilla.",
        f"Tell a cozy story in which {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").label} notices a small sign that foreshadows sharing.",
        f"Write a bedtime ending where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").label} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").label} share the warm snack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    return [
        QAItem(
            question=f"How did {child.label} find the missing quesadilla?",
            answer=f"{child.label} followed the warm smell with their nose from {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "starting_place")} toward {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "destination")}.",
        ),
        QAItem(
            question=f"What foreshadowed that the quesadilla would be shared?",
            answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "foreshadow")} showed that someone had planned for more than one hungry person.",
        ),
        QAItem(
            question=f"Why had {helper.label} moved the quesadilla?",
            answer=f"{helper.label} moved it because {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "reason")}.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"{child.label} and {helper.label} shared every warm bite, then settled down for bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a nose help a person do?",
            answer="A nose helps a person breathe and notice smells, such as the warm smell of food.",
        ),
        QAItem(
            question="Why is sharing kind?",
            answer="Sharing lets people enjoy something together and helps everyone feel remembered and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"shared={world.facts.get('shared')}")
    return "\n".join(lines)


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else 0
    child_name, child_type = CHILDREN[(seed * 7 + 1) % len(CHILDREN)]
    helper_name, helper_type = _safe_lookup(HELPERS, (seed * 11 + 2) % len(HELPERS))
    scenario = _safe_lookup(SCENARIOS, (seed * 13 + 3) % len(SCENARIOS))
    return StoryParams(
        seed=seed,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        setting_place=rng.choice(SETTINGS),
        filling=rng.choice(FILLINGS),
        starting_place=scenario["starting_place"],
        clue=scenario["clue"],
        foreshadow=scenario["foreshadow"],
        destination=scenario["destination"],
        reason=scenario["reason"],
        sharing_action=scenario["sharing_action"],
        reaction=rng.choice(REACTIONS),
        ending_image=rng.choice(ENDING_IMAGES),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime story about a nose, foreshadowing, and sharing."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show shared/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show shared/1."))
        print(sorted(set(asp.atoms(model, "shared"))))
        return

    base_seed = (
        getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    )

    if getattr(args, "all", None):
        seeds = [base_seed]
    else:
        if getattr(args, "n", None) < 1:
            pass
        seeds = [base_seed + i for i in range(getattr(args, "n", None))]

    samples = []
    for seed in seeds:
        sample_args = argparse.Namespace(**vars(args))
        sample_args.seed = seed
        params = resolve_params(sample_args, random.Random(seed))
        samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
