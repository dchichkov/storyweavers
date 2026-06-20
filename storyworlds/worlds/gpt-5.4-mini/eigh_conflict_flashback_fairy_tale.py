#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/eigh_conflict_flashback_fairy_tale.py
=====================================================================

A tiny fairy-tale storyworld about a child, a hurtful quarrel, a remembered
lesson, and a kinder ending.

The world is built around a small castle domain:
- two young siblings or cousins
- a shiny object they both want
- a wise elder who remembers a flashback lesson
- a conflict that can be softened by remembering the past
- a storybook ending image that proves what changed

The seed word "eigh" is woven into the world as the old counting word used in
the castle nursery rhyme, so it can appear naturally in the story text.

The simulation tracks physical meters and emotional memes, and the prose is
driven by state changes rather than by a frozen template with swapped nouns.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "queen", "woman"}
        male = {"boy", "father", "dad", "king", "man"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    detail: str
    hall: str
    dark_spot: str

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
class Prize:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    glitter: str
    precious: bool = True

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
class Rivalry:
    id: str
    want: str
    grab: str
    jab: str
    quarrel: str

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
class Memory:
    id: str
    lesson: str
    flashback_line: str
    comfort: str

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["envy"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["flashback"] < THRESHOLD:
            continue
        sig = ("flashback", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] += 1
        out.append("__flashback__")
    return out


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


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("flashback", "memory", _r_flashback),
]


def reasonableness_gate(rivalry: Rivalry, prize: Prize) -> bool:
    return prize.precious and rivalry.id in RIVALRIES and prize.id in PRIZES


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def story_severity(prize: Prize, delay: int) -> int:
    return 1 + delay if prize.precious else delay


def is_contained(response: Response, prize: Prize, delay: int) -> bool:
    return response.power >= story_severity(prize, delay)


def tell(
    setting: Setting,
    prize: Prize,
    rivalry: Rivalry,
    memory: Memory,
    response: Response,
    hero_name: str,
    hero_gender: str,
    other_name: str,
    other_gender: str,
    elder_type: str,
    delay: int = 0,
    relation: str = "siblings",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="other"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder"))
    key = world.add(Entity(id="thing", type="thing", label=prize.label))
    world.facts["setting"] = setting
    world.facts["prize_cfg"] = prize
    world.facts["rivalry"] = rivalry
    world.facts["memory"] = memory
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["relation"] = relation
    hero.memes["envy"] = 1.0
    other.memes["envy"] = 1.0
    world.say(
        f"Once in a little castle, {hero.id} and {other.id} played beneath {setting.hall}. "
        f"{setting.detail}."
    )
    world.say(
        f"They both loved {prize.phrase}, for it shone like {prize.glitter}. "
        f'The nursery rhyme said, "One, two, thre-eigh," and the old stone room felt warm with song.'
    )
    world.para()
    world.say(
        f"But when {hero.id} reached for {prize.label}, {other.id} reached too, and their hands met in a fuss."
    )
    world.say(
        f'"I saw it first," said {hero.id}. "{rivalry.grab}" answered {other.id}, and the quarrel grew sharp.'
    )
    hero.memes["envy"] += 1
    other.memes["envy"] += 1
    propagate(world, narrate=False)
    if memory.id:
        hero.memes["flashback"] += 1
        world.say(
            f"{hero.id} paused, and a memory returned like a tiny bell."
        )
        world.say(memory.flashback_line)
    world.para()
    world.say(
        f"{elder.label_word.capitalize()} looked up from the fire and said, "
        f'"{memory.lesson}"'
    )
    if not is_contained(response, prize, delay):
        world.say(
            f"{hero.id} tried to keep the prize, but the trouble only shook harder."
        )
        world.say(
            f"{elder.label_word.capitalize()} had to step between them and lift the {prize.label} away."
        )
        world.say(
            f"Still, the remembered lesson made {hero.id} lower {hero.pronoun('possessive')} hands and breathe."
        )
    else:
        hero.memes["calm"] += 1
        other.memes["calm"] += 1
        world.say(
            f"{hero.id} remembered {memory.comfort} and slowly shared the {prize.label}."
        )
        world.say(
            f"{elder.label_word.capitalize()} smiled and used {response.text}."
        )
    world.para()
    if is_contained(response, prize, delay):
        world.say(
            f"In the end, {response.qa_text}."
        )
        world.say(
            f"{hero.id} and {other.id} sat together under {setting.dark_spot}, and the {prize.label} glimmered between them like a small moon."
        )
        outcome = "calm"
    else:
        world.say(
            f"In the end, {response.fail}."
        )
        world.say(
            f"{hero.id} and {other.id} stood apart for a moment, then looked to the elder for a fair turn."
        )
        outcome = "strained"
    world.facts["outcome"] = outcome
    world.facts["hero"] = hero
    world.facts["other"] = other
    world.facts["elder"] = elder
    world.facts["key"] = key
    return world


SETTINGS = {
    "castle": Setting("castle", "the castle", "Gold lamps blinked on the walls", "the long hall", "the shadowy stair"),
    "tower": Setting("tower", "the tower", "Moonlight touched the windows", "the spiral hall", "the little attic nook"),
    "garden": Setting("garden", "the garden", "Rosy hedges swayed in the breeze", "the rose arch", "the willow shade"),
}

PRIZES = {
    "crown": Prize("crown", "a tiny golden crown", "a tiny golden crown", "what the siblings both wanted", "table", "a star"),
    "orb": Prize("orb", "a glass orb", "a glass orb", "what the cousins both wanted", "pedestal", "a drop of light"),
    "ribbon": Prize("ribbon", "a silver ribbon", "a silver ribbon", "what the children both wanted", "bench", "a moonbeam"),
}

RIVALRIES = {
    "claim": Rivalry("claim", "I saw it first", "I saw it first", "That is mine", "their voices tangled"),
    "fairness": Rivalry("fairness", "Let's share", "Let's share", "Wait your turn", "the disagreement rang like a bell"),
}

MEMORIES = {
    "grandmother": Memory("grandmother", "share and the treasure stays lovely", "A flashback came: Grandmother once said, 'Two hands can hold one joy without breaking it.'", "Grandmother's lap"),
    "maid": Memory("maid", "kind hands make kinder endings", "A flashback came: the old maid had smiled and said, 'A gentle turn saves a tired heart.'", "the old song"),
}

RESPONSES = {
    "share": Response("share", 3, 3, "put the quarrel aside and share the treasure at last", "could not settle the quarrel in time", "put the quarrel aside and shared the treasure"),
    "turn": Response("turn", 2, 2, "let the elder turn it into a fair game of taking turns", "could not make the turn fair enough", "let the elder make it a fair game of turns"),
    "pause": Response("pause", 2, 1, "paused and took one slow breath", "paused, but the quarrel stayed sharp", "paused and took a slow breath"),
}

GIRL_NAMES = ["Ava", "Mina", "Nora", "Lily", "Rose", "Elsa"]
BOY_NAMES = ["Finn", "Theo", "Owen", "Leo", "Bram", "Jude"]
TRAITS = ["gentle", "brave", "thoughtful", "curious", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PRIZES:
            for rid in RIVALRIES:
                if reasonableness_gate(RIVALRIES[rid], PRIZES[pid]):
                    combos.append((sid, pid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    prize: str
    rivalry: str
    memory: str
    response: str
    hero: str
    hero_gender: str
    other: str
    other_gender: str
    elder: str
    trait: str
    delay: int = 0
    relation: str = "siblings"
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the old word "eigh" and a small conflict over {f["prize_cfg"].label}.',
        f"Tell a gentle castle story where {f['hero'].id} and {f['other'].id} quarrel, then remember an old lesson and become kinder.",
        f'Write a storybook tale with a flashback to a wise lesson, ending with {f["prize_cfg"].label} shared peacefully.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    other = f["other"]
    elder = f["elder"]
    prize = f["prize_cfg"]
    memory = f["memory"]
    resp = f["response"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id} and {other.id}, two children in a fairy-tale castle, and the wise elder who helps them."),
        ("What did the children want?", f"They both wanted {prize.phrase}, because it glittered like a tiny treasure in the hall."),
        ("What happened when they both reached for it?", f"They began to quarrel, and the conflict made the room feel sharp and uneasy."),
        ("What was the flashback?", f"It was a remembered moment when {memory.flashback_line.split(': ', 1)[1]}. That memory helped {hero.id} calm down."),
    ]
    if f["outcome"] == "calm":
        qa.append(
            ("How did the story end?", f"They shared the {prize.label} and the elder kept the peace. The ending was calm, and the treasure shone softly between them.")
        )
        qa.append(
            ("What changed after the flashback?", f"{hero.id} became calmer and kinder, because the old lesson reminded {hero.pronoun('object')} that sharing can keep treasure lovely. The remembered advice led to a gentler ending.")
        )
    else:
        qa.append(
            ("How did the story end?", f"The quarrel stayed tense, so the elder had to step in and make the turn fair. Even then, the children were left thinking about the lesson.")
        )
        qa.append(
            ("What changed after the flashback?", f"{hero.id} slowed down and breathed more carefully, but the conflict did not fully settle. The memory still softened the moment a little.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flashback?", "A flashback is when a story remembers something that happened before. It helps explain why a character feels a certain way now."),
        ("What is a conflict in a story?", "A conflict is a problem or disagreement that makes characters want different things. It gives the story a tense middle before the ending."),
        ("Why do fairy tales often have wise elders?", "Fairy tales often use wise elders to guide children toward kindness, fairness, and brave choices."),
        ("Why can sharing be a good ending?", "Sharing can end a conflict because both children get to enjoy the thing they wanted. It also keeps the people in the story feeling close."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "crown", "claim", "grandmother", "share", "Eigha", "girl", "Bram", "boy", "Queen", "gentle", 0),
    StoryParams("tower", "orb", "fairness", "maid", "turn", "Finn", "boy", "Mina", "girl", "King", "careful", 0),
    StoryParams("garden", "ribbon", "claim", "grandmother", "pause", "Lily", "girl", "Owen", "boy", "Queen", "thoughtful", 1),
]


def explain_rejection() -> str:
    return "(No story: this fairy-tale world needs a precious treasure and a real conflict over it.)"


def outcome_of(params: StoryParams) -> str:
    if is_contained(RESPONSES[params.response], PRIZES[params.prize], params.delay):
        return "calm"
    return "strained"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.precious:
            lines.append(asp.fact("precious", pid))
    for rid in RIVALRIES:
        lines.append(asp.fact("rivalry", rid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, R) :- setting(S), prize(P), rivalry(R), precious(P).
sensible(X) :- response(X), sense(X, N), sense_min(M), N >= M.
contained :- chosen_response(R), chosen_prize(P), chosen_delay(D), power(R, Pwr), severity(P, D, Sev), Pwr >= Sev.
severity(P, D, Sev) :- precious(P), Sev = 1 + D.
outcome(calm) :- contained.
outcome(strained) :- not contained.
"""


def asp_program(extra: str = "", show: str = "#show valid/3.\n#show sensible/1.\n#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(v[0] for v in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_prize", params.prize),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible response set matches.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    samples = [generate(CURATED[0])]
    rng = random.Random(777)
    for _ in range(5):
        try:
            p = resolve_params(build_parser().parse_args([]), rng)
            samples.append(generate(p))
        except StoryError:
            pass
    for s in samples:
        if not s.story.strip():
            rc = 1
            print("MISMATCH: empty story.")
    if rc == 0:
        print("OK: normal generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about conflict, flashback, and a gentler ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--rivalry", choices=RIVALRIES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["Queen", "King"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    setting, prize, rivalry = rng.choice(combos)
    memory = args.memory or rng.choice(sorted(MEMORIES))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    other_gender = args.other_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    other = args.other or rng.choice([n for n in (GIRL_NAMES if other_gender == "girl" else BOY_NAMES) if n != hero])
    elder = args.elder or rng.choice(["Queen", "King"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, prize, rivalry, memory, response, hero, hero_gender, other, other_gender, elder, rng.choice(TRAITS), delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PRIZES[params.prize],
        RIVALRIES[params.rivalry],
        MEMORIES[params.memory],
        RESPONSES[params.response],
        params.hero,
        params.hero_gender,
        params.other,
        params.other_gender,
        params.elder,
        params.delay,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.other}: {p.prize} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
