#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gusto_lawyer_oval_surprise_kindness_cautionary_myth.py
======================================================================================

A small mythic storyworld about a bold pilgrim, a careful lawyer of the village,
and an oval relic that can grant a surprise blessing when approached with
kindness and caution.

The world is built around three seed words:
- gusto
- lawyer
- oval

And three story instruments:
- Surprise
- Kindness
- Cautionary

The story style leans mythic: an old road, a spoken vow, a hidden test, a gift,
and a warning that keeps the blessing from becoming a burden.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/gusto_lawyer_oval_surprise_kindness_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4-mini/gusto_lawyer_oval_surprise_kindness_cautionary_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/gusto_lawyer_oval_surprise_kindness_cautionary_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/gusto_lawyer_oval_surprise_kindness_cautionary_myth.py --verify
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
SENSE_MIN = 2.0


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
    mythic: bool = False
    cautionary: bool = False
    surprising: bool = False
    kindhearted: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king", "lawyer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class Rule:
    name: str
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


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    setting: str
    oval: str
    response: str
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


@dataclass
class Setting:
    id: str
    place: str
    road: str
    sky: str
    relic_site: str
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
class OvalRelic:
    id: str
    label: str
    phrase: str
    surprise: str
    blessing: str
    risk: str
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


SETTINGS = {
    "hilltemple": Setting(
        id="hilltemple",
        place="the hill temple",
        road="the stone road",
        sky="the wide sky",
        relic_site="the oval shrine",
    ),
    "rivercrossing": Setting(
        id="rivercrossing",
        place="the river crossing",
        road="the wet path",
        sky="the silver dawn",
        relic_site="the oval stone by the ford",
    ),
    "orchardgate": Setting(
        id="orchardgate",
        place="the old orchard gate",
        road="the root-tangled lane",
        sky="the pink morning",
        relic_site="the oval gate-stone",
    ),
}

OVALS = {
    "sun_oval": OvalRelic(
        id="sun_oval",
        label="sun-oval",
        phrase="a sun-oval carved from pale stone",
        surprise="a gold light sprang from it and filled the court",
        blessing="the blessing of warm light",
        risk="its light could blind the careless",
        tags={"oval", "surprise", "kindness", "cautionary"},
    ),
    "moon_oval": OvalRelic(
        id="moon_oval",
        label="moon-oval",
        phrase="a moon-oval rimmed with silver",
        surprise="a cool glow rose from it like mist",
        blessing="the blessing of quiet sight",
        risk="its glow could lure the rash into deep water",
        tags={"oval", "surprise", "kindness", "cautionary"},
    ),
}

RESPONSES = {
    "shield": Response(
        id="shield",
        sense=3,
        power=3,
        text="lifted a woven shield and covered the oval light until it softened",
        fail="raised a shield, but the light was too fierce to tame",
        qa_text="lifted a woven shield over the oval relic and softened its blaze",
        tags={"kindness", "cautionary"},
    ),
    "veil": Response(
        id="veil",
        sense=2,
        power=2,
        text="spread a veil of cloth over the relic and steadied the shining",
        fail="spread a veil over the relic, but the glow kept growing",
        qa_text="spread a veil of cloth over the relic and steadied the shining",
        tags={"kindness", "cautionary"},
    ),
    "wait": Response(
        id="wait",
        sense=4,
        power=4,
        text="asked everyone to wait, breathe, and let the bright moment pass",
        fail="asked everyone to wait, but the danger had already rushed forward",
        qa_text="asked everyone to wait and let the bright moment pass safely",
        tags={"kindness", "cautionary"},
    ),
    "rush": Response(
        id="rush",
        sense=1,
        power=1,
        text="ran at the relic with gusto and made the glow leap higher",
        fail="ran at the relic with gusto, and the glow rose wild and hot",
        qa_text="rushed at the relic too quickly",
        tags={"gusto"},
    ),
}

HEROES = ["Ari", "Mina", "Sol", "Iris", "Niko", "Lena"]
GUIDES = ["Lawyer Taro", "Lawyer Sera", "Lawyer Ivo", "Lawyer Mira"]
GENDERS = ["girl", "boy"]
TRAITS = ["bold", "gentle", "quick", "careful", "bright", "thoughtful"]


def hazard_at_risk(oval: OvalRelic, response: Response) -> bool:
    return True if oval and response else False


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for oid in OVALS:
            for rid, r in RESPONSES.items():
                if r.sense >= SENSE_MIN and hazard_at_risk(OVALS[oid], r):
                    combos.append((sid, oid, rid))
    return combos


def best_response() -> Response:
    return max(sensible_responses(), key=lambda r: r.sense)


def propagation(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["radiance"] >= THRESHOLD:
            sig = ("radiance", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            for k in list(world.entities.values()):
                if k.kind == "character":
                    k.memes["awe"] += 1
                    k.memes["fear"] += 1
            out.append("__radiance__")
    return out


def tell_setting(world: World, setting: Setting, hero: Entity, guide: Entity, oval: OvalRelic) -> None:
    hero.memes["joy"] += 1
    guide.memes["duty"] += 1
    world.say(
        f"Long ago, at {setting.place}, {hero.id} and {guide.id} walked {setting.road} beneath {setting.sky}."
    )
    world.say(
        f"The old tales said the road led to {oval.phrase}, hidden at {setting.relic_site}."
    )
    world.say(f"{hero.id} carried {hero.attrs.get('gusto_word', 'gusto')} in {hero.pronoun('possessive')} step.")


def warning(world: World, guide: Entity, hero: Entity, oval: OvalRelic) -> None:
    guide.memes["caution"] += 1
    world.say(
        f'{guide.id} lifted a hand. "Easy now," {guide.pronoun()} said. '
        f'"The {oval.label_word if hasattr(oval, "label_word") else oval.label} is no toy. '
        f"{oval.risk.capitalize()}.""
    )


def surprise(world: World, oval_ent: Entity, oval: OvalRelic) -> None:
    oval_ent.meters["radiance"] += 1
    oval_ent.meters["wonder"] += 1
    propagation(world)
    world.say(
        f"When {oval_ent.id} was touched, surprise came at once: {oval.surprise}."
    )


def kind_response(world: World, guide: Entity, response: Response, oval_ent: Entity, oval: OvalRelic) -> bool:
    if response.id == "rush":
        guide.memes["impulse"] += 1
    if response.sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{response.id}': not cautious enough.)")
    contained = response.power >= 2
    body = response.text
    world.say(f"Then {guide.id} {body}.")
    if contained:
        oval_ent.meters["radiance"] = 0.0
        world.say(
            f"The light sank into a softer shine, and the court kept its breath."
        )
    else:
        world.say(
            f"But the brightness would not settle, and the court grew too hot to trust."
        )
    return contained


def ending(world: World, hero: Entity, guide: Entity, oval: OvalRelic, contained: bool) -> None:
    if contained:
        hero.memes["awe"] += 1
        hero.memes["kindness"] += 1
        guide.memes["kindness"] += 1
        world.say(
            f"{guide.id} bowed and spoke kindly: 'Caution keeps wonder from becoming harm.'"
        )
        world.say(
            f"{hero.id} nodded, and the oval relic glowed like a small, safe moon in {world.facts['setting'].place}."
        )
    else:
        hero.memes["fear"] += 1
        world.say(
            f"They fled the court with the lesson in their hearts: even a blessing must be met with caution."
        )
        world.say(
            f"Behind them, the {oval.label} burned itself bright and then dimmed to stone."
        )


def tell(setting: Setting, oval: OvalRelic, response: Response,
         hero_name: str, hero_gender: str, guide_name: str, guide_gender: str,
         gusto_word: str = "gusto") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["gusto", "mythic"],
        attrs={"gusto_word": gusto_word},
        mythic=True,
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type=guide_gender,
        role="lawyer",
        traits=["cautious", "kind"],
        cautionary=True,
    ))
    oval_ent = world.add(Entity(
        id="oval_relic",
        kind="thing",
        type="relic",
        label=oval.label,
        role="relic",
        mythic=True,
        surprising=True,
        kindhearted=True,
    ))
    world.facts.update(setting=setting, oval=oval, response=response, hero=hero, guide=guide)
    tell_setting(world, setting, hero, guide, oval)
    world.para()
    warning(world, guide, hero, oval)
    world.para()
    surprise(world, oval_ent, oval)
    contained = kind_response(world, guide, response, oval_ent, oval)
    world.para()
    ending(world, hero, guide, oval, contained)
    world.facts.update(contained=contained, hero=hero, guide=guide, oval_ent=oval_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child that includes the words "gusto", "lawyer", and "oval".',
        f"Tell a mythic story where {f['hero'].id} moves with gusto, a lawyer gives a cautionary warning, and an oval relic surprises everyone.",
        "Write a gentle myth about kindness, surprise, and caution around a strange oval treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    oval: OvalRelic = f["oval"]
    contained = f["contained"]
    qa = [
        ("Who are the story's main characters?",
         f"The story follows {hero.id} and {guide.id}, the lawyer who watches carefully over the road."),
        ("What made the moment surprising?",
         f"The oval relic was surprising because {oval.surprise}. That sudden change turned a quiet walk into a mythic event."),
        ("Why did the lawyer warn the hero?",
         f"{guide.id} warned {hero.id} because {oval.risk}. The warning was cautious, not unkind, because the guide wanted the blessing to stay safe."),
    ]
    if contained:
        qa.append((
            "How did kindness help in the end?",
            f"{guide.id} answered the surprise with kindness and a careful response, so the bright power settled down. That let {hero.id} keep the wonder without being harmed."
        ))
    else:
        qa.append((
            "What happened after the warning failed?",
            f"The shining grew too strong, so they had to leave the place and remember the cautionary lesson. Even then, the story kept its kindness because the guide still protected {hero.id}."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["oval"].tags)
    tags |= set(f["response"].tags)
    qa = []
    if "oval" in tags:
        qa.append(("What is an oval shape?",
                    "An oval is a round shape that is stretched out, like an egg or a smooth stone.")) 
    if "surprise" in tags:
        qa.append(("What is a surprise?",
                    "A surprise is something unexpected that happens all at once and makes people look up quickly."))
    if "kindness" in tags:
        qa.append(("What is kindness?",
                    "Kindness means being gentle and helpful to others, especially when they are scared or unsure."))
    if "cautionary" in tags:
        qa.append(("What does caution mean?",
                    "Caution means moving carefully so that a dangerous thing does not become worse."))
    qa.append(("What does a lawyer do?",
                "A lawyer knows how to speak carefully about rules, promises, and fair choices."))
    return qa


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.mythic:
            bits.append("mythic=True")
        if e.kindhearted:
            bits.append("kindhearted=True")
        if e.cautionary:
            bits.append("cautionary=True")
        if e.surprising:
            bits.append("surprising=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, O, R) :- setting(S), oval(O), response(R), sensible(R).
contained(S, O, R) :- valid(S, O, R), power(R,P), P >= 2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OVALS:
        lines.append(asp.fact("oval", oid))
        for t in sorted(OVALS[oid].tags):
            lines.append(asp.fact("tag", oid, t))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", int(SENSE_MIN)))
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
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos parity.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about gusto, a lawyer, and an oval relic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--oval", choices=OVALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=GENDERS)
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=GENDERS)
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
    settings = list(SETTINGS)
    ovals = list(OVALS)
    responses = [r.id for r in sensible_responses()]
    setting = args.setting or rng.choice(settings)
    oval = args.oval or rng.choice(ovals)
    response = args.response or rng.choice(responses)
    if args.response and args.response not in responses:
        raise StoryError("That response is too rash for this myth.")
    hero_gender = args.hero_gender or rng.choice(GENDERS)
    guide_gender = args.guide_gender or rng.choice(GENDERS)
    hero = args.hero or rng.choice(HEROES)
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(
        hero=hero,
        hero_gender=hero_gender,
        guide=guide,
        guide_gender=guide_gender,
        setting=setting,
        oval=oval,
        response=response,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.oval not in OVALS:
        raise StoryError("Unknown oval relic.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    resp = RESPONSES[params.response]
    if resp.sense < SENSE_MIN:
        raise StoryError("That response is too unwise for this storyworld.")
    world = tell(
        SETTINGS[params.setting],
        OVALS[params.oval],
        resp,
        params.hero,
        params.hero_gender,
        params.guide,
        params.guide_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams(hero="Ari", hero_gender="boy", guide="Lawyer Taro", guide_gender="boy", setting="hilltemple", oval="sun_oval", response="shield"),
    StoryParams(hero="Mina", hero_gender="girl", guide="Lawyer Mira", guide_gender="girl", setting="orchardgate", oval="moon_oval", response="wait"),
    StoryParams(hero="Sol", hero_gender="boy", guide="Lawyer Sera", guide_gender="girl", setting="rivercrossing", oval="sun_oval", response="veil"),
]


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
        print(asp_program("#show valid/3.\n#show sensible/1.\n#show contained/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, oval, response) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.guide}: {p.setting}, {p.oval}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
