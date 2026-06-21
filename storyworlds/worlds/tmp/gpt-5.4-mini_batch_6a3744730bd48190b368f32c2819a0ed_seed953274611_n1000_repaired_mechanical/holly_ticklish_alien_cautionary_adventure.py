#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/holly_ticklish_alien_cautionary_adventure.py
=============================================================================

A tiny standalone storyworld for a cautionary adventure about Holly, a ticklish
alien, and a small choice that could have gone wrong.

Premise
-------
Holly meets a ticklish alien on a windy hill path near an old hollow tree. The
alien wants to chase a glowing pebble into a dark opening, but Holly notices a
danger in time and chooses a safer route. The story stays adventurous, but the
turn is cautionary: curiosity is fine, yet some places need a grown-up and a
lantern.

This world models:
- typed entities with physical meters and emotional memes
- a state-driven turn from temptation to warning to safer action
- a reasonableness gate that only allows hazardous adventure setups
- a small inline ASP twin for parity checks

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/holly_ticklish_alien_cautionary_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/holly_ticklish_alien_cautionary_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/holly_ticklish_alien_cautionary_adventure.py --verify
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
class Place:
    id: str
    label: str
    dark_opening: str
    view: str
    wind: str
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
class AdventureThing:
    id: str
    label: str
    phrase: str
    glow: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_scared(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["danger"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("scared", _r_scared)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def hazard_at_risk(place: Place, thing: AdventureThing) -> bool:
    return place.dangerous and thing.dangerous


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= (1 + delay)


def would_skip_trouble(holly: Entity, alien: Entity) -> bool:
    return holly.memes["caution"] + alien.memes["hesitation"] >= 5


def predict(world: World, thing_id: str) -> dict:
    sim = world.copy()
    _do_danger(sim, sim.get(thing_id), narrate=False)
    return {"danger": sim.get("path").meters["danger"]}


def _do_danger(world: World, thing: Entity, narrate: bool = True) -> None:
    thing.meters["glimmer"] += 1
    world.get("path").meters["danger"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, holly: Entity, alien: Entity, place: Place, thing: AdventureThing) -> None:
    holly.memes["curiosity"] += 1
    alien.memes["hope"] += 1
    world.say(
        f"Holly and the ticklish alien climbed the windy path above the garden. "
        f"{place.view} Holly noticed {place.wind}, and the holly bush near the fence "
        f"shook like it was whispering a secret."
    )
    world.say(
        f"The alien pointed at a glowing pebble beside {place.dark_opening}. "
        f'"Look!" it chirped. "A shiny adventure!"'
    )


def warn(world: World, holly: Entity, alien: Entity, place: Place, thing: AdventureThing) -> None:
    pred = predict(world, thing.id)
    holly.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"Holly looked at the dark opening and bit {holly.pronoun('possessive')} lip. "
        f'"That place is too dark," Holly said. "A pebble can roll in there, and then '
        f'we could get stuck trying to reach it."'
    )


def tempt(world: World, alien: Entity, thing: AdventureThing) -> None:
    alien.memes["bravery"] += 1
    world.say(
        f"The alien wiggled and laughed because it was so ticklish. "
        f'"I can reach it," it said, already leaning closer.'
    )


def choose_safe(world: World, holly: Entity, alien: Entity, place: Place) -> None:
    holly.memes["relief"] += 1
    alien.memes["relief"] += 1
    world.say(
        f'Holly held out a hand. "Let’s use the lantern path instead," she said. '
        f'"We can explore the hill without chasing anything into the hole."'
    )
    world.say(
        f'The alien nodded, still giggling from being ticklish, and together they '
        f'followed the bright stones away from {place.dark_opening}.'
    )


def _do_adventure(world: World, thing: Entity, place: Place) -> None:
    _do_danger(world, thing)
    world.say(
        f"The pebble skittered closer to {place.dark_opening}, and the hill path felt "
        f"nervy all at once."
    )


def resolution(world: World, holly: Entity, alien: Entity, place: Place, thing: AdventureThing) -> None:
    world.say(
        f"They found the same glowing pebble again by the lantern light, this time "
        f"right where the path was safe and open."
    )
    world.say(
        f"Holly tucked it into a pocket of moss, and the ticklish alien laughed so hard "
        f"that the holly leaves trembled beside the path."
    )


def tell(place: Place, thing: AdventureThing, response: Response) -> World:
    world = World()
    holly = world.add(Entity(id="Holly", kind="character", type="girl", role="hero"))
    alien = world.add(Entity(id="Alien", kind="character", type="alien", role="companion"))
    path = world.add(Entity(id="path", type="path", label="the path"))
    hole = world.add(Entity(id="hole", type="opening", label=place.dark_opening))

    holly.memes["caution"] = 2
    alien.memes["hesitation"] = 1

    setup(world, holly, alien, place, thing)
    world.para()
    tempt(world, alien, thing)
    warn(world, holly, alien, place, thing)

    if would_skip_trouble(holly, alien):
        choose_safe(world, holly, alien, place)
        outcome = "averted"
    else:
        _do_adventure(world, thing, place)
        severity = 1
        contained = is_contained(response, severity)
        if contained:
            world.say(
                f"Holly waved to a grown-up nearby, and the grown-up used {response.text}."
            )
            world.say(
                "The scary part stopped at once, and the adventure became safe again."
            )
            resolution(world, holly, alien, place, thing)
            outcome = "contained"
        else:
            world.say(
                f"The grown-up tried to help, but {response.fail}. "
                f"Holly grabbed the alien's hand, and they backed away fast."
            )
            world.say(
                "They made it home with dusty shoes and a very important lesson: "
                "never chase a bright thing into a dark place."
            )
            outcome = "burned"

    world.facts.update(
        holly=holly,
        alien=alien,
        place=place,
        thing=thing,
        path=path,
        hole=hole,
        response=response,
        outcome=outcome,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden hill",
        dark_opening="the hollow tree",
        view="The grass below glittered with dew.",
        wind="a cool wind",
        tags={"garden", "adventure"},
    ),
    "lantern": Place(
        id="lantern",
        label="the lantern path",
        dark_opening="the cave mouth",
        view="The lantern stones glowed like tiny moons.",
        wind="a soft breeze",
        tags={"path", "cave"},
    ),
}

THINGS = {
    "pebble": AdventureThing(
        id="pebble",
        label="glowing pebble",
        phrase="a glowing pebble",
        glow="shone like a tiny star",
        dangerous=True,
        tags={"glow", "dark"},
    ),
    "map": AdventureThing(
        id="map",
        label="paper map",
        phrase="a paper map",
        glow="rustled in the wind",
        dangerous=True,
        tags={"map", "dark"},
    ),
}

RESPONSES = {
    "lantern": Response(
        id="lantern",
        sense=3,
        power=2,
        text="took out a lantern and lit the path",
        fail="the lantern flickered out",
        qa_text="took out a lantern and lit the path",
        tags={"safe"},
    ),
    "call_adult": Response(
        id="call_adult",
        sense=4,
        power=3,
        text="came quickly with a bright lantern and a steady hand",
        fail="could not find the lantern right away",
        qa_text="came quickly with a bright lantern and a steady hand",
        tags={"safe", "adult"},
    ),
    "stomp": Response(
        id="stomp",
        sense=1,
        power=1,
        text="stomped near the hole",
        fail="stomped, but that only made the dirt slide",
        qa_text="stomped near the hole",
        tags={"weak"},
    ),
}

SENSE_MIN = 2

NAMES = ["Holly"]


@dataclass
class StoryParams:
    place: str
    thing: str
    response: str
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
    StoryParams(place="garden", thing="pebble", response="call_adult"),
    StoryParams(place="lantern", thing="map", response="lantern"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for thing_id, thing in THINGS.items():
            if hazard_at_risk(place, thing):
                combos.append((place_id, thing_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary adventure storyworld about Holly and a ticklish alien.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this cautionary adventure.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, thing = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(place=place, thing=thing, response=response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly cautionary adventure story that includes the words "holly", "ticklish", and "alien".',
        f"Tell a small adventure where Holly meets a ticklish alien near {f['place'].dark_opening} and chooses a safer path instead of chasing a glowing thing inside.",
        "Write a gentle warning story with a bright ending, a curious alien, and a brave child who notices danger in time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holly = f["holly"]
    alien = f["alien"]
    place = f["place"]
    thing = f["thing"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?",
         "It is about Holly and a ticklish alien who went on a small adventure together."),
        ("What did they see on the hill?",
         f"They saw {thing.phrase} near {place.dark_opening}. That bright little thing made the dark opening tempting."),
        ("Why did Holly warn the alien?",
         f"Holly warned the alien because {place.dark_opening} was too dark and a shiny thing could roll inside. Holly wanted the adventure to stay safe."),
    ]
    if out == "averted":
        qa.append((
            "What did Holly and the alien do instead?",
            "They chose the safer lantern path instead of chasing the pebble into the hole. "
            "That kept the adventure fun without any danger."
        ))
    elif out == "contained":
        qa.append((
            "How did they stay safe after the mistake?",
            "A grown-up came quickly and used a safe response to stop the trouble. "
            "Then Holly and the alien kept the adventure going in a safer place."
        ))
    else:
        qa.append((
            "How did the story end?",
            "They got away safely, but only after learning not to chase bright things into dark openings. "
            "The ending is cautious because the danger was real."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a holly bush?",
         "A holly bush is a plant with shiny leaves. People often notice it because the leaves can look bright and prickly."),
        ("What does ticklish mean?",
         "Ticklish means that light touches or little wiggles make someone laugh or squirm. It is a funny feeling, not a hurt feeling."),
        ("What is an alien?",
         "An alien is a made-up visitor from another world. In stories, aliens can be curious, friendly, or a little strange."),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, T) :- place(P), thing(T), dangerous_place(P), dangerous_thing(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(averted) :- caution_high, not danger_started.
outcome(contained) :- danger_started, contained_fire.
outcome(burned) :- danger_started, not contained_fire.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "cave" in p.tags:
            lines.append(asp.fact("dangerous_place", pid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.dangerous:
            lines.append(asp.fact("dangerous_thing", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        print("MISMATCH: ASP gate differs from Python valid_combos().")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH: sensible responses differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, thing=None, response=None), random.Random(7)))
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def tell_place_holder(place: Place, thing: AdventureThing, response: Response) -> World:
    return tell(place, thing, response)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.thing not in THINGS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], THINGS[params.thing], RESPONSES[params.response])
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
        print(asp_program(show="#show hazard/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print("hazardous combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
