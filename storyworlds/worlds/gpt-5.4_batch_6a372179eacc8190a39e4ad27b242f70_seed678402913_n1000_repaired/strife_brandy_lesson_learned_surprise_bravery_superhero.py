#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/strife_brandy_lesson_learned_surprise_bravery_superhero.py

A standalone storyworld about a child in a superhero costume who meets a real
problem at a neighborhood celebration. The child wants to act bold, but the
world only accepts solutions that are sensible for the height of the problem
and the kind of object that is stuck. The surprise helper is always Brandy, a
small dog with a red bandana.

Seed words and features rebuilt as world state:
- strife: a public little crisis at a festive place
- brandy: Brandy is the dog helper
- lesson learned: bravery means choosing a safe, helpful plan
- surprise: Brandy unexpectedly finds the right tool
- bravery: the child speaks up, stays calm, and gets help wisely

Run it
------
python storyworlds/worlds/gpt-5.4/strife_brandy_lesson_learned_surprise_bravery_superhero.py
python storyworlds/worlds/gpt-5.4/strife_brandy_lesson_learned_surprise_bravery_superhero.py --item banner --perch branch
python storyworlds/worlds/gpt-5.4/strife_brandy_lesson_learned_surprise_bravery_superhero.py --solution trampoline
python storyworlds/worlds/gpt-5.4/strife_brandy_lesson_learned_surprise_bravery_superhero.py --all --qa
python storyworlds/worlds/gpt-5.4/strife_brandy_lesson_learned_surprise_bravery_superhero.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        dog = {"dog", "puppy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    crowd: str
    detail: str
    tool_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    use: str
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    height: int
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    reach: int
    capacity: int
    sense: int
    method: str
    surprise: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    perch: str
    solution: str
    hero_name: str
    hero_gender: str
    parent: str
    title_word: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_calm_after_recovery(world: World) -> list[str]:
    trouble = world.get("trouble")
    if trouble.meters["solved"] < THRESHOLD:
        return []
    sig = ("calm", "square")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    square = world.get("square")
    square.meters["strife"] = 0.0
    for eid in ("hero", "parent", "brandy"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="calm_after_recovery", tag="social", apply=_r_calm_after_recovery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "square": Place(
        id="square",
        label="the town square",
        crowd="neighbors in paper masks and bright capes",
        detail="streamers fluttered between the lamp posts, and a toy drum line kept thump-thumping by the fountain",
        tool_spot="the storage shed beside the fountain",
        tags={"festival"},
    ),
    "park": Place(
        id="park",
        label="the park",
        crowd="families near the bandstand",
        detail="a comic-book banner snapped above the snack tables while children dashed between chalk stars on the path",
        tool_spot="the little garden shed by the hedge",
        tags={"festival"},
    ),
    "library": Place(
        id="library",
        label="the library plaza",
        crowd="readers and stroller-pushing grown-ups",
        detail="a cape-making table rustled near the steps, and bright paper stars bobbed in the wind",
        tool_spot="the janitor closet just inside the side door",
        tags={"festival", "library"},
    ),
}

ITEMS = {
    "banner": Item(
        id="banner",
        label="banner",
        phrase="the big blue hero banner",
        use="the parade could not begin without it hanging straight",
        weight=1,
        tags={"banner"},
    ),
    "hat": Item(
        id="hat",
        label="hat",
        phrase="the mayor's shiny parade hat",
        use="the speech felt all wrong without it",
        weight=1,
        tags={"hat"},
    ),
    "satchel": Item(
        id="satchel",
        label="satchel",
        phrase="the librarian's star-sticker satchel",
        use="it held the story cards for the children",
        weight=2,
        tags={"satchel", "library"},
    ),
}

PERCHES = {
    "branch": Perch(
        id="branch",
        label="branch",
        phrase="a low branch over the path",
        height=1,
        risk="a child might still slip if a jump went wrong",
        tags={"tree"},
    ),
    "roof": Perch(
        id="roof",
        label="roof",
        phrase="the flat snack-stall roof",
        height=2,
        risk="a climb would be shaky and much too high for play",
        tags={"roof"},
    ),
    "statue": Perch(
        id="statue",
        label="statue arm",
        phrase="the bronze hero statue's outstretched arm",
        height=2,
        risk="the stone base was high and hard underfoot",
        tags={"statue"},
    ),
    "ledge": Perch(
        id="ledge",
        label="ledge",
        phrase="the high clock ledge",
        height=3,
        risk="a fall from there would be very dangerous",
        tags={"high"},
    ),
}

SOLUTIONS = {
    "grabber": Solution(
        id="grabber",
        label="grabber",
        phrase="the long grabber tool",
        reach=1,
        capacity=1,
        sense=3,
        method="held the handle steady while the grown-up pinched the stuck thing free",
        surprise="Brandy vanished for one second and came trotting back with the bright orange handle dragging behind him",
        qa_text="used a long grabber tool to pinch it free",
        tags={"grabber", "ask_adult"},
    ),
    "ladder": Solution(
        id="ladder",
        label="ladder",
        phrase="the folding ladder",
        reach=3,
        capacity=2,
        sense=3,
        method="kept the feet of the ladder from wobbling while the grown-up climbed just high enough to reach the stuck thing",
        surprise="Before anyone found the shed key, Brandy barked at the open side gate, where the folding ladder was already leaning against the wall",
        qa_text="used a ladder while the child kept it steady",
        tags={"ladder", "ask_adult"},
    ),
    "hookpole": Solution(
        id="hookpole",
        label="hook pole",
        phrase="the padded hook pole",
        reach=3,
        capacity=2,
        sense=2,
        method="guided the padded hook under the stuck thing and eased it down instead of yanking",
        surprise="Brandy spun in a happy circle beside a long pole tucked behind a planter, as if he had known it was there all along",
        qa_text="used a padded hook pole to ease it down",
        tags={"pole", "ask_adult"},
    ),
    "trampoline": Solution(
        id="trampoline",
        label="trampoline",
        phrase="a little trampoline",
        reach=1,
        capacity=1,
        sense=1,
        method="",
        surprise="",
        qa_text="",
        tags={"reckless"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Ava", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Max", "Sam", "Eli", "Theo", "Ben"]
TITLE_WORDS = ["Comet", "Thunder", "Starlight", "Rocket", "Spark", "Meteor"]


def can_reach(solution: Solution, perch: Perch) -> bool:
    return solution.reach >= perch.height


def can_carry(solution: Solution, item: Item) -> bool:
    return solution.capacity >= item.weight


def valid_combo(item: Item, perch: Perch, solution: Solution) -> bool:
    return solution.sense >= SENSE_MIN and can_reach(solution, perch) and can_carry(solution, item)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for perch_id, perch in PERCHES.items():
            for sol_id, solution in SOLUTIONS.items():
                if valid_combo(item, perch, solution):
                    combos.append((item_id, perch_id, sol_id))
    return combos


def explain_solution(solution: Solution) -> str:
    return (
        f"(Refusing solution '{solution.id}': it scores too low on common sense "
        f"(sense={solution.sense} < {SENSE_MIN}). Real bravery in this world means using a safe plan, not bouncing at danger.)"
    )


def explain_combo(item: Item, perch: Perch, solution: Solution) -> str:
    if solution.sense < SENSE_MIN:
        return explain_solution(solution)
    if not can_reach(solution, perch):
        return (
            f"(No story: {solution.phrase} cannot reach {perch.phrase}. "
            f"Pick a taller tool for something that high.)"
        )
    if not can_carry(solution, item):
        return (
            f"(No story: {solution.phrase} is too weak to bring down {item.phrase} safely. "
            f"Pick a sturdier tool.)"
        )
    return "(No story: that combination does not make physical sense.)"


def predict_reckless_climb(world: World, perch: Perch) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["risk"] += perch.height
    hero.memes["worry"] += 1
    return {"risk": hero.meters["risk"], "worry": hero.memes["worry"]}


def introduce(world: World, hero: Entity, parent: Entity, brandy: Entity, place: Place, title_word: str) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} pulled on a paper cape and whispered {title_word} power words under {hero.pronoun('possessive')} breath as {hero.pronoun()} walked with {hero.pronoun('possessive')} {parent.label_word} and little dog Brandy into {place.label}."
    )
    world.say(
        f"There were {place.crowd}, and {place.detail}."
    )
    world.say(
        f"Brandy's red bandana flapped like a tiny hero cape of its own."
    )


def trouble_begins(world: World, hero: Entity, item: Item, perch: Perch, place: Place) -> None:
    square = world.get("square")
    trouble = world.get("trouble")
    square.meters["strife"] += 1
    trouble.meters["stuck"] += 1
    hero.memes["alert"] += 1
    world.say(
        f"Then a sharp gust made a bit of strife in the middle of the fun. {item.phrase.capitalize()} flew up and landed on {perch.phrase}, and suddenly everyone was pointing at the same problem."
    )
    world.say(
        f"Without it, {item.use}."
    )


def reckless_idea(world: World, hero: Entity, perch: Perch, parent: Entity) -> None:
    pred = predict_reckless_climb(world, perch)
    world.facts["predicted_risk"] = pred["risk"]
    hero.memes["bravado"] += 1
    world.say(
        f'"I can get it!" {hero.id} cried, squaring {hero.pronoun("possessive")} shoulders like a comic-book hero. But {parent.label_word} looked up at {perch.phrase} and knew {perch.risk}.'
    )


def brave_choice(world: World, hero: Entity, parent: Entity, perch: Perch) -> None:
    hero.memes["bravery"] += 1
    hero.memes["care"] += 1
    world.say(
        f'{parent.label_word.capitalize()} touched {hero.pronoun("possessive")} cape and said, "The brave thing is not pretending you cannot fall."'
    )
    world.say(
        f"{hero.id} took one deep breath, looked up at {perch.phrase} again, and nodded. {hero.pronoun().capitalize()} chose not to climb."
    )
    world.say(
        f'"I can still help," {hero.pronoun()} said. "I will get the right grown-up tool and keep everyone back."'
    )


def surprise_tool(world: World, brandy: Entity, place: Place, solution: Solution) -> None:
    brandy.memes["joy"] += 1
    world.say(
        f"They hurried toward {place.tool_spot}, but the surprise came first: {solution.surprise}"
    )


def recover_item(world: World, hero: Entity, parent: Entity, item: Item, solution: Solution) -> None:
    trouble = world.get("trouble")
    trouble.meters["stuck"] = 0.0
    trouble.meters["solved"] += 1
    world.say(
        f"Soon {parent.label_word} and {hero.id} were working together. {hero.id} {solution.method}, and {parent.label_word} brought {item.phrase} safely down."
    )
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, parent: Entity, brandy: Entity, item: Item, place: Place, title_word: str) -> None:
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"The worried noise around {place.label} melted into cheers. Someone tied {item.phrase} back where it belonged, and Brandy barked as if he wanted a cheer too."
    )
    world.say(
        f'{parent.label_word.capitalize()} hugged {hero.id} and smiled. "That was real {title_word.lower()} bravery," {parent.pronoun()} said. "You were brave enough to choose the safe plan."'
    )
    world.say(
        f"{hero.id} grinned and scratched Brandy behind the ears. From then on, the cape felt different: not like a promise to leap at everything, but like a reminder to help with a clear head and a kind heart."
    )


def tell(
    place: Place,
    item: Item,
    perch: Perch,
    solution: Solution,
    hero_name: str,
    hero_gender: str,
    parent_type: str,
    title_word: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    brandy = world.add(Entity(id="brandy", kind="character", type="dog", label="Brandy", phrase="Brandy", role="helper"))
    square = world.add(Entity(id="square", type="place", label=place.label))
    trouble = world.add(Entity(id="trouble", type="problem", label=item.label))
    hero.attrs["name"] = hero_name
    parent.attrs["title_word"] = title_word

    introduce(world, hero, parent, brandy, place, title_word)
    world.para()
    trouble_begins(world, hero, item, perch, place)
    reckless_idea(world, hero, perch, parent)
    brave_choice(world, hero, parent, perch)
    world.para()
    surprise_tool(world, brandy, place, solution)
    recover_item(world, hero, parent, item, solution)
    ending(world, hero, parent, brandy, item, place, title_word)

    world.facts.update(
        place=place,
        item=item,
        perch=perch,
        solution=solution,
        hero=hero,
        parent=parent,
        brandy=brandy,
        title_word=title_word,
        solved=trouble.meters["solved"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ask_adult": [
        (
            "What should a child do if something important is stuck up high?",
            "A child should stop, stay on the ground, and ask a grown-up for help. Heights can turn a game into an accident very quickly."
        )
    ],
    "bravery": [
        (
            "What is real bravery?",
            "Real bravery means doing the safe and helpful thing even when you feel excited. It is not the same as taking a dangerous chance."
        )
    ],
    "ladder": [
        (
            "Why must a ladder be used carefully?",
            "A ladder can help you reach high places, but it must stand on the ground and stay steady. That is why grown-ups use it carefully."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber tool is a long tool with a squeezing end that can pick up light things from a little farther away. It helps you reach without climbing."
        )
    ],
    "pole": [
        (
            "What does a hook pole do?",
            "A hook pole can catch or guide something down from a high spot. It works best when someone uses it slowly and carefully."
        )
    ],
    "dog": [
        (
            "How can a dog help people?",
            "A dog can notice things quickly, bark when something is wrong, and lead people to what they need. Dogs do not use words, but they can still be very helpful."
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long piece of cloth with words or pictures on it. People hang banners so others can see them from far away."
        )
    ],
    "hat": [
        (
            "Why might a parade hat matter?",
            "A special hat can be part of a celebration or a costume. When it is missing, the event can feel unfinished."
        )
    ],
    "satchel": [
        (
            "What is a satchel?",
            "A satchel is a bag with a strap that carries books, papers, or small supplies. People often wear it over a shoulder."
        )
    ],
}
KNOWLEDGE_ORDER = ["bravery", "ask_adult", "dog", "ladder", "grabber", "pole", "banner", "hat", "satchel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    perch = f["perch"]
    place = f["place"]
    title_word = f["title_word"]
    name = hero.attrs["name"]
    return [
        f'Write a superhero-style story for a 3-to-5-year-old that includes the words "strife" and "Brandy".',
        f"Tell a gentle hero story where {name} wants to act like {title_word}, but learns that real bravery means not climbing for {item.label} on {perch.phrase}.",
        f"Write a surprise rescue at {place.label} where a little dog helps find the safe tool and the crowd's strife turns into cheers.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item = f["item"]
    perch = f["perch"]
    solution = f["solution"]
    place = f["place"]
    name = hero.attrs["name"]
    pw = parent.label_word
    qa = [
        (
            "Who is the story about?",
            f"It is about {name}, a child in a superhero cape, {name}'s {pw}, and a little dog named Brandy. They are all at {place.label} when the problem begins."
        ),
        (
            "What caused the strife?",
            f"A gust blew {item.phrase} onto {perch.phrase}, and people grew worried because {item.use}. The happy celebration suddenly had one shared problem in the middle of it."
        ),
        (
            f"Why did {name} decide not to climb?",
            f"{name} first wanted to rush in like a comic-book hero, but {pw} reminded {hero.pronoun('object')} that {perch.risk}. {name} showed bravery by choosing a safe plan instead of a dangerous one."
        ),
        (
            "What was the surprise?",
            f"The surprise was that Brandy helped them find {solution.phrase} before the grown-ups had even finished looking. His quick help changed the mood from worry to hope."
        ),
        (
            f"How did they solve the problem?",
            f"They worked together and {solution.qa_text}. {name} helped in a safe way, and that teamwork brought {item.label} down without anyone climbing recklessly."
        ),
        (
            "What lesson did the child learn?",
            f"{name} learned that real bravery is not leaping at every danger. It means stopping, thinking, and helping wisely so everyone stays safe."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bravery", "dog"}
    tags |= set(f["solution"].tags)
    tags |= set(f["item"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="square",
        item="banner",
        perch="branch",
        solution="grabber",
        hero_name="Lily",
        hero_gender="girl",
        parent="mother",
        title_word="Comet",
    ),
    StoryParams(
        place="park",
        item="hat",
        perch="roof",
        solution="ladder",
        hero_name="Max",
        hero_gender="boy",
        parent="father",
        title_word="Thunder",
    ),
    StoryParams(
        place="library",
        item="satchel",
        perch="ledge",
        solution="hookpole",
        hero_name="Nora",
        hero_gender="girl",
        parent="mother",
        title_word="Starlight",
    ),
]


ASP_RULES = r"""
reachable(S, P) :- solution(S), perch(P), reach(S, R), height(P, H), R >= H.
strong_enough(S, I) :- solution(S), item(I), capacity(S, C), weight(I, W), C >= W.
sensible(S) :- solution(S), sense(S, V), sense_min(M), V >= M.
valid(I, P, S) :- item(I), perch(P), solution(S), reachable(S, P), strong_enough(S, I), sensible(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("weight", item_id, item.weight))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("height", perch_id, perch.height))
    for sol_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", sol_id))
        lines.append(asp.fact("reach", sol_id, solution.reach))
        lines.append(asp.fact("capacity", sol_id, solution.capacity))
        lines.append(asp.fact("sense", sol_id, solution.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP combo gates:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False)
        print("\nOK: smoke test story generated and emitted.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child in a superhero cape learns that real bravery means choosing a safe plan."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (item, perch, solution) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        raise StoryError(explain_solution(SOLUTIONS[args.solution]))
    if args.item and args.perch and args.solution:
        item = ITEMS[args.item]
        perch = PERCHES[args.perch]
        solution = SOLUTIONS[args.solution]
        if not valid_combo(item, perch, solution):
            raise StoryError(explain_combo(item, perch, solution))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.perch is None or combo[1] == args.perch)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, perch_id, solution_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    title_word = rng.choice(TITLE_WORDS)
    place = args.place or rng.choice(sorted(PLACES))
    return StoryParams(
        place=place,
        item=item_id,
        perch=perch_id,
        solution=solution_id,
        hero_name=hero_name,
        hero_gender=gender,
        parent=parent,
        title_word=title_word,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    perch = PERCHES[params.perch]
    solution = SOLUTIONS[params.solution]
    if not valid_combo(item, perch, solution):
        raise StoryError(explain_combo(item, perch, solution))

    world = tell(
        place=place,
        item=item,
        perch=perch,
        solution=solution,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        title_word=params.title_word,
    )
    world.render().format
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("parent", PLACES[params.place].label if False else world.render()),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def _story_with_names(sample: StorySample) -> str:
    text = sample.story
    hero_name = sample.params.hero_name
    pw = "mom" if sample.params.parent == "mother" else "dad"
    text = text.replace("hero", hero_name)
    text = text.replace("parent", pw)
    return text


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    story = sample.story
    print(story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, perch, solution) combos:\n")
        for item, perch, solution in combos:
            print(f"  {item:8} {perch:8} {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for i, params in enumerate(CURATED):
            cloned = StoryParams(
                place=params.place,
                item=params.item,
                perch=params.perch,
                solution=params.solution,
                hero_name=params.hero_name,
                hero_gender=params.hero_gender,
                parent=params.parent,
                title_word=params.title_word,
                seed=base_seed + i,
            )
            samples.append(generate(cloned))
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
            header = f"### {p.hero_name}: {p.item} on {p.perch} with {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
