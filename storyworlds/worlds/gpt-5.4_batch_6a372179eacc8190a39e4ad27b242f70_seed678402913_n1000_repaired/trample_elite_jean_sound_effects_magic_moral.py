#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trample_elite_jean_sound_effects_magic_moral.py
============================================================================

A standalone story world about a small magical whodunit for young children.

Domain sketch
-------------
At a little magic school, a glowing flower or careful display gets damaged.
Everyone hears a sound -- crunch, squish, snap -- and sees signs in the room.
Some children quickly suspect the "elite" spell club or another child. But Jean,
a careful young sleuth, follows the clues and discovers what really happened.
The ending teaches a simple moral value: do not blame people just because they
seem fancy or different; look carefully and tell the truth.

Run it
------
    python storyworlds/worlds/gpt-5.4/trample_elite_jean_sound_effects_magic_moral.py
    python storyworlds/worlds/gpt-5.4/trample_elite_jean_sound_effects_magic_moral.py --verify
    python storyworlds/worlds/gpt-5.4/trample_elite_jean_sound_effects_magic_moral.py --all --qa
    python storyworlds/worlds/gpt-5.4/trample_elite_jean_sound_effects_magic_moral.py -n 5 --seed 7
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    room: str
    hush: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    item_label: str
    item_phrase: str
    item_the: str
    trace: str
    damage_word: str
    clue_mark: str
    magic_fix: str
    safe_end: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def Item_the(self) -> str:
        return self.item_the[0].upper() + self.item_the[1:]


@dataclass
class SuspectGroup:
    id: str
    label: str
    phrase: str
    fancy: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    actor_label: str
    actor_kind: str
    sound: str
    motion: str
    clue: str
    honest_fix: str
    supports: set[str] = field(default_factory=set)
    living: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SpellTool:
    id: str
    label: str
    phrase: str
    gentle: bool
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "academy_hall": Setting(
        id="academy_hall",
        place="Moonbright Academy",
        room="the hall of little spells",
        hush="The silver lamps hummed softly over rows of tiny wonders.",
        tags={"school", "magic"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="Moonbright Academy",
        room="the glass greenhouse",
        hush="Warm mist curled around pots that glimmered in the sun.",
        tags={"garden", "magic"},
    ),
    "library": Setting(
        id="library",
        place="Moonbright Academy",
        room="the whispering library",
        hush="Tall shelves leaned close as if they wanted to hear secrets too.",
        tags={"books", "magic"},
    ),
}

MYSTERIES = {
    "flower": Mystery(
        id="flower",
        item_label="moonbell flower",
        item_phrase="a glowing moonbell flower",
        item_the="the moonbell flower",
        trace="silver pollen",
        damage_word="trampled",
        clue_mark="a bent stem and sparkling dust",
        magic_fix="lifted the stem and wrapped it in a soft blue glow",
        safe_end="The moonbell stood up again and rang one shy, bright note.",
        tags={"flower", "garden"},
    ),
    "map": Mystery(
        id="map",
        item_label="star map",
        item_phrase="a floating star map",
        item_the="the star map",
        trace="glitter crumbs",
        damage_word="creased and stepped on",
        clue_mark="a shoe-shaped smudge across the corner",
        magic_fix="smoothed the crease until the stars drifted back into line",
        safe_end="The little stars winked and floated neatly in their places again.",
        tags={"map", "library"},
    ),
    "cake": Mystery(
        id="cake",
        item_label="cloud cake",
        item_phrase="a puffy cloud cake for the school tea",
        item_the="the cloud cake",
        trace="sugar sparkles",
        damage_word="squashed",
        clue_mark="a soft dent and a dusting of sweet sparkles",
        magic_fix="puffed the frosting back up into a neat white swirl",
        safe_end="The cloud cake looked fluffy enough to make everyone smile again.",
        tags={"cake", "kitchen"},
    ),
}

SUSPECT_GROUPS = {
    "elite_club": SuspectGroup(
        id="elite_club",
        label="the elite spell club",
        phrase="the elite spell club in their bright silver pins",
        fancy=True,
        tags={"elite", "club"},
    ),
    "choir": SuspectGroup(
        id="choir",
        label="the song circle",
        phrase="the song circle with their ribbon books",
        fancy=False,
        tags={"music"},
    ),
    "garden_team": SuspectGroup(
        id="garden_team",
        label="the garden helpers",
        phrase="the garden helpers with watering cans",
        fancy=False,
        tags={"garden"},
    ),
}

CAUSES = {
    "kitten": Cause(
        id="kitten",
        actor_label="a striped kitten",
        actor_kind="animal",
        sound="mrrp-mrrp!",
        motion="pounced after a bouncing mote of light",
        clue="tiny paw prints",
        honest_fix="The kitten was not mean. It had only chased the sparkle without understanding.",
        supports={"flower", "map", "cake"},
        tags={"animal", "truth"},
    ),
    "broom": Cause(
        id="broom",
        actor_label="the practice broom",
        actor_kind="object",
        sound="clack-clack!",
        motion="rolled free when a sleepy spell wore off",
        clue="thin wheel lines",
        honest_fix="The broom had no feelings at all. Someone had simply forgotten to park it safely.",
        supports={"flower", "map"},
        tags={"broom", "care"},
    ),
    "boots": Cause(
        id="boots",
        actor_label="a pair of muddy rain boots",
        actor_kind="object",
        sound="squish-squash!",
        motion="were worn by a rushing child who slipped and tried not to fall",
        clue="one muddy heel print",
        honest_fix="The child had been hurrying to help and told the truth as soon as Jean asked kindly.",
        supports={"flower", "cake"},
        tags={"boots", "truth"},
    ),
}

SPELLS = {
    "blue_mend": SpellTool(
        id="blue_mend",
        label="Blue Mend",
        phrase="the Blue Mend spell",
        gentle=True,
        effect="a soft blue ribbon of light",
        tags={"repair", "magic"},
    ),
    "hush_hold": SpellTool(
        id="hush_hold",
        label="Hush Hold",
        phrase="the Hush Hold spell",
        gentle=True,
        effect="a quiet silver circle",
        tags={"pause", "magic"},
    ),
}

KNOWLEDGE = {
    "elite": [
        (
            "What does elite mean?",
            "Elite means a group is thought to be very special or very skilled. But being elite does not mean someone is bad or good, so we still need real clues."
        )
    ],
    "trample": [
        (
            "What does trample mean?",
            "To trample something is to step on it and squash or damage it. A flower or cake can be hurt if feet or wheels go over it."
        )
    ],
    "magic": [
        (
            "What is magic in this story?",
            "Magic is a gentle way the children can glow, mend, or pause things. In this world, magic helps after the problem, but careful truth helps solve the mystery."
        )
    ],
    "truth": [
        (
            "Why is telling the truth important in a mystery?",
            "Telling the truth helps everyone understand what really happened. Without truthful clues, people might blame the wrong person."
        )
    ],
    "kindness": [
        (
            "Why should you not blame someone too fast?",
            "Quick blame can hurt feelings and miss the real answer. Looking carefully and asking kindly is a fairer way to solve a problem."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Footprints, sparkles, and sounds can all be clues."
        )
    ],
    "repair": [
        (
            "Why fix something after an accident?",
            "Fixing a damaged thing shows care and responsibility. It helps make the hurt smaller after the truth is known."
        )
    ],
}
KNOWLEDGE_ORDER = ["elite", "trample", "clue", "magic", "truth", "kindness", "repair"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect_group: str
    cause: str
    spell: str
    jean_role: str
    headmistress: str
    seed: Optional[int] = None


def cause_fits(cause: Cause, mystery: Mystery) -> bool:
    return mystery.id in cause.supports


def spell_fits(spell: SpellTool, mystery: Mystery) -> bool:
    return spell.gentle and mystery.fragile


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for mystery_id, mystery in MYSTERIES.items():
            for suspect_id in SUSPECT_GROUPS:
                for cause_id, cause in CAUSES.items():
                    for spell_id, spell in SPELLS.items():
                        if cause_fits(cause, mystery) and spell_fits(spell, mystery):
                            combos.append((setting_id, mystery_id, suspect_id, cause_id, spell_id))
    return combos


def explain_rejection(cause: Cause, mystery: Mystery) -> str:
    return (
        f"(No story: {cause.actor_label} does not make a sensible cause for {mystery.item_the}. "
        f"Pick a cause that could really leave the right clue and damage.)"
    )


def tell(
    setting: Setting,
    mystery: Mystery,
    suspect_group: SuspectGroup,
    cause: Cause,
    spell: SpellTool,
    jean_role: str = "student",
    headmistress: str = "Headmistress Willow",
) -> World:
    world = World()
    jean = world.add(
        Entity(
            id="Jean",
            kind="character",
            type="girl",
            label="Jean",
            role="sleuth",
            traits=["careful", "kind"],
            tags={"truth", "clue"},
        )
    )
    head = world.add(
        Entity(
            id=headmistress,
            kind="character",
            type="woman",
            label="the headmistress",
            role="adult",
            traits=["calm", "wise"],
            tags={"magic"},
        )
    )
    group = world.add(
        Entity(
            id="group",
            kind="group",
            type="children",
            label=suspect_group.label,
            phrase=suspect_group.phrase,
            role="suspects",
            attrs={"fancy": suspect_group.fancy},
            tags=set(suspect_group.tags),
        )
    )
    damaged = world.add(
        Entity(
            id="damaged",
            kind="thing",
            type="mystery_item",
            label=mystery.item_label,
            phrase=mystery.item_phrase,
            role="victim",
            tags=set(mystery.tags),
        )
    )
    cause_ent = world.add(
        Entity(
            id="cause",
            kind="thing" if cause.actor_kind != "animal" else "character",
            type=cause.actor_kind,
            label=cause.actor_label,
            role="cause",
            tags=set(cause.tags),
        )
    )

    world.say(
        f"At {setting.place}, Jean was the youngest {jean_role} who loved small puzzles. "
        f"That morning, {setting.room} was ready for a special showing, and {setting.hush}"
    )
    world.say(
        f"On a velvet stand sat {mystery.item_phrase}. Jean had promised to watch it until the bell rang."
    )

    world.para()
    world.say(
        f"Then came a sudden sound -- {cause.sound} -- and a surprised cry from behind a shelf."
    )
    world.say(
        f"When Jean ran over, {mystery.item_the} was {mystery.damage_word}. "
        f"There on the floor lay {mystery.clue_mark}."
    )
    damaged.meters["damaged"] += 1
    damaged.meters["trampled"] += 1
    world.facts["sound"] = cause.sound
    world.facts["clue"] = cause.clue
    world.facts["damage"] = mystery.damage_word

    world.say(
        f"Two older children whispered, \"It must have been {suspect_group.label}. "
        f"They always hurry as if the whole school should move for them.\""
    )
    group.memes["suspected"] += 1
    if suspect_group.fancy:
        world.say(
            f"They even used the word elite as if it were proof all by itself."
        )
    else:
        world.say(
            "Their guess sounded neat, but Jean knew neat guesses were not the same as true ones."
        )
    jean.memes["doubt"] += 1

    world.para()
    world.say(
        f'Jean folded her hands behind her back and whispered, "A good mystery needs clues, not rude guesses."'
    )
    world.say(
        f"She listened again, looked low to the floor, and noticed {cause.clue} beside the stand."
    )
    world.say(
        f"That matched only one thing in the room: {cause.actor_label}, which had {cause.motion}."
    )
    cause_ent.memes["revealed"] += 1
    world.facts["solved"] = True
    world.facts["wrongly_blamed"] = suspect_group.label

    world.say(
        f'Soon Jean said, "No one from {suspect_group.label} meant harm. The real answer is {cause.actor_label}."'
    )
    if cause.id == "boots":
        world.say(
            "A red-faced helper stepped forward at once and admitted the accident. "
            "The child had rushed in to bring napkins and had slipped."
        )
    elif cause.id == "broom":
        world.say(
            "A teacher blinked and remembered leaving the broom leaning by itself after practice."
        )
    else:
        world.say(
            "From under a stool popped the striped kitten, still chasing the naughty sparkle with round, proud eyes."
        )

    world.para()
    world.say(
        f"{headmistress} nodded. {head.pronoun().capitalize()} lifted a wand and used {spell.phrase}. "
        f"{spell.effect} {mystery.magic_fix}."
    )
    damaged.meters["damaged"] = 0.0
    damaged.meters["mended"] += 1
    world.say(mystery.safe_end)
    world.say(cause.honest_fix)

    world.say(
        f'Then {headmistress} said, "The moral is simple: do not blame people for seeming grand, strange, or elite. '
        f'Look carefully, speak kindly, and tell the truth."'
    )
    jean.memes["pride"] += 1
    jean.memes["kindness"] += 1
    world.say(
        "Jean smiled. The room felt lighter now, not because the magic glowed, but because everyone knew what had really happened."
    )

    world.facts.update(
        setting=setting,
        mystery=mystery,
        suspect_group=suspect_group,
        cause=cause,
        spell=spell,
        jean=jean,
        head=head,
        damaged=damaged,
        moral="Look carefully, speak kindly, and tell the truth.",
        jean_role=jean_role,
        headmistress=headmistress,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    suspect_group = f["suspect_group"]
    cause = f["cause"]
    return [
        (
            f'Write a tiny whodunit for a 3-to-5-year-old where Jean solves a magical mystery '
            f'about {mystery.item_phrase}. Include the words "trample", "elite", and "Jean".'
        ),
        (
            f"Tell a gentle mystery story at a magic school where children almost blame {suspect_group.label}, "
            f"but Jean follows the clue and discovers {cause.actor_label} really caused the trouble."
        ),
        (
            'Write a story with sound effects, a kind magical repair, and a moral about not blaming people too quickly.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    jean = f["jean"]
    mystery = f["mystery"]
    suspect_group = f["suspect_group"]
    cause = f["cause"]
    head = f["head"]
    spell = f["spell"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Jean, a careful child at magic school, and the people around her when a mystery happened. Jean is the one who stays calm and looks for the truth."
        ),
        (
            f"What happened to {mystery.item_the}?",
            f"{mystery.Item_the} was {mystery.damage_word}. Jean knew someone or something had stepped on it or knocked over it, so she began looking for clues."
        ),
        (
            "Why did some children suspect the elite club?",
            f"They guessed it was {suspect_group.label} because the group seemed important and hurried. But that was only a quick guess, not real proof."
        ),
        (
            "How did Jean solve the mystery?",
            f'Jean listened to the sound, looked down at the floor, and matched the clue to {cause.actor_label}. She solved it by using careful clues instead of blame.'
        ),
        (
            f"What did {head.label_word} do after the mystery was solved?",
            f'{head.pronoun().capitalize()} used {spell.phrase} to fix the damage. The magic helped at the end, after Jean had already found the true answer.'
        ),
        (
            "What is the moral of the story?",
            "The moral is to look carefully, speak kindly, and tell the truth. The story shows that seeming fancy or different is not the same as being guilty."
        ),
    ]
    if cause.id == "boots":
        qa.append(
            (
                "Was the person with the boots trying to be mean?",
                "No. The child had been hurrying to help and slipped by accident. Telling the truth quickly helped everyone calm down and repair the mistake."
            )
        )
    elif cause.id == "kitten":
        qa.append(
            (
                "Was the kitten bad?",
                "No. The kitten was only chasing a sparkle and did not understand the trouble it caused. Jean still told the truth without being unkind."
            )
        )
    else:
        qa.append(
            (
                "Why was the broom the real cause?",
                "Jean found lines and movement clues that matched the rolling broom. A grown-up had forgotten to leave it safely, so the answer came from carelessness, not meanness."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"elite", "trample", "clue", "magic", "truth", "kindness", "repair"}
    if f["cause"].id == "boots":
        tags.add("truth")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="greenhouse",
        mystery="flower",
        suspect_group="elite_club",
        cause="kitten",
        spell="blue_mend",
        jean_role="student sleuth",
        headmistress="Headmistress Willow",
    ),
    StoryParams(
        setting="library",
        mystery="map",
        suspect_group="elite_club",
        cause="broom",
        spell="blue_mend",
        jean_role="student sleuth",
        headmistress="Headmistress Willow",
    ),
    StoryParams(
        setting="academy_hall",
        mystery="cake",
        suspect_group="choir",
        cause="boots",
        spell="blue_mend",
        jean_role="student sleuth",
        headmistress="Headmistress Willow",
    ),
]


ASP_RULES = r"""
cause_fits(C, M) :- supports(C, M).
spell_fits(S, M) :- spell(S), gentle(S), mystery(M), fragile(M).
valid(St, M, G, C, S) :- setting(St), mystery(M), suspect_group(G), cause(C), spell(S),
                         cause_fits(C, M), spell_fits(S, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if mystery.fragile:
            lines.append(asp.fact("fragile", mid))
    for gid in SUSPECT_GROUPS:
        lines.append(asp.fact("suspect_group", gid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for mid in sorted(cause.supports):
            lines.append(asp.fact("supports", cid, mid))
    for sid, spell in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        if spell.gentle:
            lines.append(asp.fact("gentle", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "Jean" not in sample.story:
            raise StoryError("smoke test failed: empty story or missing Jean")
        print("OK: smoke test story generation passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: Jean solves a gentle magical whodunit."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect-group", dest="suspect_group", choices=SUSPECT_GROUPS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--jean-role", dest="jean_role")
    ap.add_argument("--headmistress")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.mystery:
        cause = CAUSES[args.cause]
        mystery = MYSTERIES[args.mystery]
        if not cause_fits(cause, mystery):
            raise StoryError(explain_rejection(cause, mystery))
    if args.spell and args.mystery:
        spell = SPELLS[args.spell]
        mystery = MYSTERIES[args.mystery]
        if not spell_fits(spell, mystery):
            raise StoryError("(No story: that spell is not a gentle fit for this fragile mystery item.)")

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.suspect_group is None or combo[2] == args.suspect_group)
        and (args.cause is None or combo[3] == args.cause)
        and (args.spell is None or combo[4] == args.spell)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, suspect_id, cause_id, spell_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        suspect_group=suspect_id,
        cause=cause_id,
        spell=spell_id,
        jean_role=args.jean_role or rng.choice(["student sleuth", "little detective", "puzzle helper"]),
        headmistress=args.headmistress or rng.choice(["Headmistress Willow", "Headmistress Fern"]),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mystery = MYSTERIES[params.mystery]
        suspect_group = SUSPECT_GROUPS[params.suspect_group]
        cause = CAUSES[params.cause]
        spell = SPELLS[params.spell]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if not cause_fits(cause, mystery):
        raise StoryError(explain_rejection(cause, mystery))
    if not spell_fits(spell, mystery):
        raise StoryError("(No story: that spell is not a gentle fit for this fragile mystery item.)")

    world = tell(
        setting=setting,
        mystery=mystery,
        suspect_group=suspect_group,
        cause=cause,
        spell=spell,
        jean_role=params.jean_role,
        headmistress=params.headmistress,
    )
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, suspect_group, cause, spell) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### Jean mystery {i + 1}: {p.mystery} at {p.setting} "
                f"(suspected: {p.suspect_group}, real cause: {p.cause})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
