#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py
=====================================================================

A small fable-like storyworld about a found keepsake in a forest nook, a jury of
animals, and a flashback whose remembered sound helps reveal the truth.

The domain is intentionally narrow and constraint-checked: a finder discovers a
small keepsake tucked in a nook, wants to keep it, and is challenged by another
animal who says it was hidden there earlier. A woodland jury listens. The owner
recounts a brief flashback about the day the keepsake was hidden, complete with
sound effects, and the jury tests that memory in the present. Once the facts are
clear, the finder either returns the keepsake or the owner warmly shares its use.

Run it
------
    python storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py
    python storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py --item bell --nook oak_nook
    python storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py --item pipe --nook root_nook
    python storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py --all
    python storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py --qa
    python storyworlds/worlds/gpt-5.4/nook_jury_flashback_sound_effects_fable.py --verify
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
CERTAINTY_NEEDED = 2
HONEST_TRAITS = {"honest", "meek", "fair"}
GENEROUS_TRAITS = {"kind", "patient", "gentle"}
WISE_JURORS = {"owl", "tortoise", "badger"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def be(self) -> str:
        return "was"

    def have(self) -> str:
        return "had"


@dataclass
class Nook:
    id: str
    label: str
    phrase: str
    size: str
    dry: bool
    place_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    size: str
    needs_dry: bool
    sound: str
    action: str
    test_line: str
    memory_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalSpec:
    id: str
    label: str
    title: str
    traits: list[str]
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    nook: str
    item: str
    finder: str
    owner: str
    juror: str
    storm: str
    seed: Optional[int] = None


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


def _r_evidence(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    owner = world.get("owner")
    finder = world.get("finder")
    juror = world.get("juror")
    if item.meters["sound_match"] >= THRESHOLD and owner.meters["memory_told"] >= THRESHOLD:
        sig = ("evidence",)
        if sig not in world.fired:
            world.fired.add(sig)
            juror.meters["certainty"] += 2
            owner.memes["hope"] += 1
            finder.memes["doubt"] += 1
            out.append("__evidence__")
    return out


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    finder = world.get("finder")
    juror = world.get("juror")
    if juror.meters["certainty"] >= CERTAINTY_NEEDED and finder.memes["covet"] >= THRESHOLD:
        sig = ("shame",)
        if sig not in world.fired:
            world.fired.add(sig)
            finder.memes["shame"] += 1
            out.append("__shame__")
    return out


CAUSAL_RULES = [
    Rule(name="evidence", tag="social", apply=_r_evidence),
    Rule(name="shame", tag="social", apply=_r_shame),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


NOOKS = {
    "oak_nook": Nook(
        id="oak_nook",
        label="oak nook",
        phrase="a snug nook in an old oak",
        size="small",
        dry=True,
        place_line="In the bend of an old oak, there was a quiet nook where small things could wait unseen.",
        tags={"nook", "tree"},
    ),
    "wall_nook": Nook(
        id="wall_nook",
        label="wall nook",
        phrase="a shallow nook in the garden wall",
        size="small",
        dry=True,
        place_line="Beside the path, a shallow nook in the garden wall held the day's cool shade.",
        tags={"nook", "wall"},
    ),
    "root_nook": Nook(
        id="root_nook",
        label="root nook",
        phrase="a damp nook under tangled roots",
        size="small",
        dry=False,
        place_line="Under a knot of roots lay a dark nook where rainwater liked to linger.",
        tags={"nook", "roots"},
    ),
}

ITEMS = {
    "bell": Keepsake(
        id="bell",
        label="bell",
        phrase="a little silver bell",
        size="small",
        needs_dry=True,
        sound="ting-ting",
        action="ring",
        test_line="The bell gave a clear, bright ting-ting that skipped across the leaves.",
        memory_line="I tucked my bell away because its clear voice would have given me away.",
        tags={"bell", "sound", "dry"},
    ),
    "rattle": Keepsake(
        id="rattle",
        label="seed rattle",
        phrase="a seed-pod rattle",
        size="small",
        needs_dry=False,
        sound="sha-sha",
        action="shake",
        test_line="The seed rattle answered with a soft sha-sha, just as the story promised.",
        memory_line="I hid my rattle because even a little shake would have chattered too loudly.",
        tags={"rattle", "sound"},
    ),
    "pipe": Keepsake(
        id="pipe",
        label="reed pipe",
        phrase="a tiny reed pipe",
        size="small",
        needs_dry=True,
        sound="toot-toot",
        action="blow",
        test_line="The reed pipe let out a neat toot-toot that made the fern tips quiver.",
        memory_line="I hid my pipe because one happy note would have floated straight through the wood.",
        tags={"pipe", "sound", "dry"},
    ),
}

ANIMALS = {
    "mouse": AnimalSpec(
        id="mouse",
        label="mouse",
        title="Mouse",
        traits=["quick"],
        opening="Mouse loved finding what others had missed.",
        tags={"mouse"},
    ),
    "squirrel": AnimalSpec(
        id="squirrel",
        label="squirrel",
        title="Squirrel",
        traits=["nimble"],
        opening="Squirrel was always nosing into branches, bark, and hollows.",
        tags={"squirrel"},
    ),
    "rabbit": AnimalSpec(
        id="rabbit",
        label="rabbit",
        title="Rabbit",
        traits=["meek"],
        opening="Rabbit stepped softly, but soft feet notice many things.",
        tags={"rabbit"},
    ),
    "magpie": AnimalSpec(
        id="magpie",
        label="magpie",
        title="Magpie",
        traits=["keen"],
        opening="Magpie had a bright eye for every glimmer in the wood.",
        tags={"magpie"},
    ),
    "hedgehog": AnimalSpec(
        id="hedgehog",
        label="hedgehog",
        title="Hedgehog",
        traits=["honest"],
        opening="Hedgehog moved slowly enough to see where every path bent.",
        tags={"hedgehog"},
    ),
    "mole": AnimalSpec(
        id="mole",
        label="mole",
        title="Mole",
        traits=["patient"],
        opening="Mole knew the hidden places under roots and stones.",
        tags={"mole"},
    ),
    "owl": AnimalSpec(
        id="owl",
        label="owl",
        title="Owl",
        traits=["wise"],
        opening="Owl missed very little.",
        tags={"owl", "wise"},
    ),
    "tortoise": AnimalSpec(
        id="tortoise",
        label="tortoise",
        title="Tortoise",
        traits=["steady"],
        opening="Tortoise trusted slow thinking more than loud words.",
        tags={"tortoise", "wise"},
    ),
    "badger": AnimalSpec(
        id="badger",
        label="badger",
        title="Badger",
        traits=["grave"],
        opening="Badger listened with the whole weight of silence.",
        tags={"badger", "wise"},
    ),
}

STORMS = {
    "hawk": {
        "label": "a passing hawk",
        "open": "One noon, a hawk's shadow slid over the ferns.",
        "sound": "whoosh",
        "close": "so I slipped into the nearest hiding place and dared not make a peep",
        "tags": {"hawk", "danger"},
    },
    "wind": {
        "label": "a hard wind",
        "open": "One afternoon, the wind came tumbling through the trees.",
        "sound": "whooo",
        "close": "so I hid what I carried before the gusts could snatch it away",
        "tags": {"wind", "weather"},
    },
    "rain": {
        "label": "a sudden rain",
        "open": "One day, rain began drumming on every leaf.",
        "sound": "patter-patter",
        "close": "so I hurried to shelter and hid my treasure before my paws could slip",
        "tags": {"rain", "weather"},
    },
}


def item_fits(nook: Nook, item: Keepsake) -> bool:
    return nook.size == item.size


def item_safe(nook: Nook, item: Keepsake) -> bool:
    if item.needs_dry and not nook.dry:
        return False
    return True


def valid_story(nook: Nook, item: Keepsake) -> bool:
    return item_fits(nook, item) and item_safe(nook, item)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for nook_id, nook in NOOKS.items():
        for item_id, item in ITEMS.items():
            if valid_story(nook, item):
                combos.append((nook_id, item_id))
    return combos


def owner_is_generous(owner: Entity) -> bool:
    return any(t in GENEROUS_TRAITS for t in owner.traits)


def finder_is_honest(finder: Entity) -> bool:
    return any(t in HONEST_TRAITS for t in finder.traits)


def jury_is_wise(juror: Entity) -> bool:
    return juror.type in WISE_JURORS


def outcome_of(params: StoryParams) -> str:
    owner_spec = ANIMALS[params.owner]
    return "shared" if any(t in GENEROUS_TRAITS for t in owner_spec.traits) else "returned"


def explain_rejection(nook: Nook, item: Keepsake) -> str:
    if not item_fits(nook, item):
        return (
            f"(No story: {item.phrase} does not fit sensibly in {nook.phrase}. "
            "This world only tells stories about small keepsakes tucked into a small nook.)"
        )
    if item.needs_dry and not nook.dry:
        return (
            f"(No story: {item.phrase} should be kept dry, but {nook.phrase} is damp. "
            "A truthful flashback needs a hiding place that would actually protect the keepsake.)"
        )
    return "(No story: this nook and keepsake do not make a reasonable fable together.)"


def predict_verdict(world: World) -> dict:
    sim = world.copy()
    owner = sim.get("owner")
    item = sim.get("item")
    juror = sim.get("juror")
    owner.meters["memory_told"] += 1
    item.meters["sound_match"] += 1
    propagate(sim, narrate=False)
    convinced = juror.meters["certainty"] >= CERTAINTY_NEEDED
    return {"convinced": convinced, "certainty": juror.meters["certainty"]}


def introduce(world: World, finder: Entity, nook: Nook) -> None:
    world.say(nook.place_line)
    world.say(
        f"{finder.id} came by at first light. {finder.attrs['opening']}"
    )


def discover(world: World, finder: Entity, item: Entity, nook: Nook) -> None:
    finder.memes["wonder"] += 1
    finder.memes["covet"] += 1
    item.meters["found"] += 1
    world.say(
        f"In that {nook.label}, {finder.id} found {item.phrase}. "
        f"When {finder.pronoun()} lifted it, {item.attrs['sound']}! went the hidden thing."
    )
    world.say(
        f'"Found in a nook, so mine by luck," said {finder.id}, and {finder.pronoun("possessive")} eyes shone a little too brightly.'
    )


def claim(world: World, owner: Entity, finder: Entity, item: Entity) -> None:
    owner.memes["worry"] += 1
    world.say(
        f"Just then, {owner.id} hurried up the path. "
        f'"Please do not keep that {item.label}," {owner.pronoun()} said. '
        f'"It is mine, though I hid it and lost sight of the place."'
    )
    world.say(
        f'{finder.id} curled {finder.pronoun("possessive")} paws around it and answered, '
        f'"I found it first. A finder has a claim."'
    )


def gather_jury(world: World, juror: Entity, finder: Entity, owner: Entity) -> None:
    juror.memes["duty"] += 1
    if jury_is_wise(juror):
        juror.meters["certainty"] += 0
    world.say(
        f"So the woodland jury gathered on a mossy stone, with {juror.id} at the front to hear the matter."
    )
    pred = predict_verdict(world)
    world.facts["predicted_certainty"] = pred["certainty"]
    world.say(
        f'{juror.id} looked from {finder.id} to {owner.id} and said, '
        f'"Truth walks best when memory and proof walk together. Tell us everything."'
    )


def flashback(world: World, owner: Entity, storm: dict, nook: Nook, item_cfg: Keepsake) -> None:
    owner.meters["memory_told"] += 1
    owner.memes["hope"] += 1
    world.say(
        f'{owner.id} lowered {owner.pronoun("possessive")} head and remembered aloud: '
        f'"{storm["open"]} {storm["sound"]}! went the world around me. '
        f'I reached {nook.phrase}, and {item_cfg.memory_line} '
        f'Then I left too quickly, and afterward I could not find the place again."'
    )


def doubt(world: World, finder: Entity, juror: Entity) -> None:
    finder.memes["defiance"] += 1
    world.say(
        f'{finder.id} twitched and said, "A neat tale is not the same as truth."'
    )
    if jury_is_wise(juror):
        world.say(
            f'{juror.id} did not scold. "{finder.id}," {juror.pronoun()} said, "then let the thing itself speak."'
        )


def sound_test(world: World, item: Entity, item_cfg: Keepsake) -> None:
    item.meters["sound_match"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They asked for a test. {item_cfg.test_line}"
    )


def verdict(world: World, juror: Entity, owner: Entity, finder: Entity, item: Entity) -> None:
    propagate(world, narrate=False)
    certainty = juror.meters["certainty"]
    if certainty < CERTAINTY_NEEDED:
        raise StoryError("(No story: the jury never reaches a clear, reasonable verdict.)")
    world.say(
        f'{juror.id} nodded to the jury and gave the verdict. '
        f'"The sound fits the memory, and the memory fits the hiding place. '
        f'The {item.label} belongs to {owner.id}."'
    )
    finder.memes["covet"] = 0.0
    finder.memes["respect"] += 1


def resolution(world: World, owner: Entity, finder: Entity, item: Entity, item_cfg: Keepsake) -> None:
    if finder.memes["shame"] >= THRESHOLD or finder_is_honest(finder):
        finder.memes["honor"] += 1
    world.say(
        f"{finder.id} looked down at the {item.label} and felt the heat of fairness in {finder.pronoun('possessive')} cheeks."
    )
    if owner_is_generous(owner):
        finder.meters["returned"] += 1
        owner.meters["shared"] += 1
        world.say(
            f'{finder.id} placed it in {owner.id}\'s paws. But {owner.id} smiled and said, '
            f'"A true thing should not make enemies. Sit with me, and I will {item_cfg.action} it once for us both."'
        )
        world.say(
            f"So they sat beside the nook, and {item.attrs['sound']}! sang the little keepsake between them."
        )
        world.facts["outcome"] = "shared"
    else:
        finder.meters["returned"] += 1
        world.say(
            f'{finder.id} placed it back in {owner.id}\'s paws and said, '
            f'"What is found by chance is not earned by greed."'
        )
        world.say(
            f"{owner.id} tucked the {item.label} away more wisely than before, and the nook kept only cool shade."
        )
        world.facts["outcome"] = "returned"


def moral(world: World) -> None:
    outcome = world.facts["outcome"]
    if outcome == "shared":
        world.say("And so the jury learned that truth wins trust, and kindness keeps it.")
        world.facts["moral"] = "Truth wins trust, and kindness keeps it."
    else:
        world.say("And so the jury remembered: what luck uncovers, honesty must still measure.")
        world.facts["moral"] = "What luck uncovers, honesty must still measure."


def tell(
    nook_cfg: Nook,
    item_cfg: Keepsake,
    finder_spec: AnimalSpec,
    owner_spec: AnimalSpec,
    juror_spec: AnimalSpec,
    storm: dict,
) -> World:
    if finder_spec.id == owner_spec.id:
        raise StoryError("(No story: the finder and owner must be different animals.)")
    if not valid_story(nook_cfg, item_cfg):
        raise StoryError(explain_rejection(nook_cfg, item_cfg))

    world = World()
    finder = world.add(
        Entity(
            id=finder_spec.title,
            kind="character",
            type=finder_spec.id,
            label=finder_spec.label,
            phrase=finder_spec.label,
            role="finder",
            traits=list(finder_spec.traits),
            attrs={"opening": finder_spec.opening},
            tags=set(finder_spec.tags),
        )
    )
    owner = world.add(
        Entity(
            id=owner_spec.title,
            kind="character",
            type=owner_spec.id,
            label=owner_spec.label,
            phrase=owner_spec.label,
            role="owner",
            traits=list(owner_spec.traits),
            attrs={"opening": owner_spec.opening},
            tags=set(owner_spec.tags),
        )
    )
    juror = world.add(
        Entity(
            id=juror_spec.title,
            kind="character",
            type=juror_spec.id,
            label=juror_spec.label,
            phrase=juror_spec.label,
            role="juror",
            traits=list(juror_spec.traits),
            attrs={"opening": juror_spec.opening},
            tags=set(juror_spec.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.id,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="keepsake",
            attrs={"sound": item_cfg.sound, "action": item_cfg.action},
            tags=set(item_cfg.tags),
        )
    )
    place = world.add(
        Entity(
            id="nook",
            kind="thing",
            type=nook_cfg.id,
            label=nook_cfg.label,
            phrase=nook_cfg.phrase,
            role="nook",
            attrs={"dry": nook_cfg.dry, "size": nook_cfg.size},
            tags=set(nook_cfg.tags),
        )
    )

    introduce(world, finder, nook_cfg)
    discover(world, finder, item, nook_cfg)

    world.para()
    claim(world, owner, finder, item)
    gather_jury(world, juror, finder, owner)

    world.para()
    flashback(world, owner, storm, nook_cfg, item_cfg)
    doubt(world, finder, juror)
    sound_test(world, item, item_cfg)

    world.para()
    verdict(world, juror, owner, finder, item)
    resolution(world, owner, finder, item, item_cfg)
    moral(world)

    world.facts.update(
        nook=nook_cfg,
        item_cfg=item_cfg,
        finder=finder,
        owner=owner,
        juror=juror,
        item=item,
        storm=storm,
        flashback_used=True,
        sound_effect=item_cfg.sound,
        jury_clear=juror.meters["certainty"] >= CERTAINTY_NEEDED,
    )
    return world


KNOWLEDGE = {
    "nook": [
        (
            "What is a nook?",
            "A nook is a small tucked-away corner or hollow where something can rest out of the way."
        )
    ],
    "jury": [
        (
            "What does a jury do?",
            "A jury listens carefully to a problem and helps decide what is fair by weighing the evidence."
        )
    ],
    "bell": [
        (
            "What is a bell's sound like?",
            "A small bell usually makes a bright ringing sound, like ting-ting, because the metal shakes when it moves."
        )
    ],
    "rattle": [
        (
            "How does a rattle make sound?",
            "A rattle makes sound when little hard pieces knock together inside it as it moves."
        )
    ],
    "pipe": [
        (
            "How does a pipe make a note?",
            "A pipe makes a note when air moves through it and begins to vibrate."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier, so the reader can understand the present better."
        )
    ],
    "fairness": [
        (
            "Why is finding something not always the same as owning it?",
            "Because something may already belong to someone else. Fairness asks who truly has the right to it, not only who touched it last."
        )
    ],
}
KNOWLEDGE_ORDER = ["nook", "jury", "bell", "rattle", "pipe", "flashback", "fairness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    owner = f["owner"]
    juror = f["juror"]
    item_cfg = f["item_cfg"]
    nook = f["nook"]
    outcome = f["outcome"]
    ending = "shared kindly" if outcome == "shared" else "returned with a lesson"
    return [
        (
            f'Write a short fable for a 3-to-5-year-old that includes the words "nook" and "jury", '
            f'uses a flashback, and lets a small found object reveal the truth with the sound "{item_cfg.sound}".'
        ),
        (
            f"Tell a woodland fable where {finder.id} finds {item_cfg.phrase} in {nook.phrase}, "
            f"{owner.id} claims it, and {juror.id} leads a jury that listens to a flashback before giving a fair verdict."
        ),
        (
            f"Write a gentle animal fable with sound effects, a brief look into the past, and an ending where the keepsake is {ending}."
        ),
    ]


def pair_animal_names(finder: Entity, owner: Entity) -> str:
    return f"{finder.id} and {owner.id}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    owner = f["owner"]
    juror = f["juror"]
    item_cfg = f["item_cfg"]
    nook = f["nook"]
    storm = f["storm"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_animal_names(finder, owner)}, with {juror.id} leading the jury. "
            f"The quarrel begins when {finder.id} finds {item_cfg.phrase} in a nook."
        ),
        (
            f"Why did {finder.id} think the {item_cfg.label} should belong to {finder.pronoun('object')}?",
            f"{finder.id} thought finding it first gave {finder.pronoun('object')} the right to keep it. "
            f"The discovery filled {finder.pronoun('object')} with wonder, but also with a greedy wish to claim it."
        ),
        (
            f"What happened in the flashback {owner.id} told?",
            f"{owner.id} remembered the day {storm['label']} came and forced {owner.pronoun('object')} to hide {item_cfg.phrase} in {nook.phrase}. "
            f'The flashback mattered because it explained why the object was in the nook before {finder.id} ever saw it.'
        ),
        (
            "How did the jury decide who was telling the truth?",
            f"The jury listened to the memory and then tested the keepsake's sound in the present. "
            f"When the real sound matched the flashback, {juror.id} had proof that the story fit both the object and the hiding place."
        ),
    ]
    if outcome == "shared":
        qa.append(
            (
                f"How did the story end after the verdict?",
                f"{finder.id} returned the keepsake, and {owner.id} chose kindness instead of triumph. "
                f"Because {owner.id} was generous, the two sat together and shared one small happy sound."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"{finder.id} gave the keepsake back and accepted the jury's fair judgment. "
                f"The ending shows that honesty matters even when luck first puts a treasure in your paws."
            )
        )
    qa.append(
        (
            "What was the moral of the story?",
            f"{f['moral']} The whole quarrel changed once truth had both memory and proof to stand on."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"nook", "jury", "flashback", "fairness"}
    item_id = f["item_cfg"].id
    if item_id == "bell":
        tags.add("bell")
    elif item_id == "rattle":
        tags.add("rattle")
    elif item_id == "pipe":
        tags.add("pipe")
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.traits:
            bits.append(f"traits={entity.traits}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v not in ("", None, [], {}, set())}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {entity.id:8} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        nook="oak_nook",
        item="bell",
        finder="magpie",
        owner="mole",
        juror="owl",
        storm="hawk",
    ),
    StoryParams(
        nook="wall_nook",
        item="rattle",
        finder="squirrel",
        owner="hedgehog",
        juror="badger",
        storm="wind",
    ),
    StoryParams(
        nook="oak_nook",
        item="pipe",
        finder="mouse",
        owner="rabbit",
        juror="tortoise",
        storm="rain",
    ),
]


ASP_RULES = r"""
fits(N, I) :- nook(N), item(I), nook_size(N, S), item_size(I, S).
safe(N, I) :- nook(N), item(I), not needs_dry(I).
safe(N, I) :- nook(N), item(I), needs_dry(I), dry(N).
valid(N, I) :- fits(N, I), safe(N, I).

generous_owner :- chosen_owner(O), animal(O), has_trait(O, T), generous_trait(T).
outcome(shared) :- generous_owner.
outcome(returned) :- not generous_owner.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nook_id, nook in NOOKS.items():
        lines.append(asp.fact("nook", nook_id))
        lines.append(asp.fact("nook_size", nook_id, nook.size))
        if nook.dry:
            lines.append(asp.fact("dry", nook_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_size", item_id, item.size))
        if item.needs_dry:
            lines.append(asp.fact("needs_dry", item_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for trait in animal.traits:
            lines.append(asp.fact("has_trait", animal_id, trait))
    for trait in sorted(GENEROUS_TRAITS):
        lines.append(asp.fact("generous_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_owner", params.owner)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nook, a jury, a flashback, and a little sound-telling fable."
    )
    ap.add_argument("--nook", choices=NOOKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--finder", choices=ANIMALS)
    ap.add_argument("--owner", choices=ANIMALS)
    ap.add_argument("--juror", choices=["owl", "tortoise", "badger"])
    ap.add_argument("--storm", choices=STORMS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.finder and args.owner and args.finder == args.owner:
        raise StoryError("(No story: the finder and owner must be different animals.)")
    if args.nook and args.item:
        nook = NOOKS[args.nook]
        item = ITEMS[args.item]
        if not valid_story(nook, item):
            raise StoryError(explain_rejection(nook, item))

    combos = [
        combo for combo in valid_combos()
        if (args.nook is None or combo[0] == args.nook)
        and (args.item is None or combo[1] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    nook_id, item_id = rng.choice(sorted(combos))

    juror_id = args.juror or rng.choice(["owl", "tortoise", "badger"])
    storm_id = args.storm or rng.choice(sorted(STORMS))

    animal_keys = sorted(ANIMALS)
    finder_id = args.finder or rng.choice(animal_keys)
    owner_choices = [aid for aid in animal_keys if aid != finder_id]
    owner_id = args.owner or rng.choice(owner_choices)
    if owner_id == finder_id:
        raise StoryError("(No story: the finder and owner must be different animals.)")

    return StoryParams(
        nook=nook_id,
        item=item_id,
        finder=finder_id,
        owner=owner_id,
        juror=juror_id,
        storm=storm_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.nook not in NOOKS:
        raise StoryError(f"(No story: unknown nook '{params.nook}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.finder not in ANIMALS:
        raise StoryError(f"(No story: unknown finder '{params.finder}'.)")
    if params.owner not in ANIMALS:
        raise StoryError(f"(No story: unknown owner '{params.owner}'.)")
    if params.juror not in ANIMALS:
        raise StoryError(f"(No story: unknown juror '{params.juror}'.)")
    if params.storm not in STORMS:
        raise StoryError(f"(No story: unknown storm '{params.storm}'.)")

    world = tell(
        nook_cfg=NOOKS[params.nook],
        item_cfg=ITEMS[params.item],
        finder_spec=ANIMALS[params.finder],
        owner_spec=ANIMALS[params.owner],
        juror_spec=ANIMALS[params.juror],
        storm=STORMS[params.storm],
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (nook, item) combos:\n")
        for nook_id, item_id in combos:
            print(f"  {nook_id:10} {item_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.finder} finds {p.item} in {p.nook} "
                f"(owner: {p.owner}, juror: {p.juror}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
