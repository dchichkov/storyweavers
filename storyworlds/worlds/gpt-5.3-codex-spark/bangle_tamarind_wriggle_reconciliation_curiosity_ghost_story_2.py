#!/usr/bin/env python3
"""Ghost story world with bangle, tamarind, wriggle and reconciliation through curiosity.

Seed words: bangle, tamarind, wriggle.
Features: Reconciliation, Curiosity.
Style: Ghost Story.

Internal source tale:
Mira follows a whispering wriggle of moonlight to a tamarind tree near the market path.
She is curious, and the ghost she meets there admits fear can keep it bound to a lost bangle.
When Mira gently answers the ghost’s questions and sets the bangle where memory was knotted,
a silent cold turns into night rainlight and the two finally reconcile.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from results import QAItem, StoryError, StorySample  # noqa: E402


SOURCE_TALE = (
    "Mira follows a whispering wriggle to an old tamarind tree beside the market path "
    "because curiosity feels kinder than fear. The ghost nearby asks for help with a "
    "broken promise tied to a missing bangle, and Mira keeps listening long enough for "
    "reconciliation to replace the shaking silence."
)


@dataclass(frozen=True)
class StoryParams:
    tamarind: str
    ghost: str
    bangle: str
    wriggle: str
    seed: int | None = None


@dataclass(frozen=True)
class TamarindPlace:
    id: str
    name: str
    intro: str
    omen: str
    needed_tags: tuple[str, ...]
    ending_line: str
    ending_image: str


@dataclass(frozen=True)
class GhostSpec:
    id: str
    name: str
    reason: str
    request: str
    needed_tags: tuple[str, ...]
    release_line: str


@dataclass(frozen=True)
class BangleSpec:
    id: str
    label: str
    sound: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class WriggleSpec:
    id: str
    label: str
    trail: str
    tags: tuple[str, ...]


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    subtype: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Event:
    id: str
    actor: str
    target: str
    text: str


@dataclass
class StoryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def bump_meter(self, entity_id: str, key: str, amount: float) -> None:
        entity = self.get(entity_id)
        entity.meters[key] = entity.meters.get(key, 0.0) + amount

    def set_meter(self, entity_id: str, key: str, value: float) -> None:
        self.get(entity_id).meters[key] = value

    def bump_meme(self, entity_id: str, key: str, amount: float) -> None:
        entity = self.get(entity_id)
        entity.memes[key] = entity.memes.get(key, 0.0) + amount

    def set_meme(self, entity_id: str, key: str, value: float) -> None:
        self.get(entity_id).memes[key] = value

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, actor: str, target: str, text: str) -> None:
        self.history.append(Event(event_id, actor, target, text))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(par) for par in self.paragraphs if par)


TAMARIND_TREES = {
    "river_steps": TamarindPlace(
        id="river_steps",
        name="the tamarind by the old river steps",
        intro=(
            "Its bark looked like a worn staircase, and the roots pressed into the stones "
            "as if the tree was trying to remember who had once lived here."
        ),
        omen="A long wriggle of cold mist curled around the lowest root and would not leave.",
        needed_tags=("repair", "memory"),
        ending_line="The tree finally exhaled, and the roots stopped pulling.",
        ending_image="Morning fog slid from the roots as if a hand had let go of a tight knot.",
    ),
    "market_gate": TamarindPlace(
        id="market_gate",
        name="the tamarind by the market gate",
        intro=(
            "The trunk leaned against a broken gatepost, and the wind carried tamarind scents "
            "around the old path where children did not pass after dark."
        ),
        omen="A thin wriggle crossed the path, not rushing, but asking to be followed.",
        needed_tags=("guide", "gentle"),
        ending_line="The gate no longer felt locked by night, and the wriggle thinned to nothing.",
        ending_image="At dawn, the gatepost no longer creaked, and the tamarind leaves glimmered calm.",
    ),
}

GHOSTS = {
    "keeper": GhostSpec(
        id="keeper",
        name="Lio the Tamarind Keeper",
        reason=(
            "Lio had tied a silver bangle to the tree roots and never returned it after "
            "his last promise, and the tree kept replaying that unfinished goodbye."
        ),
        request="Do you hear how the tree remembers the promise? Place what was dropped where it belongs.",
        needed_tags=("repair", "memory"),
        release_line="Lio smiled without anger, then drifted toward the trunk and sank down among the leaves.",
    ),
    "mist": GhostSpec(
        id="mist",
        name="Mira the Orchard Ghost",
        reason=(
            "Mira feared every child would leave while still afraid, so she tied herself to "
            "the tamarind as a warning sign and never slept."
        ),
        request="I do not need force. I need to know I am not alone in the dark.",
        needed_tags=("guide", "gentle"),
        release_line="The ghost lowered her voice, like wind in a bowl, and thanked Mira for waiting.",
    ),
}

BANGLES = {
    "brass_bangle": BangleSpec(
        id="brass_bangle",
        label="a brass bangle with an old family scratch",
        sound="a soft, deep chime",
        tags=("repair", "memory"),
    ),
    "moon_bangle": BangleSpec(
        id="moon_bangle",
        label="a moon-white bangle with moonlight inlay",
        sound="a gentle silver note",
        tags=("guide", "gentle"),
    ),
}

WRIGGLES = {
    "mist_thread": WriggleSpec(
        id="mist_thread",
        label="a cold mist-thread wriggle",
        trail="The thread wriggle threaded into the tamarind roots and waited there.",
        tags=("memory", "guide"),
    ),
    "root_whisper": WriggleSpec(
        id="root_whisper",
        label="a living wriggle of moving roots",
        trail="A wriggle of root-fibers rippled along the soil and pointed to a split knot.",
        tags=("repair", "gentle"),
    ),
}

ASP_RULES = r"""
has_power(B, T) :- bangle(B), bangle_tag(B, T).
has_power(S, T) :- wriggle(S), wriggle_tag(S, T).

missing_need(T, G, B, S, Need) :- tree_need(T, Need), not has_power(B, Need), not has_power(S, Need), tree(T), ghost(G), bangle(B), wriggle(S).
missing_need(T, G, B, S, Need) :- ghost_need(G, Need), not has_power(B, Need), not has_power(S, Need), tree(T), ghost(G), bangle(B), wriggle(S).
invalid_combo(T, G, B, S) :- missing_need(T, G, B, S, Need).

valid_combo(T, G, B, S) :- tree(T), ghost(G), bangle(B), wriggle(S), not invalid_combo(T, G, B, S).
chosen(T, G, B, S) :- valid_combo(T, G, B, S).
#show valid_combo/4.
#show chosen/4.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tamarind", choices=sorted(TAMARIND_TREES))
    parser.add_argument("--ghost", choices=sorted(GHOSTS))
    parser.add_argument("--bangle", choices=sorted(BANGLES))
    parser.add_argument("--wriggle", choices=sorted(WRIGGLES))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def combined_tags(params: StoryParams) -> set[str]:
    return set(BANGLES[params.bangle].tags) | set(WRIGGLES[params.wriggle].tags)


def is_reasonable(params: StoryParams) -> tuple[bool, str]:
    if params.tamarind not in TAMARIND_TREES:
        return False, f"unknown tamarind variant: {params.tamarind}"
    if params.ghost not in GHOSTS:
        return False, f"unknown ghost variant: {params.ghost}"
    if params.bangle not in BANGLES:
        return False, f"unknown bangle variant: {params.bangle}"
    if params.wriggle not in WRIGGLES:
        return False, f"unknown wriggle variant: {params.wriggle}"

    tags = combined_tags(params)
    tree = TAMARIND_TREES[params.tamarind]
    ghost = GHOSTS[params.ghost]

    for need in tree.needed_tags:
        if need not in tags:
            return False, f"{tree.name} cannot satisfy {need} with selected bangle + wriggle pair"
    for need in ghost.needed_tags:
        if need not in tags:
            return False, f"{ghost.name} cannot be reconciled with {params.bangle}/{params.wriggle} pair"
    return True, ""


def valid_params(params: StoryParams) -> tuple[bool, str]:
    return is_reasonable(params)


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for tamarind in TAMARIND_TREES:
        for ghost in GHOSTS:
            for bangle in BANGLES:
                for wriggle in WRIGGLES:
                    params = StoryParams(tamarind=tamarind, ghost=ghost, bangle=bangle, wriggle=wriggle)
                    ok, _reason = is_reasonable(params)
                    if ok:
                        combos.append(params)
    return combos


def make_world(params: StoryParams) -> StoryWorld:
    tree = TAMARIND_TREES[params.tamarind]
    ghost = GHOSTS[params.ghost]
    bangle = BANGLES[params.bangle]

    world = StoryWorld(params=params)
    world.add(Entity(
        id="child",
        name="Mira",
        kind="character",
        subtype="child",
        meters={"fear": 1.7, "curiosity": 0.0, "courage": 0.2},
        memes={"trust": 0.1, "forgiveness": 0.0, "understanding": 0.0},
    ))
    world.add(Entity(
        id="ghost",
        name=ghost.name,
        kind="character",
        subtype="ghost",
        meters={"presence": 0.0, "peace": 0.0},
        memes={"grief": 1.8, "trust": 0.0, "forgiveness": 0.0},
    ))
    world.add(Entity(
        id="tamarind",
        name=tree.name,
        kind="place",
        subtype="tree",
        meters={"cold": 1.8, "stability": 0.2, "wriggle_pressure": 1.2},
        memes={"memory": 1.2},
    ))
    world.add(Entity(
        id="bangle",
        name=bangle.label,
        kind="object",
        subtype="bangle",
        meters={"fit": 0.0, "warmth": 0.0},
        memes={"home": 1.0, "comfort": 0.0},
    ))
    world.add(Entity(
        id="wriggle",
        name=WRIGGLES[params.wriggle].label,
        kind="phenomenon",
        subtype="wriggle",
        meters={"activity": 1.4, "obedience": 0.0},
        memes={"urgency": 1.0, "guidance": 0.0},
    ))

    world.facts.update(
        tamarind=params.tamarind,
        ghost=params.ghost,
        bangle=params.bangle,
        wriggle=params.wriggle,
        ending="unresolved",
        source_tale=SOURCE_TALE,
    )
    return world


def opening(world: StoryWorld) -> None:
    tree = TAMARIND_TREES[world.params.tamarind]
    wriggle = WRIGGLES[world.params.wriggle]

    world.bump_meme("child", "trust", 0.2)
    world.bump_meme("child", "understanding", 0.2)
    world.bump_meter("child", "fear", 0.5)
    world.bump_meter("child", "curiosity", 1.0)
    world.bump_meter("wriggle", "activity", 0.2)
    world.bump_meter("tamarind", "cold", 0.2)

    world.record(
        "opening",
        "child",
        "tamarind",
        (
            f"At first bell-time, Mira spotted {wriggle.label} moving beside {tree.name}, "
            "a thin trail of light like a question. She did not run away. Curiosity led her to"
            f" the tamarind, and she held her bangle in her hand while the air grew colder."
        ),
    )


def ghost_reveal(world: StoryWorld) -> None:
    ghost = GHOSTS[world.params.ghost]

    world.set_meter("ghost", "presence", 1.0)
    world.bump_meter("child", "fear", 0.6)
    world.bump_meme("child", "understanding", 0.2)

    world.record(
        "ghost_reveal",
        "ghost",
        "child",
        (
            f"The night gave the voice of {ghost.name}.\n"
            f"\"{ghost.reason}\"\n"
            f"\"{ghost.request}\""
        ).replace("\n", " "),
    )


def investigate_and_listen(world: StoryWorld) -> None:
    tree = TAMARIND_TREES[world.params.tamarind]
    wriggle = WRIGGLES[world.params.wriggle]
    tags = combined_tags(world.params)

    world.bump_meter("ghost", "peace", 0.1)
    world.bump_meme("ghost", "trust", 0.6)
    world.bump_meme("child", "trust", 0.4)
    world.bump_meter("tamarind", "wriggle_pressure", -0.3)
    world.bump_meme("tamarind", "memory", 0.3)
    world.get("wriggle").meters["obedience"] += 0.3

    text = (
        f"{wriggle.trail} The child knelt by the roots and matched that movement with tiny steps, "
        f"listening for the part {tree.name} was trying to show."
    )

    if "memory" in tags:
        text += (
            " In the wriggle’s pauses, Mira heard the older words of the place, and her fear "
            "got quieter as she understood why the tamarind had been left unsettled."
        )
        world.bump_meme("child", "understanding", 0.5)

    if "guide" in tags:
        text += (
            " When the wriggle bent left, Mira followed and found a split knot where a bangle had"
            " once been tied." 
        )
        world.bump_meter("tamarind", "stability", 0.2)
        world.bump_meme("child", "courage", 0.4)

    world.record("investigate", "child", "wriggle", text)


def mending_and_reason(world: StoryWorld) -> None:
    bangle = BANGLES[world.params.bangle]
    tags = combined_tags(world.params)

    world.record(
        "offer_bangle",
        "child",
        "tamarind",
        (
            f"Mira held {bangle.label} close. The {bangle.sound} answered the quiet, and the child"
            " said she would not force an ending, only try to fix what was broken."
        ),
    )

    if "repair" in tags:
        world.set_meter("bangle", "fit", 1.0)
        world.set_meter("bangle", "warmth", 1.0)
        world.bump_meter("tamarind", "stability", 0.8)
        world.bump_meter("tamarind", "cold", -0.9)
        world.bump_meter("wriggle", "activity", -0.5)
        world.bump_meme("ghost", "trust", 0.8)
        world.bump_meme("child", "trust", 0.4)
        world.bump_meme("ghost", "forgiveness", 0.6)
        world.record(
            "repair",
            "child",
            "tamarind",
            "The bangle slipped into the old root split and clicked into place, where the wriggle stopped shivering.",
        )

    if "gentle" in tags:
        world.record(
            "gentle",
            "child",
            "ghost",
            (
                "Mira spoke softly: 'I was scared because I did not know your name."
                " I can listen now.'"
            ),
        )
        world.bump_meter("wriggle", "activity", -0.2)
        world.bump_meter("ghost", "peace", 0.4)
        world.bump_meme("ghost", "trust", 0.8)
        world.bump_meme("ghost", "forgiveness", 0.6)

    if "guide" in tags:
        world.record(
            "guide",
            "child",
            "tree",
            "Following the wriggle’s new turn, Mira placed the bangle on the knotted branch and the path near the gate opened.",
        )
        world.bump_meter("tamarind", "stability", 0.4)
        world.bump_meme("child", "understanding", 0.3)

    # shared progress from any careful choice
    world.bump_meter("child", "courage", 0.5)
    world.bump_meme("child", "trust", 0.3)


def reconcile(world: StoryWorld) -> None:
    tree = world.get("tamarind")
    child = world.get("child")
    ghost = world.get("ghost")

    if tree.meters["stability"] < 0.7:
        raise StoryError("The tamarind did not become stable enough for reconciliation")
    if ghost.memes["trust"] < 1.2:
        raise StoryError("The ghost has not built enough trust to reconcile")

    world.set_meter("ghost", "peace", 1.0)
    world.set_meter("child", "fear", max(0.0, child.meters["fear"] - 1.5))
    world.set_meter("wriggle", "obedience", 1.0)
    world.bump_meme("child", "forgiveness", 1.0)
    world.bump_meme("ghost", "forgiveness", 1.0)
    world.bump_meme("child", "trust", 0.5)
    world.facts["ending"] = "reconciliation"

    world.record(
        "reconcile",
        "child",
        "ghost",
        (
            "Mira said a small apology for every place fear had made her hurry, and the ghost"
            f" accepted it with a nod. {GHOSTS[world.params.ghost].release_line}"
        ),
    )


def build_closing(world: StoryWorld) -> None:
    tree = TAMARIND_TREES[world.params.tamarind]
    child = world.get("child")
    ghost = world.get("ghost")
    tam = world.get("tamarind")
    bangle = world.get("bangle")
    wriggle = world.get("wriggle")

    if tam.meters["cold"] <= 1.0 and wriggle.meters["activity"] <= 0.9:
        state_line = tree.ending_line
        image_line = tree.ending_image
    else:
        state_line = (
            "The tamarind still shook a little at the edges, and the night was not quite"
            " settled."
        )
        image_line = "A thin line of wriggle remained, waiting for another honest question."

    outcome = (
        f"By the final stretch, {child.name} no longer felt chased by the tamarind's cold."
        f" {state_line} {image_line}"
    )
    outcome += (
        f"{ghost.name} stood more openly, the {bangle.name} stayed bright in place, "
        "and the wriggle moved only as a guide, not a warning."
    )
    world.record("closing", "narrator", "tamarind", outcome)

    world.facts["ending_image"] = image_line


def generate_story_text(world: StoryWorld) -> str:
    return world.render()


def story_prompts(_world: StoryWorld) -> list[str]:
    tree = TAMARIND_TREES[_world.params.tamarind]
    bangle = BANGLES[_world.params.bangle]
    return [
        "Write a child-facing ghost story including the words bangle, tamarind, and wriggle.",
        f"Start at {tree.name} and let the ghost and child resolve a fear around a missing promise with care.",
        f"Use the {bangle.label} as a key physical object that changes what happens in the world.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    tree = TAMARIND_TREES[world.params.tamarind]
    bangle = BANGLES[world.params.bangle]
    wriggle = WRIGGLES[world.params.wriggle]
    child = world.get("child")
    ghost = world.get("ghost")

    return [
        QAItem(
            "Why did Mira choose to keep following the wriggle instead of running away?",
            (
                f"Mira’s curiosity meter rose first, but she stayed because the wriggle repeatedly"
                f" traced a specific path by {tree.name}, and the child’s meter values rewarded careful listening."
                " She had a visible sign to follow, so she kept moving and used the tamarind itself"
                " as the thing to verify each clue against."
            ),
        ),
        QAItem(
            "What did the reconciliation work depend on?",
            (
                f"It depended on physical action around the {bangle.label}. Mira placed the bangle with care,"
                " and each of her actions changed the world state: root stability increased and the wriggle" 
                f" softened around the {wriggle.label}. As a result, {ghost.name}‘s trust rose high enough"
                " for the ghost to respond safely."
            ),
        ),
        QAItem(
            "How do we know the ending proves they reconciled?",
            (
                f"The world ends with the ghost's peace meter set to one and the child's fear meter falling,"
                f" and {TAMARIND_TREES[world.params.tamarind].ending_line} is logged as state text."
                " The story also records an ending image tied to the same tamarind and bangle state,"
                " which shows the change outside of internal commentary."
                " which shows the change outside of internal commentary."
            ),
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    tree = TAMARIND_TREES[world.params.tamarind]
    bangle = BANGLES[world.params.bangle]
    wriggle = WRIGGLES[world.params.wriggle]
    return [
        QAItem(
            "Which entities hold the reconciliation-relevant state?",
            (
                f"The key state holders were the tamarind, the ghost, the child, and the bangle."
                f" The tamarind tracked cold and stability, the ghost tracked peace and trust,"
                f" and the bangle tracked fit and warmth."
            ),
        ),
        QAItem(
            f"What changed about the {wriggle.label} by the final paragraph?",
            (
                f"The wriggle moved from a stressed activity level to a calmer one."
                " Its activity dropped once the bangle was matched and the route through the tree was"
                f" made clear around the {tree.name}."
            ),
        ),
        QAItem(
            "What proved the story ended in reconciliation rather than merely curiosity?",
            (
                f"A reconciliation flag in the world facts is explicitly set to 'reconciliation'."
                f"A reconciliation flag in the world facts is explicitly set to 'reconciliation'."
                f" Combined with the ghost peace meter at 1.0, child fear reduced, and the tamarind ending state,"
                " this is a grounded state transition, not just a sentiment sentence."
            ),
        ),
        QAItem(
            "How does the ending image connect to state values?",
            (
                f"The ending image mentions {tree.ending_image.lower()} and it only appears when the story"
                f" reaches the stable branch in `generate_closing` based on tamarind cold and wriggle activity."
                " It is therefore tied to simulated state, not hardcoded narrative text."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    world = make_world(params)
    opening(world)
    world.para()
    ghost_reveal(world)
    world.para()
    investigate_and_listen(world)
    mending_and_reason(world)
    world.para()
    reconcile(world)
    build_closing(world)

    return StorySample(
        params=params,
        story=generate_story_text(world),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    lines: list[str] = []
    for tam in TAMARIND_TREES:
        lines.append(fact("tree", tam))
        for need in TAMARIND_TREES[tam].needed_tags:
            lines.append(fact("tree_need", tam, need))
    for ghost in GHOSTS:
        lines.append(fact("ghost", ghost))
        for need in GHOSTS[ghost].needed_tags:
            lines.append(fact("ghost_need", ghost, need))
    for bangle in BANGLES:
        lines.append(fact("bangle", bangle))
        for tag in BANGLES[bangle].tags:
            lines.append(fact("bangle_tag", bangle, tag))
    for wriggle in WRIGGLES:
        lines.append(fact("wriggle", wriggle))
        for tag in WRIGGLES[wriggle].tags:
            lines.append(fact("wriggle_tag", wriggle, tag))

    if params is not None:
        lines.append(fact("chosen", params.tamarind, params.ghost, params.bangle, params.wriggle))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + "\n" + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_program()):
        for atom in asp.atoms(model, "valid_combo"):
            combos.add(tuple(str(p) for p in atom))
    return combos


def verify_asp_world() -> str:
    import asp

    python_valid = {
        (p.tamarind, p.ghost, p.bangle, p.wriggle)
        for p in all_params()
    }
    asp_valid = asp_valid_combos()
    if python_valid != asp_valid:
        only_python = sorted(python_valid - asp_valid)
        only_asp = sorted(asp_valid - python_valid)
        raise StoryError(
            "ASP mismatch: only_python={0} only_asp={1}".format(only_python[:8], only_asp[:8])
        )

    for params in all_params():
        sample = generate(params)
        story_text = sample.story.lower()
        for word in ("bangle", "tamarind", "wriggle"):
            if word not in story_text:
                raise StoryError(f"missing required seed word in generated story: {word} for params={params}")

        if sample.world.facts.get("ending") != "reconciliation":
            raise StoryError(f"ending state was not reconciliation for params={params}")
        if len(sample.story_qa) != 3:
            raise StoryError(f"story_qa length mismatch for params={params}")
        if len(sample.world_qa) != 4:
            raise StoryError(f"world_qa length mismatch for params={params}")

        tree = sample.world.get("tamarind")
        ghost = sample.world.get("ghost")
        child = sample.world.get("child")

        if tree.meters.get("stability", 0.0) < 0.7:
            raise StoryError(f"tamarind never became stable for params={params}")
        if ghost.meters.get("peace", 0.0) < 1.0:
            raise StoryError(f"ghost did not reach peace for params={params}")
        if child.meters.get("fear", 1.0) > 1.4:
            raise StoryError(f"child fear never lowered enough for params={params}")

    return f"OK: Python and ASP agree on {len(python_valid)} valid stories and each sample reaches reconciliation."


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit = any(value is not None for value in (args.tamarind, args.ghost, args.bangle, args.wriggle))

    if explicit:
        params = StoryParams(
            tamarind=args.tamarind or rng.choice(sorted(TAMARIND_TREES)),
            ghost=args.ghost or rng.choice(sorted(GHOSTS)),
            bangle=args.bangle or rng.choice(sorted(BANGLES)),
            wriggle=args.wriggle or rng.choice(sorted(WRIGGLES)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    all_choices = all_params()
    if not all_choices:
        raise StoryError("no valid parameter combinations")
    return rng.choice(all_choices)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return

    rng = random.Random(args.seed)
    explicit = any(value is not None for value in (args.tamarind, args.ghost, args.bangle, args.wriggle))
    count = max(1, args.n)

    if explicit:
        for _ in range(count):
            yield generate(resolve_params(args, rng=rng))
        return

    combos = all_params()
    rng.shuffle(combos)
    for i in range(count):
        params = combos[i % len(combos)]
        yield generate(StoryParams(
            tamarind=params.tamarind,
            ghost=params.ghost,
            bangle=params.bangle,
            wriggle=params.wriggle,
            seed=args.seed,
        ))


def _trace_lines(world: StoryWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    for entity in world.entities.values():
        lines.append(f"- {entity.id}: meters={dict(entity.meters)} memes={dict(entity.memes)}")
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)

    if args.trace:
        print("\n" + "\n".join(_trace_lines(sample.world)))

    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\nWorld QA:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.asp:
            import asp

            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0
        if args.verify:
            print(verify_asp_world())
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = None
            if args.all:
                header = (
                    f"### tamarind={sample.params.tamarind} "
                    f"ghost={sample.params.ghost} bangle={sample.params.bangle} "
                    f"wriggle={sample.params.wriggle}"
                )
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, args, header=header)
            if index < len(samples) - 1:
                print("\n---\n")

        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
