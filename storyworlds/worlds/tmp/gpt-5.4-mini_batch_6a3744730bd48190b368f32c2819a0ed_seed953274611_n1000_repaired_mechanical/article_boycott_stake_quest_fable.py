#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/article_boycott_stake_quest_fable.py
=====================================================================

A small standalone story world for a fable-like quest about an article, a
boycott, and a stake.

Premise
-------
A village has stopped buying the baker's bread after a quarrel over a stake at
the market stall. A small quest follows: a messenger must carry an article of
agreement to the town elder, where a calm choice can end the boycott.

The world is kept tiny on purpose:
- typed entities with physical meters and emotional memes
- a forward-chained causal simulation
- a reasonableness gate
- a Python gate plus an inline ASP twin
- three Q&A sets grounded in the simulated state

The fable tone stays child-facing and concrete, with a clear turn and ending.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "fox", "stag"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    bustle: str
    road: str
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
class Article:
    id: str
    title: str
    opening: str
    truth: str
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
class Stake:
    id: str
    label: str
    use: str
    can_move: bool = True
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_grievance(world: World) -> list[str]:
    out: list[str] = []
    town = world.entities.get("town")
    if not town or town.memes["grievance"] < THRESHOLD:
        return out
    sig = ("grievance",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role == "villager":
            e.memes["doubt"] += 1
    out.append("The village had gone quiet with doubt.")
    return out


def _r_article_spreads(world: World) -> list[str]:
    out: list[str] = []
    if world.get("article").meters["carried"] < THRESHOLD:
        return out
    sig = ("article",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("messenger").memes["hope"] += 1
    out.append("The article gave the messenger hope.")
    return out


CAUSAL_RULES = [Rule("grievance", "social", _r_grievance), Rule("article", "social", _r_article_spreads)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cause_boycott(world: World) -> None:
    world.get("town").memes["grievance"] += 1
    for e in list(world.entities.values()):
        if e.role == "villager":
            e.meters["unspoken"] += 1
    propagate(world, narrate=False)


def lift_boycott(world: World) -> None:
    town = world.get("town")
    town.memes["grievance"] = 0
    town.memes["peace"] += 1
    for e in list(world.entities.values()):
        if e.role == "villager":
            e.memes["doubt"] = 0
            e.memes["warmth"] += 1


def tell(world: World, place: Place, article: Article, stake: Stake,
         response: Response, messenger_name: str = "Milo",
         messenger_type: str = "mouse", elder_name: str = "Greta",
         elder_type: str = "goat") -> World:
    messenger = world.add(Entity(id=messenger_name, kind="character", type=messenger_type, role="messenger"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    town = world.add(Entity(id="town", kind="place", label=place.label))
    baker = world.add(Entity(id="baker", kind="character", type="goat", role="villager", label="the baker"))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="hen", role="villager", label="the neighbor"))
    art = world.add(Entity(id="article", type="thing", label=article.title))
    stk = world.add(Entity(id="stake", type="thing", label=stake.label))

    messenger.memes["duty"] += 1
    messenger.memes["fear"] += 1
    baker.memes["hurt"] += 1
    neighbor.memes["hurt"] += 1

    world.say(
        f"In a little village by the road, the {place.label} buzzed with whispers. "
        f"A small boycott had begun, and even the baker's oven went cold."
    )
    world.say(
        f"The trouble came from a stake at the market stall, and the people kept "
        f"pointing at it as if it were the whole argument."
    )
    world.say(
        f"Milo was given an article named '{article.title}'. Its opening line said, "
        f"'{article.opening}'."
    )
    world.say(
        f'"If this truth reaches Greta," said the baker, "she can mend what the '
        f"boycott has broken."'
    )

    world.para()
    world.say(
        f"So Milo began a quest down the road. {place.road} stretched ahead, and "
        f"the article stayed tucked close, warm against {messenger.pronoun('possessive')} side."
    )
    world.say(
        f"At the gate, Milo saw the stake leaning in the dirt like a stubborn little spear."
    )
    world.say(
        f'"Take the stake away," whispered the neighbor, "and the quarrel may finally rest."'
    )

    world.para()
    if stake.can_move:
        stk.meters["moved"] += 1
        messenger.memes["brave"] += 1
        world.say(
            f"Milo did not pick a side in anger. {messenger.pronoun().capitalize()} "
            f"lifted the stake gently, set it straight beside the path, and carried the article on."
        )
    else:
        world.say(
            f"Milo tried to move the stake, but it would not budge. Still, the article "
            f"had to go on, because the village needed the truth more than the argument."
        )

    art.meters["carried"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last Milo reached Greta beneath the old fig tree. {elder.pronoun().capitalize()} "
        f"read the article in silence, then nodded as the last line settled like rain on dry earth."
    )
    world.say(
        f"Greta asked the baker and the neighbor to stand together, and the boycott "
        f"began to loosen."
    )

    if response.power >= 2:
        lift_boycott(world)
        world.say(
            f"With a calm voice, {elder.pronoun()} explained {response.text.replace('{stake}', stake.label)}."
        )
        world.say(
            f"The stall was opened again, the bread was shared, and the stake was moved "
            f"to a fairer place where no one would mistake it for a threat."
        )
    else:
        world.say(
            f"Greta tried {response.fail.replace('{stake}', stake.label)}, but the village "
            f"was still too stiff with anger, and the boycott stayed in place."
        )

    world.say("That evening, the oven glowed once more, and the road smelled of warm bread.")

    world.facts.update(
        messenger=messenger,
        elder=elder,
        town=town,
        baker=baker,
        neighbor=neighbor,
        article_cfg=article,
        stake_cfg=stake,
        response=response,
        place=place,
        boycott_active=town.memes["grievance"] >= THRESHOLD,
        stake_moved=stk.meters["moved"] >= THRESHOLD,
        ended_peaceful=town.memes["peace"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for aid, article in ARTICLES.items():
            for sid, stake in STAKES.items():
                if reasonableness_gate(place, article, stake):
                    out.append((pid, aid, sid))
    return out


def reasonableness_gate(place: Place, article: Article, stake: Stake) -> bool:
    return "quest" in place.tags and "boycott" in article.tags and "stake" in stake.tags


@dataclass
class StoryParams:
    place: str
    article: str
    stake: str
    response: str
    messenger: str
    messenger_type: str
    elder: str
    elder_type: str
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


PLACES = {
    "market": Place(id="market", label="market square", bustle="small stalls and soft voices", road="The road crossed the wheat field and the creek bridge.", tags={"quest", "fable"}),
    "mill": Place(id="mill", label="mill town", bustle="grain dust and the creak of carts", road="The road curled past the mill wheel and the apple cart.", tags={"quest", "fable"}),
}

ARTICLES = {
    "agreement": Article(id="agreement", title="The Little Article of Fair Trade", opening="No stall should stand above the common good", truth="A fair promise can mend a noisy village", tags={"article", "boycott"}),
    "notice": Article(id="notice", title="The Market Article", opening="Let the baker speak and let the stall be shared", truth="Words can calm a crowd when they are truthful", tags={"article", "boycott"}),
}

STAKES = {
    "marker": Stake(id="marker", label="the stake", use="mark a fair boundary", tags={"stake"}),
    "post": Stake(id="post", label="the wooden stake", use="hold the stall sign", tags={"stake"}),
}

RESPONSES = {
    "talk": Response(id="talk", sense=3, power=3, text="a patient talk about the stake and the market's rules", fail="spoke softly, but nobody listened", qa_text="spoke patiently about the stake and the market's rules"),
    "read": Response(id="read", sense=4, power=4, text="read the article aloud until the truth was hard to ignore", fail="read the article, but the crowd stayed split", qa_text="read the article aloud until the truth was hard to ignore"),
}

MESSENGERS = ["Milo", "Pip", "Sera", "Nell"]
ELDERS = ["Greta", "Hugo", "Mara", "Bram"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like quest about an article, a boycott, and a stake.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--article", choices=ARTICLES)
    ap.add_argument("--stake", choices=STAKES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--messenger")
    ap.add_argument("--messenger-type", choices=["mouse", "sparrow", "hare", "fox"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["goat", "owl", "tortoise", "heron"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.article is None or c[1] == args.article)
              and (args.stake is None or c[2] == args.stake)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, article, stake = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    messenger = args.messenger or rng.choice(MESSENGERS)
    messenger_type = args.messenger_type or rng.choice(["mouse", "sparrow", "hare", "fox"])
    elder = args.elder or rng.choice(ELDERS)
    elder_type = args.elder_type or rng.choice(["goat", "owl", "tortoise", "heron"])
    return StoryParams(place=place, article=article, stake=stake, response=response,
                       messenger=messenger, messenger_type=messenger_type,
                       elder=elder, elder_type=elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a quest that includes the words "article", "boycott", and "stake".',
        f"Tell a child-friendly story where {f['messenger'].id} carries an article to end a boycott at the {f['place'].label}.",
        f"Write a moral story where a messenger learns that a calm article can settle a boycott better than a sharp stake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What was the quest about?",
               answer=f"It was about carrying an article to the elder so the village could end the boycott and stop arguing over the stake."),
        QAItem(question="Why had the village stopped buying bread?",
               answer="The villagers were upset about the stake at the market stall. Their anger made them refuse the bread until someone brought the matter into the open."),
        QAItem(question="What changed at the end?",
               answer="The elder listened, the boycott loosened, and the bread came back to the table. The stake was moved to a fairer place, so the village could feel peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an article?",
               answer="An article can be a written piece that tells people about a topic or explains a rule. In this story it carries important news."),
        QAItem(question="What is a boycott?",
               answer="A boycott is when people refuse to buy or do something because they are upset. It is a way of showing protest with their choices."),
        QAItem(question="What is a stake?",
               answer="A stake is a strong piece of wood pushed into the ground. People can use it to mark a place or hold something in place."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,S) :- place(P), article(A), stake(S),
                quest_place(P), boycott_article(A), stake_tag(S).
peaceful :- carried(article), moved(stake).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("quest_place", pid))
    for aid in ARTICLES:
        lines.append(asp.fact("article", aid))
        lines.append(asp.fact("boycott_article", aid))
    for sid in STAKES:
        lines.append(asp.fact("stake", sid))
        lines.append(asp.fact("stake_tag", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, article=None, stake=None, response=None, messenger=None, messenger_type=None, elder=None, elder_type=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.article not in ARTICLES or params.stake not in STAKES or params.response not in RESPONSES:
        raise StoryError("(Invalid parameters.)")
    world = tell(Place(**vars(PLACES[params.place])), Article(**vars(ARTICLES[params.article])),
                 Stake(**vars(STAKES[params.stake])), RESPONSES[params.response],
                 messenger_name=params.messenger, messenger_type=params.messenger_type,
                 elder_name=params.elder, elder_type=params.elder_type)
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


CURATED = [
    StoryParams(place="market", article="agreement", stake="marker", response="read", messenger="Milo", messenger_type="mouse", elder="Greta", elder_type="goat"),
    StoryParams(place="mill", article="notice", stake="post", response="talk", messenger="Pip", messenger_type="sparrow", elder="Mara", elder_type="owl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
