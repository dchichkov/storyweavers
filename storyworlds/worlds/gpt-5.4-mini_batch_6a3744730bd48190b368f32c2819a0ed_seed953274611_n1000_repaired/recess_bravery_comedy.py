#!/usr/bin/env python3
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
    funny: bool = False
    brave: bool = False
    fragile: bool = False
    helps: bool = False
    loud: bool = False

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
class Setting:
    id: str
    place: str
    detail: str
    crowd: str
    sound: str
    afford: set[str] = field(default_factory=set)
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
class Plan:
    id: str
    goal: str
    wobble: str
    punchline: str
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
class Challenge:
    id: str
    label: str
    scene: str
    cause: str
    severity: int
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
    action: str
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


@dataclass
class StoryParams:
    setting: str
    plan: str
    challenge: str
    response: str
    hero: str
    helper: str
    adult: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _rule_confetti(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["brave"] >= THRESHOLD and e.memes["giggle"] >= THRESHOLD:
            sig = ("confetti", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["sparkle"] += 1
            out.append("__sparkle__")
    return out


def _rule_wiggle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["stuck"] < THRESHOLD:
            continue
        sig = ("wiggle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["panic"] += 1
        out.append("The stuck moment made everybody stare for one long silly second.")
    return out


CAUSAL_RULES: list[Rule] = []


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


CAUSAL_RULES = [
    Rule("wiggle", "social", _rule_wiggle),
    Rule("confetti", "social", _rule_confetti),
]


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


def reasonable(setting: Setting, plan: Plan, challenge: Challenge, response: Response) -> bool:
    return (
        setting.id in SETTINGS
        and plan.id in PLANS
        and challenge.id in CHALLENGES
        and response.id in RESPONSES
        and challenge.id in setting.afford
        and response.sense >= 2
    )


def resolve_bravery(hero: Entity, helper: Entity) -> bool:
    return hero.memes["brave"] + helper.memes["cheer"] >= 7.0


def challenge_pressure(challenge: Challenge) -> int:
    return challenge.severity


def can_fix(response: Response, challenge: Challenge) -> bool:
    return response.power >= challenge_pressure(challenge)


def predict(world: World, challenge: Challenge, response: Response, hero_id: str) -> dict:
    sim = world.copy()
    _challenge(sim, sim.get(hero_id), challenge, narrate=False)
    return {
        "stuck": sim.get(hero_id).meters["stuck"] >= THRESHOLD,
        "panic": sim.get(hero_id).memes["panic"],
        "sparkle": sim.get(hero_id).meters["sparkle"],
        "beats": response.power - challenge.severity,
    }


def _setup(world: World, hero: Entity, helper: Entity, setting: Setting, plan: Plan) -> None:
    hero.memes["brave"] += 2
    helper.memes["cheer"] += 2
    world.say(
        f"It was recess, and {hero.id} and {helper.id} turned {setting.place} into {setting.detail}. "
        f"{setting.crowd} {setting.sound} while they planned to {plan.goal}."
    )
    world.say(f'{hero.id} grinned. "{plan.goal}!" {helper.id} said, already laughing.')


def _tempt(world: World, hero: Entity, plan: Plan) -> None:
    hero.memes["giggle"] += 1
    world.say(
        f'{hero.id} wanted to try a brave stunt: {plan.wobble}. '
        f'It sounded heroic, even though it was also a tiny bit ridiculous.'
    )


def _warn(world: World, helper: Entity, hero: Entity, challenge: Challenge) -> None:
    helper.memes["cheer"] += 1
    world.say(
        f'{helper.id} blinked. "{challenge.cause}, and that could turn recess into a wobble-fest," '
        f"{helper.id} said."
    )


def _challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    hero.meters["stuck"] += 1
    hero.meters["flustered"] += 1
    hero.memes["panic"] += 1
    world.say(
        f"{challenge.scene} {challenge.cause}. {hero.id} froze for a second, then tried not to laugh at {hero.pronoun('object')}self."
    )
    propagate(world, narrate=narrate)


def _solve(world: World, adult: Entity, response: Response, hero: Entity, challenge: Challenge) -> None:
    hero.meters["stuck"] = 0
    hero.memes["panic"] = 0
    adult.memes["calm"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over, {response.action} until the problem was small enough to fit inside a shrug."
    )
    world.say(
        f"The silly trouble was gone, and {challenge.label} stopped bossing recess around."
    )


def _fail(world: World, adult: Entity, response: Response, hero: Entity, challenge: Challenge) -> None:
    world.say(
        f"{adult.label_word.capitalize()} tried to help, but {response.fail}."
    )
    world.say(
        f"So {challenge.label} kept the game in a knot while everyone hurried out of the tricky spot."
    )


def _ending(world: World, hero: Entity, helper: Entity, setting: Setting, plan: Plan) -> None:
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"In the end, {hero.id} and {helper.id} did {plan.punchline}. "
        f"They were still at recess, but now the whole thing felt like a joke they had beaten."
    )


def tell(setting: Setting, plan: Plan, challenge: Challenge, response: Response,
         hero_name: str = "Maya", hero_gender: str = "girl",
         helper_name: str = "Nico", helper_gender: str = "boy",
         adult_type: str = "teacher") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", brave=True))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    world.facts.update(setting=setting, plan=plan, challenge=challenge, response=response)
    _setup(world, hero, helper, setting, plan)
    world.para()
    _tempt(world, hero, plan)
    _warn(world, helper, hero, challenge)
    if resolve_bravery(hero, helper):
        world.say(f"{hero.id} took a breath and went ahead anyway, with a grin that was half courage and half comedy.")
        _challenge(world, hero, challenge)
        world.para()
        if can_fix(response, challenge):
            _solve(world, adult, response, hero, challenge)
            world.para()
            _ending(world, hero, helper, setting, plan)
            outcome = "fixed"
        else:
            _fail(world, adult, response, hero, challenge)
            world.say("The recess bell rang while everybody was still trying not to giggle at the mess.")
            outcome = "stuck"
    else:
        world.say(f"{helper.id} talked {hero.id} down before the silly stunt could even start.")
        world.say(f"They chose a safer joke instead, and recess stayed bright and easy.")
        outcome = "avoided"
    world.facts.update(hero=hero, helper=helper, adult=adult, outcome=outcome)
    return world


SETTINGS = {
    "playground": Setting(
        id="playground",
        place="the playground",
        detail="a pirate ship made of monkey bars",
        crowd="The swings creaked and the slide gleamed",
        sound="buzzed like busy bees",
        afford={"climb", "zipline", "balance"},
    ),
    "gym": Setting(
        id="gym",
        place="the gym",
        detail="a fort of cones and mats",
        crowd="Sneakers squeaked and balls boinged",
        sound="bounced with friendly echoes",
        afford={"balance", "dash"},
    ),
    "field": Setting(
        id="field",
        place="the field",
        detail="an enormous kingdom of chalk lines",
        crowd="Kids chased shadows and skipped circles",
        sound="hummed with happy yelling",
        afford={"dash", "race"},
    ),
}

PLANS = {
    "high_jump": Plan(id="high_jump", goal="be the bravest bird", wobble="jump from the bottom bar like a superhero", punchline="made a dramatic bow", risk="bars", tags={"bravery", "comedy"}),
    "cone_tower": Plan(id="cone_tower", goal="build the tallest silly tower", wobble="stack cones while standing on one toe", punchline="saluted the tower", risk="cones", tags={"bravery", "comedy"}),
    "shadow_race": Plan(id="shadow_race", goal="race our own shadows", wobble="sprint backwards while keeping a straight face", punchline="won by tripping over nothing at all", risk="shadows", tags={"bravery", "comedy"}),
}

CHALLENGES = {
    "zip_tangle": Challenge(id="zip_tangle", label="the zip-tangle", scene="At the monkey bars, ", cause="the zipper of the new cape hooked onto the bar", severity=2, tags={"playground"}),
    "shoelace": Challenge(id="shoelace", label="the shoelace knot", scene="On the gym floor, ", cause="one shoelace decided to tie itself into a joke", severity=3, tags={"gym"}),
    "chalk_line": Challenge(id="chalk_line", label="the chalk line", scene="By the field line, ", cause="the chalk line was so slippery-looking that it felt like it was winking", severity=2, tags={"field"}),
}

RESPONSES = {
    "laugh_and_lift": Response(id="laugh_and_lift", sense=3, power=3, action="laughed, then lifted the cape free", fail="the cape stayed stuck for one more very silly moment", qa_text="laughed, then lifted the cape free", tags={"fix"}),
    "knot_untie": Response(id="knot_untie", sense=3, power=3, action="knelt down and untied the knot with two quick fingers", fail="the knot behaved like a stubborn pretzel", qa_text="knelt down and untied the knot", tags={"fix"}),
    "chalk_wipe": Response(id="chalk_wipe", sense=2, power=2, action="wiped away the chalk and turned the line back into a line", fail="the chalk only smeared into a bigger joke", qa_text="wiped away the chalk", tags={"fix"}),
    "paper_fan": Response(id="paper_fan", sense=1, power=1, action="waved a paper fan", fail="that was about as useful as a sandwich in a rainstorm", qa_text="waved a paper fan", tags={"bad"}),
}

GIRL_NAMES = ["Maya", "Nina", "Lila", "Ruby", "Zoe", "Ivy"]
BOY_NAMES = ["Nico", "Owen", "Theo", "Jasper", "Ben", "Leo"]
TRAITS = ["bold", "cheerful", "quick", "silly", "curious"]

KNOWLEDGE = {
    "recess": [("What is recess?", "Recess is a break at school when kids can run around, play, and rest their brains for a little while.")],
    "bravery": [("What is bravery?", "Bravery means doing something hard or scary even when your knees feel a little wobbly.")],
    "comedy": [("What makes a story funny?", "A funny story often has surprises, silly mistakes, or characters who bounce back with a smile.")],
    "monkey_bars": [("What are monkey bars?", "Monkey bars are playground bars you can swing across with your hands.")],
    "slip": [("Why do people slip?", "People slip when a floor or surface is smooth, wet, or hard to grip.")],
    "adult_help": [("Why ask an adult for help?", "Adults can help safely when a problem is too tricky, too high, or too stuck.")],
    "laugh": [("Why is laughing helpful?", "Laughing can make a stressful moment feel smaller and help people stay calm together.")],
}
KNOWLEDGE_ORDER = ["recess", "bravery", "comedy", "monkey_bars", "slip", "adult_help", "laugh"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PLANS:
            for c in CHALLENGES:
                for r in RESPONSES:
                    if reasonable(SETTINGS[s], PLANS[p], CHALLENGES[c], RESPONSES[r]):
                        out.append((s, p, c, r))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: recess bravery comedy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--adult", choices=["teacher", "coach", "parent"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.plan is None or c[1] == args.plan)
              and (args.challenge is None or c[2] == args.challenge)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, p, c, r = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    adult = args.adult or rng.choice(["teacher", "coach", "parent"])
    return StoryParams(setting=s, plan=p, challenge=c, response=r, hero=hero, helper=helper, adult=adult)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, p, c = f["setting"], f["plan"], f["challenge"]
    return [
        f'Write a funny recess story for a child where bravery helps two kids deal with "{c.label}".',
        f"Tell a comedy story about recess at {s.place} where {f['hero'].id} tries to {p.wobble} but a silly snag appears.",
        f'Write a short story that includes the word "recess" and ends with brave kids laughing after a problem is solved.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, adult = f["hero"], f["helper"], f["adult"]
    setting, plan, challenge, response = f["setting"], f["plan"], f["challenge"], f["response"]
    qa = [
        ("Where does the story happen?", f"It happens at {setting.place} during recess. The whole scene is built around kids having a break and trying something funny."),
        ("What did the hero want to do?", f"{hero.id} wanted to {plan.wobble}. That was the brave, silly idea that started the comedy."),
        ("What went wrong?", f"{challenge.cause}. It turned the brave plan into a stuck moment for a second."),
    ]
    if f["outcome"] == "fixed":
        qa.append(("How was the problem solved?", f"{adult.label_word.capitalize()} {response.qa_text}. That fixed the trouble and let the kids keep playing." ))
        qa.append(("How did the ending feel?", f"The ending felt proud and funny, because {hero.id} and {helper.id} turned a problem into a joke they could laugh about." ))
    elif f["outcome"] == "avoided":
        qa.append(("How was the problem avoided?", f"{helper.id} helped {hero.id} back away before the stunt started, so recess stayed safe and silly without any mess." ))
    else:
        qa.append(("How did the story end?", f"The problem stayed stuck for a while, and the story ended with the kids hurrying away while trying not to laugh at how odd it all was." ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = {"recess", "bravery", "comedy", "adult_help", "laugh"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="playground", plan="high_jump", challenge="zip_tangle", response="laugh_and_lift", hero="Maya", helper="Nico", adult="teacher"),
    StoryParams(setting="gym", plan="cone_tower", challenge="shoelace", response="knot_untie", hero="Nina", helper="Leo", adult="coach"),
    StoryParams(setting="field", plan="shadow_race", challenge="chalk_line", response="chalk_wipe", hero="Owen", helper="Ivy", adult="parent"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < 2).)"


def outcome_of(params: StoryParams) -> str:
    if not resolve_bravery(Entity(id="h"), Entity(id="k")):
        return "avoided"
    return "fixed" if can_fix(RESPONSES[params.response], CHALLENGES[params.challenge]) else "stuck"


ASP_RULES = r"""
valid(S,P,C,R) :- setting(S), plan(P), challenge(C), response(R),
                  afford(S,C), sense(R,SR), SR >= 2.
outcome(fixed) :- chosen_response(R), chosen_challenge(C), power(R,PR), severity(C,SV), PR >= SV.
outcome(stuck) :- chosen_response(R), chosen_challenge(C), power(R,PR), severity(C,SV), PR < SV.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s, v in SETTINGS.items():
        lines.append(asp.fact("setting", s))
        for a in v.afford:
            lines.append(asp.fact("afford", s, a))
    for p, v in PLANS.items():
        lines.append(asp.fact("plan", p))
    for c, v in CHALLENGES.items():
        lines.append(asp.fact("challenge", c))
        lines.append(asp.fact("severity", c, v.severity))
    for r, v in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, v.sense))
        lines.append(asp.fact("power", r, v.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("MISMATCH: ordinary generation failed.")
        rc = 1
    print("OK: verification ran.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("plan", PLANS), ("challenge", CHALLENGES), ("response", RESPONSES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(SETTINGS[params.setting], PLANS[params.plan], CHALLENGES[params.challenge], RESPONSES[params.response], params.hero, "girl" if params.hero in GIRL_NAMES else "boy", params.helper, "girl" if params.helper in GIRL_NAMES else "boy", params.adult)
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
