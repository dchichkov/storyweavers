#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/greenery_dialogue_twist_foreshadowing_comedy.py
===============================================================================

A small standalone storyworld about a child, a messy patch of greenery, a
chatty garden helper, and a comic twist: the "monster in the bushes" turns out
to be a lost, grumpy sprinkler head that was only pretending to be scary.

The world is built to support:
- greenery as the central setting/material
- dialogue as a major narrative instrument
- foreshadowing via small physical clues and emotional beats
- a twist that changes the apparent problem into a funny reveal
- a comedy tone with a light, child-facing ending

Run it:
    python storyworlds/worlds/gpt-5.4-mini/greenery_dialogue_twist_foreshadowing_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/greenery_dialogue_twist_foreshadowing_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/greenery_dialogue_twist_foreshadowing_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/greenery_dialogue_twist_foreshadowing_comedy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    greenery: str
    clue: str
    echo: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class PlantThing:
    id: str
    label: str
    phrase: str
    lively: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class OddSound:
    id: str
    label: str
    clue: str
    comic: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
            self.events.append(text)

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_clue(world: World) -> list[str]:
    out = []
    t = world.facts.get("twist_target")
    if not t:
        return out
    if world.get(t).meters["rustle"] >= THRESHOLD and ("clue", t) not in world.fired:
        world.fired.add(("clue", t))
        world.get("garden").memes["mystery"] += 1
        out.append("__clue__")
    return out


def _r_comedy(world: World) -> list[str]:
    out = []
    if world.get("child").memes["embarrassed"] >= THRESHOLD and ("comedy",) not in world.fired:
        world.fired.add(("comedy",))
        world.get("child").memes["relief"] += 1
        out.append("__comic__")
    return out


CAUSAL_RULES = [Rule("clue", _r_clue), Rule("comedy", _r_comedy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup(world: World, child: Entity, helper: Entity, setting: Setting, plant: PlantThing, odd: OddSound) -> None:
    child.memes["curious"] += 1
    helper.memes["proud"] += 1
    world.say(
        f"On a bright afternoon, {child.id} wandered into {setting.place}, where "
        f"{setting.greenery} made the air smell fresh and sweet."
    )
    world.say(
        f"{helper.id} waved from the path. \"Look at all this greenery,\" {helper.pronoun()} said. "
        f"\"It feels like the garden is wearing a leafy coat.\""
    )
    world.say(
        f"{child.id} laughed. \"That coat looks itchy.\" \"Only if you hug a thorn,\" "
        f"{helper.id} said, pointing to {plant.phrase}."
    )
    world.say(
        f"Near the bushes, something went {odd.clue}... {odd.clue}... like a tiny goblin "
        f"trying not to sneeze."
    )
    world.facts["twist_target"] = "mystery"


def foreshadow(world: World, plant: PlantThing, odd: OddSound) -> None:
    world.say(
        f"{plant.label.capitalize()} sat in the middle of the path with one leaf bent sideways, "
        f"and that bent leaf looked a lot like a little ear."
    )
    world.say(
        f"\"Did the hedge just blink?\" {world.get('child').id} asked."
    )
    world.say(
        f"\"If it did, it has excellent timing,\" said {world.get('helper').id}, trying not to laugh."
    )
    world.get("garden").meters["rustle"] += 1


def twist(world: World, helper: Entity, plant: PlantThing, odd: OddSound) -> None:
    world.get("child").memes["embarrassed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} reached into the greenery and pulled out the 'monster': "
        f"a round, muddy sprinkler head wearing two sticks and a leaf like a fake moustache."
    )
    world.say(
        f"\"I knew it!\" said {world.get('child').id}. \"It was a sneaky garden beast!\""
    )
    world.say(
        f"\"Nope,\" {helper.id} said, snickering. \"It was just the sprinkler hiding so well it almost became a bush.\""
    )
    world.say(
        f"The little machine went {odd.comic} and gave one embarrassed drip, as if it wanted to apologize."
    )


def resolve(world: World, child: Entity, helper: Entity, plant: PlantThing) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{child.id} carefully set the leaf moustache back on the grass. "
        f"\"Can we keep the funny bush?\" {child.id} asked."
    )
    world.say(
        f"\"We can keep the joke,\" said {helper.id}, \"but the sprinkler should go back to watering the {plant.label}.\""
    )
    world.say(
        f"They fixed the sprinkler, and soon the greenery glowed brighter, as if the garden itself was laughing."
    )


SETTINGS = {
    "garden": Setting(
        "garden",
        "the backyard garden",
        "lush greenery and climbing vines",
        "a soft rustle in the hedge",
        "a leaf-flop in the breeze",
    ),
    "park": Setting(
        "park",
        "the little city park",
        "greenery around the swings",
        "a wobble in the tall grass",
        "a squeaky bump near the flower bed",
    ),
    "greenhouse": Setting(
        "greenhouse",
        "the sunny greenhouse",
        "rows of greenery under glass",
        "a tiny tap behind the fern pot",
        "a wet plink from the watering can",
    ),
}

PLANTS = {
    "hedge": PlantThing("hedge", "hedge", "the hedge"),
    "fern": PlantThing("fern", "fern", "the fern"),
    "bush": PlantThing("bush", "bush", "the bush"),
}

ODD_SOUNDS = {
    "rustle": OddSound("rustle", "rustle", "rustle", "rustle"),
    "squeak": OddSound("squeak", "squeak", "squeak", "squeak"),
    "plink": OddSound("plink", "plink", "plink", "plink"),
}

CHILD_NAMES = ["Mia", "Theo", "Lily", "Ben", "Zoe", "Max", "Ava", "Sam"]
HELPER_NAMES = ["Grandma", "Uncle Jo", "Auntie May", "Mr. Purl", "Mrs. Green"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    plant: str
    sound: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, o) for s in SETTINGS for p in PLANTS for o in ODD_SOUNDS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy greenery storyworld with dialogue, foreshadowing, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--sound", choices=ODD_SOUNDS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.plant is None or c[1] == args.plant)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, plant, sound = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(setting, plant, sound, child, "girl" if child in {"Mia", "Lily", "Zoe", "Ava"} else "boy", helper, "woman" if helper in {"Grandma", "Auntie May", "Mrs. Green"} else "man")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    plant = PLANTS[params.plant]
    odd = ODD_SOUNDS[params.sound]
    child = world.add(Entity("child", "character", params.child_gender))
    child.id = params.child
    helper = world.add(Entity("helper", "character", params.helper_gender))
    helper.id = params.helper
    garden = world.add(Entity("garden", "place", label=setting.place))
    world.facts.update(setting=setting, plant=plant, odd=odd, child=child, helper=helper, garden=garden)

    setup(world, child, helper, setting, plant, odd)
    world.para()
    foreshadow(world, plant, odd)
    world.para()
    twist(world, helper, plant, odd)
    world.para()
    resolve(world, child, helper, plant)
    world.facts["ending"] = "comic_twist"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story that uses the word "greenery" and includes dialogue in a garden.',
        f"Tell a comedy for a young child where {f['child'].id} hears a strange {f['odd'].label} in the {f['setting'].place} and the mystery turns out to be silly.",
        f"Write a foreshadowing story where a tiny clue in the greenery hints that the scary sound is actually a joke.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    plant: PlantThing = f["plant"]
    odd: OddSound = f["odd"]
    return [
        QAItem(
            question="Why did the garden sound mysterious at first?",
            answer=f"It sounded mysterious because the greenery kept rustling, and there was a small {odd.label} near the bushes. That made {child.id} think something was hiding there."
        ),
        QAItem(
            question="What was the foreshadowing clue?",
            answer=f"The bent leaf that looked like a little ear was the clue. It hinted that the 'monster' was something garden-shaped, not something scary."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the monster was not a monster at all. It was a muddy sprinkler head with a leaf on its face, and that made the whole scene funny."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{helper.id} fixed the sprinkler, {child.id} got to laugh, and the {plant.label} kept growing. The ending showed that the greenery was safe and lively again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is greenery?",
            answer="Greenery means lots of green plants, leaves, and growing things. It makes a place feel alive and fresh."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue about something that will matter later. It helps the ending feel surprising but not random."
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer="Dialogue lets characters speak to each other directly. It makes a story sound lively and helps readers hear the characters' feelings."
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLANTS:
        lines.append(asp.fact("plant", pid))
    for oid in ODD_SOUNDS:
        lines.append(asp.fact("sound", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,O) :- setting(S), plant(P), sound(O).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, plant=None, sound=None, child=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


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
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story QA ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world QA ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


CURATED = [
    StoryParams("garden", "hedge", "rustle", "Mia", "girl", "Grandma", "woman"),
    StoryParams("park", "bush", "squeak", "Theo", "boy", "Mr. Purl", "man"),
    StoryParams("greenhouse", "fern", "plink", "Ava", "girl", "Mrs. Green", "woman"),
]


def generate_random(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            try:
                p = generate_random(random.Random(base_seed + i), args)
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
