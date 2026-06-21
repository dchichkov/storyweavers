#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/equal_brush_spend_cautionary_transformation_conflict_bedtime.py
================================================================================================

A bedtime storyworld about two children, a shared brush, and a cautious turn
toward transformation.  A child wants to spend extra time brushing a magical
night-garden charm, but a worried sibling warns that too much brushing makes
the charm change in a risky way.  If they ignore the warning, the charm changes
badly; if they listen, they find a gentler equal share and end with a calm,
sleepy image.

The story is intentionally small: one cozy room, one brush, one transformation,
and a conflict that turns into a safer bedtime ending.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTION_MIN = 2
TRANSFORM_TRIGGER = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
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
    mood: str
    window_line: str
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
class Brush:
    id: str
    label: str
    phrase: str
    spend_word: str
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
class Charm:
    id: str
    label: str
    phrase: str
    safe_state: str
    risky_state: str
    transformed_state: str
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
class Resolve:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    brush = world.get("brush")
    charm = world.get("charm")
    if brush.meters["spend"] >= TRANSFORM_TRIGGER and charm.meters["glow"] < THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            charm.meters["glow"] += 1
            charm.memes["unease"] += 1
            out.append("__transform__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child_a").memes["want_more"] >= THRESHOLD and world.get("child_b").memes["warn"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child_a").memes["conflict"] += 1
            world.get("child_b").memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("transform", _r_transform), Rule("conflict", _r_conflict)]


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


def can_spend_enough(res: Resolve, brush: Brush, charm: Charm) -> bool:
    return res.power >= 2 and brush.label and charm.label


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid in BRUSHES:
            for cid in CHARMS:
                if BRUSHES[bid].phrase and CHARMS[cid].phrase:
                    combos.append((sid, bid, cid))
    return combos


def _do_brushing(world: World, brush: Entity, charm: Entity, amount: float) -> None:
    brush.meters["spend"] += amount
    world.get("child_a").memes["want_more"] += 1
    charm.meters["brushed"] += amount
    propagate(world, narrate=False)


def tell(setting: Setting, brush: Brush, charm: Charm, resolve: Resolve,
         child_a: str = "Mina", child_b: str = "June",
         child_a_type: str = "girl", child_b_type: str = "girl",
         parent: str = "mom") -> World:
    world = World()
    a = world.add(Entity(id="child_a", kind="character", type=child_a_type, label=child_a, role="spend"))
    b = world.add(Entity(id="child_b", kind="character", type=child_b_type, label=child_b, role="cautionary"))
    p = world.add(Entity(id="parent", kind="character", type=parent, label=parent, role="parent"))
    br = world.add(Entity(id="brush", kind="thing", type="brush", label=brush.label, attrs={"phrase": brush.phrase}, tags=set(brush.tags)))
    ch = world.add(Entity(id="charm", kind="thing", type="charm", label=charm.label, attrs={"phrase": charm.phrase}, tags=set(charm.tags)))

    a.memes["joy"] += 1
    b.memes["caution"] += 1
    b.memes["warn"] += 1
    world.say(
        f"At bedtime, {child_a} and {child_b} sat by the window in {setting.place}. "
        f"{setting.window_line} {child_a} found {brush.phrase}, and {child_a} wanted to spend a little longer brushing {charm.phrase}."
    )
    world.say(
        f"{child_a} said it would be equal if each turn felt fair and square, but {child_b} bit {('her' if b.type == 'girl' else 'his')} lip and warned that too much brushing could change the charm."
    )

    world.para()
    a.memes["want_more"] += 1
    if not can_spend_enough(resolve, brush, charm):
        raise StoryError("This story needs a sensible resolve with enough power.")
    world.say(
        f'"Let me spend more time," {child_a} whispered. "{brush.spend_word} makes it look prettier."'
    )
    world.say(
        f'"Careful," {child_b} said. "The charm might transform before bedtime."'
    )

    world.para()
    if resolve.power >= 2 and setting.id == "bedroom":
        _do_brushing(world, br, ch, 2.0)
        if ch.meters["glow"] >= THRESHOLD:
            world.say(
                f"Sure enough, the charm gave a small sparkly shiver and changed into {charm.risky_state}, which made both children gasp."
            )
        if resolve.power >= 3:
            ch.meters["glow"] = 0.0
            world.say(
                f"{parent.capitalize()} came softly to the door and {resolve.text.replace('{charm}', charm.label)}."
            )
            world.say(
                f"The room grew quiet again, and the charm settled into {charm.safe_state} instead of the risky change."
            )
            a.memes["calm"] += 1
            b.memes["calm"] += 1
        else:
            world.say(
                f"{parent.capitalize()} tried to help, but {resolve.fail.replace('{charm}', charm.label)}."
            )
            world.say(
                f"By the end, the charm stayed in {charm.transformed_state}, and the two children had to stop the game and go to sleep."
            )
            a.memes["fear"] += 1
            b.memes["fear"] += 1
    else:
        world.say(
            f"{child_b} suggested they share the brush equally: one careful stroke for {child_a}, one for {child_b}, then put it away."
        )
        world.say(
            f"They listened, and the charm stayed in {charm.safe_state}. The brush was set down before it could transform, and bedtime felt peaceful."
        )
        a.memes["calm"] += 1
        b.memes["calm"] += 1

    world.para()
    world.say(
        f"At last, {child_a} and {child_b} curled under the blanket while {setting.mood} light slipped across the room. "
        f"The brush was on the shelf, the charm was safe, and everyone could spend the rest of the night dreaming."
    )

    world.facts.update(
        child_a=a, child_b=b, parent=p, brush=br, charm=ch, setting=setting,
        resolve=resolve, outcome="transformed" if ch.meters["glow"] >= THRESHOLD else "calm"
    )
    return world


SETTINGS = {
    "bedroom": Setting(id="bedroom", place="the bedroom", mood="soft", window_line="The moonlight made a pale square on the rug."),
    "nursery": Setting(id="nursery", place="the nursery", mood="gentle", window_line="A lamp hummed low beside the crib."),
    "attic": Setting(id="attic", place="the attic room", mood="still", window_line="The attic window showed one shy star."),
}

BRUSHES = {
    "paintbrush": Brush(id="paintbrush", label="paintbrush", phrase="a little paintbrush", spend_word="spend", tags={"brush"}),
    "hairbrush": Brush(id="hairbrush", label="hairbrush", phrase="a smooth hairbrush", spend_word="brush", tags={"brush"}),
    "featherbrush": Brush(id="featherbrush", label="feather brush", phrase="a soft feather brush", spend_word="spend", tags={"brush"}),
}

CHARMS = {
    "paper_moon": Charm(id="paper_moon", label="paper moon", phrase="a paper moon charm", safe_state="resting on the sill", risky_state="a silver moth-wing shimmer", transformed_state="a glittery little blur", tags={"transformation"}),
    "wood_star": Charm(id="wood_star", label="wooden star", phrase="a wooden star charm", safe_state="still and warm", risky_state="a spinning bright star", transformed_state="a twirling chip of light", tags={"transformation"}),
    "night_seed": Charm(id="night_seed", label="night seed", phrase="a tiny night seed", safe_state="asleep in its bowl", risky_state="a glowing sprout", transformed_state="a glowing sprout", tags={"transformation"}),
}

RESOLVES = {
    "gentle": Resolve(id="gentle", sense=3, power=3, text="set the brush down gently and covered the charm with a napkin", fail="could only hold the napkin up for a moment before the shimmer came back", tags={"caution"}),
    "calm": Resolve(id="calm", sense=3, power=2, text="cupped the charm in a warm hand and dimmed the light with a tiny cloth", fail="was too late to keep the glow from spreading", tags={"caution"}),
}

GIRL_NAMES = ["Mina", "June", "Lina", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Eli", "Noah"]


@dataclass
class StoryParams:
    setting: str
    brush: str
    charm: str
    resolve: str
    child_a: str
    child_a_type: str
    child_b: str
    child_b_type: str
    parent: str
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.resolve and RESOLVES[args.resolve].sense < CAUTION_MIN:
        raise StoryError("That ending is too weak for this bedtime story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.brush is None or c[1] == args.brush)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, brush, charm = rng.choice(sorted(combos))
    resolve = args.resolve or rng.choice(sorted(RESOLVES))
    a_type = args.child_a_type or rng.choice(["girl", "boy"])
    b_type = args.child_b_type or ("boy" if a_type == "girl" and rng.random() < 0.5 else "girl")
    child_a = args.child_a or _pick_name(rng, a_type)
    child_b = args.child_b or _pick_name(rng, b_type, avoid=child_a)
    parent = args.parent or rng.choice(["mom", "dad"])
    return StoryParams(setting=setting, brush=brush, charm=charm, resolve=resolve,
                       child_a=child_a, child_a_type=a_type, child_b=child_b,
                       child_b_type=b_type, parent=parent)


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.brush in BRUSHES and params.charm in CHARMS and params.resolve in RESOLVES


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"].label
    b = f["child_b"].label
    br = f["brush"].label
    ch = f["charm"].label
    return [
        f'Write a bedtime story that includes the words "equal", "brush", and "spend".',
        f"Tell a gentle conflict story where {a} wants to spend more time with the {br}, but {b} worries that the {ch} may transform.",
        f"Write a calm bedtime story about two children finding an equal way to use a brush without causing a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, ch, br, res = f["child_a"], f["child_b"], f["charm"], f["brush"], f["resolve"]
    qas = [
        QAItem(
            question=f"What did {a.id} want to do with the {br.label}?",
            answer=f"{a.id} wanted to spend more time brushing {ch.phrase}. {a.id} thought the extra brushing would make it look prettier, but that choice also made trouble possible."
        ),
        QAItem(
            question=f"Why did {b.id} warn {a.id}?",
            answer=f"{b.id} warned {a.id} because the charm could transform if it was brushed too much. {b.id} was trying to keep the bedtime game safe and calm."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a quiet bedtime image: the brush was put away and the charm stayed safe in its gentle state. If the transformation began, the grown-up helped settle it before sleep."
        ),
    ]
    if f["outcome"] == "transformed":
        qas.append(
            QAItem(
                question=f"What did the grown-up do when the charm changed?",
                answer=f"The grown-up came softly and used the {res.id} way to calm things down. That helped the room settle again, even after the risky change."
            )
        )
    else:
        qas.append(
            QAItem(
                question="What was the equal choice the children made?",
                answer=f"They shared the brush fairly and took turns, so no one spent too long on the charm. That equal choice kept the bedtime moment peaceful."
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["brush"].tags) | set(world.facts["charm"].tags) | set(world.facts["resolve"].tags)
    out: list[QAItem] = []
    if "brush" in tags:
        out.append(QAItem("What is a brush?", "A brush is a tool with bristles that you use for brushing, painting, or smoothing something. It is gentle when you use it carefully."))
    if "transformation" in tags:
        out.append(QAItem("What is a transformation?", "A transformation is a change from one form or state into another. In stories, it can be magical or surprising."))
    if "caution" in tags:
        out.append(QAItem("What does it mean to be cautious?", "To be cautious means to move carefully and think about what could go wrong first. Caution helps keep a story safe."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions -- answerable from the story text =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bedroom", brush="paintbrush", charm="paper_moon", resolve="gentle", child_a="Mina", child_a_type="girl", child_b="June", child_b_type="girl", parent="mom"),
    StoryParams(setting="nursery", brush="hairbrush", charm="wood_star", resolve="calm", child_a="Owen", child_a_type="boy", child_b="Mina", child_b_type="girl", parent="dad"),
    StoryParams(setting="attic", brush="featherbrush", charm="night_seed", resolve="gentle", child_a="Lina", child_a_type="girl", child_b="Theo", child_b_type="boy", parent="mom"),
]


ASP_RULES = r"""
transform :- brush_spend(B, N), N >= 2, charm(C), not safe(C).
conflict :- want_more(A), warn(B), A != B.
outcome(transformed) :- transform.
outcome(calm) :- not transform.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BRUSHES:
        lines.append(asp.fact("brush", bid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    for rid, r in RESOLVES.items():
        lines.append(asp.fact("resolve", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    # smoke test
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, brush=None, charm=None, resolve=None, child_a=None, child_a_type=None, child_b=None, child_b_type=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    if valid_combos():
        print(f"OK: valid_combos() produced {len(valid_combos())} combos.")
    else:
        rc = 1
        print("MISMATCH: no valid combos.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about equal sharing, a brush, and cautious transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--brush", choices=BRUSHES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--resolve", choices=RESOLVES)
    ap.add_argument("--child-a")
    ap.add_argument("--child-b")
    ap.add_argument("--child-a-type", choices=["girl", "boy"])
    ap.add_argument("--child-b-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
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


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], BRUSHES[params.brush], CHARMS[params.charm], RESOLVES[params.resolve], params.child_a, params.child_b, params.child_a_type, params.child_b_type, params.parent)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.brush is None or c[1] == args.brush)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, brush, charm = rng.choice(sorted(combos))
    resolve = args.resolve or rng.choice(sorted(RESOLVES))
    a_type = args.child_a_type or rng.choice(["girl", "boy"])
    b_type = args.child_b_type or ("boy" if a_type == "girl" and rng.random() < 0.5 else "girl")
    child_a = args.child_a or rng.choice(GIRL_NAMES if a_type == "girl" else BOY_NAMES)
    child_b = args.child_b or rng.choice([n for n in (GIRL_NAMES if b_type == "girl" else BOY_NAMES) if n != child_a])
    parent = args.parent or rng.choice(["mom", "dad"])
    return StoryParams(setting=setting, brush=brush, charm=charm, resolve=resolve, child_a=child_a, child_a_type=a_type, child_b=child_b, child_b_type=b_type, parent=parent)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show combo/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("No ASP story listing is defined for this small world.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
