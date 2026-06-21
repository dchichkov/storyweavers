#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fanny_cancer_foreshadowing_inner_monologue_pirate_tale.py
==========================================================================================

A standalone storyworld for a small pirate tale with foreshadowing and inner
monologue.

Premise:
- Fanny is a young pirate on a little ship.
- The crew is chasing a bright island at dusk.
- A strange sign in the sky, Cancer the crab constellation, hints that weather
  is changing.
- Fanny listens to her own thoughts, notices the omen, and helps the crew make a
  safer choice before the sea turns rough.

The world model uses typed entities with physical meters and emotional memes.
The story is not a frozen paragraph: the rendered prose comes from evolving
world state.

This file follows the Storyweavers contract:
- stdlib-only
- imports results eagerly
- imports asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
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
FORESHADOW_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    sky_note: str
    wind: str
    sea_color: str
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
class Omen:
    id: str
    sign: str
    creature: str
    phrase: str
    warning: str
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
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, traits=list(v.traits),
            role=v.role, attrs=dict(v.attrs), meters=defaultdict(float, v.meters),
            memes=defaultdict(float, v.memes),
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_storm(world: World) -> list[str]:
    out: list[str] = []
    sea = world.get("sea")
    for e in list(world.entities.values()):
        if e.meters["storm"] < THRESHOLD:
            continue
        sig = ("storm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        sea.meters["rough"] += 1
        for kid in list(world.entities.values()):
            if kid.role in {"captain", "mate"}:
                kid.memes["worry"] += 1
        out.append("__storm__")
    return out


def _r_reef(world: World) -> list[str]:
    ship = world.get("ship")
    reef = world.get("reef")
    if ship.meters["drift"] >= THRESHOLD and reef.meters["near"] >= THRESHOLD:
        sig = ("reef",)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["scraped"] += 1
            reef.meters["scraped"] += 1
            return ["__reef__"]
    return []


CAUSAL_RULES = [Rule("storm", "weather", _r_storm), Rule("reef", "navigation", _r_reef)]


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


def omen_gathering(setting: Setting, omen: Omen) -> bool:
    return "sky" in setting.tags and omen.id == "cancer"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def storm_strength(delay: int) -> int:
    return 1 + delay


def can_avoid_storm(delay: int, response: Response) -> bool:
    return response.power >= storm_strength(delay)


def predict_storm(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.get("sea").meters["storm"] += storm_strength(delay)
    propagate(sim, narrate=False)
    return {
        "rough": sim.get("sea").meters["rough"],
        "reef": sim.get("ship").meters["scraped"] >= THRESHOLD,
    }


def setup(world: World, fanny: Entity, mate: Entity, setting: Setting) -> None:
    fanny.memes["curiosity"] += 1
    mate.memes["calm"] += 1
    world.say(
        f"At {setting.place}, {fanny.id} and {mate.id} climbed aboard the little ship. "
        f"{setting.scene}"
    )
    world.say(
        f"{fanny.id} leaned on the rail and watched the water. {setting.sky_note} "
        f"The sea looked {setting.sea_color}, and the wind felt {setting.wind}."
    )


def voyage_goal(world: World, fanny: Entity, omen: Omen) -> None:
    world.say(
        f'"We can still reach the bright island before dark," {fanny.id} thought, '
        f"though the sky already felt a little strange."
    )
    fanny.memes["hope"] += 1
    world.say(
        f"In her head, {fanny.id} counted the sails and told herself the day was '
        f"only getting interesting."
    )


def foreshadow(world: World, mate: Entity, omen: Omen) -> None:
    mate.memes["worry"] += 1
    world.facts["omen_seen"] = omen.id
    world.say(
        f"Then {mate.id} pointed up. {omen.phrase} {omen.warning}"
    )
    world.say(
        f"{mate.id} whispered that old sailors watched {omen.creature} signs when "
        f"the sea wanted to change its mind."
    )


def inner_monologue(world: World, fanny: Entity, omen: Omen, response: Response, delay: int) -> None:
    fanny.memes["doubt"] += 1
    pred = predict_storm(world, delay)
    world.facts["predicted_rough"] = pred["rough"]
    world.facts["predicted_reef"] = pred["reef"]
    world.say(
        f"{fanny.id} looked up again and thought, "
        f'"If {omen.sign} is hanging there, maybe the water is warning us. '
        f"If we keep pushing the ship forward, the night could turn mean."'
    )
    world.say(
        f'"Maybe we should use {response.id.replace("_", " ")}," she thought. '
        f'"A smart pirate does not race a storm just to be brave."'
    )


def decide(world: World, fanny: Entity, mate: Entity, response: Response, delay: int) -> bool:
    if can_avoid_storm(delay, response):
        fanny.memes["courage"] += 1
        world.say(
            f'{fanny.id} took a breath and said, "Let us turn the ship now, before '
            f"the clouds get heavy."'
        )
        return True
    fanny.memes["stubborn"] += 1
    world.say(
        f'{fanny.id} shook her head. "We can beat it," she said, and kept the bow '
        f"pointed at the dark water."
    )
    return False


def heed_and_turn(world: World, fanny: Entity, mate: Entity, response: Response) -> None:
    world.get("ship").meters["drift"] = 0
    world.get("sea").meters["storm"] = 0
    fanny.memes["relief"] += 1
    mate.memes["relief"] += 1
    body = response.text
    world.say(
        f"{mate.id} nodded, and together they {body}."
    )
    world.say(
        f"The ship slid away from the worst of the clouds, and the bright island "
        f"stayed safely on the horizon."
    )


def storm_breaks(world: World, fanny: Entity, mate: Entity, response: Response) -> None:
    world.get("sea").meters["storm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A gust hit like a slap. Rain raked the deck, and the mast groaned."
    )
    world.say(
        f"{fanny.id} heard herself say, 'No, no, no,' even as the ship lurched."
    )
    world.say(
        f"{mate.id} tried to help, but the sea was already angry and the bow had gone the wrong way."
    )
    if response.power < storm_strength(1):
        world.say(
            f"{response.fail.replace('{target}', 'the storm')}. The little ship had to "
            f"fight every wave."
        )


def safe_end(world: World, fanny: Entity, mate: Entity) -> None:
    world.say(
        f"By morning the clouds had broken apart. {fanny.id} and {mate.id} found "
        f"the calm water again, and the ship smelled of salt instead of fear."
    )
    world.say(
        f"Above them, {world.facts['omen_seen']} had faded into daylight, but "
        f"{fanny.id} kept the lesson close: some warnings are worth listening to."
    )


def storm_loss(world: World, fanny: Entity, mate: Entity) -> None:
    world.say(
        f"By the time the storm tired itself out, the deck was soaked and the map "
        f"had curled at the edges."
    )
    world.say(
        f"{fanny.id} still helped {mate.id} tie the loose lines, and in her heart "
        f"she promised not to ignore the sky next time."
    )


def tell(setting: Setting, omen: Omen, response: Response,
         fanny_name: str = "Fanny", mate_name: str = "Matey",
         delay: int = 0) -> World:
    world = World()
    fanny = world.add(Entity(id=fanny_name, kind="character", type="girl", role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type="boy", role="mate"))
    world.add(Entity(id="ship", type="ship", label="the ship"))
    world.add(Entity(id="sea", type="sea", label="the sea"))
    reef = world.add(Entity(id="reef", type="reef", label="the reef"))
    reef.meters["near"] += 1

    setup(world, fanny, mate, setting)
    world.para()
    voyage_goal(world, fanny, omen)
    foreshadow(world, mate, omen)
    inner_monologue(world, fanny, omen, response, delay)

    world.para()
    turned = decide(world, fanny, mate, response, delay)
    if turned:
        heed_and_turn(world, fanny, mate, response)
        safe_end(world, fanny, mate)
        outcome = "safe"
    else:
        storm_breaks(world, fanny, mate, response)
        if can_avoid_storm(delay, response):
            outcome = "safe"
            safe_end(world, fanny, mate)
        else:
            outcome = "rough"
            storm_loss(world, fanny, mate)

    world.facts.update(
        fanny=fanny, mate=mate, setting=setting, omen=omen, response=response,
        delay=delay, outcome=outcome, cautious=turned,
    )
    return world


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the moonlit harbor",
        scene="Their tiny sloop rocked beside the pier, with a lantern, a map, and a brass compass on the bench.",
        sky_note="The clouds had little silver edges, but one patch of sky was already darkening.",
        wind="cool and prickly",
        sea_color="blue-black",
        tags={"sky", "sea"},
    ),
    "island": Setting(
        id="island",
        place="the hidden island",
        scene="Their little cutter waited under a crooked palm, and the crew had packed rope, biscuits, and a bright red flag.",
        sky_note="The sunset glowed gold behind the palms, but one dark curl of cloud was sliding in from the east.",
        wind="warm at first, then sharp",
        sea_color="green and glassy",
        tags={"sky", "sea"},
    ),
}

OMENS = {
    "cancer": Omen(
        id="cancer",
        sign="Cancer",
        creature="the crab",
        phrase="Above the mast, the stars had gathered into the shape of Cancer, the crab.",
        warning="Its little claws seemed to pinch the edge of the night, as if saying, 'Turn back, little ship.'",
        tags={"foreshadowing"},
    ),
    "cloudbank": Omen(
        id="cloudbank",
        sign="cloudbank",
        creature="the cloud",
        phrase="Far out over the water, a dark cloudbank rose like a wall.",
        warning="It looked soft from far away, but the middle of it was black as ink.",
        tags={"foreshadowing"},
    ),
}

RESPONSES = {
    "reef_turn": Response(
        id="reef turn",
        sense=3,
        power=3,
        text="turned the wheel hard and let the sail catch a kinder wind",
        fail="tried to turn too late",
        qa_text="turned the wheel hard and let the sail catch a kinder wind",
        tags={"safe"},
    ),
    "drop_sail": Response(
        id="drop the sail",
        sense=3,
        power=2,
        text="dropped the sail and waited out the worst of it",
        fail="dropped the sail, but the waves still caught them",
        qa_text="dropped the sail and waited out the worst of it",
        tags={"safe"},
    ),
    "full_speed": Response(
        id="full speed",
        sense=1,
        power=0,
        text="kept pushing forward",
        fail="kept pushing forward, but the sea did not care",
        qa_text="kept pushing forward",
        tags={"risky"},
    ),
}

GIRL_NAMES = ["Fanny", "Mara", "Nell", "Ivy", "Tess"]
BOY_NAMES = ["Rook", "Pip", "Jory", "Finn", "Ben"]

@dataclass
class StoryParams:
    setting: str
    omen: str
    response: str
    fanny: str = "Fanny"
    mate: str = "Matey"
    delay: int = 0
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


CURATED = [
    StoryParams(setting="harbor", omen="cancer", response="reef_turn", fanny="Fanny", mate="Pip", delay=0),
    StoryParams(setting="island", omen="cloudbank", response="drop_sail", fanny="Fanny", mate="Rook", delay=1),
    StoryParams(setting="harbor", omen="cancer", response="full_speed", fanny="Fanny", mate="Ben", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for oid in OMENS:
            for rid, resp in RESPONSES.items():
                if rid != "full_speed" or resp.sense >= 2:
                    out.append((sid, oid, rid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a child where {f["fanny"].id} notices an omen in the sky and thinks to herself before choosing what to do.',
        f'Tell a story that includes the word "{f["omen"].sign}" and shows a brave pirate listening to her inner monologue instead of rushing ahead.',
        f'Write a foreshadowing story where a little ship sees {f["omen"].sign}, changes course, and ends safely at sea.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    fanny: Entity = f["fanny"]
    mate: Entity = f["mate"]
    omen: Omen = f["omen"]
    response: Response = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {fanny.id}, a young pirate who sailed with {mate.id}. The story follows what she notices and how she decides what to do."),
        ("What warning did they see in the sky?",
         f"They saw {omen.sign} above the mast, and it looked like a sign that the weather could change. That made the coming storm feel possible before it actually arrived."),
        ("What was Fanny thinking to herself?",
         f"She thought that a smart pirate should not race a storm just to seem brave. Her inner monologue helped her slow down and choose a safer plan."),
    ]
    if f["outcome"] == "safe":
        qa.append((
            "How did the story end?",
            f"It ended safely because {fanny.id} listened to the warning and {response.qa_text}. The ship stayed away from the worst water and the bright island remained ahead, not lost."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with rough weather because {fanny.id} ignored the warning and kept going. Even so, the crew stayed together and the ship did not sink."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["omen"].tags) | set(f["response"].tags)
    if f["outcome"] == "safe":
        tags.add("foreshadowing")
    out: list[tuple[str, str]] = []
    if "foreshadowing" in tags:
        out.append(("What is foreshadowing?",
                     "Foreshadowing is when a story gives a small hint about what may happen later. It helps the reader feel the change coming before it arrives."))
    out.append(("What is a pirate tale?",
                 "A pirate tale is a story about ships, the sea, and crew members having an adventure. It often includes maps, storms, and a daring choice."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe(S,R) :- response(R), sense(R, Sx), sense_min(M), Sx >= M.
omen_seen(cancer) :- omen(cancer).
outcome(safe) :- chosen_response(R), response(R), sense(R, S), S >= 2.
outcome(rough) :- chosen_response(R), response(R), sense(R, S), S < 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OMENS:
        lines.append(asp.fact("omen", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show safe/2."))
    return sorted(set(asp.atoms(model, "safe")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    program = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("setting", params.setting),
        asp.fact("omen", params.omen),
    ])
    model = asp.one_model(asp_program(program, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    try:
        if set(asp_valid_combos()) != {(s, r) for s, _, r in valid_combos() if RESPONSES[r].sense >= 2}:
            print("MISMATCH in ASP gate.")
            rc = 1
        else:
            print("OK: ASP gate matches Python gate.")
    except Exception as exc:
        print(f"ASP verify failed: {exc}")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, omen=None, response=None, fanny=None, mate=None, delay=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with foreshadowing and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--fanny")
    ap.add_argument("--mate")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    combos = [(s, o, r) for s, o, r in valid_combos()
              if (args.setting is None or s == args.setting)
              and (args.omen is None or o == args.omen)
              and (args.response is None or r == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, omen, response = rng.choice(sorted(combos))
    fanny = args.fanny or rng.choice(GIRL_NAMES)
    mate = args.mate or rng.choice(BOY_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting=setting, omen=omen, response=response, fanny=fanny, mate=mate, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.omen not in OMENS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    setting = SETTINGS[params.setting]
    omen = OMENS[params.omen]
    response = RESPONSES[params.response]
    world = World()
    fanny = world.add(Entity(id=params.fanny, kind="character", type="girl", role="captain"))
    mate = world.add(Entity(id=params.mate, kind="character", type="boy", role="mate"))
    world.add(Entity(id="ship", type="ship", label="the ship"))
    sea = world.add(Entity(id="sea", type="sea", label="the sea"))
    world.add(Entity(id="reef", type="reef", label="the reef")).meters["near"] += 1

    setup(world, fanny, mate, setting)
    world.para()
    voyage_goal(world, fanny, omen)
    foreshadow(world, mate, omen)
    inner_monologue(world, fanny, omen, response, params.delay)
    world.para()

    turned = decide(world, fanny, mate, response, params.delay)
    if turned:
        heed_and_turn(world, fanny, mate, response)
        safe_end(world, fanny, mate)
        outcome = "safe"
    else:
        sea.meters["storm"] += storm_strength(params.delay)
        propagate(world, narrate=False)
        storm_breaks(world, fanny, mate, response)
        storm_loss(world, fanny, mate)
        outcome = "rough"

    world.facts.update(fanny=fanny, mate=mate, setting=setting, omen=omen, response=response, outcome=outcome)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show safe/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("safe responses:")
        for s, r in asp_valid_combos():
            print(f"  {s} -> {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
