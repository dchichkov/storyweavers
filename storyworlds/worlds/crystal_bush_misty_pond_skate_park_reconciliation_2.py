#!/usr/bin/env python3
"""A mystery-leaning skate-park storyworld about a missing bell, a rhyme, and reconciliation.

Internal source tale:
Two young skaters practice a dusk line at a skate park beside a crystal bush and
misty pond. The tiny brass beat bell they use to keep time goes missing. One
friend leaves a rhyming clue because he saw where the bell went, but the other
friend mistakes the rhyme for teasing because they are already tense. When they
stop blaming each other and follow the physical evidence, they recover the bell,
understand the clue, and reconcile before trying the line again.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class PracticeRoute:
    id: str
    name: str
    opening: str
    loss: str
    ending: str


@dataclass(frozen=True)
class RhymeClue:
    id: str
    place: str
    line: str
    clue_note: str


@dataclass(frozen=True)
class Mystery:
    id: str
    place: str
    trap: str
    motion: str
    evidence: str
    discovery: str
    aftereffect: str


@dataclass(frozen=True)
class RecoveryTool:
    id: str
    solves: str
    label: str
    action: str
    proof: str


@dataclass(frozen=True)
class ReconciliationStyle:
    id: str
    apology: str
    response: str
    closing_image: str


@dataclass(frozen=True)
class StoryParams:
    route: str
    rhyme: str
    mystery: str
    tool: str
    reconciliation: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class SkateParkWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "SkateParkWorld":
        return copy.deepcopy(self)


ROUTES: dict[str, PracticeRoute] = {
    "rail": PracticeRoute(
        id="rail",
        name="the comet rail",
        opening="They started at the comet rail, where each landing flashed and rang against the evening air.",
        loss="Mina clipped the rail a little crooked, laughed, and rolled back toward the bench for the next try.",
        ending="they floated past the comet rail with one shared count and one shared grin",
    ),
    "banks": PracticeRoute(
        id="banks",
        name="the moon banks",
        opening="They warmed up on the moon banks, where the smooth slopes made every wheel whisper twice.",
        loss="Mina cut across the second bank, then circled back for the bell before the next timed run.",
        ending="they stitched the moon banks into one clean silver line",
    ),
    "bowl": PracticeRoute(
        id="bowl",
        name="the owl bowl",
        opening="They saved the owl bowl for dusk, because its curved walls held echoes like a secret being repeated.",
        loss="Mina carved high once, then coasted to the bench to clip the bell back on for the full routine.",
        ending="they crossed the lip of the owl bowl together as if the mystery had made their timing tighter",
    ),
}

RHYMES: dict[str, RhymeClue] = {
    "bush_hush": RhymeClue(
        id="bush_hush",
        place="bush",
        line='Pax had chalked: "Past the whispering rush, find the beat in the crystal bush."',
        clue_note="The chalk couplet pointed toward the glittering bush by the fence.",
    ),
    "bush_flash": RhymeClue(
        id="bush_flash",
        place="bush",
        line='Pax had written: "Where bright branches swish, seek the bell in the crystal bush."',
        clue_note="The neat rhyme aimed straight at the sparkling branches beyond the ramps.",
    ),
    "pond_beyond": RhymeClue(
        id="pond_beyond",
        place="pond",
        line='Pax had chalked: "When the wheel-song fades beyond, bend and listen by the misty pond."',
        clue_note="The chalk words led toward the fog-soft boards by the pond edge.",
    ),
    "pond_respond": RhymeClue(
        id="pond_respond",
        place="pond",
        line='Pax had written: "If the lost bell will not respond, kneel down low by the misty pond."',
        clue_note="The couplet clearly pointed toward the pond walk and its pale rail.",
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "bush_snag": Mystery(
        id="bush_snag",
        place="bush",
        trap="snag",
        motion="A breeze had lifted the ribbon loop and swung the brass bell off the bench into the crystal bush.",
        evidence="a spray of tiny clear leaves trembled harder than the rest, and one branch held a new scratch of brass",
        discovery="The bell was hanging in the branch tips, bright as a small moon caught in glass leaves.",
        aftereffect="When the branch sprang back, the bell gave one clear note that sounded exactly like the beat they had lost.",
    ),
    "bush_mulch": Mystery(
        id="bush_mulch",
        place="bush",
        trap="mulch",
        motion="A wheel bump had knocked the brass bell down the curb, where it tucked itself under the silver mulch beneath the crystal bush.",
        evidence="there was a tiny furrow in the mulch and a half-hidden circle of brass dusted with glitter",
        discovery="The bell was lying under the dry silver chips at the root of the bush, with only one edge showing.",
        aftereffect="As soon as the chips were brushed away, the brass gleam proved the bell had been buried by motion, not by a trick.",
    ),
    "pond_reeds": Mystery(
        id="pond_reeds",
        place="pond",
        trap="reeds",
        motion="A rolling board had nudged the bell across the damp planks until it slipped under the reeds beside the misty pond.",
        evidence="a wet crescent on the boards ended beside bent reeds, and something warm-colored blinked there through the mist",
        discovery="The bell was tucked under the reeds, where pond drops kept turning its brass rim bright and dim.",
        aftereffect="When the reeds opened, the children could see the wet path the bell had taken all the way from the bench.",
    ),
    "pond_grate": Mystery(
        id="pond_grate",
        place="pond",
        trap="grate",
        motion="The sloped path had rolled the bell to the pond drain, where it clicked behind a narrow grate.",
        evidence="small half-moon scratches in the grit ended at the drain, and a brass wink flashed through the slots",
        discovery="The bell was trapped just behind the grate, shivering with each soft drip from the pond rail.",
        aftereffect="The little metal ping from the grate matched the sound Pax had heard before he wrote the rhyme.",
    ),
}

TOOLS: dict[str, RecoveryTool] = {
    "glove": RecoveryTool(
        id="glove",
        solves="snag",
        label="a padded glove",
        action="Pax steadied the branch while Mina reached in with a padded glove and twisted the bell free.",
        proof="The glove kept the sharp crystal leaves from scratching her fingers while the branch stopped rattling.",
    ),
    "brush": RecoveryTool(
        id="brush",
        solves="mulch",
        label="a soft deck brush",
        action="Mina used a soft deck brush to sweep the silver chips aside while Pax cupped his hand at the root to catch the bell.",
        proof="The brush moved the loose mulch without knocking the tiny bell deeper out of sight.",
    ),
    "net": RecoveryTool(
        id="net",
        solves="reeds",
        label="the park's stray-ball net",
        action="Mina lowered the park's stray-ball net between the reeds while Pax guided the rim until the bell slid into the mesh.",
        proof="The wet reeds bent into the net, and the brass bell clicked against the ring instead of slipping back into the water grass.",
    ),
    "magnet": RecoveryTool(
        id="magnet",
        solves="grate",
        label="a shoelace magnet",
        action="Pax tied a small magnet to a shoelace and lowered it through the grate while Mina kept the line steady.",
        proof="Once the magnet caught, the bell rose cleanly, showing it had only been trapped behind the grate.",
    ),
}

RECONCILIATIONS: dict[str, ReconciliationStyle] = {
    "own_blame": ReconciliationStyle(
        id="own_blame",
        apology='"I let my guess race faster than the truth," Mina said. "Next time I will follow the clue before I blame you."',
        response='Pax nodded and said, "That is the kind of rhyme a real partner can trust."',
        closing_image="the two friends bumping fists on the bench before rolling back into the dusk",
    ),
    "shared_rhyme": ReconciliationStyle(
        id="shared_rhyme",
        apology='"Quick blame, dim light; slow search, truth bright," Mina said. Pax smiled and answered, "Side by side is how we set it right."',
        response="They both laughed, because the rhyme sounded warmer once it belonged to both of them.",
        closing_image="their chalked couplet glowing pale on the bench while their boards waited nose to nose",
    ),
    "promise_rhyme": ReconciliationStyle(
        id="promise_rhyme",
        apology='"If a mystery feels mean, we check what can be seen," Mina said. "I should have looked at the ground and listened to you."',
        response='Pax touched the bell and said, "Now the clue and the truth sound the same again."',
        closing_image="the brass bell resting between them for one small second before Mina clipped it back on",
    ),
}

PLACE_LABELS = {
    "bush": "the crystal bush",
    "pond": "the misty pond",
}

TRAP_LABELS = {
    "snag": "a high branch snag",
    "mulch": "loose silver mulch",
    "reeds": "wet reeds",
    "grate": "a narrow drain grate",
}


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.route not in ROUTES:
        return False, f"unknown route: {params.route}"
    if params.rhyme not in RHYMES:
        return False, f"unknown rhyme: {params.rhyme}"
    if params.mystery not in MYSTERIES:
        return False, f"unknown mystery: {params.mystery}"
    if params.tool not in TOOLS:
        return False, f"unknown tool: {params.tool}"
    if params.reconciliation not in RECONCILIATIONS:
        return False, f"unknown reconciliation: {params.reconciliation}"
    rhyme = RHYMES[params.rhyme]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    if rhyme.place != mystery.place:
        return False, "the rhyming clue must point to the place where the bell really went"
    if tool.solves != mystery.trap:
        return False, "the recovery tool must match the way the bell is trapped"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for route in ROUTES:
        for rhyme in RHYMES:
            for mystery in MYSTERIES:
                for tool in TOOLS:
                    for reconciliation in RECONCILIATIONS:
                        params = StoryParams(
                            route=route,
                            rhyme=rhyme,
                            mystery=mystery,
                            tool=tool,
                            reconciliation=reconciliation,
                        )
                        if valid_params(params)[0]:
                            combos.append(params)
    return combos


def make_world(params: StoryParams) -> SkateParkWorld:
    route = ROUTES[params.route]
    rhyme = RHYMES[params.rhyme]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    reconciliation = RECONCILIATIONS[params.reconciliation]
    world = SkateParkWorld(params)
    world.add(
        Entity(
            id="mina",
            kind="character",
            type="girl",
            label="Mina",
            role="accuser",
            traits=["quick", "serious"],
        )
    )
    world.add(
        Entity(
            id="pax",
            kind="character",
            type="boy",
            label="Pax",
            role="clue_writer",
            traits=["observant", "rhyming"],
        )
    )
    world.add(
        Entity(
            id="coach",
            kind="character",
            type="woman",
            label="Coach Lila",
            role="coach",
            traits=["steady"],
        )
    )
    world.add(Entity(id="park", kind="place", type="skate_park", label="the skate park"))
    world.add(Entity(id="bush", kind="place", type="bush", label="the crystal bush"))
    world.add(Entity(id="pond", kind="place", type="pond", label="the misty pond"))
    world.add(Entity(id="bell", kind="object", type="bell", label="the brass beat bell", owner="mina"))
    world.add(Entity(id="pair", kind="group", type="duo", label="the two skaters"))

    world.get("park").meters["mist"] = 1.0
    world.get("park").meters["echo"] = 1.0
    world.get("bush").meters["glitter"] = 1.0
    world.get("pond").meters["fog"] = 1.0
    world.get("bell").meters["present"] = 1.0
    world.get("bell").attrs["location"] = "bench"
    world.get("pair").meters["ready"] = 1.0
    world.get("pair").memes["trust"] = 2.0
    world.get("pair").memes["joy"] = 1.0
    world.get("mina").memes["trust"] = 1.0
    world.get("pax").memes["trust"] = 1.0

    world.facts.update(
        route_name=route.name,
        rhyme_line=rhyme.line,
        rhyme_note=rhyme.clue_note,
        mystery_motion=mystery.motion,
        mystery_evidence=mystery.evidence,
        mystery_discovery=mystery.discovery,
        mystery_aftereffect=mystery.aftereffect,
        resolved_place=PLACE_LABELS[mystery.place],
        trap_label=TRAP_LABELS[mystery.trap],
        tool_label=tool.label,
        apology_text=reconciliation.apology,
        response_text=reconciliation.response,
        closing_image=reconciliation.closing_image,
    )
    return world


def opening(world: SkateParkWorld) -> None:
    route = ROUTES[world.params.route]
    pair = world.get("pair")
    pair.memes["anticipation"] += 1.0
    world.record(
        "opening",
        "At the edge of the skate park, the crystal bush glittered in the last light and the misty pond held the dusk like a silver secret.",
        "park",
    )
    world.record(
        "setup",
        f"{route.opening} Mina and Pax were practicing a timed dusk line, and Mina clipped the brass beat bell to her board so each turn could land on the same bright note.",
        "pair",
        "bell",
    )


def bell_goes_missing(world: SkateParkWorld) -> None:
    route = ROUTES[world.params.route]
    mystery = MYSTERIES[world.params.mystery]
    bell = world.get("bell")
    pair = world.get("pair")
    bell.meters["present"] = 0.0
    bell.meters["lost"] = 1.0
    bell.attrs["location"] = mystery.place
    pair.meters["ready"] = 0.0
    pair.memes["worry"] += 1.0
    world.record(
        "loss",
        f"{route.loss} When she reached for the brass beat bell, it was gone. {mystery.motion}",
        "mina",
        "bell",
    )


def reveal_rhyme(world: SkateParkWorld) -> None:
    rhyme = RHYMES[world.params.rhyme]
    pax = world.get("pax")
    pax.memes["helpful"] += 1.0
    world.record(
        "rhyme",
        f"In a stripe of chalk on the bench, {rhyme.line} {rhyme.clue_note}",
        "pax",
        rhyme.place,
    )


def misunderstanding(world: SkateParkWorld) -> None:
    mina = world.get("mina")
    pax = world.get("pax")
    pair = world.get("pair")
    mina.memes["blame"] += 1.0
    mina.memes["hurt"] += 0.5
    pax.memes["hurt"] += 1.0
    pair.memes["trust"] -= 1.25
    world.record(
        "misunderstanding",
        '"Did you turn my missing bell into a joke?" Mina asked. The rhyme was neat and playful, so in her worry it felt more like teasing than help, and Pax went quiet because he had meant it as a map.',
        "mina",
        "pax",
    )


def turn_toward_evidence(world: SkateParkWorld) -> None:
    mystery = MYSTERIES[world.params.mystery]
    pair = world.get("pair")
    pair.memes["reflection"] += 1.0
    if mystery.id == "bush_snag":
        clue = (
            "Coach Lila crouched by the bench and pointed toward a shaken branch by the fence. "
            '"Mysteries trust marks more than moods," she said. "See what the world is saying before you decide what your friend meant."'
        )
    elif mystery.id == "bush_mulch":
        clue = (
            "Coach Lila tapped the curb with her shoe and pointed to a thin furrow in the silver chips under the bush. "
            '"Mysteries trust marks more than moods," she said. "See what the world is saying before you decide what your friend meant."'
        )
    else:
        clue = (
            "Coach Lila pointed to a wet arc on the planks and a dim brass blink through the fog. "
            '"A real clue leaves a trail," she said. "Follow the ground before you follow your temper."'
        )
    world.record("turn", clue, "coach", "pair")


def search_together(world: SkateParkWorld) -> None:
    mystery = MYSTERIES[world.params.mystery]
    pair = world.get("pair")
    mina = world.get("mina")
    pax = world.get("pax")
    pair.memes["trust"] += 0.5
    mina.memes["curiosity"] += 1.0
    pax.memes["courage"] += 1.0
    world.record(
        "search",
        f"So Mina and Pax read the chalk again and walked the path together. Soon they found the proof: {mystery.evidence}.",
        "pair",
        mystery.place,
    )


def recover_bell(world: SkateParkWorld) -> None:
    mystery = MYSTERIES[world.params.mystery]
    tool = TOOLS[world.params.tool]
    bell = world.get("bell")
    pair = world.get("pair")
    bell.meters["lost"] = 0.0
    bell.meters["present"] = 1.0
    bell.meters["recovered"] = 1.0
    bell.attrs["location"] = "mina_board"
    pair.meters["ready"] = 1.0
    pair.memes["relief"] += 1.0
    world.record(
        "recover",
        f"{mystery.discovery} {tool.action} {tool.proof} {mystery.aftereffect}",
        "pair",
        "bell",
    )


def reconcile(world: SkateParkWorld) -> None:
    style = RECONCILIATIONS[world.params.reconciliation]
    mina = world.get("mina")
    pax = world.get("pax")
    pair = world.get("pair")
    mina.memes["blame"] = 0.0
    mina.memes["apology"] += 1.0
    pax.memes["hurt"] = 0.0
    pax.memes["forgiveness"] += 1.0
    pair.memes["trust"] += 1.75
    pair.memes["reconciliation"] += 1.0
    world.facts["reconciled"] = True
    world.record(
        "reconcile",
        f"{style.apology} {style.response}",
        "mina",
        "pax",
    )


def closing(world: SkateParkWorld) -> None:
    route = ROUTES[world.params.route]
    style = RECONCILIATIONS[world.params.reconciliation]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "ending",
        f'Mina clipped the bell back onto her board, gave it one bright tap, and the friends tried the line again. This time {route.ending}. Behind them, the crystal bush kept its glassy hush, the misty pond held one last pale ring, and the mystery ended with {style.closing_image}.',
        "pair",
        "park",
    )


def tell(params: StoryParams) -> SkateParkWorld:
    world = make_world(params)
    opening(world)
    world.para()
    bell_goes_missing(world)
    reveal_rhyme(world)
    misunderstanding(world)
    turn_toward_evidence(world)
    world.para()
    search_together(world)
    recover_bell(world)
    reconcile(world)
    world.para()
    closing(world)
    return world


def generation_prompts(world: SkateParkWorld) -> list[str]:
    route = ROUTES[world.params.route]
    tool = TOOLS[world.params.tool]
    return [
        'Write a child-facing mystery set in a skate park that clearly includes the words "crystal bush" and "misty pond."',
        f"Make the central problem a missing brass beat bell during practice at {route.name}, and let a rhyme clue guide the turn toward physical evidence.",
        f"Resolve the story through reconciliation, a truthful apology, and a concrete recovery using {tool.label}.",
    ]


def story_grounded_qa(world: SkateParkWorld) -> list[QAItem]:
    mystery = MYSTERIES[world.params.mystery]
    tool = TOOLS[world.params.tool]
    return [
        QAItem(
            question="Why did Mina think Pax had made the problem worse?",
            answer=(
                "Mina saw that the brass beat bell was missing and found Pax's rhyme on the bench instead of a plain explanation. "
                "Because she was already worried and the couplet sounded playful, she mistook his clue for teasing."
            ),
        ),
        QAItem(
            question="Where had the missing bell really gone?",
            answer=(
                f"The bell had really gone to {PLACE_LABELS[mystery.place]}. "
                f"{mystery.motion} That is why Pax's rhyme pointed there."
            ),
        ),
        QAItem(
            question="What clue showed the children they should trust the rhyme?",
            answer=(
                f"They found physical proof that matched the couplet: {mystery.evidence}. "
                "Once the world and the words agreed, the rhyme stopped looking like a prank and started looking like a map."
            ),
        ),
        QAItem(
            question="How did Mina and Pax solve the mystery and make up?",
            answer=(
                f"They searched together and used {tool.label} to get the bell back. "
                "The recovery proved Pax had been helping, so Mina apologized and the two friends practiced side by side again."
            ),
        ),
    ]


def world_knowledge_qa(world: SkateParkWorld) -> list[QAItem]:
    mystery = MYSTERIES[world.params.mystery]
    tool = TOOLS[world.params.tool]
    return [
        QAItem(
            question="Why can a tiny metal part vanish quickly at a skate park?",
            answer=(
                "A small metal part can bounce, roll, or slip into cracks before anyone notices. "
                "Ramps, reeds, mulch, and drain grates can hide something shiny in only a second."
            ),
        ),
        QAItem(
            question="How can a rhyme help in a mystery?",
            answer=(
                "A rhyme can help someone remember a clue without using many words. "
                "In this world, the couplet carried the place of the bell like a small song-map."
            ),
        ),
        QAItem(
            question=f"Why was {tool.label} the right tool this time?",
            answer=(
                f"It was the right tool because the bell was trapped by {TRAP_LABELS[mystery.trap]}. "
                f"That tool fit the physical problem and let the children recover the bell safely."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(R, H, M, T, C) :-
    route(R), rhyme(H), mystery(M), tool(T), reconciliation(C),
    rhyme_place(H, P), mystery_place(M, P),
    mystery_trap(M, K), tool_solves(T, K).

ok :- chosen(R, H, M, T, C), valid(R, H, M, T, C).

#show valid/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for route in ROUTES:
        rows.append(fact("route", route))
    for rhyme_key, rhyme in RHYMES.items():
        rows.append(fact("rhyme", rhyme_key))
        rows.append(fact("rhyme_place", rhyme_key, rhyme.place))
    for mystery_key, mystery in MYSTERIES.items():
        rows.append(fact("mystery", mystery_key))
        rows.append(fact("mystery_place", mystery_key, mystery.place))
        rows.append(fact("mystery_trap", mystery_key, mystery.trap))
    for tool_key, tool in TOOLS.items():
        rows.append(fact("tool", tool_key))
        rows.append(fact("tool_solves", tool_key, tool.solves))
    for reconciliation in RECONCILIATIONS:
        rows.append(fact("reconciliation", reconciliation))
    if params is not None:
        rows.append(
            fact(
                "chosen",
                params.route,
                params.rhyme,
                params.mystery,
                params.tool,
                params.reconciliation,
            )
        )
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    from asp import atoms, one_model

    combos: set[tuple[str, str, str, str, str]] = set()
    for combo in atoms(one_model(asp_program()), "valid"):
        combos.add(tuple(str(part) for part in combo))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = {
        (p.route, p.rhyme, p.mystery, p.tool, p.reconciliation)
        for p in all_params()
    }
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )
    for params in all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        story = sample.story
        if "crystal bush" not in story or "misty pond" not in story or "skate park" not in story:
            raise StoryError(f"required seed language missing from story for params={params}")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if not sample.world.facts.get("reconciled"):
            raise StoryError(f"story did not reconcile for params={params}")
        if sample.world.get("bell").meters["recovered"] < 1.0:
            raise StoryError(f"bell was not recovered for params={params}")
        if "  " in story or "{}" in story:
            raise StoryError(f"story leaked placeholder/scaffold text for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid skate-park mysteries, "
        "and every generated story recovers the bell and reconciles the friends."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--rhyme", choices=sorted(RHYMES))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--reconciliation", choices=sorted(RECONCILIATIONS))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit = any(
        getattr(args, key) is not None
        for key in ("route", "rhyme", "mystery", "tool", "reconciliation")
    )
    if explicit:
        params = StoryParams(
            route=args.route or rng.choice(list(ROUTES)),
            rhyme=args.rhyme or rng.choice(list(RHYMES)),
            mystery=args.mystery or rng.choice(list(MYSTERIES)),
            tool=args.tool or rng.choice(list(TOOLS)),
            reconciliation=args.reconciliation or rng.choice(list(RECONCILIATIONS)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    choice = rng.choice(all_params())
    return StoryParams(
        route=choice.route,
        rhyme=choice.rhyme,
        mystery=choice.mystery,
        tool=choice.tool,
        reconciliation=choice.reconciliation,
        seed=args.seed,
    )


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    explicit = any(
        getattr(args, key) is not None
        for key in ("route", "rhyme", "mystery", "tool", "reconciliation")
    )
    if explicit:
        rng = random.Random(args.seed)
        for index in range(max(1, args.n)):
            params = resolve_params(args, rng)
            params = StoryParams(
                route=params.route,
                rhyme=params.rhyme,
                mystery=params.mystery,
                tool=params.tool,
                reconciliation=params.reconciliation,
                seed=args.seed + index,
            )
            yield generate(params)
        return
    combos = all_params()
    rng = random.Random(args.seed)
    rng.shuffle(combos)
    count = max(1, args.n)
    for index in range(count):
        chosen = combos[index % len(combos)]
        yield generate(
            StoryParams(
                route=chosen.route,
                rhyme=chosen.rhyme,
                mystery=chosen.mystery,
                tool=chosen.tool,
                reconciliation=chosen.reconciliation,
                seed=args.seed + index,
            )
        )


def trace_lines(world: SkateParkWorld) -> list[str]:
    bell = world.get("bell")
    pair = world.get("pair")
    mina = world.get("mina")
    pax = world.get("pax")
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  bell_location={location} present={present:.1f} recovered={recovered:.1f}".format(
            location=bell.attrs.get("location", "unknown"),
            present=bell.meters["present"],
            recovered=bell.meters["recovered"],
        )
    )
    lines.append(
        "  pair_trust={trust:.2f} pair_ready={ready:.1f} mina_blame={blame:.1f} pax_forgiveness={forgiveness:.1f}".format(
            trust=pair.memes["trust"],
            ready=pair.meters["ready"],
            blame=mina.memes["blame"],
            forgiveness=pax.memes["forgiveness"],
        )
    )
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        payload = sample.to_dict()
        if header:
            payload = {"header": header, **payload}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace:
        print()
        print("\n".join(trace_lines(sample.world)))
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
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
                p = sample.params
                header = (
                    f"### route={p.route} rhyme={p.rhyme} mystery={p.mystery} "
                    f"tool={p.tool} reconciliation={p.reconciliation}"
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
