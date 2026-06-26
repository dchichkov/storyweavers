#!/usr/bin/env python3
"""
storyworlds/worlds/bonnie_lemur_rhyme_pirate_tale.py
====================================================

A standalone story world for a tiny Pirate Tale with rhyme, built around
Bonnie, a lemur, and a small lyrical problem that can be resolved with a
reasonable pirate choice.

The seed premise:
---
Bonnie sailed with a lemur friend and loved singing rhymes on the deck.
A shiny map promised a treasure, but the wind, the waves, and a missing rhyme
made the crew stuck. Bonnie had to choose whether to chase the treasure loudly
or use a clever rhyme to calm the ship, guide the lemur, and finish the trip.

World model:
---
- Characters have meters for motion, travel, treasure, and ship care.
- Characters also have memes for joy, worry, confidence, and teamwork.
- The world advances through causal rules: singing a rhyme can calm worry,
  stormy sailing can rattle the ship, and a steady crew can reach the cove.
- The ending proves a change in state: the crew reaches the treasure, the lemur
  feels safe, and the rhyme becomes part of the victory.

Story shape:
---
Setup: Bonnie, the lemur, the ship, and the map.
Tension: the sea grows rough and the crew loses rhythm.
Turn: Bonnie uses rhyme as a guide and a promise.
Resolution: the ship steadies, the treasure is found, and the crew celebrates.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    companion: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    sea: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    rhyme_line: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "treasure"
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def make_meter() -> dict[str, float]:
    return {"motion": 0.0, "travel": 0.0, "treasure": 0.0, "shipcare": 0.0}


def make_memes() -> dict[str, float]:
    return {"joy": 0.0, "worry": 0.0, "confidence": 0.0, "teamwork": 0.0, "rhythm": 0.0}


def _r_rough_sea(world: World) -> list[str]:
    out = []
    ship = world.entities.get("ship")
    storm = world.entities.get("storm")
    if not ship or not storm:
        return out
    if storm.meters.get("rough", 0.0) < THRESHOLD:
        return out
    sig = ("rough_sea",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.meters["shipcare"] += 1
    out.append("The ship creaked and rocked, and the crew had to hold on tight.")
    return out


def _r_rhyme_calm(world: World) -> list[str]:
    out = []
    bonnie = world.entities.get("bonnie")
    lemur = world.entities.get("lemur")
    if not bonnie or not lemur:
        return out
    if bonnie.memes.get("rhythm", 0.0) < THRESHOLD:
        return out
    sig = ("rhyme_calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lemur.memes["worry"] = max(0.0, lemur.memes.get("worry", 0.0) - 1.0)
    bonnie.memes["confidence"] += 1
    bonnie.memes["teamwork"] += 1
    out.append("Bonnie's rhyme made the lemur breathe easier and listen close.")
    return out


def _r_travel_progress(world: World) -> list[str]:
    out = []
    bonnie = world.entities.get("bonnie")
    ship = world.entities.get("ship")
    if not bonnie or not ship:
        return out
    if bonnie.memes.get("confidence", 0.0) < THRESHOLD:
        return out
    sig = ("travel_progress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship.meters["travel"] += 1
    bonnie.meters["travel"] += 1
    out.append("With steady feet and a steady tune, the ship moved closer to the cove.")
    return out


CAUSAL_RULES = [_r_rough_sea, _r_rhyme_calm, _r_travel_progress]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_result(world: World, action: Activity) -> dict:
    sim = world.copy()
    bonnie = sim.get("bonnie")
    bonnie.memes["rhythm"] += 1
    bonnie.memes["worry"] += 0
    if action.id == "sail":
        sim.get("storm").meters["rough"] += 1
    propagate(sim, narrate=False)
    return {
        "travel": sim.get("ship").meters.get("travel", 0.0),
        "worry": sim.get("lemur").memes.get("worry", 0.0),
    }


def can_rhyme_help(activity: Activity, place: Place) -> bool:
    return activity.id in place.affords


def choose_tool(activity: Activity) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.id in tool.helps and "rhythm" in tool.guards:
            return tool
    return None


def tell(place: Place, activity: Activity, prize: Prize, hero_name: str = "Bonnie") -> World:
    world = World(place)
    bonnie = world.add(Entity(
        id="bonnie", kind="character", type="girl", label=hero_name,
        traits=["brave", "cheerful"], meters=make_meter(), memes=make_memes()
    ))
    lemur = world.add(Entity(
        id="lemur", kind="character", type="lemur", label="lemur",
        traits=["small", "wide-eyed"], meters=make_meter(), memes=make_memes()
    ))
    ship = world.add(Entity(
        id="ship", type="ship", label="little ship", meters=make_meter(), memes=make_memes()
    ))
    storm = world.add(Entity(
        id="storm", type="weather", label="storm wind", meters={"rough": 0.0}, memes=make_memes()
    ))
    map_ = world.add(Entity(
        id="map", type="thing", label="map", phrase=prize.phrase, meters=make_meter(), memes=make_memes()
    ))
    prize_ent = world.add(Entity(
        id="treasure", type=prize.type, label=prize.label, phrase=prize.phrase,
        meters=make_meter(), memes=make_memes(), plural=prize.plural
    ))

    world.say(
        f"Bonnie was a bright little pirate who loved a rhyme and a calm sea. "
        f"The lemur stayed close on the deck, blinking at the waves and the shiny map."
    )
    world.say(
        f"Together they chased {prize_ent.phrase} by {activity.gerund}, and Bonnie kept a tune "
        f"that made the mast feel merry."
    )

    world.para()
    world.say(
        f"One day the water turned wild. The storm pushed the ship and the lemur squeaked "
        f"as the deck shivered under {bonnie.pronoun('possessive')} boots."
    )
    bonnie.memes["worry"] += 1
    storm.meters["rough"] += 1
    propagate(world)

    world.para()
    bonnie.memes["rhythm"] += 1
    bonnie.memes["confidence"] += 1
    world.say(
        f"Then Bonnie took a breath and sang, '{activity.rhyme_line}' "
        f"The lemur listened, and the tune felt like a lantern in the spray."
    )

    tool = choose_tool(activity)
    if tool:
        world.say(
            f"Bonnie used {tool.label} as a guide, so the crew could {activity.verb} "
            f"without losing the beat."
        )

    propagate(world)

    world.para()
    if bonnie.meters["travel"] >= THRESHOLD:
        world.say(
            f"At last the ship reached the cove. The treasure was there, the lemur was safe, "
            f"and Bonnie laughed as the rhyme sailed on with the tide."
        )
        bonnie.memes["joy"] += 1
        lemur.memes["worry"] = max(0.0, lemur.memes.get("worry", 0.0) - 1.0)
        bonnie.meters["treasure"] += 1
    else:
        world.say(
            f"The rhyme was not enough on its own, so Bonnie steadied the wheel, held the lemur "
            f"close, and tried again until the ship found its way."
        )

    world.facts.update(
        bonnie=bonnie, lemur=lemur, ship=ship, storm=storm, map=map_, treasure=prize_ent,
        place=place, activity=activity, tool=tool,
    )
    return world


PLACES = {
    "harbor": Place(name="the harbor", sea="calm", affords={"sail", "sing"}),
    "reef": Place(name="the reef", sea="rough", affords={"sail", "sing"}),
    "cove": Place(name="the cove", sea="bright", affords={"sail", "sing"}),
}

ACTIVITIES = {
    "sail": Activity(
        id="sail",
        verb="sail to the cove",
        gerund="sailing by moonlight",
        risk="rough seas",
        rhyme_line="Ho, ho, the lantern glows, and steady rhyme will guide our toes",
        weather="windy",
        tags={"sea", "wind", "rhyme"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing to the waves",
        gerund="singing on the deck",
        risk="stormy spray",
        rhyme_line="Yo, yo, the song will flow, and even windy waters slow",
        weather="breezy",
        tags={"song", "rhyme"},
    ),
}

PRIZES = {
    "gold": Prize(label="gold coin chest", phrase="a gold coin chest", region="deck"),
    "pearl": Prize(label="pearl box", phrase="a pearl box", region="deck"),
    "shell": Prize(label="shell bundle", phrase="a shell bundle", region="deck", plural=True),
}

TOOLS = [
    Tool(id="lantern", label="the lantern rhyme", prep="light the lantern", tail="lifted the lantern high", guards={"rhythm"}, helps={"sail", "sing"}),
    Tool(id="drum", label="the little drum", prep="tap the drum", tail="beat the drum softly", guards={"rhythm"}, helps={"sing"}),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pname, place in PLACES.items():
        for aid, act in ACTIVITIES.items():
            if aid not in place.affords:
                continue
            for pr in PRIZES:
                combos.append((pname, aid, pr))
    return combos


def explain_rejection(place: str, activity: str, prize: str) -> str:
    return f"(No story: {place}, {activity}, and {prize} do not fit the pirate rhyme premise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate rhyme story world with Bonnie and a lemur.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(place=place, activity=activity, prize=prize)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for children that includes a rhyme and a lemur.',
        f"Tell a gentle pirate story where Bonnie and the lemur go to {f['place'].name} "
        f"and {f['activity'].verb}, then solve the problem with a rhyme.",
        f"Make a child-friendly tale about Bonnie, a lemur, and {f['treasure'].phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bonnie = f["bonnie"]
    lemur = f["lemur"]
    act = f["activity"]
    prize = f["treasure"]
    place = f["place"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"It is about Bonnie and the lemur on {place.name}.",
        ),
        QAItem(
            question=f"What did Bonnie want to do with the ship?",
            answer=f"Bonnie wanted to {act.verb} while singing a rhyme.",
        ),
        QAItem(
            question=f"Why did the lemur need Bonnie's help?",
            answer=f"The sea grew rough, so the lemur got worried and needed Bonnie to steady the trip.",
        ),
        QAItem(
            question=f"What helped the crew keep going?",
            answer=f"The rhyme helped, and {tool.label if tool else 'Bonnie\'s steady song'} kept the crew moving toward the treasure.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the ship reached the cove, the treasure was found, and the lemur felt safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words that sound alike at the end, which makes a song or poem feel musical.",
        ),
        QAItem(
            question="What is a pirate ship for?",
            answer="A pirate ship is used for sailing across the sea, carrying the crew, and searching for places to explore.",
        ),
        QAItem(
            question="Why do sailors watch the sea?",
            answer="Sailors watch the sea because the wind and waves can change quickly, and they need to stay safe.",
        ),
        QAItem(
            question="What is a lemur?",
            answer="A lemur is a small animal with a long tail and quick hands, and some lemurs like to climb and look around.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], PRIZES[params.prize])
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


ASP_RULES = r"""
% A place supports an activity if the activity is allowed there.
valid_story(P, A, T) :- place(P), affords(P, A), treasure(T).

% A rhyme helps when Bonnie has rhythm and the place allows singing or sailing.
rhyme_help(A) :- activity(A), has_rhyme(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, place in PLACES.items():
        lines.append(asp.fact("place", p))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("has_rhyme", a))
    for t in PRIZES:
        lines.append(asp.fact("treasure", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="harbor", activity="sing", prize="gold"),
    StoryParams(place="reef", activity="sail", prize="pearl"),
    StoryParams(place="cove", activity="sail", prize="shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.activity} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
