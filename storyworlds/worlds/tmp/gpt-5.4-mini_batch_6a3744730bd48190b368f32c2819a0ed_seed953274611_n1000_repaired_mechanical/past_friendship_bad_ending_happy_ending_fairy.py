#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/past_friendship_bad_ending_happy_ending_fairy.py
=================================================================================

A small fairy-tale storyworld about two friends in the past: they try to share a
magical task, one ending goes badly, and another ends happily because a kinder
choice or a better helper changes what happens.

The domain is intentionally tiny and classical:
- a pair of friends,
- a fairy-tale task,
- a fragile enchanted thing,
- a bad ending when the task goes wrong,
- a happy ending when the friends use a safer, gentler plan.

It supports the standard Storyweavers storyworld CLI and a tiny inline ASP twin
for parity checks.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king", "knight"}
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


@dataclass
class Tale:
    id: str
    place: str
    title: str
    setting: str
    task: str
    reason: str
    ending_image: str
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
class Charm:
    id: str
    label: str
    shine: str
    safe: bool = True
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
class Trouble:
    id: str
    label: str
    spell: str
    risky: bool = True
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
class Fix:
    id: str
    label: str
    method: str
    power: int
    kindness: int
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
    tale: str
    trouble: str
    fix: str
    friend_a: str
    friend_a_type: str
    friend_b: str
    friend_b_type: str
    helper: str
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
        clone.facts = dict(self.facts)
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


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["shattered"] < THRESHOLD:
            continue
        if ("spoil", ent.id) in world.fired:
            continue
        world.fired.add(("spoil", ent.id))
        if "heart" in world.entities:
            world.get("heart").memes["sadness"] += 1
        out.append("__spoiled__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    if world.get("heart").memes["hope"] >= THRESHOLD and world.get("heart").memes["trust"] >= THRESHOLD:
        if ("mend", "heart") not in world.fired:
            world.fired.add(("mend", "heart"))
            world.get("heart").memes["hope"] += 1
            out.append("__mended__")
    return out


CAUSAL_RULES = [Rule("spoil", "physical", _r_spoil), Rule("mend", "social", _r_mend)]


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


def valid_tale(tale: Tale, trouble: Trouble, fix: Fix) -> bool:
    return trouble.risky and fix.power >= 2 and fix.kindness >= SENSE_MIN


def outcome_of(params: StoryParams) -> str:
    return "happy" if FIXES[params.fix].power >= TROUBLES[params.trouble].spell.count(" ") + 1 else "bad"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.kindness >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: (f.kindness, f.power))


def _past_phrase() -> str:
    return "In the past, in a little kingdom"


def tell(tale: Tale, trouble: Trouble, fix: Fix, a_name: str, a_type: str,
         b_name: str, b_type: str, helper_name: str, helper_type: str) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_type, role="friend"))
    b = world.add(Entity(id=b_name, kind="character", type=b_type, role="friend"))
    h = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    heart = world.add(Entity(id="heart", kind="thing", type="thing", label="the little heart"))
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    h.memes["kindness"] += 1
    heart.memes["trust"] = 1
    heart.memes["hope"] = 1

    world.say(f"{_past_phrase()}, {a.id} and {b.id} were true friends. {tale.setting}")
    world.say(f"They had a task to do: {tale.task}.")
    world.say(f"They wished to do it because {tale.reason}.")
    world.para()
    world.say(f"But then {trouble.label} came near, and its {trouble.spell} made the task risky.")
    world.say(f"{a.id} looked worried, and {b.id} looked down at the ground.")

    if fix.kindness >= SENSE_MIN and fix.power >= 2:
        world.para()
        world.say(
            f"{h.id} came by with {fix.label}. {h.pronoun().capitalize()} said they could "
            f"{fix.method} instead of rushing."
        )
        world.say(f"The friends agreed, and together they tried the gentler way.")
        if fix.power >= 3:
            world.get("heart").memes["hope"] += 1
            world.get("heart").memes["trust"] += 1
            world.say("The little heart felt safe again.")
            world.say(f"{tale.ending_image}")
        else:
            world.get("heart").meters["shattered"] += 1
            propagate(world, narrate=False)
            world.say(f"Still, the trouble was too strong, and the little heart cracked.")
            world.say("That was the bad ending: the friends were sorry, and the magic dimmed.")
    else:
        world.para()
        world.get("heart").meters["shattered"] += 1
        propagate(world, narrate=False)
        world.say(f"{a.id} and {b.id} hurried anyway, and the little heart broke.")
        world.say("That was the bad ending: the spell slipped away, and everyone felt sad.")

    world.facts.update(
        tale=tale,
        trouble=trouble,
        fix=fix,
        friend_a=a,
        friend_b=b,
        helper=h,
        heart=heart,
        ending="happy" if heart.memes["hope"] >= 2 and heart.meters["shattered"] < THRESHOLD else "bad",
    )
    return world


TALES = {
    "rose_garden": Tale(
        id="rose_garden",
        place="rose garden",
        title="The Rose Garden Promise",
        setting="A white gate opened into a rose garden, and the morning wind smelled sweet.",
        task="carry silver water to the sleeping roses",
        reason="the roses were old friends of the moon and needed gentle care",
        ending_image="By dusk, the roses stood bright again, and the garden glowed like a lantern."
    ),
    "moon_well": Tale(
        id="moon_well",
        place="moon well",
        title="The Moon Well Wish",
        setting="A moon-well shimmered beside the path, and every stone looked silver.",
        task="drop a ribbon into the well to ask for rain",
        reason="the land had been dry, and the farmers hoped for clouds",
        ending_image="At the end, the ribbon floated clean and the well sang softly in the dark."
    ),
    "glass_harp": Tale(
        id="glass_harp",
        place="glass harp",
        title="The Glass Harp Song",
        setting="Under a star tree, a glass harp waited on a mossy bench.",
        task="play one gentle note so the birds would return",
        reason="the birds loved music and had forgotten the path home",
        ending_image="Soon the birds came back, and the harp rang like a tiny star."
    ),
}

TROUBLES = {
    "wind": Trouble(id="wind", label="a wild wind", spell="whirling gust", risky=True, tags={"wind", "past"}),
    "shadow": Trouble(id="shadow", label="a long shadow", spell="cold hush", risky=True, tags={"shadow", "past"}),
    "frost": Trouble(id="frost", label="a thin frost", spell="silver bite", risky=True, tags={"frost", "past"}),
}

FIXES = {
    "slow_song": Fix(id="slow_song", label="a slow song", method="sing softly and wait", power=3, kindness=3, tags={"song", "gentle"}),
    "blanket": Fix(id="blanket", label="a warm blanket", method="wrap the task and move slowly", power=2, kindness=2, tags={"blanket", "gentle"}),
    "lantern": Fix(id="lantern", label="a lantern", method="light the path and do it together", power=4, kindness=3, tags={"lantern", "gentle"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for t in TALES:
        for tr in TROUBLES:
            for fx in FIXES:
                if valid_tale(TALES[t], TROUBLES[tr], FIXES[fx]):
                    out.append((t, tr, fx))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale friendship storyworld.")
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--friend-a")
    ap.add_argument("--friend-a-type", choices=["girl", "boy"])
    ap.add_argument("--friend-b")
    ap.add_argument("--friend-b-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["fairy", "queen", "knight", "mother", "father"])
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
              if (args.tale is None or c[0] == args.tale)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tale, trouble, fix = rng.choice(sorted(combos))
    a_name = args.friend_a or rng.choice(["Mira", "Nell", "Tobi", "Elin"])
    b_name = args.friend_b or rng.choice([n for n in ["Mira", "Nell", "Tobi", "Elin", "Pip"] if n != a_name])
    a_type = args.friend_a_type or rng.choice(["girl", "boy"])
    b_type = args.friend_b_type or ("boy" if a_type == "girl" else "girl")
    helper = args.helper or rng.choice(["the fairy", "the queen", "the knight"])
    helper_type = args.helper_type or rng.choice(["fairy", "queen", "knight"])
    return StoryParams(
        tale=tale,
        trouble=trouble,
        fix=fix,
        friend_a=a_name,
        friend_a_type=a_type,
        friend_b=b_name,
        friend_b_type=b_type,
        helper=helper,
        helper_type=helper_type,
    )


def prompts(world: World) -> list[str]:
    f = world.facts
    t: Tale = f["tale"]
    tr: Trouble = f["trouble"]
    fx: Fix = f["fix"]
    return [
        f"Write a fairy tale about friendship in the past, and include the word 'past'.",
        f"Tell a short story where two friends try to {t.task}, but {tr.label} causes trouble.",
        f"Write a fairy-tale story with a bad ending and a happy ending, where a helper uses {fx.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["friend_a"]
    b: Entity = f["friend_b"]
    h: Entity = f["helper"]
    t: Tale = f["tale"]
    tr: Trouble = f["trouble"]
    fx: Fix = f["fix"]
    ending = f["ending"]
    items = [
        QAItem(
            question="Who were the friends?",
            answer=f"The friends were {a.id} and {b.id}. They cared about each other and wanted to help with the task together."
        ),
        QAItem(
            question="What made the task hard?",
            answer=f"{tr.label} made the task hard because its {tr.spell} was risky. The trouble turned a simple job into a tense moment."
        ),
    ]
    if ending == "happy":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily because {h.id} brought {fx.label} and the friends chose the gentle way. The little heart stayed safe, and the fairy-tale image at the end showed the change."
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended badly because the friends rushed ahead and the little heart broke. The ending showed how a wrong choice can spoil a good wish."
        ))
    return items


KNOWLEDGE = {
    "past": [("What does 'past' mean?", "The past is time that already happened before now.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, share, and help each other.")],
    "fairy": [("What does a fairy do in a fairy tale?", "A fairy often helps, warns, or gives magic in a fairy tale.")],
    "ending": [("What is an ending in a story?", "The ending is the last part, where you learn what finally happened.")],
    "heart": [("What does a heart symbolize in fairy tales?", "A heart often stands for feelings like love, trust, and kindness.")],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trouble"].tags) | set(world.facts["fix"].tags) | {"past", "friendship", "ending"}
    out: list[QAItem] = []
    for tag, qa in KNOWLEDGE.items():
        if tag in tags:
            for q, a in qa:
                out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    tale = TALES.get(params.tale)
    trouble = TROUBLES.get(params.trouble)
    fix = FIXES.get(params.fix)
    if tale is None or trouble is None or fix is None:
        raise StoryError("Invalid params for this world.")
    world = tell(tale, trouble, fix, params.friend_a, params.friend_a_type, params.friend_b, params.friend_b_type, params.helper, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, R, F) :- tale(T), trouble(R), fix(F), risky(R), kindness(F, K), K >= sense_min, power(F, P), P >= 2.
ending(happy) :- chosen_fix(F), power(F, P), P >= 3.
ending(bad) :- chosen_fix(F), power(F, P), P < 3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TALES:
        lines.append(asp.fact("tale", tid))
    for rid, r in TROUBLES.items():
        lines.append(asp.fact("trouble", rid))
        if r.risky:
            lines.append(asp.fact("risky", rid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("kindness", fid, f.kindness))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generate smoke test passed.")
    return 0


CURATED = [
    StoryParams(tale="rose_garden", trouble="wind", fix="lantern", friend_a="Mira", friend_a_type="girl", friend_b="Pip", friend_b_type="boy", helper="the fairy", helper_type="fairy"),
    StoryParams(tale="moon_well", trouble="shadow", fix="slow_song", friend_a="Nell", friend_a_type="girl", friend_b="Tobi", friend_b_type="boy", helper="the queen", helper_type="queen"),
    StoryParams(tale="glass_harp", trouble="frost", fix="blanket", friend_a="Elin", friend_a_type="girl", friend_b="Finn", friend_b_type="boy", helper="the knight", helper_type="knight"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def _trace_dummy(_: World) -> None:
    return


if __name__ == "__main__":
    main()
