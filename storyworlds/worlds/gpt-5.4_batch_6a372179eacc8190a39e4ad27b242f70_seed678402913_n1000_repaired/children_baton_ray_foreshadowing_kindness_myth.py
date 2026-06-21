#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/children_baton_ray_foreshadowing_kindness_myth.py
==============================================================================

A standalone storyworld in a small myth-like domain: at dawn, children carry a
ceremonial baton to greet the sun's first ray. In this village, elders say the
ray does not strike by accident. It falls where kindness is needed first.

The world model turns that saying into simulation: a dawn omen points to a
place, a creature or person there has a concrete need, and the chosen kindness
must actually fit that need. The baton matters physically too: it can lift,
bridge, reflect light, and steady a hand, but only some uses are reasonable for
some problems. The first ray foreshadows the trouble; the children's kindness
resolves it.

Run it
------
    python storyworlds/worlds/gpt-5.4/children_baton_ray_foreshadowing_kindness_myth.py
    python storyworlds/worlds/gpt-5.4/children_baton_ray_foreshadowing_kindness_myth.py --omen reeds --need nestling --kindness lift_branch
    python storyworlds/worlds/gpt-5.4/children_baton_ray_foreshadowing_kindness_myth.py --need goat_kid --kindness share_water
    python storyworlds/worlds/gpt-5.4/children_baton_ray_foreshadowing_kindness_myth.py --all
    python storyworlds/worlds/gpt-5.4/children_baton_ray_foreshadowing_kindness_myth.py --qa --json
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
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Omen:
    id: str
    place: str
    sight: str
    path: str
    myth_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    being_label: str
    being_phrase: str
    type: str
    place: str
    trouble: str
    pain: str
    relief: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Kindness:
    id: str
    method: str
    body: str
    proof: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notice_need(world: World) -> list[str]:
    child = world.get("child")
    being = world.get("being")
    if child.meters["at_need_place"] < THRESHOLD or being.meters["in_need"] < THRESHOLD:
        return []
    sig = ("noticed_need",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["concern"] += 1
    return ["__noticed__"]


def _r_kindness_heals(world: World) -> list[str]:
    child = world.get("child")
    being = world.get("being")
    baton = world.get("baton")
    if child.meters["helping"] < THRESHOLD or baton.meters["used_kindly"] < THRESHOLD:
        return []
    if being.meters["in_need"] < THRESHOLD:
        return []
    sig = ("kindness_heals",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    being.meters["in_need"] = 0.0
    being.meters["comfort"] += 1
    child.memes["joy"] += 1
    child.memes["mercy"] += 1
    baton.memes["honor"] += 1
    return ["__helped__"]


RULES = [
    Rule(name="notice_need", tag="social", apply=_r_notice_need),
    Rule(name="kindness_heals", tag="social", apply=_r_kindness_heals),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def need_matches_omen(omen: Omen, need: Need) -> bool:
    return omen.id == need.place


def kindness_fits_need(kindness: Kindness, need: Need) -> bool:
    return need.id in kindness.needs


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for omen_id, omen in OMENS.items():
        for need_id, need in NEEDS.items():
            if not need_matches_omen(omen, need):
                continue
            for kindness_id, kindness in KINDNESSES.items():
                if kindness_fits_need(kindness, need):
                    combos.append((omen_id, need_id, kindness_id))
    return combos


@dataclass
class StoryParams:
    omen: str
    need: str
    kindness: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    elder_title: str
    baton_name: str
    seed: Optional[int] = None


def dawn_opening(world: World, child: Entity, friend: Entity, elder: Entity, baton: Entity) -> None:
    world.say(
        f"In the days when dawn was said to walk the earth on quiet feet, the children "
        f"of Sunstep village climbed the shrine path each morning with {baton.phrase}."
    )
    world.say(
        f"That day {child.id} and {friend.id} carried it between them while {elder.label_word} "
        f"followed with a basket of laurel leaves."
    )
    world.say(
        f'"Remember," said {elder.label_word}, "the first ray chooses its own road. '
        f'Where it rests, mercy is waiting."'
    )


def foreshadow(world: World, child: Entity, friend: Entity, omen: Omen) -> None:
    child.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    baton = world.get("baton")
    baton.meters["raised"] += 1
    world.say(
        f"When the rim of the sun rose, a thin ray touched the gold on the baton and "
        f"ran from it like a bright finger. It did not scatter over the stones."
    )
    world.say(f"It slipped instead toward {omen.sight}.")
    world.say(omen.myth_line)
    world.facts["foreshadowed_place"] = omen.place


def hurry_or_heed(world: World, child: Entity, friend: Entity, omen: Omen) -> None:
    friend.memes["eagerness"] += 1
    world.say(
        f'{friend.id} almost laughed with surprise. "The bell is above us," '
        f'{friend.pronoun()} said. "If we hurry, we can still reach the top first."'
    )
    world.say(
        f"But {child.id} kept looking at the ray on {omen.place}. The old saying felt "
        f"less like a story and more like a hand pointing."
    )


def approach_need(world: World, child: Entity, friend: Entity, need: Need, omen: Omen) -> None:
    child = world.get("child")
    being = world.get("being")
    child.meters["at_need_place"] += 1
    propagate(world, narrate=False)
    world.say(f"So the children followed {omen.path}.")
    world.say(
        f"There they found {need.being_phrase} {need.trouble}. {need.pain}"
    )


def choose_kindness(world: World, child: Entity, friend: Entity, kindness: Kindness, need: Need) -> None:
    baton = world.get("baton")
    child.meters["helping"] += 1
    baton.meters["used_kindly"] += 1
    world.say(
        f"{child.id} did not set the baton down as a prize. {child.pronoun().capitalize()} "
        f"used it as {kindness.method}."
    )
    world.say(kindness.body.format(
        child=child.id,
        friend=friend.id,
        being=need.being_label,
        baton=baton.label_word,
    ))
    propagate(world, narrate=False)


def blessing_end(world: World, child: Entity, friend: Entity, elder: Entity, kindness: Kindness, need: Need) -> None:
    baton = world.get("baton")
    being = world.get("being")
    world.say(
        f"{need.relief} {kindness.proof.format(being=need.being_label)}"
    )
    world.say(
        f"When the children finally reached the shrine, they were late for the bell, "
        f"but {elder.label_word} only smiled."
    )
    world.say(
        f'"The sun loses nothing by waiting for kindness," {elder.label_word} said. '
        f'Another ray rested on {baton.phrase}, and the gold seemed warmer than before.'
    )
    world.say(
        f"From then on, the children of Sunstep would remember that morning: the first ray, "
        f"the guiding baton, and {need.lesson}"
    )
    world.facts["helped"] = being.meters["comfort"] >= THRESHOLD


def tell(params: StoryParams) -> World:
    if params.omen not in OMENS:
        raise StoryError(f"(Unknown omen: {params.omen})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.kindness not in KINDNESSES:
        raise StoryError(f"(Unknown kindness: {params.kindness})")

    omen = OMENS[params.omen]
    need = NEEDS[params.need]
    kindness = KINDNESSES[params.kindness]

    if not need_matches_omen(omen, need):
        raise StoryError(explain_rejection(omen, need, kindness))
    if not kindness_fits_need(kindness, need):
        raise StoryError(explain_rejection(omen, need, kindness))

    world = World()
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        role="child",
        traits=["gentle"],
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_gender,
        label=params.friend_name,
        role="friend",
        traits=["quick"],
    ))
    elder = world.add(Entity(
        id=params.elder_title,
        kind="character",
        type="woman" if params.elder_title == "Grandmother Ione" else "man",
        label=params.elder_title,
        role="elder",
    ))
    baton = world.add(Entity(
        id="baton",
        kind="thing",
        type="baton",
        label=params.baton_name,
        phrase=f"the {params.baton_name}",
        role="baton",
        tags={"baton", "sun"},
    ))
    being = world.add(Entity(
        id="being",
        kind="thing",
        type=need.type,
        label=need.being_label,
        phrase=need.being_phrase,
        role="being",
    ))
    being.meters["in_need"] = 1
    world.facts.update(
        omen=omen,
        need=need,
        kindness=kindness,
        child=child,
        friend=friend,
        elder=elder,
        baton=baton,
        being=being,
    )

    dawn_opening(world, child, friend, elder, baton)
    world.para()
    foreshadow(world, child, friend, omen)
    hurry_or_heed(world, child, friend, omen)
    world.para()
    approach_need(world, child, friend, need, omen)
    choose_kindness(world, child, friend, kindness, need)
    world.para()
    blessing_end(world, child, friend, elder, kindness, need)
    return world


OMENS = {
    "reeds": Omen(
        id="reeds",
        place="the reeds by the spring",
        sight="the reeds by the spring, where dew hung like silver beads",
        path="the mossy steps down to the spring",
        myth_line='The ray lay there so steadily that even the wind seemed to hush around it.',
        tags={"spring", "reeds", "ray"},
    ),
    "bridge": Omen(
        id="bridge",
        place="the little bridge over the rill",
        sight="the little bridge over the rill, where water talked under the planks",
        path="the fig path that bent toward the rill",
        myth_line='It shone on one narrow board as if the sun had drawn a line there before anyone spoke.',
        tags={"bridge", "water", "ray"},
    ),
    "olive": Omen(
        id="olive",
        place="the old olive tree below the shrine wall",
        sight="the old olive tree below the shrine wall, with pale roots showing through the earth",
        path="the dusty curve beneath the shrine wall",
        myth_line='The ray trembled in the leaves first, then settled at the roots like a quiet answer.',
        tags={"olive", "tree", "ray"},
    ),
}

NEEDS = {
    "nestling": Need(
        id="nestling",
        being_label="a fallen nestling",
        being_phrase="a fallen nestling",
        type="bird",
        place="reeds",
        trouble="with one wing tangled in a hook of river grass",
        pain="Its small beak opened and closed, and the reeds shook each time it tried to free itself.",
        relief="Soon the nestling was loose and safe in the children's cupped hands.",
        lesson="that the gods hear songs more gladly from hands that help than from hands that only hurry",
        tags={"bird", "reeds", "kindness"},
    ),
    "goat_kid": Need(
        id="goat_kid",
        being_label="a goat kid",
        being_phrase="a goat kid from the lower pens",
        type="goat",
        place="bridge",
        trouble="with one front hoof caught between two bridge boards",
        pain="It gave a thin, frightened cry each time it pulled, and the stream flashed helplessly below.",
        relief="Soon the hoof was free, and the goat kid sprang to the bank in a scatter of bright drops.",
        lesson="that bright things are given to children not for boasting, but for making a hard place gentler",
        tags={"goat", "bridge", "kindness"},
    ),
    "old_man": Need(
        id="old_man",
        being_label="an old fig seller",
        being_phrase="an old fig seller",
        type="man",
        place="olive",
        trouble="sitting at the roots with his basket spilled and his ankle trembling from a twist",
        pain="Purple figs had rolled into the dust, and he could only reach the nearest ones.",
        relief="Soon the figs were gathered again, and the old man rose slowly with the children beside him.",
        lesson="that even a sun-marked baton shines brightest when it becomes a staff for someone weary",
        tags={"elder", "olive", "kindness"},
    ),
}

KINDNESSES = {
    "lift_branch": Kindness(
        id="lift_branch",
        method="a gentle lever to raise the snagging grass away from the bird's wing",
        body="{child} steadied the grass with the baton while {friend} slipped careful fingers under the wing and eased it free.",
        proof="The little breast stopped fluttering so wildly, and {being} blinked in the new light.",
        needs={"nestling"},
        tags={"baton", "lever", "bird"},
    ),
    "bridge_gap": Kindness(
        id="bridge_gap",
        method="a brace across the loose boards so the trapped hoof could be turned safely",
        body="{child} laid the baton across the gap, and {friend} held the frightened {being} still until the hoof could be lifted and turned.",
        proof="For one breath it stood trembling, then {being} bounded away and looked back once as if in thanks.",
        needs={"goat_kid"},
        tags={"baton", "bridge", "goat"},
    ),
    "staff_support": Kindness(
        id="staff_support",
        method="a staff for the old man's shaking hand while the spilled figs were gathered",
        body="{child} placed the baton in the old man's hand, and {friend} knelt in the dust to gather the figs one by one back into the basket.",
        proof="The old man leaned on it, and the pain in his face eased enough for a smile.",
        needs={"old_man"},
        tags={"baton", "staff", "elder"},
    ),
}

GIRL_NAMES = ["Thaleia", "Mira", "Eleni", "Daphne", "Nysa", "Clio"]
BOY_NAMES = ["Theron", "Ivo", "Leander", "Phaon", "Maron", "Cyros"]
ELDERS = ["Grandmother Ione", "Old Nereus"]
BATONS = ["sun baton", "laurel baton", "golden baton"]


CURATED = [
    StoryParams(
        omen="reeds",
        need="nestling",
        kindness="lift_branch",
        child_name="Daphne",
        child_gender="girl",
        friend_name="Theron",
        friend_gender="boy",
        elder_title="Grandmother Ione",
        baton_name="sun baton",
    ),
    StoryParams(
        omen="bridge",
        need="goat_kid",
        kindness="bridge_gap",
        child_name="Leander",
        child_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        elder_title="Old Nereus",
        baton_name="golden baton",
    ),
    StoryParams(
        omen="olive",
        need="old_man",
        kindness="staff_support",
        child_name="Clio",
        child_gender="girl",
        friend_name="Cyros",
        friend_gender="boy",
        elder_title="Grandmother Ione",
        baton_name="laurel baton",
    ),
]


def explain_rejection(omen: Omen, need: Need, kindness: Kindness) -> str:
    if not need_matches_omen(omen, need):
        return (
            f"(No story: the omen points to {omen.place}, but the need '{need.id}' belongs at "
            f"a different place. In this world, the first ray must foreshadow the true location "
            f"of the kindness.)"
        )
    if not kindness_fits_need(kindness, need):
        return (
            f"(No story: kindness '{kindness.id}' does not sensibly solve '{need.id}'. "
            f"The baton must be used in a way that truly helps the being in need.)"
        )
    return "(No story: this combination is not reasonable.)"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


KNOWLEDGE = {
    "ray": [
        (
            "What is a ray of sunlight?",
            "A ray of sunlight is a narrow line of light from the sun. When it slips through leaves or over stones, it can make one place look bright and special."
        )
    ],
    "baton": [
        (
            "What is a baton?",
            "A baton is a rod or staff that someone carries in the hand. In stories and ceremonies, it can be a sign of duty or a tool used with care."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that explains the world with wonder. Myths often speak about signs, promises, and lessons people remember."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing that someone is hurting or needs help, and then doing something gentle and useful. A kind act is not just a feeling; it changes what happens next."
        )
    ],
    "bird": [
        (
            "Why should you be gentle with a small bird?",
            "A small bird has light bones and can be hurt easily. Gentle hands help it feel safe instead of more frightened."
        )
    ],
    "goat": [
        (
            "Why might an animal struggle when it is trapped?",
            "An animal does not understand what is happening and wants to get free fast. That fear can make it pull harder and get more tangled."
        )
    ],
    "elder": [
        (
            "Why is it kind to help an old person stand?",
            "An old person may hurt more easily or move more slowly. A steady hand or staff can make standing safe again."
        )
    ],
}
KNOWLEDGE_ORDER = ["myth", "ray", "baton", "kindness", "bird", "goat", "elder"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    need = world.facts["need"]
    omen = world.facts["omen"]
    kindness = world.facts["kindness"]
    return [
        'Write a short myth-like story for a 3-to-5-year-old that includes the words "children", "baton", and "ray".',
        f"Tell a gentle myth in which children see the sun's first ray rest on {omen.place}, understand it as a sign, and use a baton in kindness to help {need.being_label}.",
        f"Write a story with foreshadowing where {child.id} and {friend.id} are almost in a hurry, but the omen of light leads them to {kindness.id} and a merciful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    need = world.facts["need"]
    omen = world.facts["omen"]
    kindness = world.facts["kindness"]
    baton = world.facts["baton"]
    being = world.facts["being"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about the children {child.id} and {friend.id}, who carried {baton.phrase} at dawn. It is also about {elder.label_word}, who taught them to pay attention to the first ray."
        ),
        (
            "What was the foreshadowing sign in the story?",
            f"The foreshadowing sign was the first ray of sunlight resting on {omen.place}. That sign mattered because the elder had already said the ray would show where mercy was waiting."
        ),
        (
            f"Why did {child.id} stop hurrying upward?",
            f"{child.id} stopped because the ray looked purposeful, not random. The old saying suddenly felt true, so {child.pronoun()} followed the light instead of racing to the bell."
        ),
        (
            f"What trouble did the children find?",
            f"They found {need.being_phrase} {need.trouble}. {need.pain}"
        ),
        (
            f"How did the baton help {need.being_label}?",
            f"The baton helped because it was used as {kindness.method}. It mattered physically, not just ceremonially, and that is what let the children solve the problem gently."
        ),
        (
            "How did the story end, and what changed?",
            f"It ended with the need relieved: {need.relief} The children arrived late to the shrine, but they understood that kindness was more important than being first."
        ),
    ]
    if being.meters["comfort"] >= THRESHOLD:
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned {need.lesson}. The warm ray on the baton at the end shows that the morning itself seemed to bless their choice."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"myth", "ray", "baton", "kindness"}
    need = world.facts["need"]
    if need.id == "nestling":
        tags.add("bird")
    elif need.id == "goat_kid":
        tags.add("goat")
    elif need.id == "old_man":
        tags.add("elder")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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


ASP_RULES = r"""
need_matches(O, N) :- omen_place(O, P), need_place(N, P).
kindness_fits(K, N) :- kindness(K), helps(K, N).
valid(O, N, K) :- omen(O), need(N), kindness(K), need_matches(O, N), kindness_fits(K, N).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("omen_place", omen_id, omen.id))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("need_place", need_id, need.place))
    for kindness_id, kindness in KINDNESSES.items():
        lines.append(asp.fact("kindness", kindness_id))
        for need_id in sorted(kindness.needs):
            lines.append(asp.fact("helps", kindness_id, need_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_test() -> None:
    params = resolve_params(build_parser().parse_args([]), random.Random(123))
    sample = generate(params)
    if not sample.story or "children" not in sample.story.lower() or "baton" not in sample.story.lower():
        raise StoryError("(Smoke test failed: generated story missing required shape or words.)")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
    try:
        _smoke_test()
        for params in CURATED:
            sample = generate(params)
            if not sample.story:
                raise StoryError("(Smoke test failed: empty story.)")
        print(f"OK: smoke-tested generation on {len(CURATED) + 1} scenarios.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Myth-like storyworld: children carry a baton at dawn, the first ray foreshadows where kindness is needed."
    )
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.omen and args.need:
        omen = OMENS[args.omen]
        need = NEEDS[args.need]
        kindness = KINDNESSES[args.kindness] if args.kindness else next(iter(KINDNESSES.values()))
        if not need_matches_omen(omen, need):
            raise StoryError(explain_rejection(omen, need, kindness))
    if args.need and args.kindness:
        omen = OMENS[args.omen] if args.omen else next(iter(OMENS.values()))
        need = NEEDS[args.need]
        kindness = KINDNESSES[args.kindness]
        if not kindness_fits_need(kindness, need):
            raise StoryError(explain_rejection(omen, need, kindness))

    combos = [
        combo for combo in valid_combos()
        if (args.omen is None or combo[0] == args.omen)
        and (args.need is None or combo[1] == args.need)
        and (args.kindness is None or combo[2] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    omen_id, need_id, kindness_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=child_name)
    elder_title = rng.choice(ELDERS)
    baton_name = rng.choice(BATONS)
    return StoryParams(
        omen=omen_id,
        need=need_id,
        kindness=kindness_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        elder_title=elder_title,
        baton_name=baton_name,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("omen", OMENS),
        ("need", NEEDS),
        ("kindness", KINDNESSES),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Unknown {field_name}: {value})")
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (omen, need, kindness) combos:\n")
        for omen_id, need_id, kindness_id in combos:
            print(f"  {omen_id:7} {need_id:10} {kindness_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.child_name} & {p.friend_name}: {p.need} at {p.omen} ({p.kindness})"
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
