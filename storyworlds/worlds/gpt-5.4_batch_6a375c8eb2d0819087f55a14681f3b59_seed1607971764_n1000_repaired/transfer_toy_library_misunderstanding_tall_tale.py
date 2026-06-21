#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/transfer_toy_library_misunderstanding_tall_tale.py
==============================================================================

A standalone storyworld for a tiny, child-facing tall tale set in a toy library.

Premise
-------
A child visits a toy library, where toys can be borrowed and later returned.
The child sees a shelf label about the "transfer cart" and misunderstands it:
they think "transfer" means a toy may be moved straight into their own bag forever.
They proudly carry off an oversized toy. A librarian gently explains the mix-up,
shows the real transfer process, and helps the child borrow the toy the proper way.

World model
-----------
This world models:
- typed entities with physical meters and emotional memes
- a misunderstanding about ownership and borrowing rules
- a transfer process inside the toy library: shelf -> transfer cart -> checkout desk
- a state-driven tall-tale turn, where the chosen toy is so comically grand that
  the misunderstanding becomes impossible to ignore
- a clear resolution proving what changed: the toy is borrowed properly and the
  child later returns it

Run it
------
python storyworlds/worlds/gpt-5.4/transfer_toy_library_misunderstanding_tall_tale.py
python storyworlds/worlds/gpt-5.4/transfer_toy_library_misunderstanding_tall_tale.py --toy dragon_wagon
python storyworlds/worlds/gpt-5.4/transfer_toy_library_misunderstanding_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/transfer_toy_library_misunderstanding_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/transfer_toy_library_misunderstanding_tall_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    location: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "librarian_f"}
        male = {"boy", "man", "father", "librarian_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "librarian_f":
            return "librarian"
        if self.type == "librarian_m":
            return "librarian"
        return self.type
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
    wonder_line: str
    return_spot: str
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
class Toy:
    id: str
    label: str
    phrase: str
    huge_line: str
    movement_line: str
    size: int
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
class Sign:
    id: str
    text: str
    child_guess: str
    real_meaning: str
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
class HelperMove:
    id: str
    explain_line: str
    process_line: str
    ending_line: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_bag_strain(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    bag = world.entities.get("bag")
    if not child or not toy or not bag:
        return out
    if child.meters["carrying"] < THRESHOLD:
        return out
    if toy.meters["bulk"] < 1:
        return out
    sig = ("bag_strain", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bag.meters["stuffed"] += 1
    child.memes["strain"] += 1
    if toy.meters["bulk"] >= 3:
        child.memes["embarrassment"] += 1
        world.get("room").meters["commotion"] += 1
        out.append("__commotion__")
    return out


def _r_wrong_transfer(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    if not child or not toy:
        return out
    if child.meters["attempted_private_take"] < THRESHOLD:
        return out
    sig = ("wrong_transfer", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.meters["misplaced"] += 1
    world.get("room").meters["rule_tension"] += 1
    child.memes["certainty"] += 1
    child.memes["confusion"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bag_strain", tag="physical", apply=_r_bag_strain),
    Rule(name="wrong_transfer", tag="social", apply=_r_wrong_transfer),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def misunderstanding_possible(sign: Sign, toy: Toy) -> bool:
    return "transfer" in sign.text.lower() and toy.size >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for sign_id, sign in SIGNS.items():
            for toy_id, toy in TOYS.items():
                if misunderstanding_possible(sign, toy):
                    combos.append((setting_id, sign_id, toy_id))
    return combos


def predict_commotion(toy: Toy) -> bool:
    return toy.size >= 3


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In the toy library, {child.id} thought every shelf looked taller than a tree "
        f"and every bin looked deeper than a pond. {setting.wonder_line}"
    )
    world.say(
        f"Beside the checkout desk stood {helper.id}, the {helper.label_word}, with a smile "
        f"as calm as a bookmark resting in the middle of a favorite page."
    )


def show_toy(world: World, child: Entity, toy_cfg: Toy) -> None:
    child.memes["desire"] += 1
    world.say(
        f"Then {child.id} spotted {toy_cfg.phrase}. {toy_cfg.huge_line}"
    )


def notice_sign(world: World, child: Entity, sign: Sign) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Above one rolling cart hung a neat little sign that said, "
        f'"{sign.text}."'
    )
    world.say(
        f"{child.id} sounded out the big word slowly. In {child.pronoun('possessive')} mind, "
        f"{sign.child_guess}"
    )


def decide_wrongly(world: World, child: Entity, toy: Entity, bag: Entity, toy_cfg: Toy) -> None:
    child.meters["attempted_private_take"] += 1
    child.meters["carrying"] += 1
    toy.location = "bag"
    bag.meters["load"] += float(toy_cfg.size)
    toy.meters["bulk"] = float(toy_cfg.size)
    propagate(world, narrate=False)
    world.say(
        f'"Aha," {child.id} whispered. "Today this toy will transfer right into my bag forever."'
    )
    world.say(
        f"So {child.pronoun()} tugged and huffed and managed to steer the {toy_cfg.label} toward "
        f"{child.pronoun('possessive')} bag. {toy_cfg.movement_line}"
    )


def commotion(world: World, child: Entity, toy_cfg: Toy) -> None:
    if world.get("room").meters["commotion"] < THRESHOLD:
        return
    child.memes["surprise"] += 1
    world.say(
        f"That was when the whole toy library seemed to notice. The wheels squeaked, the blocks rattled, "
        f"and even the picture books looked ready to peek over their covers. In a room that tidy, "
        f"a {toy_cfg.label} on the move felt as big as a parade."
    )


def explain(world: World, helper: Entity, child: Entity, sign: Sign, toy_cfg: Toy, move: HelperMove) -> None:
    helper.memes["care"] += 1
    child.memes["confusion"] += 1
    world.say(
        f'"Oh, pumpkin," {helper.id} said gently, {move.explain_line} '
        f'"Here, transfer does not mean a toy becomes yours forever."'
    )
    world.say(
        f'"It means the toy is moved from one place to another inside the library first, '
        f'and then we borrow it the proper way."'
    )
    world.say(
        f"{child.id} blinked. The misunderstanding slid off {child.pronoun('object')} all at once, "
        f"like a paper crown slipping sideways. {sign.real_meaning}"
    )


def proper_transfer(world: World, helper: Entity, child: Entity, toy: Entity, setting: Setting, move: HelperMove) -> None:
    toy.location = "transfer_cart"
    toy.meters["misplaced"] = 0.0
    world.facts["toy_transferred"] = True
    child.meters["attempted_private_take"] = 0.0
    child.meters["carrying"] = 0.0
    world.say(
        f"{helper.id} placed a library card on the desk, guided the toy onto the transfer cart, "
        f"and showed each step slowly. {move.process_line}"
    )
    world.say(
        f"From the shelf it went to the cart, from the cart it rolled to the desk, and from the desk "
        f"it was checked out into {child.id}'s care. That was the real transfer."
    )
    toy.location = "borrowed_home"
    toy.owner = child.id
    child.memes["understanding"] += 1
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.facts["checked_out"] = True
    world.facts["borrow_location"] = "home"


def return_scene(world: World, child: Entity, helper: Entity, toy_cfg: Toy, setting: Setting, move: HelperMove) -> None:
    world.say(
        f"A week later, {child.id} came back through the door carrying the great {toy_cfg.label} properly, "
        f"with both hands and a grin. {move.ending_line}"
    )
    world.say(
        f"{child.pronoun().capitalize()} rolled it to {setting.return_spot} and said, "
        f'"Now I know how a toy can transfer and still belong to everyone."'
    )


def tell(setting: Setting, sign: Sign, toy_cfg: Toy, move: HelperMove,
         child_name: str = "Mabel", child_type: str = "girl",
         helper_name: str = "Ms. Juniper", helper_type: str = "librarian_f") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    bag = world.add(Entity(id="bag", kind="thing", type="bag", label="book bag"))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=toy_cfg.label, location="shelf"))
    cart = world.add(Entity(id="cart", kind="thing", type="cart", label="transfer cart", location="aisle"))

    world.facts["setting"] = setting
    world.facts["sign"] = sign
    world.facts["toy_cfg"] = toy_cfg
    world.facts["move"] = move
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["toy"] = toy
    world.facts["bag"] = bag
    world.facts["toy_transferred"] = False
    world.facts["checked_out"] = False
    world.facts["borrow_location"] = ""
    world.facts["commotion"] = False
    world.facts["misunderstood"] = True

    introduce(world, child, helper, setting)
    show_toy(world, child, toy_cfg)

    world.para()
    notice_sign(world, child, sign)
    decide_wrongly(world, child, toy, bag, toy_cfg)
    if predict_commotion(toy_cfg):
        world.facts["commotion"] = True
        commotion(world, child, toy_cfg)

    world.para()
    explain(world, helper, child, sign, toy_cfg, move)
    proper_transfer(world, helper, child, toy, setting, move)

    world.para()
    return_scene(world, child, helper, toy_cfg, setting, move)

    return world


SETTINGS = {
    "toy_library": Setting(
        id="toy_library",
        place="the toy library",
        wonder_line="Some shelves held puzzles in bright boxes, some held dollhouses, and one corner glittered with toy wheels and wings as if a parade had been packed into wooden cubbies.",
        return_spot="the return rug by the front desk",
        tags={"library", "borrow", "return"},
    ),
}

TOYS = {
    "dragon_wagon": Toy(
        id="dragon_wagon",
        label="dragon wagon",
        phrase="a dragon wagon with red scales painted on its sides",
        huge_line="It looked long enough to carry six stuffed bears, three brave dolls, and maybe one polite goose.",
        movement_line="The wagon rolled like a tiny thundercloud, and the bag did not look nearly ready for such glory.",
        size=3,
        tags={"wagon", "dragon", "big_toy"},
    ),
    "moon_train": Toy(
        id="moon_train",
        label="moon train",
        phrase="a moon train with silver windows and a bell on top",
        huge_line="Its little cars seemed ready to cross a night sky from snack time to supper.",
        movement_line="Each car clinked behind the next, and the train stretched farther than a scarf in the wind.",
        size=3,
        tags={"train", "big_toy"},
    ),
    "castle_crate": Toy(
        id="castle_crate",
        label="castle crate",
        phrase="a castle crate full of towers, gates, and tiny flags",
        huge_line="The crate looked stout enough to build a kingdom before lunch and defend it until bedtime.",
        movement_line="Blocks knocked softly inside like knights tapping on their shields.",
        size=2,
        tags={"blocks", "castle"},
    ),
    "puzzle_whale": Toy(
        id="puzzle_whale",
        label="puzzle whale",
        phrase="a puzzle whale in a blue box with a smiling tail",
        huge_line="Even its box seemed broad enough to sail from one end of story hour to the other.",
        movement_line="The box tucked under one arm, though it still made the bag bulge like a loaf of bread.",
        size=2,
        tags={"puzzle", "whale"},
    ),
}

SIGNS = {
    "transfer_cart": Sign(
        id="transfer_cart",
        text="TRANSFER CART",
        child_guess='that "transfer" must mean a toy could move from library life into forever-home life',
        real_meaning="The sign had only meant that toys were to be moved between shelves, desks, and returns before the borrowing was written down.",
        tags={"transfer", "misunderstanding"},
    ),
    "transfer_queue": Sign(
        id="transfer_queue",
        text="TRANSFER TO CHECKOUT",
        child_guess='that a toy waiting there had already chosen its next family and simply needed a bag',
        real_meaning="The sign had meant the toy was waiting for staff to move it toward checkout, not to vanish from the shared shelves forever.",
        tags={"transfer", "misunderstanding", "checkout"},
    ),
}

HELPER_MOVES = {
    "gentle_steps": HelperMove(
        id="gentle_steps",
        explain_line="with a voice so soft it could have shelved a storm,",
        process_line="First we move it where the desk can see it. Then we write your name on the borrowing slip. Then you may take it home until return day.",
        ending_line="The librarian checked the return with a nod and rolled it back into the shared collection, ready for the next child.",
        tags={"explain", "process"},
    ),
    "stamp_and_smile": HelperMove(
        id="stamp_and_smile",
        explain_line="tapping the cart with one finger as if waking up the true meaning of the word,",
        process_line="A toy has to be transferred through the library's steps before anyone borrows it, and after that it must come back so another child can love it too.",
        ending_line="A neat stamp landed on the return card, and the toy set off toward the shelves again like a hero headed home.",
        tags={"explain", "process", "return"},
    ),
}

GIRL_NAMES = ["Mabel", "Tess", "Nora", "Lila", "Ada", "Ruby"]
BOY_NAMES = ["Jasper", "Milo", "Theo", "Bram", "Otis", "Ned"]


KNOWLEDGE = {
    "library": [
        (
            "What is a toy library?",
            "A toy library is a place where families can borrow toys for a while and bring them back later. It works a bit like a book library, but with toys instead of books.",
        )
    ],
    "borrow": [
        (
            "What does it mean to borrow a toy?",
            "Borrowing means you may take the toy home for some time, but it still belongs to the shared library. Later, you return it so someone else can enjoy it too.",
        )
    ],
    "return": [
        (
            "Why do people return borrowed toys?",
            "They return borrowed toys so the toy can be shared fairly with other children. Returning it also helps the library keep track of where everything belongs.",
        )
    ],
    "transfer": [
        (
            "What does transfer mean?",
            "Transfer means to move something from one place or person to another. In a library, it can mean moving an item through the proper steps, not giving it away forever.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks a word or situation means one thing, but it really means something else. Talking and explaining can clear it up.",
        )
    ],
    "checkout": [
        (
            "What happens at checkout in a library?",
            "At checkout, a grown-up or librarian records who is borrowing the item. That way the library knows the item is out and when it should come back.",
        )
    ],
}
KNOWLEDGE_ORDER = ["library", "borrow", "return", "transfer", "misunderstanding", "checkout"]


@dataclass
class StoryParams:
    setting: str
    sign: str
    toy: str
    helper_move: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
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


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    sign = world.facts["sign"]
    toy_cfg = world.facts["toy_cfg"]
    return [
        f'Write a tall-tale style story for ages 3 to 5 set in a toy library that uses the word "transfer".',
        f"Tell a gentle misunderstanding story where {child.label} sees a sign reading {sign.text!r}, guesses the wrong meaning, and tries to take a {toy_cfg.label} home before a librarian explains the proper borrowing steps.",
        f'Write a child-facing story with a big, funny toy-library mix-up, a calm explanation, and an ending that shows the toy being borrowed and later returned the right way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    sign = world.facts["sign"]
    toy_cfg = world.facts["toy_cfg"]
    setting = world.facts["setting"]
    move = world.facts["move"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child visiting {setting.place}, and {helper.label}, the librarian who helps explain the mix-up.",
        ),
        (
            "What did the child see that started the problem?",
            f"{child.label} saw a sign that said {sign.text!r}. {child.pronoun().capitalize()} guessed that transfer meant the toy could move into {child.pronoun('possessive')} bag forever, and that wrong guess started the trouble.",
        ),
        (
            f"Why did the misunderstanding become such a big scene?",
            f"The chosen toy was a {toy_cfg.label}, and it was far too grand to slip away quietly. When {child.label} tried to move it, the whole room noticed because the toy was bulky and made a cheerful commotion.",
        ),
        (
            f"How did the librarian fix the misunderstanding?",
            f"{helper.label} did not scold. {helper.pronoun().capitalize()} explained that transfer meant moving the toy through the library's own steps first, and then borrowing it properly through checkout.",
        ),
        (
            "How did the story end?",
            f"The toy was borrowed the right way and later returned to {setting.return_spot}. That ending shows {child.label} had learned the toy still belonged to everyone, even after a proper transfer and checkout.",
        ),
    ]
    if world.facts.get("checked_out"):
        qa.append(
            (
                "What were the proper steps for the toy?",
                f"The toy went from the shelf to the transfer cart and then to the desk for checkout. {move.process_line}",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["setting"].tags) | set(world.facts["sign"].tags)
    if "checkout" in world.facts["sign"].tags:
        tags.add("checkout")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="toy_library",
        sign="transfer_cart",
        toy="dragon_wagon",
        helper_move="gentle_steps",
        child_name="Mabel",
        child_gender="girl",
        helper_name="Ms. Juniper",
        helper_type="librarian_f",
    ),
    StoryParams(
        setting="toy_library",
        sign="transfer_queue",
        toy="moon_train",
        helper_move="stamp_and_smile",
        child_name="Jasper",
        child_gender="boy",
        helper_name="Mr. Reed",
        helper_type="librarian_m",
    ),
    StoryParams(
        setting="toy_library",
        sign="transfer_cart",
        toy="castle_crate",
        helper_move="stamp_and_smile",
        child_name="Ruby",
        child_gender="girl",
        helper_name="Ms. Vale",
        helper_type="librarian_f",
    ),
    StoryParams(
        setting="toy_library",
        sign="transfer_queue",
        toy="puzzle_whale",
        helper_move="gentle_steps",
        child_name="Theo",
        child_gender="boy",
        helper_name="Mr. Pine",
        helper_type="librarian_m",
    ),
]


def explain_rejection(sign: Sign, toy: Toy) -> str:
    return (
        f"(No story: {sign.text!r} would not make a strong misunderstanding with {toy.label}. "
        f"This world only tells cases where the word 'transfer' plus a big enough toy can honestly create a visible mix-up.)"
    )


ASP_RULES = r"""
misunderstanding_possible(S,T) :- sign(S), toy(T), sign_has_transfer(S), toy_size(T,N), N >= 2.
valid(Setting,S,T) :- setting(Setting), sign(S), toy(T), misunderstanding_possible(S,T).

commotion(T) :- toy_size(T,N), N >= 3.

#show valid/3.
#show commotion/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        if "transfer" in sign.text.lower():
            lines.append(asp.fact("sign_has_transfer", sid))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("toy_size", tid, toy.size))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_commotion_toys() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(t for (t,) in asp.atoms(model, "commotion"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_commotion = {toy_id for toy_id, toy in TOYS.items() if predict_commotion(toy)}
    asp_commotion = set(asp_commotion_toys())
    if py_commotion == asp_commotion:
        print(f"OK: commotion rule matches ({sorted(py_commotion)}).")
    else:
        rc = 1
        print(f"MISMATCH in commotion toys: clingo={sorted(asp_commotion)} python={sorted(py_commotion)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a tall-tale misunderstanding about a transfer cart in a toy library."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--helper-move", choices=HELPER_MOVES, dest="helper_move")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.toy:
        sign = SIGNS[args.sign]
        toy = TOYS[args.toy]
        if not misunderstanding_possible(sign, toy):
            raise StoryError(explain_rejection(sign, toy))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.sign is None or c[1] == args.sign)
        and (args.toy is None or c[2] == args.toy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sign_id, toy_id = rng.choice(sorted(combos))
    helper_move = args.helper_move or rng.choice(sorted(HELPER_MOVES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = rng.choice(["librarian_f", "librarian_m"])
    helper_name = rng.choice(["Ms. Juniper", "Ms. Vale", "Ms. Poppy"] if helper_type == "librarian_f"
                             else ["Mr. Reed", "Mr. Pine", "Mr. Lark"])
    return StoryParams(
        setting=setting_id,
        sign=sign_id,
        toy=toy_id,
        helper_move=helper_move,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")
    if params.helper_move not in HELPER_MOVES:
        raise StoryError(f"(Unknown helper move: {params.helper_move})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper_type not in {"librarian_f", "librarian_m"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    sign = SIGNS[params.sign]
    toy = TOYS[params.toy]
    if not misunderstanding_possible(sign, toy):
        raise StoryError(explain_rejection(sign, toy))

    world = tell(
        setting=SETTINGS[params.setting],
        sign=sign,
        toy_cfg=toy,
        move=HELPER_MOVES[params.helper_move],
        child_name=params.child_name,
        child_type=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name).replace("helper", params.helper_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, sign, toy) combos:\n")
        for setting_id, sign_id, toy_id in combos:
            comet = "commotion" if toy_id in asp_commotion_toys() else "quiet"
            print(f"  {setting_id:12} {sign_id:15} {toy_id:12} [{comet}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.toy} with {p.sign}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
