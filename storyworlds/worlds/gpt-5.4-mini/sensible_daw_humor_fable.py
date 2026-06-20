#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sensible_daw_humor_fable.py
============================================================

A tiny standalone storyworld for a humorous fable about a sensible daw.

Premise
-------
A proud fox keeps a shiny bell on a fence. A hungry daw wants to show off,
but a sensible daw knows better than to snatch what the fox guards. The birds
discover that cleverness is funnier, and safer, than greed.

This world models:
- characters and objects with physical meters and emotional memes
- a small causal engine
- a prediction beat, a turn, and a resolution
- a reasonableness gate and inline ASP twin
- three Q&A sets grounded in the simulated world

The story should feel like a short fable: concrete, child-facing, slightly funny,
and ending with a lesson image that proves what changed.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    shimmery: bool = False
    guard: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    image: str
    lesson: str
    humortone: str

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
class Temptation:
    id: str
    label: str
    lure: str
    where: str
    noise: str
    risk: str
    tags: set[str] = field(default_factory=set)
    makes_mess: bool = False

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
class Prize:
    id: str
    label: str
    phrase: str
    owner: str
    keeper: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bell").meters["jingling"] >= THRESHOLD and ("noise",) not in world.fired:
        world.fired.add(("noise",))
        world.get("crowd").memes["mirth"] += 1
        out.append("The whole lane laughed at the silly ringing.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bait").meters["tipped"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("bait").meters["scattered"] += 1
    world.get("fox").memes["annoyance"] += 1
    out.append("The fox looked offended, which only made the birds blink harder.")
    return out


CAUSAL_RULES = [Rule("noise", "social", _r_noise), Rule("spill", "physical", _r_spill)]


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
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(temptation: Temptation, prize: Prize) -> bool:
    return temptation.makes_mess and prize.fragile


def would_restrain(trait: str, partner_age: int, bird_age: int) -> bool:
    return trait in {"sensible", "careful", "patient"} and partner_age >= bird_age


def risk_level(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= risk_level(delay)


def predict(world: World, temptation_id: str) -> dict:
    sim = world.copy()
    _do_temptation(sim, sim.get(temptation_id), narrate=False)
    return {
        "jingling": sim.get("bell").meters["jingling"] >= THRESHOLD,
        "scattered": sim.get("bait").meters["scattered"] >= THRESHOLD,
    }


def _do_temptation(world: World, temptation: Entity, narrate: bool = True) -> None:
    temptation.meters["touched"] += 1
    temptation.meters["tipped"] += 1
    propagate(world, narrate=narrate)


def start(world: World, hero: Entity, partner: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    partner.memes["pride"] += 1
    world.say(
        f"By the old fence in {setting.place}, {hero.id} and {partner.id} found "
        f"a tiny stage of trouble. {setting.image}"
    )
    world.say(
        f'"This looks like a grand chance," said {partner.id}, with all the confidence '
        f'of a goose in a ribbon.'
    )


def warn(world: World, partner: Entity, hero: Entity, temptation: Temptation, prize: Prize) -> None:
    pred = predict(world, "bait")
    partner.memes["caution"] += 1
    world.facts["predicted_noise"] = pred["jingling"]
    world.say(
        f'{partner.id} peered at the shiny {prize.label} and lowered {partner.pronoun("possessive")} voice. '
        f'"We should be sensible, {hero.id}. If we poke the {temptation.label}, the {prize.label} will ring, '
        f'and {prize.keeper} will hear."'
    )


def dawdle(world: World, hero: Entity, partner: Entity, temptation: Temptation) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Nonsense," said {hero.id}. "A daw with style can manage one little trick." '
        f'And off {hero.id} hopped toward the bait.'
    )


def act(world: World, temptation: Temptation) -> None:
    _do_temptation(world, world.get("bait"))
    world.say(
        f"{temptation.noise} The seed tray tipped, and the shiny {world.get('bell').label} gave one loud jingle."
    )


def alarm(world: World, fox: Entity) -> None:
    world.say(f'"Who is making that racket?" cried {fox.id}, whose tail had gone very straight.')


def rescue(world: World, keeper: Entity, response: Response, temptation: Temptation) -> None:
    world.get("bell").meters["jingling"] = 0.0
    body = response.text.replace("{target}", temptation.label)
    world.say(f"{keeper.id} came at once and {body}.")
    world.say("The lane grew quiet again, except for a single embarrassed cough from the fence.")


def lesson(world: World, keeper: Entity, hero: Entity, partner: Entity, setting: Setting) -> None:
    for eid in (hero.id, partner.id):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["lesson"] += 1
        world.get(eid).memes["joy"] += 1
    world.say(
        f"{keeper.id} shook {keeper.pronoun('possessive')} head, but {keeper.pronoun()} was smiling too."
    )
    world.say(
        f'"If you want a clever trick, try a kind one," {keeper.id} said. "A sensible daw gets farther '
        f'than a greedy one."'
    )
    world.say(
        f"The two birds bowed to the {setting.humortone} lesson and hopped off to do something less noisy."
    )


def ending(world: World, keeper: Entity, hero: Entity, partner: Entity, setting: Setting) -> None:
    world.say(
        f"After that, {hero.id} kept {partner.id} from the bait, and together they found {setting.lesson}. "
        f"That day the fence stayed tidy, the bell stayed still, and the daw learned that being sensible can be funny too."
    )


def tell(
    setting: Setting,
    temptation: Temptation,
    prize: Prize,
    response: Response,
    hero_name: str = "Daw",
    hero_gender: str = "boy",
    partner_name: str = "Mira",
    partner_gender: str = "girl",
    keeper_gender: str = "boy",
    delay: int = 0,
    hero_age: int = 4,
    partner_age: int = 5,
    relation: str = "friends",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", age=hero_age))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", age=partner_age, traits=["sensible"]))
    keeper = world.add(Entity(id="Fox", kind="character", type=keeper_gender, role="keeper", label="the fox"))
    world.add(Entity(id="crowd", kind="character", type="thing", label="the lane"))
    world.add(Entity(id="bait", type="thing", label=temptation.label))
    world.add(Entity(id="bell", type="thing", label=prize.label, shimmery=True))

    hero.memes["curiosity"] = 1.0
    partner.memes["sensibility"] = 1.0
    world.facts["relation"] = relation
    world.facts["delay"] = delay

    start(world, hero, partner, setting)
    world.para()
    warn(world, partner, hero, temptation, prize)

    restrained = would_restrain("sensible", partner_age, hero_age)
    if restrained:
        hero.memes["trust"] += 1
        world.say(f'{hero.id} blinked, then nodded. "All right," {hero.id} said. "Let us be wise instead."')
        world.para()
        lesson(world, keeper, hero, partner, setting)
        outcome = "averted"
    else:
        dawdle(world, hero, partner, temptation)
        world.para()
        act(world, temptation)
        alarm(world, keeper)
        contained = is_contained(response, delay)
        if contained:
            world.para()
            rescue(world, keeper, response, temptation)
            lesson(world, keeper, hero, partner, setting)
            outcome = "contained"
        else:
            world.para()
            world.say(
                f"{keeper.id} tried {response.fail.replace('{target}', temptation.label)}."
            )
            world.say("But the little problem grew into a bigger one, so the birds had to retreat and start again tomorrow.")
            outcome = "bothered"
    world.para()
    ending(world, keeper, hero, partner, setting)
    world.facts.update(
        hero=hero,
        partner=partner,
        keeper=keeper,
        setting=setting,
        temptation=temptation,
        prize=prize,
        response=response,
        outcome=outcome,
        restrained=restrained,
    )
    return world


SETTINGS = {
    "lane": Setting("lane", "the lane", "The bakery window glowed like a moon, and crumbs had gathered on the stones.", "a small treasure of breadcrumbs", "humble"),
    "orchard": Setting("orchard", "the orchard path", "The apples hung red and smug, as if they knew a joke.", "a ripe pear behind the fence", "cheerful"),
    "green": Setting("green", "the village green", "Children had left a ribbon, a pebble, and a very serious-looking leaf behind.", "a soft pretzel from the picnic", "gentle"),
}

TEMPTATIONS = {
    "seed": Temptation("seed", "seed tray", "a seed tray", "by the fence", "The tray was wobbling already.", "make a noisy scene", {"seed", "food"}, makes_mess=True),
    "bellpull": Temptation("bellpull", "bell pull", "a bell pull", "on the gate", "The rope looked far too dramatic.", "ring out the secret", {"bell", "noise"}, makes_mess=True),
    "jamjar": Temptation("jamjar", "jam jar", "a jam jar", "near the sill", "The jar glinted as if it had a tiny sun in it.", "slip into a sticky laugh", {"jam", "sticky"}, makes_mess=True),
}

PRIZES = {
    "bell": Prize("bell", "little bell", "a little silver bell", "Fox", "the fox", fragile=True, tags={"bell", "noise"}),
    "cup": Prize("cup", "teacup", "a thin teacup", "Fox", "the fox", fragile=True, tags={"cup"}),
}

RESPONSES = {
    "pluck": Response("pluck", 3, 2,
                      "lifted the {target} carefully and set it back on the tray",
                      "tried to lift the {target}, but it slipped and made everything worse",
                      "lifted the {target} carefully and set it back"),
    "cover": Response("cover", 2, 2,
                      "covered the {target} with a cloth and calmed the mess",
                      "threw a cloth over the {target}, but the noise had already spread",
                      "covered the {target} with a cloth"),
    "apology": Response("apology", 3, 1,
                        "bowed and apologized to the fox until the mood settled",
                        "muttered an apology, but the fox was still too cross to listen",
                        "bowed and apologized"),
    "water_bucket": Response("water_bucket", 1, 1,
                             "splashed a bucket of water around the {target}",
                             "sloshed water everywhere and only made the lane puddly",
                             "splashed a bucket of water around the {target}"),
}

GIRL_NAMES = ["Mira", "Lena", "Pip", "Ari", "Nell", "Tia"]
BOY_NAMES = ["Daw", "Oren", "Joss", "Nico", "Pru", "Tavi"]
TRAITS = ["sensible", "cheerful", "curious", "careful", "witty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, tempt in TEMPTATIONS.items():
            for pid, prize in PRIZES.items():
                if hazard_at_risk(tempt, prize):
                    combos.append((sid, tid, pid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    temptation: str
    prize: str
    response: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    keeper_gender: str
    trait: str
    delay: int = 0
    hero_age: int = 4
    partner_age: int = 5
    relation: str = "friends"
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


KNOWLEDGE = {
    "daw": [("What is a daw?",
             "A daw is a clever black bird that likes shiny things and noisy plans.")],
    "sensible": [("What does sensible mean?",
                  "Sensible means using good judgment and choosing the wiser thing to do.")],
    "bell": [("What does a bell do?",
              "A bell rings when it is tapped or moved, so people can hear it from far away.")],
    "fox": [("Why is a fox sometimes tricky in fables?",
             "In fables, a fox is often shown as sly or proud, which makes the story funny and meaningful.")],
    "noise": [("Why can noise give away a secret?",
               "Noise travels to other ears, so if something rattles or jingles, everyone nearby notices.")],
}
KNOWLEDGE_ORDER = ["daw", "sensible", "bell", "fox", "noise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous fable for a young child that includes the words "{f["hero"].id}" and "sensible".',
        f"Tell a short animal story about a daw who wants to show off, but a sensible friend stops the trouble.",
        f"Write a gentle, funny fable where the shiny bell matters, and the lesson is that sensible choices are better than greedy ones.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, keeper = f["hero"], f["partner"], f["keeper"]
    setting, temptation, prize = f["setting"], f["temptation"], f["prize"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, {partner.id}, and {keeper.label_word}. The little bird friends try to choose between a silly idea and a sensible one."
        ),
        QAItem(
            question="Why did the sensible bird warn the other bird?",
            answer=f"{partner.id} warned {hero.id} because the shiny {prize.label} could ring and make a fuss. That would bring {keeper.label_word} over, so the warning was a sensible one."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(QAItem(
            question=f"What did {hero.id} do after being warned?",
            answer=f"{hero.id} listened, stopped, and chose the wiser path instead of poking the bait. So the bell stayed quiet and the story turned into a little lesson about being sensible."
        ))
    elif f["outcome"] == "contained":
        qa.append(QAItem(
            question="How was the trouble fixed?",
            answer=f"{keeper.label_word.capitalize()} used {f['response'].qa_text} and the noise settled down. After that, the birds learned their lesson and the lane became quiet again."
        ))
    else:
        qa.append(QAItem(
            question="What happened when the plan failed?",
            answer=f"The little problem turned into a bigger mess, so the birds had to back away and try again tomorrow. They still learned that the funny plan was not worth the trouble."
        ))
    qa.append(QAItem(
        question="How did the story end?",
        answer=f"It ended with the birds choosing a calmer path in {setting.place}. The bell stayed still, and the sensible daw proved that clever restraint can be the funniest trick of all."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["temptation"].tags) | set(world.facts["prize"].tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.shimmery:
            bits.append("shimmery")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lane", "seed", "bell", "pluck", "Daw", "boy", "Mira", "girl", "boy", "sensible", 0, 4, 5, "friends"),
    StoryParams("orchard", "bellpull", "cup", "cover", "Daw", "boy", "Nell", "girl", "boy", "curious", 0, 4, 5, "friends"),
    StoryParams("green", "jamjar", "bell", "apology", "Daw", "boy", "Ari", "girl", "boy", "careful", 1, 4, 5, "friends"),
]


def explain_rejection(temptation: Temptation, prize: Prize) -> str:
    if not hazard_at_risk(temptation, prize):
        return "(No story: that shiny thing would not reasonably cause a lesson here.)"
    return "(No story: this combination is not sensible enough for the fable engine.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    ok = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} < {SENSE_MIN}. Try: {ok}.)"


def outcome_of(params: StoryParams) -> str:
    if would_restrain(params.trait, params.partner_age, params.hero_age):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "bothered"


ASP_RULES = r"""
hazard(T, P) :- temptation(T), prize(P), makes_mess(T), fragile(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, T, P) :- setting(S), temptation(T), prize(P), hazard(T, P).

restrain :- trait(sensible), partner_older.
outcome(averted) :- restrain.
severity(V) :- delay(D), V = D + 1.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(contained) :- not restrain, contained.
outcome(bothered) :- not restrain, not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", tid))
        if t.makes_mess:
            lines.append(asp.fact("makes_mess", tid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("trait", "sensible"))
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
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("partner_older"),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses.")
    else:
        print("OK: sensible responses match.")
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke story was empty.")
    else:
        print("OK: smoke generate() produced a story.")
    mismatches = 0
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches:
        rc = 1
        print(f"MISMATCH: {mismatches} curated outcomes differ.")
    else:
        print("OK: outcome model matches curated scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous fable about a sensible daw.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--parent", choices=["fox"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, temptation, prize = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = "boy"
    partner_gender = "girl"
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    partner = args.partner or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    trait = "sensible"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, temptation, prize, response, hero, hero_gender, partner, partner_gender, "boy", trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TEMPTATIONS[params.temptation],
        PRIZES[params.prize],
        RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        keeper_gender=params.keeper_gender,
        delay=params.delay,
        hero_age=params.hero_age,
        partner_age=params.partner_age,
        relation=params.relation,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for setting, temptation, prize in combos:
            print(f"  {setting:10} {temptation:10} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero} and {p.partner}: {p.temptation} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
