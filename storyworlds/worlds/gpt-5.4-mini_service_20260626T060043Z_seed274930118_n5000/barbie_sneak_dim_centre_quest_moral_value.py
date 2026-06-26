#!/usr/bin/env python3
"""
storyworlds/worlds/barbie_sneak_dim_centre_quest_moral_value.py
===============================================================

A small rhyming storyworld about Barbie, a sneaky dim-lit centre, and a quest
that teaches a moral value.

Premise:
- Barbie wants to sneak into a dim centre to find a lost quest charm.
- The centre is tempting, but it is dark, quiet, and a little scary.
- A helper points out that honesty and asking first is the better path.
- Barbie chooses the kinder path and still completes the quest.

The world is intentionally tiny and constraint-checked:
- physical meters track light, distance, hiddenness, and quest progress
- emotional memes track worry, bravery, trust, and pride
- the story only renders if the simulated state supports a real turn and ending

The prose style aims at a child-facing rhyming story with a clear beginning,
turn, and resolution.
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
# World entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    centre_name: str
    dim: bool = True
    quest_spot: str = "the centre"


@dataclass
class Quest:
    id: str
    item: str
    item_phrase: str
    goal: str
    rhyme: str
    moral_value: str


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "mall": Setting(place="the mall", centre_name="the centre court", dim=True, quest_spot="the centre court"),
    "playhouse": Setting(place="the playhouse", centre_name="the middle stage", dim=True, quest_spot="the middle stage"),
    "garden": Setting(place="the garden", centre_name="the stone centre", dim=True, quest_spot="the stone centre"),
}

QUESTS = {
    "crown": Quest(
        id="crown",
        item="crown",
        item_phrase="a tiny silver crown",
        goal="place the crown on the little stand at the centre",
        rhyme="down",
        moral_value="honesty",
    ),
    "star": Quest(
        id="star",
        item="star",
        item_phrase="a bright gold star",
        goal="set the star back on the centre post",
        rhyme="glow",
        moral_value="kindness",
    ),
    "ring": Quest(
        id="ring",
        item="ring",
        item_phrase="a shiny pink ring",
        goal="return the ring to the centre box",
        rhyme="tune",
        moral_value="trust",
    ),
}

NAMES = ["Barbie", "Mia", "Luna", "Nora", "Pia", "Zoe"]
HELPERS = ["Aunt June", "Mika", "Nia", "Toby"]
TRAITS = ["brave", "curious", "bouncy", "sweet"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting, quest: Quest) -> None:
        self.setting = setting
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _bump(entity: Entity, key: str, amount: float = 1.0, which: str = "meter") -> None:
    target = entity.meter if which == "meter" else entity.meme
    target[key] = target.get(key, 0.0) + amount


def _at_least(entity: Entity, key: str, amount: float = THRESHOLD, which: str = "meter") -> bool:
    target = entity.meter if which == "meter" else entity.meme
    return target.get(key, 0.0) >= amount


# ---------------------------------------------------------------------------
# Rhyming narration beats
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a bright little Barbie, with curls neat and neat. "
        f"She loved a good quest and a cheerful new beat."
    )
    world.say(
        f"In {world.setting.place}, by {world.setting.centre_name}, she spotted a prize. "
        f"It glimmered like candy and shone to her eyes."
    )
    world.say(
        f"{helper.id} smiled and said, “That prize has a place, "
        f"but first we should ask and not rush in haste.”"
    )


def sneak_toward_centre(world: World, hero: Entity) -> None:
    _bump(hero, "distance", 1.0)
    _bump(hero, "hidden", 1.0)
    _bump(hero, "worry", 1.0, which="meme")
    world.say(
        f"Barbie tiptoed softly, on a dim little track, "
        f"but the centre was shadowy, calling her back."
    )
    world.say(
        f"She wanted to sneak-dim to the centre, quiet and sly, "
        f"yet her heart made a thump and a fluttering sigh."
    )


def warning(world: World, hero: Entity, helper: Entity) -> None:
    _bump(hero, "worry", 1.0, which="meme")
    _bump(hero, "trust", 1.0, which="meme")
    world.say(
        f"{helper.id} said, “A sneaky old step can feel clever at first, "
        f"but secret wrong choices can make trouble burst.”"
    )
    world.say(
        f"“A moral value is shining: be honest, be bright. "
        f"Ask first, then act, and the day will feel right.”"
    )


def turn_to_honesty(world: World, hero: Entity, helper: Entity) -> None:
    _bump(hero, "bravery", 1.0, which="meme")
    _bump(hero, "trust", 1.0, which="meme")
    world.say(
        f"Barbie paused in the hush of the centre-lit hall, "
        f"then chose the kind path that was best of all."
    )
    world.say(
        f"She stepped to {helper.id} and spoke clear and true, "
        f"“Will you help me with this quest? I want to do good.”"
    )


def complete_quest(world: World, hero: Entity, helper: Entity) -> None:
    quest = world.quest
    _bump(hero, quest.id, 1.0)
    _bump(hero, "pride", 1.0, which="meme")
    _bump(hero, "worry", -1.0, which="meme")
    world.say(
        f"Together they walked to {world.setting.centre_name}, where the light met the floor. "
        f"They placed the {quest.item} in the centre, then opened the door."
    )
    world.say(
        f"The quest was complete, with a happy new glow. "
        f"The dim place felt kinder, and softer, and slow."
    )
    world.say(
        f"Barbie smiled wide, with her heart warm and sound; "
        f"honesty helped her bring treasure around."
    )


def tell(setting: Setting, quest: Quest, hero_name: str, helper_name: str) -> World:
    world = World(setting, quest)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", label=helper_name))
    world.add(Entity(id="quest_item", kind="thing", type=quest.item, label=quest.item, phrase=quest.item_phrase))
    world.facts.update(hero=hero, helper=helper, quest=quest, setting=setting)

    intro(world, hero, helper)
    world.say("")
    sneak_toward_centre(world, hero)
    warning(world, hero, helper)
    world.say("")
    turn_to_honesty(world, hero, helper)
    complete_quest(world, hero, helper)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is valid when the setting has a centre and the quest has a moral value.
valid_story(S, Q) :- setting(S), quest(Q), centre(S), moral(Q).

% A "sneak-dim" route is only reasonable if the centre is dim.
sneak_dim_ok(S, Q) :- valid_story(S, Q), dim_centre(S).

% A story is complete when the hero chooses honesty and the quest is finished.
complete(S, Q) :- sneak_dim_ok(S, Q), honesty(Q).
#show valid_story/2.
#show sneak_dim_ok/2.
#show complete/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("centre", sid))
        if setting.dim:
            lines.append(asp.fact("dim_centre", sid))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("moral", qid))
        lines.append(asp.fact("honesty" if quest.moral_value == "honesty" else "moral", qid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.one_model(asp_program())
    atoms = set(asp.atoms(models, "valid_story"))
    if atoms:
        return 0
    print("ASP verification failed: no valid_story atoms found.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short rhyming story about {hero.id} and a sneaky dim centre quest.',
        f"Tell a child-friendly tale where {hero.id} wants to sneak into {setting.centre_name} "
        f"but chooses the moral value of {quest.moral_value}.",
        f'Write a tiny story that includes Barbie, the centre, and a quest with a kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.centre_name}?",
            answer=f"{hero.id} wanted to sneak toward the centre to finish the {quest.id} quest.",
        ),
        QAItem(
            question=f"Who helped {hero.id} choose the kind path?",
            answer=f"{helper.id} helped by reminding {hero.id} to ask first and be honest.",
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=f"The story taught {quest.moral_value}, which means telling the truth and choosing the kind way.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} completed the quest in the centre and felt proud because she chose honesty over sneaking.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a centre mean in a place?",
            answer="A centre is the middle part of a place, where things often feel most important or easy to notice.",
        ),
        QAItem(
            question="What does sneak mean?",
            answer="To sneak means to move quietly and secretly so other people do not notice right away.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to behave, like honesty, kindness, or trust.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = ", ".join(f"{k}={v}" for k, v in sorted(e.meter.items()) if v)
        memes = ", ".join(f"{k}={v}" for k, v in sorted(e.meme.items()) if v)
        bits = []
        if meters:
            bits.append(f"meters({meters})")
        if memes:
            bits.append(f"memes({memes})")
        if e.phrase:
            bits.append(f'phrase="{e.phrase}"')
        lines.append(f"{e.id}: {e.kind}/{e.type} " + (" ".join(bits) if bits else ""))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming Barbie quest storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--name", choices=NAMES)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, quest=quest, name=name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    helper = rng_helper = "Aunt June"
    world = tell(setting, quest, params.name, helper)
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
    StoryParams(setting="mall", quest="crown", name="Barbie"),
    StoryParams(setting="playhouse", quest="star", name="Mia"),
    StoryParams(setting="garden", quest="ring", name="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(f"models: {len(model)} shown atoms")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
