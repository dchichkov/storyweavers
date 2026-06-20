#!/usr/bin/env python3
"""A child-facing ghost story about curiosity, reconciliation, and a tamarind tree.

Seed words: bangle, tamarind, wriggle.
Features: Reconciliation, Curiosity.
Style: ghost story.

An internal source tale:
A child named Lio follows a wriggle of silver fog around an old tamarind tree because
she is curious about a midnight rattle. The mist reveals a lonely ghost who can only
settle when the child matches an offered bangle to the right place and the fear in
both hearts finally turns into care.
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

# Make shared result containers importable when executed directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from results import QAItem, StoryError, StorySample  # noqa: E402


SOURCE_TALE = (
    "At dusk, Lio follows a cool wriggle of fog near the tamarind tree because "
    "curiosity feels safer than guessing. A soft ghost voice wants help with a broken "
    "bangle tied into the roots. When Lio discovers the mismatch and helps repair the "
    "ghost’s worry, the haunting turns into forgiveness."
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
    setting: str
    omen: str
    calm_line: str
    ending_image: str
    needed_tags: tuple[str, ...]


@dataclass(frozen=True)
class GhostSpec:
    id: str
    name: str
    concern: str
    whisper: str
    needed_tags: tuple[str, ...]
    release_phrase: str


@dataclass(frozen=True)
class BangleType:
    id: str
    label: str
    tone: str
    comfort: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class WriggleSign:
    id: str
    label: str
    description: str
    tags: tuple[str, ...]
    path_text: str


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    type: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


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

    def bump_meter(self, entity_id: str, name: str, value: float) -> None:
        ent = self.get(entity_id)
        ent.meters[name] = ent.meters.get(name, 0.0) + value

    def bump_meme(self, entity_id: str, name: str, value: float) -> None:
        ent = self.get(entity_id)
        ent.memes[name] = ent.memes.get(name, 0.0) + value

    def set_meter(self, entity_id: str, name: str, value: float) -> None:
        ent = self.get(entity_id)
        ent.meters[name] = value

    def set_meme(self, entity_id: str, name: str, value: float) -> None:
        ent = self.get(entity_id)
        ent.memes[name] = value

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(par) for par in self.paragraphs if par)


TAMARIND_TREES = {
    "river_gate": TamarindPlace(
        id="river_gate",
        name="the tamarind tree by the old river gate",
        setting=(
            "Its trunk leaned like a doorway above the dark bank, and tiny tamarind pods"
            " rattled against the gate whenever the wind changed"
        ),
        omen="Each breath around the trunk felt colder than the pond air, as if the tree held its own long memory.",
        calm_line="When the bangle settled right, the tamarind trunk stopped shivering.",
        ending_image=(
            "At first light, the tamarind bark glowed from dew, and Lio could see the bangle"
            " hanging where the roots should be warm instead of cold."
        ),
        needed_tags=("repair", "memory"),
    ),
    "fence_corner": TamarindPlace(
        id="fence_corner",
        name="the tamarind at the broken courtyard fence",
        setting=(
            "Lanterns from the house barely touched the far end, where the tree wrapped a"
            " torn fencepost with soft silver bark lines."
        ),
        omen="A small wriggle of fog moved between the fence nails and then stopped near the branch",
        calm_line="When the night accepted the bangle, the fence-post wriggle faded and the leaves settled.",
        ending_image=(
            "By sunrise, the courtyard fence stood still, and the bangle sat on the branch with"
            " no chill left in the air around it."
        ),
        needed_tags=("guide", "gentle"),
    ),
    "market_hill": TamarindPlace(
        id="market_hill",
        name="the tamarind beyond the hill market",
        setting=(
            "The tamarind grew beside an old weighing post, where day smells gave way to"
            " night jasmine and old stories."
        ),
        omen="A wriggle of light slipped over the tamarind roots like the thread of a forgotten promise.",
        calm_line="The roots held still once the wriggle had a path to follow, and no one felt alone there at midnight.",
        ending_image=(
            "Morning showed the tamarind roots in clean soil, and Lio waved to the place where"
            " the wriggle ended in silver."
        ),
        needed_tags=("guide", "memory"),
    ),
}

GHOSTS = {
    "keeper": GhostSpec(
        id="keeper",
        name="Nira of the tamarind roots",
        concern=(
            "Nira had tied a silver bangle to the tamarind roots to keep the night safe,"
            " but the knot had slipped loose and fear began to grow"
        ),
        whisper=(
            '"I do not mean to hurt you," the voice hissed softly. '
            '"I am trying to keep the roots from writhing open when children pass at night."'
        ),
        needed_tags=("repair", "memory"),
        release_phrase=(
            "Nira nodded, softer than before, and her shoulders dropped like fog letting go."
        ),
    ),
    "guide": GhostSpec(
        id="guide",
        name="Tomas the orchard guide",
        concern=(
            "Tomas had guarded a narrow path around the tamarind for years and could not"
            " leave because the wriggle kept pulling people from the safe route"
        ),
        whisper=(
            '"Walk by my branch and I can tell you where the wriggle points," the ghost said. '
            '"I only wanted a careful friend, not a frightened one."'
        ),
        needed_tags=("guide", "gentle"),
        release_phrase=(
            "Tomas smiled in the shape of moonlight and moved backward, no longer standing "
            "between Lio and the path."
        ),
    ),
    "forgiver": GhostSpec(
        id="forgiver",
        name="Ari of the old orchard",
        concern=(
            "Ari had been left behind by a promise, and the tamarind still remembered the"
            " wordless apology that never arrived"
        ),
        whisper=(
            '"Do you hear it?" Ari asked. "A wriggle is just a question with no answer yet."'
            " If you answer it kindly, the memory can close."
        ),
        needed_tags=("memory", "guide"),
        release_phrase=(
            "Ari reached down like a hand made of moonlight and touched the tamarind trunk"
            " without fear."
        ),
    ),
}

BANGLES = {
    "brass_mended": BangleType(
        id="brass_mended",
        label="brass bangle with a small scratch in the circle",
        tone="low-clink",
        comfort="firm",
        tags=("repair", "memory"),
    ),
    "silver_gentle": BangleType(
        id="silver_gentle",
        label="silver bangle with tiny engraved leaves",
        tone="soft chime",
        comfort="gentle",
        tags=("gentle", "guide"),
    ),
    "amber_memory": BangleType(
        id="amber_memory",
        label="amber bangle set with a warm seed bead",
        tone="quiet hum",
        comfort="warm",
        tags=("memory", "guide", "repair"),
    ),
}

WRIGGLES = {
    "silver_fade": WriggleSign(
        id="silver_fade",
        label="a thin silver wriggle",
        description="a thin silver wriggle sliding through the moonlit soil",
        tags=("guide", "gentle"),
        path_text="It curled toward the path where tamarind roots crossed the yard.",
    ),
    "root_snarl": WriggleSign(
        id="root_snarl",
        label="a wriggle of tangled roots",
        description="a wriggle of tangled roots near the tamarind base",
        tags=("repair", "memory"),
        path_text="It wriggled toward a loose knot in the roots and moved like a question mark there.",
    ),
    "mist_thread": WriggleSign(
        id="mist_thread",
        label="a misty wriggle",
        description="a misty wriggle that moved like a thread pulled through leaves",
        tags=("memory", "guide"),
        path_text="The thread wriggle looped low and pointed to the branch where the old bangle had gone.",
    ),
}

ASP_RULES = r"""
has_capability(B, Tag) :- bangle(B), bangle_tag(B, Tag).
has_capability(S, Tag) :- wriggle(S), wriggle_tag(S, Tag).

invalid(T, G, B, S) :- tree_need(T, Need), not has_capability(B, Need), not has_capability(S, Need), tree(T), ghost(G), bangle(B), wriggle(S).
invalid(T, G, B, S) :- ghost_need(G, Need), not has_capability(B, Need), not has_capability(S, Need), ghost(G), tree(T), bangle(B), wriggle(S).

valid(T, G, B, S) :-
    tree(T), ghost(G), bangle(B), wriggle(S),
    not invalid(T, G, B, S).

chosen(T, G, B, S) :- valid(T, G, B, S).
#show valid/4.
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
    tree = TAMARIND_TREES[params.tamarind]
    ghost = GHOSTS[params.ghost]
    tags = combined_tags(params)
    for need in tree.needed_tags:
        if need not in tags:
            return False, f"{tree.name} cannot be fixed with this bangle + wriggle pairing (missing {need})"
    for need in ghost.needed_tags:
        if need not in tags:
            return False, f"{ghost.name} cannot feel safe with this pairing (missing {need})"
    return True, ""


def valid_params(params: StoryParams) -> tuple[bool, str]:
    return is_reasonable(params)


def all_params() -> list[StoryParams]:
    options: list[StoryParams] = []
    for tamarind in TAMARIND_TREES:
        for ghost in GHOSTS:
            for bangle in BANGLES:
                for wriggle in WRIGGLES:
                    params = StoryParams(tamarind=tamarind, ghost=ghost, bangle=bangle, wriggle=wriggle)
                    ok, _reason = is_reasonable(params)
                    if ok:
                        options.append(params)
    return options


def make_world(params: StoryParams) -> StoryWorld:
    tree = TAMARIND_TREES[params.tamarind]
    ghost = GHOSTS[params.ghost]
    bangle = BANGLES[params.bangle]
    wriggle = WRIGGLES[params.wriggle]

    world = StoryWorld(params=params)
    world.add(Entity(id="child", name="Lio", kind="character", type="boy", meters={"fear": 2.0, "curiosity": 0.0}, memes={"trust": 0.0, "forgiveness": 0.0}))
    world.add(Entity(
        id="ghost",
        name=ghost.name,
        kind="ghost",
        type="ghost",
        meters={"visible": 0.0, "peace": 0.0},
        memes={"memory": 2.0, "trust": 0.0},
    ))
    world.add(Entity(
        id="tamarind",
        name=tree.name,
        kind="place",
        type="tree",
        meters={"stability": 0.0, "wriggle_pressure": 1.0},
        memes={"murmur": 0.0},
    ))
    world.add(Entity(
        id="bangle",
        name=bangle.label,
        kind="object",
        type="bangle",
        meters={"attached": 0.0, "warmth": 0.0},
        memes={"value": 1.0},
    ))
    world.add(Entity(
        id="wriggle",
        name=wriggle.label,
        kind="phenomenon",
        type="wriggle",
        meters={"activity": 1.5, "obedience": 0.0},
        memes={"signal": 1.0},
    ))
    world.facts.update(
        tamarind=tree.id,
        ghost=ghost.id,
        bangle=bangle.id,
        wriggle=wriggle.id,
        combined_tags=sorted(combined_tags(params)),
        source_tale=SOURCE_TALE,
        ending="unresolved",
    )
    return world


def opening(world: StoryWorld) -> None:
    child = world.get("child")
    tree = TAMARIND_TREES[world.params.tamarind]
    wriggle = WRIGGLES[world.params.wriggle]
    world.bump_meme("child", "curiosity", 1.0)
    world.bump_meme("ghost", "memory", 0.2)
    world.record(
        "opening",
        (
            f"Lio followed {wriggle.description} toward {tree.name}, where the tamarind trunk had"
            f" begun to sound like breathing. The child kept walking anyway because curiosity"
            f" was louder than fear, and a soft tamarind smell stayed steady in the air."
        ),
        actor="child",
        target="tamarind",
    )


def ghost_reveal(world: StoryWorld) -> None:
    tree = TAMARIND_TREES[world.params.tamarind]
    ghost = GHOSTS[world.params.ghost]
    world.set_meter("ghost", "visible", 1.0)
    world.bump_meter("child", "fear", 1.0)
    world.bump_meter("tamarind", "wriggle_pressure", 0.5)
    world.bump_meme("ghost", "trust", 0.5)
    world.record(
        "ghost_reveal",
        (
            f'{tree.omen} Then {ghost.whisper} The bangle in Lio’s pocket began to ring with a {BANGLES[world.params.bangle].tone}, '
            f'and the wriggle tightened around the roots as if it wanted the wrong knot to be seen.'
        ),
        actor="ghost",
        target="child",
    )


def investigate_and_match(world: StoryWorld) -> None:
    tree = TAMARIND_TREES[world.params.tamarind]
    ghost = GHOSTS[world.params.ghost]
    wriggle = WRIGGLES[world.params.wriggle]
    bangle = BANGLES[world.params.bangle]
    world.bump_meme("child", "curiosity", 1.0)
    world.bump_meter("wriggle", "activity", 0.5)
    world.bump_meter("tamarind", "stability", 0.2)
    world.record(
        "investigate",
        (
            f'{wriggle.path_text} Lio crouched and followed with care, tracing the bangle notch in the tamarind bark. '
            f'The ghost did not strike, only watched. {ghost.name} said, "If you can match this to the right line, {ghost.name.split()[0]} can finally rest."'
        ),
        actor="child",
        target="wriggle",
    )

    if "repair" in combined_tags(world.params):
        world.record(
        "repair",
        (
                f"Lio pressed the {bangle.label} onto the split knot and wrapped the tamarind roots once the shape fit. "
                f'The wriggle loosened, then thinned as the knot held.'
        ),
            actor="child",
            target="tamarind",
        )
        world.set_meter("bangle", "attached", 1.0)
        world.bump_meter("tamarind", "stability", 1.0)
        world.set_meter("wriggle", "obedience", 1.0)
        world.bump_meme("child", "trust", 0.8)
        world.bump_meme("ghost", "trust", 1.2)
    if "guide" in combined_tags(world.params):
        world.record(
            "guide",
            (
                f"The wriggle moved to the branch where the bangle had once been tied."
                f" Following it, Lio found a loose split in the tree where the ghost had hidden the loose end."
            ),
            actor="child",
            target="tree",
        )
        world.bump_meme("child", "understanding", 1.0)
        world.bump_meter("tamarind", "stability", 0.4)
        world.bump_meme("ghost", "trust", 0.6)
    if "gentle" in combined_tags(world.params):
        world.record(
            "gentle",
            "The cold around the tamarind eased into warm mist, and the wriggle no longer felt sharp or urgent.",
            actor="ghost",
            target="tamarind",
        )
        world.bump_meme("ghost", "trust", 0.8)
        world.bump_meter("tamarind", "stability", 0.3)


def reconcile(world: StoryWorld) -> None:
    tree = TAMARIND_TREES[world.params.tamarind]
    ghost = GHOSTS[world.params.ghost]
    child = world.get("child")
    if world.get("tamarind").meters["stability"] < 0.5:
        raise StoryError("The tamarind roots remained unstable; reconciliation cannot happen yet")

    if world.get("ghost").memes["trust"] < 1.0:
        raise StoryError("The ghost did not trust the child enough for reconciliation")

    world.set_meter("ghost", "peace", 1.0)
    world.set_meter("child", "fear", max(0.0, world.get("child").meters["fear"] - 1.5))
    world.bump_meme("child", "forgiveness", 1.2)
    world.bump_meme("ghost", "trust", 0.8)
    world.bump_meme("child", "trust", 0.8)
    world.facts["ending"] = "reconciliation"
    world.record(
        "reconcile",
        (
            f"Lio said, \"I found it, and I am sorry for being scared before I listened.\""
            f" {ghost.name} listened, and {ghost.release_phrase}"
        ),
        actor="child",
        target="ghost",
    )
    world.record(
        "end_image",
        (
            f"{tree.calm_line}"
            f" {tree.ending_image}"
        ),
        actor="narrator",
    )


def generate_story(world: StoryWorld) -> str:
    world.para()
    child = world.get("child")
    ghost = world.get("ghost")
    wriggle = world.get("wriggle")
    tamarind = world.get("tamarind")

    # A final state-driven sentence: these lines change if event state changes.
    if tamarind.meters["wriggle_pressure"] > 1.0 or wriggle.meters["activity"] > 1.2:
        extra = (
            f"The tamarind still held its secret, but the pressure in the roots eased when"
            f" Lio kept one hand on the bangle and one hand on trust.")
    else:
        extra = (
            f"The tamarind stayed calm because both child and ghost now read the same route"
            f" across the knot and the roots.")
    world.record(
        "closing_state",
        f"Lio and {ghost.name} shared the night as a held pause, not a fear. {extra}",
        actor="narrator",
    )

    return world.render()


def story_prompts(world: StoryWorld) -> list[str]:
    tree = TAMARIND_TREES[world.params.tamarind]
    ghost = GHOSTS[world.params.ghost]
    bangle = BANGLES[world.params.bangle]
    return [
        "Write a child-facing ghost story that includes bangle, tamarind, and wriggle.",
        f"Use {tree.name} as a physical place where curiosity about a ghostly signal is rewarded by careful action.",
        f"Show reconciliation after the child notices and fixes {ghost.name}'s need with the {bangle.label}.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    tree = TAMARIND_TREES[world.params.tamarind]
    bangle = BANGLES[world.params.bangle]
    ghost = GHOSTS[world.params.ghost]
    child = world.get("child")
    ghost_ent = world.get("ghost")

    return [
        QAItem(
            "Why did Lio continue after the first frightening moment?",
            (
                f"Lio kept going because the story world tied curiosity to a visible cue: the wriggle led to a specific place around {tree.name}, "
                "and the child trusted what the physical signs showed more than the initial fear."
            ),
        ),
        QAItem(
            "What changed the ghost and the child from warning to trust?",
            (
                f"The child matched the {bangle.label} to the tamarind knot and followed the wriggle in the way it moved, which lowered the root pressure and made the ghost feel safe. "
                "After that physical repair and the clear answer, trust rose in the world state and the ghost could speak without anger."
            ),
        ),
        QAItem(
            "How is the ending proof of reconciliation shown?",
            (
                f"The ending is shown by state: the tamarind’s pressure was reduced, the bangle stayed attached, and the ghost’s peace meter became stable. "
                f"{child.name} and {ghost.name} ended by sharing a calm moment, not by fleeing each other."
            ),
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    tree = TAMARIND_TREES[world.params.tamarind]
    bangle = BANGLES[world.params.bangle]
    wriggle = WRIGGLES[world.params.wriggle]
    return [
        QAItem(
            "Which physical item carried the change in this world?",
            (
                f"The physical carrier was the {bangle.label} and its placement on the tamarind roots. "
                "That single object anchored the child’s action to the world and let the wriggle and ghost behavior shift."
            ),
        ),
        QAItem(
            "What happened to the wriggle after the reconciliation?",
            (
                f"After Lio acted, the wriggle no longer stayed sharp. The wriggle moved as a gentle signal toward the bangle line, "
                "then thinned and stopped driving at the roots of the tamarind tree."
            ),
        ),
        QAItem(
            "What was the ghost’s visible state by the final paragraph?",
            (
                f"{tree.name} still held meaning, but the ghost was no longer fully visible as a threat. "
                "The world tracked this as a stable peace state, so the ghost’s role became a guide instead of a warning."
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
    investigate_and_match(world)
    world.para()
    reconcile(world)
    story = generate_story(world)

    return StorySample(
        params=params,
        story=story,
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for tam_id in TAMARIND_TREES:
        rows.append(fact("tree", tam_id))
        for need in TAMARIND_TREES[tam_id].needed_tags:
            rows.append(fact("tree_need", tam_id, need))
    for ghost_id in GHOSTS:
        rows.append(fact("ghost", ghost_id))
        for need in GHOSTS[ghost_id].needed_tags:
            rows.append(fact("ghost_need", ghost_id, need))
    for bangle_id in BANGLES:
        rows.append(fact("bangle", bangle_id))
        for tag in BANGLES[bangle_id].tags:
            rows.append(fact("bangle_tag", bangle_id, tag))
    for wriggle_id in WRIGGLES:
        rows.append(fact("wriggle", wriggle_id))
        for tag in WRIGGLES[wriggle_id].tags:
            rows.append(fact("wriggle_tag", wriggle_id, tag))
    if params is not None:
        rows.append(fact("chosen", params.tamarind, params.ghost, params.bangle, params.wriggle))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n"


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_program()):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(piece) for piece in atom))
    return combos


def verify_asp_world() -> str:
    import asp

    python_valid = {(p.tamarind, p.ghost, p.bangle, p.wriggle) for p in all_params()}
    asp_valid = asp_valid_combos()
    if python_valid != asp_valid:
        only_python = sorted(python_valid - asp_valid)
        only_asp = sorted(asp_valid - python_valid)
        raise StoryError(f"ASP mismatch: only_python={only_python[:5]} only_asp={only_asp[:5]}")

    for params in all_params():
        sample = generate(params)
        text = sample.story.lower()
        if not all(word in text for word in ("bangle", "tamarind", "wriggle")):
            raise StoryError(f"required seed words missing in generated story for params={params}")
        if sample.world.facts.get("ending") != "reconciliation":
            raise StoryError(f"reconciliation did not complete for params={params}")
        if len(sample.story_qa) != 3 or len(sample.world_qa) != 3:
            raise StoryError(f"story did not emit three QA entries per set for params={params}")
        if sample.world.get("tamarind").meters["stability"] < 0.5:
            raise StoryError(f"tamarind stability not reached for params={params}")

    sample_count = len(python_valid)
    return (
        f"OK: Python and ASP agree on {sample_count} valid reconciliation stories,"
        f" and all generated stories include bangle, tamarind, wriggle while reaching reconciliation."
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit = any(
        value is not None for value in (args.tamarind, args.ghost, args.bangle, args.wriggle)
    )
    if explicit:
        params = StoryParams(
            tamarind=args.tamarind or rng.choice(list(TAMARIND_TREES)),
            ghost=args.ghost or rng.choice(list(GHOSTS)),
            bangle=args.bangle or rng.choice(list(BANGLES)),
            wriggle=args.wriggle or rng.choice(list(WRIGGLES)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    candidates = all_params()
    if not candidates:
        raise StoryError("no valid parameter combinations exist")
    return rng.choice(candidates)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return

    rng = random.Random(args.seed)
    explicit = any(value is not None for value in (args.tamarind, args.ghost, args.bangle, args.wriggle))
    if explicit:
        for _ in range(max(1, args.n)):
            yield generate(resolve_params(args, rng))
        return

    combos = all_params()
    rng.shuffle(combos)
    count = max(1, args.n)
    for index in range(count):
        candidate = combos[index % len(combos)]
        yield generate(
            StoryParams(
                tamarind=candidate.tamarind,
                ghost=candidate.ghost,
                bangle=candidate.bangle,
                wriggle=candidate.wriggle,
                seed=args.seed,
            )
        )


def _trace_lines(world: StoryWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    for ent in world.entities.values():
        lines.append(f"- {ent.id}: meters={dict(ent.meters)} memes={dict(ent.memes)}")
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
                header = f"### tamarind={sample.params.tamarind} ghost={sample.params.ghost} bangle={sample.params.bangle} wriggle={sample.params.wriggle}"
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
