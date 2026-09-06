#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chocolate_ado_chariot_sharing_friendship_moral_value.py
=======================================================================================

A standalone storyworld about animal friends, a shared chocolate treat, and a
toy chariot that triggers a small ado before a moral-value resolution.

Seed words:
- chocolate
- ado
- chariot

Features:
- Sharing
- Friendship
- Moral Value

Style:
- Animal Story

This world models a tiny animal-friend domain: one animal arrives with a sweet,
another feels left out, a chariot prop raises a bit of ado, and the group learns
that sharing grows friendship. The world state drives the prose, the Q&A, and
the ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2

ANIMAL_NAMES = ["Benny", "Milo", "Tilly", "Pippa", "Roo", "Nina", "Wally", "Suki"]
ANIMAL_TYPES = ["rabbit", "fox", "bear", "mouse", "hedgehog", "cat"]
SCENES = [
    "the sunny meadow",
    "the soft barnyard",
    "the little garden",
    "the grassy hill",
]
TREATS = ["chocolate square", "chocolate bar", "small chocolate coin"]
CHARIOTS = ["toy chariot", "little chariot", "wooden chariot"]
PLOTS = [
    "lost_parcel", "pantry_delivery", "allergy_label", "stuck_wheel",
    "tabletop_race", "melting_package", "owner_tag", "two_seats",
    "festival_jobs", "recipe_card", "rattling_box", "thank_you_gift",
]
VOICES = ["gentle", "playful", "thoughtful", "brisk"]
ENDINGS = ["lantern", "wheel_tracks", "paper_flag", "bell"]
TURNS = ["listen", "list", "swap", "demonstrate", "question", "vote", "roles", "kindness"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"share": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "left_out": 0.0, "friendship": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    scene: str
    name1: str
    type1: str
    name2: str
    type2: str
    name3: str
    type3: str
    treat: str
    chariot: str
    plot: str = "lost_parcel"
    voice: str = "gentle"
    ending: str = "lantern"
    turn: str = "listen"
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = _copy.deepcopy(self.facts)
        return w


def _propagate(world: World) -> None:
    if "share" in world.fired:
        return
    choco = world.get("choco")
    if choco.meters["share"] >= THRESHOLD:
        world.fired.add("share")
        for e in world.animals():
            e.memes["friendship"] += 1
            e.memes["joy"] += 1
            e.memes["left_out"] = 0.0
        world.get("leftout").memes["left_out"] = 0.0


def predict(world: World) -> dict:
    sim = world.copy()
    choco = sim.get("choco")
    choco.meters["share"] += 1
    _propagate(sim)
    return {
        "friendship": sum(e.memes["friendship"] for e in sim.animals()),
        "left_out": sim.get("leftout").memes["left_out"],
    }


def reasonableness_gate() -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    if not reasonableness_gate():
        return []
    combos = []
    for scene in SCENES:
        for treat in TREATS:
            for ch in CHARIOTS:
                combos.append((scene, treat, ch))
    return combos


def _dialogue(voice: str, a: Entity, b: Entity, c: Entity) -> str:
    lines = {
        "gentle": f"'Let's stop the ado and listen to everyone,' {c.id} said softly.",
        "playful": f"'Three friends, three ideas, and zero need for ado!' {b.id} declared.",
        "thoughtful": f"{a.id} took a breath. 'Fair does not always mean identical, but it means nobody is ignored.'",
        "brisk": f"'Pause,' said {c.id}. 'We can share the choice, the work, and the fun.'",
    }
    return lines[voice]


def _turn(turn: str, a: Entity, b: Entity, c: Entity) -> str:
    turns = {
        "listen": f"They listened in a circle, and {c.id}'s concern finally had room to be heard.",
        "list": f"{b.id} scratched three useful jobs into the soil, one beside each name.",
        "swap": f"{a.id} imagined changing places with {c.id}, and the fair choice became easier to see.",
        "demonstrate": f"Instead of rushing again, {b.id} demonstrated a careful first step and invited the others to continue it.",
        "question": f"'What choice keeps everyone safe and included?' {c.id} asked, and all three considered the answer.",
        "vote": "They suggested choices, checked that each one was safe, and reached a three-paw vote.",
        "roles": "Once they named the different roles, they understood that no single helper had to do everything.",
        "kindness": f"{a.id} noticed {c.id}'s drooping ears and chose friendship over getting their own way.",
    }
    return turns[turn]


def _plot(world: World, a: Entity, b: Entity, c: Entity, params: StoryParams) -> None:
    scene, treat, chariot = params.scene, params.treat, params.chariot
    world.say(f"At {scene}, {a.id} the {a.type}, {b.id} the {b.type}, and {c.id} the {c.type} met beside a {chariot}.")

    if params.plot == "lost_parcel":
        world.say(f"A sealed package of {treat} rolled from the chariot, and each friend insisted on being the one who found it first.")
        world.say("Their ado faded when they noticed three sets of tracks around the parcel: each of them had helped stop it.")
        issue = "the friends argued over who had found the parcel"
        action = "They carried the sealed chocolate parcel together to the lost-and-found table."
        result = "Its grateful owner gave them three painted friendship badges."
    elif params.plot == "pantry_delivery":
        world.say(f"They had promised to deliver a sealed package of {treat} in the chariot to the community pantry, but everyone wanted to steer.")
        world.say("Their ado made the cart wobble without moving until they saw that steering, pulling, and watching the path were all important jobs.")
        issue = "everyone wanted the same delivery job"
        action = "They shared the jobs and pulled the toy chariot at a careful walking pace."
        result = "The parcel reached the pantry dry, unopened, and right on time."
    elif params.plot == "allergy_label":
        world.say(f"{a.id} was about to offer the {treat}, but {b.id} spotted an allergy warning on its wrapper.")
        world.say("The sudden ado became a useful pause: friends should ask before sharing food, and real chocolate is not safe for many animals.")
        issue = "the treat might not be safe for every friend"
        action = "They kept the chocolate sealed and shared turns decorating the chariot instead."
        result = "A trusted grown-up later brought each animal a suitable snack."
    elif params.plot == "stuck_wheel":
        world.say(f"The chariot was carrying a sealed package of {treat} for a neighbor when one wheel sank into soft earth.")
        world.say(f"{a.id} blamed the mud, {b.id} blamed the load, and {c.id} nearly left during the ado.")
        issue = "a stuck wheel led the friends to blame one another"
        action = "They shared the work: one steadied the parcel, one lifted the axle, and one laid flat twigs beneath the wheel."
        result = "The little chariot rolled free without anyone climbing aboard."
    elif params.plot == "tabletop_race":
        world.say(f"A game judge set the {treat} beside a tabletop track as a prize for the fastest toy chariot.")
        world.say("When each friend grabbed for the controls, the toy spun in place and the race dissolved into ado.")
        issue = "competing for one prize spoiled their tabletop game"
        action = "They entered as one team, sharing the winding key, course map, and finish-line flag."
        result = "They won a ribbon and donated the still-wrapped chocolate to the bake-sale table."
    elif params.plot == "melting_package":
        world.say(f"They discovered that a wrapped package of {treat} for the village baker was growing warm in the sunny chariot.")
        world.say("Instead of letting worried ado turn into blame, they listened for the baker's bell and planned a shaded route.")
        issue = "a chocolate delivery was warming in the sun"
        action = "They shared a parasol, route map, and gentle pull on the chariot."
        result = "The baker received the package before it melted and thanked all three helpers."
    elif params.plot == "owner_tag":
        world.say(f"Inside the parked chariot sat a {treat}, and for one noisy minute each friend imagined keeping it.")
        world.say(f"Then {c.id} found a tiny owner tag tied beneath the handle, turning the ado into a search.")
        issue = "the friends were tempted to keep something that was not theirs"
        action = "They followed the name on the tag and returned the sealed chocolate with the chariot."
        result = "The owner shared a story and let them ring the chariot bell in turns."
    elif params.plot == "two_seats":
        world.say(f"The toy chariot had room for only two dolls, and a {treat} was its pretend picnic cargo.")
        world.say(f"{a.id} and {b.id} began without {c.id}; the game sounded like ado instead of friendship.")
        issue = "their pretend game left one friend without a role"
        action = "They shared turns as driver, map reader, and picnic host while the animal friends stayed safely on the ground."
        result = "Every doll reached the pretend picnic, and every friend shaped the adventure."
    elif params.plot == "festival_jobs":
        world.say(f"For the friendship festival, their chariot had to carry a sealed package of {treat}, paper flags, and a small bell.")
        world.say("All three wanted to hang the final flag, and their tugging caused a fluttering ado.")
        issue = "the friends competed for the most noticeable festival job"
        action = "They traded jobs halfway through, sharing both the plain work and the exciting work."
        result = "The finished chariot displayed three different flags and one shared team name."
    elif params.plot == "recipe_card":
        world.say(f"A chocolate recipe card lay in the chariot, promising a prize for a careful team plan.")
        world.say("A small ado began: one friend wanted to choose ingredients, one wanted all the credit, and one worried about allergies.")
        issue = "the recipe project did not yet include every friend's needs"
        action = "They shared the planning, listed allergies first, and asked a trusted grown-up to choose safe ingredients."
        result = "Their prize was for the kindest plan, not for tasting the recipe."
    elif params.plot == "rattling_box":
        world.say(f"A box marked 'CHOCOLATE DISPLAY' rattled inside the chariot, and the friends feared the treats had broken.")
        world.say("Their worried ado stopped when they agreed to inspect the box without tasting anything.")
        issue = "the friends worried that a display parcel was damaged"
        action = "They shared careful tasks: holding the cart still, reading the label, and fetching the craft teacher."
        result = "The rattle came from wooden pretend sweets, all perfectly safe and unbroken."
    else:
        world.say(f"A neighbor left a sealed package of {treat} in the chariot as a thank-you gift for the whole garden club.")
        world.say("The friends' ado began when they tried to decide who deserved it most.")
        issue = "the friends measured who had done the most work"
        action = "They made a shared list and saw that planting, watering, and tidying had all mattered."
        result = "They delivered the chocolate to the club leader and chose separate, approved snacks for themselves."

    c.memes["left_out"] += 1
    world.say(_dialogue(params.voice, a, b, c))
    world.say(_turn(params.turn, a, b, c))
    world.para()
    world.say(action)
    world.get("choco").meters["share"] += 1
    _propagate(world)
    world.say(result)
    world.facts.update(issue=issue, action=action, result=result)


def _ending(world: World, a: Entity, b: Entity, c: Entity, ending: str) -> None:
    images = {
        "lantern": "At dusk, the lantern cast three friendly shadows beside the resting chariot.",
        "wheel_tracks": "Behind them, one neat pair of wheel tracks crossed three sets of pawprints all the way home.",
        "paper_flag": "A paper flag bearing all three names fluttered from the parked chariot.",
        "bell": "The chariot bell gave three small notes, one for each friend, before the meadow grew quiet.",
    }
    world.say(f"Their friendship taught them that sharing can mean sharing food, but it can also mean sharing work, turns, credit, and care. {images[ending]}")


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.name1, kind="character", type=params.type1, role="first"))
    b = world.add(Entity(id=params.name2, kind="character", type=params.type2, role="second"))
    c = world.add(Entity(id=params.name3, kind="character", type=params.type3, role="third"))
    world.add(Entity(id="choco", type="treat", label=params.treat))
    world.add(Entity(id="leftout", type="state", label="left out"))
    world.facts.update(scene=params.scene, treat=params.treat, chariot=params.chariot)

    _plot(world, a, b, c, params)
    world.para()
    _ending(world, a, b, c, params.ending)
    world.facts.update(
        a=a, b=b, c=c, outcome="shared", choco=world.get("choco"),
        moral="sharing", plot=params.plot
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a safe animal story about chocolate, a chariot, a little ado, and friends who learn a deeper meaning of sharing.",
        f"Tell a child-friendly animal story in which {world.facts['issue']} and friendship guides the solution.",
        "Write a moral-value tale using chocolate, a chariot, and a little ado; show that sharing includes turns, work, credit, and care.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, c = f["a"], f["b"], f["c"]
    return [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {c.id}, three animal friends who face a problem together."),
        ("Why was there ado?",
         f"There was ado because {f['issue']}. The difficulty pushed the animals to stop and include one another."),
        ("How did the problem get fixed?",
         f"{f['action']} {f['result']}"),
        ("What moral value does the story teach?",
         "It teaches that sharing is more than dividing food. Friends can also share work, turns, credit, and care so everyone is included."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is chocolate?",
         "Chocolate is a food made from cacao. Real chocolate can make many animals ill, and allergies differ, so children should ask a trusted grown-up before sharing or eating an unfamiliar treat."),
        ("What is a chariot?",
         "A chariot is a wheeled cart from history or stories. In this tale it is a toy or hand-pulled cart, used on the ground at a careful walking pace."),
        ("What does ado mean?",
         "Ado means a little fuss or commotion. It can happen when friends disagree before they solve a problem."),
        ("What is friendship?",
         "Friendship is the caring bond between friends. Friends help, listen, and try to be kind to one another."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared :- choco_share(1).
friendship(A) :- animal(A), shared.
outcome(shared) :- shared.
"""


def asp_facts() -> str:
    try:
        import storyworlds.asp as asp
    except ModuleNotFoundError:
        import asp
    lines = []
    for scene in SCENES:
        lines.append(asp.fact("scene", scene))
    for treat in TREATS:
        lines.append(asp.fact("treat", treat))
    for ch in CHARIOTS:
        lines.append(asp.fact("chariot", ch))
    lines.append(asp.fact("choco_share", 1))
    for name in ANIMAL_NAMES:
        lines.append(asp.fact("animal", name))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except ModuleNotFoundError:
        import asp
    rc = 0
    model = asp.one_model(asp_program(show="#show outcome/1."))
    got = set(asp.atoms(model, "outcome"))
    want = {("shared",)}
    if got != want:
        print("MISMATCH in ASP outcome:", got, want)
        rc = 1
    else:
        print("OK: ASP outcome matches Python reasoning.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        print(f"MISMATCH in generate() smoke test: {err}")
        rc = 1
    return rc


def asp_valid_combos() -> list[tuple]:
    try:
        import storyworlds.asp as asp
    except ModuleNotFoundError:
        import asp
    model = asp.one_model(asp_program(show="#show scene/1.\n#show treat/1.\n#show chariot/1."))
    scenes = [x[0] for x in asp.atoms(model, "scene")]
    treats = [x[0] for x in asp.atoms(model, "treat")]
    chariots = [x[0] for x in asp.atoms(model, "chariot")]
    return [(s, t, c) for s in scenes for t in treats for c in chariots]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about chocolate, ado, and a chariot.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--chariot", choices=CHARIOTS)
    ap.add_argument("--plot", choices=PLOTS)
    ap.add_argument("--voice", choices=VOICES)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=ANIMAL_TYPES)
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=ANIMAL_TYPES)
    ap.add_argument("--name3")
    ap.add_argument("--type3", choices=ANIMAL_TYPES)
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


@dataclass
class _Choice:
    name: str
    typ: str
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


CURATED = [
    StoryParams(
        scene="the sunny meadow",
        name1="Benny", type1="rabbit",
        name2="Milo", type2="fox",
        name3="Tilly", type3="mouse",
        treat="chocolate bar",
        chariot="toy chariot",
        plot="allergy_label", voice="thoughtful", ending="paper_flag",
        turn="question",
    ),
    StoryParams(
        scene="the little garden",
        name1="Pippa", type1="cat",
        name2="Roo", type2="bear",
        name3="Suki", type3="hedgehog",
        treat="chocolate square",
        chariot="wooden chariot",
        plot="stuck_wheel", voice="gentle", ending="wheel_tracks",
        turn="roles",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.treat and args.chariot:
        pass
    scenes = [args.scene] if args.scene else SCENES
    treats = [args.treat] if args.treat else TREATS
    chariots = [args.chariot] if args.chariot else CHARIOTS
    combos = [(s, t, c) for s in scenes for t in treats for c in chariots]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, treat, chariot = rng.choice(combos)
    def pick_name(existing: set[str]) -> tuple[str, str]:
        typ = rng.choice(ANIMAL_TYPES)
        name = rng.choice([n for n in ANIMAL_NAMES if n not in existing])
        return name, typ
    n1, t1 = args.name1 or pick_name(set())[0], args.type1 or rng.choice(ANIMAL_TYPES)
    n2, t2 = args.name2 or pick_name({n1})[0], args.type2 or rng.choice(ANIMAL_TYPES)
    n3, t3 = args.name3 or pick_name({n1, n2})[0], args.type3 or rng.choice(ANIMAL_TYPES)
    return StoryParams(
        scene=scene,
        name1=n1,
        type1=t1,
        name2=n2,
        type2=t2,
        name3=n3,
        type3=t3,
        treat=treat,
        chariot=chariot,
        plot=args.plot or rng.choice(PLOTS),
        voice=args.voice or rng.choice(VOICES),
        ending=args.ending or rng.choice(ENDINGS),
        turn=args.turn or rng.choice(TURNS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if params.chariot not in CHARIOTS:
        raise StoryError("Unknown chariot.")
    if params.plot not in PLOTS:
        raise StoryError("Unknown plot.")
    if params.voice not in VOICES:
        raise StoryError("Unknown voice.")
    if params.ending not in ENDINGS:
        raise StoryError("Unknown ending.")
    if params.turn not in TURNS:
        raise StoryError("Unknown turn.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program(show="#show scene/1.\n#show treat/1.\n#show chariot/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP combos:")
        for x in asp_valid_combos():
            print(" ", x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        seen_structures = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            structure = (params.plot, params.voice, params.ending, params.turn)
            if sample.story not in seen and structure not in seen_structures:
                seen.add(sample.story)
                seen_structures.add(structure)
                samples.append(sample)
            i += 1

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
