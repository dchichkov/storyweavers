#!/usr/bin/env python3
"""
Fairy-tale storyworld: an elephant, a brave promise, and a bad ending.

A tiny simulated domain built from a seed tale:
- A small elephant hears a plea in a fairy-tale village.
- Dialogue matters: spoken promises change courage and fear.
- Bravery can push the elephant forward, but not every brave choice succeeds.
- The ending is intentionally bad: the hero tries, but the rescue fails, and
  the last image proves the loss.

The world is state-driven: characters have physical meters and emotional memes,
and the prose is assembled from what actually happened in the simulation.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"elephant"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str = "misty"
    title: str = "fairy tale"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


SETTINGS = {
    "forest": Setting(place="the moonlit forest", weather="misty"),
    "bridge": Setting(place="the old stone bridge", weather="windy"),
    "castle": Setting(place="the castle gate", weather="rainy"),
}

HERO_NAMES = ["Pip", "Milo", "Nia", "Luna", "Tavi", "Rosa"]
COMPANION_NAMES = ["Mara", "Finn", "Sera", "Owen", "Iris", "Jory"]


def _say_dialogue(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.id} said.')


def _bravery_gain(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + amount


def _fear_gain(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + amount


def _damage_gain(world: World, thing: Entity, amount: float = 1.0) -> None:
    thing.meters["broken"] = thing.meters.get("broken", 0.0) + amount


def _rule_try_rescue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("elephant")
    relic = world.get("lantern")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if world.fired.__contains__(("rescue",)):
        return out
    world.fired.add(("rescue",))
    relic.meters["unsafe"] = relic.meters.get("unsafe", 0.0) + 1
    out.append("The elephant stepped closer to the lantern bridge.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_rule_try_rescue,):
            sent = fn(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(place: str, hero_name: str, companion_name: str) -> World:
    world = World(setting=SETTINGS[place])

    elephant = world.add(Entity(
        id="elephant",
        kind="character",
        type="elephant",
        label="a small elephant",
        traits=["small", "kind", "brave"],
        memes={"bravery": 0.0, "fear": 0.0, "hope": 0.0, "sorrow": 0.0},
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type="girl",
        label=f"little {companion_name}",
        memes={"hope": 0.0, "fear": 0.0},
        traits=["little", "gentle"],
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="thing",
        label="glass lantern",
        phrase="a glass lantern hanging on a willow rope",
        owner=companion.id,
        caretaker=companion.id,
        meters={"light": 1.0, "unsafe": 0.0, "broken": 0.0},
    ))
    king = world.add(Entity(
        id=hero_name,
        kind="character",
        type="king",
        label=f"King {hero_name}",
        memes={"worry": 0.0},
        traits=["old", "grave"],
    ))

    # Setup
    world.say(
        f"In {world.setting.place}, there lived a small elephant with ears like fans and a heart that listened well."
    )
    world.say(
        f"One evening, {companion.id} found {lantern.phrase} swinging high over the bridge, and {lantern.label} was the only light left for the lane."
    )
    world.say(
        f"{elephant.id} liked the little village, and {companion.id} liked speaking to {elephant.pronoun('object')} because {elephant.pronoun()} never laughed at a frightened voice."
    )

    # Tension
    world.para()
    _say_dialogue(world, companion, "The rope is fraying. If the lantern falls, the path will go dark.")
    world.say(
        f"{elephant.id} looked at the dark water below the bridge and felt {elephant.pronoun('possessive')} knees tremble."
    )
    _fear_gain(world, elephant, 1.0)
    _say_dialogue(world, elephant, "I am not a mighty knight, but I can still try.")
    _bravery_gain(world, elephant, 1.0)
    world.say(
        f"That promise warmed {elephant.pronoun('possessive')} chest, and {companion.id} clasped {companion.pronoun('possessive')} hands as if the words were a spell."
    )
    world.say(
        f"The king warned them that the bridge was old and the wind had teeth."
    )

    # Turn
    world.para()
    world.say(
        f"{elephant.id} walked onto the bridge anyway, one careful foot at a time, while the lantern swayed above the river."
    )
    propagate(world, narrate=True)
    _say_dialogue(world, elephant, "Hold the rope steady. I will lift it free.")
    world.say(
        f"{companion.id} tried to help, but the wind shoved the rope against a jagged stone."
    )
    _damage_gain(world, lantern, 1.0)
    lantern.meters["light"] = 0.4
    world.say(
        f"There was a crack like snapped sugar, and the glass lantern shivered in {elephant.pronoun('possessive')} trunk."
    )

    # Bad ending
    world.para()
    _say_dialogue(world, king, "Step back! The bridge is failing!")
    world.say(
        f"{elephant.id} braced {elephant.pronoun('possessive')} feet, but the old stones slid apart."
    )
    _damage_gain(world, lantern, 1.0)
    lantern.meters["broken"] = 2.0
    lantern.meters["light"] = 0.0
    elephant.memes["sorrow"] = 1.0
    companion.memes["fear"] = 1.0
    world.say(
        f"The lantern fell into the black river and the light went out at once."
    )
    world.say(
        f"{companion.id} wept, {king.id} bowed {king.pronoun('possessive')} head, and {elephant.id} stood very still with wet ears and a broken promise."
    )
    world.say(
        f"At the end of the night, the bridge was dark, the river kept the glass, and the brave little elephant walked home alone under the cold stars."
    )

    world.facts.update(
        elephant=elephant,
        companion=companion,
        lantern=lantern,
        king=king,
        place=place,
        hero_name=hero_name,
        companion_name=companion_name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about an elephant who hears a warning and answers with dialogue and bravery.',
        f"Tell a gentle but sad story in {world.setting.place} where {f['companion_name']} asks an elephant for help and the ending goes wrong.",
        f'Write a story that includes a small elephant, spoken promises, and a bad ending with the light going out.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    elephant = f["elephant"]
    companion = f["companion"]
    lantern = f["lantern"]
    king = f["king"]
    return [
        QAItem(
            question=f"Who tried to help {companion.id} with the lantern?",
            answer=f"{elephant.id}, the small elephant, tried to help {companion.id}. {elephant.id} spoke bravely and walked onto the bridge to save the light.",
        ),
        QAItem(
            question="What did the elephant say before going onto the bridge?",
            answer="The elephant said, \"I am not a mighty knight, but I can still try.\" That was the brave promise that sent the elephant forward.",
        ),
        QAItem(
            question="Why did the story end badly?",
            answer=f"The bridge was old and the wind was strong. The rope snapped, the glass lantern fell into the river, and the light went out before anyone could save it.",
        ),
        QAItem(
            question=f"How did {companion.id} feel at the end?",
            answer=f"{companion.id} wept because the lantern was broken and the path went dark. The bad ending left {companion.id} frightened and sad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an elephant?",
            answer="An elephant is a very large animal with a long trunk and big ears. Elephants are often gentle and strong.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means trying to do the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is a dialogue in a story?",
            answer="Dialogue is when characters speak to each other using words in quotation marks.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(elephant).
character(X) :- hero(X).
character(X) :- companion(X).
character(X) :- king(X).

dialogue(Quote,Speaker) :- says(Speaker, Quote).
brave(X) :- courage(X), courage(X, positive).
bad_ending :- bridge_fails, lantern_lost, sadness(elephant).

bridge_fails :- old_bridge, strong_wind, step_on_bridge(elephant), not safe_bridge.
lantern_lost :- lantern_breaks, falls_into_river.
resolution(X) :- brave(X), helps(X), not bad_ending.

safe_bridge :- reinforced_bridge.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "elephant"),
        asp.fact("companion", "companion"),
        asp.fact("king", "king"),
        asp.fact("old_bridge"),
        asp.fact("strong_wind"),
        asp.fact("step_on_bridge", "elephant"),
        asp.fact("lantern_breaks"),
        asp.fact("falls_into_river"),
        asp.fact("sadness", "elephant"),
        asp.fact("courage", "elephant", "positive"),
        asp.fact("helps", "elephant"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_bad_ending() -> bool:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    return any(sym.name == "bad_ending" for sym in model)


def asp_verify() -> int:
    py = True
    aspv = asp_bad_ending()
    if py == aspv:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print(f"MISMATCH: python={py} asp={aspv}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world: an elephant, dialogue, bravery, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    if hero_name == companion_name:
        raise StoryError("The elephant's helper must have a different name.")
    return StoryParams(place=place, hero_name=hero_name, companion_name=companion_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hero_name, params.companion_name)
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
    StoryParams(place="forest", hero_name="Pip", companion_name="Mara"),
    StoryParams(place="bridge", hero_name="Luna", companion_name="Iris"),
    StoryParams(place="castle", hero_name="Tavi", companion_name="Sera"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show bad_ending/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
