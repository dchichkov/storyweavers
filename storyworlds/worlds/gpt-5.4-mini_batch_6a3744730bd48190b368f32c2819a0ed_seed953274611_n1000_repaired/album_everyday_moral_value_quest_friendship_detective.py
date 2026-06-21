#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/album_everyday_moral_value_quest_friendship_detective.py
=======================================================================================

A tiny detective storyworld about an everyday mystery, a friendship quest, and a
moral choice about returning something precious: an album full of memories.

The world is built for child-facing stories. The child-friendly detective notices
a problem, follows clues in the everyday world, weighs a moral value, and ends
with a concrete change in the album, the friendship, and the setting.

Includes:
- StoryParams and registries
- random generation with -n / --all / --seed
- trace / qa / json
- inline ASP twin with --asp / --verify / --show-asp
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
class Place:
    id: str
    label: str
    clues: list[str]
    after: str
    safe_spot: str
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
class Item:
    id: str
    label: str
    phrase: str
    value: str
    ownerable: bool = True
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
class Quest:
    id: str
    goal: str
    method: str
    risk: str
    ending_goal: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    place: str
    item: str
    quest: str
    response: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    adult_name: str
    adult_gender: str
    trait: str
    delay: int = 0
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def hazard_possible(item: Item, quest: Quest) -> bool:
    return item.ownerable and "return" in quest.id


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for iid, item in ITEMS.items():
            for qid, quest in QUESTS.items():
                if hazard_possible(item, quest):
                    combos.append((pid, iid, qid))
    return combos


def clue_pressure(place: Place, delay: int) -> int:
    return len(place.clues) + delay


def is_resolved(response: Response, place: Place, delay: int) -> bool:
    return response.power >= clue_pressure(place, delay)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about an album, an everyday mystery, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--response", choices=RESPONSES)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too weak for a detective rescue.")
    if args.item and args.quest and not hazard_possible(ITEMS[args.item], QUESTS[args.quest]):
        raise StoryError("That quest and item do not make a real mystery.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, quest = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    d_gender = rng.choice(["girl", "boy"])
    f_gender = "boy" if d_gender == "girl" else "girl"
    a_gender = rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        item=item,
        quest=quest,
        response=response,
        detective_name=_pick_name(rng, d_gender),
        detective_gender=d_gender,
        friend_name=_pick_name(rng, f_gender),
        friend_gender=f_gender,
        adult_name="Aunt June" if a_gender == "mother" else "Uncle Ben",
        adult_gender=a_gender,
        trait=rng.choice(TRAITS),
        delay=rng.randint(0, 2),
    )


def predict(world: World, place_id: str) -> dict:
    sim = world.copy()
    place = sim.get(place_id)
    place.meters["trouble"] += 1
    return {"trouble": place.meters["trouble"], "solved": False}


def tell(place: Place, item: Item, quest: Quest, response: Response,
         detective_name: str, detective_gender: str,
         friend_name: str, friend_gender: str,
         adult_name: str, adult_gender: str,
         trait: str, delay: int) -> World:
    world = World()
    d = world.add(Entity(id=detective_name, kind="character", type=detective_gender, traits=["smart", trait], role="detective"))
    f = world.add(Entity(id=friend_name, kind="character", type=friend_gender, traits=["kind"], role="friend"))
    a = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the adult"))
    album = world.add(Entity(id="album", type="album", label="the album", plural=False))
    street = world.add(Entity(id="street", type="place", label=place.label))
    album.meters["missing"] = 1.0
    d.memes["curiosity"] += 1
    f.memes["worry"] += 1
    world.say(
        f"On an everyday morning, {d.id} and {f.id} walked to {place.label}. "
        f"The air smelled like old paper and warm sidewalks, and {place.after}."
    )
    world.say(
        f'{d.id} noticed that {place.safe_spot} was too quiet. "Our album is missing," '
        f"{f.id} whispered. {d.id} knew this was a little quest, the kind where a kind choice matters."
    )
    world.para()
    world.say(
        f'The clue trail led to {item.phrase}. {d.id} found a small smear on it and '
        f'said, "Something here was moved today."'
    )
    pred = predict(world, "street")
    world.facts["pred_trouble"] = pred["trouble"]
    world.say(
        f"{f.id} pointed at the path. '{quest.goal.capitalize()},' {f.pronoun()} said, "
        f"and they followed the clues together."
    )
    world.para()
    world.say(
        f'{d.id} wanted to {quest.method}, but {f.id} remembered the moral value of being honest. '
        f'"If someone found it, we should return it kindly," {f.id} said.'
    )
    world.say(
        f'{d.id} agreed, because friendship meant helping the truth, not keeping a secret that could hurt someone.'
    )
    world.para()
    if is_resolved(response, place, delay):
        album.meters["missing"] = 0.0
        album.meters["returned"] = 1.0
        d.memes["joy"] += 1
        f.memes["joy"] += 1
        world.say(
            f"{a.label_word.capitalize()} came with a smile and {response.text.replace('{item}', item.label)}."
        )
        world.say(
            f"{response.qa_text.replace('{item}', item.label).capitalize()}. The album was set back on the shelf, "
            f"and its pages opened to a picture of the two friends together."
        )
    else:
        album.meters["missing"] = 1.0
        album.meters["returned"] = 0.0
        world.say(
            f"{a.label_word.capitalize()} came with a frown and {response.fail.replace('{item}', item.label)}."
        )
        world.say(
            f"The clues were too hard to solve that day, so the friends kept looking with calm hearts and empty hands."
        )
    world.facts.update(
        detective=d, friend=f, adult=a, album=album, place=place, item=item,
        quest=quest, response=response, outcome="returned" if album.meters["returned"] >= THRESHOLD else "open",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child that includes the words "album" and "everyday".',
        f"Tell a friendship quest story where {f['detective'].id} and {f['friend'].id} search for a missing album and choose the honest thing to do.",
        "Write a moral-value mystery where two friends follow clues in an everyday place and return what belongs to someone else.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, fr, adult = f["detective"], f["friend"], f["adult"]
    album = f["album"]
    qa = [
        QAItem(
            question="What kind of story is this?",
            answer="It is a detective story about two friends solving an everyday mystery. They work together, and the story also teaches a moral value about honesty."
        ),
        QAItem(
            question="Why did the friends keep looking together?",
            answer=f"They wanted to solve the quest and find the missing album. They also trusted each other, so friendship helped them stay calm and keep following the clues."
        ),
        QAItem(
            question="What did they choose to do with the album?",
            answer="They chose the honest thing and tried to return it instead of keeping it. That choice shows the moral value at the center of the story."
        ),
    ]
    if album.meters["returned"] >= THRESHOLD:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the album back where it belonged, and the friends smiling beside it. The ending shows that being honest kept their friendship strong."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended with the mystery still open, but the friends stayed kind and kept looking. Even then, they did not stop caring about doing the right thing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a detective?", "A detective is someone who looks for clues and tries to solve a mystery."),
        QAItem("What is a quest?", "A quest is a search for something important or hard to find."),
        QAItem("What is friendship?", "Friendship is caring about someone, helping them, and being kind together."),
        QAItem("What does honesty mean?", "Honesty means telling the truth and not trying to trick people."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story q&a =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id}: {' '.join(bits)}")
    out.append(f"  fired={sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


PLACES = {
    "street": Place(id="street", label="the street", clues=["a bent corner of paper", "a shoe print", "a note in chalk"], after="the baker's door was open, and the mailbox was tipped sideways", safe_spot="the corner bench", tags={"everyday"}),
    "library": Place(id="library", label="the library", clues=["a library slip", "a squeaky cart wheel"], after="the reading room was tidy, but one shelf looked newly touched", safe_spot="the front desk", tags={"everyday"}),
    "market": Place(id="market", label="the market", clues=["a price tag", "a dropped ribbon", "a basket mark"], after="the stall lights blinked in the late morning", safe_spot="the fruit stand", tags={"everyday"}),
}

ITEMS = {
    "album": Item(id="album", label="album", phrase="the album", value="memories", ownerable=True, tags={"album"}),
    "box": Item(id="box", label="box", phrase="a cardboard box", value="hiding", ownerable=True, tags={"everyday"}),
    "bag": Item(id="bag", label="bag", phrase="a small bag", value="carrying", ownerable=True, tags={"everyday"}),
}

QUESTS = {
    "return_album": Quest(id="return_album", goal="find who lost the album", method="keep following the clues", risk="someone might keep it by mistake", ending_goal="return the album", tags={"quest", "album"}),
    "find_owner": Quest(id="find_owner", goal="find the owner of the lost thing", method="ask kindly and compare clues", risk="the clue trail might be confusing", ending_goal="return it to the right person", tags={"quest", "friendship"}),
}

RESPONSES = {
    "safe_return": Response(id="safe_return", sense=3, power=3, text="helped place the album back on the table and thanked everyone for the clues", fail="could not help place the album back where it belonged", qa_text="They helped place the album back on the table and thanked everyone for the clues", tags={"honest"}),
    "careful_search": Response(id="careful_search", sense=3, power=2, text="kept the search calm and asked one more kind question", fail="looked one more time, but the clues still did not line up", qa_text="They kept the search calm and asked one more kind question", tags={"kind"}),
    "ask_owner": Response(id="ask_owner", sense=2, power=1, text="asked the right person and waited for an answer", fail="asked, but nobody knew for sure", qa_text="They asked the right person and waited for an answer", tags={"kind"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Tom", "Ben", "Finn", "Noah", "Max"]
TRAITS = ["careful", "curious", "brave", "kind", "patient"]


CURATED = [
    StoryParams(place="street", item="album", quest="return_album", response="safe_return", detective_name="Mia", detective_gender="girl", friend_name="Leo", friend_gender="boy", adult_name="Aunt June", adult_gender="mother", trait="careful", delay=0),
    StoryParams(place="library", item="album", quest="find_owner", response="careful_search", detective_name="Tom", detective_gender="boy", friend_name="Nora", friend_gender="girl", adult_name="Uncle Ben", adult_gender="father", trait="patient", delay=1),
]


def explain_rejection(item: Item, quest: Quest) -> str:
    return f"(No story: the item and quest do not make a believable everyday mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "returned" if is_resolved(RESPONSES[params.response], PLACES[params.place], params.delay) else "open"


ASP_RULES = r"""
valid(P,I,Q) :- place(P), item(I), quest(Q), safe_combo(P,I,Q).
outcome(returned) :- chosen(P), chosen_resp(R), place(P), response(R), power(R,PW), pressure(P,PR), PW >= PR.
outcome(open) :- chosen(P), chosen_resp(R), place(P), response(R), power(R,PW), pressure(P,PR), PW < PR.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("pressure", pid, len(p.clues)))
        for c in p.clues:
            lines.append(asp.fact("clue", pid, c))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("safe_combo", "street", "album", "return_album"))
        lines.append(asp.fact("safe_combo", "library", "album", "find_owner"))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen", params.place),
        asp.fact("chosen_resp", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("MISMATCH: generate() produced empty story")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.quest not in QUESTS or params.response not in RESPONSES:
        raise StoryError("Invalid StoryParams.")
    world = tell(
        PLACES[params.place], ITEMS[params.item], QUESTS[params.quest], RESPONSES[params.response],
        params.detective_name, params.detective_gender, params.friend_name, params.friend_gender,
        params.adult_name, params.adult_gender, params.trait, params.delay,
    )
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


def _random_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, quest = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    d_gender = rng.choice(["girl", "boy"])
    f_gender = "boy" if d_gender == "girl" else "girl"
    return StoryParams(
        place=place, item=item, quest=quest, response=response,
        detective_name=_pick_name(rng, d_gender), detective_gender=d_gender,
        friend_name=_pick_name(rng, f_gender), friend_gender=f_gender,
        adult_name="Aunt June", adult_gender="mother", trait=rng.choice(TRAITS),
        delay=rng.randint(0, 2),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = _random_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            params.seed = base_seed + i
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
            header = f"### {p.detective_name}: {p.quest} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
