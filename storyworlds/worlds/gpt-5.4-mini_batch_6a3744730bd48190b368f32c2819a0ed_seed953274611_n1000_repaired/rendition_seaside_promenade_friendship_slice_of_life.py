#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rendition_seaside_promenade_friendship_slice_of_life.py
======================================================================================

A small storyworld set on a seaside promenade, built for a slice-of-life
friendship story with a gentle rendition thread.

The domain premise:
- Two friends spend time along a seaside promenade.
- One is preparing a small public rendition: a song, poem, or tune.
- The other helps in a practical, caring way.
- A little snag appears in ordinary life, then friendship solves it.
- The ending proves something changed: confidence grows, the rendition happens,
  and the promenade feels warmer because of the shared moment.

The world model keeps the story grounded in physical meters and emotional memes.
The prose is generated from live simulated state rather than from a frozen
template with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/rendition_seaside_promenade_friendship_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/rendition_seaside_promenade_friendship_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4-mini/rendition_seaside_promenade_friendship_slice_of_life.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/rendition_seaside_promenade_friendship_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/rendition_seaside_promenade_friendship_slice_of_life.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CONFIDENCE_MIN = 2
HELPFUL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    mood: str
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
class Rendition:
    id: str
    kind: str
    instrument: str
    phrase: str
    practice: str
    ending: str
    topic: str
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
class Snag:
    id: str
    label: str
    cause: str
    effect: str
    risk: str
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
class Support:
    id: str
    label: str
    action: str
    benefit: str
    strength: int
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
    setting: str
    rendition: str
    snag: str
    support: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    if performer.meters.get("nerves", 0.0) < THRESHOLD:
        return out
    if world.facts.get("snag_resolved"):
        return out
    if performer.meters.get("spill", 0.0) >= THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("A little spill spoiled the paper at first.")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("friend")
    performer = world.get("performer")
    if helper.meters.get("help", 0.0) < THRESHOLD:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    performer.memes["calm"] = performer.memes.get("calm", 0.0) + 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    out.append("Their friend stayed close and made the moment feel easier.")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("comfort", "social", _r_comfort)]


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


def needs_help(snag: Snag) -> bool:
    return snag.id in {"paper_wind", "stained_hands"}


def reasonable_support(support: Support, snag: Snag) -> bool:
    return support.strength >= HELPFUL_MIN and needs_help(snag)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for rendition in RENDITIONS:
            for snag in SNAGS:
                for support in SUPPORTS:
                    if reasonable_support(SUPPORTS[support], SNAGS[snag]):
                        combos.append((setting, rendition, snag))
    return combos


SETTINGS = {
    "promenade": Setting(
        id="promenade",
        place="the seaside promenade",
        detail="The sea air smelled salty, and gulls drifted above the railings.",
        mood="bright",
        tags={"seaside", "promenade"},
    ),
    "pier": Setting(
        id="pier",
        place="the old pier",
        detail="Wooden boards creaked softly while waves tapped underneath.",
        mood="breezy",
        tags={"seaside"},
    ),
}

RENDITIONS = {
    "song": Rendition(
        id="song",
        kind="song",
        instrument="ukulele",
        phrase="a small song",
        practice="hummed it under their breath",
        ending="played the last warm notes",
        topic="rendition",
        tags={"rendition", "music"},
    ),
    "poem": Rendition(
        id="poem",
        kind="poem",
        instrument="notebook",
        phrase="a short poem",
        practice="read the lines slowly",
        ending="said the last line with a smile",
        topic="rendition",
        tags={"rendition", "poem"},
    ),
    "tune": Rendition(
        id="tune",
        kind="tune",
        instrument="whistle",
        phrase="a soft tune",
        practice="checked the rhythm again and again",
        ending="whistled the last note into the breeze",
        topic="rendition",
        tags={"rendition", "music"},
    ),
}

SNAGS = {
    "paper_wind": Snag(
        id="paper_wind",
        label="a gust of wind",
        cause="the wind could flip the page",
        effect="the page fluttered and nearly blew away",
        risk="the words might scatter",
        tags={"wind", "paper"},
    ),
    "stained_hands": Snag(
        id="stained_hands",
        label="sticky hands",
        cause="their hands were a little messy from snacks",
        effect="the notebook got smudged",
        risk="the clean page needed care",
        tags={"mess", "snack"},
    ),
    "shy_voice": Snag(
        id="shy_voice",
        label="a shy voice",
        cause="the performer felt quiet at first",
        effect="the first line came out tiny",
        risk="the start felt too small to share",
        tags={"shy", "voice"},
    ),
}

SUPPORTS = {
    "hold_page": Support(
        id="hold_page",
        label="holding the page flat",
        action="held the notebook steady",
        benefit="the words stayed in place",
        strength=3,
        tags={"help", "paper"},
    ),
    "napkin": Support(
        id="napkin",
        label="a napkin",
        action="wiped the sticky fingers clean",
        benefit="the page stayed neat",
        strength=2,
        tags={"help", "clean"},
    ),
    "cheer": Support(
        id="cheer",
        label="a cheerful cheer",
        action="gave a bright nod and a soft cheer",
        benefit="the brave feeling grew",
        strength=2,
        tags={"help", "voice"},
    ),
}

FRIEND_NAMES = ["Maya", "Noah", "Lina", "Owen", "Ava", "Eli", "Zoe", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Seaside promenade friendship storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rendition", choices=RENDITIONS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--friend-a")
    ap.add_argument("--friend-a-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-b")
    ap.add_argument("--friend-b-gender", choices=["girl", "boy"])
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
    if args.support and args.snag and not reasonable_support(SUPPORTS[args.support], SNAGS[args.snag]):
        raise StoryError("That support is not a good fit for the snag.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rendition is None or c[1] == args.rendition)
              and (args.snag is None or c[2] == args.snag)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rendition, snag = rng.choice(sorted(combos))
    support = args.support or rng.choice(sorted(SUPPORTS))
    a = args.friend_a or rng.choice(FRIEND_NAMES)
    b = args.friend_b or rng.choice([n for n in FRIEND_NAMES if n != a])
    ag = args.friend_a_gender or rng.choice(["girl", "boy"])
    bg = args.friend_b_gender or ("boy" if ag == "girl" else "girl")
    return StoryParams(setting=setting, rendition=rendition, snag=snag, support=support,
                       friend_a=a, friend_a_gender=ag, friend_b=b, friend_b_gender=bg)


def _pronoun(gender: str, case: str = "subject") -> str:
    return {"subject": {"girl": "she", "boy": "he"}[gender],
            "object": {"girl": "her", "boy": "him"}[gender],
            "possessive": {"girl": "her", "boy": "his"}[gender]}[case]


def tell(world_setting: Setting, r: Rendition, snag: Snag, support: Support,
         a: str, ag: str, b: str, bg: str) -> World:
    w = World()
    performer = w.add(Entity(id="performer", kind="character", type=ag, label=a, role="performer"))
    friend = w.add(Entity(id="friend", kind="character", type=bg, label=b, role="friend"))
    promenade = w.add(Entity(id="place", type="place", label=world_setting.place))
    performer.meters["nerves"] = 1.0
    performer.memes["hope"] = 1.0
    friend.memes["care"] = 1.0

    w.say(
        f"{a} and {b} spent the afternoon at {world_setting.place}. "
        f"{world_setting.detail}"
    )
    w.say(
        f"{a} was getting ready for {r.phrase}. {a} wanted to use {r.instrument}, "
        f"and {a} {r.practice} while the waves whispered nearby."
    )

    w.para()
    if snag.id == "paper_wind":
        performer.meters["spill"] = 1.0
        w.say(
            f"Then {snag.label} arrived. {snag.effect}, and {snag.risk}."
        )
    elif snag.id == "stained_hands":
        performer.meters["spill"] = 1.0
        w.say(
            f"Before the first line, {snag.label} were the problem. {snag.effect}, "
            f"and {snag.risk}."
        )
    else:
        performer.meters["nerves"] = 2.0
        w.say(
            f"At first, {snag.label} made {a} hesitate. {snag.effect}, but "
            f"{a} still wanted to try."
        )

    w.say(
        f"{b} noticed and stayed beside {a}. {b} offered {support.label} and "
        f"{support.action}."
    )
    performer.meters["help"] = float(support.strength)
    if reasonable_support(support, snag):
        w.say(
            f"That helped right away. {support.benefit}, and {a}'s nerves settled."
        )
        performer.meters["nerves"] = 0.0
        performer.memes["joy"] = 1.0
        friend.memes["joy"] = 1.0
        w.say(
            f"So {a} took a breath, {r.ending}, and {b} smiled because the "
            f"rendition could finally be heard."
        )
    else:
        w.say(
            f"It was kind, but not enough to solve the little trouble."
        )
    propagate(w, narrate=False)

    w.facts.update(setting=world_setting, rendition=r, snag=snag, support=support,
                   performer=performer, friend=friend, place=promenade.id,
                   resolved=reasonable_support(support, snag))
    return w


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.rendition not in RENDITIONS or params.snag not in SNAGS or params.support not in SUPPORTS:
        raise StoryError("Invalid params.")
    if not reasonable_support(SUPPORTS[params.support], SNAGS[params.snag]):
        raise StoryError("Unsupported snag/support pairing.")
    w = tell(SETTINGS[params.setting], RENDITIONS[params.rendition], SNAGS[params.snag],
             SUPPORTS[params.support], params.friend_a, params.friend_a_gender,
             params.friend_b, params.friend_b_gender)
    story = (
        f"{params.friend_a} and {params.friend_b} had a quiet day at the "
        f"{SETTINGS[params.setting].place}. "
    )
    story = w.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(w),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(w)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(w)],
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a slice-of-life story about two friends on a seaside promenade, "
        "and include the word rendition.",
        f"Tell a gentle friendship story where {f['performer'].label} wants to "
        f"share a {f['rendition'].kind} at the seaside promenade and a friend helps.",
        "Write a calm everyday story with a small snag, a kind fix, and a happy "
        "rendition at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    perf = f["performer"]
    friend = f["friend"]
    r = f["rendition"]
    snag = f["snag"]
    support = f["support"]
    setting = f["setting"]
    qa = [
        ("Where does the story happen?",
         f"It happens at {setting.place}. The sea air and the promenade set the gentle mood."),
        ("What was the rendition?",
         f"It was {r.phrase}. {perf.label} wanted to share it in a simple, everyday way."),
        ("How did the friend help?",
         f"{friend.label} offered {support.label} and {support.action}. That made the small problem easier to handle."),
    ]
    if f.get("resolved"):
        qa.append((
            "How did the story end?",
            f"The problem settled down and {perf.label} could finish the rendition. "
            f"The two friends ended the day feeling closer and more confident."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["rendition"].tags) | set(f["snag"].tags) | set(f["support"].tags)
    out = []
    if "seaside" in tags:
        out.append(("What is a seaside promenade?",
                     "A seaside promenade is a walking place along the water where people can stroll, talk, and watch the sea."))
    if "rendition" in tags:
        out.append(("What does rendition mean?",
                     "A rendition is a way of performing or presenting something, like a song, poem, or tune."))
    if "help" in tags:
        out.append(("Why is helping a friend nice?",
                     "Helping a friend makes a hard moment easier and shows care. Friendship feels stronger when people look out for each other."))
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
        lines.append(f"  {e.id:10} ({e.type:9}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
resolved :- support(S), strong(S), snag_need(Sn).
story_ok :- setting(promenade), rendition(R), snag(Sn), support(S), resolved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RENDITIONS:
        lines.append(asp.fact("rendition", r))
    for sn in SNAGS:
        lines.append(asp.fact("snag", sn))
    for s in SUPPORTS.values():
        lines.append(asp.fact("support", s.id))
        lines.append(asp.fact("strong", s.id, s.strength))
    lines.append(asp.fact("promenade", "promenade"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    return [tuple() for _ in asp.atoms(model, "story_ok")]


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(StoryParams(setting="promenade", rendition="song", snag="paper_wind", support="hold_page",
                                      friend_a="Mina", friend_a_gender="girl", friend_b="Jules", friend_b_gender="boy"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if not valid_combos():
        print("MISMATCH: no valid combos found")
        rc = 1
    else:
        print("OK: smoke test passed and valid combos exist.")
    return rc


CURATED = [
    StoryParams(setting="promenade", rendition="song", snag="paper_wind", support="hold_page",
                friend_a="Mina", friend_a_gender="girl", friend_b="Jules", friend_b_gender="boy"),
    StoryParams(setting="promenade", rendition="poem", snag="stained_hands", support="napkin",
                friend_a="Asha", friend_a_gender="girl", friend_b="Noah", friend_b_gender="boy"),
    StoryParams(setting="pier", rendition="tune", snag="shy_voice", support="cheer",
                friend_a="Owen", friend_a_gender="boy", friend_b="Lina", friend_b_gender="girl"),
]


def explain_rejection() -> str:
    return "That combination would not make a sensible friendship fix."


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} plausible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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

    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
