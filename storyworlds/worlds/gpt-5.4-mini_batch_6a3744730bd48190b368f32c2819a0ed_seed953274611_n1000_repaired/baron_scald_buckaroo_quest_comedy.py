#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baron_scald_buckaroo_quest_comedy.py
=====================================================================

A small self-contained story world for a comic quest tale: a proud baron,
an overly hot "scald" mishap, and a buckaroo who keeps the quest moving with
common-sense fixes, brisk helpers, and a funny ending image.

The world is driven by simulated state:
- physical meters: heat, scorch, effort, treasure, travel
- emotional memes: pride, worry, delight, relief, laughter

The story premise is simple:
A baron wants a grand quest done in a dramatic way, but the path gets too
hot, a scalding problem appears, and a buckaroo proposes a sensible comic fix.
The ending proves something changed in the world: the quest is completed,
the heat is handled, and the characters end in a brighter mood.

This file is standalone and uses only stdlib plus the shared result/ASP helpers.
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

QUEST_MIN_GOAL = 2
SCALD_THRESHOLD = 1.0
RESOLVE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    title: str = ""
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
        return self.label or self.id
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
    scene: str
    path: str
    quest_kind: str
    hazard_kind: str
    finish_image: str
    travel_hint: str
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
class QuestItem:
    id: str
    label: str
    phrase: str
    helps: str
    fits_hazard: bool = False
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


def _r_scorch(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["heat"] < SCALD_THRESHOLD:
            continue
        sig = ("scorch", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["scorch"] += 1
        if "road" in world.entities:
            world.get("road").meters["danger"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__heat__")
    return out


CAUSAL_RULES = [Rule("scorch", _r_scorch)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_quest(quest: Place, item: QuestItem) -> bool:
    return quest.hazard_kind in item.tags and item.fits_hazard


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def quest_severity(item: QuestItem, delay: int) -> int:
    return 1 + delay


def is_resolved(response: Response, item: QuestItem, delay: int) -> bool:
    return response.power >= quest_severity(item, delay)


def predict_heat(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_scald(sim, sim.get(item_id), narrate=False)
    return {"heated": sim.get(item_id).meters["heat"] >= SCALD_THRESHOLD}


def _do_scald(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["heat"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, baron: Entity, buckaroo: Entity, quest: Place) -> None:
    baron.memes["pride"] += 1
    buckaroo.memes["delight"] += 1
    world.say(
        f"Baron {baron.id} declared a grand quest at {quest.label}. "
        f"{quest.scene}"
    )
    world.say(
        f"{buckaroo.id} tipped {buckaroo.pronoun('possessive')} hat and said the "
        f"day felt like a circus with boots."
    )


def need_path(world: World, quest: Place, baron: Entity, buckaroo: Entity) -> None:
    world.say(
        f"But the trail was {quest.path}, and the map pointed toward the {quest.quest_kind}."
    )
    world.say(
        f'"We can get there," said {buckaroo.id}, "but not if the path starts acting '
        f'like a frying pan."'
    )


def warn(world: World, buckaroo: Entity, baron: Entity, item: QuestItem) -> None:
    heat = predict_heat(world, "treasure_item")
    buckaroo.memes["worry"] += 1
    if heat["heated"]:
        world.say(
            f'{buckaroo.id} blinked. "{baron.id}, that plan could scald the {item.label}. '
            f'We need a safer trick."'
        )


def insist(world: World, baron: Entity, item: QuestItem) -> None:
    baron.memes["pride"] += 1
    world.say(
        f'"A noble quest must be dramatic," Baron {baron.id} said, and set the '
        f'{item.label} right by the hot stone."
    )


def introduce_mishap(world: World, item: QuestItem, quest: Place) -> None:
    _do_scald(world, world.get("treasure_item"))
    world.say(
        f"A sizzling pop made everyone jump. The {item.label} got scalded, and the "
        f"whole trail smelled like soup with a mistake in it."
    )


def comic_fix(world: World, baron: Entity, buckaroo: Entity, response: Response,
              item: QuestItem, quest: Place, delay: int) -> None:
    body = response.text.replace("{item}", item.label)
    world.say(f"{buckaroo.id} grinned and {body}.")
    if is_resolved(response, item, delay):
        world.get("treasure_item").meters["heat"] = 0
        world.get("road").meters["danger"] = 0
        baron.memes["pride"] += 0.5
        buckaroo.memes["relief"] += 1
        world.say(
            f"The hot trouble cooled at once, and Baron {baron.id} had to laugh "
            f"at how much less noble the easy fix was."
        )
    else:
        world.say(
            f"The fix was too small for the sizzling trouble, and the quest got "
            f"muddled into a very embarrassing dash."
        )


def finish(world: World, baron: Entity, buckaroo: Entity, quest: Place, item: QuestItem) -> None:
    baron.memes["relief"] += 1
    buckaroo.memes["delight"] += 1
    world.say(
        f"By sunset, the quest was done anyway. Baron {baron.id} carried the {item.label} "
        f"past the last ridge, and {buckaroo.id} laughed so hard {buckaroo.pronoun()} had to "
        f"hold {buckaroo.pronoun('possessive')} sides."
    )
    world.say(
        f"At the end, the {quest.finish_image} proved the day had changed: no more heat, "
        f"no more fuss, just a buckaroo, a baron, and a completed quest."
    )


def tell(quest: Place, item: QuestItem, response: Response, baron_name: str = "Bram",
         buckaroo_name: str = "Bess", delay: int = 0) -> World:
    world = World()
    baron = world.add(Entity(id=baron_name, kind="character", type="man", role="baron", title="baron"))
    buckaroo = world.add(Entity(id=buckaroo_name, kind="character", type="girl", role="buckaroo", title="buckaroo"))
    road = world.add(Entity(id="road", type="thing", label="road"))
    treasure = world.add(Entity(id="treasure_item", kind="thing", type="thing", label=item.label))
    baron.memes["pride"] = 1
    buckaroo.memes["delight"] = 1

    open_scene(world, baron, buckaroo, quest)
    need_path(world, quest, baron, buckaroo)
    world.para()
    insist(world, baron, item)
    warn(world, buckaroo, baron, item)
    world.para()
    introduce_mishap(world, item, quest)
    comic_fix(world, baron, buckaroo, response, item, quest, delay)
    world.para()
    finish(world, baron, buckaroo, quest, item)

    world.facts.update(
        baron=baron, buckaroo=buckaroo, quest=quest, item=item, response=response,
        delay=delay, road=road, treasure=treasure, resolved=is_resolved(response, item, delay)
    )
    return world


PLACES = {
    "volcano": Place(
        id="volcano",
        label="the bright volcano trail",
        scene="The quest began on a winding trail where banners flapped like tiny flags.",
        path="so hot it made the stones hiss",
        quest_kind="golden gate",
        hazard_kind="hot",
        finish_image="cool moonlight on the trail",
        travel_hint="follow the tunnel markers",
        tags={"quest", "hot"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the castle kitchen",
        scene="The quest started beside a clattering kitchen where pots sang like bells.",
        path="slick with steam and jokes",
        quest_kind="silver spoon",
        hazard_kind="hot",
        finish_image="a clean counter and a smiling window",
        travel_hint="cross the spoon-bridge",
        tags={"quest", "hot"},
    ),
    "desert": Place(
        id="desert",
        label="the singing desert",
        scene="The quest opened under a wide sky, and the wind hummed like a fiddle.",
        path="hot enough to toast a pebble",
        quest_kind="sunken badge",
        hazard_kind="hot",
        finish_image="a tidy camp with a single brave lantern",
        travel_hint="follow the camel tracks",
        tags={"quest", "hot"},
    ),
}

ITEMS = {
    "crown": QuestItem(
        id="crown", label="crown", phrase="a shiny crown", helps="sparkles", fits_hazard=True,
        tags={"hot", "quest"},
    ),
    "lantern": QuestItem(
        id="lantern", label="lantern", phrase="a brass lantern", helps="glows", fits_hazard=True,
        tags={"hot", "quest"},
    ),
    "map": QuestItem(
        id="map", label="map", phrase="a paper map", helps="guides", fits_hazard=True,
        tags={"hot", "quest"},
    ),
}

RESPONSES = {
    "shade": Response(
        id="shade", sense=3, power=2,
        text="hoisted a big shade cloth over the {item} and marched it into the cooler path",
        fail="hoisted a little napkin over the {item}, which was no help at all",
        qa_text="hoisted a big shade cloth over the {item} and marched it into the cooler path",
        tags={"hot", "quest"},
    ),
    "cart": Response(
        id="cart", sense=3, power=3,
        text="rolled over a squeaky cart and loaded the {item} onto it like treasure in a parade",
        fail="rolled over a tiny cart that wobbled and tipped the {item} back into the heat",
        qa_text="rolled over a squeaky cart and loaded the {item} onto it like treasure in a parade",
        tags={"hot", "quest"},
    ),
    "boots": Response(
        id="boots", sense=2, power=2,
        text="swapped into cooler boots and took the {item} by the safest road",
        fail="wore the same hot boots and only kicked up more dust",
        qa_text="swapped into cooler boots and took the {item} by the safest road",
        tags={"hot", "quest"},
    ),
    "water_hat": Response(
        id="water_hat", sense=1, power=1,
        text="put a wet hat on the {item}",
        fail="put a wet hat on the {item}, which only made everyone confused",
        qa_text="put a wet hat on the {item}",
        tags={"hot", "quest"},
    ),
}

@dataclass
class StoryParams:
    theme: str
    item: str
    response: str
    baron_name: str
    buckaroo_name: str
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
    StoryParams(theme="volcano", item="crown", response="shade", baron_name="Bram", buckaroo_name="Bess", delay=0),
    StoryParams(theme="kitchen", item="lantern", response="cart", baron_name="Boris", buckaroo_name="Bree", delay=0),
    StoryParams(theme="desert", item="map", response="boots", baron_name="Barney", buckaroo_name="Kit", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            if valid_quest(place, item):
                for rid, resp in RESPONSES.items():
                    if resp.sense >= 2:
                        combos.append((pid, iid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comic quest story world with a baron and a buckaroo.")
    ap.add_argument("--theme", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--baron-name")
    ap.add_argument("--buckaroo-name")
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
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.item is None or c[1] == args.item)
              and (args.response is None or c[2] == args.response)]
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(Refusing response: it is too flimsy for a sensible comedy quest.)")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, item, response = rng.choice(sorted(combos))
    return StoryParams(
        theme=theme,
        item=item,
        response=response,
        baron_name=args.baron_name or rng.choice(["Bram", "Boris", "Barnaby", "Basil"]),
        buckaroo_name=args.buckaroo_name or rng.choice(["Bess", "Bree", "Bea", "Kit"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 1),
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in PLACES or params.item not in ITEMS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("(Refusing response: it is too flimsy for a sensible comedy quest.)")
    if not valid_quest(PLACES[params.theme], ITEMS[params.item]):
        raise StoryError("(No story: that item does not fit the quest hazard.)")
    world = tell(PLACES[params.theme], ITEMS[params.item], RESPONSES[params.response],
                 params.baron_name, params.buckaroo_name, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedic quest story that includes the words "baron", "buckaroo", and "scald".',
        f"Tell a funny quest story where Baron {f['baron'].id} wants the {f['item'].label}, but {f['buckaroo'].id} keeps the quest from becoming a scalding disaster.",
        f"Write a short, child-friendly adventure in which a baron and a buckaroo solve a hot quest with a clever fix and a laugh.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    baron, buckaroo, quest, item, resp = f["baron"], f["buckaroo"], f["quest"], f["item"], f["response"]
    return [
        ("Who is the story about?",
         f"It is about Baron {baron.id} and the buckaroo {buckaroo.id}. They set out on a quest and kept bumping into comic trouble."),
        ("What went wrong on the quest?",
         f"The path got hot enough to scald the {item.label}. That made the quest silly and tricky at the same time."),
        ("How did they fix it?",
         f"{buckaroo.id} used a sensible plan and {resp.qa_text.replace('{item}', item.label)}. That cool-headed move let the quest keep going."),
        ("How did the story end?",
         f"They finished the quest with less heat, more laughter, and a clear win. The ending image shows the trail calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a quest?",
         "A quest is a journey to get something important or solve a problem. People on a quest keep going until they reach the goal."),
        ("Why can scalding be dangerous?",
         "Scalding means something is so hot that it can burn skin quickly. Hot things should be handled carefully."),
        ("What is a buckaroo?",
         "A buckaroo is a cowboy word for a horse rider or ranch hand. In a comic story, a buckaroo can be a cheerful helper."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} {e.type:7} meters={dict(meters)} memes={dict(memes)} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.fits_hazard:
            lines.append(asp.fact("fits_hazard", iid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, I, R) :- place(P), item(I), response(R), fits_hazard(I), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, response) combos:\n")
        for p, i, r in combos:
            print(f"  {p:8} {i:8} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.baron_name} and {p.buckaroo_name}: {p.theme}/{p.item}/{p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedic quest story that includes the words "baron", "buckaroo", and "scald".',
        f"Tell a funny quest story where Baron {f['baron'].id} wants the {f['item'].label}, but {f['buckaroo'].id} keeps the quest from becoming a scalding disaster.",
        f"Write a short, child-friendly adventure in which a baron and a buckaroo solve a hot quest with a clever fix and a laugh.",
    ]


if __name__ == "__main__":
    main()
