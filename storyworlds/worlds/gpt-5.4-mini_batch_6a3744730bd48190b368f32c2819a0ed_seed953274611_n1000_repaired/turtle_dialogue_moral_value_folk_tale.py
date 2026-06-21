#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/turtle_dialogue_moral_value_folk_tale.py
=========================================================================

A small folk-tale storyworld about a turtle, a river path, a tempting shortcut,
and a moral choice. The story is driven by a simple simulated world with
dialogue and a clear moral-value turn: a traveler wants to rush across a stream,
a turtle warns them, a safer act is chosen, and the ending proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/turtle_dialogue_moral_value_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/turtle_dialogue_moral_value_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/turtle_dialogue_moral_value_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/turtle_dialogue_moral_value_folk_tale.py --verify
"""

from __future__ import annotations

import argparse
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
MORAL_MIN = 2

NAMES = ["Milo", "Nina", "Pip", "Iris", "Juno", "Kiran", "Sora", "Tavi"]
COMPANIONS = ["crow", "goat", "rabbit", "squirrel", "mule"]
PLACES = {
    "bridge": {
        "label": "the old bridge",
        "risk": "the river below",
        "feature": "the bridge boards",
        "safe": "the narrow path by the reeds",
        "scene": "a mossy river crossing",
        "tags": {"river", "bridge"},
    },
    "ford": {
        "label": "the shallow ford",
        "risk": "the fast water",
        "feature": "the stones in the river",
        "safe": "the stepping stones near the bank",
        "scene": "a quiet river bend",
        "tags": {"river", "ford"},
    },
}
CHORES = {
    "berries": {
        "verb": "pick berries",
        "moral": "carefulness",
        "warning": "The berries are hidden close to the wet edge, and one wrong step could send you sliding.",
        "lesson": "It is wise to slow down and look before you reach.",
        "joy": "the bowl would be full and unbroken",
        "tags": {"berries", "careful"},
    },
    "goose": {
        "verb": "chase the goose",
        "moral": "kindness",
        "warning": "A startled goose can flap into trouble, and chasing it can leave you both frightened.",
        "lesson": "It is kinder to give frightened creatures a little room.",
        "joy": "the goose would calm down and nobody would be hurt",
        "tags": {"goose", "kindness"},
    },
    "fish": {
        "verb": "catch fish",
        "moral": "patience",
        "warning": "The river fish need still hands, and a hurried splash can scare them all away.",
        "lesson": "Patience often catches what hurry loses.",
        "joy": "the catch would come gently, one fish at a time",
        "tags": {"fish", "patience"},
    },
}
RESPONSES = {
    "pause": {
        "sense": 3,
        "power": 3,
        "text": "stopped beside the turtle, listened, and chose the slow safe way instead",
        "fail": "tried to stop, but the rush had already carried the moment away",
        "qa": "stopped, listened, and chose the slow safe way",
        "tags": {"pause", "careful"},
    },
    "detour": {
        "sense": 3,
        "power": 2,
        "text": "took the longer path around the wet stones and crossed safely",
        "fail": "tried the longer path, but the footing was still too tricky",
        "qa": "took the longer path around the wet stones",
        "tags": {"detour", "safe"},
    },
    "wait": {
        "sense": 2,
        "power": 2,
        "text": "waited for the river to settle before trying again",
        "fail": "waited, but the river stayed too wild for that plan",
        "qa": "waited for the river to settle",
        "tags": {"wait", "patience"},
    },
}

ASP_RULES = r"""
safe(R) :- response(R), sense(R,S), S >= sense_min.
valid(P,C,R) :- place(P), chore(C), response(R), risky(P,C), safe(R).
moral_story(P,C,R) :- valid(P,C,R).
"""

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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class PlaceCfg:
    id: str
    label: str
    risk: str
    feature: str
    safe: str
    scene: str
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
class ChoreCfg:
    id: str
    verb: str
    moral: str
    warning: str
    lesson: str
    joy: str
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
class ResponseCfg:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str
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
    chore: str
    response: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

def hazard(place: PlaceCfg, chore: ChoreCfg) -> bool:
    return "river" in place.tags and chore.id in CHORES

def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, r) for p in PLACES for c in CHORES for r in RESPONSES if hazard(PlaceCfg(**PLACES[p]), ChoreCfg(**CHORES[c])) and RESPONSES[r]["sense"] >= MORAL_MIN]

def sensible_responses() -> list[ResponseCfg]:
    return [ResponseCfg(id=k, **v) for k, v in RESPONSES.items() if v["sense"] >= MORAL_MIN]

def _r_ripple(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["trouble"] >= THRESHOLD and ("ripple", e.id) not in world.fired:
            world.fired.add(("ripple", e.id))
            world.get("scene").meters["tension"] += 1
            for kid in ("hero", "companion"):
                world.get(kid).memes["worry"] += 1
            out.append("__ripple__")
    return out

def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_ripple(world):
            changed = True

def tell(place: PlaceCfg, chore: ChoreCfg, response: ResponseCfg, params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, role="hero"))
    companion = w.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion, role="companion"))
    elder = w.add(Entity(id="elder", kind="character", type=params.elder_type, label=params.elder, role="elder"))
    scene = w.add(Entity(id="scene", type="place", label=place.scene))
    turtle = w.add(Entity(id="turtle", kind="character", type="turtle", label="the turtle", role="guide"))
    w.facts.update(place=place, chore=chore, response=response, hero=hero, companion=companion, elder=elder, scene=scene, turtle=turtle)

    hero.memes["desire"] += 1
    companion.memes["joy"] += 1
    w.say(f"Once, at {place.label}, {hero.label} and {companion.label} came walking with a little goal in mind.")
    w.say(f'"Look," said {hero.label}, "I want to {chore.verb}."')
    w.say(f'{companion.label} smiled. "That sounds fine," {companion.pronoun()} said, "if the ground is kind."')
    w.para()
    w.say(f'Near the water sat {turtle.label}, slow as a leaf on a still pond.')
    w.say(f'"Good day," said the turtle. "What do you seek?"')
    w.say(f'"We seek {chore.verb}," said {hero.label}.')
    w.say(f'"Then hear me," said the turtle. "{chore.warning}"')
    w.say(f'"Why?" asked {hero.label}.')
    w.say(f'"Because," said the turtle, "{chore.lesson}"')
    hero.memes["temptation"] += 1
    if response.id == "pause":
        w.para()
        w.say(f'"You are right," said {hero.label}. "{response.text}."')
        w.say(f'"Good," said {turtle.label}. "A kind heart grows larger when it listens."')
        companion.memes["trust"] += 1
        hero.memes["wisdom"] += 1
        w.say(f"So {hero.label} and {companion.label} chose {place.safe} instead, and {chore.joy}.')
        w.say(f'They worked slowly, and the river kept its peace.')
    elif response.id == "detour":
        w.para()
        w.say(f'"Come then," said {companion.label}, "{response.text}."')
        w.say(f'"A longer path is still a good path," said the turtle, "if it keeps feet safe."')
        hero.memes["wisdom"] += 1
        w.say(f'They crossed by {place.safe}, and {chore.joy}.')
        w.say(f'The turtle watched them go, its shell bright in the sun.')
    else:
        w.para()
        w.say(f'"We will try," said {hero.label}, "{response.text}."')
        w.say(f'"Patience," said the turtle, "is the smallest river boat."')
        hero.memes["stubborn"] += 1
        w.say(f'They waited, and the water settled enough for {place.safe}, so {chore.joy}.')
        w.say(f'At last, the day felt gentle again.')
    elder.memes["pride"] += 1
    world = w
    world.facts.update(outcome="safe", moral=chore.moral)
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story with dialogue that includes a turtle and teaches {f["chore"].moral}.',
        f'Tell a short story where the turtle speaks, warns a child, and the child chooses a wiser path at {f["place"].label}.',
        f'Write a gentle moral tale for young children about {f["chore"].verb} near {f["place"].risk}.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    turtle = f["turtle"]
    chore = f["chore"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.label} wanted to {chore.verb}. The wish started the story, and it was the reason the turtle had to speak up."
        ),
        QAItem(
            question=f"What did the turtle say to warn them?",
            answer=f"The turtle warned them that {chore.warning.lower()} It gave a calm reason, so the child could choose a wiser path."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a safer choice at {place.label}. The children listened, and the ending showed the moral value of {chore.moral}."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a turtle like in a folk tale?",
            answer="A turtle is often slow, steady, and wise in folk tales. It can speak like a teacher and help others make good choices."
        ),
        QAItem(
            question="Why is it good to listen before acting?",
            answer="Listening gives you time to think. That helps you avoid trouble and choose the safer, kinder way."
        ),
        QAItem(
            question="What does a moral value mean?",
            answer="A moral value is a good idea for how to live, like patience, kindness, or carefulness. Stories often show it through what the characters choose."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)

CURATED = [
    StoryParams(place="bridge", chore="berries", response="pause", hero="Milo", hero_type="boy", companion="Nina", companion_type="girl", elder="Grandma", elder_type="woman"),
    StoryParams(place="ford", chore="fish", response="wait", hero="Iris", hero_type="girl", companion="Tavi", companion_type="boy", elder="Grandpa", elder_type="man"),
    StoryParams(place="bridge", chore="goose", response="detour", hero="Pip", hero_type="boy", companion="Sora", companion_type="girl", elder="Auntie", elder_type="woman"),
]

def explain_rejection(place: PlaceCfg, chore: ChoreCfg, response: ResponseCfg) -> str:
    return f"(No story: the chosen combination does not make a solid moral tale.)"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld with a turtle, dialogue, and a moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--chore", choices=CHORES)
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.chore and args.response and (args.place, args.chore, args.response) not in combos:
        raise StoryError(explain_rejection(PlaceCfg(**PLACES[args.place]), ChoreCfg(**CHORES[args.chore]), ResponseCfg(id=args.response, **RESPONSES[args.response])))
    picks = [c for c in combos if (not args.place or c[0] == args.place) and (not args.chore or c[1] == args.chore) and (not args.response or c[2] == args.response)]
    if not picks:
        raise StoryError("(No valid combination matches the given options.)")
    place, chore, response = rng.choice(sorted(picks))
    hero_type = rng.choice(["boy", "girl"])
    companion_type = "girl" if hero_type == "boy" else "boy"
    return StoryParams(
        place=place, chore=chore, response=response,
        hero=rng.choice(NAMES), hero_type=hero_type,
        companion=rng.choice([n for n in NAMES if n != ""]), companion_type=companion_type,
        elder=rng.choice(["Grandma", "Grandpa", "Auntie", "Uncle"]),
        elder_type=rng.choice(["woman", "man"]),
    )

def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.chore not in CHORES or params.response not in RESPONSES:
        raise StoryError("invalid params")
    world = tell(PlaceCfg(id=params.place, **PLACES[params.place]), ChoreCfg(id=params.chore, **CHORES[params.chore]), ResponseCfg(id=params.response, **RESPONSES[params.response]), params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", MORAL_MIN)]
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CHORES:
        lines.append(asp.fact("chore", c))
        lines.append(asp.fact("risky", "bridge", c))
        lines.append(asp.fact("risky", "ford", c))
    for r, d in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, d["sense"]))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            rc = 1
            print("MISMATCH in ASP parity.")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            rc = 1
            print("MISMATCH: empty story.")
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        traceback.print_exc()
        return 1
    return rc

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
