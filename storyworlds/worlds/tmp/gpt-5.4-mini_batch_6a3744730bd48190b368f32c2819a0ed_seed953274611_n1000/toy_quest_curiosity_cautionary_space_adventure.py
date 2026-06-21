#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/toy_quest_curiosity_cautionary_space_adventure.py
=================================================================================

A small standalone storyworld about a child on a space quest who gets too curious
about a mysterious toy signal, follows a cautionary warning, and ends with a
safer way to explore.

The domain is built around:
- a quest for a toy on a moon base or starship,
- curiosity as the driving tension,
- a cautionary turn that prevents trouble or resolves it safely,
- a space-adventure style with concrete state changes.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes,
- a forward causal world model,
- a Python reasonableness gate and inline ASP twin,
- story-grounded and world-knowledge QA,
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp.
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
BRAVERY_INIT = 5.0
CAUTION_MIN = 2

CREW_ROLES = {"child", "mentor"}


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
    reachable: bool = False
    glowing: bool = False
    fragile: bool = False
    safe: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mentor"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_zone: str
    quest_phrase: str
    launch_line: str
    style_tag: str


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    where: str
    lure: str
    safe_alt: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    scene: str
    risk: int
    power: int
    makes_danger: bool = True
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["danger"] >= THRESHOLD and ("alarm", e.id) not in world.fired:
            world.fired.add(("alarm", e.id))
            for c in world.characters():
                c.memes["fear"] += 1
            out.append("__alarm__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


CAUSAL_RULES: list[Rule] = [Rule("alarm", "social", _r_alarm)]


def quest_at_risk(toy: Toy, hazard: Hazard) -> bool:
    return toy.where == hazard.scene and hazard.makes_danger


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= CAUTION_MIN]


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard.risk + delay


def would_avert(child: Entity, mentor: Entity) -> bool:
    cautious = mentor.memes["caution"] + 1.0
    return child.memes["curiosity"] < mentor.memes["trust"] and cautious > BRAVERY_INIT


def _do_hazard(world: World, hazard: Entity, narrate: bool = True) -> None:
    hazard.meters["danger"] += 1
    propagate(world, narrate=narrate)


def scout(world: World, child: Entity, toy: Toy, setting: Setting) -> None:
    world.say(
        f"On the {setting.place}, {child.id} spotted {toy.phrase} near {setting.dark_zone}. "
        f"{setting.scene}"
    )
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f'"{setting.quest_phrase}!" {child.id} whispered. "{toy.lure}"'
    )


def warn(world: World, mentor: Entity, child: Entity, toy: Toy, hazard: Hazard) -> None:
    mentor.memes["caution"] += 1
    world.say(
        f'{mentor.id} touched {child.pronoun("possessive")} shoulder. '
        f'"Careful," {mentor.pronoun()} said. "{toy.label} is close to {hazard.label}, '
        f'and that can turn a toy hunt into a space mess."'
    )


def defy(world: World, child: Entity, toy: Toy) -> None:
    child.memes["defiance"] += 1
    world.say(f'"But I have to see!" {child.id} said, and followed the blinking trail.')


def back_down(world: World, child: Entity, mentor: Entity, toy: Toy, alt: str) -> None:
    child.memes["relief"] += 1
    mentor.memes["relief"] += 1
    world.say(
        f'{child.id} looked at {mentor.id}, then at {toy.label}, and gave up the risky idea. '
        f"They chose {alt} instead."
    )


def trigger(world: World, toy_ent: Entity, hazard: Hazard) -> None:
    _do_hazard(world, toy_ent)
    world.say(
        f"A bright spark flashed from {hazard.label}, and the glow around the toy grew hot. "
        f"The little trail of light wobbled like it wanted to race away."
    )


def call_help(world: World, mentor: Entity, child: Entity, response: Response, hazard: Hazard) -> None:
    world.say(
        f'"{child.id}!" {mentor.id} shouted. "{mentor.pronoun("subject").capitalize()} reached the control panel and {response.text}."'
    )
    world.say(
        f"The danger shrank fast, and the blinking light stopped before it could spread through the hatch."
    )
    mentor.memes["pride"] += 1
    child.memes["fear"] += 1
    child.memes["trust"] += 1


def lesson(world: World, mentor: Entity, child: Entity, toy: Toy, safe_alt: str) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    world.say(
        f"Afterward, {mentor.id} knelt down and hugged {child.id}. "
        f'""You did the brave thing by calling me," {mentor.pronoun()} said. '
        f'"A toy should be fun, not risky. When curiosity gets big, use a safe helper."'
    )
    world.say(
        f"The next morning, {mentor.id} handed over {safe_alt}. {child.id} smiled, "
        f"and the quest continued with a safer map and a calmer heart."
    )


def tell(setting: Setting, toy: Toy, hazard: Hazard, response: Response, delay: int = 0,
         child_name: str = "Nova", child_type: str = "girl",
         mentor_name: str = "Commander Rae", mentor_type: str = "mentor") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type, role="mentor"))
    toy_ent = world.add(Entity(id="toy", type="thing", label=toy.label, fragile=toy.fragile))
    hazard_ent = world.add(Entity(id="hazard", type="thing", label=hazard.label, glowing=True, safe=False))

    child.memes["curiosity"] = BRAVERY_INIT
    mentor.memes["trust"] = 4.0
    mentor.memes["caution"] = 4.0

    scout(world, child, toy, setting)
    world.para()
    warn(world, mentor, child, toy, hazard)
    av = would_avert(child, mentor)
    if av:
        back_down(world, child, mentor, toy, toy.safe_alt)
        world.para()
        lesson(world, mentor, child, toy, toy.safe_alt)
        outcome = "averted"
        contained = True
    else:
        defy(world, child, toy)
        world.para()
        trigger(world, toy_ent, hazard)
        child.memes["curiosity"] += 1
        child.memes["fear"] += 1
        contained = is_contained(response, hazard, delay)
        if contained:
            world.para()
            call_help(world, mentor, child, response, hazard)
            lesson(world, mentor, child, toy, toy.safe_alt)
        else:
            world.say(
                f"{response.fail.replace('{toy}', toy.label)} The station shuddered, and everyone had to retreat to the safety dock."
            )
            world.say(
                f"Even so, {mentor.id} kept {child.id} close, and the crew later sealed the hatch so the toy hunt could try again another day."
            )
        outcome = "contained" if contained else "failed"

    world.facts.update(
        child=child, mentor=mentor, toy=toy, hazard=hazard, response=response,
        delay=delay, outcome=outcome, contained=contained, safe_alt=toy.safe_alt,
    )
    return world


SETTINGS = {
    "moonbase": Setting(
        id="moonbase",
        place="Moon Base Nine",
        scene="The silver corridors gleamed, and tiny portholes showed the stars blinking back.",
        dark_zone="the airlock shadow",
        quest_phrase="Could the toy be hiding in the shadow",
        launch_line="The crew followed the glow through the hall",
        style_tag="space adventure",
    ),
    "starship": Setting(
        id="starship",
        place="Starship Comet",
        scene="The engines hummed softly while the blue panels blinked like sleepy stars.",
        dark_zone="the cargo bay corner",
        quest_phrase="Could the toy be hiding behind the crates",
        launch_line="The crew padded down the corridor",
        style_tag="space adventure",
    ),
    "asteroid_outpost": Setting(
        id="asteroid_outpost",
        place="Aster Outpost",
        scene="The outpost floated above the rocks, and every window opened onto a glittering sky.",
        dark_zone="the docking nook",
        quest_phrase="Was the toy tucked into the docking nook",
        launch_line="The little boots tapped along the ring tunnel",
        style_tag="space adventure",
    ),
}

TOYS = {
    "robot": Toy(
        id="robot", label="a tiny robot toy", phrase="a tiny robot toy",
        where="the airlock shadow", lure="Its eyes blinked once, as if it wanted to play.",
        safe_alt="a bright flashlight",
        fragile=False, tags={"toy", "robot"},
    ),
    "comet_ball": Toy(
        id="comet_ball", label="a comet ball toy", phrase="a comet ball toy",
        where="the cargo bay corner", lure="It shimmered silver and rolled when nobody looked.",
        safe_alt="a soft glow stick",
        fragile=True, tags={"toy"},
    ),
    "moon_puppet": Toy(
        id="moon_puppet", label="a moon puppet toy", phrase="a moon puppet toy",
        where="the docking nook", lure="It waved its little arms like it knew the route.",
        safe_alt="a map tablet with bright icons",
        fragile=True, tags={"toy"},
    ),
}

HAZARDS = {
    "spark_panel": Hazard(
        id="spark_panel", label="a sparking panel", scene="the airlock shadow", risk=3, power=3, tags={"spark", "panel"}
    ),
    "drift_dust": Hazard(
        id="drift_dust", label="a drifting dust burst", scene="the cargo bay corner", risk=2, power=2, tags={"dust"}
    ),
    "shimmer_field": Hazard(
        id="shimmer_field", label="a shimmering field", scene="the docking nook", risk=4, power=4, tags={"field"}
    ),
}

RESPONSES = {
    "cut_power": Response(
        id="cut_power", sense=4, power=4,
        text="cut the power and opened the safety shutters",
        fail="the panel still crackled too hard to stop",
        qa_text="cut the power and opened the safety shutters",
        tags={"power", "safe"},
    ),
    "shield": Response(
        id="shield", sense=3, power=3,
        text="pulled the shield cover over the sparks",
        fail="the shield was too small and the sparks slipped around it",
        qa_text="pulled the shield cover over the sparks",
        tags={"shield"},
    ),
    "signal_help": Response(
        id="signal_help", sense=5, power=5,
        text="sent a help signal to the control room",
        fail="the signal bounced away from the danger and did not help",
        qa_text="sent a help signal to the control room",
        tags={"help"},
    ),
    "water_spray": Response(
        id="water_spray", sense=1, power=1,
        text="sprayed water",
        fail="sprayed water, but it was nowhere near enough",
        qa_text="sprayed water",
        tags={"water"},
    ),
}

CURATED = [
    StoryParams(
        setting="moonbase", toy="robot", hazard="spark_panel", response="signal_help",
        delay=0, child_name="Nova", child_type="girl", mentor_name="Commander Rae", mentor_type="mentor",
    ),
    StoryParams(
        setting="starship", toy="comet_ball", hazard="drift_dust", response="shield",
        delay=0, child_name="Milo", child_type="boy", mentor_name="Pilot Jun", mentor_type="mentor",
    ),
    StoryParams(
        setting="asteroid_outpost", toy="moon_puppet", hazard="shimmer_field", response="cut_power",
        delay=1, child_name="Iris", child_type="girl", mentor_name="Captain Sol", mentor_type="mentor",
    ),
]


@dataclass
class StoryParams:
    setting: str
    toy: str
    hazard: str
    response: str
    delay: int = 0
    child_name: str = "Nova"
    child_type: str = "girl"
    mentor_name: str = "Commander Rae"
    mentor_type: str = "mentor"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for toy_id, toy in TOYS.items():
            if toy.where != setting.dark_zone:
                continue
            for hid, hazard in HAZARDS.items():
                if hazard.scene == toy.where and hazard.makes_danger:
                    out.append((sid, toy_id, hid))
    return out


def explain_rejection(toy: Toy, hazard: Hazard) -> str:
    if toy.where != hazard.scene:
        return (
            f"(No story: {toy.label} is in {toy.where}, but {hazard.label} is in {hazard.scene}. "
            "The quest needs the toy and the risk to meet in one place.)"
        )
    return "(No story: this combination does not make a believable space-adventure hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on caution (sense={r.sense} < {CAUTION_MIN}). Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure toy quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--mentor-name")
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
    if args.response and RESPONSES[args.response].sense < CAUTION_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.toy is None or c[1] == args.toy)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy_id, hazard_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(
        setting=setting,
        toy=toy_id,
        hazard=hazard_id,
        response=response,
        delay=rng.randint(0, 1),
        child_name=args.child_name or rng.choice(["Nova", "Milo", "Iris", "Pax", "Lyra"]),
        child_type=rng.choice(["girl", "boy"]),
        mentor_name=args.mentor_name or rng.choice(["Commander Rae", "Pilot Jun", "Captain Sol"]),
        mentor_type="mentor",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the word "toy" and a curious child exploring a base.',
        f"Tell a cautionary quest story where {f['child'].id} spots {f['toy'].label} near a danger and listens to {f['mentor'].id} before it becomes a mess.",
        f"Write a moon-base or starship story with a toy hunt, a warning, and a safer ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, mentor, toy, hazard = f["child"], f["mentor"], f["toy"], f["hazard"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {mentor.id} on a space quest for a toy. The story follows curiosity, a warning, and a safer choice."),
        ("Why did {0} feel curious?".format(child.id),
         f"{child.id} saw {toy.phrase} and wanted to know more about it. The blinking clue made the quest feel exciting, but it was close to {hazard.label}."),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after {mentor.id} warned {child.id}?",
            f"{child.id} gave up the risky idea and chose the safer path. That kept the toy hunt calm and stopped any danger from starting."
        ))
    elif f["contained"]:
        qa.append((
            f"How did {mentor.id} stop the danger?",
            f"{mentor.id} used {f['response'].qa_text} to shut it down. The quick response kept the quest from turning into a bigger problem."
        ))
    else:
        qa.append((
            "What went wrong?",
            f"The danger was too strong for that response. The crew had to retreat and try again another day."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with a safer helper in hand and the quest still going. {child.id} kept the toy idea, but now curiosity had a safer way to travel."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["toy"].tags) | set(f["hazard"].tags)
    if f["contained"]:
        tags |= set(f["response"].tags)
    out = []
    if "toy" in tags:
        out.append(("What is a toy?",
                     "A toy is something children play with. It should be safe and fun to hold."))

    out.append(("What does caution mean?",
                 "Caution means being careful before acting, especially when something could be risky."))

    out.append(("What is curiosity?",
                 "Curiosity is the feeling that makes you want to explore and learn more. It can be good, as long as you stay safe."))

    if "help" in tags or f["contained"]:
        out.append(("Why is calling for help smart?",
                     "Calling for help brings in a grown-up who knows how to deal with danger. It is a quick way to keep everyone safe."))
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.toy not in TOYS or params.hazard not in HAZARDS or params.response not in RESPONSES:
        raise StoryError("(Invalid params: unknown setting/toy/hazard/response.)")
    toy = TOYS[params.toy]
    hazard = HAZARDS[params.hazard]
    if not quest_at_risk(toy, hazard):
        raise StoryError(explain_rejection(toy, hazard))
    response = RESPONSES[params.response]
    if response.sense < CAUTION_MIN:
        raise StoryError(explain_response(params.response))
    world = tell(SETTINGS[params.setting], toy, hazard, response, delay=params.delay,
                 child_name=params.child_name, child_type=params.child_type,
                 mentor_name=params.mentor_name, mentor_type=params.mentor_type)
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


ASP_RULES = r"""
quest_at_risk(T, H) :- toy(T), hazard(H), meets(T, H).
sensible(R) :- response(R), sense(R, S), min_sense(M), S >= M.
contained(R, H, D) :- response(R), power(R, P), hazard(H), risk(H, Rk), delay(D), P >= Rk + D.
outcome(averted) :- cautious_move.
outcome(contained) :- not cautious_move, chosen_response(R), chosen_hazard(H), delay(D), contained(R, H, D).
outcome(failed) :- not cautious_move, chosen_response(R), chosen_hazard(H), delay(D), not contained(R, H, D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("meets", tid, t.where))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("risk", hid, h.risk))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("min_sense", CAUTION_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show quest_at_risk/2."))
    return sorted(set(asp.atoms(model, "quest_at_risk")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
        print("python:", sorted(valid_combos()))
        print("asp:", sorted(asp_valid_combos()))
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses.")
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("SMOKE TEST FAILED: empty story.")
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def outcome_of(params: StoryParams) -> str:
    if params.response not in RESPONSES:
        return "?"
    if would_avert(Entity(id="c", type=params.child_type), Entity(id="m", type=params.mentor_type)):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "failed"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show quest_at_risk/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show quest_at_risk/2.\n#show sensible/1."))
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        print("compatible quest combos:")
        for t, h in sorted(set(asp.atoms(model, "quest_at_risk"))):
            print(f"  {t:12} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name} on {p.setting}: {p.toy} near {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
