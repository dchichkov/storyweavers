#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/sociology_religion_disco_suspense_humor_bravery_folk.py
===========================================================================================================

A small folk-tale storyworld about a village gathering where sociology,
religion, and disco meet under one moonlit roof.

Seed-tale sketch:
---
In a little village, people had grown lonely after a long winter. A kind child
noticed that neighbors were not speaking much to one another, and the old
chapel bell had grown quiet. The child loved listening to the elders' stories
and wanted the village to feel like one warm circle again.

One evening, the village planned a disco in the barn to raise coins for the
chapel roof. The priest worried that the spinning lights might scare the doves
from the rafters and upset the holy candles. The village wise woman warned
that the neighborly gossip had already split the room into little islands.

The child was nervous but brave. With a funny hat, a careful plan, and a clear
voice, the child helped set the lanterns safely, invited the shyest folk to the
dance floor, and asked everyone to speak one kind word before the music began.
By the end, the barn rang with laughter, the coins clicked into the charity
bowl, and the old chapel felt warm again.

World model notes:
---
- physical meters: crowd, coin_bowl, candle_safety, lanterns, noise, floor_spin
- emotional memes: courage, suspicion, laughter, belonging, reverence, awkwardness
- the simulated state drives the prose, the suspense, the humor, and the ending image
  where the village is visibly changed
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World entities and state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "place" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    role: str = ""  # villager, priest, child, elder, musician, goat, etc.
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    sacred: bool = False


@dataclass
class SceneChoice:
    """The core compatible combo for the tale."""
    setting: str
    event: str
    token: str
    guardian_item: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "barn": Setting(place="the old barn", indoors=True, sacred=False),
    "chapel-yard": Setting(place="the chapel yard", indoors=False, sacred=True),
    "village-green": Setting(place="the village green", indoors=False, sacred=False),
}

EVENTS = {
    "disco": {
        "keyword": "disco",
        "verb": "dance at the disco",
        "gerund": "dancing at the disco",
        "rush": "dash onto the dance floor",
        "noise": "the music thumped and clapped like big friendly feet",
        "risk": "floor_spin",
        "suspense": "The lanterns swayed a little in the rafters, and everybody held their breath.",
        "humor": "One goose tried to bob its head in time and missed the beat by a whole wing.",
        "tags": {"disco", "music", "dance"},
    },
    "storycircle": {
        "keyword": "story circle",
        "verb": "tell stories in the circle",
        "gerund": "telling stories in a circle",
        "rush": "hurry to the storyteller's bench",
        "noise": "the voices rose and fell like a soft pond ripple",
        "risk": "crowd",
        "suspense": "A hush fell when the oldest chair creaked by itself.",
        "humor": "A kitten climbed into the basket and looked as if it had come to judge the tale.",
        "tags": {"sociology", "story", "village"},
    },
    "bell-chorus": {
        "keyword": "bell chorus",
        "verb": "ring the bell chorus",
        "gerund": "ringing bells together",
        "rush": "run to the bell rope",
        "noise": "the bells chimed like bright drops of rain",
        "risk": "reverence",
        "suspense": "The priest touched the rope and waited to see if the old brass would sing true.",
        "humor": "One small bell gave a squeak so thin that even the priest blinked at it.",
        "tags": {"religion", "bell", "song"},
    },
}

TOKENS = {
    "lanterns": {
        "label": "paper lanterns",
        "phrase": "a string of paper lanterns",
        "protects": {"candle_safety"},
        "helps": {"disco", "storycircle"},
        "kind": "thing",
    },
    "candles": {
        "label": "candle guards",
        "phrase": "little glass covers for the candles",
        "protects": {"candle_safety"},
        "helps": {"bell-chorus"},
        "kind": "thing",
    },
    "cookies": {
        "label": "honey cookies",
        "phrase": "a tray of honey cookies",
        "protects": {"laughter"},
        "helps": {"storycircle", "disco"},
        "kind": "thing",
    },
}

PEOPLE = {
    "child": {"type": "girl", "role": "child", "name": ["Mina", "Pip", "Lina", "Jori"]},
    "priest": {"type": "priest", "role": "priest", "name": ["Father Vale", "Sister Runa"]},
    "elder": {"type": "woman", "role": "elder", "name": ["Grandma Wren", "Aunt Sula"]},
    "musician": {"type": "man", "role": "musician", "name": ["Tomas", "Bren", "Orrin"]},
}

FOLK_TRAITS = ["brave", "curious", "cheerful", "small", "quick-witted", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    event: str
    token: str
    child_name: str
    priest_name: str
    elder_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A tale is reasonable when the event belongs in the setting and the token
% honestly addresses the event's risk.
compatible(S, E, T) :- setting(S), event(E), token(T),
                       affords(S, E), helps(T, E),
                       protects(T, R), risk(E, R).

% A full story is compatible when the chosen people can all fit the tale.
valid_story(S, E, T) :- compatible(S, E, T), has_child, has_priest, has_elder.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.sacred:
            lines.append(asp.fact("sacred", sid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("risk", eid, e["risk"]))
        for t in sorted(e["tags"]):
            lines.append(asp.fact("tag", eid, t))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        for r in sorted(t["protects"]):
            lines.append(asp.fact("protects", tid, r))
        for e in sorted(t["helps"]):
            lines.append(asp.fact("helps", tid, e))
    lines.append(asp.fact("has_child"))
    lines.append(asp.fact("has_priest"))
    lines.append(asp.fact("has_elder"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for eid, e in EVENTS.items():
            for tid, t in TOKENS.items():
                if e["risk"] in t["protects"] and eid in t["helps"]:
                    out.append((sid, eid, tid))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonable story engine
# ---------------------------------------------------------------------------
def reason_gate(setting: str, event: str, token: str) -> None:
    if (setting, event, token) not in valid_combos():
        raise StoryError(
            f"(No story: the {token} does not honestly solve the risk of {event} "
            f"in {setting}. The folk tale needs a fitting helper.)"
        )


def choose_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.event:
        combos = [c for c in combos if c[1] == args.event]
    if args.token:
        combos = [c for c in combos if c[2] == args.token]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, event, token = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        event=event,
        token=token,
        child_name=rng.choice(PEOPLE["child"]["name"]),
        priest_name=rng.choice(PEOPLE["priest"]["name"]),
        elder_name=rng.choice(PEOPLE["elder"]["name"]),
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    event = EVENTS[params.event]
    token = TOKENS[params.token]
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name, kind="character", type="girl",
        role="child", label=params.child_name,
    ))
    priest = world.add(Entity(
        id=params.priest_name, kind="character", type="priest",
        role="priest", label=params.priest_name,
    ))
    elder = world.add(Entity(
        id=params.elder_name, kind="character", type="woman",
        role="elder", label=params.elder_name,
    ))
    helper = world.add(Entity(
        id=token["label"], kind="thing", type=token["kind"], label=token["label"],
        phrase=token["phrase"],
    ))
    world.facts.update(child=child, priest=priest, elder=elder, helper=helper, event=event, token=token)
    return world


def simulate(world: World) -> None:
    child = world.facts["child"]
    priest = world.facts["priest"]
    elder = world.facts["elder"]
    event = world.facts["event"]
    token = world.facts["token"]
    helper = world.facts["helper"]

    child.memes["curiosity"] = 1
    child.memes["courage"] = 1
    priest.memes["reverence"] = 1
    elder.memes["belonging"] = 1

    world.say(
        f"In {world.setting.place}, {child.id} was a {random.choice(FOLK_TRAITS)} little child "
        f"who liked to listen to village talk and church songs."
    )
    world.say(
        f"The folk had come to plan a {event['keyword']} for the evening, "
        f"and {child.id} hoped it would bring the neighbors together."
    )
    world.say(
        f"The plan had a purpose too: the coin bowl at the door needed filling, "
        f"so the chapel roof could be mended before the next rain."
    )

    world.para()
    world.say(
        f"But when the lanterns were lit, the priest frowned a little. "
        f"{event['suspense']}"
    )
    priest.memes["suspicion"] = 1
    world.facts["suspense"] = True
    world.say(
        f'"If the room gets too wild," {priest.id} said, "the holy candles may wobble and the peace may crack."'
    )

    world.say(
        f"{elder.id} gave a wise cough and pointed at the shy benches. "
        f'"A village does not grow warm by itself," {elder.id} said. "Someone must start the circle."'
    )
    world.say(
        f"{event['humor']}'
        .replace(\"'\", \"\")  # keep source clean; the line below is the actual sentence
    )

    child.memes["awkwardness"] = 1
    child.memes["courage"] += 1
    world.say(
        f"{child.id}'s knees felt wobbly, but {child.id} stepped forward anyway. "
        f'\"I can help,\" {child.id} said, and the words came out small but steady.'
    )

    world.para()
    world.say(
        f"{child.id} tied {helper.label} along the candle hooks and set the lanterns higher, "
        f"so the bright paper would guard the holy flames from the spinning feet."
    )
    world.say(
        f"Then {child.id} asked each neighbor for one kind word before the music began. "
        f"The grumpy miller said, \"Your beard looks like a nesting bird,\" and everybody laughed."
    )
    world.say(
        f"That laugh loosened the room. {child.id} invited the shyest folk first, "
        f"and even the priest took a careful step or two."
    )

    # World-state turn: crowd, coin bowl, and emotions.
    world.facts["coin_bowl"] = 0
    world.facts["crowd"] = 1
    world.facts["candle_safety"] = 1.0
    world.facts["lanterns"] = 1.0
    world.facts["floor_spin"] = 1.0

    world.facts["coin_bowl"] += 5
    world.facts["crowd"] += 8
    child.memes["belonging"] += 2
    child.memes["laughter"] = 1
    priest.memes["suspicion"] = 0
    priest.memes["reverence"] += 1
    elder.memes["belonging"] += 2

    world.say(
        f"Soon the music sang, the boots shuffled, and the coin bowl clicked and chimed with every round of dancing."
    )
    world.say(
        f"{priest.id} saw that the candles stayed safe, the lanterns glowed softly, and the barn had become a kind place."
    )
    world.say(
        f"The village laugh grew bigger than its worry, and the night felt as wide as a field after harvest."
    )

    world.para()
    world.say(
        f"By the end, the chapel roof had its coins, the neighbors spoke to one another, "
        f"and {child.id} stood under the lanterns with a brave smile."
    )
    world.say(
        f"The old barn smelled of straw, honey cookies, and warm joy, and the village knew "
        f"that a little courage can make a whole crowd feel like family."
    )

    world.facts["resolved"] = True
    world.facts["helper_item"] = helper


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a folk tale for a young child about a village disco, a worried priest, and a brave child who helps everyone get along.",
        f"Tell a gentle story in which {f['child'].id} helps the neighbors at {world.setting.place} without letting the candles get into danger.",
        f"Write a suspenseful but funny tale about a {f['event']['keyword']} that ends with the village feeling closer together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, priest, elder = f["child"], f["priest"], f["elder"]
    event, token = f["event"], f["token"]
    return [
        QAItem(
            question=f"Who was the brave child in the story?",
            answer=f"The brave child was {child.id}. {child.id} stepped forward first and helped calm the room.",
        ),
        QAItem(
            question=f"Why was {priest.id} worried before the music began?",
            answer=(
                f"{priest.id} was worried that the {event['keyword']} might make the holy candles wobble "
                f"and disturb the peace. The worry faded once the lanterns and candle guards kept everything safe."
            ),
        ),
        QAItem(
            question=f"What did {f['child'].id} use to help protect the candles?",
            answer=(
                f"{child.id} used {token['phrase']} to keep the bright paper and the holy flames safely apart."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=(
                f"By the end, the coin bowl was full enough to help the chapel roof, the neighbors were talking, "
                f"and the village felt warm and united instead of shy."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a disco?",
            answer="A disco is a dance party with music, moving feet, and lots of lively lights.",
        ),
        QAItem(
            question="What does a priest do in a village story?",
            answer="A priest is a person who helps care for the village's worship, prayers, and sacred places.",
        ),
        QAItem(
            question="What is sociology?",
            answer="Sociology is the study of how people live together in groups, share rules, and make communities.",
        ),
        QAItem(
            question="Why do villagers sometimes hold a gathering?",
            answer="Villagers gather to share work, talk together, celebrate, or help one another with a common need.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:18} ({e.kind:8}) {' '.join(bits)}")
    for k, v in world.facts.items():
        if k in {"child", "priest", "elder", "helper", "event", "token"}:
            continue
        lines.append(f"  fact {k}: {v}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld: sociology, religion, disco, humor, bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return choose_combo(args, rng)


def generate(params: StoryParams) -> StorySample:
    reason_gate(params.setting, params.event, params.token)
    world = build_world(params)
    simulate(world)
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


CURATED = [
    StoryParams(setting="barn", event="disco", token="lanterns", child_name="Mina", priest_name="Father Vale", elder_name="Grandma Wren"),
    StoryParams(setting="chapel-yard", event="bell-chorus", token="candles", child_name="Pip", priest_name="Sister Runa", elder_name="Aunt Sula"),
    StoryParams(setting="village-green", event="storycircle", token="cookies", child_name="Lina", priest_name="Father Vale", elder_name="Grandma Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} valid stories:")
        for s, e, t in models:
            print(f"  {s:12} {e:12} {t:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
