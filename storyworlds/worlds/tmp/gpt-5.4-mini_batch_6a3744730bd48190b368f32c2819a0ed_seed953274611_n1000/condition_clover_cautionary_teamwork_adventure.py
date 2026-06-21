#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/condition_clover_cautionary_teamwork_adventure.py
==================================================================================

A small standalone story world for a cautionary teamwork adventure built from the
seed words "condition" and "clover".

Premise
-------
A child crew explores a windy meadow to find a lucky clover for a sick or
strained companion, but they must work together, obey a simple caution, and
choose the safe path to finish the adventure well.

This world models:
- a shared outdoor task with a physical goal
- a condition that can improve or worsen
- teamwork as a causal force that can help the group succeed
- a cautionary turn where risky behavior threatens the goal
- a complete ending image proving what changed

It follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- a reasonableness gate
- inline ASP rules and facts
- prompts, story-grounded QA, and world-knowledge QA
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
CLAMOR_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    description: str
    windy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Condition:
    id: str
    label: str
    phrase: str
    danger_phrase: str
    helps_when: str
    worsens_when: str
    makes_risk: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clover:
    id: str
    label: str
    phrase: str
    lucky_phrase: str
    grows_in: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_breeze(world: World) -> list[str]:
    out: list[str] = []
    meadow = world.entities.get("meadow")
    for e in world.entities.values():
        if e.meters["wind"] < THRESHOLD:
            continue
        sig = ("breeze", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if meadow:
            meadow.meters["risk"] += 1
        out.append("__wind__")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.entities.values() if e.role in {"leader", "helper"}]
    if any(e.meters["risk"] >= THRESHOLD for e in crew):
        for e in crew:
            e.memes["worry"] += 1
    if world.get("clover").meters["handled"] >= THRESHOLD:
        for e in crew:
            e.memes["hope"] += 1
    return out


CAUSAL_RULES = [Rule("breeze", "weather", _r_breeze), Rule("risk", "social", _r_risk)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(cond: Condition, clover: Clover) -> bool:
    return cond.makes_risk and clover.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def would_avert(teamwork: bool, caution: bool) -> bool:
    return teamwork and caution


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def _do_risky(world: World, clover: Entity) -> None:
    clover.meters["shaken"] += 1
    clover.meters["handled"] += 1
    propagate(world, narrate=False)


def predict_outcome(world: World, clover_id: str, delay: int) -> dict:
    sim = world.copy()
    _do_risky(sim, sim.get(clover_id))
    return {
        "shaken": sim.get(clover_id).meters["shaken"] >= THRESHOLD,
        "risk": sim.get("meadow").meters["risk"],
        "contained": delay <= 1,
    }


def setup(world: World, leader: Entity, helper: Entity, place: Place) -> None:
    leader.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a bright morning, {leader.id} and {helper.id} set off into {place.label}. "
        f"{place.description}"
    )
    world.say(
        f"They were searching for something small and lucky, because their friend's "
        f"condition had made the day feel heavy."
    )


def need(world: World, leader: Entity, helper: Entity, c: Condition, clover: Clover) -> None:
    world.say(
        f"The wind kept tugging at the grass, and the children knew the clover could "
        f"help if they found it before it was trampled."
    )
    world.say(
        f'"We need the {clover.label}," said {helper.id}. '
        f'"The {c.label} is bad, and a little lucky thing might cheer everyone up."'
    )


def caution(world: World, helper: Entity, leader: Entity, c: Condition, clover: Clover) -> None:
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} bit {helper.pronoun("possessive")} lip. '
        f'"Careful now," {helper.pronoun()} said. "{c.danger_phrase}. '
        f'If we rush, we could lose the clover and still not help our friend."'
    )


def teamwork_move(world: World, leader: Entity, helper: Entity, clover: Clover) -> None:
    leader.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'{leader.id} nodded. "You watch the path," {leader.id} said. '
        f'"I will look low in the grass."'
    )
    world.say(
        f"Side by side, they searched in a slow, careful circle until {helper.id} "
        f"spotted a tiny green stem."
    )


def rush(world: World, leader: Entity, clover: Clover) -> None:
    leader.memes["impulse"] += 1
    world.say(
        f'{leader.id} almost rushed ahead, because the clover looked easy to grab. '
        f'But the wind made the stalk wobble.'
    )


def risky_touch(world: World, clover_ent: Entity, clover: Clover) -> None:
    _do_risky(world, clover_ent)
    world.say(
        f"{leader_name(world)} reached too fast, and the clover shook loose in the breeze. "
        f"{clover.lucky_phrase}, but only if they could keep it safe."
    )


def leader_name(world: World) -> str:
    return world.facts["leader"].id


def rescue(world: World, parent: Entity, response: Response, clover_ent: Entity, clover: Clover) -> None:
    clover_ent.meters["shaken"] = 0
    clover_ent.meters["handled"] = 1
    world.get("meadow").meters["risk"] = 0
    body = response.text.replace("{clover}", clover.label)
    world.say(f"{parent.label_word.capitalize()} came over and {body}.")
    world.say(
        f"The little stem stopped trembling, and the bright patch of grass looked calm again."
    )


def finish(world: World, parent: Entity, leader: Entity, helper: Entity, clover: Clover, place: Place) -> None:
    leader.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} smiled at their teamwork. "
        f'"Good job being careful," {parent.pronoun()} said. "You found the clover and protected it too."'
    )
    world.say(
        f"The children carried the tiny clover back across {place.label}, and its green leaves "
        f"sat safe in {leader.id}'s palm like a little promise."
    )


def calm_end(world: World, parent: Entity, leader: Entity, helper: Entity, clover: Clover, place: Place) -> None:
    leader.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, the team walked home together, one child carrying the clover and the other "
        f"carrying the path in mind."
    )
    world.say(
        f"Their friend's condition would still need care, but now they had a lucky clover, a safer plan, "
        f"and a brave memory from the meadow."
    )


def tell(place: Place, condition: Condition, clover: Clover, response: Response,
         leader_name_: str = "Maya", leader_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0,
         caution_first: bool = True, teamwork: bool = True) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name_, kind="character", type=leader_gender, role="leader"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    meadow = world.add(Entity(id="meadow", type="place", label=place.label))
    c_ent = world.add(Entity(id="condition", type="condition", label=condition.label))
    cl_ent = world.add(Entity(id="clover", type="clover", label=clover.label))
    leader.memes["hope"] = 1
    helper.memes["care"] = 1
    world.facts["leader"] = leader
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["condition"] = condition
    world.facts["clover_cfg"] = clover
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["teamwork"] = teamwork
    world.facts["caution_first"] = caution_first

    setup(world, leader, helper, place)
    world.para()
    need(world, leader, helper, condition, clover)
    caution(world, helper, leader, condition, clover)
    if teamwork:
        teamwork_move(world, leader, helper, clover)
    if not caution_first:
        rush(world, leader, clover)
    if would_avert(teamwork, caution_first):
        world.say(f"They stopped and chose the careful way before anything went wrong.")
        rescue(world, parent, response, cl_ent, clover)
        finish(world, parent, leader, helper, clover, place)
        calm_end(world, parent, leader, helper, clover, place)
        outcome = "averted"
        contained = True
    else:
        world.para()
        rush(world, leader, clover)
        risky_touch(world, cl_ent, clover)
        if is_contained(response, delay):
            rescue(world, parent, response, cl_ent, clover)
            finish(world, parent, leader, helper, clover, place)
            calm_end(world, parent, leader, helper, clover, place)
            outcome = "contained"
            contained = True
        else:
            world.say(
                f"The wind got stronger, and the clover nearly blew away before help could reach it."
            )
            world.say(
                f"{parent.label_word.capitalize()} had to hurry over and guide them back together."
            )
            world.say(
                f"In the end, they kept the clover, but only because the team learned to move slowly and listen."
            )
            outcome = "burned"
            contained = False
    world.facts["outcome"] = outcome
    world.facts["contained"] = contained
    return world


PLACES = {
    "meadow": Place(id="meadow", label="the meadow", description="Tall grass waved like a green sea.", windy=True, tags={"meadow", "wind"}),
    "hill": Place(id="hill", label="the hilltop meadow", description="The hilltop was open to the sky and extra windy.", windy=True, tags={"meadow", "wind"}),
    "field": Place(id="field", label="the field", description="Daisies leaned in one direction under the steady breeze.", windy=True, tags={"meadow", "wind"}),
}

CONDITIONS = {
    "fever": Condition(id="fever", label="fever", phrase="a hot fever", danger_phrase="a fever can make someone weak and tired", helps_when="rest", worsens_when="run", makes_risk=True, tags={"condition", "fever"}),
    "sprain": Condition(id="sprain", label="sprain", phrase="a sore sprain", danger_phrase="a sprain can hurt more if we bounce around", helps_when="rest", worsens_when="rush", makes_risk=True, tags={"condition", "sprain"}),
    "sneeze": Condition(id="sneeze", label="cold", phrase="a bad cold", danger_phrase="a cold can make a friend feel chilly and worn out", helps_when="warm", worsens_when="stay_cold", makes_risk=False, tags={"condition", "cold"}),
}

CLOVERS = {
    "clover": Clover(id="clover", label="clover", phrase="a tiny clover", lucky_phrase="the clover looked like luck itself", grows_in="meadow", fragile=True, tags={"clover"}),
    "four_leaf": Clover(id="four_leaf", label="four-leaf clover", phrase="a tiny four-leaf clover", lucky_phrase="the four leaves shone like a green star", grows_in="meadow", fragile=True, tags={"clover"}),
    "white_clover": Clover(id="white_clover", label="white clover", phrase="a white clover bloom", lucky_phrase="the white bloom nodded like it knew their secret", grows_in="field", fragile=True, tags={"clover"}),
}

RESPONSES = {
    "kneel": Response(id="kneel", sense=3, power=2, text="knelt down and lifted the {clover} gently between two fingers", fail="knelt too late and the {clover} had already blown sideways", qa_text="knelt down and lifted the {clover} gently between two fingers", tags={"gentle"}),
    "shield": Response(id="shield", sense=3, power=2, text="held a hand over the wind and scooped the {clover} into a safe little cup of fingers", fail="tried to shield the {clover}, but the wind pushed harder", qa_text="held a hand over the wind and scooped the {clover} into a safe little cup of fingers", tags={"teamwork"}),
    "basket": Response(id="basket", sense=2, power=1, text="used a basket to carry the {clover} so it would not be crushed", fail="used the basket, but the wind was too fast to trust it alone", qa_text="used a basket to carry the {clover} so it would not be crushed", tags={"tool"}),
    "water_bucket": Response(id="water_bucket", sense=1, power=0, text="threw water on the {clover}", fail="threw water on the {clover}, which only made a mess", qa_text="threw water on the {clover}", tags={"bad"}),
}

GIRL_NAMES = ["Maya", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Sam"]


@dataclass
class StoryParams:
    place: str
    condition: str
    clover: str
    response: str
    leader_name: str
    leader_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    delay: int = 0
    caution_first: bool = True
    teamwork: bool = True
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, cond in CONDITIONS.items():
            for clid, cl in CLOVERS.items():
                if hazard_at_risk(cond, cl):
                    combos.append((pid, cid, clid))
    return combos


def explain_rejection(cond: Condition, cl: Clover) -> str:
    if not hazard_at_risk(cond, cl):
        return f"(No story: {cond.label} does not create a useful risk with {cl.label}, so there is no cautionary turn.)"
    return "(No story: invalid combination.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} < {SENSE_MIN}. Try: {better}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the words "{f["condition"].label}" and "{f["clover_cfg"].label}".',
        f"Tell a cautionary teamwork adventure where {f['leader'].id} and {f['helper'].id} search for a clover while worrying about a {f['condition'].label}.",
        f'Write a story where teamwork helps two children find a "{f["clover_cfg"].label}" safely in a windy place.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader, helper, parent = f["leader"], f["helper"], f["parent"]
    cond, cl = f["condition"], f["clover_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {leader.id}, {helper.id}, and {parent.label_word}. They work together on a windy adventure and look for {cl.phrase}."),
        ("Why were they careful?", f"They were careful because {cond.danger_phrase}. That warning made the clover search feel like a real adventure instead of a quick grab."),
        ("What were they looking for?", f"They were looking for {cl.phrase}. It could cheer up their friend and it also gave them a reason to move slowly and work as a team."),
    ]
    if f.get("outcome") == "averted":
        qa.append((f"What happened when they listened to the warning?",
                   f"They slowed down, shared the job, and kept the clover safe. Teamwork helped them finish the adventure without a scare."))
        qa.append((f"How did the story end?",
                   f"It ended with the clover safe in their hands and everyone calmer than before. The ending proves that careful teamwork can be just as brave as rushing."))
    elif f.get("outcome") == "contained":
        body = f["response"].qa_text.replace("{clover}", cl.label)
        qa.append((f"How did they protect the clover?",
                   f"One child warned, the other helped, and then {body}. The quick, careful response kept the little plant from getting lost in the wind."))
        qa.append((f"How did they feel at the end?",
                   f"They felt proud and relieved. The clover was safe, and their teamwork turned a risky moment into a good memory."))
    else:
        qa.append((f"What went wrong?",
                   f"They moved too fast, and the wind nearly stole the clover. They still learned that caution matters, because teamwork works best when everyone listens first."))
        qa.append((f"What did they learn?",
                   f"They learned that a brave adventure also needs patience. If they slow down and listen, the clover and their friend can both stay safer."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["condition"].tags) | set(f["clover_cfg"].tags)
    if f.get("outcome") != "averted":
        tags |= set(f["response"].tags)
    out = []
    if "condition" in tags:
        out.append(("What is a condition?", "A condition is a state someone can have, like a fever or a sprain. It can affect how they feel and what they should do next."))
    if "clover" in tags:
        out.append(("What is a clover?", "A clover is a small plant with three round leaves, and some clovers are lucky if they have four leaves."))
    if "gentle" in tags:
        out.append(("Why should you touch a clover gently?", "A clover is small and easy to crush. Gentle fingers help keep the stem and leaves whole."))
    if "teamwork" in tags:
        out.append(("What is teamwork?", "Teamwork means people help each other with different jobs so the whole group can do something better together."))
    if "tool" in tags:
        out.append(("What does a basket do?", "A basket can carry small things carefully so they do not get crushed or dropped."))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", condition="fever", clover="clover", response="kneel", leader_name="Maya", leader_gender="girl", helper_name="Noah", helper_gender="boy", parent="mother", delay=0, caution_first=True, teamwork=True),
    StoryParams(place="hill", condition="sprain", clover="four_leaf", response="shield", leader_name="Lily", leader_gender="girl", helper_name="Eli", helper_gender="boy", parent="father", delay=0, caution_first=True, teamwork=True),
    StoryParams(place="field", condition="fever", clover="white_clover", response="basket", leader_name="Ava", leader_gender="girl", helper_name="Sam", helper_gender="boy", parent="mother", delay=0, caution_first=False, teamwork=True),
]


def outcome_of(params: StoryParams) -> str:
    if params.caution_first and params.teamwork:
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "burned"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CONDITIONS.items():
        lines.append(asp.fact("condition", cid))
        if c.makes_risk:
            lines.append(asp.fact("risking", cid))
    for clid, cl in CLOVERS.items():
        lines.append(asp.fact("clover", clid))
        if cl.fragile:
            lines.append(asp.fact("fragile", clid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(C, L) :- risking(C), fragile(L).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, C, L) :- place(P), condition(C), clover(L), hazard(C, L).
averted :- teamwork, caution_first.
contained :- not averted, sensible(R), power(R, P), delay(D), P >= D + 1.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("teamwork"),
        asp.fact("caution_first") if params.caution_first else "",
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    vals = asp.atoms(model, "outcome")
    return vals[0][0] if vals else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    for p in CURATED[:1]:
        try:
            sample = generate(p)
            _ = sample.story
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL: {err}")
    if rc == 0:
        print("OK: generate() smoke test passed.")
    cases = list(CURATED)
    for s in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            pass
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome parity passed on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome checks failed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary teamwork adventure story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--condition", choices=CONDITIONS)
    ap.add_argument("--clover", choices=CLOVERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--leader-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--caution-first", action="store_true")
    ap.add_argument("--no-caution-first", action="store_true")
    ap.add_argument("--no-teamwork", action="store_true")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and (args.condition is None or c[1] == args.condition)
              and (args.clover is None or c[2] == args.clover)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, condition, clover = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if leader_gender == "girl" else "girl")
    leader_name = args.leader_name or rng.choice(GIRL_NAMES if leader_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != leader_name])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    caution_first = False if args.no_caution_first else True
    teamwork = not args.no_teamwork
    return StoryParams(place=place, condition=condition, clover=clover, response=response,
                       leader_name=leader_name, leader_gender=leader_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       parent=parent, delay=delay, caution_first=caution_first,
                       teamwork=teamwork)


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "condition", "clover", "response"):
        if key not in params.__dict__:
            raise StoryError(f"missing StoryParams field: {key}")
    if params.condition not in CONDITIONS or params.clover not in CLOVERS or params.place not in PLACES or params.response not in RESPONSES:
        raise StoryError("(Invalid StoryParams choice.)")
    world = tell(
        PLACES[params.place], CONDITIONS[params.condition], CLOVERS[params.clover],
        RESPONSES[params.response],
        leader_name_=params.leader_name, leader_gender=params.leader_gender,
        helper_name=params.helper_name, helper_gender=params.helper_gender,
        parent_type=params.parent, delay=params.delay,
        caution_first=params.caution_first, teamwork=params.teamwork,
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t in combos:
            print("  ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
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
