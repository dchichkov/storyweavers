#!/usr/bin/env python3
"""A small animal storyworld about hereditary ritual, marsh mythology, and friendship.

Internal source tale:
Maro, a young otter, inherits a family ritual object and feels pressed to prove
he can carry an old marsh promise by himself. The local mythology sounds grand
enough to make him lonely, but the real trouble is physical: the heirloom or
its setup has gone wrong in a concrete way. His friend Pip stays beside him,
reads the old tale more kindly, and helps repair the object. When the ritual
works at last, the ending image shows that hereditary work in this world is not
a solitary burden but something friendship can help complete.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from results import QAItem, StoryError, StorySample


SITE_NAMES: dict[str, str] = {
    "moon_pool": "Moon Pool",
    "heron_stone": "Heron Stone",
    "firefly_bank": "Firefly Bank",
    "reed_stage": "the Reed Stage",
}


@dataclass(frozen=True)
class Grove:
    id: str
    name: str
    opening: str
    ending: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Myth:
    id: str
    site: str
    claim: str
    friend_line: str
    awakening: str
    lonely_fear: str


@dataclass(frozen=True)
class Heirloom:
    id: str
    site: str
    kind: str
    name: str
    inheritance: str
    attempt: str


@dataclass(frozen=True)
class Problem:
    id: str
    name: str
    kind: str
    discovery: str
    block: str
    risk: str
    result: str


@dataclass(frozen=True)
class Method:
    id: str
    name: str
    solves: str
    tool: str
    action: str
    proof: str


@dataclass
class StoryParams:
    grove: str
    myth: str
    heirloom: str
    problem: str
    method: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
    place: str | None = None


@dataclass
class MarshWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.entities[entity.role] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        place: str | None = None,
    ) -> None:
        self.history.append(Event(event_id, text, actor, target, place))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


GROVES: dict[str, Grove] = {
    "reedbank_hollow": Grove(
        id="reedbank_hollow",
        name="Reedbank Hollow",
        opening=(
            "In Reedbank Hollow, the stream widened into dark, still water, and the tall reeds leaned "
            "close as if they liked listening to secrets."
        ),
        ending=(
            "Maro and Pip walked home shoulder to shoulder while silver water rings widened under the reeds "
            "and made the whole hollow look newly awake."
        ),
        sites=("moon_pool", "reed_stage"),
    ),
    "heron_bend": Grove(
        id="heron_bend",
        name="Heron Bend",
        opening=(
            "At Heron Bend, the bank curved around a flat gray stone, and white feathers from the marsh birds "
            "rested among the mint like scraps of cloud."
        ),
        ending=(
            "The bend kept giving back soft sounds from water and wing, and Maro no longer felt alone inside them."
        ),
        sites=("heron_stone", "moon_pool"),
    ),
    "firefly_meadow": Grove(
        id="firefly_meadow",
        name="Firefly Meadow",
        opening=(
            "Beside Firefly Meadow, dusk always came gently, and the grass shone at the tips as if tiny lamps were "
            "waiting for someone to remember them."
        ),
        ending=(
            "Long after the work was done, the meadow stayed lit in little gold points, and the path home looked kind."
        ),
        sites=("firefly_bank", "reed_stage"),
    ),
}


MYTHS: dict[str, Myth] = {
    "moon_koi": Myth(
        id="moon_koi",
        site="moon_pool",
        claim=(
            "Their marsh mythology said silver moon koi would rise only when the family keeper sent one honest note "
            "across Moon Pool."
        ),
        friend_line=(
            "One worn line in the old tale said the first keeper never played alone; a friend steadied the reeds and "
            "listened for the true note."
        ),
        awakening=(
            "Under the dark water, silver koi turned in a bright circle and opened a shining lane through the reeds."
        ),
        lonely_fear=(
            "Maro feared that if he failed, he would let the whole family line look smaller than the story promised."
        ),
    ),
    "heron_echo": Myth(
        id="heron_echo",
        site="heron_stone",
        claim=(
            "The bend's marsh mythology promised that the white heron on the standing stone would answer a rightful "
            "drum with a guiding echo."
        ),
        friend_line=(
            "In the oldest version, two young animals kept the beat together until the heron's echo came back whole."
        ),
        awakening=(
            "The stone heron answered with one deep echo that rolled over the bend like a soft bell."
        ),
        lonely_fear=(
            "Maro feared the family rhythm would flatten under his paws and make the inheritance feel too heavy for him."
        ),
    ),
    "lantern_moths": Myth(
        id="lantern_moths",
        site="firefly_bank",
        claim=(
            "The bank-side marsh mythology said moon moths gathered only when the hereditary lantern bowl carried a "
            "calm light above the grass."
        ),
        friend_line=(
            "Grandmother's favorite line said a borrowed paw may guard the flame, because kind help does not weaken a "
            "family promise."
        ),
        awakening=(
            "Moon moths and fireflies drifted around the bowl until the whole bank glowed honey-gold."
        ),
        lonely_fear=(
            "Maro feared the old promise would dim in his paws before anyone saw what his family had protected."
        ),
    ),
    "reed_chorus": Myth(
        id="reed_chorus",
        site="reed_stage",
        claim=(
            "The reed-bed marsh mythology said the water reeds would part into a little singing bridge when the family "
            "crown sat whole and the keeper sang kindly."
        ),
        friend_line=(
            "The first keeper in the tale had a friend beside her, plaiting the last stems while the song rose."
        ),
        awakening=(
            "The reeds lifted and crossed themselves into a green footbridge that sang in the breeze."
        ),
        lonely_fear=(
            "Maro feared the welcome song would break in public and make him look clumsy with his own family's work."
        ),
    ),
}


HEIRLOOMS: dict[str, Heirloom] = {
    "shell_flute": Heirloom(
        id="shell_flute",
        site="moon_pool",
        kind="breath",
        name="shell flute",
        inheritance=(
            "The shell flute was hereditary in Maro's family; his mother wrapped it in the same blue cloth that had "
            "once belonged to his grandmother."
        ),
        attempt="he raised the shell flute and blew the soft rising note his mother had taught him.",
    ),
    "pebble_drum": Heirloom(
        id="pebble_drum",
        site="heron_stone",
        kind="echo",
        name="pebble drum",
        inheritance=(
            "The pebble drum was hereditary in Maro's family, passed down whenever the oldest child was ready to learn "
            "the bend song."
        ),
        attempt="he set the pebble drum on his knees and tried the steady calling beat.",
    ),
    "lantern_bowl": Heirloom(
        id="lantern_bowl",
        site="firefly_bank",
        kind="light",
        name="lantern bowl",
        inheritance=(
            "The lantern bowl was hereditary in Maro's family, and each elder had carried it across the grass on the "
            "first warm evening of spring."
        ),
        attempt="he lifted the lantern bowl and tried to wake its patient little flame.",
    ),
    "reed_crown": Heirloom(
        id="reed_crown",
        site="reed_stage",
        kind="weave",
        name="reed crown",
        inheritance=(
            "The reed crown was hereditary in Maro's family; each season another careful paw repaired it and passed it on."
        ),
        attempt="he settled the reed crown over his ears and began the gentle welcome song.",
    ),
}


PROBLEMS: dict[str, Problem] = {
    "silt_plug": Problem(
        id="silt_plug",
        name="silt plug",
        kind="breath",
        discovery="A dark plug of silt had dried inside the flute's narrow throat.",
        block="Only a damp gasp came out instead of a clean note.",
        risk="The broken sound made Maro's stomach dip, because the promise seemed stuck before it even crossed the water.",
        result="When the plug slipped free, the flute sent out a round silver note.",
    ),
    "slack_lacing": Problem(
        id="slack_lacing",
        name="slack lacing",
        kind="echo",
        discovery="The willow lacing under the drum had loosened and let the skin sag.",
        block="The beat thudded flat and shy instead of flying to the stone.",
        risk="Maro felt the story shrinking around him, as if he had inherited a silence instead of a song.",
        result="Once the lacing was firm again, the drum answered with a brave, full beat.",
    ),
    "wet_wick": Problem(
        id="wet_wick",
        name="wet wick",
        kind="light",
        discovery="The wick had drunk mist all morning and would only smoke and shiver.",
        block="The little flame bent low and refused to stand.",
        risk="Maro worried the old promise would go dim before the watching meadow could believe in it.",
        result="After the wick warmed and caught, the bowl held a calm golden light.",
    ),
    "split_binding": Problem(
        id="split_binding",
        name="split binding",
        kind="weave",
        discovery="One old binding had split, so the crown listed and dropped reeds onto Maro's nose.",
        block="The welcome song broke every time the loose stems brushed his face.",
        risk="Maro thought the family task might fall apart before anyone heard the kind part of it.",
        result="When the binding held again, the crown sat steady and sang with the wind.",
    ),
}


METHODS: dict[str, Method] = {
    "stream_rinse": Method(
        id="stream_rinse",
        name="stream rinse",
        solves="breath",
        tool="a smooth rush stem and clear stream water",
        action=(
            "Pip held a smooth rush stem steady while Maro rinsed clear stream water through the flute until the dark "
            "silt curled out."
        ),
        proof="The shell flute felt light again, and the next breath found its true path.",
    ),
    "double_beat": Method(
        id="double_beat",
        name="double beat",
        solves="echo",
        tool="a willow cord and two patient paws",
        action=(
            "Pip pulled the willow cord snug while Maro tapped a patient practice beat, tightening the skin a little at a time."
        ),
        proof="The drum skin settled firm beneath Maro's paws, ready to carry a real echo.",
    ),
    "shared_spark": Method(
        id="shared_spark",
        name="shared spark",
        solves="light",
        tool="a dry thistle tuft sheltered in Pip's acorn cap",
        action=(
            "Pip sheltered a dry thistle spark inside his acorn cap while Maro warmed the wick between his paws until it "
            "was ready to drink the flame."
        ),
        proof="The wick stopped shivering and held a still, honey-colored flame.",
    ),
    "patient_plait": Method(
        id="patient_plait",
        name="patient plait",
        solves="weave",
        tool="fresh reed strands and Pip's nimble fingers",
        action=(
            "Pip threaded fresh reed strands through the split places while Maro bent the old crown slowly, so none of "
            "the elder stems snapped."
        ),
        proof="The crown sat whole again, and a soft green hum moved through it.",
    ),
}


def site_name(site_id: str) -> str:
    return SITE_NAMES[site_id]


def valid_params(params: StoryParams) -> tuple[bool, str]:
    grove = GROVES[params.grove]
    myth = MYTHS[params.myth]
    heirloom = HEIRLOOMS[params.heirloom]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]
    if myth.site not in grove.sites:
        return (
            False,
            f"{grove.name} does not host the rite at {site_name(myth.site)}, so that mythology does not fit this grove.",
        )
    if heirloom.site != myth.site:
        return (
            False,
            f"The {heirloom.name} belongs to {site_name(heirloom.site)}, not to the mythology centered on {site_name(myth.site)}.",
        )
    if problem.kind != heirloom.kind:
        return (
            False,
            f"The problem '{problem.name}' affects a {problem.kind} heirloom, but the {heirloom.name} is a {heirloom.kind} heirloom.",
        )
    if method.solves != problem.kind:
        return (
            False,
            f"The method '{method.name}' solves {method.solves} trouble, not the {problem.kind} trouble caused by '{problem.name}'.",
        )
    return True, ""


def explain_rejection(grove_id: str, myth_id: str, heirloom_id: str, problem_id: str, method_id: str) -> str:
    ok, reason = valid_params(StoryParams(grove_id, myth_id, heirloom_id, problem_id, method_id))
    if ok:
        return "The requested choices are valid."
    return reason


def all_params() -> list[StoryParams]:
    rows: list[StoryParams] = []
    for grove_id in GROVES:
        for myth_id in MYTHS:
            for heirloom_id in HEIRLOOMS:
                for problem_id in PROBLEMS:
                    for method_id in METHODS:
                        params = StoryParams(grove_id, myth_id, heirloom_id, problem_id, method_id)
                        ok, _ = valid_params(params)
                        if ok:
                            rows.append(params)
    return rows


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    rows = all_params()
    for field_name in ("grove", "myth", "heirloom", "problem", "method"):
        chosen = getattr(args, field_name)
        if chosen is not None:
            rows = [row for row in rows if getattr(row, field_name) == chosen]
    return rows


def build_world(params: StoryParams) -> MarshWorld:
    grove = GROVES[params.grove]
    myth = MYTHS[params.myth]
    heirloom = HEIRLOOMS[params.heirloom]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]
    world = MarshWorld(params=params)
    hero = world.add(
        Entity(
            id="maro",
            kind="animal",
            type="otter",
            label="Maro the young otter",
            role="hero",
            traits=["careful", "earnest"],
            attrs={"mark": "a silver curl above his left paw"},
        )
    )
    friend = world.add(
        Entity(
            id="pip",
            kind="animal",
            type="squirrel",
            label="Pip the squirrel",
            role="friend",
            traits=["nimble", "kind"],
        )
    )
    world.add(
        Entity(
            id="grandmother_sula",
            kind="animal",
            type="otter",
            label="Grandmother Sula",
            role="elder",
            traits=["gentle", "steady"],
        )
    )
    heir = world.add(
        Entity(
            id="heirloom",
            kind="object",
            type=heirloom.kind,
            label=f"the {heirloom.name}",
            role="heirloom",
            attrs={"site": myth.site, "tool": method.tool},
        )
    )
    site = world.add(
        Entity(
            id="rite_site",
            kind="place",
            type="ritual_site",
            label=site_name(myth.site),
            role="site",
        )
    )
    pair = world.add(
        Entity(
            id="pair",
            kind="group",
            type="friendship",
            label="Maro and Pip",
            role="pair",
        )
    )

    hero.meters["steadiness"] = 1.0
    hero.meters["burden"] = 2.0
    hero.memes["belonging"] = 2.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 2.0
    friend.memes["care"] = 2.0
    heir.meters["stuckness"] = 1.0
    heir.meters["ready"] = 0.0
    site.meters["wonder"] = 1.0
    site.meters["awakened"] = 0.0
    pair.memes["friendship"] = 2.0

    world.facts.update(
        {
            "grove_name": grove.name,
            "site_name": site_name(myth.site),
            "myth_id": myth.id,
            "heirloom_name": heirloom.name,
            "problem_name": problem.name,
            "method_name": method.name,
            "method_tool": method.tool,
            "solved": False,
            "awakening": myth.awakening,
            "ending": grove.ending,
            "friend_line": myth.friend_line,
        }
    )
    return world


def prompts_for(params: StoryParams) -> list[str]:
    grove = GROVES[params.grove]
    myth = MYTHS[params.myth]
    heirloom = HEIRLOOMS[params.heirloom]
    return [
        "Write a child-facing animal story about hereditary duty in a gentle marsh.",
        "Use friendship as the turning force, not just decoration.",
        f"Center the plot on the {heirloom.name} at {site_name(myth.site)} in {grove.name}, and let the local mythology matter.",
    ]


def story_qa_for(world: MarshWorld) -> list[QAItem]:
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        QAItem(
            question="Why was Maro nervous when the ritual began?",
            answer=(
                f"Maro was nervous because the {world.facts['problem_name']} kept the {world.facts['heirloom_name']} from working the way his family story promised. "
                f"He also thought a hereditary promise had to be carried alone, so the trouble felt like a test of his whole family line."
            ),
        ),
        QAItem(
            question="How did Pip help solve the problem?",
            answer=(
                f"{friend.label} stayed beside Maro and used {world.facts['method_tool']} to help repair the {world.facts['heirloom_name']}. "
                f"That practical help mattered because the old mythology already held room for a friend, so Pip's kindness fit the story instead of breaking it."
            ),
        ),
        QAItem(
            question="What proved that the old mythology was alive in this story?",
            answer=(
                f"The proof came when the ritual finally worked. {world.facts['awakening']} "
                f"That ending image showed the promise answering in the real world, not only in words."
            ),
        ),
        QAItem(
            question="What changed in Maro by the end?",
            answer=(
                f"Maro ended the story steadier and less lonely than he began it. "
                f"He learned that hereditary work can stay meaningful even when a friend helps carry it with care."
            ),
        ),
    ]


def world_qa_for(world: MarshWorld) -> list[QAItem]:
    return [
        QAItem(
            question="Why do the animals in this marsh keep hereditary objects in one family line?",
            answer=(
                "They keep those objects in one family line because each generation learns the care, memory, and promise attached to them. "
                "The inheritance is not about showing off ownership; it is about protecting a ritual well enough to pass it on kindly."
            ),
        ),
        QAItem(
            question="What does mythology do in this world besides decorate the story?",
            answer=(
                "Mythology gives the animals a way to remember where to go, what to notice, and what kind of behavior fits the ritual. "
                "It shapes their choices, but the story still expects them to solve real physical problems in the marsh."
            ),
        ),
        QAItem(
            question="How does friendship improve ceremonial work in this world?",
            answer=(
                "Friendship improves ceremonial work by adding help, steadiness, and another pair of careful paws at the moment of trouble. "
                "In this world, a friend does not steal the meaning of the rite; a friend helps the keeper fulfill it honestly."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    grove = GROVES[params.grove]
    myth = MYTHS[params.myth]
    heirloom = HEIRLOOMS[params.heirloom]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]

    world = build_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    heir = world.get("heirloom")
    site = world.get("site")
    pair = world.get("pair")

    world.record(
        "opening",
        grove.opening,
        actor=hero.id,
        place=grove.id,
    )
    world.record(
        "inheritance",
        (
            f"{hero.label} had {hero.attrs['mark']}, the same bright mark his mother and grandmother had worn. "
            f"{heirloom.inheritance}"
        ),
        actor=hero.id,
        target=heir.id,
        place=grove.id,
    )
    world.record(
        "mythology",
        myth.claim,
        actor=hero.id,
        target=site.id,
        place=myth.site,
    )
    world.para()

    world.record(
        "attempt",
        f"At {site_name(myth.site)}, Pip the squirrel padded beside him while {heirloom.attempt}",
        actor=hero.id,
        target=friend.id,
        place=myth.site,
    )
    world.record(
        "block",
        f"{problem.block} {problem.discovery}",
        actor=hero.id,
        target=heir.id,
        place=myth.site,
    )
    hero.meters["steadiness"] = 0.0
    hero.meters["burden"] = 3.0
    hero.memes["worry"] = 2.0
    heir.meters["stuckness"] = 2.0
    world.record(
        "fear",
        f"{problem.risk} {myth.lonely_fear}",
        actor=hero.id,
        place=myth.site,
    )
    world.para()

    world.record(
        "friendship_turn",
        (
            f"{friend.label} did not step back. {myth.friend_line}"
        ),
        actor=friend.id,
        target=hero.id,
        place=myth.site,
    )
    world.record(
        "repair",
        method.action,
        actor=friend.id,
        target=heir.id,
        place=myth.site,
    )
    world.record(
        "repair_proof",
        method.proof,
        actor=hero.id,
        target=heir.id,
        place=myth.site,
    )
    hero.meters["steadiness"] = 3.0
    hero.meters["burden"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 3.0
    hero.memes["friendship"] = 3.0
    friend.memes["friendship"] = 3.0
    pair.memes["friendship"] = 4.0
    heir.meters["stuckness"] = 0.0
    heir.meters["ready"] = 1.0
    world.facts["solved"] = True
    world.para()

    world.record(
        "result",
        problem.result,
        actor=hero.id,
        target=heir.id,
        place=myth.site,
    )
    world.record(
        "awakening",
        myth.awakening,
        actor=hero.id,
        target=site.id,
        place=myth.site,
    )
    site.meters["awakened"] = 1.0
    site.meters["wonder"] = 3.0
    world.record(
        "lesson",
        (
            "Maro understood then that a hereditary promise was not a lonely test. "
            "It was a family gift that friendship could help carry without taking any of its meaning away."
        ),
        actor=hero.id,
        target=friend.id,
        place=myth.site,
    )
    hero.memes["belonging"] = 3.0
    hero.memes["courage"] = 3.0
    world.record(
        "ending",
        grove.ending,
        actor=pair.id,
        place=grove.id,
    )

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(params),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


ASP_RULES = r"""
valid(G,M,H,P,T) :-
    grove(G), myth(M), heirloom(H), problem(P), method(T),
    myth_site(M, S), grove_site(G, S),
    heirloom_site(H, S),
    heirloom_kind(H, K), problem_kind(P, K), method_solves(T, K).

ok :- chosen(G, M, H, P, T), valid(G, M, H, P, T).

#show valid/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    lines: list[str] = []
    for grove_id, grove in GROVES.items():
        lines.append(fact("grove", grove_id))
        for site in grove.sites:
            lines.append(fact("grove_site", grove_id, site))
    for myth_id, myth in MYTHS.items():
        lines.append(fact("myth", myth_id))
        lines.append(fact("myth_site", myth_id, myth.site))
    for heirloom_id, heirloom in HEIRLOOMS.items():
        lines.append(fact("heirloom", heirloom_id))
        lines.append(fact("heirloom_site", heirloom_id, heirloom.site))
        lines.append(fact("heirloom_kind", heirloom_id, heirloom.kind))
    for problem_id, problem in PROBLEMS.items():
        lines.append(fact("problem", problem_id))
        lines.append(fact("problem_kind", problem_id, problem.kind))
    for method_id, method in METHODS.items():
        lines.append(fact("method", method_id))
        lines.append(fact("method_solves", method_id, method.solves))
    if params is not None:
        lines.append(fact("chosen", params.grove, params.myth, params.heirloom, params.problem, params.method))
    return "\n".join(lines) + "\n"


def asp_program(show: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    required_bits = [
        "hereditary",
        "mythology",
        "friendship",
        "maro",
        "pip",
    ]
    for bit in required_bits:
        if bit not in story_lower:
            raise AssertionError(f"story is missing '{bit}'")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if world.get("heirloom").meters.get("ready", 0) < 1:
        raise AssertionError("heirloom never became ready")
    if world.get("heirloom").meters.get("stuckness", 1) != 0:
        raise AssertionError("heirloom stayed stuck")
    if world.get("site").meters.get("awakened", 0) < 1:
        raise AssertionError("ritual site never awakened")
    if world.get("pair").memes.get("friendship", 0) < 4:
        raise AssertionError("friendship never strengthened enough")
    if world.get("hero").memes.get("courage", 0) < 3:
        raise AssertionError("hero never regained courage")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 14:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted((params.grove, params.myth, params.heirloom, params.problem, params.method) for params in all_params())
    lp = sorted(asp_valid_combos())
    if py != lp:
        print("MISMATCH between Python and ASP gates:")
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        if only_py:
            print("  only in Python:", only_py)
        if only_lp:
            print("  only in ASP:", only_lp)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid hereditary-marsh stories).")
    for params in all_params():
        chosen = StoryParams(**vars(params))
        verify_sample(generate(chosen))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an animal story about hereditary ritual, marsh mythology, and friendship."
    )
    parser.add_argument("--grove", choices=sorted(GROVES))
    parser.add_argument("--myth", choices=sorted(MYTHS))
    parser.add_argument("--heirloom", choices=sorted(HEIRLOOMS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = all(getattr(args, field) is not None for field in ("grove", "myth", "heirloom", "problem", "method"))
    if explicit:
        params = StoryParams(args.grove, args.myth, args.heirloom, args.problem, args.method, args.seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    combos = matching_params(args)
    if not combos:
        grove = args.grove or next(iter(GROVES))
        myth = args.myth or next(iter(MYTHS))
        heirloom = args.heirloom or next(iter(HEIRLOOMS))
        problem = args.problem or next(iter(PROBLEMS))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(grove, myth, heirloom, problem, method))
    chosen = StoryParams(**vars(rng.choice(combos)))
    chosen.seed = args.seed
    return chosen


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_params(args)
        if not combos:
            grove = args.grove or next(iter(GROVES))
            myth = args.myth or next(iter(MYTHS))
            heirloom = args.heirloom or next(iter(HEIRLOOMS))
            problem = args.problem or next(iter(PROBLEMS))
            method = args.method or next(iter(METHODS))
            raise StoryError(explain_rejection(grove, myth, heirloom, problem, method))
        samples: list[StorySample] = []
        for index, params in enumerate(combos):
            chosen = StoryParams(**vars(params))
            chosen.seed = args.seed + index if args.seed is not None else None
            samples.append(generate(chosen))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = base_seed + index
        rng = random.Random(seed)
        chosen = resolve_params(args, rng)
        chosen.seed = seed
        samples.append(generate(chosen))
    return samples


def dump_trace(world: MarshWorld) -> str:
    lines = ["TRACE", f"grove: {world.facts['grove_name']}", f"site: {world.facts['site_name']}"]
    for event in world.history:
        where = f" @ {event.place}" if event.place else ""
        lines.append(f"- {event.id}{where}: {event.text}")
    lines.append("ENTITIES")
    seen: set[str] = set()
    for entity in world.entities.values():
        if entity.id in seen:
            continue
        seen.add(entity.id)
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
        if meters:
            lines.append(f"    meters={meters}")
        if memes:
            lines.append(f"    memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines: list[str] = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid hereditary-marsh stories:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:18}" for part in combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== hereditary_mythology_friendship_animal_story #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
