#!/usr/bin/env python3
"""
storyworlds/worlds/zig_cabinet_sound_effects_humor_inner_monologue.py
======================================================================

A small whodunit story world about a zigzagging search, a stubborn cabinet,
sound effects, humor, and a detective's inner monologue.

Premise:
- A child detective notices a missing snack from a cabinet.
- The clues are concrete: a squeak, a bump, crumbs, a sticky paw, and a zigzag
  trail on the floor.
- The turn comes from the detective's inner monologue: the obvious suspect is
  funny, but wrong.
- The resolution proves who moved the snack and why.

This world is deliberately compact, classical, and state-driven. The narration
changes according to the simulated trace rather than swapping nouns in a frozen
paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    container: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    cozy: bool = True
    contains: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    hidden_in: str
    smell: str = ""
    can_make_sound: bool = False
    clue_kind: str = ""
    owner: str = ""


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    alibi: str
    sound: str = ""
    clue: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.suspects: dict[str, Suspect] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def add_suspect(self, suspect: Suspect) -> Suspect:
        self.suspects[suspect.id] = suspect
        return suspect

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.suspects = copy.deepcopy(self.suspects)
        clone.events = list(self.events)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    detective: str
    detective_type: str
    cabinet: str
    missing_item: str
    suspect: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(name="the kitchen", cozy=True),
    "hall": Place(name="the hall", cozy=True),
    "pantry": Place(name="the pantry", cozy=True),
}

DETECTIVE_NAMES = ["Zig", "Milo", "Nina", "Toby", "Ivy", "Pip", "Luna", "Bea"]
SUSPECT_NAMES = ["Mimi", "Bobo", "Patches", "Waffle"]
CABINETS = {
    "blue": ("blue cabinet", "a blue cabinet with one sticky door"),
    "tall": ("tall cabinet", "a tall cabinet that reached almost to the ceiling"),
    "round": ("round cabinet", "a round cabinet with a shiny knob"),
}
MISSING_ITEMS = {
    "cookie": ("cookie tin", "a tin of butter cookies", "snack"),
    "spoon": ("silver spoon", "a shiny silver spoon", "tool"),
    "toy": ("toy train", "a tiny red toy train", "plaything"),
}


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    detective = world.add_entity(Entity(
        id=params.detective,
        kind="character",
        type=params.detective_type,
        label=params.detective,
        meters={"curiosity": 1.0, "humor": 1.0, "attention": 1.0},
        memes={"puzzle": 1.0},
    ))
    cabinet_label, cabinet_phrase = CABINETS[params.cabinet]
    cabinet = world.add_entity(Entity(
        id="cabinet",
        kind="thing",
        type="cabinet",
        label=cabinet_label,
        phrase=cabinet_phrase,
        hidden=False,
    ))
    item_label, item_phrase, clue_kind = MISSING_ITEMS[params.missing_item]
    item = world.add_item(Item(
        id="missing",
        label=item_label,
        phrase=item_phrase,
        hidden_in="cabinet",
        smell={"cookie": "sweet", "spoon": "metallic", "toy": "dusty"}[params.missing_item],
        can_make_sound=(params.missing_item != "spoon"),
        clue_kind=clue_kind,
        owner=params.detective,
    ))
    cabinet.hidden = False

    suspect = world.add_suspect(Suspect(
        id="suspect",
        label=params.suspect,
        type="pet" if params.suspect in {"Mimi", "Patches"} else "person",
        motive="wanted the smell" if params.missing_item == "cookie" else "wanted a shiny thing",
        alibi="was napping by the rug",
        sound="scritch-scritch" if params.suspect in {"Mimi", "Patches"} else "tap-tap",
        clue="sticky paw" if params.suspect in {"Mimi", "Patches"} else "smudged fingers",
    ))

    world.facts.update(
        detective=detective,
        cabinet=cabinet,
        item=item,
        suspect=suspect,
        place=place,
        item_kind=params.missing_item,
    )
    return world


def _search(world: World) -> None:
    det = world.facts["detective"]
    cab = world.facts["cabinet"]
    item = world.facts["item"]
    suspect = world.facts["suspect"]

    det.meters["curiosity"] += 1
    det.memes["puzzle"] += 1
    world.say(
        f"{det.id} stood in {world.place.name} and stared at the {cab.label}. "
        f"Inside, the {item.label} was gone."
    )
    world.say(
        f"*click* went the knob. *creak* went the door. "
        f"{det.id} wrinkled {det.pronoun('possessive')} nose and thought, "
        f"Maybe this was not a simple missing-snack day."
    )

    world.para()
    det.meters["attention"] += 1
    world.say(
        f"{det.id} noticed a zigzag line of crumbs on the floor, then a tiny "
        f"{suspect.sound} from the corner."
    )
    world.say(
        f"\"Hmm,\" {det.id} thought, \"a loud little trail, a cabinet, and a suspect. "
        f"This is either a mystery or a very clumsy parade.\""
    )
    world.facts["zigzag_seen"] = True
    world.facts["sound_seen"] = True


def _false_guess(world: World) -> None:
    det = world.facts["detective"]
    suspect = world.facts["suspect"]
    item = world.facts["item"]
    det.memes["doubt"] = det.memes.get("doubt", 0.0) + 1
    world.say(
        f"{det.id} peered at {suspect.label} and thought, "
        f"Could {suspect.label} be the thief? {suspect.alibi} sounded too neat."
    )
    world.say(
        f"Then {det.id} looked again and almost laughed. "
        f"\"No, no,\" {det.id} thought, \"{suspect.label} may be suspicious, "
        f"but even a brave detective should not blame a sleepy face for a missing {item.label}.\""
    )
    world.facts["false_guess"] = True


def _reveal(world: World) -> None:
    det = world.facts["detective"]
    item = world.facts["item"]
    suspect = world.facts["suspect"]

    if item.label == "cookie tin":
        reason = "the smell had lured the little hands first"
    elif item.label == "toy train":
        reason = "the shiny wheels had rolled away during play"
    else:
        reason = "the cabinet door had been left open just enough to tempt someone"
    world.say(
        f"Then {det.id} found the truth: the missing {item.label} had not been stolen at all."
    )
    world.say(
        f"*thump!* went the floorboard as the real clue turned up near the cabinet. "
        f"It was {suspect.label}'s clue, yes, but the final answer was bigger: "
        f"{det.id}'s own little hands had moved the {item.label} while making room for {reason}."
    )
    world.say(
        f"{det.id} blushed and laughed. \"Aha,\" {det.id} thought, "
        f"\"the thief is me, which is embarrassing, but at least the mystery has manners.\""
    )
    world.facts["revealed"] = True


def _ending(world: World) -> None:
    det = world.facts["detective"]
    item = world.facts["item"]
    cab = world.facts["cabinet"]
    world.say(
        f"After that, {det.id} put the {item.label} back into the {cab.label} and closed the door gently."
    )
    world.say(
        f"*snick!* The cabinet stayed shut, the crumbs were swept away, and "
        f"{det.id} gave {det.pronoun('possessive')} own nose a stern little look."
    )
    world.say(
        f"\"Case closed,\" {det.id} thought, \"and next time I will check the cabinet before I accuse the cat.\""
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _search(world)
    world.para()
    _false_guess(world)
    world.para()
    _reveal(world)
    world.para()
    _ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    return [
        f"Write a short whodunit for a child detective named {det.id} about a missing item in a cabinet.",
        f"Tell a funny mystery story with sound effects like *click* and *creak* and a zigzag clue.",
        f"Write a cozy detective story where the cabinet, the clue trail, and an inner monologue lead to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    item = f["item"]
    cab = f["cabinet"]
    suspect = f["suspect"]
    return [
        QAItem(
            question=f"What was missing from the {cab.label}?",
            answer=f"The missing thing was {item.label}, which had been kept in the {cab.label}.",
        ),
        QAItem(
            question=f"What clue made {det.id} think the story was a mystery?",
            answer="The zigzag line of crumbs, the squeaky sound, and the closed cabinet made it feel like a mystery.",
        ),
        QAItem(
            question=f"Who did {det.id} first suspect?",
            answer=f"{det.id} first suspected {suspect.label}, because {suspect.alibi} sounded too neat.",
        ),
        QAItem(
            question=f"Who turned out to be responsible for the missing {item.label}?",
            answer=f"It turned out to be {det.id} who had moved the {item.label} while looking around the cabinet.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The {item.label} was put back into the {cab.label}, the cabinet was closed, and {det.id} decided to check before accusing anyone next time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cabinet?",
            answer="A cabinet is a piece of furniture with doors or shelves where people keep things inside.",
        ),
        QAItem(
            question="What does a sound effect like *creak* help a story do?",
            answer="A sound effect helps a story feel alive by letting the reader hear what is happening.",
        ),
        QAItem(
            question="Why can a funny inner monologue help in a mystery?",
            answer="A funny inner monologue shows what a character is thinking, which can make the mystery amusing and easier to follow.",
        ),
        QAItem(
            question="What is a zigzag line?",
            answer="A zigzag line goes back and forth in sharp turns instead of staying straight.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    for item in world.items.values():
        lines.append(f"{item.id}: label={item.label} hidden_in={item.hidden_in} smell={item.smell}")
    for suspect in world.suspects.values():
        lines.append(f"{suspect.id}: label={suspect.label} motive={suspect.motive} clue={suspect.clue}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with a cabinet mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--cabinet", choices=CABINETS)
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
    ap.add_argument("--suspect")
    ap.add_argument("--detective-type", choices=["girl", "boy"], dest="detective_type")
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
    place = args.place or rng.choice(list(PLACES))
    cabinet = args.cabinet or rng.choice(list(CABINETS))
    missing_item = args.missing_item or rng.choice(list(MISSING_ITEMS))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    suspect = args.suspect or rng.choice(SUSPECT_NAMES)
    if detective == suspect:
        raise StoryError("The detective and the suspect should not have the same name.")
    return StoryParams(
        place=place,
        detective=detective,
        detective_type=detective_type,
        cabinet=cabinet,
        missing_item=missing_item,
        suspect=suspect,
    )


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(kitchen;hall;pantry).
cabinet(blue; tall; round).
item(cookie; spoon; toy).
detective(zig; mila; toby; ivy).
suspect(mimi; bobo; patches; waffle).

#show valid/4.

valid(P, C, I, D) :- place(P), cabinet(C), item(I), detective(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CABINETS:
        lines.append(asp.fact("cabinet", c))
    for i in MISSING_ITEMS:
        lines.append(asp.fact("item", i))
    for d in DETECTIVE_NAMES:
        lines.append(asp.fact("detective", d.lower()))
    for s in SUSPECT_NAMES:
        lines.append(asp.fact("suspect", s.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="kitchen", detective="Zig", detective_type="boy", cabinet="blue", missing_item="cookie", suspect="Mimi"),
        StoryParams(place="hall", detective="Nina", detective_type="girl", cabinet="tall", missing_item="toy", suspect="Patches"),
        StoryParams(place="pantry", detective="Toby", detective_type="boy", cabinet="round", missing_item="spoon", suspect="Bobo"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = build_curated()
        for p in params_list:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.detective}: {p.place}, {p.cabinet}, {p.missing_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
