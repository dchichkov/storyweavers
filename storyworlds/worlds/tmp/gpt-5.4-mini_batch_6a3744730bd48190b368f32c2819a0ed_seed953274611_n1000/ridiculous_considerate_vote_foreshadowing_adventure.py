#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ridiculous_considerate_vote_foreshadowing_adventure.py
======================================================================================

A small adventure storyworld about a trail expedition, a ridiculous shortcut,
a considerate warning, and a vote that chooses the safer path.

The world keeps one eye on foreshadowing: a clue in the terrain can hint at
trouble before it happens, giving the careful character a reason to speak up.
The ending can be a happy route around danger, or a brief misadventure that
gets resolved with teamwork and a sensible choice.

The required seed words are woven into the domain:
- ridiculous
- considerate
- vote

This file is standalone and uses only stdlib plus the shared result/asp helpers.
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
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"caution": 0.0, "joy": 0.0, "fear": 0.0, "pride": 0.0}

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
        return self.label or self.id


@dataclass
class Place:
    id: str
    name: str
    scenic: str
    clue: str
    path: str
    hazard: str
    safe_route: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    treasure: str
    gear: str
    clue_noun: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    label: str
    trigger: str
    warning: str
    spread: int
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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    quest: str
    danger: str
    response: str
    leader: str
    leader_gender: str
    friend: str
    friend_gender: str
    adult: str
    seed: Optional[int] = None
    head_start: int = 0
    relation: str = "friends"


PLACES = {
    "bridge": Place(
        id="bridge",
        name="the old rope bridge",
        scenic="a windy gorge",
        clue="the ropes swayed like they remembered a storm",
        path="cross the bridge",
        hazard="the bridge would groan and wobble",
        safe_route="walk around by the stone path",
        tags={"bridge", "wind"},
    ),
    "caves": Place(
        id="caves",
        name="the echoing caves",
        scenic="a tunnel of shiny stones",
        clue="water dripped from the ceiling in nervous little taps",
        path="enter the caves",
        hazard="the floor could turn slippery in a blink",
        safe_route="follow the lantern path beside the stream",
        tags={"caves", "water"},
    ),
    "harbor": Place(
        id="harbor",
        name="the harbor cliffs",
        scenic="a bright cliffside above the sea",
        clue="the gulls kept circling the same crack in the rock",
        path="climb the cliffs",
        hazard="the rocks could crumble under hurried feet",
        safe_route="use the wide stairs by the lighthouse",
        tags={"cliffs", "rock"},
    ),
}

QUESTS = {
    "map": Quest(
        id="map",
        title="the lost map",
        goal="find the lost map",
        treasure="the blue map",
        gear="a compass and a lantern",
        clue_noun="map",
        tags={"map"},
    ),
    "shell": Quest(
        id="shell",
        title="the pearl shell",
        goal="bring back the pearl shell",
        treasure="the pearl shell",
        gear="a basket and a rope",
        clue_noun="shell",
        tags={"shell"},
    ),
    "flag": Quest(
        id="flag",
        title="the hill flag",
        goal="reach the hill flag",
        treasure="the red flag",
        gear="a walking stick and a snack pack",
        clue_noun="flag",
        tags={"flag"},
    ),
}

DANGERS = {
    "storm": Danger(
        id="storm",
        label="storm wind",
        trigger="the clouds were stacking up fast",
        warning="the gusts were already tugging at hats and hems",
        spread=2,
        tags={"wind"},
    ),
    "slip": Danger(
        id="slip",
        label="slippery stones",
        trigger="the stones were shiny with water",
        warning="the ground looked slick enough to skate on",
        spread=2,
        tags={"water"},
    ),
    "crumbles": Danger(
        id="crumbles",
        label="crumbly rock",
        trigger="a crack zigzagged across the path",
        warning="small pebbles were already rolling downhill",
        spread=3,
        tags={"rock"},
    ),
}

RESPONSES = {
    "pause_vote": Response(
        id="pause_vote",
        sense=3,
        power=4,
        text="paused at the safe spot and led a quick vote. Then {adult} chose the careful route and guided everyone around {hazard}",
        fail="tried to stop the trouble, but the danger had already grown past the group",
        qa_text="paused, called a vote, and took the careful route around {hazard}",
        tags={"vote", "careful"},
    ),
    "backtrack": Response(
        id="backtrack",
        sense=3,
        power=3,
        text="turned back at once and took the long way around before {hazard} could catch them",
        fail="turned back, but the danger had already reached the team",
        qa_text="turned back and took the long way around before {hazard} could catch them",
        tags={"careful"},
    ),
    "gear_help": Response(
        id="gear_help",
        sense=2,
        power=3,
        text="used their gear to steady themselves and crossed by the safer path beside {hazard}",
        fail="used their gear, but it was not enough to beat {hazard}",
        qa_text="used their gear and crossed by the safer path beside {hazard}",
        tags={"gear"},
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Ivy", "Zoe", "Ava", "Nora", "Tess", "Ruby"]
BOY_NAMES = ["Finn", "Theo", "Max", "Eli", "Noah", "Jasper", "Leo", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for q in QUESTS.values():
            for d in DANGERS.values():
                if d.tags & p.tags:
                    combos.append((p.id, q.id, d.id))
    return combos


def hazard_at_risk(place: Place, danger: Danger) -> bool:
    return bool(place.tags & danger.tags)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def is_contained(response: Response, danger: Danger, head_start: int) -> bool:
    return response.power >= danger.spread + head_start


def reasonableness_gate(place: Place, danger: Danger, response: Response) -> bool:
    return hazard_at_risk(place, danger) and response.sense >= 2


def story_outcome(params: StoryParams) -> str:
    if params.head_start > 1:
        return "rough"
    return "safe"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with foreshadowing, a vote, and a careful route.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--danger", choices=sorted(DANGERS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--adult", choices=["captain", "guide", "ranger"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too silly for a careful adventure.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.danger is None or c[2] == args.danger)]
    if not combos:
        raise StoryError("No reasonable adventure matches those choices.")
    place_id, quest_id, danger_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(s.id for s in sensible_responses()))
    adult = args.adult or rng.choice(["captain", "guide", "ranger"])
    gender = rng.choice(["girl", "boy"])
    leader = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = "boy" if gender == "girl" else "girl"
    friend = rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    if friend == leader:
        friend = (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)[0]
    return StoryParams(
        place=place_id,
        quest=quest_id,
        danger=danger_id,
        response=response_id,
        leader=leader,
        leader_gender=gender,
        friend=friend,
        friend_gender=friend_gender,
        adult=adult,
        head_start=rng.randint(0, 2),
    )


def predict(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    sim.get("leader").meters["risk"] += 1
    if params.head_start > 0:
        sim.get("hazard").meters["risk"] += params.head_start
    return {"risky": sim.get("hazard").meters["risk"] >= THRESHOLD}


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.quest not in QUESTS or params.danger not in DANGERS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    danger = DANGERS[params.danger]
    response = RESPONSES[params.response]
    if not reasonableness_gate(place, danger, response):
        raise StoryError("That combination does not make a believable adventure.")
    world = World()
    leader = world.add(Entity(id=params.leader, kind="character", type=params.leader_gender, role="leader"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    adult = world.add(Entity(id=params.adult, kind="character", type="adult", label=f"the {params.adult}"))
    trail = world.add(Entity(id="trail", type="place", label=place.name))
    hazard = world.add(Entity(id="hazard", type="danger", label=danger.label))
    world.facts.update(place=place, quest=quest, danger=danger, response=response, leader=leader, friend=friend, adult=adult, trail=trail, hazard=hazard, params=params)

    leader.memes["caution"] = 1.0
    friend.memes["joy"] = 1.0
    world.say(f"{leader.id} and {friend.id} set out on an adventure to {quest.goal} at {place.name}.")
    world.say(f"The path looked grand, but {place.clue}; that was the first foreshadowing clue.")
    world.say(f"They had their {quest.gear}, and {quest.treasure} was the prize waiting at the end.")

    world.para()
    world.say(f"Halfway there, they saw that {danger.trigger}, and {danger.warning}.")
    leader.memes["caution"] += 1
    friend.memes["fear"] += 1
    world.say(f"{leader.id} thought a ridiculous shortcut would be faster, but {friend.id} was considerate and slowed down.")
    world.say(f'"We should vote," {friend.id} said. "The risky way sounds ridiculous."')
    world.say(f"Everyone paused for a quick vote about whether to {place.path} or choose the safer path.")

    world.para()
    outcome = "safe"
    if params.head_start >= 2:
        world.get("hazard").meters["risk"] += 2
        world.say(f"{leader.id} tried to hurry anyway, and the danger nearly caught them.")
        world.say(f"{adult.label_word.capitalize()} arrived just in time, and {response.text.format(hazard=danger.label, adult=adult.label_word)}.")
        world.say(f"The team backed away from {danger.label} and kept the story moving.")
        outcome = "rough"
    elif is_contained(response, danger, params.head_start):
        world.say(f"The vote went the careful way. {adult.label_word.capitalize()} {response.text.format(hazard=danger.label, adult=adult.label_word)}.")
        world.say(f"They reached {quest.treasure} safely, and the warning clue made perfect sense in hindsight.")
    else:
        world.say(f"The vote helped, but the danger was too quick. {response.fail}.")
        world.say("They still escaped, but only after a tense scramble back to the trailhead.")
        outcome = "rough"

    world.para()
    if outcome == "safe":
        world.say(f"In the end, {leader.id} held up {quest.treasure} while {friend.id} grinned beside {leader.pronoun('object')}.")
        world.say(f"Their adventure proved that a considerate vote can choose the brave path and still keep everyone safe.")
    else:
        world.say(f"By sunset, they were safe again, dusty but together, and they promised to choose the wiser path next time.")
    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    quest: Quest = f["quest"]
    danger: Danger = f["danger"]
    return [
        f'Write an adventure story that includes the words "ridiculous", "considerate", and "vote" while {quest.goal} near {place.name}.',
        f"Tell a foreshadowing adventure where a careful friend notices a clue at {place.name}, warns that the shortcut sounds ridiculous, and the group takes a vote.",
        f"Write a child-friendly adventure about {quest.treasure} where a considerate choice beats {danger.label} after a vote.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    quest: Quest = f["quest"]
    danger: Danger = f["danger"]
    params: StoryParams = f["params"]
    outcome = f["outcome"]
    answer1 = (
        f"They were trying to {quest.goal} at {place.name}. The clue in the scenery hinted that trouble was nearby, so the story could warn them before the risky part."
    )
    answer2 = (
        f"{params.friend} was considerate. {params.friend} noticed the foreshadowing clue, called for a vote, and helped the group choose the safer route instead of the ridiculous shortcut."
    )
    answer3 = (
        f"The story ended safely if the vote kept them away from {danger.label}. "
        f"That choice proved the adventure could stay exciting without letting the danger win."
    )
    return [
        QAItem(question="What were they trying to do?", answer=answer1),
        QAItem(question="Who was considerate, and why did that matter?", answer=answer2),
        QAItem(question="How did the story end?", answer=answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    danger: Danger = f["danger"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            question="What is a vote?",
            answer="A vote is when a group chooses by listening to each idea and picking the option most people think is best. It helps friends decide together instead of arguing forever.",
        ),
        QAItem(
            question="What does considerate mean?",
            answer="Considerate means thinking about other people and trying to keep them safe or comfortable. A considerate person notices feelings and chooses kindly.",
        ),
        QAItem(
            question=f"Why is {danger.label} dangerous?",
            answer=f"{danger.label.capitalize()} is dangerous because it can make the path unsafe very quickly. If a traveler ignores the warning, the problem can spread before anyone expects it.",
        ),
        QAItem(
            question=f"Why was the clue important to {quest.goal}?",
            answer="The clue was important because it foreshadowed the problem ahead. It gave the characters a reason to slow down and make a smarter choice before the danger arrived.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bridge", quest="map", danger="storm", response="pause_vote", leader="Mia", leader_gender="girl", friend="Finn", friend_gender="boy", adult="guide", head_start=0),
    StoryParams(place="caves", quest="shell", danger="slip", response="backtrack", leader="Theo", leader_gender="boy", friend="Ava", friend_gender="girl", adult="ranger", head_start=1),
    StoryParams(place="harbor", quest="flag", danger="crumbles", response="gear_help", leader="Lena", leader_gender="girl", friend="Owen", friend_gender="boy", adult="captain", head_start=0),
]


ASP_RULES = r"""
hazard(P,D) :- place(P), danger(D), share_tag(P,D).
sensible(R) :- response(R), sense(R,S), min_sense(M), S >= M.
valid(P,Q,D) :- place(P), quest(Q), danger(D), hazard(P,D).
outcome(safe) :- response_ok.
outcome(rough) :- not response_ok.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for t in sorted(p.tags):
            lines.append(asp.fact("share_tag", p.id, t))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
    for d in DANGERS.values():
        lines.append(asp.fact("danger", d.id))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, danger=None, response=None, adult=None), random.Random(1)))
    if not sample.story:
        print("MISMATCH: generate produced empty story.")
        rc = 1
    else:
        print("OK: generate/emit smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.quest not in QUESTS or params.danger not in DANGERS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        try:
            # smoke test with default-ish curated params
            sample = generate(CURATED[0])
            if not sample.story:
                raise StoryError("Smoke test failed.")
        except Exception as e:
            print(f"Smoke test error: {e}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible place/quest/danger combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
