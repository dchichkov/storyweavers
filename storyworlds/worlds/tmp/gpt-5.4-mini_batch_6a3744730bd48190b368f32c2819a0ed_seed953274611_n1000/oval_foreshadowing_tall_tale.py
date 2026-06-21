#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oval_foreshadowing_tall_tale.py
================================================================

A standalone storyworld for a tiny Tall Tale domain with foreshadowing:
a child notices an oval omen, the omen hints at trouble ahead, a grown-up
reads the sign in time, and the family uses a sensible remedy before the
trouble arrives.

The story is built from simulated world state, not from frozen prose. The
oval detail matters twice: it appears early as the foreshadowing clue, then
returns in the ending image as proof that the clue was understood.
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
FORESHADOW_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Sign:
    id: str
    label: str
    phrase: str
    foreshadows: str
    omen_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    severity: int
    triggers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    text: str
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


def _r_flood(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["flood"] < THRESHOLD:
            continue
        sig = ("flood", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "road" in world.entities:
            world.get("road").meters["mud"] += 1
        for kid in world.entities.values():
            if kid.kind == "character":
                kid.memes["alarm"] += 1
        out.append("__flood__")
    return out


CAUSAL_RULES = [Rule("flood", "physical", _r_flood)]


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


def omen_predicts(sign: Sign, trouble: Trouble) -> bool:
    return trouble.id in sign.foreshadows


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.power >= FORESHADOW_MIN]


def valid_pair(sign: Sign, trouble: Trouble, remedy: Remedy) -> bool:
    return omen_predicts(sign, trouble) and remedy.power >= trouble.severity


def flood_severity(delay: int) -> int:
    return 1 + delay


def would_be_ready(sign: Sign, trouble: Trouble, remedy: Remedy, delay: int) -> bool:
    return valid_pair(sign, trouble, remedy) and remedy.power >= flood_severity(delay)


def predict(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    sim.get(trouble_id).meters["flood"] += 1
    propagate(sim, narrate=False)
    return {
        "alarm": sim.get("child").memes["alarm"],
        "mud": sim.get("road").meters["mud"] if "road" in sim.entities else 0,
    }


def tell_setup(world: World, child: Entity, grownup: Entity, place: str, sign: Sign) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Out on the wide prairie, {child.id} and {grownup.id} rode toward "
        f"{place}. The wind was so bold it could comb the grass flat."
    )
    world.say(
        f"Then {child.id} spotted {sign.phrase}. It looked like an oval little "
        f"coin dropped from the sky."
    )


def foreshadow(world: World, child: Entity, sign: Sign, trouble: Trouble) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"That oval sign means something," {child.id} said. {sign.omen_text} '
        f"It was a plain thing to look at, but it had a long memory in it."
    )
    world.say(
        f"{sign.foreshadows.capitalize()} {trouble.phrase} was on the way."
    )


def warn(world: World, grownup: Entity, child: Entity, sign: Sign, trouble: Trouble) -> None:
    child.memes["fear"] += 1
    pred = predict(world, trouble.id)
    world.facts["predicted_alarm"] = pred["alarm"]
    world.say(
        f'{grownup.id} squinted at the sky and nodded. "That oval sign is a '
        f"warning," {grownup.id} said. \"If {trouble.phrase} comes, it will hit "
        f"hard.\""
    )


def trouble_arrives(world: World, trouble: Trouble) -> None:
    world.get("stormcloud").meters["flood"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon enough, {trouble.phrase} rolled in, dark as a barrel and loud as "
        f"a brass band."
    )


def respond(world: World, grownup: Entity, remedy: Remedy, trouble: Trouble) -> None:
    body = remedy.text
    world.say(f"{grownup.id} did not waste a blink. {body}.")
    if remedy.power >= trouble.severity:
        world.get("stormcloud").meters["flood"] = 0
        if "road" in world.entities:
            world.get("road").meters["mud"] = 0
        world.say(
            f"The trouble gave a grumble, turned aside, and the prairie held "
            f"steady under the big sky."
        )
    else:
        world.get("stormcloud").meters["flood"] = trouble.severity
        propagate(world, narrate=False)
        world.say(
            f"But the trouble was bigger than that, and it kept pushing water "
            f"across the road."
        )


def lesson(world: World, grownup: Entity, child: Entity, sign: Sign) -> None:
    child.memes["brave"] += 1
    child.memes["relief"] += 1
    world.say(
        f"Afterward, {grownup.id} put a hand on {child.id}'s shoulder. "
        f'"Sometimes the world drops a clue before the storm," {grownup.id} said. '
        f'"You saw the clue, and that gave us time."'
    )
    world.say(
        f"{child.id} looked back at the oval mark and nodded. It had warned "
        f"them in time, just like an old tale trying to be helpful."
    )


def ending_image(world: World, child: Entity, sign: Sign) -> None:
    world.say(
        f"By sunset, the road was dry again, and the oval sign still lay on the "
        f"fence rail, shining pale in the last light while {child.id} waved at it "
        f"like an old friend."
    )


def tell(sign: Sign, trouble: Trouble, remedy: Remedy, child_name: str = "Nora",
         child_type: str = "girl", grownup_name: str = "Uncle Reed",
         grownup_type: str = "uncle", place: str = "the canyon road",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    grownup = world.add(Entity(id=grownup_name, kind="character", type=grownup_type, role="grownup"))
    world.add(Entity(id="stormcloud", type="weather", label="the stormcloud"))
    world.add(Entity(id="road", type="place", label="the road"))

    tell_setup(world, child, grownup, place, sign)
    world.para()
    foreshadow(world, child, sign, trouble)
    warn(world, grownup, child, sign, trouble)

    world.para()
    trouble_arrives(world, trouble)
    if would_be_ready(sign, trouble, remedy, delay):
        respond(world, grownup, remedy, trouble)
        lesson(world, grownup, child, sign)
    else:
        respond(world, grownup, remedy, trouble)
        world.say(
            f"The lesson was still plain: a clue can arrive before a problem does, "
            f"but only a strong enough answer can keep the day from washing out."
        )

    world.para()
    ending_image(world, child, sign)

    outcome = "steady" if would_be_ready(sign, trouble, remedy, delay) else "washed"
    world.facts.update(
        child=child,
        grownup=grownup,
        sign=sign,
        trouble=trouble,
        remedy=remedy,
        place=place,
        delay=delay,
        outcome=outcome,
        ready=would_be_ready(sign, trouble, remedy, delay),
    )
    return world


@dataclass
class StoryParams:
    sign: str
    trouble: str
    remedy: str
    child_name: str
    child_type: str
    grownup_name: str
    grownup_type: str
    place: str
    delay: int = 0
    seed: Optional[int] = None


SIGNS = {
    "oval_stone": Sign(
        id="oval_stone",
        label="oval stone",
        phrase="an oval stone with a bright white stripe through it",
        foreshadows="the creek will rise before morning",
        omen_text="It had a river-smooth shine, the sort old folks call a weather eye.",
        tags={"oval", "foreshadowing", "stone"},
    ),
    "oval_cloud": Sign(
        id="oval_cloud",
        label="oval cloud",
        phrase="an oval cloud hanging over the ridge",
        foreshadows="rain is coming fast",
        omen_text="It sat in the sky like a giant barn egg nobody dared to throw.",
        tags={"oval", "foreshadowing", "cloud"},
    ),
    "oval_shadow": Sign(
        id="oval_shadow",
        label="oval shadow",
        phrase="an oval shadow on the fence boards",
        foreshadows="the wind will swing the gate loose",
        omen_text="It had the look of a secret trying to become a warning.",
        tags={"oval", "foreshadowing", "shadow"},
    ),
}

TROUBLES = {
    "creek_rise": Trouble(
        id="creek_rise",
        label="creek rise",
        phrase="the creek rising",
        severity=1,
        triggers={"oval_stone"},
        tags={"water", "flood"},
    ),
    "rain_squall": Trouble(
        id="rain_squall",
        label="rain squall",
        phrase="a hard rain squall",
        severity=1,
        triggers={"oval_cloud"},
        tags={"rain", "water"},
    ),
    "gate_wind": Trouble(
        id="gate_wind",
        label="gate wind",
        phrase="a gate-banging wind",
        severity=1,
        triggers={"oval_shadow"},
        tags={"wind"},
    ),
}

REMEDIES = {
    "move_herd": Remedy(
        id="move_herd",
        label="move the herd",
        phrase="lead the cows to higher ground",
        power=2,
        text="he waved his hat and led the cows to higher ground before the creek could reach their hooves",
        tags={"water", "flood"},
    ),
    "tie_gate": Remedy(
        id="tie_gate",
        label="tie the gate",
        phrase="lash the gate with a rope",
        power=2,
        text="she fetched a rope and lashed the gate tight so the wind could not swing it open",
        tags={"wind"},
    ),
    "cover_sacks": Remedy(
        id="cover_sacks",
        label="cover the sacks",
        phrase="cover the seed sacks with tarps",
        power=2,
        text="he pulled tarps over the seed sacks, tying the corners down with a knot as stubborn as a mule",
        tags={"rain", "water"},
    ),
    "bucket_chain": Remedy(
        id="bucket_chain",
        label="bucket chain",
        phrase="set up a bucket chain",
        power=1,
        text="they set up a bucket chain, working hard to keep the water from crossing the yard",
        tags={"water"},
    ),
}

GIRL_NAMES = ["Nora", "Mae", "Ruby", "Ivy", "June", "Alice", "Rose"]
BOY_NAMES = ["Eli", "Otis", "Jasper", "Cal", "Hank", "Wade", "Liam"]
GROWNUP_NAMES = ["Uncle Reed", "Aunt Jo", "Grandpa Bill", "Grandma Pearl"]
PLACES = ["the canyon road", "the creek bend", "the fence line", "the open prairie"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, sign in SIGNS.items():
        for tid, trouble in TROUBLES.items():
            if tid not in sign.foreshadows:
                continue
            for rid, remedy in REMEDIES.items():
                if remedy.tags & trouble.tags:
                    combos.append((sid, tid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with an oval omen and a foreshadowed outcome.")
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-type", choices=["uncle", "aunt", "grandpa", "grandma"])
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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


def explain_rejection(sign: Sign, trouble: Trouble, remedy: Remedy) -> str:
    if not omen_predicts(sign, trouble):
        return f"(No story: {sign.label} does not foreshadow {trouble.phrase}, so there is no true clue-to-trouble arc.)"
    if remedy.power < trouble.severity:
        return f"(No story: {remedy.label} is too weak for {trouble.phrase}; the fix would not be sensible.)"
    return "(No story: this combination does not make a good foreshadowing tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.trouble:
        sign = SIGNS[args.sign]
        trouble = TROUBLES[args.trouble]
        remedy = REMEDIES[args.remedy] if args.remedy else next(iter(REMEDIES.values()))
        if not omen_predicts(sign, trouble) or remedy.power < trouble.severity:
            raise StoryError(explain_rejection(sign, trouble, remedy))

    combos = [c for c in valid_combos()
              if (args.sign is None or c[0] == args.sign)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sign_id, trouble_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup_type = args.grownup_type or rng.choice(["uncle", "aunt", "grandpa", "grandma"])
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    place = args.place or rng.choice(PLACES)
    return StoryParams(
        sign=sign_id,
        trouble=trouble_id,
        remedy=remedy_id,
        child_name=name,
        child_type=gender,
        grownup_name=grownup,
        grownup_type=grownup_type,
        place=place,
        delay=args.delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the word "oval" and a clue that hints at {f["trouble"].phrase}.',
        f"Tell a foreshadowing story where {f['child'].id} notices {f['sign'].phrase} and a grown-up gets the warning in time.",
        f"Write a big-hearted prairie story where a tiny oval sign helps the family prepare before trouble arrives.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, grownup, sign, trouble, remedy = f["child"], f["grownup"], f["sign"], f["trouble"], f["remedy"]
    ready = f["ready"]
    items = [
        QAItem(
            question="Who noticed the clue first?",
            answer=f"{child.id} noticed it first. {child.id} saw {sign.phrase}, and that was the first hint that something was coming."
        ),
        QAItem(
            question="What did the oval clue warn about?",
            answer=f"It warned about {trouble.phrase}. The story uses that clue as foreshadowing, so the sign arrives before the trouble does."
        ),
        QAItem(
            question="What did the grown-up do when they understood the clue?",
            answer=f"{grownup.id} acted right away and {remedy.text}. That matched the warning and kept the day from getting worse."
        ),
    ]
    if ready:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended steady and safe. The trouble came, but the family was ready, so the road stayed calm and the oval sign kept its meaning."
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the trouble still pushing hard. The clue was real, but the answer was too small to finish the job."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["sign"].tags) | set(f["trouble"].tags) | set(f["remedy"].tags)
    bank = {
        "oval": QAItem("What is an oval?", "An oval is a smooth shape like a stretched circle. Folks in tall tales often treat an oval sign like a clue from the sky."),
        "foreshadowing": QAItem("What is foreshadowing?", "Foreshadowing is when a story gives a hint about something that will happen later. It helps the reader feel the coming trouble before it arrives."),
        "water": QAItem("Why can rising water be a problem?", "Rising water can reach roads, fields, and hooves. It can make travel hard and can wash things away if nobody gets ready."),
        "wind": QAItem("Why can strong wind be a problem?", "Strong wind can swing gates, scatter loose things, and make it hard to keep a place in order. A quick fix can stop a bigger mess."),
    }
    order = ["oval", "foreshadowing", "water", "wind"]
    return [bank[k] for k in order if k in tags and k in bank]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
omen(S,T) :- sign(S), trouble(T), foreshadows(S,T).
ready(S,T,R) :- omen(S,T), remedy(R), trouble(T), remedy_power(R,P), trouble_severity(T,V), P >= V.
outcome(steady) :- ready(_,_,_).
outcome(washed) :- not ready(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        for t in s.foreshadows.split():
            pass
    for sid, s in SIGNS.items():
        for tid, tr in TROUBLES.items():
            if tid in s.foreshadows:
                lines.append(asp.fact("foreshadows", sid, tid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_severity", tid, t.severity))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show omen/2.\n#show ready/3."))
    return sorted(set(asp.atoms(model, "ready")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_sign", params.sign),
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def valid_asp_ready() -> list[tuple]:
    return asp_valid_combos()


def asp_verify() -> int:
    rc = 0
    py = {(s, t, r) for (s, t, r) in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos() parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    for p in [StoryParams(sign="oval_stone", trouble="creek_rise", remedy="move_herd", child_name="Nora", child_type="girl", grownup_name="Uncle Reed", grownup_type="uncle", place="the canyon road", delay=0)]:
        if asp_outcome(p) == "?" or asp_outcome(p) not in {"steady", "washed"}:
            rc = 1
            print("MISMATCH in outcome parity.")
    return rc


CURATED = [
    StoryParams(sign="oval_stone", trouble="creek_rise", remedy="move_herd", child_name="Nora", child_type="girl", grownup_name="Uncle Reed", grownup_type="uncle", place="the creek bend", delay=0),
    StoryParams(sign="oval_cloud", trouble="rain_squall", remedy="cover_sacks", child_name="Eli", child_type="boy", grownup_name="Aunt Jo", grownup_type="aunt", place="the open prairie", delay=0),
    StoryParams(sign="oval_shadow", trouble="gate_wind", remedy="tie_gate", child_name="June", child_type="girl", grownup_name="Grandpa Bill", grownup_type="grandpa", place="the fence line", delay=0),
]


def generate(params: StoryParams) -> StorySample:
    if params.sign not in SIGNS or params.trouble not in TROUBLES or params.remedy not in REMEDIES:
        raise StoryError("Invalid story parameters.")
    sign = SIGNS[params.sign]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    if not omen_predicts(sign, trouble):
        raise StoryError(explain_rejection(sign, trouble, remedy))
    if remedy.power < trouble.severity:
        raise StoryError(explain_rejection(sign, trouble, remedy))
    world = tell(sign, trouble, remedy, params.child_name, params.child_type, params.grownup_name, params.grownup_type, params.place, params.delay)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.sign is None or c[0] == args.sign)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sign, trouble, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup_type = args.grownup_type or rng.choice(["uncle", "aunt", "grandpa", "grandma"])
    grownup_name = args.grownup or rng.choice(GROWNUP_NAMES)
    place = args.place or rng.choice(PLACES)
    return StoryParams(
        sign=sign,
        trouble=trouble,
        remedy=remedy,
        child_name=child_name,
        child_type=gender,
        grownup_name=grownup_name,
        grownup_type=grownup_type,
        place=place,
        delay=args.delay,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show ready/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show ready/3."))
        ready = sorted(set(asp.atoms(model, "ready")))
        print(f"{len(ready)} compatible omens:\n")
        for s, t, r in ready:
            print(f"  {s:12} {t:12} {r}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.sign} -> {p.trouble} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
