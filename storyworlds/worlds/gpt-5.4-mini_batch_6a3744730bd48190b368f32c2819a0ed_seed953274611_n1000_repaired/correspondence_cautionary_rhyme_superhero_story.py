#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/correspondence_cautionary_rhyme_superhero_story.py
===================================================================================

A small standalone storyworld for a superhero cautionary rhyme about
correspondence: a young hero and a trusted helper exchange a note, a risky
mistake nearly exposes the city's secret map, and a careful response turns the
day around.

The world is intentionally narrow and classical:
- typed entities with meters and memes
- a causal simulation that drives the prose
- a reasonableness gate for compatible scenarios
- a lazy ASP twin for parity checks
- three Q&A sets grounded in the simulated world
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
SAFE_SCORE_MIN = 2

HEROES = ["Nova", "Comet", "Ruby", "Piper", "Milo", "Iris"]
_HELPERS = ["Kai", "Zara", "Nico", "Tess", "Leo", "Mina"]
PLACES = {
    "rooftop": {"sky", "wind"},
    "alley": {"shadows", "wind"},
    "library": {"quiet", "paper"},
}
MESSENGERS = {
    "paper_plane": {"id": "paper_plane", "label": "paper plane", "flight": "zip"},
    "mail_bat": {"id": "mail_bat", "label": "mail bat", "flight": "flap"},
    "pigeon": {"id": "pigeon", "label": "carrier pigeon", "flight": "flutter"},
}
THREATS = {
    "rain": {"id": "rain", "label": "rain cloud", "hurts": "paper", "risk": "soak"},
    "wind": {"id": "wind", "label": "wind gust", "hurts": "paper", "risk": "blow away"},
    "villain": {"id": "villain", "label": "night thief", "hurts": "secret", "risk": "steal"},
}
RESPONSES = {
    "tuck_away": {"id": "tuck_away", "sense": 3, "power": 3,
                  "text": "tucked the correspondence into a waterproof pouch",
                  "fail": "tucked the correspondence away, but not fast enough",
                  "qa": "tucked the correspondence into a waterproof pouch"},
    "signal_back": {"id": "signal_back", "sense": 3, "power": 4,
                    "text": "sent a bright signal and guided the helper home",
                    "fail": "sent a signal, but the danger was already too close",
                    "qa": "sent a bright signal and guided the helper home"},
    "shout_alert": {"id": "shout_alert", "sense": 2, "power": 4,
                    "text": "shouted for help and the whole block woke up",
                    "fail": "shouted for help, but the wind still carried the note off",
                    "qa": "shouted for help and the whole block woke up"},
    "water_bucket": {"id": "water_bucket", "sense": 1, "power": 1,
                     "text": "splashed a bucket of water on the paper",
                     "fail": "splashed water around, but it did not solve the problem",
                     "qa": "splashed a bucket of water on the paper"},
}
CAUTIOUS_TRAITS = {"careful", "cautious", "wise", "thoughtful"}
RHYME_ENDINGS = ["light", "night", "bright", "sight"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
class StoryParams:
    place: str
    messenger: str
    threat: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None
    delay: int = 0
    relation: str = "friends"
    trust: int = 6
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    note = world.get("note")
    if note.meters["exposed"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("city").meters["alarm"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("helper").memes["worry"] += 1
    note.meters["at_risk"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("spread", "risk", _r_spread)]


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


def cautious_gate(trait: str) -> bool:
    return trait in CAUTIOUS_TRAITS


def sensible_responses() -> list[str]:
    return [rid for rid, r in RESPONSES.items() if r["sense"] >= SAFE_SCORE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for messenger in MESSENGERS:
            for threat in THREATS:
                if messenger == "paper_plane" and threat == "wind":
                    combos.append((place, messenger, threat))
                elif messenger != "paper_plane" and threat in {"rain", "villain"}:
                    combos.append((place, messenger, threat))
    return combos


def choose_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def rhyme_line(end: str) -> str:
    return f"to keep the city safe through the {end}"


def predict_risk(world: World) -> dict:
    sim = world.copy()
    _r_spread(sim)
    return {
        "alarm": sim.get("city").meters["alarm"],
        "worry": sim.get("hero").memes["worry"],
    }


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender,
                            role="hero", traits=[params.trait]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender,
                              role="helper", traits=[params.trait]))
    city = world.add(Entity(id="city", kind="place", type="city", label="the city"))
    note = world.add(Entity(id="note", kind="thing", type="note", label="the correspondence"))
    messenger = world.add(Entity(id="messenger", kind="thing", type="messenger",
                                 label=MESSENGERS[params.messenger]["label"]))
    threat = world.add(Entity(id="threat", kind="thing", type="threat",
                              label=THREATS[params.threat]["label"]))

    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"On a windy day in {params.place}, {hero.id} and {helper.id} were the "
        f"city's smallest heroes. {hero.id} carried {note.label}, and {helper.id} "
        f"watched the rooftops for trouble."
    )
    world.say(
        f'"{hero.id}!" {helper.id} called. "Keep the {note.label} tucked tight and bright." '
        f"Their work had a rhyme: {rhyme_line(RHYME_ENDINGS[0])}."
    )

    world.para()
    world.say(
        f"But a {threat.label} rolled in, and the {messenger.label} had to cross the sky. "
        f"{hero.id} knew the note mattered because it held correspondence for the watch tower."
    )
    world.say(
        f"{helper.id} peered at the clouds. \"If that note gets wet, the message may be lost,\" "
        f"{helper.pronoun()} warned."
    )
    hero.memes["pride"] += 1
    helper.memes["caution"] += 1

    if params.threat == "wind":
        note.meters["exposed"] += 1
    elif params.threat == "rain":
        note.meters["exposed"] += 1
        note.meters["wet"] += 1
    else:
        note.meters["exposed"] += 1

    risk = predict_risk(world)
    world.facts["predicted_alarm"] = risk["alarm"]
    world.facts["predicted_worry"] = risk["worry"]

    if cautious_gate(params.trait) and params.trust >= 7 and params.relation == "friends":
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"{hero.id} listened, nodded, and chose the safer route at once. "
            f"No gust could snatch the note, and the two heroes kept their rhythm "
            f"{rhyme_line(RHYME_ENDINGS[1])}."
        )
        world.para()
        body = RESPONSES[params.response]["text"]
        world.say(
            f"In a flash, the pair {body}, then sent the message again with a steadier plan."
        )
        world.say(
            f"By evening, the correspondence reached the tower, dry and neat, "
            f"and the skyline shone {RHYME_ENDINGS[2]} and {RHYME_ENDINGS[0]}."
        )
        outcome = "avoided"
    else:
        world.say(
            f"{hero.id} took one more step toward the ledge, even though the warning rang clear."
        )
        note.meters["exposed"] += 1
        hero.memes["defiance"] += 1

        world.para()
        world.say(
            f"{params.messenger} zipped across the wind, but the threat grew sharp and the note began to slip."
        )
        world.say(
            f"Then {hero.id} shouted for the careful fix, because the correspondence could not be left to fly alone."
        )

        body = RESPONSES[params.response]["text"] if params.response in RESPONSES else RESPONSES["tuck_away"]["text"]
        if params.response not in RESPONSES:
            raise StoryError("(Unknown response.)")
        response = RESPONSES[params.response]
        if response["sense"] < SAFE_SCORE_MIN:
            raise StoryError(f"(Refusing response '{params.response}': too weak and unwise.)")
        if response["power"] >= 3:
            note.meters["exposed"] = 0.0
            note.meters["wet"] = 0.0
            world.say(f"{helper.id} came in fast and {body}.")
            world.say(
                f"The risky gust lost its grip, and the message stayed safe for the tower."
            )
            outcome = "contained"
        else:
            world.say(f"{helper.id} tried to help, but {response['fail']}.")
            world.say(
                f"The note tore loose and rode the wind, so the heroes had to chase it across the block."
            )
            outcome = "lost"

        world.para()
        world.say(
            f"Afterward, {helper.id} tied the correspondence with a ribbon and {rhyme_line(RHYME_ENDINGS[3])}."
        )
        world.say(
            f"{hero.id} nodded in the moonlit air. A careful hero learns: a message should not be left in the weather."
        )

    world.facts.update(
        hero=hero, helper=helper, city=city, note=note, messenger=messenger,
        threat=threat, params=params, outcome=outcome, response=params.response
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero cautionary rhyme that uses the word "correspondence" and shows a hero protecting a message from a {f["threat"].label}.',
        f"Tell a kid-friendly superhero story where {f['hero'].id} and {f['helper'].id} must keep correspondence safe while the weather turns risky.",
        f'Write a rhyming cautionary story about a secret message, a careful warning, and a bright rescue in the city.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    note = f["note"]
    threat = f["threat"]
    resp = RESPONSES[f["response"]]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, two small superheroes keeping the city's messages safe. They work together because the correspondence matters to the watch tower."),
        ("What was the correspondence?",
         f"It was a message that had to reach the tower without getting ruined. The heroes treated it carefully because a wet or lost note could cause real trouble."),
        ("Why did the helper warn the hero?",
         f"{helper.id} warned {hero.id} because the {threat.label} could ruin the correspondence. The warning mattered because the note was exposed to the weather and needed protection."),
    ]
    if world.facts["outcome"] in {"contained", "avoided"}:
        qa.append(
            ("How did they solve the problem?",
             f"They used a safer plan and kept the correspondence together instead of letting it drift in the wind. {helper.id} then {resp['qa']}, which matched the danger well enough to protect the message.")
        )
        qa.append(
            ("How did the story end?",
             f"It ended with the message safe and the city calm. The final image shows a neat, dry correspondence ready for the tower, which proves the heroes learned to be careful.")
        )
    else:
        qa.append(
            ("How did the story end?",
             f"It ended with the note getting away, so the heroes had to chase it. That ending is cautionary: when they were not careful enough, the correspondence was nearly lost.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"correspondence", f["response"]}
    if f["threat"].id == "rain":
        tags.add("rain")
    if f["threat"].id == "wind":
        tags.add("wind")
    out: list[tuple[str, str]] = []
    know = {
        "correspondence": [("What does correspondence mean?",
                            "Correspondence means letters, notes, or messages that people send to one another.")],
        "rain": [("Why can rain be a problem for paper?",
                  "Rain can soak paper, and wet paper may blur the words or tear apart.")],
        "wind": [("Why can wind make a note hard to keep?",
                 "Wind can snatch light paper away, so a note may flutter off before it reaches the right place.")],
        "tuck_away": [("Why use a waterproof pouch for a message?",
                       "A waterproof pouch helps keep paper dry when the weather turns rough.")],
        "signal_back": [("Why send a signal back?",
                         "A signal can help guide someone home or show that the message is being protected.")],
        "shout_alert": [("Why shout for help?",
                        "Shouting for help is a fast way to get other people to notice danger nearby.")],
    }
    order = ["correspondence", "rain", "wind", "tuck_away", "signal_back", "shout_alert"]
    for tag in order:
        if tag in tags:
            out.extend(know[tag])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this combination does not make a believable correspondence problem.)"


ASP_RULES = r"""
valid(P,M,T) :- place(P), messenger(M), threat(T), okay(P,M,T).
risk(note, exposed) :- note(N), exposed(N).
safe(response(R)) :- response(R), sense(R,S), min_sense(M), S >= M.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MESSENGERS:
        lines.append(asp.fact("messenger", m))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    for r, v in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, v["sense"]))
        lines.append(asp.fact("power", r, v["power"]))
    lines.append(asp.fact("min_sense", SAFE_SCORE_MIN))
    for p, allowed in PLACES.items():
        for w in allowed:
            lines.append(asp.fact("okay", p, w))
    lines.append(asp.fact("note", "note"))
    lines.append(asp.fact("exposed", "note"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show safe/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    sens_py = set(sensible_responses())
    sens_cl = set(asp_sensible())
    if sens_py == sens_cl:
        print(f"OK: sensible responses match ({sorted(sens_py)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_dict()
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAILED: generate() smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero cautionary rhyme about correspondence.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--messenger", choices=MESSENGERS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=["careful", "cautious", "wise", "thoughtful", "bold"])
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
    if args.response and RESPONSES[args.response]["sense"] < SAFE_SCORE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': too weak for this story.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.messenger is None or c[1] == args.messenger)
              and (args.threat is None or c[2] == args.threat)]
    if not combos:
        raise StoryError(explain_rejection(StoryParams(place="", messenger="", threat="", response="", hero="", hero_gender="", helper="", helper_gender="", trait="")))
    place, messenger, threat = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or choose_name(rng, HEROES)
    helper = args.helper or choose_name(rng, _HELPERS, avoid=hero)
    trait = args.trait or rng.choice(["careful", "cautious", "wise", "thoughtful", "bold"])
    return StoryParams(place=place, messenger=messenger, threat=threat, response=response,
                       hero=hero, hero_gender=hero_gender, helper=helper,
                       helper_gender=helper_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.messenger not in MESSENGERS or params.threat not in THREATS:
        raise StoryError("(Invalid story parameters.)")
    if params.response not in RESPONSES:
        raise StoryError("(Invalid response.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


CURATED = [
    StoryParams(place="rooftop", messenger="paper_plane", threat="wind", response="tuck_away",
                hero="Nova", hero_gender="girl", helper="Kai", helper_gender="boy", trait="careful"),
    StoryParams(place="library", messenger="pigeon", threat="rain", response="signal_back",
                hero="Ruby", hero_gender="girl", helper="Mina", helper_gender="girl", trait="wise"),
    StoryParams(place="alley", messenger="mail_bat", threat="villain", response="shout_alert",
                hero="Comet", hero_gender="boy", helper="Tess", helper_gender="girl", trait="cautious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for p, m, t in combos:
            print(f"  {p:8} {m:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
