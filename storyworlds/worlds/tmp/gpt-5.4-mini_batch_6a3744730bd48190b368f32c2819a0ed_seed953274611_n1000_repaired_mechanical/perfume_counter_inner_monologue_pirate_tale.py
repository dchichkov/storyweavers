#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perfume_counter_inner_monologue_pirate_tale.py
==============================================================================

A tiny storyworld with a pirate-tale feel, built from the seed words
"perfume" and "counter" and featuring inner monologue.

Premise:
- A child in pretend pirate mode spots a bottle of perfume on a counter.
- The child wants to use it as "treasure scent" for a pirate game.
- A careful helper warns that perfume is not a toy and can be too strong.
- The child chooses a safer pretend treasure instead, or, in one curated
  branch, spills a little and cleans it up with help.

The world model drives the prose through state changes:
- physical meters: scent, spill, wetness, clutter
- emotional memes: excitement, worry, pride, relief

The script supports text, JSON, QA, trace, a Python reasonableness gate,
and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    location: str
    dangerous: bool = False
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


@dataclass
class SettingCfg:
    id: str
    scene: str
    detail: str
    pirate_words: str
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
    setting: str
    perfume: str
    counter: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
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
        return clone


def hazard_at_risk(perfume: ItemCfg, counter: ItemCfg) -> bool:
    return perfume.dangerous and counter.dangerous


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def story_outcome(params: StoryParams) -> str:
    return "contained" if RESPONSES[params.response].power >= 1 else "scattered"


def _spilled(world: World) -> None:
    perfume = world.get("perfume")
    counter = world.get("counter")
    perfume.meters["spill"] += 1
    perfume.meters["scent"] += 1
    counter.meters["wet"] += 1
    counter.meters["clutter"] += 1
    world.get("room").meters["scent"] += 1
    for eid in ("hero", "helper"):
        world.get(eid).memes["worry"] += 1


def predict_spill(world: World) -> dict:
    sim = world.copy()
    _spilled(sim)
    return {
        "spilled": sim.get("perfume").meters["spill"] >= THRESHOLD,
        "wet": sim.get("counter").meters["wet"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity, helper: Entity, setting: SettingCfg) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a blustery afternoon, {hero.id} and {helper.id} played pirates in "
        f"{setting.scene}. {setting.detail}"
    )
    world.say(
        f'"{setting.pirate_words}," {hero.id} thought. '
        f'"This ship needs a proper treasure smell."'
    )


def notice(world: World, hero: Entity, perfume: ItemCfg, counter: ItemCfg) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"{hero.id} spotted {perfume.phrase} on the {counter.label}. "
        f"'{hero.id} wondered if one tiny spritz could make the whole cabin feel "
        f"like a pirate ship.'"
    )


def warn(world: World, helper: Entity, hero: Entity, perfume: ItemCfg) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} leaned closer and said, 'Careful. {perfume.label_word if hasattr(perfume, 'label_word') else perfume.label} is not a toy.'"
    )


def choose_safe(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["pride"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} listened to the warning and took a slow breath. "
        f"'{hero.id} thought, I can still have treasure without making a mess.'"
    )
    world.say(
        f"They found a shiny coin, a strip of paper flag, and a wooden spoon to "
        f"be the captain's spoon. The pirate game kept sailing."
    )


def spill_and_fix(world: World, adult: Entity, response: Response, perfume: ItemCfg, counter: ItemCfg) -> None:
    _spilled(world)
    world.say(
        f"{hero_name(world)} nudged the bottle, and a little perfume splashed "
        f"across the {counter.label}. The air turned sweet and sharp at once."
    )
    if response.power >= 1:
        body = response.text.replace("{counter}", counter.label)
        world.say(f"{adult.label_word.capitalize()} came at once and {body}.")
        world.say(
            "The counter was wiped clean, the bottle was moved far from little hands, "
            "and the pirate ship smelled safe again."
        )
    else:
        body = response.fail.replace("{counter}", counter.label)
        world.say(f"{adult.label_word.capitalize()} came, but {body}.")
        world.say("The room stayed too perfumed and the pirate crew had to open a window.")


def hero_name(world: World) -> str:
    return world.facts["hero"].id


def ending(world: World, setting: SettingCfg, outcome: str) -> None:
    if outcome == "contained":
        world.say(
            f"In the end, the little ship sailed on with no perfume on the {setting.id}. "
            f"Just a tidy counter, a brave child, and a safer treasure game."
        )
    else:
        world.say(
            f"In the end, the perfume stayed off the {setting.id}, and the crew "
            f"remembered to keep bottles away from the counter's edge."
        )


def tell(setting: SettingCfg, perfume: ItemCfg, counter: ItemCfg, response: Response,
         hero_name_value: str, hero_gender: str, helper_name: str, helper_gender: str,
         adult_name: str, adult_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name_value, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the adult"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="perfume", type="item", label=perfume.label))
    world.add(Entity(id="counter", type="item", label=counter.label))
    world.facts.update(hero=hero, helper=helper, adult=adult, room=room, setting=setting,
                       perfume=perfume, counter=counter, response=response)

    intro(world, hero, helper, setting)
    world.para()
    notice(world, hero, perfume, counter)
    warn(world, helper, hero, perfume)

    if perfume.id == "safe_choice":
        choose_safe(world, hero, helper)
        outcome = "contained"
    else:
        if predict_spill(world)["spilled"]:
            world.para()
            spill_and_fix(world, adult, response, perfume, counter)
            outcome = "contained" if response.power >= 1 else "scattered"
        else:
            choose_safe(world, hero, helper)
            outcome = "contained"

    world.para()
    ending(world, setting, outcome)
    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "harbor": SettingCfg(
        id="harbor",
        scene="a cardboard harbor with a sail made from an old napkin",
        detail="A cracked mug became the captain's lookout, and the table felt like a dock.",
        pirate_words="Arrr, the tide is in!",
    ),
    "cabin": SettingCfg(
        id="cabin",
        scene="a tiny ship cabin under a blanket fort",
        detail="The blankets hung low like cloudy sails, and every whisper sounded secret.",
        pirate_words="Shiver me timbers, this cabin needs treasure!",
    ),
}

PERFUMES = {
    "rose": ItemCfg(id="rose", label="perfume", phrase="a little bottle of rose perfume", location="on the counter", dangerous=True, tags={"perfume", "scent"}),
    "citrus": ItemCfg(id="citrus", label="perfume", phrase="a tiny bottle of citrus perfume", location="on the counter", dangerous=True, tags={"perfume", "scent"}),
    "safe_choice": ItemCfg(id="safe_choice", label="perfume", phrase="a pretend perfume bottle made from a shiny toy cup", location="on the counter", dangerous=False, tags={"perfume"}),
}

COUNTERS = {
    "kitchen": ItemCfg(id="kitchen", label="counter", phrase="the kitchen counter", location="on the counter", dangerous=True, tags={"counter"}),
    "ship_counter": ItemCfg(id="ship_counter", label="counter", phrase="the ship's counter", location="on the counter", dangerous=True, tags={"counter"}),
}

RESPONSES = {
    "wipe": Response(
        id="wipe",
        sense=3,
        power=1,
        text="wiped the counter with a damp cloth and moved the bottle to a high shelf",
        fail="wiped quickly, but the smell still clung to the counter",
        qa_text="wiped the counter with a damp cloth and moved the bottle to a high shelf",
        tags={"clean", "help"},
    ),
    "open_window": Response(
        id="open_window",
        sense=3,
        power=1,
        text="opened the window, wiped the spill, and let the breeze carry the scent away",
        fail="opened the window, but the scent still hung in the air",
        qa_text="opened the window and let the breeze carry the scent away",
        tags={"clean", "help"},
    ),
    "ignore": Response(
        id="ignore",
        sense=1,
        power=0,
        text="tried to shrug it off, but that did not help at all",
        fail="shrugged it off and hoped the smell would go away",
        qa_text="shrugged it off",
        tags={"bad"},
    ),
}

GIRL_NAMES = ["Lily", "Mira", "Zoe", "Tessa"]
BOY_NAMES = ["Tom", "Milo", "Nate", "Finn"]
TRAITS = ["curious", "careful", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PERFUMES:
            for c in COUNTERS:
                if hazard_at_risk(PERFUMES[p], COUNTERS[c]):
                    out.append((s, p, c))
    return out


def explain_rejection(perfume: ItemCfg, counter: ItemCfg) -> str:
    return f"(No story: this counter/perfume pair does not make a useful pirate problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low; pick a safer help action.)"


ASP_RULES = r"""
hazard(P, C) :- dangerous_perfume(P), dangerous_counter(C).
valid(S, P, C) :- setting(S), perfume(P), counter(C), hazard(P, C).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, cfg in PERFUMES.items():
        lines.append(asp.fact("perfume", p))
        if cfg.dangerous:
            lines.append(asp.fact("dangerous_perfume", p))
    for c, cfg in COUNTERS.items():
        lines.append(asp.fact("counter", c))
        if cfg.dangerous:
            lines.append(asp.fact("dangerous_counter", c))
    for r, cfg in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, cfg.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {r for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, perfume=None, counter=None, response=None, hero=None, helper=None, adult=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale perfume/counter story world with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--perfume", choices=PERFUMES)
    ap.add_argument("--counter", choices=COUNTERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if args.perfume and args.counter:
        if not hazard_at_risk(PERFUMES[args.perfume], COUNTERS[args.counter]):
            raise StoryError(explain_rejection(PERFUMES[args.perfume], COUNTERS[args.counter]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(list(SETTINGS))
    perfume = args.perfume or rng.choice(list(PERFUMES))
    counter = args.counter or rng.choice(list(COUNTERS))
    if not hazard_at_risk(PERFUMES[perfume], COUNTERS[counter]):
        perfume = "rose"
        counter = "kitchen"
    response = args.response or rng.choice([r for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    adult = args.adult or ("Mum" if adult_gender == "mother" else "Dad")
    return StoryParams(setting=setting, perfume=perfume, counter=counter, response=response,
                       hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender,
                       adult=adult, adult_gender=adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale story for a young child that includes the words "perfume" and "counter".',
        f"Tell a story where {f['hero'].id} thinks about perfume on the counter, then listens to a careful helper.",
        f"Write a gentle inner-monologue pirate adventure with a safe ending and a little smell-related mishap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, adult = f["hero"], f["helper"], f["adult"]
    perfume, counter = f["perfume"], f["counter"]
    out = [
        QAItem(
            question=f"What did {hero.id} notice on the {counter.label}?",
            answer=f"{hero.id} noticed {perfume.phrase} on the {counter.label}. The bottle looked tempting, but it was also something to be careful with."
        ),
        QAItem(
            question=f"What did {helper.id} say about the perfume?",
            answer=f"{helper.id} warned that the perfume was not a toy. That warning helped {hero.id} pause and think before acting."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended safely, with the counter tidy and the pirate game still going. The child chose a safer treasure idea instead of making a mess."
        ),
    ]
    if f["outcome"] == "scattered":
        out.append(QAItem(
            question=f"Why did {adult.label_word if hasattr(adult, 'label_word') else adult.id} come in?",
            answer=f"{adult.id} came in because the perfume had spilled and the counter was wet and strong-smelling. The grown-up cleaned it up so the room could be safe again."
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is perfume?",
            answer="Perfume is a strong-smelling liquid that people use to smell nice. It is not a toy, and little children should not play with it."
        ),
        QAItem(
            question="What is a counter?",
            answer="A counter is a flat surface in a kitchen or shop where people set things down. Bottles should stay back from the edge so they do not fall."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)],
             "", "== (2) Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines += ["", "== (3) World knowledge =="]
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="harbor", perfume="rose", counter="kitchen", response="wipe",
                hero="Lily", hero_gender="girl", helper="Tom", helper_gender="boy",
                adult="Mum", adult_gender="mother"),
    StoryParams(setting="cabin", perfume="citrus", counter="ship_counter", response="open_window",
                hero="Finn", hero_gender="boy", helper="Mira", helper_gender="girl",
                adult="Dad", adult_gender="father"),
]


def generate(params: StoryParams) -> StorySample:
    if params.perfume not in PERFUMES or params.counter not in COUNTERS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    setting = SETTINGS[params.setting]
    perfume = PERFUMES[params.perfume]
    counter = COUNTERS[params.counter]
    response = RESPONSES[params.response]
    if not hazard_at_risk(perfume, counter):
        raise StoryError(explain_rejection(perfume, counter))
    world = tell(setting, perfume, counter, response, params.hero, params.hero_gender,
                 params.helper, params.helper_gender, params.adult, params.adult_gender)
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for s, p, c in asp_valid_combos():
            print(s, p, c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
