#!/usr/bin/env python3
"""
storyworlds/worlds/communicative_cautionary_quest_folk_tale.py
===============================================================

A small folk-tale story world about a communicative quest with a cautionary turn.

Seed tale premise:
---
In a little village by a bright river, a child named Nia loved carrying messages
for the neighbors. One morning, the village elder gave Nia a sealed note and
said it must reach the miller before sunset. Along the road, Nia met a chattering
crow who offered to read the note aloud. The elder had warned, "A message that
is spoken too soon can lose its safe path." Nia had to decide whether to keep the
note secret, ask for help, or trust the crow.

World model:
---
- A message can be kept, shared, delayed, or delivered.
- Telling the wrong listener can cause gossip, loss of trust, and a failed quest.
- Good caution means asking the right person at the right time and delivering the
  message by hand.

Story shape:
---
setup -> caution -> quest turn -> delivery or near-loss -> resolution image
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    sealed: bool = False
    heard_by: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "elder", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather", "miller"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Village:
    place: str = "the village"
    road: str = "the river road"
    setting_detail: str = "The road wound past willow trees and a small stone bridge."
    safe_listeners: set[str] = field(default_factory=lambda: {"elder", "miller"})
    risky_listeners: set[str] = field(default_factory=lambda: {"crow", "sparrow", "fox"})
    gossip_limit: float = 1.0


class World:
    def __init__(self, village: Village) -> None:
        self.village = village
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.village)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Params / registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    village_name: str = "Willowbend"
    hero_name: str = "Nia"
    hero_type: str = "girl"
    elder_name: str = "Ivo"
    messenger_kind: str = "note"
    quest: str = "deliver"
    listener: str = "crow"
    seed: Optional[int] = None


HERO_NAMES = ["Nia", "Tamsin", "Rowan", "Mina", "Pip", "Lark", "Ari", "Sora"]
ELDER_NAMES = ["Ivo", "Mara", "Bram", "Tilda", "Orin"]
VILLAGE_NAMES = ["Willowbend", "Hearthglade", "Stoneferry", "Foxrun", "Juniper"]
TRAITS = ["careful", "quick", "brave", "curious", "gentle", "thoughtful"]
LISTENERS = ["crow", "sparrow", "fox", "goat", "child", "fisherman"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.listener in {"elder", "miller"}:
        raise StoryError("The risky listener must be someone who might gossip, not the intended receiver.")
    if params.quest not in {"deliver"}:
        raise StoryError("This world only supports a hand-delivered message quest.")
    if params.messenger_kind not in {"note", "basket-token", "sealed-message"}:
        raise StoryError("Unsupported messenger kind.")


def _init_world(params: StoryParams) -> World:
    village = Village(place=f"the village of {params.village_name}")
    world = World(village)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", "communicative", random.choice(TRAITS)],
        memes={"hope": 0.0, "worry": 0.0, "trust": 1.0, "resolve": 0.0, "shame": 0.0},
    ))
    elder = world.add(Entity(
        id=params.elder_name,
        kind="character",
        type="elder",
        label="the elder",
        traits=["wise", "old"],
        memes={"trust": 1.0, "worry": 0.0},
    ))
    receiver = world.add(Entity(
        id="Miller",
        kind="character",
        type="miller",
        label="the miller",
        traits=["busy", "kind"],
        memes={"trust": 1.0},
    ))
    note = world.add(Entity(
        id="Message",
        type="note",
        label="sealed note",
        phrase=f"a sealed {params.messenger_kind}",
        owner=elder.id,
        keeper=hero.id,
        carried_by=hero.id,
        sealed=True,
        meters={"travel": 0.0},
        memes={"privacy": 1.0, "importance": 1.0},
    ))
    world.facts.update(hero=hero, elder=elder, receiver=receiver, note=note, params=params)
    return world


def _event_set(note: Entity, speaker: Entity, listener: Entity) -> None:
    note.heard_by.add(listener.id)
    speaker.memes["trust"] = max(0.0, speaker.memes.get("trust", 0.0) - 0.5)
    speaker.memes["shame"] = speaker.memes.get("shame", 0.0) + 0.5
    listener.memes["trust"] = max(0.0, listener.memes.get("trust", 1.0) - 0.2)


def _good_step(world: World, hero: Entity, elder: Entity, receiver: Entity, note: Entity) -> None:
    hero.memes["resolve"] += 1.0
    hero.memes["worry"] += 0.5
    world.say(
        f"Little {hero.id} lived in {world.village.place}, where words traveled fast on the wind."
    )
    world.say(
        f"{hero.id} loved being communicative, so {hero.pronoun()} listened closely when {elder.label} gave {hero.pronoun('object')} {note.phrase}."
    )
    world.say(
        f'"Take this to {receiver.label} before sunset," {elder.label} said. '
        f'"A message spoken too soon can wander off and come back bent."'
    )


def _road_trip(world: World, hero: Entity) -> None:
    world.para()
    world.say(world.village.setting_detail)
    world.say(
        f"{hero.id} tucked the note close and walked along {world.village.road}, trying not to let anyone see the wax seal."
    )


def _temptation(world: World, hero: Entity, listener: Entity, note: Entity) -> None:
    world.say(
        f"Near a turn in the road, {listener.id} hopped onto a fence rail and asked, "
        f'"What is your secret, {hero.id}?"'
    )
    hero.memes["worry"] += 1.0
    world.say(
        f"{hero.id} paused. {hero.pronoun().capitalize()} wanted to answer, because {hero.pronoun('subject')} liked sharing news."
    )
    if listener.type in world.village.risky_listeners:
        world.say(
            f"But {elder.label}'s warning rang in {hero.id}'s mind: some ears make stories smaller by passing them around."
        )
    else:
        world.say(
            f"Still, {hero.id} remembered that not every friendly question deserves the whole message."
        )


def _crossroads_choice(world: World, hero: Entity, elder: Entity, receiver: Entity, note: Entity, listener: Entity) -> None:
    if listener.type in world.village.risky_listeners:
        world.say(
            f'"I cannot say," {hero.id} whispered, and {hero.pronoun()} held the note tighter.'
        )
        hero.memes["resolve"] += 1.0
    else:
        world.say(
            f'{hero.id} gave {listener.id} a tiny greeting, but kept the message sealed.'
        )
    world.say(
        f"That cautious choice kept the quest on its own path."
    )


def _deliver(world: World, hero: Entity, elder: Entity, receiver: Entity, note: Entity) -> None:
    note.carried_by = receiver.id
    note.keeper = receiver.id
    note.meters["travel"] += 1.0
    hero.memes["hope"] += 1.0
    receiver.memes["trust"] += 0.5
    world.para()
    world.say(
        f"At last {hero.id} reached {receiver.label} and placed the sealed note into {receiver.pronoun('possessive')} hands."
    )
    world.say(
        f'{receiver.id} broke the seal, read the words once, and nodded. "This is good news, and it arrived whole," {receiver.pronoun()} said.'
    )
    world.say(
        f"{hero.id} smiled, because the message had stayed true from mouth to hand to ear."
    )


def _ending_image(world: World, hero: Entity, elder: Entity, receiver: Entity) -> None:
    world.para()
    world.say(
        f"By evening, the village lanterns glowed over the river, and {hero.id} walked home knowing when to speak and when to keep a promise quiet."
    )
    world.say(
        f"{elder.label} nodded at {hero.id}, and even the bridge looked as if it had learned to listen."
    )


def tell(params: StoryParams) -> World:
    world = _init_world(params)
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    receiver = world.facts["receiver"]
    note = world.facts["note"]

    _good_step(world, hero, elder, receiver, note)
    _road_trip(world, hero)

    listener = world.add(Entity(
        id=params.listener.capitalize(),
        kind="character",
        type=params.listener,
        label=f"the {params.listener}",
        traits=["chatty", "nosy"] if params.listener in world.village.risky_listeners else ["friendly"],
        memes={"trust": 0.5},
    ))
    _temptation(world, hero, listener, note)
    _crossroads_choice(world, hero, elder, receiver, note, listener)
    _deliver(world, hero, elder, receiver, note)
    _ending_image(world, hero, elder, receiver)

    world.facts.update(listener=listener, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short folk tale about a communicative child named {p.hero_name} who must deliver a message without letting gossip steal it.',
        f"Tell a cautionary quest story set in {p.village_name} where {p.hero_name} carries a sealed note for the elder and learns to speak carefully.",
        f'Write a gentle village story about a secret message, a tempting question, and a safe delivery before sunset.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    receiver = world.facts["receiver"]
    listener = world.facts["listener"]
    note = world.facts["note"]

    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, a little communicative {hero.type} who carried a sealed message through {p.village_name}.",
        ),
        QAItem(
            question=f"What job did {elder.label} give {hero.id}?",
            answer=f"{elder.label} asked {hero.id} to deliver the sealed note to {receiver.label} before sunset.",
        ),
        QAItem(
            question=f"What tempting thing did {listener.id} do on the road?",
            answer=f"{listener.id} asked what secret {hero.id} was carrying, which tempted the child to talk too soon.",
        ),
        QAItem(
            question=f"How did {hero.id} keep the quest safe?",
            answer=f"{hero.id} held the note close, refused to repeat the secret, and kept the message sealed until {receiver.label} could read it.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"By the end, the note reached {receiver.label} whole, and {hero.id} learned that careful speech can protect an important message.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a sealed note?",
        answer="A sealed note is a piece of writing closed up so other people cannot read it until the seal is broken.",
    ),
    QAItem(
        question="Why can gossip be risky?",
        answer="Gossip can be risky because it can change a story as it passes from person to person.",
    ),
    QAItem(
        question="What does it mean to deliver something by hand?",
        answer="To deliver something by hand means to carry it yourself and give it directly to the right person.",
    ),
    QAItem(
        question="Why do folk tales often include a warning?",
        answer="Folk tales often include a warning so the listener can learn a lesson from the hero's choice.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is valid when a hero can carry a sealed message to the receiver.
valid_quest(Hero, Listener) :- hero(Hero), listener(Listener), risky(Listener).

% Cautionary turn: risky listeners are not to be trusted with the full message.
must_keep_secret(Hero, Listener) :- valid_quest(Hero, Listener).

% Successful resolution requires the message to stay sealed and be delivered.
resolved(Hero, Receiver) :- hero(Hero), receiver(Receiver), delivered(Hero, Receiver), sealed_message.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero", "Nia"))
    lines.append(asp.fact("receiver", "Miller"))
    for name in LISTENERS:
        lines.append(asp.fact("listener", name))
        if name in {"crow", "sparrow", "fox"}:
            lines.append(asp.fact("risky", name))
    lines.append(asp.fact("sealed_message"))
    lines.append(asp.fact("delivered", "Nia", "Miller"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_quest/2."))
    atoms = set(asp.atoms(model, "valid_quest"))
    expected = {("Nia", "crow"), ("Nia", "sparrow"), ("Nia", "fox")}
    if atoms == expected:
        print(f"OK: clingo gate matches expected quest set ({len(atoms)} risky listeners).")
        return 0
    print("MISMATCH between clingo and expected quest set:")
    print("  clingo:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation / validation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small communicative cautionary quest folk tale world."
    )
    ap.add_argument("--village-name", choices=VILLAGE_NAMES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-name", choices=ELDER_NAMES)
    ap.add_argument("--listener", choices=LISTENERS)
    ap.add_argument("--messenger-kind", choices=["note", "basket-token", "sealed-message"])
    ap.add_argument("--quest", choices=["deliver"])
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
    params = StoryParams(
        village_name=args.village_name or rng.choice(VILLAGE_NAMES),
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        elder_name=args.elder_name or rng.choice(ELDER_NAMES),
        messenger_kind=args.messenger_kind or rng.choice(["note", "basket-token", "sealed-message"]),
        quest=args.quest or "deliver",
        listener=args.listener or rng.choice(LISTENERS),
    )
    reasonableness_gate(params)
    if params.listener in {"elder", "miller"}:
        raise StoryError("Listener must be a risky passerby, not the intended receiver.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.sealed:
            bits.append("sealed=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.heard_by:
            bits.append(f"heard_by={sorted(e.heard_by)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


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
    StoryParams(village_name="Willowbend", hero_name="Nia", hero_type="girl", elder_name="Ivo", messenger_kind="note", quest="deliver", listener="crow"),
    StoryParams(village_name="Hearthglade", hero_name="Tamsin", hero_type="girl", elder_name="Mara", messenger_kind="sealed-message", quest="deliver", listener="fox"),
    StoryParams(village_name="Stoneferry", hero_name="Rowan", hero_type="boy", elder_name="Bram", messenger_kind="basket-token", quest="deliver", listener="sparrow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_quest/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_quest/2."))
        vals = sorted(set(asp.atoms(model, "valid_quest")))
        print(f"{len(vals)} risky quest pairs:\n")
        for hero, listener in vals:
            print(f"  {hero:8} -> {listener}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} in {p.village_name} (listener: {p.listener})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
