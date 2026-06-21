#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/buster_progressive_problem_solving_suspense_kindness_whodunit.py
================================================================================================

A tiny whodunit storyworld about a missing prize, a suspicious trail, a gentle
helper, and a child detective named Buster who solves the puzzle step by step.

The world is built to support three narrative instruments:
- Problem Solving: clues narrow the search in stages.
- Suspense: the hidden object moves through a few risky locations.
- Kindness: the detective solves the mystery without blame or meanness.

Seed words: buster, progressive
Style: whodunit
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    hiding_spots: list[str]
    mood: str
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
class Item:
    id: str
    label: str
    clue_label: str
    safe_spot: str
    risky_spots: list[str]
    owner: str
    plural: bool = False
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
class Suspect:
    id: str
    label: str
    type: str
    is_kind: bool
    can_help: bool = False
    clues: list[str] = field(default_factory=list)
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
class Rule:
    name: str
    apply: callable
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


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for sid in world.facts.get("search_route", []):
        spot = world.get(sid)
        if spot.meters["searched"] >= THRESHOLD:
            continue
        if spot.meters["hinted"] >= THRESHOLD:
            sig = ("anxiety", sid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append("The mystery felt closer now.")
    return out


RULES = [Rule("anxiety", _r_anxiety)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def clue_strength(route_index: int) -> int:
    return 1 + route_index


def valid_config(item: Item, setting: Setting) -> bool:
    return item.safe_spot in setting.hiding_spots and any(s in setting.hiding_spots for s in item.risky_spots)


def pick_names(rng: random.Random) -> tuple[str, str, str]:
    detective = rng.choice(["Buster", "Milo", "Nina", "Lena", "Theo", "Ruby"])
    helper = rng.choice([n for n in ["Pia", "Mina", "Ari", "June", "Ollie", "Eve"] if n != detective])
    culprit = rng.choice(["the cat", "the puppy", "the wind", "a helpful little brother", "the sleepy robot"])
    return detective, helper, culprit


def tell(setting: Setting, item: Item, detective_name: str = "Buster",
         helper_name: str = "Mina", culprit_name: str = "the cat") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type="boy", role="detective",
                                 traits=["curious", "kind"], attrs={"seed_word": "buster"}))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper",
                               traits=["gentle", "progressive"], attrs={"seed_word": "progressive"}))
    culprit = world.add(Entity(id=culprit_name, kind="character", type="thing", role="suspect",
                               traits=["sneaky"], attrs={"maybe_guilty": True}))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    prize = world.add(Entity(id="prize", type=item.id, label=item.label, attrs={"owner": item.owner}))

    detective.memes["curiosity"] = 2
    helper.memes["kindness"] = 2

    world.say(
        f"At {setting.place}, Buster found a small mystery waiting in the quiet room. "
        f"The prize was missing, and the air felt still and watchful."
    )
    world.say(
        f'Buster said, "I will solve this progressive mystery step by step." '
        f'{helper.id} nodded and promised to help without making a fuss.'
    )

    world.para()
    first_spot = setting.hiding_spots[0]
    world.get("room").meters["searched"] += 1
    world.get("room").meters["hinted"] += 1
    world.say(
        f"They checked the {first_spot} first. There was no prize there, but they found a tiny clue: "
        f"{item.clue_label} dust on the floor."
    )
    world.say("That meant the answer was not far away, but it was not solved yet.")

    world.para()
    second_spot = setting.hiding_spots[1]
    world.get("room").meters["searched"] += 1
    world.get("room").meters["hinted"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Then Buster looked at the {second_spot} and noticed another clue near the edge. "
        f"It seemed the prize had been moved carefully, not stolen in a rough way."
    )

    world.para()
    culprit.memes["nervous"] += 1
    world.say(
        f"{helper.id} whispered that the only one who had been near the prize was {culprit.label}. "
        f"But Buster shook his head and said, 'We should ask before we accuse.'"
    )
    if culprit.label == "the cat":
        world.say("The cat blinked and looked innocent, which made the room feel even more mysterious.")
    elif culprit.label == "the puppy":
        world.say("The puppy wagged its tail, which made Buster suspect the trail led somewhere kinder.")
    else:
        world.say(f"{culprit.label_word.capitalize()} looked worried, as if {culprit.pronoun()} knew something important.")

    world.para()
    world.say(
        f"Buster followed the last clue to the {item.safe_spot}. There, under a soft cover, was the prize at last."
    )
    world.say(
        f"{helper.id} smiled because Buster had solved it with patience. He let the suspect off the hook, "
        f"and even thanked them for not hiding the clue too well."
    )
    world.say(
        f"By the end, the room felt bright again, and Buster and {helper.id} sat together with the prize found and everyone calm."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        setting=setting,
        item=item,
        route=[room.id],
        search_route=[room.id],
        solved=True,
        clue_count=2,
    )
    return world


SETTINGS = {
    "playroom": Setting(id="playroom", place="the playroom", hiding_spots=["rug", "toy shelf", "reading nook"], mood="quiet"),
    "kitchen": Setting(id="kitchen", place="the kitchen", hiding_spots=["counter", "chair", "pantry"], mood="still"),
    "classroom": Setting(id="classroom", place="the classroom", hiding_spots=["desk", "window ledge", "book bin"], mood="watchful"),
}

ITEMS = {
    "ball": Item(id="ball", label="red ball", clue_label="red powder", safe_spot="toy shelf", risky_spots=["rug", "chair"], owner="the child", tags={"toy"}),
    "badge": Item(id="badge", label="silver badge", clue_label="silver glitter", safe_spot="reading nook", risky_spots=["counter", "book bin"], owner="the teacher", tags={"badge"}),
    "hat": Item(id="hat", label="blue hat", clue_label="blue thread", safe_spot="pantry", risky_spots=["rug", "window ledge"], owner="the parent", tags={"hat"}),
}

GIRL_NAMES = ["Mina", "Pia", "June", "Eve", "Ruby", "Nora"]
BOY_NAMES = ["Buster", "Theo", "Owen", "Milo", "Finn", "Max"]

@dataclass
class StoryParams:
    setting: str
    item: str
    detective: str = "Buster"
    helper: str = "Mina"
    culprit: str = "the cat"
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


CURATED = [
    StoryParams(
        setting="playroom",
        item="ball",
        detective="Buster",
        helper="Mina",
        culprit="the cat",
        seed=7,
    ),
    StoryParams(
        setting="classroom",
        item="badge",
        detective="Buster",
        helper="June",
        culprit="the wind",
        seed=11,
    ),
    StoryParams(
        setting="kitchen",
        item="hat",
        detective="Buster",
        helper="Pia",
        culprit="the puppy",
        seed=19,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with Buster.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--culprit")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, iid) for sid, s in SETTINGS.items() for iid, item in ITEMS.items() if valid_config(item, s)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.item:
        if (args.setting, args.item) not in combos:
            raise StoryError("That setting and item do not make a good mystery.")
    choices = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.item is None or c[1] == args.item)]
    if not choices:
        raise StoryError("No valid story matches those choices.")
    setting, item = rng.choice(sorted(choices))
    detective = args.detective or "Buster"
    helper = args.helper or rng.choice(["Mina", "June", "Pia", "Eve"])
    culprit = args.culprit or rng.choice(["the cat", "the puppy", "the wind", "the sleepy robot"])
    return StoryParams(setting=setting, item=item, detective=detective, helper=helper, culprit=culprit)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a young child starring {f["detective"].id} and the word "buster".',
        f'Write a progressive mystery where {f["detective"].id} solves a missing-prize case step by step and shows kindness.',
        f'Tell a suspenseful but gentle story about a missing {f["item"].label} and a helper who keeps everyone calm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"].id
    helper = f["helper"].id
    item = f["item"].label
    setting = f["setting"].place
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{det} solved it by looking at the clues one by one. He stayed kind and did not blame anyone too quickly.",
        ),
        QAItem(
            question="What was missing?",
            answer=f"The missing thing was the {item}. The story slowly revealed where it had been hidden.",
        ),
        QAItem(
            question=f"How did {helper} help?",
            answer=f"{helper} helped by pointing out clues and staying calm. That made the search feel safer and steadier.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the prize found again in {setting}. Everyone was calm, and Buster had solved the mystery kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a little piece of information that helps someone solve a mystery. A clue can be a mark, a trail, or something that looks out of place.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="It means figuring out what happened by paying attention and thinking carefully. Good detectives look at clues before they decide.",
        ),
        QAItem(
            question="Why is kindness helpful in a mystery?",
            answer="Kindness keeps people calm and willing to help. When nobody feels blamed too soon, it is easier to find the truth.",
        ),
    ]


ASP_RULES = r"""
valid_combo(S, I) :- setting(S), item(I), safe_pair(S, I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for spot in item.risky_spots:
            lines.append(asp.fact("risky_spot", iid, spot))
        lines.append(asp.fact("safe_spot", iid, item.safe_spot))
    for sid, s in SETTINGS.items():
        for spot in s.hiding_spots:
            lines.append(asp.fact("spot", sid, spot))
    for sid, s in SETTINGS.items():
        for iid, item in ITEMS.items():
            if valid_config(item, s):
                lines.append(asp.fact("safe_pair", sid, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS:
        raise StoryError("Unknown setting or item.")
    world = tell(SETTINGS[params.setting], ITEMS[params.item], params.detective, params.helper, params.culprit)
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
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(e.id, meters, memes, e.role, e.attrs)
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for q in sample.story_qa:
            print(q.question)
            print(q.answer)
        print("== world qa ==")
        for q in sample.world_qa:
            print(q.question)
            print(q.answer)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
