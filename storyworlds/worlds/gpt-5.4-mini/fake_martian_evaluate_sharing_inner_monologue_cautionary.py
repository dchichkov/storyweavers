#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fake_martian_evaluate_sharing_inner_monologue_cautionary.py
============================================================================================

A tiny fairy-tale storyworld about a child, a shiny "martian" trinket, a fake
claim, a sharing choice, and a cautious inner monologue that prevents trouble.

The world is intentionally small and classical:
- one child wants a glowing object for a pretend story
- an item is mistaken for something magical or martian
- a careful inner monologue helps the child evaluate the risk
- sharing a truthful explanation changes the ending image

The required seed words are woven into the domain:
- fake
- martian
- evaluate

Style: fairy tale, child-facing, concrete, and state-driven.
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
CAUTION_MIN = 2.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



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
    mood: str
    has_pond: bool = False
    has_tower: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Wonder:
    id: str
    label: str
    phrase: str
    glow: str
    appears_martian: bool = False
    is_fake: bool = False
    shareable: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Evaluation:
    id: str
    sense: int
    text: str
    warning: str
    truth_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    orb = world.entities.get("wonder")
    if not orb or orb.meters["seen"] < THRESHOLD:
        return out
    sig = ("shine", orb.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        if kid.role == "child":
            kid.memes["wonder"] += 1
    out.append("__shine__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("risk") and not world.facts.get("shared_truth"):
        for kid in world.characters():
            if kid.role == "child":
                kid.memes["worry"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [
    Rule("shine", "light", _r_shine),
    Rule("fear", "social", _r_fear),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable_wonder(wonder: Wonder) -> bool:
    return wonder.shareable and wonder.appears_martian


def evaluate_need(wonder: Wonder, setting: Setting) -> bool:
    return wonder.appears_martian and setting.has_tower


def prudent_choice(evaluation: Evaluation) -> bool:
    return evaluation.sense >= CAUTION_MIN


def predict_truth(world: World, wonder_id: str) -> dict:
    sim = world.copy()
    _take_close_look(sim, sim.get(wonder_id), narrate=False)
    return {
        "risk": bool(sim.facts.get("risk", False)),
        "shared": bool(sim.facts.get("shared_truth", False)),
    }


def _take_close_look(world: World, wonder: Entity, narrate: bool = True) -> None:
    wonder.meters["seen"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Once upon a time, in {setting.place}, {child.id} and {friend.id} went "
        f"wandering where the grass was green and the birds sang like silver bells."
    )
    world.say(
        f"They found a small wonder on a stone, and it shone with a strange blue glow."
    )


def describe_wonder(world: World, child: Entity, wonder: Wonder) -> None:
    world.say(
        f"{child.id} leaned close. {child.pronoun().capitalize()} thought, "
        f'"It looks like a {wonder.label}, maybe a {wonder.label_word if hasattr(wonder, "label_word") else wonder.label} from the stars."'
    )


def reveal_fake(world: World, child: Entity, wonder: Wonder) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} wanted to believe the wonder was a real {wonder.label}, but "
        f"a tiny doubt tapped at {child.pronoun("possessive")} heart."
    )
    world.say(
        f'The thought came quietly: "It may be fake, and I should evaluate it before I boast."'
    )


def caution(world: World, friend: Entity, child: Entity, wonder: Wonder) -> None:
    friend.memes["care"] += 1
    pred = predict_truth(world, "wonder")
    world.facts["risk"] = evaluate_need(wonder, world.setting)
    world.say(
        f"{friend.id} touched {friend.pronoun('possessive')} chin and said, "
        f'"Let us not hurry. Not every bright thing is a martian treasure."'
    )
    if pred["risk"]:
        world.say(
            f'"We ought to evaluate it first," {friend.id} whispered. '
            f'"If it is special, we can share the truth. If not, we should keep our feet on the ground."'
        )


def choose_truth(world: World, child: Entity, wonder: Wonder, evaluation: Evaluation) -> None:
    child.memes["courage"] += 1
    if prudent_choice(evaluation):
        world.facts["shared_truth"] = True
        world.say(
            f"{child.id} nodded. {child.pronoun().capitalize()} remembered the careful thought and chose to tell the truth."
        )
        world.say(
            f'"It is a fake martian stone," {child.id} said, "but it still sparkles beautifully."'
        )
    else:
        world.facts["shared_truth"] = False
        world.say(
            f"{child.id} nearly called it a martian treasure at once, yet the doubt stayed."
        )


def share_and_end(world: World, child: Entity, friend: Entity, wonder: Wonder) -> None:
    child.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Then {child.id} shared the stone with {friend.id}, and the two children passed it back and forth like a little star."
    )
    world.say(
        f"They laughed at the pretty trick of it, and the fake treasure became a shared game instead of a proud mistake."
    )
    world.say(
        f"By sunset, the wonder still glowed on the path, but now it belonged to honesty, friendship, and a calmer heart."
    )


def tell(setting: Setting, wonder: Wonder, evaluation: Evaluation,
         child_name: str = "Lina", child_gender: str = "girl",
         friend_name: str = "Pip", friend_gender: str = "boy",
         parent_name: str = "Queen Mira", parent_gender: str = "queen") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label="the queen"))
    orb = world.add(Entity(id="wonder", kind="thing", type="thing", label=wonder.label, attrs={"shareable": wonder.shareable}))
    world.facts["wonder_cfg"] = wonder
    world.facts["evaluation_cfg"] = evaluation
    world.facts["setting"] = setting
    world.facts["parent"] = parent

    setup(world, child, friend, setting)
    world.para()
    describe_wonder(world, child, wonder)
    reveal_fake(world, child, wonder)
    caution(world, friend, child, wonder)

    world.para()
    _take_close_look(world, orb)
    choose_truth(world, child, wonder, evaluation)
    share_and_end(world, child, friend, wonder)

    world.facts.update(
        child=child, friend=friend, wonder=orb,
        risk=world.facts.get("risk", False),
        shared_truth=world.facts.get("shared_truth", False),
        evaluated=True,
    )
    return world


SETTINGS = {
    "castle_garden": Setting("castle garden", "the castle garden", "fair", has_tower=True),
    "moon_lane": Setting("moonlit lane", "the moonlit lane", "silver", has_tower=False),
    "rose_dell": Setting("rose dell", "the rose dell", "golden", has_tower=True),
}

WONDERS = {
    "glow_pebble": Wonder("glow_pebble", "pebble", "a pebble like a moon coin", "glowed blue",
                          appears_martian=True, is_fake=True, shareable=True, tags={"fake", "martian", "share"}),
    "tin_star": Wonder("tin_star", "star", "a star-shaped tin charm", "sparkled bright",
                       appears_martian=True, is_fake=True, shareable=True, tags={"fake", "martian", "share"}),
    "glass_egg": Wonder("glass_egg", "egg", "a glass egg on a ribbon", "shimmered green",
                        appears_martian=False, is_fake=False, shareable=True, tags={"share"}),
}

EVALUATIONS = {
    "careful": Evaluation("careful", 3, "careful evaluation", "a gentle warning", "truth first", tags={"evaluate", "cautionary"}),
    "swift": Evaluation("swift", 1, "quick guessing", "a hurried warning", "truth first", tags={"evaluate", "cautionary"}),
}

GIRL_NAMES = ["Lina", "Mina", "Rose", "Ava", "Sera", "Elin"]
BOY_NAMES = ["Pip", "Bram", "Theo", "Finn", "Noel", "Joss"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    wonder: str
    evaluation: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for wid, wonder in WONDERS.items():
            for eid, evaluation in EVALUATIONS.items():
                if is_reasonable_wonder(wonder) and evaluate_need(wonder, setting) and prudent_choice(evaluation):
                    combos.append((sid, wid, eid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: fake martian wonder, evaluate, share, and caution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--evaluation", choices=EVALUATIONS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.wonder:
        w = WONDERS[args.wonder]
        if not is_reasonable_wonder(w):
            raise StoryError("No story: this wonder is not a shareable fake martian thing.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.wonder is None or c[1] == args.wonder)
              and (args.evaluation is None or c[2] == args.evaluation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, wonder, evaluation = rng.choice(sorted(combos))
    cgender = args.child_gender or rng.choice(["girl", "boy"])
    fgender = args.friend_gender or ("boy" if cgender == "girl" else "girl")
    child_name = rng.choice(GIRL_NAMES if cgender == "girl" else BOY_NAMES)
    friend_name = rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != child_name])
    parent_name = rng.choice(["Queen Mira", "King Alder", "Queen Willow"])
    parent_gender = "queen" if parent_name.startswith("Queen") else "king"
    return StoryParams(setting, wonder, evaluation, child_name, cgender, friend_name, fgender, parent_name, parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child that includes the words "fake", "martian", and "evaluate".',
        f"Tell a gentle cautionary story where {f['child'].id} thinks a shining object might be martian, then pauses to evaluate it before sharing the truth.",
        f"Write a fairy tale about a fake treasure, an inner warning, and a kind act of sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, wonder = f["child"], f["friend"], f["wonder_cfg"]
    parent = f["parent"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, who found a strange little wonder in the castle path. {parent.id} helps by making the ending feel calm and safe."),
        ("What did the child think the object was at first?",
         f"{child.id} thought it might be a martian treasure. That was the fake part of the idea, because the shiny thing only looked magical."),
        ("What did the careful inner thought help the child do?",
         f"It helped {child.id} evaluate the object before bragging. That pause made {child.id} choose truth instead of a quick guess."),
    ]
    if f.get("shared_truth"):
        qa.append(("How did the children finish the story?",
                   f"They shared the object and told the truth together. The fake treasure became a shared game, and nobody was fooled for long."))
    else:
        qa.append(("How did the children finish the story?",
                   f"They did not settle the matter as calmly as they could have, but the warning still kept the tale from becoming boastful."))
    return qa


KNOWLEDGE = {
    "fake": [("What does fake mean?",
              "Fake means something is not real, even if it looks real for a moment.")],
    "martian": [("What is a martian in a story?",
                 "A martian is a made-up visitor from Mars, often used in a pretend story.")],
    "evaluate": [("What does evaluate mean?",
                  "Evaluate means to look carefully at something and think about it before deciding.")],
    "share": [("What does it mean to share?",
               "To share means to let someone else use, see, or enjoy the same thing with you.")],
    "cautionary": [("What is a cautionary story?",
                    "A cautionary story teaches a lesson by showing what can go wrong and how to choose better.")],
}

def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["wonder_cfg"].tags) | {"share", "cautionary"}
    if world.facts.get("shared_truth"):
        tags.add("evaluate")
    out = []
    for key in ["fake", "martian", "evaluate", "share", "cautionary"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(W) :- wonder(W), martian(W), fake(W), shareable(W).
needs_eval(S, W) :- setting(S), wonder(W), martian(W), tower(S).
good_story(S, W, E) :- reasonable(W), needs_eval(S, W), evaluation(E), sense(E, N), caution_min(M), N >= M.
outcome(shared_truth) :- good_story(S, W, E), chosen(S), chosen_w(W), chosen_e(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_tower:
            lines.append(asp.fact("tower", sid))
    for wid, w in WONDERS.items():
        lines.append(asp.fact("wonder", wid))
        if w.appears_martian:
            lines.append(asp.fact("martian", wid))
        if w.is_fake:
            lines.append(asp.fact("fake", wid))
        if w.shareable:
            lines.append(asp.fact("shareable", wid))
    for eid, e in EVALUATIONS.items():
        lines.append(asp.fact("evaluation", eid))
        lines.append(asp.fact("sense", eid, e.sense))
    lines.append(asp.fact("caution_min", CAUTION_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP vs Python valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, wonder=None, evaluation=None,
                                                            child_gender=None, friend_gender=None),
                                         random.Random(7)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], WONDERS[params.wonder], EVALUATIONS[params.evaluation],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender,
                 params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def explain_rejection() -> str:
    return "No story: this combination does not support a fair fake-martian cautionary sharing tale."


CURATED = [
    StoryParams("castle_garden", "glow_pebble", "careful", "Lina", "girl", "Pip", "boy", "Queen Mira", "queen"),
    StoryParams("rose_dell", "tin_star", "careful", "Mina", "girl", "Joss", "boy", "King Alder", "king"),
    StoryParams("castle_garden", "tin_star", "careful", "Theo", "boy", "Elin", "girl", "Queen Willow", "queen"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
